"""
Base HTTP client for Klaviyo API.

Handles:
- HTTP requests with rate limiting
- Retry logic with exponential backoff
- Error handling
- Authentication headers
"""
import httpx
import asyncio
import re
import logging
from typing import Dict, Optional, Any
from httpx import HTTPStatusError

from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class KlaviyoClient:
    """
    Base HTTP client with rate limiting and retry logic.
    
    This is the foundation for all Klaviyo API interactions.
    All service modules use this client for making requests.
    """
    
    BASE_URL = "https://a.klaviyo.com/api"
    
    def __init__(self, api_key: str, rate_limit_tier: str = "medium"):
        """
        Initialize Klaviyo client.
        
        Args:
            api_key: Klaviyo API key
            rate_limit_tier: Rate limit tier - "small", "medium", "large", "xl"
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Klaviyo-API-Key {api_key}",
            "revision": "2025-10-15",
            "accept": "application/vnd.api+json",
            "Content-Type": "application/json"
        }
        
        # Initialize rate limiter based on tier (Updated 2025)
        # Using optimized rates: 80% of limit for safety margin
        # Klaviyo limits: S=3/60, M=10/150, L=75/700, XL=350/3500
        rate_limits = {
            "small": (2.4, 48),     # 80% of S tier: 2.4/sec, 48/min (limit: 3/sec, 60/min)
            "medium": (8.0, 120),   # 80% of M tier: 8/sec, 120/min (limit: 10/sec, 150/min)
            "large": (60.0, 560),   # 80% of L tier: 60/sec, 560/min (limit: 75/sec, 700/min)
            "xl": (280.0, 2800)     # 80% of XL tier: 280/sec, 2800/min (limit: 350/sec, 3500/min)
        }
        
        rps, rpm = rate_limits.get(rate_limit_tier.lower(), rate_limits["small"])
        self.rate_limiter = RateLimiter(requests_per_second=rps, requests_per_minute=rpm)
    
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retry_on_429: bool = True,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Klaviyo API with rate limiting.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/metrics/")
            params: Query parameters
            data: Request body (will be JSON encoded)
            retry_on_429: Whether to retry on rate limit errors
            max_retries: Maximum number of retries for 429 errors
            
        Returns:
            JSON response as dict
            
        Raises:
            HTTPStatusError: If request fails after all retries
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        # Wait for rate limiter
        await self.rate_limiter.acquire()
        
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=self.headers,
                        params=params,
                        json=data
                    )
                    
                    # Parse and use Klaviyo rate limit headers (if available)
                    self._update_rate_limits_from_headers(response)
                    
                    # Check for rate limiting
                    if response.status_code == 429 and retry_on_429 and attempt < max_retries:
                        # Use Retry-After header (Klaviyo provides this on 429 errors)
                        retry_after = self._extract_retry_after_from_header(response)
                        if not retry_after:
                            # Fallback: try to extract from JSON body
                            retry_after = self._extract_retry_after(response)
                        if not retry_after:
                            # Exponential backoff as last resort
                            base_delay = min(2 ** attempt, 10)
                            import random
                            jitter = random.uniform(0.1, 0.3)
                            retry_after = base_delay + jitter
                        
                        # Use server-provided retry time (don't cap it - Klaviyo knows best)
                        logger.warning(
                            f"Rate limited (429). Waiting {retry_after:.1f} seconds (from Retry-After header) before retry "
                            f"{attempt + 1}/{max_retries}..."
                        )
                        await asyncio.sleep(retry_after)
                        
                        # Wait for rate limiter again before retry
                        await self.rate_limiter.acquire()
                        continue
                    
                    response.raise_for_status()
                    return response.json()
                    
            except HTTPStatusError as e:
                # Don't retry 400 errors (bad request) - they won't succeed on retry
                if e.response.status_code == 400:
                    raise  # Fail immediately for bad requests
                if e.response.status_code == 429 and retry_on_429 and attempt < max_retries:
                    # Extract Retry-After from header
                    retry_after = self._extract_retry_after_from_header(e.response)
                    if not retry_after:
                        retry_after = self._extract_retry_after(e.response)
                    if not retry_after:
                        retry_after = min(2 ** attempt, 10)
                    
                    logger.warning(
                        f"Rate limited (429). Waiting {retry_after:.1f} seconds before retry "
                        f"{attempt + 1}/{max_retries}..."
                    )
                    await asyncio.sleep(retry_after)
                    await self.rate_limiter.acquire()
                    continue
                # For other errors (5xx), retry if we have attempts left
                if e.response.status_code >= 500 and attempt < max_retries:
                    wait_time = min(2 ** attempt, 5)  # Short wait for server errors
                    logger.warning(f"Server error {e.response.status_code}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    await self.rate_limiter.acquire()
                    continue
                raise
        
        # If we get here, all retries failed
        raise HTTPStatusError("Rate limit exceeded after all retries", request=None, response=None)
    
    def _extract_retry_after_from_header(self, response) -> Optional[int]:
        """
        Extract Retry-After delay from HTTP header (Klaviyo provides this on 429 errors).
        
        Args:
            response: HTTP response object
            
        Returns:
            Retry delay in seconds, or None if not found
        """
        try:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                return int(retry_after)
        except (ValueError, TypeError):
            pass
        return None
    
    def _update_rate_limits_from_headers(self, response):
        """
        Update rate limiter based on Klaviyo RateLimit headers.
        
        Klaviyo provides these headers on all non-429 responses:
        - RateLimit-Limit: The number of requests allowed per time period
        - RateLimit-Remaining: The approximate number of requests remaining within a window
        - RateLimit-Reset: Number of seconds remaining before current window resets
        
        We use these to dynamically adjust our rate limiting to match Klaviyo's actual limits.
        """
        try:
            # Get rate limit headers
            limit = response.headers.get("RateLimit-Limit")
            remaining = response.headers.get("RateLimit-Remaining")
            reset = response.headers.get("RateLimit-Reset")
            
            if limit and remaining and reset:
                limit_int = int(limit)
                remaining_int = int(remaining)
                reset_int = int(reset)
                
                # If we're running low on remaining requests, slow down
                # Calculate requests per minute from limit
                # Klaviyo uses 1-minute windows for steady rate limits
                if remaining_int < limit_int * 0.2:  # Less than 20% remaining
                    # Slow down by increasing minimum interval
                    # Reduce to 50% of normal rate when low on quota
                    self.rate_limiter.requests_per_minute = max(
                        int(limit_int * 0.5),  # Use 50% of limit when low
                        remaining_int  # But never less than remaining
                    )
                    logger.debug(
                        f"Rate limit low ({remaining_int}/{limit_int} remaining). "
                        f"Reduced to {self.rate_limiter.requests_per_minute} req/min"
                    )
                elif remaining_int > limit_int * 0.5:  # More than 50% remaining
                    # We have plenty of quota, can use normal rate
                    # Reset to configured rate (80% of limit)
                    original_rpm = int(limit_int * 0.8)
                    if self.rate_limiter.requests_per_minute < original_rpm:
                        self.rate_limiter.requests_per_minute = original_rpm
                        logger.debug(f"Rate limit healthy. Reset to {original_rpm} req/min")
        except (ValueError, TypeError, AttributeError) as e:
            # Headers not available or invalid - that's okay, use defaults
            pass
    
    def _extract_retry_after(self, response) -> Optional[int]:
        """
        Extract retry-after delay from 429 response JSON body (fallback).
        
        Args:
            response: HTTP response object
            
        Returns:
            Retry delay in seconds, or None if not found
        """
        try:
            error_data = response.json()
            error_detail = error_data.get("errors", [{}])[0]
            retry_after = error_detail.get("meta", {}).get("retry_after")
            if not retry_after:
                # Try to parse from detail message
                detail = error_detail.get("detail", "")
                if "Expected available in" in detail:
                    match = re.search(r'(\d+) seconds?', detail)
                    if match:
                        return int(match.group(1))
        except Exception:
            pass
        return None
    
    async def test_connection(self) -> bool:
        """
        Test API connection.
        
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            HTTPStatusError: If there's a specific HTTP error (401, 403, etc.)
        """
        try:
            await self.request("GET", "/accounts/")
            return True
        except HTTPStatusError as e:
            # Re-raise HTTP errors so we can provide better error messages
            logger.error(f"Connection test failed with HTTP {e.response.status_code}: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Connection test failed: {e}", exc_info=True)
            return False

