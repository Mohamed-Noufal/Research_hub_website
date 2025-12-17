"""
Europe PMC service - Alternative to BASE for open biomedical access.
Covers biomedical and life sciences with reliable API access.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from app.services.base_source import PaperSource
from app.utils.http_client import AcademicAPIClient

class EuropePMCService(PaperSource):
    """Europe PMC service for biomedical and life sciences open access content"""

    def __init__(self):
        super().__init__()
        self.source_name = "europe_pmc"
        # Use the exact search URL as per documentation
        self.search_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

        # Europe PMC allows up to 1000 requests per minute for registered users
        # For anonymous access, be conservative
        self.client = AcademicAPIClient(
            user_agent="Academic-Search-Bot/1.0 (research@example.com)",
            rate_limit_per_second=5.0,  # Conservative: 5 requests per second
            max_retries=5  # Enable retries for rate limits and server errors (429, 503, 5xx)
        )

    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search Europe PMC for biomedical literature
        """
        try:
            async with self.client:
                # Use search endpoint with proper parameters
                params = {
                    "query": query,
                    "format": "json",
                    "pageSize": min(limit, 25),  # Max 25 per request
                    "page": 1
                }

                response, data = await self.client.get(self.search_url, params=params)

                papers = []
                results = data.get("resultList", {}).get("result", [])

                for item in results:
                    paper = self.normalize_paper(item)
                    if paper:
                        papers.append(paper)

                return papers[:limit]

        except Exception as e:
            print(f"Europe PMC search error: {e}")
            return []

    async def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get single paper by Europe PMC ID or DOI"""
        try:
            async with self.client:
                # Try to get by PMCID first, then DOI
                if paper_id.startswith("PMC"):
                    # It's a PMCID
                    params = {
                        "query": f"PMCID:{paper_id}",
                        "format": "json",
                        "pageSize": 1
                    }
                else:
                    # Try as DOI
                    params = {
                        "query": f"DOI:{paper_id}",
                        "format": "json",
                        "pageSize": 1
                    }

                response, data = await self.client.get(self.search_url, params=params)

                results = data.get("resultList", {}).get("result", [])
                if results:
                    return self.normalize_paper(results[0])

        except Exception as e:
            print(f"Europe PMC get_paper_by_id error: {e}")

        return None

    def normalize_paper(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Europe PMC format to standard schema"""
        # Extract title
        title = raw_data.get("title", "").strip()

        # Extract abstract
        abstract = raw_data.get("abstractText", "").strip()

        # Extract authors
        authors = []
        author_list = raw_data.get("authorList", {}).get("author", [])
        if isinstance(author_list, list):
            for author in author_list:
                if isinstance(author, dict):
                    full_name = author.get("fullName", "")
                    if full_name:
                        authors.append(full_name)
                elif isinstance(author, str):
                    authors.append(author)

        # Extract publication date
        pub_date = None
        date_info = raw_data.get("firstPublicationDate", "")
        if date_info:
            try:
                # Format: "2023-10-15"
                pub_date = datetime.strptime(date_info, "%Y-%m-%d").date()
            except ValueError:
                try:
                    # Try year-month format
                    pub_date = datetime.strptime(date_info, "%Y-%m").date()
                except ValueError:
                    try:
                        # Try year only
                        pub_date = datetime.strptime(date_info, "%Y").date()
                    except ValueError:
                        pass

        # Extract DOI
        doi = raw_data.get("doi")

        # Extract PMCID and PMID
        pmcid = raw_data.get("pmcid")
        pmid = raw_data.get("pmid")

        # Extract journal info
        journal_info = raw_data.get("journalInfo", {})
        venue = journal_info.get("journal", {}).get("title", "") if isinstance(journal_info, dict) else ""

        # Extract PDF URL (Europe PMC provides full text access)
        pdf_url = None
        if pmcid:
            # Europe PMC provides direct PDF access for open access content
            pdf_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"

        return {
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "publication_date": pub_date,
            "pdf_url": pdf_url,
            "source": "europe_pmc",
            "source_id": pmcid or doi or raw_data.get("id"),
            "doi": doi,
            "citation_count": 0,  # Europe PMC doesn't provide citation counts in basic search
            "venue": venue,
            "pmcid": pmcid,
            "pmid": pmid,
            "fullText": raw_data.get("fullText", ""),
            "isOpenAccess": raw_data.get("isOpenAccess", False)
        }

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse Europe PMC date format"""
        if not date_str:
            return None

        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%Y-%m")
            except ValueError:
                try:
                    return datetime.strptime(date_str, "%Y")
                except ValueError:
                    return None
