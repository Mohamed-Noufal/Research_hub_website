"""
ERIC (Education Resources Information Center) service.
Provides access to education, teaching, pedagogy, training, and learning science research.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from app.services.base_source import PaperSource
from app.utils.http_client import AcademicAPIClient

class ERICService(PaperSource):
    """ERIC service for education and social science research"""

    def __init__(self):
        super().__init__()
        self.source_name = "eric"
        self.base_url = "https://api.ies.ed.gov/eric/"

        # ERIC allows ~1-5 requests per second, be conservative
        self.client = AcademicAPIClient(
            user_agent="Academic-Search-Bot/1.0 (research@example.com)",
            rate_limit_per_second=2.0,  # Conservative rate limiting
            max_retries=3  # Retry for network issues
        )

    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search ERIC for educational research
        """
        try:
            async with self.client:
                params = {
                    "search": query,
                    "limit": min(limit, 25),  # ERIC max is ~2000 but we'll use smaller batches
                    "startRecord": 1  # Start from first record
                }

                response, data = await self.client.get(self.base_url, params=params)

                papers = []
                # ERIC API returns data in response.docs, not records
                response_data = data.get("response", {})
                records = response_data.get("docs", [])

                for record in records:
                    paper = self.normalize_paper(record)
                    if paper:
                        papers.append(paper)

                return papers[:limit]

        except Exception as e:
            print(f"ERIC search error: {e}")
            return []

    async def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get single paper by ERIC ID"""
        try:
            async with self.client:
                # ERIC doesn't have direct ID lookup, try search by ID
                params = {
                    "search": f"id:{paper_id}",
                    "limit": 1
                }

                response, data = await self.client.get(self.base_url, params=params)

                # ERIC API returns data in response.docs, not records
                response_data = data.get("response", {})
                records = response_data.get("docs", [])
                if records:
                    return self.normalize_paper(records[0])

        except Exception as e:
            print(f"ERIC get_paper_by_id error: {e}")

        return None

    def normalize_paper(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ERIC format to standard schema"""
        # Extract title
        title = raw_data.get("title", "").strip()

        # Extract authors - ERIC uses "author" field (list of strings)
        authors_raw = raw_data.get("author", [])
        authors = []
        if isinstance(authors_raw, list):
            authors = [author for author in authors_raw if isinstance(author, str) and author.strip()]

        # Extract publication date
        pub_date = None
        date_str = raw_data.get("publicationDate", "")
        if date_str:
            try:
                # Try different date formats
                for fmt in ["%Y", "%Y-%m", "%Y-%m-%d"]:
                    try:
                        pub_date = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        continue
            except:
                pass

        # Extract description (abstract)
        description = raw_data.get("description", "").strip()

        # Extract source information
        source_info = raw_data.get("source", "")
        venue = ""
        if isinstance(source_info, dict):
            venue = source_info.get("title", "")
        elif isinstance(source_info, str):
            venue = source_info

        # Extract URL
        url = raw_data.get("url", "")

        # Extract identifiers
        identifiers = raw_data.get("identifiers", [])
        doi = None
        eric_id = raw_data.get("id")

        if isinstance(identifiers, list):
            for identifier in identifiers:
                if isinstance(identifier, dict):
                    if identifier.get("type") == "doi":
                        doi = identifier.get("value")
                elif isinstance(identifier, str) and identifier.startswith("10."):
                    doi = identifier

        return {
            "title": title,
            "abstract": description,
            "authors": authors,
            "publication_date": pub_date,
            "pdf_url": url,  # ERIC provides direct links to papers
            "source": "eric",
            "source_id": eric_id,
            "doi": doi,
            "citation_count": 0,  # ERIC doesn't provide citation counts
            "venue": venue,
            "language": "en",  # ERIC is primarily English
            "fullText": description  # Use description as full text
        }

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse ERIC date format"""
        if not date_str:
            return None

        try:
            # Try different formats that ERIC might use
            for fmt in ["%Y", "%Y-%m", "%Y-%m-%d", "%B %Y", "%m/%d/%Y"]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None
