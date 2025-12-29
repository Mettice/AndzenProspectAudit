"""
Test script for Klaviyo API connection and data extraction.
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Load environment variables from project root
load_dotenv(ROOT_DIR / ".env")

from api.services.klaviyo import KlaviyoService


async def test_connection():
    """Test Klaviyo API connection."""
    api_key = os.getenv("KLAVIYO_API_KEY")
    
    if not api_key:
        print("Error: KLAVIYO_API_KEY environment variable not set")
        print("Please set it in your .env file or export it:")
        print("  export KLAVIYO_API_KEY='your_api_key_here'")
        return False
    
    print("Testing Klaviyo API connection...")
    service = KlaviyoService(api_key=api_key)
    
    try:
        result = await service.test_connection()
        if result:
            print("✓ Connection successful!")
            return True
        else:
            print("✗ Connection failed")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def test_data_extraction():
    """Test data extraction from Klaviyo."""
    api_key = os.getenv("KLAVIYO_API_KEY")
    
    if not api_key:
        print("Error: KLAVIYO_API_KEY environment variable not set")
        return False
    
    print("\nTesting data extraction...")
    service = KlaviyoService(api_key=api_key)
    
    try:
        # Extract data for last 30 days
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        date_range = {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }
        
        print(f"Extracting data from {date_range['start']} to {date_range['end']}...")
        data = await service.extract_all_data(date_range=date_range)
        
        print(f"✓ Data extraction successful!")
        print(f"  - Revenue data: {'✓' if data.get('revenue') else '✗'}")
        print(f"  - Campaigns: {len(data.get('campaigns', []))}")
        print(f"  - Flows: {len(data.get('flows', []))}")
        
        return True
    except Exception as e:
        print(f"✗ Error during data extraction: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("=" * 50)
    print("Klaviyo API Test Script")
    print("=" * 50)
    
    # Test connection
    connection_ok = await test_connection()
    
    if connection_ok:
        # Test data extraction
        await test_data_extraction()
    
    print("\n" + "=" * 50)
    print("Tests completed")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())

