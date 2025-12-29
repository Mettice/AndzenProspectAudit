#!/usr/bin/env python3
"""
Test script to compare 90 days vs 30 days revenue extraction to understand the audit issue.
"""
import asyncio
import logging
import os
import sys
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables")

# Add api directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from api.services.klaviyo.client import KlaviyoClient
from api.services.klaviyo.revenue.time_series import RevenueTimeSeriesService

# Configure logging for debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_date_range_comparison():
    """Test 30 days vs 90 days to understand the audit issue."""
    
    # Get API key from environment
    api_key = os.getenv("KLAVIYO_API_KEY")
    if not api_key:
        print("❌ KLAVIYO_API_KEY environment variable not set")
        return
    
    print(f"🔑 Using API key: {api_key[:8]}...{api_key[-4:]}")
    print("🧪 Testing 30 Days vs 90 Days Revenue Extraction")
    print("=" * 70)
    
    # Initialize services
    client = KlaviyoClient(api_key)
    revenue_service = RevenueTimeSeriesService(client)
    
    try:
        # Test 1: 30 Days (Known Working)
        print("\n💰 TEST 1: 30 Days Revenue (Known Working)")
        print("-" * 50)
        
        kav_30 = await revenue_service.get_revenue_time_series(
            days=30,
            interval="day", 
            account_timezone="Australia/Sydney"
        )
        
        if 'error' in kav_30:
            print(f"❌ 30-Day Error: {kav_30['error']}")
        else:
            totals_30 = kav_30.get('totals', {})
            print(f"✅ 30-Day Total Revenue: ${totals_30.get('total_revenue', 0):,.2f}")
            print(f"✅ 30-Day Flow Revenue: ${totals_30.get('flow_revenue', 0):,.2f}")
            print(f"✅ 30-Day Period: {kav_30.get('period', {}).get('start_date')} to {kav_30.get('period', {}).get('end_date')}")
        
        # Test 2: 90 Days (Currently Failing in Audit)  
        print("\n💰 TEST 2: 90 Days Revenue (Audit Issue)")
        print("-" * 50)
        
        kav_90 = await revenue_service.get_revenue_time_series(
            days=90,
            interval="day", 
            account_timezone="Australia/Sydney"
        )
        
        if 'error' in kav_90:
            print(f"❌ 90-Day Error: {kav_90['error']}")
        else:
            totals_90 = kav_90.get('totals', {})
            print(f"✅ 90-Day Total Revenue: ${totals_90.get('total_revenue', 0):,.2f}")
            print(f"✅ 90-Day Flow Revenue: ${totals_90.get('flow_revenue', 0):,.2f}")
            print(f"✅ 90-Day Period: {kav_90.get('period', {}).get('start_date')} to {kav_90.get('period', {}).get('end_date')}")
        
        # Test 3: Comparison Analysis
        print(f"\n{'='*70}")
        print("📊 COMPARISON ANALYSIS") 
        print(f"{'='*70}")
        
        if 'totals' in locals() and totals_30 and totals_90:
            revenue_30 = totals_30.get('total_revenue', 0)
            revenue_90 = totals_90.get('total_revenue', 0)
            
            print(f"📅 30-Day Revenue: ${revenue_30:,.2f}")
            print(f"📅 90-Day Revenue: ${revenue_90:,.2f}")
            
            if revenue_90 == 0 and revenue_30 > 0:
                print("🚨 ISSUE IDENTIFIED: 90-day query returns $0 while 30-day works")
                print("💡 HYPOTHESIS: Date range goes too far back or API structure changes")
            elif revenue_90 > revenue_30:
                print("✅ EXPECTED: 90-day revenue should be higher than 30-day")
            else:
                print("⚠️  UNEXPECTED: Need to investigate date ranges")
                
            print(f"\n🎯 DASHBOARD TARGET: A$5,741,338.07 (ALL-TIME)")
            print(f"📊 OUR 30-DAY: ${revenue_30:,.2f} ({revenue_30/5741338.07*100:.1f}% of dashboard)")
            print(f"📊 OUR 90-DAY: ${revenue_90:,.2f} ({revenue_90/5741338.07*100:.1f}% of dashboard)")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_date_range_comparison())