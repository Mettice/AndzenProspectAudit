"""Test date range calculations."""
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta

# Test 12 months
end = datetime.now(timezone.utc)
start_12m = end - relativedelta(months=12)
print(f"12 months: {start_12m.strftime('%Y-%m-%dT%H:%M:%SZ')} to {end.strftime('%Y-%m-%dT%H:%M:%SZ')}")
print(f"  Days difference: {(end - start_12m).days}")

# Test 90 days
start_90d = end - timedelta(days=90)
print(f"\n90 days: {start_90d.strftime('%Y-%m-%dT%H:%M:%SZ')} to {end.strftime('%Y-%m-%dT%H:%M:%SZ')}")
print(f"  Days difference: {(end - start_90d).days}")

# Check if dates are valid
print(f"\n12 months start is in past: {start_12m < end}")
print(f"90 days start is in past: {start_90d < end}")

