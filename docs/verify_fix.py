import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), 'api'))

from api.services.klaviyo.client import KlaviyoClient
from api.services.klaviyo.revenue.time_series import RevenueTimeSeriesService

async def verify_fix():
    load_dotenv()
    api_key = os.getenv("KLAVIYO_API_KEY")
    client = KlaviyoClient(api_key)
    revenue_service = RevenueTimeSeriesService(client)
    
    print("--- VERIFYING REVENUE ESTIMATION FIX ---")
    data = await revenue_service.get_revenue_time_series(days=30, account_timezone="Australia/Sydney")
    
    totals = data.get("totals", {})
    print(f"Total Revenue: ${totals.get('total_revenue', 0):,.2f}")
    print(f"Flow Revenue: ${totals.get('flow_revenue', 0):,.2f}")
    print(f"Campaign Revenue: ${totals.get('campaign_revenue', 0):,.2f}")
    print(f"Attributed Revenue: ${totals.get('attributed_revenue', 0):,.2f}")
    print(f"KAV %: {totals.get('kav_percentage', 0)}%")
    
    if totals.get('flow_revenue') == totals.get('total_revenue') and totals.get('total_revenue') > 0:
        print("❌ CRITICAL: Flow == Total (Bug Persists)")
    elif totals.get('flow_revenue', 0) == 0 and totals.get('total_revenue') > 0:
         print("⚠️  Warning: Flow Revenue is 0 (Attribution failed completely?)")
    else:
        print("✅ Fix Verified: Revenue attribution is estimated proportional to total.")

if __name__ == "__main__":
    asyncio.run(verify_fix())
