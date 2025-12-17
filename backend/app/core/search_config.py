"""
Central Configuration for Academic Search System
Defines all sources, categories, and search hierarchies.
"""

from typing import Dict, Any, List
import re


class SearchConfig:
    """Central configuration for all search sources and categories"""

    # Define all available sources
    SOURCES = {
        "arxiv": {
            "name": "arXiv",
            "description": "Computer Science, Physics, Math preprints",
            "api_class": "ArxivService",
            "rate_limit": 100,  # calls per minute
            "reliability": 0.95,
            "speed": "fast",
            "specialties": ["cs", "physics", "math"]
        },
        "semantic_scholar": {
            "name": "Semantic Scholar",
            "description": "AI-powered all-discipline search",
            "api_class": "SemanticScholarService",
            "rate_limit": 100,
            "reliability": 0.90,
            "speed": "medium",
            "specialties": ["all"]
        },
        "openalex": {
            "name": "OpenAlex",
            "description": "Global research database",
            "api_class": "OpenAlexService",
            "rate_limit": 500,
            "reliability": 0.85,
            "speed": "fast",
            "specialties": ["all"]
        },
        "pubmed": {
            "name": "PubMed",
            "description": "Biomedical literature",
            "api_class": "PubMedService",
            "rate_limit": 60,
            "reliability": 0.98,
            "speed": "medium",
            "specialties": ["medicine", "biology"]
        },
        "europe_pmc": {
            "name": "Europe PMC",
            "description": "European biomedical research",
            "api_class": "EuropePMCService",
            "rate_limit": 100,
            "reliability": 0.85,
            "speed": "medium",
            "specialties": ["medicine", "biology"]
        },
        "crossref": {
            "name": "Crossref",
            "description": "DOI resolution and metadata",
            "api_class": "CrossrefService",
            "rate_limit": 500,
            "reliability": 0.90,
            "speed": "fast",
            "specialties": ["all"]
        },
        "core": {
            "name": "CORE",
            "description": "Open access research",
            "api_class": "CoreService",
            "rate_limit": 50,
            "reliability": 0.70,  # Sometimes unreliable
            "speed": "slow",
            "specialties": ["all"]
        },
        "eric": {
            "name": "ERIC",
            "description": "Education research and resources",
            "api_class": "EricService",
            "rate_limit": 100,
            "reliability": 0.85,
            "speed": "medium",
            "specialties": ["education", "social"]
        },
        "biorxiv": {
            "name": "bioRxiv",
            "description": "Biology preprints",
            "api_class": "BiorxivService",
            "rate_limit": 100,
            "reliability": 0.80,
            "speed": "medium",
            "specialties": ["biology", "medicine"]
        }
    }

    # Define categories with source hierarchy
    CATEGORIES = {
        "ai_cs": {
            "name": "AI & Computer Science",
            "description": "Machine learning, AI, computer vision, NLP",
            "sources": {
                "primary": "arxiv",         # 80% success
                "backup": "semantic_scholar", # 15% success
                "fallback": "openalex"       # 5% success
            },
            "keywords": ["machine learning", "deep learning", "AI", "neural network",
                        "computer vision", "NLP", "algorithm", "artificial intelligence",
                        "data science", "reinforcement learning", "convolutional",
                        "transformer", "GPT", "BERT", "large language model"]
        },
        "medicine_biology": {
            "name": "Medicine & Biology",
            "description": "Clinical research, biomedical, healthcare",
            "sources": {
                "primary": "pubmed",
                "backup": "europe_pmc",
                "fallback": "crossref"
            },
            "keywords": ["cancer", "disease", "clinical", "medical", "patient",
                        "treatment", "diagnosis", "therapy", "drug", "vaccine",
                        "genomics", "biotechnology", "molecular biology", "protein",
                        "DNA", "RNA", "gene", "mutation", "clinical trial"]
        },
        "engineering_physics": {
            "name": "Engineering & Physics",
            "description": "Applied sciences, engineering, physics",
            "sources": {
                "primary": "arxiv",
                "backup": "openalex",
                "fallback": "crossref"
            },
            "keywords": ["engineering", "physics", "quantum", "materials",
                        "mechanics", "system", "design", "circuit", "semiconductor",
                        "thermodynamics", "fluid", "dynamics", "control systems",
                        "robotics", "aerospace", "mechanical", "electrical"]
        },
        "agriculture_animal": {
            "name": "Agriculture & Animal Science",
            "description": "Farming, animal science, food security",
            "sources": {
                "primary": "openalex",
                "backup": "core",
                "fallback": "crossref"
            },
            "keywords": ["agriculture", "farming", "livestock", "crop",
                        "animal", "soil", "food", "pesticide", "fertilizer",
                        "breeding", "veterinary", "nutrition", "sustainable",
                        "yield", "pest", "disease", "climate", "water"]
        },
        "humanities_social": {
            "name": "Humanities & Social Sciences",
            "description": "Psychology, sociology, education, humanities",
            "sources": {
                "primary": "eric",
                "backup": "openalex",
                "fallback": "core"
            },
            "keywords": ["psychology", "sociology", "education", "social",
                        "culture", "history", "philosophy", "anthropology",
                        "economics", "political", "policy", "behavior",
                        "learning", "teaching", "curriculum", "pedagogy"]
        },
        "economics_business": {
            "name": "Economics & Business",
            "description": "Economics, finance, business management",
            "sources": {
                "primary": "openalex",
                "backup": "core",
                "fallback": "crossref"
            },
            "keywords": ["economics", "business", "finance", "market",
                        "trade", "management", "investment", "corporate",
                        "entrepreneurship", "strategy", "financial", "economic",
                        "GDP", "inflation", "unemployment", "policy"]
        },
        "general": {
            "name": "General (All Fields)",
            "description": "Cross-disciplinary and general research",
            "sources": {
                "primary": "semantic_scholar",
                "backup": "openalex",
                "fallback": "crossref"
            },
            "keywords": []
        }
    }

    @classmethod
    def auto_detect_category(cls, query: str) -> str:
        """Auto-detect category from query keywords"""
        query_lower = query.lower()

        # Score each category
        scores = {}
        for category_id, category_info in cls.CATEGORIES.items():
            score = sum(1 for keyword in category_info['keywords']
                       if keyword in query_lower)
            scores[category_id] = score

        # Return category with highest score
        best_category = max(scores, key=scores.get)

        # If no keywords match, return general
        if scores[best_category] == 0:
            return "general"

        return best_category

    @classmethod
    def get_source_hierarchy(cls, category: str) -> List[str]:
        """Get source search order for a category"""
        category_info = cls.CATEGORIES.get(category, cls.CATEGORIES["general"])
        sources = category_info['sources']

        return [
            sources['primary'],
            sources['backup'],
            sources['fallback']
        ]

    @classmethod
    def get_category_info(cls, category: str) -> Dict[str, Any]:
        """Get full category information"""
        return cls.CATEGORIES.get(category, cls.CATEGORIES["general"])

    @classmethod
    def get_source_info(cls, source: str) -> Dict[str, Any]:
        """Get source information"""
        return cls.SOURCES.get(source, {})

    @classmethod
    def detect_search_mode(cls, query: str) -> str:
        """Auto-detect if query needs AI or quick search"""
        question_words = ["how", "what", "why", "when", "where", "who", "which",
                         "explain", "describe", "understand", "work", "function"]

        query_lower = query.lower().strip()

        # Check for question patterns
        is_question = (
            any(query_lower.startswith(word) for word in question_words) or
            query_lower.endswith('?') or
            '?' in query_lower
        )

        # Check length (long queries often need AI)
        is_long = len(query.split()) > 6

        # Check for complex academic terms
        complex_terms = ["algorithm", "methodology", "framework", "paradigm",
                        "theory", "model", "approach", "technique", "mechanism"]

        has_complex_terms = any(term in query_lower for term in complex_terms)

        if is_question or is_long or has_complex_terms:
            return "ai"
        return "quick"

    @classmethod
    def get_search_suggestions(cls, query: str) -> Dict[str, Any]:
        """Get search suggestions and mode detection"""
        mode = cls.detect_search_mode(query)
        category = cls.auto_detect_category(query)
        category_info = cls.get_category_info(category)

        suggestions = {
            "query": query,
            "suggested_mode": mode,
            "detected_category": category,
            "category_info": {
                "name": category_info["name"],
                "description": category_info["description"]
            },
            "source_hierarchy": cls.get_source_hierarchy(category),
            "confidence": "high" if mode == "ai" else "medium"
        }

        # Add helpful tips
        if mode == "ai":
            suggestions["tip"] = "AI mode will analyze your query and find the most relevant papers"
            suggestions["reason"] = "Detected as question or complex academic query"
        else:
            suggestions["tip"] = "Quick mode provides fast keyword-based results"
            suggestions["reason"] = "Detected as simple keyword search"

        return suggestions
