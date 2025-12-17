from typing import List, Dict, Any

class CategoryService:
    """Service for managing search categories and their sources"""

    def __init__(self):
        self.categories = {
            "ai_cs": {
                "name": "AI & Computer Science",
                "sources": ["arxiv", "openalex", "semantic_scholar"],
                "description": "AI, machine learning, computer vision, NLP",
                "parallel_search": True,
                "fallback_enabled": True
            },
            "medicine_biology": {
                "name": "Medicine & Biology",
                "sources": ["pubmed", "biorxiv", "crossref"],
                "description": "Medical research, clinical studies, biology",
                "parallel_search": True,
                "fallback_enabled": True
            },
            "agriculture_animal": {
                "name": "Agriculture & Animal Science",
                "sources": ["openalex", "core", "doaj"],
                "description": "Agricultural research, animal science, farming",
                "parallel_search": True,
                "fallback_enabled": True
            },
            "humanities_social": {
                "name": "Humanities & Social Sciences",
                "sources": ["core", "base", "doaj"],
                "description": "Psychology, sociology, humanities research",
                "parallel_search": True,
                "fallback_enabled": True
            },
            "economics_business": {
                "name": "Economics & Business",
                "sources": ["doaj", "core", "openalex"],
                "description": "Economics, business, finance research",
                "parallel_search": True,
                "fallback_enabled": True
            }
        }

    def get_category(self, category_id: str) -> Dict[str, Any]:
        """Get category configuration"""
        return self.categories.get(category_id)

    def get_sources_for_category(self, category_id: str) -> List[str]:
        """Get sources for a category"""
        category = self.get_category(category_id)
        return category["sources"] if category else ["openalex"]

    def get_all_categories(self) -> Dict[str, Dict[str, Any]]:
        """Get all categories"""
        return self.categories

    def validate_category(self, category_id: str) -> bool:
        """Check if category exists"""
        return category_id in self.categories

    def get_category_info(self, category_id: str) -> Dict[str, Any]:
        """Get full category information"""
        category = self.get_category(category_id)
        if category:
            return {
                "id": category_id,
                "name": category["name"],
                "description": category["description"],
                "sources": category["sources"],
                "source_count": len(category["sources"])
            }
        return None
