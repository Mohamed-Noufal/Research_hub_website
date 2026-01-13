"""
LLM Fallback Handler - Resilient LLM calls with retries and fallbacks
Ensures system stays operational even when primary LLM fails.
"""
from typing import Optional, List, Dict, Any, Callable
import asyncio
import time
import logging
import random

logger = logging.getLogger(__name__)


class LLMFallbackHandler:
    """
    Handles LLM failures with retries and model fallbacks.
    
    Features:
    - Exponential backoff on failures
    - Fallback to secondary model
    - Circuit breaker to prevent cascade failures
    - Request timeout handling
    
    Usage:
        handler = LLMFallbackHandler(
            primary_model="qwen/qwen3-32b",
            fallback_models=["openai/gpt-3.5-turbo"],
            primary_client=groq_client,
            fallback_clients={"openai/gpt-3.5-turbo": openai_client}
        )
        
        response = await handler.complete(prompt)
    """
    
    def __init__(
        self,
        primary_model: str,
        primary_client,
        fallback_models: Optional[List[str]] = None,
        fallback_clients: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        timeout: float = 60.0,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: float = 300.0
    ):
        """
        Args:
            primary_model: Primary model identifier
            primary_client: Primary LLM client
            fallback_models: List of fallback model identifiers
            fallback_clients: Dict mapping model to client
            max_retries: Max retries per model
            base_delay: Initial retry delay (seconds)
            max_delay: Maximum retry delay (seconds)
            timeout: Request timeout (seconds)
            circuit_breaker_threshold: Failures before circuit opens
            circuit_breaker_timeout: Time before circuit closes (seconds)
        """
        self.primary_model = primary_model
        self.primary_client = primary_client
        self.fallback_models = fallback_models or []
        self.fallback_clients = fallback_clients or {}
        
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.timeout = timeout
        
        # Circuit breaker state
        self.cb_threshold = circuit_breaker_threshold
        self.cb_timeout = circuit_breaker_timeout
        self.failure_counts: Dict[str, int] = {}
        self.circuit_open_until: Dict[str, float] = {}
        
        # Stats
        self.stats = {
            "primary_success": 0,
            "primary_failures": 0,
            "fallback_attempts": 0,
            "fallback_success": 0,
            "total_retries": 0
        }
    
    async def complete(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        Complete prompt with retry and fallback logic.
        
        Args:
            prompt: The prompt to complete
            temperature: LLM temperature
            max_tokens: Max response tokens
            **kwargs: Additional LLM parameters
            
        Returns:
            LLM response string
            
        Raises:
            LLMError: If all models fail
        """
        # Try primary model first
        all_models = [self.primary_model] + self.fallback_models
        
        for model in all_models:
            is_primary = model == self.primary_model
            client = self.primary_client if is_primary else self.fallback_clients.get(model)
            
            if not client:
                logger.warning(f"No client for model {model}")
                continue
            
            # Check circuit breaker
            if self._is_circuit_open(model):
                logger.warning(f"Circuit open for {model}, skipping")
                continue
            
            # Try with retries
            result = await self._try_with_retries(
                client=client,
                model=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            if result is not None:
                if is_primary:
                    self.stats["primary_success"] += 1
                else:
                    self.stats["fallback_success"] += 1
                    self.stats["fallback_attempts"] += 1
                
                # Reset failure count on success
                self.failure_counts[model] = 0
                return result
            else:
                if is_primary:
                    self.stats["primary_failures"] += 1
                else:
                    self.stats["fallback_attempts"] += 1
        
        # All models failed
        raise LLMError("All LLM models failed")
    
    async def _try_with_retries(
        self,
        client,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> Optional[str]:
        """Try a single model with exponential backoff retries."""
        
        for attempt in range(self.max_retries):
            try:
                # Call with timeout
                response = await asyncio.wait_for(
                    self._call_llm(client, prompt, temperature, max_tokens, **kwargs),
                    timeout=self.timeout
                )
                return response
                
            except asyncio.TimeoutError:
                logger.warning(f"{model} attempt {attempt + 1} timed out")
                self._record_failure(model)
                
            except RateLimitError as e:
                # Rate limit - wait and retry
                wait_time = getattr(e, 'retry_after', self.base_delay * (2 ** attempt))
                logger.warning(f"{model} rate limited, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
                self.stats["total_retries"] += 1
                
            except Exception as e:
                logger.warning(f"{model} attempt {attempt + 1} failed: {e}")
                self._record_failure(model)
                
                # Exponential backoff with jitter
                if attempt < self.max_retries - 1:
                    delay = min(
                        self.max_delay,
                        self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                    )
                    await asyncio.sleep(delay)
                    self.stats["total_retries"] += 1
        
        return None
    
    async def _call_llm(
        self,
        client,
        prompt: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """Call LLM client (handles different client interfaces)."""
        
        # Try different client interfaces
        if hasattr(client, 'complete'):
            # Our LLMClient interface
            if asyncio.iscoroutinefunction(client.complete):
                return await client.complete(prompt, temperature=temperature, **kwargs)
            else:
                return client.complete(prompt, temperature=temperature, **kwargs)
        
        elif hasattr(client, 'chat'):
            # OpenAI-style interface
            response = await client.chat.completions.create(
                model=kwargs.get('model', 'gpt-3.5-turbo'),
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        
        elif hasattr(client, 'generate'):
            # Generic generate interface
            response = await client.generate(prompt=prompt, temperature=temperature)
            return response
        
        else:
            raise ValueError(f"Unknown LLM client interface: {type(client)}")
    
    def _record_failure(self, model: str):
        """Record failure for circuit breaker."""
        self.failure_counts[model] = self.failure_counts.get(model, 0) + 1
        
        if self.failure_counts[model] >= self.cb_threshold:
            # Open circuit
            self.circuit_open_until[model] = time.time() + self.cb_timeout
            logger.warning(f"Circuit breaker opened for {model}")
    
    def _is_circuit_open(self, model: str) -> bool:
        """Check if circuit breaker is open for model."""
        if model not in self.circuit_open_until:
            return False
        
        if time.time() > self.circuit_open_until[model]:
            # Circuit timeout expired, close it
            del self.circuit_open_until[model]
            self.failure_counts[model] = 0
            logger.info(f"Circuit breaker closed for {model}")
            return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        total = self.stats["primary_success"] + self.stats["primary_failures"] + self.stats["fallback_attempts"]
        return {
            **self.stats,
            "success_rate": (self.stats["primary_success"] + self.stats["fallback_success"]) / max(total, 1) * 100,
            "circuit_status": {
                model: "open" if self._is_circuit_open(model) else "closed"
                for model in [self.primary_model] + self.fallback_models
            }
        }


class LLMError(Exception):
    """Base exception for LLM errors."""
    pass


class RateLimitError(LLMError):
    """Rate limit exceeded."""
    def __init__(self, message: str, retry_after: float = 60.0):
        super().__init__(message)
        self.retry_after = retry_after


def with_fallback(handler: LLMFallbackHandler):
    """
    Decorator to wrap async functions with LLM fallback handling.
    
    Usage:
        @with_fallback(handler)
        async def generate_summary(prompt: str) -> str:
            return await llm.complete(prompt)
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Function {func.__name__} failed: {e}")
                # Try to extract prompt from args/kwargs
                prompt = kwargs.get('prompt') or (args[0] if args else None)
                if prompt and isinstance(prompt, str):
                    return await handler.complete(prompt)
                raise
        return wrapper
    return decorator
