#!/usr/bin/env python3
"""
Debug script to find correct subscription-related metrics.
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
from api.services.klaviyo.lists.service import ListsService

async def debug_subscription_metrics():
    """Find subscription and list-related metrics."""
    
    api_key = os.getenv("KLAVIYO_API_KEY")
    if not api_key:
        print("❌ KLAVIYO_API_KEY not set")
        return
    
    print("🔍 DEBUGGING SUBSCRIPTION METRICS")
    print("=" * 50)
    
    client = KlaviyoClient(api_key)
    metrics_service = MetricsService(client)
    lists_service = ListsService(client)
    
    try:
        # 1. Find subscription-related metrics
        print("📊 SUBSCRIPTION-RELATED METRICS")
        print("-" * 40)
        metrics = await metrics_service.get_metrics()
        
        subscription_terms = ['subscrib', 'unsubscrib', 'list', 'signup', 'opt', 'member', 'join']
        subscription_metrics = []
        
        for metric in metrics:
            name = metric.get('attributes', {}).get('name', '').lower()
            if any(term in name for term in subscription_terms):
                subscription_metrics.append(metric)
        
        print(f"Found {len(subscription_metrics)} subscription-related metrics:")
        for metric in subscription_metrics:
            name = metric.get('attributes', {}).get('name', 'Unknown')
            metric_id = metric.get('id', 'No ID')
            print(f"  • {name} ({metric_id})")
        
        # 2. Check lists and their profile counts
        print(f"\n📋 LIST INFORMATION")
        print("-" * 40)
        lists = await lists_service.get_lists()
        
        print(f"Found {len(lists)} lists:")
        for i, list_item in enumerate(lists[:5]):  # Show first 5
            attrs = list_item.get('attributes', {})
            list_name = attrs.get('name', 'Unknown')
            list_id = list_item.get('id', 'No ID')
            created = attrs.get('created', 'Unknown')
            
            print(f"  {i+1}. {list_name}")
            print(f"     ID: {list_id}")
            print(f"     Created: {created}")
            
            # Try to get profile count
            try:
                count = await lists_service.get_list_profiles_count(list_id)
                print(f"     Profiles: {count:,}")
            except Exception as e:
                print(f"     Profiles: Error getting count - {e}")
        
        # 3. Test specific metric lookups
        print(f"\n🔍 TESTING SPECIFIC METRIC LOOKUPS")
        print("-" * 40)
        
        test_names = [
            "Subscribed to List",
            "Unsubscribed", 
            "Unsubscribed from List",
            "Added to List",
            "Removed from List",
            "List Member Added",
            "List Member Removed",
            "Opted In",
            "Opted Out"
        ]
        
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
    asyncio.run(debug_subscription_metrics())