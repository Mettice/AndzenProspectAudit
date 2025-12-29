#!/usr/bin/env python3
"""
Debug script to understand why we're getting $233k instead of A$2.4M in revenue.
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timezone, timedelta

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add api directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from api.services.klaviyo.client import KlaviyoClient
from api.services.klaviyo.metrics.service import MetricsService
from api.services.klaviyo.metrics.aggregates import MetricAggregatesService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def debug_revenue_gap():
    """Debug why we're getting $233k instead of A$2.4M."""
    
    api_key = os.getenv("KLAVIYO_API_KEY")
    if not api_key:
        print("❌ KLAVIYO_API_KEY not set")
        return
    
    print("🔍 DEBUGGING REVENUE GAP: $233k vs A$2.4M")
    print("=" * 60)
    
    client = KlaviyoClient(api_key)
    metrics_service = MetricsService(client)
    aggregates_service = MetricAggregatesService(client)
    
    # Dashboard period: Oct 21 - Dec 21, 2025
    start_date = "2025-10-21T00:00:00Z"
    end_date = "2025-12-21T23:59:59Z"
    
    try:
        print(f"📅 Period: {start_date} to {end_date}")
        print(f"🎯 Target: A$2,460,774.32 attributed (Dashboard)")
        print(f"💰 Current: $233,324.93 (Our API)")
        print()
        
        # 1. Check all available metrics
        print("🔍 STEP 1: Available Revenue Metrics")
        print("-" * 40)
        metrics = await metrics_service.get_metrics()
        revenue_metrics = [m for m in metrics if any(term in m.get('attributes', {}).get('name', '').lower() 
                          for term in ['revenue', 'order', 'placed', 'purchase', 'checkout', 'value'])]
        
        print(f"Found {len(revenue_metrics)} revenue-related metrics:")
        for metric in revenue_metrics[:10]:  # Show first 10
            name = metric.get('attributes', {}).get('name', 'Unknown')
            metric_id = metric.get('id', 'No ID')
            print(f"  • {name} ({metric_id})")
        
        # 2. Test different revenue metrics
        print(f"\n🧪 STEP 2: Testing Different Revenue Metrics")
        print("-" * 40)
        
        test_metrics = [
            "Placed Order",
            "Ordered Product", 
            "Checkout Started",
            "Active on Site"
        ]
        
        for metric_name in test_metrics:
            try:
                metric = await metrics_service.get_metric_by_name(metric_name)
                if metric:
                    metric_id = metric.get('id')
                    print(f"\n📊 Testing: {metric_name} ({metric_id})")
                    
                    # Query aggregates
                    result = await aggregates_service.query(
                        metric_id=metric_id,
                        start_date=start_date,
                        end_date=end_date,
                        measurements=["sum_value", "count"],
                        timezone="Australia/Sydney"
                    )
                    
                    # Parse results
                    data = result.get('data', {}).get('attributes', {}).get('data', [])
                    total_revenue = 0
                    total_orders = 0
                    
                    if data and len(data) == 1 and isinstance(data[0], dict):
                        measurements = data[0].get('measurements', {})
                        sum_values = measurements.get('sum_value', [])
                        count_values = measurements.get('count', [])
                        
                        total_revenue = sum(float(val) for val in sum_values if val is not None)
                        total_orders = sum(float(val) for val in count_values if val is not None)
                    
                    print(f"    Revenue: ${total_revenue:,.2f}")
                    print(f"    Orders: {total_orders:,}")
                    
                    if total_revenue > 1000000:  # Over $1M
                        print(f"    🎯 POTENTIAL MATCH! This is closer to dashboard figures")
                
            except Exception as e:
                print(f"    ❌ Error testing {metric_name}: {e}")
        
        # 3. Check currency in metric definitions
        print(f"\n💱 STEP 3: Currency Analysis")
        print("-" * 40)
        placed_order = await metrics_service.get_metric_by_name("Placed Order")
        if placed_order:
            attrs = placed_order.get('attributes', {})
            print(f"Metric Name: {attrs.get('name')}")
            print(f"Integration: {attrs.get('integration', {})}")
            print(f"Full attributes: {attrs}")
        
        # 4. Test with flow attribution
        print(f"\n🔄 STEP 4: Flow Attribution Analysis")
        print("-" * 40)
        placed_order_metric = await metrics_service.get_metric_by_name("Placed Order")
        if placed_order_metric:
            metric_id = placed_order_metric.get('id')
            
            # Test flow attribution query
            flow_result = await aggregates_service.query(
                metric_id=metric_id,
                start_date=start_date,
                end_date=end_date,
                measurements=["sum_value"],
                by=["$attributed_flow"],
                timezone="Australia/Sydney"
            )
            
            flow_data = flow_result.get('data', {}).get('attributes', {}).get('data', [])
            print(f"Found {len(flow_data)} flow attribution records")
            
            # Show top flows
            for i, flow_item in enumerate(flow_data[:5]):
                groupings = flow_item.get('groupings', {})
                measurements = flow_item.get('measurements', {})
                flow_name = groupings.get('$attributed_flow', ['Unknown'])[0]
                sum_value = measurements.get('sum_value', [])
                revenue = sum(float(val) for val in sum_value if val is not None)
                print(f"  {i+1}. {flow_name}: ${revenue:,.2f}")
        
        # 5. Raw response analysis
        print(f"\n🔬 STEP 5: Raw API Response Analysis")
        print("-" * 40)
        if placed_order_metric:
            metric_id = placed_order_metric.get('id')
            raw_result = await aggregates_service.query(
                metric_id=metric_id,
                start_date=start_date,
                end_date=end_date,
                measurements=["sum_value", "count"],
                timezone="Australia/Sydney"
            )
            
            print(f"Raw response keys: {list(raw_result.keys())}")
            data_attrs = raw_result.get('data', {}).get('attributes', {})
            print(f"Response attributes: {list(data_attrs.keys())}")
            if 'data' in data_attrs:
                print(f"Data structure: {type(data_attrs['data'])}, Length: {len(data_attrs['data'])}")
                if data_attrs['data']:
                    print(f"First data item: {data_attrs['data'][0]}")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_revenue_gap())