import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.services.base_source import PaperSource

class CrossRefService(PaperSource):
    """CrossRef service for DOI metadata"""

    def __init__(self, email: Optional[str] = None):
        super().__init__()
        self.source_name = "crossref"
        self.base_url = "https://api.crossref.org"
        self.email = email  # For polite pool access
        # CrossRef allows up to 1000 requests per day for free
        self.rows_per_page = 20

    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search CrossRef works
        """
        try:
            url = f"{self.base_url}/works"
            params = {
                "query.title": query,
                "rows": min(limit, 1000),  # API max is 1000
                "sort": "relevance"
            }

            # Add mailto for polite pool (higher rate limits)
            if hasattr(self, 'email') and self.email:
                params["mailto"] = self.email

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)

                # Log detailed error info for debugging
                if response.status_code >= 400:
                    print(f"CrossRef API Error - Status: {response.status_code}")
                    print(f"CrossRef API Error - URL: {response.url}")
                    try:
                        error_body = response.json()
                        print(f"CrossRef API Error - Body: {error_body}")
                    except:
                        print(f"CrossRef API Error - Text: {response.text[:500]}")

                response.raise_for_status()
                data = response.json()

            papers = []
            for item in data.get("message", {}).get("items", []):
                paper = self.normalize_paper(item)
                if paper:
                    papers.append(paper)

            return papers[:limit]

        except Exception as e:
            print(f"CrossRef search error: {str(e)}")
            return []

    async def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get single paper by DOI"""
        try:
            # Clean DOI
            doi = paper_id.strip().replace("https://doi.org/", "").replace("doi:", "")

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/works/{doi}")
                response.raise_for_status()
                data = response.json()

            return self.normalize_paper(data.get("message", {}))

        except Exception as e:
            print(f"CrossRef get_paper_by_id error: {e}")
        return None

    def normalize_paper(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert CrossRef format to standard schema"""
        # Extract title
        title = ""
        if "title" in raw_data and raw_data["title"]:
            title = raw_data["title"][0] if isinstance(raw_data["title"], list) else raw_data["title"]

        # Extract abstract
        abstract = ""
        if "abstract" in raw_data:
            abstract = raw_data["abstract"]

        # Extract authors
        authors = []
        if "author" in raw_data:
            for author in raw_data["author"]:
                if isinstance(author, dict):
                    given = author.get("given", "")
                    family = author.get("family", "")
                    if given and family:
                        authors.append(f"{given} {family}")
                    elif family:
                        authors.append(family)

        # Extract publication date
        pub_date = None
        if "published" in raw_data and "date-parts" in raw_data["published"]:
            date_parts = raw_data["published"]["date-parts"]
            if date_parts and len(date_parts) > 0:
                parts = date_parts[0]
                if len(parts) >= 3:
                    try:
                        pub_date = f"{parts[0]}-{parts[1]:02d}-{parts[2]:02d}"
                    except:
                        pass
                elif len(parts) >= 1:
                    pub_date = f"{parts[0]}-01-01"

        # Extract DOI
        doi = raw_data.get("DOI", "")

        # Extract venue (journal title)
        venue = ""
        if "container-title" in raw_data and raw_data["container-title"]:
            venue = raw_data["container-title"][0] if isinstance(raw_data["container-title"], list) else raw_data["container-title"]

        # Extract publisher
        publisher = raw_data.get("publisher", "")

        return {
            "title": title.strip(),
            "abstract": abstract.strip(),
            "authors": authors,
            "publication_date": self._parse_date(pub_date),
            "pdf_url": None,  # CrossRef doesn't provide direct PDFs
            "source": "crossref",
            "source_id": doi,
            "doi": doi,
            "citation_count": 0,  # CrossRef doesn't provide citation counts directly
            "venue": venue,
            "publisher": publisher
        }

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse CrossRef date format"""
        if not date_str:
            return None

        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            # Try year only
            try:
                return datetime.strptime(date_str[:4], "%Y")
            except ValueError:
                return None
