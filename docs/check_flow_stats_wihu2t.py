import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add api directory to path
sys.path.append(os.path.join(os.getcwd(), 'api'))

from api.services.klaviyo.client import KlaviyoClient
# from api.services.klaviyo.klaviyo import KlaviyoService # Deprecated/Moved

async def test_flow_stats():
    load_dotenv()
    api_key = os.getenv("KLAVIYO_API_KEY")
    # Initialize Client directly or Orchestrator if needed.
    # But we need specific service methods.
    # Let's verify where get_flow_statistics is. 
    # It is likely in api.services.klaviyo.flows.statistics.
    # But KlaviyoClient might not have it directly if modularized.
    
    # Let's check how Orchestrator initializes.
    # It takes instances of services.
    
    # We need to manually initialize the FlowStatisticsService.
    from api.services.klaviyo.flows.statistics import FlowStatisticsService
    from api.services.klaviyo.flows.service import FlowsService
    
    client = KlaviyoClient(api_key)
    flow_service = FlowsService(client)
    flow_stats_service = FlowStatisticsService(client)

    print("--- TESTING FLOW STATS WITH ORDERED PRODUCT (Wihu2T) ---")
    
    # 1. Get Top Flows (sorted by updated to get active ones)
    # The get_flows service usually supports sorting?
    # Let's manually sort the results just in case service doesn't
    flows = await flow_service.get_flows()
    if not flows:
        print("No flows found.")
        return

    # Sort by updated
    flows.sort(key=lambda x: x.get('attributes', {}).get('updated', ''), reverse=True)
    
    flow_ids = [f["id"] for f in flows[:20]] # Test top 20 RECENT flows
    print(f"Testing {len(flow_ids)} flows (Most recently updated)...")
    for f in flows[:5]:
        print(f" - {f.get('attributes', {}).get('name')} ({f.get('id')})")

    # 2. Get Stats with Ordered Product as Conversion Metric
    metric_id = "Wihu2T" # Ordered Product
    
    stats = await flow_stats_service.get_statistics(
        flow_ids=flow_ids,
        timeframe="last_30_days",
        conversion_metric_id=metric_id, # Ordered Product
        statistics=["conversion_value"] # Correct statistic name for revenue
    )
    
    # print(f"DEBUG: Stats Response for Ordered Product: {stats}")
    # 3. Analyze Results
    total_flow_revenue = 0
    if stats and 'results' in stats: # Check structure returned by modular service
        # statistics.py likely returns valid data structure
        # Let's inspect ONE item
        # print("Sample Item:", stats['results'][0] if len(stats.get('results',[])) > 0 else "None")
        
        # New modular service might return different structure than raw API
        # Usually: List of flow data
        
        for item in stats.get('results', []):
            # item structure?
            # Assuming standard API response structure or simplified?
            # Let's print keys of first item
            
            # The service.get_statistics might wrapper things?
            # Let's assume it returns the "data" part of API response or similar
            
            # If standard API: item has 'attributes' -> 'results'
            attrs = item.get('attributes', {})
            results = attrs.get('results', [])
            
            # If service simplified it:
            if 'revenue' in item:
                 val = float(item['revenue'])
                 # But we requested generic stats? No, service.get_statistics probably has defaults?
            
            # Let's assume standard API structure for now as we didn't check service implementation details
            val = 0
            for r in results:
                if r.get('statistic') == 'conversion_value':
                    val = float(r.get('value', 0))
                    break
            
            total_flow_revenue += val
            flow_id = item.get('id')
            if val > 0:
                print(f"Flow {flow_id}: ${val:,.2f}")
    
    print("-" * 50)
    print(f"Total Flow Revenue (Ordered Product, Top 20): ${total_flow_revenue:,.2f}")
    
    # Compare with Placed Order?
    print("\n--- COMPARISON WITH PLACED ORDER (U7yLfB) ---")
    stats_po = await flow_stats_service.get_statistics(
        flow_ids=flow_ids,
        timeframe="last_30_days",
        conversion_metric_id="U7yLfB", # Placed Order
        statistics=["conversion_value"]
    )
    total_po = 0
    if stats_po and 'results' in stats_po:
         for item in stats_po.get('results', []):
            results = item.get('attributes', {}).get('results', [])
            val = 0
            for r in results:
                if r.get('statistic') == 'conversion_value':
                     val = float(r.get('value', 0))
                     break
            total_po += val
    
    print(f"Total Flow Revenue (Placed Order, Top 20): ${total_po:,.2f}")


if __name__ == "__main__":
    asyncio.run(test_flow_stats())
