import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add api directory to path
sys.path.append(os.path.join(os.getcwd(), 'api'))

from api.services.klaviyo.client import KlaviyoClient
from api.services.klaviyo.metrics.service import MetricsService
from api.services.klaviyo.metrics.aggregates import MetricAggregatesService
from api.services.klaviyo.utils.date_helpers import get_klaviyo_compatible_range

async def reproduce():
    load_dotenv()
    api_key = os.getenv("KLAVIYO_API_KEY")
    client = KlaviyoClient(api_key)
    metrics_service = MetricsService(client)
    aggregates_service = MetricAggregatesService(client)

    print("--- METRIC DISCOVERY ---")
    
    # Test Timeframe (last 30 days)
    date_range = get_klaviyo_compatible_range(30, "Australia/Sydney")
    print(f"Timeframe: {date_range['start']} to {date_range['end']}")

    # 1. Get all metrics and filter
    all_metrics = await metrics_service.get_metrics()
    candidates = []
    for m in all_metrics:
        name = m.get('attributes', {}).get('name', '')
        if 'Order' in name or 'Revenue' in name:
            candidates.append(m)
    
    print(f"Found {len(candidates)} candidate metrics:")
    for m in candidates:
        name = m.get('attributes', {}).get('name')
        mid = m.get('id')
        integration = m.get('attributes', {}).get('integration', {}).get('name', 'Unknown')
        print(f" - {name} ({mid}) [Integration: {integration}]")
        
        # Query Total for this metric properties
        resp = await aggregates_service.query(
            metric_id=mid,
            start_date=date_range["start"],
            end_date=date_range["end"],
            measurements=["sum_value"],
            interval="day"
        )
        
        # Calculate Sum
        val_sum = 0
        if resp and 'data' in resp:
            data = resp['data'].get('attributes', {}).get('data', [])
            for x in data:
                if isinstance(x, dict):
                    m_val = x.get('measurements', {}).get('sum_value', [])
                    if isinstance(m_val, list) and m_val: val_sum += float(m_val[0] or 0)
                    else: val_sum += float(m_val or 0)
                # handle other formats if needed
        
        print(f"   -> Total (Last 30d): ${val_sum:,.2f}")
        
        # If this looks like the main revenue metric (> 1M), test attribution
        if val_sum > 1000000:
             print("   *** POTENTIAL MATCH - Testing Attribution ***")
             flow_resp = await aggregates_service.query(
                metric_id=mid,
                start_date=date_range["start"],
                end_date=date_range["end"],
                measurements=["sum_value"],
                by=["$attributed_flow"],
                interval="day"
            )
             f_sum = 0
             f_data = flow_resp.get('data', {}).get('attributes', {}).get('data', [])
             for x in f_data:
                # Sum items
                 if isinstance(x, dict):
                     m_val = x.get('measurements', {}).get('sum_value', [])
                     if isinstance(m_val, list) and m_val: f_sum += float(m_val[0] or 0)
                     else: f_sum += float(m_val or 0)
             
             print(f"   -> Flow Attributed: ${f_sum:,.2f}")
             if abs(val_sum - f_sum) < val_sum * 0.05:
                 print("      ⚠️ Attribution Broken (Total ~= Flow)")
             else:
                 print("      ✅ Attribution Likely Working")

if __name__ == "__main__":
    asyncio.run(reproduce())
