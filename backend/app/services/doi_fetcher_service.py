"""
DOI Paper Fetcher Service
Fetches paper metadata and PDF from DOI using multiple sources
"""
from typing import Optional, Dict, Any
import httpx
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DOIFetcherService:
    """Service to fetch papers by DOI from multiple sources"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.sources = {
            "crossref": self._fetch_from_crossref,
            "unpaywall": self._fetch_from_unpaywall,
            "semantic_scholar": self._fetch_from_semantic_scholar,
        }
    
    async def fetch_paper_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Fetch paper metadata and PDF link by DOI
        
        Args:
            doi: Digital Object Identifier (e.g., "10.1038/nature12373")
        
        Returns:
            Paper metadata dict or None if not found
        """
        # Clean DOI (remove URL prefix if present)
        doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
        
        logger.info(f"Fetching paper by DOI: {doi}")
        
        # Try each source in order
        for source_name, fetch_func in self.sources.items():
            try:
                logger.info(f"Trying source: {source_name}")
                paper = await fetch_func(doi)
                
                if paper:
                    logger.info(f"✅ Found paper in {source_name}")
                    paper["source"] = source_name
                    paper["doi"] = doi
                    return paper
                    
            except Exception as e:
                logger.warning(f"Failed to fetch from {source_name}: {e}")
                continue
        
        logger.error(f"❌ Paper not found for DOI: {doi}")
        return None
    
    async def _fetch_from_crossref(self, doi: str) -> Optional[Dict[str, Any]]:
        """Fetch from Crossref API (metadata only, no PDF)"""
        url = f"https://api.crossref.org/works/{doi}"
        
        response = await self.client.get(url)
        response.raise_for_status()
        
        data = response.json()
        message = data.get("message", {})
        
        # Extract metadata
        paper = {
            "title": message.get("title", [""])[0],
            "abstract": message.get("abstract", ""),
            "authors": self._parse_crossref_authors(message.get("author", [])),
            "publication_date": self._parse_crossref_date(message.get("published")),
            "journal": message.get("container-title", [""])[0],
            "publisher": message.get("publisher", ""),
            "citation_count": message.get("is-referenced-by-count", 0),
            "url": message.get("URL", ""),
            "pdf_url": None,  # Crossref doesn't provide PDF links
            "metadata": {
                "volume": message.get("volume"),
                "issue": message.get("issue"),
                "page": message.get("page"),
                "issn": message.get("ISSN", []),
                "subject": message.get("subject", []),
            }
        }
        
        return paper
    
    async def _fetch_from_unpaywall(self, doi: str) -> Optional[Dict[str, Any]]:
        """Fetch from Unpaywall API (includes open access PDF links)"""
        # Unpaywall requires an email in the query
        email = "your-email@example.com"  # TODO: Make this configurable
        url = f"https://api.unpaywall.org/v2/{doi}?email={email}"
        
        response = await self.client.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        # Get best OA location (open access PDF)
        best_oa = data.get("best_oa_location", {})
        
        paper = {
            "title": data.get("title", ""),
            "abstract": data.get("abstract", ""),
            "authors": self._parse_unpaywall_authors(data.get("z_authors", [])),
            "publication_date": self._parse_date(data.get("published_date")),
            "journal": data.get("journal_name", ""),
            "publisher": data.get("publisher", ""),
            "citation_count": 0,  # Unpaywall doesn't provide this
            "url": data.get("doi_url", ""),
            "pdf_url": best_oa.get("url_for_pdf") if best_oa else None,
            "is_open_access": data.get("is_oa", False),
            "oa_status": data.get("oa_status", "closed"),
            "metadata": {
                "year": data.get("year"),
                "genre": data.get("genre"),
                "journal_issns": data.get("journal_issns"),
            }
        }
        
        return paper
    
    async def _fetch_from_semantic_scholar(self, doi: str) -> Optional[Dict[str, Any]]:
        """Fetch from Semantic Scholar API"""
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
        params = {
            "fields": "title,abstract,authors,year,citationCount,openAccessPdf,externalIds,publicationDate,journal"
        }
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Get PDF URL from open access
        pdf_url = None
        if data.get("openAccessPdf"):
            pdf_url = data["openAccessPdf"].get("url")
        
        paper = {
            "title": data.get("title", ""),
            "abstract": data.get("abstract", ""),
            "authors": self._parse_semantic_scholar_authors(data.get("authors", [])),
            "publication_date": self._parse_date(data.get("publicationDate")),
            "journal": data.get("journal", {}).get("name", ""),
            "citation_count": data.get("citationCount", 0),
            "url": f"https://www.semanticscholar.org/paper/{data.get('paperId')}",
            "pdf_url": pdf_url,
            "semantic_scholar_id": data.get("paperId"),
            "metadata": {
                "external_ids": data.get("externalIds", {}),
                "year": data.get("year"),
            }
        }
        
        return paper
    
    # Helper methods for parsing
    
    def _parse_crossref_authors(self, authors: list) -> list:
        """Parse Crossref author format"""
        return [
            {
                "name": f"{a.get('given', '')} {a.get('family', '')}".strip(),
                "affiliation": a.get("affiliation", [{}])[0].get("name") if a.get("affiliation") else None
            }
            for a in authors
        ]
    
    def _parse_unpaywall_authors(self, authors: list) -> list:
        """Parse Unpaywall author format"""
        return [
            {
                "name": a.get("family", "") if isinstance(a, dict) else str(a),
                "affiliation": None
            }
            for a in authors
        ]
    
    def _parse_semantic_scholar_authors(self, authors: list) -> list:
        """Parse Semantic Scholar author format"""
        return [
            {
                "name": a.get("name", ""),
                "author_id": a.get("authorId"),
                "affiliation": None
            }
            for a in authors
        ]
    
    def _parse_crossref_date(self, date_parts: dict) -> Optional[datetime]:
        """Parse Crossref date format"""
        if not date_parts:
            return None
        
        parts = date_parts.get("date-parts", [[]])[0]
        if not parts:
            return None
        
        year = parts[0] if len(parts) > 0 else 1
        month = parts[1] if len(parts) > 1 else 1
        day = parts[2] if len(parts) > 2 else 1
        
        try:
            return datetime(year, month, day)
        except:
            return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO date string"""
        if not date_str:
            return None
        
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return None
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Example usage
async def example_usage():
    """Example of how to use the DOI fetcher"""
    fetcher = DOIFetcherService()
    
    # Fetch paper by DOI
    doi = "10.1038/nature12373"
    paper = await fetcher.fetch_paper_by_doi(doi)
    
    if paper:
        print(f"Title: {paper['title']}")
        print(f"Authors: {', '.join(a['name'] for a in paper['authors'])}")
        print(f"PDF URL: {paper.get('pdf_url', 'Not available')}")
    else:
        print("Paper not found")
    
    await fetcher.close()
