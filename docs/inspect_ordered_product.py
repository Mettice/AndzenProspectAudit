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

async def inspect():
    load_dotenv()
    api_key = os.getenv("KLAVIYO_API_KEY")
    client = KlaviyoClient(api_key)
    aggregates_service = MetricAggregatesService(client)

    metric_id = "Wihu2T" # Ordered Product
    print(f"Inspecting Ordered Product ({metric_id})")
    
    date_range = get_klaviyo_compatible_range(30, "Australia/Sydney")
    
    results = {
        "metric_id": metric_id,
        "queries": {}
    }

    # Helper for robust parsing
    def safe_parse_sum(data_list):
        total = 0
        for item in data_list:
            try:
                # Case 1: item is a list (e.g., [value, count, unique])
                if isinstance(item, list):
                    if len(item) > 0 and item[0] is not None:
                        # Value might be nested list?
                        if isinstance(item[0], list):
                             total += float(item[0][0]) if item[0] else 0
                        else:
                             total += float(item[0])
                # Case 2: item is a dict (measurements)
                elif isinstance(item, dict):
                    m = item.get('measurements', {}).get('sum_value', 0)
                    if isinstance(m, list):
                        # Sum values in list
                        total += sum(float(v) for v in m if v is not None)
                    elif m is not None:
                        total += float(m)
                # Case 3: item is direct value
                elif isinstance(item, (int, float)):
                    total += float(item)
            except Exception as e:
                # print(f"Parse error for item {item}: {e}")
                pass
        return total

    # 1. Total
    total_resp = await aggregates_service.query(
        metric_id=metric_id,
        start_date=date_range["start"],
        end_date=date_range["end"],
        measurements=["sum_value"],
        interval="day"
    )
    s = 0
    if total_resp and 'data' in total_resp:
        data = total_resp['data'].get('attributes', {}).get('data', [])
        s = safe_parse_sum(data)
    results["queries"]["total"] = s

    # 2. Group by $attributed_flow
    flow_resp = await aggregates_service.query(
        metric_id=metric_id,
        start_date=date_range["start"],
        end_date=date_range["end"],
        measurements=["sum_value"],
        by=["$attributed_flow"],
        interval="day"
    )
    s_flow = 0
    print("\n--- ATTRIBUTED FLOW GROUPS ---")
    if flow_resp and 'data' in flow_resp:
         data = flow_resp['data'].get('attributes', {}).get('data', [])
         for x in data:
             # Get group key
             groupings = x.get('groupings', {})
             # Print raw groupings to debug
             # print(f"DEBUG: {groupings}")
             
             flow_id = groupings.get('$attributed_flow') # None if missing
             
             # Calculate value for this group
             val = 0
             if isinstance(x, dict):
                 m = x.get('measurements', {}).get('sum_value', 0)
                 if isinstance(m, list):
                     val = sum(float(v) for v in m if v is not None)
                 elif m is not None:
                     val = float(m)
             
             if flow_id:
                 print(f"✅ Flow ID: '{flow_id}' -> Revenue: ${val:,.2f}")
                 s_flow += val
             else:
                 # Unattributed
                 # print(f"  (Skipping Unattributed - Missing Key) -> ${val:,.2f}")
                 pass
                 
    results["queries"]["by_attributed_flow"] = s_flow
    print(f"Corrected Flow Revenue Sum (Strict Filter): ${s_flow:,.2f}")
                 
    results["queries"]["by_attributed_flow"] = s_flow
    print(f"Corrected Flow Revenue Sum: ${s_flow:,.2f}")

    # 3. Group by $attributed_message
    msg_resp = await aggregates_service.query(
        metric_id=metric_id,
        start_date=date_range["start"],
        end_date=date_range["end"],
        measurements=["sum_value"],
        by=["$attributed_message"],
        interval="day"
    )
    s_msg = 0
    if msg_resp and 'data' in msg_resp:
         data = msg_resp['data'].get('attributes', {}).get('data', [])
         s_msg = safe_parse_sum(data)
    results["queries"]["by_attributed_message"] = s_msg

    # 4. Group by $flow (legacy?)
    legacy_flow_resp = await aggregates_service.query(
        metric_id=metric_id,
        start_date=date_range["start"],
        end_date=date_range["end"],
        measurements=["sum_value"],
        by=["$flow"],
        interval="day"
    )
    s_lflow = 0
    if legacy_flow_resp and 'data' in legacy_flow_resp:
         data = legacy_flow_resp['data'].get('attributes', {}).get('data', [])
         s_lflow = safe_parse_sum(data)
    results["queries"]["by_flow"] = s_lflow

    with open("inspection_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("Results saved to inspection_results.json")

if __name__ == "__main__":
    asyncio.run(inspect())
