from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
from app.services.base_source import PaperSource
from app.utils.http_client import AcademicAPIClient

class bioRxivService(PaperSource):
    """bioRxiv preprint server service with interval pagination"""

    def __init__(self):
        super().__init__()
        self.source_name = "biorxiv"
        self.base_url = "https://api.biorxiv.org"

        # Use conservative rate limiting to avoid being blocked
        self.client = AcademicAPIClient(
            user_agent="Academic-Search-Bot/1.0 (research@example.com)",
            rate_limit_per_second=1.0  # Conservative: 1 request per second
        )

    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search bioRxiv preprints using date range pagination patterns
        """
        try:
            # Use date range format: get papers from last 90 days
            # Calculate date range
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)

            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            cursor = 0  # Start from beginning
            collected_papers = []

            while len(collected_papers) < limit * 2:  # Get more for filtering
                # Use details endpoint with date range: server/start_date/end_date/cursor
                url = f"{self.base_url}/details/biorxiv/{start_str}/{end_str}/{cursor}"

                # Make request without closing client
                response, data = await self.client.request_with_retry("GET", url)

                collection = data.get('collection', [])
                if not collection:
                    break  # No more results

                # Process this batch
                for item in collection:
                    # Filter by query relevance using title and abstract
                    if self._matches_query(item, query):
                        paper = self.normalize_paper(item)
                        if paper:
                            collected_papers.append(paper)

                # Check for cursor/count for next page
                messages = data.get('messages', [])
                if messages:
                    # Parse cursor from messages array
                    for msg in messages:
                        if 'cursor' in msg:
                            cursor = msg['cursor']
                            break
                    else:
                        break  # No cursor found, end pagination
                else:
                    break  # No messages, end pagination

                # Safety check to prevent infinite loops
                if cursor == 0:
                    break

            # Sort by relevance and return top results
            collected_papers.sort(key=lambda x: self._calculate_relevance_score(x, query), reverse=True)
            return collected_papers[:limit]

        except Exception as e:
            print(f"bioRxiv search error: {e}")
            return []

    async def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get single paper by DOI"""
        try:
            url = f"{self.base_url}/details/biorxiv/{paper_id}/na/json"

            response, data = await self.client.request_with_retry("GET", url)

            if data.get('collection'):
                return self.normalize_paper(data['collection'][0])

        except Exception as e:
            print(f"bioRxiv get_paper_by_id error: {e}")

        return None

    def normalize_paper(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert bioRxiv format to standard schema"""
        return {
            "title": raw_data.get("title", "").strip(),
            "abstract": raw_data.get("abstract", "").strip(),
            "authors": self._parse_authors(raw_data.get("authors", [])),
            "publication_date": self._parse_date(raw_data.get("date")),
            "pdf_url": f"https://www.biorxiv.org/content/{raw_data.get('doi', '')}.full.pdf" if raw_data.get('doi') else None,
            "source": "biorxiv",
            "source_id": raw_data.get("doi", ""),
            "doi": raw_data.get("doi"),
            "citation_count": 0,  # bioRxiv preprints don't have citations
            "venue": "bioRxiv",
            "category": raw_data.get("category", ""),
            "server": raw_data.get("server", "biorxiv")
        }

    def _matches_query(self, item: Dict, query: str) -> bool:
        """Check if paper matches query using text similarity"""
        query_lower = query.lower()

        # Check title
        title = item.get("title", "").lower()
        if query_lower in title:
            return True

        # Check abstract
        abstract = item.get("abstract", "").lower()
        if query_lower in abstract:
            return True

        # Check category relevance for medicine/biology
        category = item.get("category", "").lower()
        if any(term in category for term in ["biology", "medicine", "health", "clinical", "biomedical"]):
            # For medical queries, include relevant categories
            if any(term in query_lower for term in ["medical", "health", "clinical", "disease", "treatment"]):
                return True

        return False

    def _calculate_relevance_score(self, paper: Dict, query: str) -> float:
        """Calculate relevance score for sorting"""
        score = 0.0
        query_lower = query.lower()

        # Title matches get highest score
        if query_lower in paper.get("title", "").lower():
            score += 1.0

        # Abstract matches get medium score
        if query_lower in paper.get("abstract", "").lower():
            score += 0.5

        # Recent papers get slight boost
        if paper.get("publication_date"):
            days_old = (datetime.now() - paper["publication_date"]).days
            recency_boost = max(0, 1 - (days_old / 365))  # Linear decay over 1 year
            score += recency_boost * 0.1

        return score

    def _parse_authors(self, authors_data) -> List[str]:
        """Parse authors from bioRxiv format"""
        if isinstance(authors_data, list):
            return [author.get("name", "") for author in authors_data if author.get("name")]
        return []

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse bioRxiv date format"""
        if not date_str:
            return None

        try:
            # Format: "2023-10-15"
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None
