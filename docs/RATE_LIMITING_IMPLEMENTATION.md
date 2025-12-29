# Rate Limiting Implementation

## Problem
The Klaviyo API was returning 429 (Too Many Requests) errors when querying multiple flows. We were making too many requests too quickly.

## Solution: Rate Limiter Class

### Klaviyo Rate Limits (from documentation)
- **Small (S)**: 3 requests/second, 60/minute
- **Medium (M)**: 10 requests/second, 150/minute  
- **Large (L)**: 75 requests/second, 700/minute
- **Extra Large (XL)**: 350 requests/second, 3,500/minute

### Implementation

1. **RateLimiter Class**
   - Tracks request timestamps in sliding windows (1 second and 1 minute)
   - Enforces both per-second and per-minute limits
   - Uses asyncio locks for thread safety
   - Defaults to conservative Medium tier (8 req/sec, 120/min)

2. **Integration**
   - All API requests go through `_make_request()` which uses the rate limiter
   - Automatic retry with exponential backoff on 429 errors
   - Extracts retry delay from API response when available

3. **Flow Query Optimization**
   - Limited to 10 flows by default to avoid rate limits
   - Added small delays between flow queries (0.2s)
   - Two-pass approach: identify flows first, then query stats

## Usage

```python
# Default (Medium tier - 8 req/sec, 120/min)
klaviyo = KlaviyoService(api_key="...")

# Custom tier
klaviyo = KlaviyoService(api_key="...", rate_limit_tier="large")
```

## Benefits

1. ✅ Prevents 429 errors by respecting rate limits
2. ✅ Automatic retry with proper backoff
3. ✅ Configurable rate limit tiers
4. ✅ Thread-safe implementation
5. ✅ Efficient sliding window tracking

## Testing

The rate limiter should now prevent most 429 errors. If you still see them:
1. Reduce the rate limit tier (e.g., use "small")
2. Increase delays between requests
3. Reduce the number of flows queried simultaneously

