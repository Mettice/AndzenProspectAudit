import asyncio
import os
import sys
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

    print("--- REPRODUCTION SCRIPT ---")
    
    # Test Timeframe (last 30 days)
    date_range = get_klaviyo_compatible_range(30, "Australia/Sydney")
    print(f"Timeframe: {date_range['start']} to {date_range['end']}")

    # Metrics to test
    metric_names = ["Ordered Product", "Placed Order"]

    for name in metric_names:
        print(f"\nTesting Metric: {name}")
        metric = await metrics_service.get_metric_by_name(name)
        if not metric:
            print(f"❌ Metric {name} not found")
            continue
        
        metric_id = metric["id"]
        print(f"ID: {metric_id}")

        # 1. Total Revenue
        total_data = await aggregates_service.query(
            metric_id=metric_id,
            start_date=date_range["start"],
            end_date=date_range["end"],
            measurements=["sum_value"],
            interval="day"
        )
        if total_data and 'data' in total_data:
            attributes = total_data['data'].get('attributes', {})
            vals = attributes.get('data', [])
            total_sum = 0
            for x in vals:
                # API response structure varies.
                # If interval=day, x should be a dict with 'measurements'
                # OR if simple, it might be the value itself?
                # Based on time_series.py, it seems it handles both.
                # Let's try robust parsing.
                if isinstance(x, dict):
                    m = x.get('measurements', {}).get('sum_value', [])
                    if isinstance(m, list):
                        total_sum += sum(float(v) for v in m if v is not None)
                    else:
                        total_sum += float(m or 0)
                elif isinstance(x, list) and x:
                    # sometimes simply a list of [val, count, unique]?
                    # If we only requested sum_value...
                    total_sum += float(x[0])
                elif isinstance(x, (int, float)):
                    total_sum += float(x)
            
            print(f"Total Revenue (Fixed Parse): {total_sum}")
        else:
            print(f"Failed to get Total Revenue data: {total_data}")
            total_sum = 0

        # 2. Attribution Flow
        flow_data = await aggregates_service.query(
            metric_id=metric_id,
            start_date=date_range["start"],
            end_date=date_range["end"],
            measurements=["sum_value"],
            by=["$attributed_flow"],
            interval="day"
        )
        
        # Calculate Flow Sum
        flow_sum = 0
        flow_raw_data = flow_data.get('data', {}).get('attributes', {}).get('data', [])
        # Structure: list of items, each has 'groupings' and 'measurements'
        for item in flow_raw_data:
             if isinstance(item, dict):
                 m = item.get('measurements', {}).get('sum_value', [])
                 if isinstance(m, list):
                     flow_sum += sum(float(x) for x in m if x is not None)
                 elif m is not None:
                     flow_sum += float(m)
        
        print(f"Flow Revenue (Sum of attributed): {flow_sum}")
        
        if abs(total_sum - flow_sum) < 1.0:
            print("⚠️  CRITICAL: Flow Revenue == Total Revenue (Bug Reproduced)")
        else:
             print(f"✅ Flow Revenue is subset ({flow_sum} < {total_sum})")

if __name__ == "__main__":
    asyncio.run(reproduce())
