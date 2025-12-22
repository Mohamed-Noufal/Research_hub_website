"""
LLM Client Wrapper for Groq
Handles token counting, cost tracking, and retry logic
"""
import os
import time
import logging
from typing import Optional, Dict, Any
from groq import Groq
import tiktoken
from sqlalchemy.orm import Session
from sqlalchemy import text
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    """Wrapper for Groq API with cost tracking"""
    
    def __init__(self, db: Session = None):
        self.api_key = settings.GROQ_API_KEY
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found in settings")
            
        self.client = Groq(api_key=self.api_key)
        self.db = db
        
        # Pricing (approximate for Llama 3 70B on Groq - verify current rates)
        # Assuming $0.59 per 1M input tokens, $0.79 per 1M output tokens (Example rates)
        self.cost_per_1k_input = 0.00059
        self.cost_per_1k_output = 0.00079
        
        # Tokenizer (using cl100k_base as approximation for Llama 3)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))

    def _log_usage(
        self, 
        model: str, 
        input_tokens: int, 
        output_tokens: int,
        duration_ms: int
    ):
        """Log LLM usage to database if available"""
        if not self.db:
            return
            
        try:
            total_cost = (
                (input_tokens / 1000 * self.cost_per_1k_input) +
                (output_tokens / 1000 * self.cost_per_1k_output)
            )
            
            self.db.execute(
                text("""
                    INSERT INTO llm_usage_logs (
                        model, input_tokens, output_tokens, 
                        total_tokens, cost_usd, duration_ms
                    ) VALUES (
                        :model, :input, :output, 
                        :total, :cost, :duration
                    )
                """),
                {
                    'model': model,
                    'input': input_tokens,
                    'output': output_tokens,
                    'total': input_tokens + output_tokens,
                    'cost': total_cost,
                    'duration': duration_ms
                }
            )
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log LLM usage: {e}")
            # Rollback to prevent transaction errors
            try:
                self.db.rollback()
            except:
                pass

    @retry(
        stop=stop_after_attempt(2),  # Reduced from 3 for production (1 retry only)
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def complete(
        self,
        prompt: str,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.5,
        max_tokens: int = 1024,
        system_prompt: str = "You represent a helpful AI assistant."
    ) -> str:
        """
        Generate completion with retry logic and tracking
        """
        start_time = time.time()
        
        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            # Call Groq API
            # Note: Groq python client is synchronous by default unless using AsyncGroq?
            # Creating async wrapper or using AsyncGroq recommended. 
            # For simplicity using sync call in thread or verify if Groq() supports async.
            # Official lib has AsyncGroq. Let's switch to AsyncGroq if possible or run in executor.
            # Assuming standard Groq client for now, but wrapping in simple async if needed.
            # Actually, `groq` package has `AsyncGroq`. Let's use that for proper async.
            pass 
        except Exception:
            pass

        # Re-initializing for Async support
        from groq import AsyncGroq
        async_client = AsyncGroq(api_key=self.api_key)
        
        try:
            response = await async_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            
            # Calculate metrics
            duration_ms = int((time.time() - start_time) * 1000)
            input_tokens = self.count_tokens(prompt) + self.count_tokens(system_prompt)
            output_tokens = self.count_tokens(content)
            
            # Log usage
            self._log_usage(model, input_tokens, output_tokens, duration_ms)
            
            return content
            
        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            raise e
