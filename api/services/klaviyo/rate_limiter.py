"""
Rate limiter for Klaviyo API requests.

Based on Klaviyo rate limits:
- Small (S): 3 req/sec, 60/min
- Medium (M): 10 req/sec, 150/min
- Large (L): 75 req/sec, 700/min
- Extra Large (XL): 350 req/sec, 3500/min

Defaults to Medium tier (10 req/sec, 150/min) for safety.
"""
import asyncio
import time
from collections import deque


class RateLimiter:
    """
    Rate limiter for Klaviyo API requests.
    
    Based on Klaviyo rate limits:
    - Small (S): 3 req/sec, 60/min
    - Medium (M): 10 req/sec, 150/min
    - Large (L): 75 req/sec, 700/min
    - Extra Large (XL): 350 req/sec, 3500/min
    
    Defaults to Medium tier (10 req/sec, 150/min) for safety.
    """
    
    def __init__(self, requests_per_second: float = 9.0, requests_per_minute: int = 140):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_second: Max requests per second (default 9, optimized for M tier)
            requests_per_minute: Max requests per minute (default 140, optimized for M tier)
        """
        self.requests_per_second = requests_per_second
        self.requests_per_minute = requests_per_minute
        self.min_interval = 1.0 / requests_per_second  # Minimum time between requests
        
        # Track request timestamps
        self.request_times = deque()  # For per-second tracking
        self.minute_times = deque()   # For per-minute tracking
        
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait until we can make a request without exceeding rate limits."""
        async with self._lock:
            now = time.time()
            
            # Remove old timestamps (older than 1 second)
            while self.request_times and self.request_times[0] < now - 1.0:
                self.request_times.popleft()
            
            # Remove old timestamps (older than 1 minute)
            while self.minute_times and self.minute_times[0] < now - 60.0:
                self.minute_times.popleft()
            
            # Check per-second limit
            if len(self.request_times) >= self.requests_per_second:
                wait_time = 1.0 - (now - self.request_times[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    now = time.time()
                    # Clean up again after waiting
                    while self.request_times and self.request_times[0] < now - 1.0:
                        self.request_times.popleft()
            
            # Check per-minute limit
            if len(self.minute_times) >= self.requests_per_minute:
                wait_time = 60.0 - (now - self.minute_times[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    now = time.time()
                    # Clean up again after waiting
                    while self.minute_times and self.minute_times[0] < now - 60.0:
                        self.minute_times.popleft()
            
            # Record this request
            self.request_times.append(now)
            self.minute_times.append(now)
            
            # Ensure minimum interval between requests
            if len(self.request_times) > 1:
                time_since_last = now - self.request_times[-2]
                if time_since_last < self.min_interval:
                    await asyncio.sleep(self.min_interval - time_since_last)

