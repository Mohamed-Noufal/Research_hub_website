"""
Production-ready HTTP client with retry logic, rate limiting, and comprehensive error handling.
Used by all academic source services for robust API interactions.
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any, Tuple
import httpx

logger = logging.getLogger(__name__)

class AcademicAPIClient:
    """
    Production-ready HTTP client for academic APIs with:
    - Exponential backoff retry logic
    - Rate limit enforcement
    - Comprehensive error logging
    - Polite headers (User-Agent, mailto)
    """

    def __init__(
        self,
        user_agent: str = "Academic-Search-Bot/1.0 (research@example.com)",
        default_timeout: int = 30,
        max_retries: int = 5,
        backoff_base: float = 0.5,
        rate_limit_per_second: Optional[float] = None
    ):
        """
        Initialize the API client.

        Args:
            user_agent: User-Agent string for polite requests
            default_timeout: Default request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            backoff_base: Base delay for exponential backoff
            rate_limit_per_second: Optional rate limit (requests per second)
        """
        self.user_agent = user_agent
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.rate_limit_per_second = rate_limit_per_second

        # Rate limiting
        self.last_request_time = 0.0
        self.min_interval = 1.0 / rate_limit_per_second if rate_limit_per_second else 0.0

        # Create session with default headers
        self.session = httpx.AsyncClient(
            timeout=default_timeout,
            headers={"User-Agent": user_agent, "Accept": "application/json"}
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()

    async def request_with_retry(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        mailto: Optional[str] = None
    ) -> Tuple[httpx.Response, Any]:
        """
        Make HTTP request with comprehensive retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Additional headers
            params: Query parameters
            data: Form data
            json_data: JSON data
            timeout: Request timeout override
            mailto: Email for polite pool access

        Returns:
            Tuple of (response, parsed_data)
        """
        # Apply rate limiting
        await self._enforce_rate_limit()

        # Prepare headers
        request_headers = headers.copy() if headers else {}
        if mailto and "mailto" not in str(params or {}):
            # Add mailto as query param if not already present
            if params is None:
                params = {}
            params["mailto"] = mailto

        # Prepare timeout
        request_timeout = timeout or self.default_timeout

        attempt = 0
        while attempt <= self.max_retries:
            attempt += 1

            try:
                # Make the request
                response = await self.session.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    params=params,
                    data=data,
                    json=json_data,
                    timeout=request_timeout
                )

                # Log request details for debugging
                logger.debug(f"HTTP {method} {url} -> {response.status_code}")

                # Check for errors
                if response.status_code >= 400:
                    await self._log_error_response(response, attempt, url, method)

                # Success
                if 200 <= response.status_code < 300:
                    try:
                        return response, response.json()
                    except Exception:
                        return response, response.text

                # Handle retryable errors
                if self._is_retryable_error(response.status_code):
                    if attempt <= self.max_retries:
                        delay = self._calculate_backoff_delay(attempt)
                        logger.warning(
                            f"Retryable error {response.status_code} for {method} {url}. "
                            f"Retrying in {delay:.2f}s (attempt {attempt}/{self.max_retries})"
                        )
                        await asyncio.sleep(delay)
                        continue

                # Non-retryable error
                response.raise_for_status()

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning(f"Network error attempt {attempt} for {method} {url}: {e}")
                if attempt <= self.max_retries:
                    delay = self._calculate_backoff_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                raise

        # Should not reach here
        raise RuntimeError(f"Request failed after {self.max_retries} retries")

    async def _enforce_rate_limit(self):
        """Enforce rate limiting between requests."""
        if self.min_interval > 0:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
            self.last_request_time = time.time()

    async def _log_error_response(self, response: httpx.Response, attempt: int, url: str, method: str):
        """Log detailed error information for debugging."""
        try:
            # Try to parse error response
            if response.headers.get("content-type", "").startswith("application/json"):
                error_data = response.json()
                logger.error(
                    f"API Error {response.status_code} (attempt {attempt}): {method} {url}\n"
                    f"Headers: {dict(response.headers)}\n"
                    f"Error Response: {error_data}"
                )
            else:
                error_text = response.text[:1000]  # Limit log size
                logger.error(
                    f"API Error {response.status_code} (attempt {attempt}): {method} {url}\n"
                    f"Headers: {dict(response.headers)}\n"
                    f"Response: {error_text}"
                )
        except Exception as log_error:
            logger.error(
                f"API Error {response.status_code} (attempt {attempt}): {method} {url}\n"
                f"Could not parse error response: {log_error}"
            )

    def _is_retryable_error(self, status_code: int) -> bool:
        """Check if an HTTP status code is retryable."""
        return (
            status_code == 429 or  # Rate limited
            status_code >= 500 or  # Server errors
            status_code in (408, 503, 504)  # Timeout, service unavailable
        )

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        return self.backoff_base * (2 ** (attempt - 1))

    # Convenience methods for common operations
    async def get(self, url: str, **kwargs) -> Tuple[httpx.Response, Any]:
        """GET request with retry logic."""
        return await self.request_with_retry("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> Tuple[httpx.Response, Any]:
        """POST request with retry logic."""
        return await self.request_with_retry("POST", url, **kwargs)
