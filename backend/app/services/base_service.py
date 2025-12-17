import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
from urllib.parse import quote
from app.services.base_source import PaperSource

class BASEService(PaperSource):
    """BASE (Bielefeld Academic Search Engine) service"""

    def __init__(self):
        super().__init__()
        self.source_name = "base"
        self.base_url = "https://www.base-search.net"
        self.api_url = "https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi"
        self.oai_url = "https://www.base-search.net/oai/provider"

    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search BASE using their search interface
        """
        try:
            # BASE search parameters
            params = {
                "func": "PerformSearch",
                "query": query,
                "hits": min(limit * 2, 100),  # Get more for filtering
                "output": "xml",
                "sort": "relevance",
                "cc": "all"  # All collections
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.api_url, params=params)
                response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(response.text)
            papers = []

            for record in root.findall(".//record"):
                paper = self._parse_record_xml(record)
                if paper and self._is_relevant_paper(paper):
                    papers.append(paper)

            return papers[:limit]

        except Exception as e:
            print(f"BASE search error: {e}")
            return []

    async def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get single paper by BASE ID"""
        try:
            # Try OAI-PMH GetRecord
            params = {
                "verb": "GetRecord",
                "identifier": f"oai:base-search.net:{paper_id}",
                "metadataPrefix": "oai_dc"
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.oai_url, params=params)
                response.raise_for_status()

            root = ET.fromstring(response.text)
            record = root.find(".//{http://www.openarchives.org/OAI/2.0/}record")
            if record:
                return self._parse_oai_record(record)

        except Exception as e:
            print(f"BASE get_paper_by_id error: {e}")
        return None

    def _parse_record_xml(self, record_elem) -> Optional[Dict[str, Any]]:
        """Parse BASE search result XML"""
        try:
            # Extract basic metadata
            title_elem = record_elem.find(".//title")
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""

            # Extract description/abstract
            desc_elem = record_elem.find(".//description")
            abstract = ""
            if desc_elem is not None and desc_elem.text:
                abstract = desc_elem.text.strip()

            # Extract creators/authors
            authors = []
            for creator_elem in record_elem.findall(".//creator"):
                if creator_elem.text:
                    authors.append(creator_elem.text.strip())

            # Extract date
            date_elem = record_elem.find(".//date")
            pub_date = None
            if date_elem is not None and date_elem.text:
                pub_date = date_elem.text.strip()

            # Extract identifiers
            doi = None
            base_id = None
            for id_elem in record_elem.findall(".//identifier"):
                if id_elem.text:
                    id_text = id_elem.text.strip()
                    if id_text.startswith("doi:"):
                        doi = id_text.replace("doi:", "")
                    elif "base-search.net" in id_text:
                        base_id = id_text.split("/")[-1]

            # Extract publisher/venue
            publisher_elem = record_elem.find(".//publisher")
            venue = publisher_elem.text.strip() if publisher_elem is not None and publisher_elem.text else ""

            # Extract subject
            subject_elem = record_elem.find(".//subject")
            subject = subject_elem.text.strip() if subject_elem is not None and subject_elem.text else ""

            return {
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "publication_date": pub_date,
                "doi": doi,
                "base_id": base_id,
                "venue": venue,
                "subject": subject,
                "source": "base"
            }

        except Exception as e:
            print(f"BASE record parsing error: {e}")
            return None

    def _parse_oai_record(self, record_elem) -> Optional[Dict[str, Any]]:
        """Parse OAI-PMH record"""
        try:
            metadata = record_elem.find(".//{http://www.openarchives.org/OAI/2.0/oai_dc/}dc")

            if metadata is None:
                return None

            # Extract title
            title_elem = metadata.find(".//{http://purl.org/dc/elements/1.1/}title")
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""

            # Extract description
            desc_elem = metadata.find(".//{http://purl.org/dc/elements/1.1/}description")
            abstract = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ""

            # Extract creators
            authors = []
            for creator_elem in metadata.findall(".//{http://purl.org/dc/elements/1.1/}creator"):
                if creator_elem.text:
                    authors.append(creator_elem.text.strip())

            # Extract date
            date_elem = metadata.find(".//{http://purl.org/dc/elements/1.1/}date")
            pub_date = date_elem.text.strip() if date_elem is not None and date_elem.text else None

            # Extract identifiers
            doi = None
            for id_elem in metadata.findall(".//{http://purl.org/dc/elements/1.1/}identifier"):
                if id_elem.text and "doi.org" in id_elem.text:
                    doi = id_elem.text.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
                    break

            # Extract publisher
            publisher_elem = metadata.find(".//{http://purl.org/dc/elements/1.1/}publisher")
            venue = publisher_elem.text.strip() if publisher_elem is not None and publisher_elem.text else ""

            return {
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "publication_date": pub_date,
                "doi": doi,
                "venue": venue,
                "source": "base"
            }

        except Exception as e:
            print(f"BASE OAI parsing error: {e}")
            return None

    def normalize_paper(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert BASE format to standard schema"""
        return {
            "title": raw_data.get("title", "").strip(),
            "abstract": raw_data.get("abstract", "").strip(),
            "authors": raw_data.get("authors", []),
            "publication_date": self._parse_date(raw_data.get("publication_date")),
            "pdf_url": None,  # BASE may provide links but not direct PDFs
            "source": "base",
            "source_id": raw_data.get("base_id") or raw_data.get("doi", ""),
            "doi": raw_data.get("doi"),
            "citation_count": 0,  # BASE doesn't provide citation counts
            "venue": raw_data.get("venue", ""),
            "subject": raw_data.get("subject", "")
        }

    def _is_relevant_paper(self, paper: Dict) -> bool:
        """Filter for academic relevance"""
        # Skip if no title
        if not paper.get("title") or len(paper.get("title", "")) < 10:
            return False

        # Skip non-academic content
        title_lower = paper.get("title", "").lower()
        venue_lower = paper.get("venue", "").lower()

        # Skip obvious non-academic content
        skip_terms = ["thesis", "dissertation", "blog", "news", "personal"]
        if any(term in title_lower or term in venue_lower for term in skip_terms):
            return False

        return True

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse BASE date format"""
        if not date_str:
            return None

        try:
            # Try various formats
            for fmt in ["%Y-%m-%d", "%Y-%m", "%Y", "%Y-%m-%dT%H:%M:%S%z"]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None
