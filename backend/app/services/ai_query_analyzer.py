import json
import asyncio
from typing import Dict, Any
from groq import Groq
from app.core.config import settings


class AIQueryAnalyzer:
    """Simple AI-powered query expansion for research paper search"""

    def __init__(self):
        api_key = settings.GROQ_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        self.client = Groq(api_key=api_key)

    async def analyze_and_expand_query(self, user_query: str) -> Dict[str, Any]:
        """
        Generate academic search phrases using simple AI call

        Args:
            user_query: Original user search query

        Returns:
            Dict with generated search queries
        """
        try:
            # Simple AI call - just like your working example
            # Run synchronous Groq call in thread pool
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="qwen/qwen3-32b",  # Switched to Qwen 3 32B
                messages=[{
                    "role": "user",
                    "content": self._create_prompt(user_query)
                }],
                temperature=1,  # Higher temperature for variety
                max_tokens=500
            )

            ai_response = response.choices[0].message.content

            # Parse JSON directly - no complex parsing
            terms = json.loads(ai_response.strip())

            return {
                'original_query': user_query,
                'search_queries': [user_query] + terms,  # Original first, then AI terms
                'method': 'simple_ai'
            }

        except Exception as e:
            # Simple fallback - just return original query
            return {
                'original_query': user_query,
                'search_queries': [user_query],
                'method': 'fallback',
                'error': str(e)
            }

    def _create_prompt(self, user_query: str) -> str:
        """Create prompt for generating academic search suggestions"""
        prompt = f"""You are an expert academic research assistant. A user wants to find research papers about: "{user_query}"

Generate 4 specific, well-formed academic search queries that would help them find relevant papers. Each query should be:

1. Complete and searchable (8-12 words)
2. Academic and technical in tone
3. Focused on different aspects of the topic
4. Suitable for academic databases like Google Scholar, arXiv, PubMed

IMPORTANT: Respond with ONLY a JSON array of 4 strings. No other text.

Example for "machine learning":
[
  "deep learning algorithms for image classification",
  "machine learning techniques in medical diagnosis",
  "neural network architectures for natural language processing",
  "supervised learning methods for predictive modeling"
]

Now generate 4 academic search queries for: "{user_query}"
"""
        return prompt

    async def generate_search_suggestions(
        self,
        context: str,
        category: str = None
    ) -> Dict[str, Any]:
        """
        Generate search query suggestions from research problem description
        
        Args:
            context: Research problem statement and goals
            category: Optional research category
            
        Returns:
            Dict with suggested queries, topics, and metadata
        """
        try:
            # Run synchronous Groq call in thread pool
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="qwen/qwen3-32b",
                messages=[{
                    "role": "user",
                    "content": self._create_suggestion_prompt(context, category)
                }],
                temperature=0.8,
                max_tokens=800
            )

            ai_response = response.choices[0].message.content
            
            # Parse JSON response
            suggestions_data = json.loads(ai_response.strip())
            
            # Format suggestions with relevance scores
            formatted_suggestions = []
            for i, suggestion in enumerate(suggestions_data.get('queries', [])):
                formatted_suggestions.append({
                    'query': suggestion,
                    'category': category or suggestions_data.get('category', 'ai_cs'),
                    'relevance_score': 0.95 - (i * 0.05),  # Decreasing relevance
                    'reasoning': suggestions_data.get('reasoning', [None])[i] if i < len(suggestions_data.get('reasoning', [])) else None
                })
            
            return {
                'queries': formatted_suggestions,
                'topics': suggestions_data.get('topics', []),
                'category': suggestions_data.get('category', category),
                'complexity': suggestions_data.get('complexity', 'medium')
            }

        except Exception as e:
            # Fallback: extract keywords and create basic suggestions
            keywords = context.lower().split()[:10]
            basic_query = ' '.join(keywords[:5])
            
            return {
                'queries': [{
                    'query': basic_query,
                    'category': category or 'ai_cs',
                    'relevance_score': 0.7,
                    'reasoning': 'Basic keyword extraction (AI service unavailable)'
                }],
                'topics': keywords[:5],
                'category': category or 'ai_cs',
                'complexity': 'medium',
                'error': str(e)
            }

    def _create_suggestion_prompt(self, context: str, category: str = None) -> str:
        """Create prompt for generating search suggestions from research problem"""
        category_context = f" in the {category} domain" if category else ""
        
        prompt = f"""You are an expert academic research assistant. A researcher has described their research problem{category_context}:

"{context}"

Based on this description, generate 3-5 specific, well-formed academic search queries that would help them find relevant research papers. Each query should be:

1. Highly relevant to their specific problem
2. Searchable (8-15 words)
3. Academic and technical in tone
4. Focused on different aspects of their research
5. Suitable for academic databases (arXiv, PubMed, Semantic Scholar, etc.)

Also identify:
- Key topics/keywords from their problem
- Suggested research category
- Complexity level (simple/medium/complex)

Respond with ONLY a JSON object in this exact format:
{{
  "queries": ["query 1", "query 2", "query 3"],
  "reasoning": ["why query 1 is relevant", "why query 2 is relevant", "why query 3 is relevant"],
  "topics": ["topic1", "topic2", "topic3"],
  "category": "ai_cs",
  "complexity": "medium"
}}

Example for "I'm studying climate change impact on agriculture in Africa":
{{
  "queries": [
    "climate change impact agricultural productivity sub-Saharan Africa",
    "rainfall variability crop yield Africa adaptation strategies",
    "climate-smart agriculture sub-Saharan Africa policy recommendations"
  ],
  "reasoning": [
    "Directly addresses core problem with geographic specificity",
    "Focuses on specific climate variable and farmer responses",
    "Addresses adaptation strategies and policy aspects"
  ],
  "topics": ["climate change", "agriculture", "Africa", "adaptation", "crop yield"],
  "category": "agriculture_animal",
  "complexity": "medium"
}}

Now generate suggestions for the researcher's problem."""
        
        return prompt

    async def health_check(self) -> bool:
        """Check if AI service is working"""
        try:
            result = await self.analyze_and_expand_query("test query")
            return len(result.get('search_queries', [])) > 1  # Should have original + AI terms
        except Exception:
            return False
