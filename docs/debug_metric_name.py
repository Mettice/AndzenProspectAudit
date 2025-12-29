#!/usr/bin/env python3
"""
Debug script to check exactly what revenue metrics are available and their names.
"""
import asyncio
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from api.services.klaviyo.client import KlaviyoClient
from api.services.klaviyo.metrics.service import MetricsService

async def debug_metric_names():
    """Check exact metric names available."""
    
    api_key = os.getenv("KLAVIYO_API_KEY")
    if not api_key:
        print("❌ KLAVIYO_API_KEY not set")
        return
    
    print("🔍 DEBUGGING METRIC NAMES")
    print("=" * 40)
    
    client = KlaviyoClient(api_key)
    metrics_service = MetricsService(client)
    
    try:
        # Get all metrics
        metrics = await metrics_service.get_metrics()
        
        # Find revenue-related metrics
        revenue_metrics = [m for m in metrics if any(term in m.get('attributes', {}).get('name', '').lower() 
                          for term in ['revenue', 'order', 'placed', 'purchase', 'checkout', 'value', 'product'])]
        
        print(f"Found {len(revenue_metrics)} revenue-related metrics:")
        print()
        
        for metric in revenue_metrics:
            name = metric.get('attributes', {}).get('name', 'Unknown')
            metric_id = metric.get('id', 'No ID')
            print(f"  • {name} ({metric_id})")
            
        print()
        print("🔍 Testing specific lookups:")
        
        # Test the lookups we're using
        test_names = ["Ordered Product", "Placed Order", "ordered product", "placed order"]
        
        for name in test_names:
            try:
                result = await metrics_service.get_metric_by_name(name)
                if result:
                    actual_name = result.get('attributes', {}).get('name', 'Unknown')
                    metric_id = result.get('id', 'No ID')
                    print(f"  ✅ '{name}' → Found: {actual_name} ({metric_id})")
                else:
                    print(f"  ❌ '{name}' → Not found")
            except Exception as e:
                print(f"  ❌ '{name}' → Error: {e}")
                
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_metric_names())