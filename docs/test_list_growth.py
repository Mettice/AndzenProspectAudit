"""
Test script to verify how to get list growth data from Klaviyo API.
"""
import asyncio
import os
from dotenv import load_dotenv
from api.services.klaviyo import KlaviyoService

load_dotenv()

async def test_list_growth():
    """Test different methods to get list growth data."""
    api_key = os.getenv("KLAVIYO_API_KEY")
    if not api_key:
        print("❌ KLAVIYO_API_KEY not found in .env")
        return
    
    service = KlaviyoService(api_key)
    
    print("=" * 60)
    print("TESTING LIST GROWTH DATA RETRIEVAL")
    print("=" * 60)
    
    # 1. Get lists
    print("\n1. Getting lists...")
    lists = await service.get_lists()
    if lists:
        print(f"   ✓ Found {len(lists)} lists")
        main_list = lists[0]
        list_id = main_list["id"]
        list_name = main_list.get("attributes", {}).get("name", "Unknown")
        print(f"   ✓ Main list: {list_name} (ID: {list_id})")
    else:
        print("   ✗ No lists found")
        return
    
    # 2. Get current count
    print("\n2. Getting current subscriber count...")
    current_count = await service.get_list_profiles_count(list_id)
    print(f"   ✓ Current subscribers: {current_count:,}")
    
    # 3. Get all metrics to find subscription-related ones
    print("\n3. Searching for subscription-related metrics...")
    all_metrics = await service.metrics.get_metrics()
    print(f"   ✓ Found {len(all_metrics)} total metrics")
    
    # Find subscription metrics
    subscription_metrics = []
    for metric in all_metrics:
        name = metric.get("attributes", {}).get("name", "")
        if any(keyword in name.lower() for keyword in ["subscribe", "unsubscribe", "list"]):
            subscription_metrics.append({
                "id": metric.get("id"),
                "name": name,
                "created": metric.get("attributes", {}).get("created")
            })
    
    print(f"   ✓ Found {len(subscription_metrics)} subscription-related metrics:")
    for m in subscription_metrics:
        print(f"      - {m['name']} (ID: {m['id']})")
    
    # 4. Try metric aggregates with list filter
    print("\n4. Testing metric aggregates with list filter...")
    subscribed_metric_id = None
    for m in subscription_metrics:
        if m['name'] == 'Subscribed to List':
            subscribed_metric_id = m['id']
            break
    
    if subscribed_metric_id:
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        try:
            # Try with list filter
            from api.services.klaviyo.filters import build_metric_filter
            filters = build_metric_filter(
                start_date.strftime("%Y-%m-%dT00:00:00Z"),
                end_date.strftime("%Y-%m-%dT23:59:59Z"),
                [f"equals(list_id,'{list_id}')"]  # Filter by list
            )
            
            payload = {
                "data": {
                    "type": "metric-aggregate",
                    "attributes": {
                        "metric_id": subscribed_metric_id,
                        "measurements": ["count"],
                        "interval": "month",
                        "filter": filters
                    }
                }
            }
            
            response = await service._client.request("POST", "/metric-aggregates/", data=payload)
            print(f"   ✓ Metric aggregates with list filter worked!")
            print(f"   Response structure: {list(response.keys())}")
            if response.get("data"):
                attrs = response["data"].get("attributes", {})
                print(f"   Dates: {len(attrs.get('dates', []))} points")
                print(f"   Data: {attrs.get('data', [])[:5]}")  # First 5 values
        except Exception as e:
            print(f"   ✗ Metric aggregates with list filter error: {e}")
            # Try without list filter
            try:
                filters = build_metric_filter(
                    start_date.strftime("%Y-%m-%dT00:00:00Z"),
                    end_date.strftime("%Y-%m-%dT23:59:59Z")
                )
                payload = {
                    "data": {
                        "type": "metric-aggregate",
                        "attributes": {
                            "metric_id": subscribed_metric_id,
                            "measurements": ["count"],
                            "interval": "month",
                            "filter": filters
                        }
                    }
                }
                response = await service._client.request("POST", "/metric-aggregates/", data=payload)
                print(f"   ⚠ Metric aggregates WITHOUT list filter worked (but may include all lists)")
                attrs = response.get("data", {}).get("attributes", {})
                print(f"   Dates: {len(attrs.get('dates', []))} points")
                print(f"   Sample data: {attrs.get('data', [])[:5]}")
            except Exception as e2:
                print(f"   ✗ Metric aggregates without filter also failed: {e2}")
    
    # 5. Try profiles endpoint (basic, no sort)
    print("\n5. Testing profiles endpoint (basic)...")
    try:
        response = await service._client.request(
            "GET",
            f"/lists/{list_id}/profiles/",
            params={
                "page[size]": 10
            }
        )
        profiles = response.get("data", [])
        print(f"   ✓ Profiles endpoint accessible")
        print(f"   ✓ Found {len(profiles)} profiles (showing first 10)")
        if profiles:
            first_profile = profiles[0]
            attrs = first_profile.get("attributes", {})
            print(f"   ✓ Sample profile email: {attrs.get('email', 'N/A')}")
            # Check if profile has subscription relationship
            relationships = first_profile.get("relationships", {})
            if relationships:
                print(f"   ✓ Profile has relationships: {list(relationships.keys())}")
    except Exception as e:
        print(f"   ✗ Profiles endpoint error: {e}")
    
    # 5b. Try to get profile subscriptions relationship
    print("\n5b. Testing profile subscriptions relationship...")
    try:
        # Get a profile first
        response = await service._client.request(
            "GET",
            f"/lists/{list_id}/profiles/",
            params={"page[size]": 1}
        )
        profiles = response.get("data", [])
        if profiles:
            profile_id = profiles[0].get("id")
            # Try to get subscriptions for this profile
            try:
                sub_response = await service._client.request(
                    "GET",
                    f"/profiles/{profile_id}/relationships/subscriptions/"
                )
                print(f"   ✓ Subscriptions relationship accessible")
                print(f"   Response: {sub_response}")
            except Exception as e:
                print(f"   ✗ Subscriptions relationship error: {e}")
    except Exception as e:
        print(f"   ✗ Could not get profile for relationship test: {e}")
    
    # 6. Try the actual list growth method
    print("\n6. Testing get_list_growth_data method (with smart list selection)...")
    try:
        # Don't pass list_id - let the method select the best list
        growth_data = await service.get_list_growth_data(months=12)
        print(f"   ✓ Method completed")
        print(f"   ✓ Selected list: {growth_data.get('list_name', 'Unknown')}")
        print(f"   ✓ List ID: {growth_data.get('list_id', 'Unknown')}")
        print(f"   ✓ Current total: {growth_data.get('current_total', 0):,}")
        print(f"   ✓ Growth subscribers: {growth_data.get('growth_subscribers', 0):,}")
        print(f"   ✓ Lost subscribers: {growth_data.get('lost_subscribers', 0):,}")
        print(f"   ✓ Monthly data points: {len(growth_data.get('monthly_data', []))}")
        
        if growth_data.get('note'):
            print(f"   ⚠ Note: {growth_data.get('note')}")
        
        if growth_data.get('monthly_data'):
            print(f"\n   Sample monthly data:")
            for month in growth_data['monthly_data'][:3]:
                print(f"      {month['month']}: +{month['new_subscribers']} -{month['lost_subscribers']} (net: {month['net_change']})")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_list_growth())

