#!/usr/bin/env python3
"""
Debug script for testing revenue extraction fixes.

This script tests the improved revenue parsing logic with proper timezone handling
and debugging output for Cherry Collectables Klaviyo data.
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
from api.services.klaviyo.metrics.service import MetricsService
from api.services.klaviyo.metrics.aggregates import MetricAggregatesService
from api.services.klaviyo.utils.date_helpers import get_klaviyo_compatible_range

# Configure logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_revenue_extraction():
    """Test revenue extraction with improved timezone and parsing logic."""
    
    # Get API key from environment
    api_key = os.getenv("KLAVIYO_API_KEY")
    if not api_key:
        print("❌ KLAVIYO_API_KEY environment variable not set")
        print("💡 Make sure the .env file contains KLAVIYO_API_KEY=your_api_key")
        return
    
    print(f"🔑 Using API key: {api_key[:8]}...{api_key[-4:]}")  # Show partial key for verification
    
    print("🔍 Testing Revenue Extraction Fixes")
    print("=" * 60)
    
    # Initialize services
    client = KlaviyoClient(api_key)
    metrics_service = MetricsService(client)
    aggregates_service = MetricAggregatesService(client)
    revenue_service = RevenueTimeSeriesService(client)
    
    try:
        # Test 1: Check date range calculation
        print("\n📅 TEST 1: Date Range Calculation")
        print("-" * 40)
        
        date_range = get_klaviyo_compatible_range(90, "Australia/Sydney")
        print(f"Start Date: {date_range['start']}")
        print(f"End Date: {date_range['end']}")
        print(f"Timezone: {date_range['timezone']}")
        
        # Test 2: Check Placed Order metric access
        print("\n📊 TEST 2: Placed Order Metric Access")
        print("-" * 40)
        
        placed_order = await metrics_service.get_metric_by_name("Placed Order")
        if placed_order:
            metric_id = placed_order.get("id")
            print(f"✅ Found Placed Order metric: {metric_id}")
        else:
            print("❌ Placed Order metric not found")
            return
        
        # Test 3: Direct revenue query with debugging
        print("\n💰 TEST 3: Direct Revenue Query (Last 7 Days)")
        print("-" * 40)
        
        # Query last 7 days for faster testing
        test_range = get_klaviyo_compatible_range(7, "Australia/Sydney")
        
        revenue_data = await aggregates_service.query(
            metric_id=metric_id,
            start_date=test_range["start"],
            end_date=test_range["end"],
            measurements=["sum_value", "count", "unique"],
            interval="day",
            timezone="Australia/Sydney"
        )
        
        print(f"Revenue query response keys: {list(revenue_data.keys()) if revenue_data else 'None'}")
        
        if revenue_data and 'data' in revenue_data:
            attrs = revenue_data['data'].get('attributes', {})
            dates = attrs.get('dates', [])
            values = attrs.get('data', [])
            
            print(f"Dates returned: {len(dates)}")
            print(f"Values returned: {len(values)}")
            
            # Show first few data points
            print("\nFirst 3 days of data:")
            for i in range(min(3, len(dates))):
                date = dates[i] if i < len(dates) else "N/A"
                value = values[i] if i < len(values) else "N/A"
                print(f"  {date}: {value}")
                
            # Calculate total revenue
            total_revenue = 0
            for value in values:
                if isinstance(value, list) and len(value) > 0:
                    try:
                        total_revenue += float(value[0] or 0)
                    except (ValueError, TypeError):
                        continue
                        
            print(f"\n📈 Total Revenue (7 days): ${total_revenue:,.2f}")
        
        # Test 4: Full revenue time series with new logic
        print("\n🎯 TEST 4: Full Revenue Time Series (90 Days)")
        print("-" * 40)
        
        kav_data = await revenue_service.get_revenue_time_series(
            days=90,
            interval="day", 
            account_timezone="Australia/Sydney"
        )
        
        if 'error' in kav_data:
            print(f"❌ Error: {kav_data['error']}")
        else:
            totals = kav_data.get('totals', {})
            print(f"✅ Total Revenue: ${totals.get('total_revenue', 0):,.2f}")
            print(f"✅ Attributed Revenue: ${totals.get('attributed_revenue', 0):,.2f}")
            print(f"✅ KAV Percentage: {totals.get('kav_percentage', 0):.2f}%")
            print(f"✅ Flow Revenue: ${totals.get('flow_revenue', 0):,.2f}")
            print(f"✅ Campaign Revenue: ${totals.get('campaign_revenue', 0):,.2f}")
            
            # Check time series data
            time_series = kav_data.get('time_series', [])
            revenue_days = [day for day in time_series if day.get('total_revenue', 0) > 0]
            print(f"✅ Days with Revenue: {len(revenue_days)}/{len(time_series)}")
        
        print("\n" + "=" * 60)
        print("🎉 Revenue Extraction Test Complete!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_revenue_extraction())