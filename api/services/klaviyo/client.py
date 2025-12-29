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
        # Using Small tier by default for safety to avoid rate limiting
        rate_limits = {
            "small": (2.5, 50),     # Very conservative for S tier: 3/sec, 60/min
            "medium": (8.0, 120),   # Conservative for M tier: 10/sec, 150/min
            "large": (60.0, 600),   # Conservative for L tier: 75/sec, 700/min  
            "xl": (280.0, 3000)     # Conservative for XL tier: 350/sec, 3500/min
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
                    
                    # Check for rate limiting
                    if response.status_code == 429 and retry_on_429 and attempt < max_retries:
                        retry_after = self._extract_retry_after(response)
                        if not retry_after:
                            # More aggressive exponential backoff - shorter waits
                            base_delay = min(2 ** attempt, 10)  # Cap base delay at 10s (was 30s)
                            import random
                            jitter = random.uniform(0.1, 0.3)  # Smaller jitter
                            retry_after = base_delay + jitter
                        else:
                            # Use server-provided retry time, but cap it
                            retry_after = min(retry_after, 15)  # Cap at 15 seconds (was 60s)
                        
                        logger.warning(
                            f"Rate limited. Waiting {retry_after:.1f} seconds before retry "
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
                    # Already handled above, but catch here too
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
    
    def _extract_retry_after(self, response) -> Optional[int]:
        """
        Extract retry-after delay from 429 response.
        
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
        """
        try:
            await self.request("GET", "/accounts/")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}", exc_info=True)
            return False

