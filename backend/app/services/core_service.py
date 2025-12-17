import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
import urllib.parse
from app.services.base_source import PaperSource
from app.core.config import settings

class COREService(PaperSource):
    """CORE (COnnecting REpositories) service"""

    def __init__(self):
        super().__init__()
        self.source_name = "core"
        self.base_url = "https://api.core.ac.uk/v3"
        self.search_url = f"{self.base_url}/search/works/"  # Note: trailing slash required
        self.api_key = settings.CORE_API_KEY

    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search CORE using their search API
        """
        try:
            params = {
                "q": query,
                "limit": min(limit * 2, 100),  # Get more for filtering
                "sort": "relevance",  # Sort by relevance
                "scroll": False
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.search_url, params=params, headers=headers)

                # Log detailed error info for debugging
                if response.status_code >= 400:
                    print(f"CORE API Error - Status: {response.status_code}")
                    print(f"CORE API Error - Headers: {dict(response.headers)}")
                    try:
                        error_body = response.json()
                        print(f"CORE API Error - Body: {error_body}")
                    except:
                        print(f"CORE API Error - Text: {response.text[:500]}")

                response.raise_for_status()
                data = response.json()

            papers = []
            for item in data.get("results", []):
                paper = self.normalize_paper(item)
                if paper and self._is_relevant_paper(paper):
                    papers.append(paper)

            return papers[:limit]

        except Exception as e:
            print(f"CORE search error: {e}")
            return []

    async def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get single paper by CORE ID"""
        try:
            url = f"{self.base_url}/works/{paper_id}"

            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

            return self.normalize_paper(data)

        except Exception as e:
            print(f"CORE get_paper_by_id error: {e}")

        return None

    def normalize_paper(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert CORE format to standard schema"""
        return {
            "title": raw_data.get("title", "").strip(),
            "abstract": raw_data.get("abstract", "").strip() if raw_data.get("abstract") else "",
            "authors": self._parse_authors(raw_data.get("authors", [])),
            "publication_date": self._parse_date(raw_data.get("publishedDate")),
            "pdf_url": raw_data.get("downloadUrl"),
            "source": "core",
            "source_id": str(raw_data.get("id", "")),
            "doi": raw_data.get("doi"),
            "citation_count": 0,  # CORE doesn't provide citation counts
            "venue": raw_data.get("publisher", ""),
            "language": raw_data.get("language", ""),
            "fullText": raw_data.get("fullText", "")
        }

    def _is_relevant_paper(self, paper: Dict) -> bool:
        """Filter for academic relevance"""
        # Skip if no title or abstract
        if not paper.get("title") or len(paper.get("title", "")) < 10:
            return False

        # Skip non-academic publishers
        non_academic = ["blog", "news", "magazine", "personal"]
        venue = paper.get("venue", "").lower()
        if any(term in venue for term in non_academic):
            return False

        # Prefer papers with abstracts
        if not paper.get("abstract"):
            return False

        return True

    def _parse_authors(self, authors_data) -> List[str]:
        """Parse authors from CORE format"""
        authors = []
        if isinstance(authors_data, list):
            for author in authors_data:
                if isinstance(author, dict):
                    name = author.get("name", "")
                    if name:
                        authors.append(name)
                elif isinstance(author, str):
                    authors.append(author)
        return authors

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse CORE date format"""
        if not date_str:
            return None

        try:
            # Try different formats
            for fmt in ["%Y-%m-%d", "%Y-%m", "%Y", "%Y-%m-%dT%H:%M:%S%z"]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None
