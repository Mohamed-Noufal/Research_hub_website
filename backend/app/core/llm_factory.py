"""
LLM Client Factory - Creates LLM clients based on model selection
Supports multiple providers with unified interface.
"""
from typing import Optional, Any
import os
import logging

from app.core.model_config import ModelConfig, ModelProvider, get_model_by_id, get_default_model

logger = logging.getLogger(__name__)


class UnifiedLLMClient:
    """
    Unified LLM client that supports multiple providers.
    
    Usage:
        client = UnifiedLLMClient.from_model_id("groq/qwen3-32b")
        response = await client.complete("Hello!")
    """
    
    def __init__(self, model_config: ModelConfig, raw_client: Any):
        self.config = model_config
        self.client = raw_client
        self.total_input_tokens = 0
        self.total_output_tokens = 0
    
    async def complete(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        Complete a prompt using the configured model.
        
        Args:
            prompt: The prompt to complete
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            
        Returns:
            Model response string
        """
        provider = self.config.provider
        
        if provider == ModelProvider.GROQ:
            return await self._complete_groq(prompt, temperature, max_tokens)
        elif provider == ModelProvider.TOGETHER:
            return await self._complete_together(prompt, temperature, max_tokens)
        elif provider == ModelProvider.OPENAI:
            return await self._complete_openai(prompt, temperature, max_tokens)
        elif provider == ModelProvider.GOOGLE:
            return await self._complete_google(prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _complete_groq(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Groq API completion."""
        response = self.client.chat.completions.create(
            model=self.config.id,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        self._track_usage(response.usage)
        return response.choices[0].message.content
    
    async def _complete_together(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Together AI completion."""
        response = self.client.chat.completions.create(
            model=self.config.id,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        self._track_usage(response.usage)
        return response.choices[0].message.content
    
    async def _complete_openai(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """OpenAI completion."""
        response = self.client.chat.completions.create(
            model=self.config.id,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        self._track_usage(response.usage)
        return response.choices[0].message.content
    
    async def _complete_google(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Google Gemini completion using new google-genai SDK (2025+)."""
        # New SDK: use client.models.generate_content
        response = self.client.models.generate_content(
            model=self.config.id,
            contents=prompt,
            config={
                "temperature": temperature,
                "max_output_tokens": max_tokens
            }
        )
        # Track usage if available
        if hasattr(response, 'usage_metadata'):
            self.total_input_tokens += getattr(response.usage_metadata, 'prompt_token_count', 0)
            self.total_output_tokens += getattr(response.usage_metadata, 'candidates_token_count', 0)
        return response.text
    
    def _track_usage(self, usage: Any):
        """Track token usage for cost estimation."""
        if usage:
            self.total_input_tokens += getattr(usage, 'prompt_tokens', 0)
            self.total_output_tokens += getattr(usage, 'completion_tokens', 0)
    
    def get_usage_stats(self) -> dict:
        """Get usage statistics."""
        from app.core.model_config import estimate_cost
        return {
            "model": self.config.id,
            "provider": self.config.provider.value,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "estimated_cost": estimate_cost(
                f"{self.config.provider.value}/{self.config.id.split('/')[-1]}",
                self.total_input_tokens,
                self.total_output_tokens
            )
        }


class LLMClientFactory:
    """
    Factory for creating LLM clients.
    
    Usage:
        factory = LLMClientFactory()
        client = factory.create("groq/qwen3-32b")
        # or
        client = factory.create_default()
    """
    
    _clients: dict = {}  # Cache for reusing clients
    
    @classmethod
    def create(cls, model_id: str) -> UnifiedLLMClient:
        """
        Create LLM client for specified model.
        
        Args:
            model_id: Model identifier (e.g., "groq/qwen3-32b")
            
        Returns:
            UnifiedLLMClient instance
            
        Raises:
            ValueError: If model not found or API key missing
        """
        # Check cache
        if model_id in cls._clients:
            return cls._clients[model_id]
        
        # Get model config
        config = get_model_by_id(model_id)
        if not config:
            raise ValueError(f"Unknown model: {model_id}")
        
        # Get API key
        api_key = os.getenv(config.requires_api_key)
        if not api_key:
            raise ValueError(f"Missing API key: {config.requires_api_key}")
        
        # Create provider-specific client
        raw_client = cls._create_raw_client(config.provider, api_key)
        
        # Wrap in unified client
        client = UnifiedLLMClient(config, raw_client)
        cls._clients[model_id] = client
        
        return client
    
    @classmethod
    def create_default(cls) -> UnifiedLLMClient:
        """Create client for default model."""
        default = get_default_model()
        model_id = f"{default.provider.value}/{default.id.split('/')[-1]}"
        return cls.create(model_id)
    
    @classmethod
    def _create_raw_client(cls, provider: ModelProvider, api_key: str) -> Any:
        """Create raw provider client."""
        
        if provider == ModelProvider.GROQ:
            from groq import Groq
            return Groq(api_key=api_key)
        
        elif provider == ModelProvider.TOGETHER:
            from together import Together
            return Together(api_key=api_key)
        
        elif provider == ModelProvider.OPENAI:
            from openai import OpenAI
            return OpenAI(api_key=api_key)
        
        elif provider == ModelProvider.GOOGLE:
            # New google-genai SDK (2025+) - replaces deprecated google-generativeai
            from google import genai
            return genai.Client(api_key=api_key)
        
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    @classmethod
    def clear_cache(cls):
        """Clear client cache."""
        cls._clients.clear()


# ==================== CONVENIENCE FUNCTIONS ====================

def get_llm_client(model_id: Optional[str] = None) -> UnifiedLLMClient:
    """
    Get LLM client (convenience function).
    
    Args:
        model_id: Optional model ID, uses default if not specified
    """
    if model_id:
        return LLMClientFactory.create(model_id)
    return LLMClientFactory.create_default()
