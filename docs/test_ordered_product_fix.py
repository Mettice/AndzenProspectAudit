#!/usr/bin/env python3
"""
Test the "Ordered Product" metric fix to see if we now get the correct revenue.
"""
import asyncio
import logging
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from api.services.klaviyo.client import KlaviyoClient
from api.services.klaviyo.revenue.time_series import RevenueTimeSeriesService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_ordered_product_fix():
    """Test if switching to Ordered Product metric fixes the revenue gap."""
    
    api_key = os.getenv("KLAVIYO_API_KEY")
    if not api_key:
        print("❌ KLAVIYO_API_KEY not set")
        return
    
    print("🎯 TESTING ORDERED PRODUCT METRIC FIX")
    print("=" * 50)
    print("Dashboard Target: A$5,741,338.07 (Oct 21 - Dec 21)")
    print("Expected USD: ~$6,066,997.86 (from our debug)")
    print()
    
    client = KlaviyoClient(api_key)
    revenue_service = RevenueTimeSeriesService(client)
    
    try:
        # Test the exact dashboard period
        print("📊 Testing Revenue with Ordered Product Metric")
        print("-" * 40)
        
        kav_data = await revenue_service.get_revenue_time_series(
            days=61,  # Oct 21 to Dec 21 (roughly 61 days)
            interval="day",
            account_timezone="Australia/Sydney"
        )
        
        if 'error' in kav_data:
            print(f"❌ Error: {kav_data['error']}")
        else:
            totals = kav_data.get('totals', {})
            period = kav_data.get('period', {})
            
            total_revenue = totals.get('total_revenue', 0)
            flow_revenue = totals.get('flow_revenue', 0)
            campaign_revenue = totals.get('campaign_revenue', 0)
            attributed_revenue = totals.get('attributed_revenue', 0)
            
            print(f"✅ Period: {period.get('start_date')} to {period.get('end_date')}")
            print(f"✅ Total Revenue: ${total_revenue:,.2f}")
            print(f"✅ Flow Revenue: ${flow_revenue:,.2f}")  
            print(f"✅ Campaign Revenue: ${campaign_revenue:,.2f}")
            print(f"✅ Attributed Revenue: ${attributed_revenue:,.2f}")
            print(f"✅ KAV %: {totals.get('kav_percentage', 0):.1f}%")
            
            print(f"\n🎯 COMPARISON TO DASHBOARD:")
            dashboard_total_aud = 5741338.07
            dashboard_attributed_aud = 2460774.32
            
            # Rough USD conversion (AUD to USD ~0.65-0.70)
            dashboard_total_usd = dashboard_total_aud * 0.67  # Conservative estimate
            dashboard_attributed_usd = dashboard_attributed_aud * 0.67
            
            print(f"Dashboard Total (A$): ${dashboard_total_aud:,.2f}")
            print(f"Dashboard Total (~USD): ${dashboard_total_usd:,.2f}")  
            print(f"Our Total (USD): ${total_revenue:,.2f}")
            print(f"Match %: {(total_revenue / dashboard_total_usd * 100):.1f}%")
            
            print(f"\nDashboard Attributed (A$): ${dashboard_attributed_aud:,.2f}")
            print(f"Dashboard Attributed (~USD): ${dashboard_attributed_usd:,.2f}")
            print(f"Our Attributed (USD): ${attributed_revenue:,.2f}")
            print(f"Attribution Match %: {(attributed_revenue / dashboard_attributed_usd * 100):.1f}%")
            
            if total_revenue > 3000000:  # Over $3M
                print(f"\n🎉 SUCCESS! Revenue is now in the expected range!")
                print(f"   We went from $233k to ${total_revenue:,.0f} - that's a {total_revenue/233324*100:.0f}x improvement!")
            else:
                print(f"\n⚠️  Still below expected range. Need further investigation.")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ordered_product_fix())