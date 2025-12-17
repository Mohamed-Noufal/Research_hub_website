import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.services.base_source import PaperSource
from app.utils.http_client import AcademicAPIClient
from app.core.config import settings

class PubMedService(PaperSource):
    """PubMed/NCBI service with proper E-utilities implementation"""

    def __init__(self):
        super().__init__()
        self.source_name = "pubmed"
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.db = "pubmed"
        self.api_key = getattr(settings, 'NCBI_API_KEY', None)

        # Rate limits: 3 requests/sec without key, 10 requests/sec with key
        rate_limit = 10.0 if self.api_key else 3.0
        self.client = AcademicAPIClient(
            user_agent="Academic-Search-Bot/1.0 (research@example.com)",
            rate_limit_per_second=rate_limit
        )

    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search PubMed using E-utilities (esearch → efetch pattern)
        """
        try:
            async with self.client:
                # Step 1: ESearch to get PMIDs
                pmids = await self._esearch_pmids(query, limit)
                if not pmids:
                    return []

                # Step 2: EFetch to get paper details
                papers = await self._efetch_papers(pmids)
                return papers[:limit]

        except Exception as e:
            print(f"PubMed search error: {str(e)}")
            return []

    async def _esearch_pmids(self, query: str, limit: int) -> List[str]:
        """Use esearch to get PMIDs for the query."""
        esearch_url = f"{self.base_url}/esearch.fcgi"
        params = {
            "db": self.db,
            "term": query,
            "retmax": min(limit, 100),  # NCBI max is 100,000 but we limit
            "retmode": "json",
            "sort": "relevance"
        }

        # Add API key if available for higher rate limits
        if self.api_key:
            params["api_key"] = self.api_key

        response, data = await self.client.get(esearch_url, params=params)

        # Extract PMIDs from esearch result
        esearch_result = data.get("esearchresult", {})
        pmids = esearch_result.get("idlist", [])

        return pmids

    async def _efetch_papers(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """Use efetch to get detailed paper information."""
        if not pmids:
            return []

        efetch_url = f"{self.base_url}/efetch.fcgi"
        params = {
            "db": self.db,
            "id": ",".join(pmids),
            "retmode": "xml"
        }

        # Add API key if available
        if self.api_key:
            params["api_key"] = self.api_key

        response, xml_text = await self.client.get(efetch_url, params=params)

        # Parse XML response
        papers = []
        try:
            root = ET.fromstring(xml_text)
            
            for article in root.findall('.//PubmedArticle'):
                try:
                    # Extract PMID
                    pmid_elem = article.find('.//PMID')
                    pmid = pmid_elem.text if pmid_elem is not None else None
                    
                    # Extract title
                    title_elem = article.find('.//ArticleTitle')
                    title = title_elem.text if title_elem is not None else f"PubMed Paper {pmid}"
                    
                    # Extract abstract
                    abstract_parts = []
                    for abstract_text in article.findall('.//AbstractText'):
                        if abstract_text.text:
                            abstract_parts.append(abstract_text.text)
                    abstract = " ".join(abstract_parts) if abstract_parts else "No abstract available"
                    
                    # Extract authors
                    authors = []
                    for author in article.findall('.//Author'):
                        last_name = author.find('LastName')
                        fore_name = author.find('ForeName')
                        if last_name is not None and fore_name is not None:
                            authors.append(f"{fore_name.text} {last_name.text}")
                        elif last_name is not None:
                            authors.append(last_name.text)
                    
                    if not authors:
                        authors = ["Unknown Author"]
                    
                    # Extract publication date
                    pub_date = None
                    pub_date_elem = article.find('.//PubDate')
                    if pub_date_elem is not None:
                        year = pub_date_elem.find('Year')
                        month = pub_date_elem.find('Month')
                        day = pub_date_elem.find('Day')
                        
                        if year is not None:
                            year_text = year.text
                            month_text = month.text if month is not None else "01"
                            day_text = day.text if day is not None else "01"
                            
                            # Convert month name to number if needed
                            month_map = {
                                'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                                'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                                'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                            }
                            month_text = month_map.get(month_text, month_text)
                            
                            try:
                                pub_date = f"{year_text}-{month_text.zfill(2)}-{day_text.zfill(2)}"
                            except:
                                pub_date = year_text
                    
                    # Extract DOI
                    doi = None
                    for article_id in article.findall('.//ArticleId'):
                        if article_id.get('IdType') == 'doi':
                            doi = article_id.text
                            break
                    
                    # Extract journal/venue
                    journal_elem = article.find('.//Journal/Title')
                    venue = journal_elem.text if journal_elem is not None else "PubMed"
                    
                    papers.append({
                        "title": title,
                        "abstract": abstract,
                        "authors": authors,
                        "publication_date": pub_date,
                        "pdf_url": None,  # PubMed doesn't provide direct PDFs
                        "source": "pubmed",
                        "source_id": pmid,
                        "doi": doi,
                        "citation_count": 0,
                        "venue": venue,
                        "year": int(pub_date[:4]) if pub_date and len(pub_date) >= 4 else 2024
                    })
                    
                except Exception as e:
                    print(f"Error parsing PubMed article: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error parsing PubMed XML: {e}")
            return []

        return papers

    async def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get single paper by PMID"""
        try:
            async with self.client:
                papers = await self._efetch_papers([paper_id])
                return papers[0] if papers else None
        except Exception as e:
            print(f"PubMed get_paper_by_id error: {str(e)}")
            return None



    def normalize_paper(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert PubMed format to standard schema"""
        return {
            "title": raw_data.get("title", "").strip(),
            "abstract": raw_data.get("abstract", "").strip(),
            "authors": raw_data.get("authors", []),
            "publication_date": self._parse_date(raw_data.get("publication_date")),
            "pdf_url": None,  # PubMed doesn't provide direct PDFs
            "source": "pubmed",
            "source_id": str(raw_data.get("pmid", "")),
            "doi": raw_data.get("doi"),
            "citation_count": 0,  # PubMed doesn't provide citation counts
            "venue": raw_data.get("venue", ""),
            "pmid": raw_data.get("pmid")
        }

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse PubMed date format"""
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
