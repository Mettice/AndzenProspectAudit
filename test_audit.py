"""
Test script for audit generation.

This script tests the complete audit pipeline:
1. Klaviyo data extraction
2. Report generation with modular templates
3. Output verification

Usage:
    python test_audit.py
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from api.services.klaviyo import KlaviyoService
from api.services.report import EnhancedReportService


async def test_audit():
    """Test the complete  audit generation pipeline."""
    
    print("=" * 70)
    print("AUDIT SYSTEM TEST")
    print("=" * 70)
    print()
    
    # Get API key from environment or prompt
    api_key = os.getenv("KLAVIYO_API_KEY")
    if not api_key:
        api_key = input("Enter your Klaviyo API key: ").strip()
        if not api_key:
            print("❌ No API key provided. Exiting.")
            return
    
    # Test client details
    client_name = "Test Client"
    auditor_name = "Test Auditor"
    client_code = "TEST"
    
    print(f"📋 Test Configuration:")
    print(f"   Client: {client_name}")
    print(f"   Auditor: {auditor_name}")
    print(f"   Code: {client_code}")
    print()
    
    try:
        # Step 1: Initialize services
        print("🔧 Step 1: Initializing services...")
        klaviyo_service = KlaviyoService(api_key=api_key)
        report_service = EnhancedReportService()
        print("   ✓ Services initialized")
        print()
        
        # Step 2: Test API connection
        print("🔌 Step 2: Testing Klaviyo API connection...")
        connection_ok = await klaviyo_service.test_connection()
        if not connection_ok:
            print("   ❌ API connection failed!")
            return
        print("   ✓ API connection successful")
        print()
        
        # Step 3: Extract  audit data
        print("📊 Step 3: Extracting  audit data (90 days)...")
        print("   This may take a few minutes...")
        print()
        
        audit_data = await klaviyo_service.extract_audit_data(days=90)
        
        # Verify data structure
        print()
        print("   ✓ Data extraction complete")
        print(f"   Data keys: {list(audit_data.keys())}")
        
        # Check for key sections
        required_keys = [
            "cover_data",
            "kav_data",
            "list_growth_data",
            "data_capture_data",
            "automation_overview_data",
            "welcome_flow_data",
            "abandoned_cart_data",
            "campaign_performance_data",
            "segmentation_data"
        ]
        
        missing_keys = [key for key in required_keys if key not in audit_data]
        if missing_keys:
            print(f"   ⚠️  Missing keys: {missing_keys}")
        else:
            print("   ✓ All required data sections present")
        print()
        
        # Step 4: Generate audit report
        print("📝 Step 4: Generating  audit report...")
        print("   Rendering templates...")
        print()
        
        report_result = await report_service.generate_audit(
            audit_data=audit_data,
            client_name=client_name,
            auditor_name=auditor_name,
            client_code=client_code
        )
        
        print()
        print("   ✓ Report generation complete!")
        print()
        
        # Step 5: Verify output
        print("✅ Step 5: Verifying output...")
        html_path = Path(report_result["html_url"])
        
        if html_path.exists():
            file_size = html_path.stat().st_size
            print(f"   ✓ HTML report created: {html_path}")
            print(f"   ✓ File size: {file_size:,} bytes")
            print(f"   ✓ Pages: {report_result.get('pages', 'Unknown')}")
            print(f"   ✓ Sections: {len(report_result.get('sections', []))}")
        else:
            print(f"   ❌ HTML report not found at: {html_path}")
        
        if report_result.get("pdf_url"):
            pdf_path = Path(report_result["pdf_url"])
            if pdf_path.exists():
                pdf_size = pdf_path.stat().st_size
                print(f"   ✓ PDF report created: {pdf_path}")
                print(f"   ✓ PDF size: {pdf_size:,} bytes")
            else:
                print(f"   ⚠️  PDF report not found (may not be installed)")
        else:
            print(f"   ⚠️  PDF generation skipped (WeasyPrint may not be installed)")
        
        print()
        print("=" * 70)
        print("✅ TEST COMPLETE!")
        print("=" * 70)
        print()
        print(f"📄 Report Location: {html_path}")
        print(f"   Open in browser: file://{html_path.absolute()}")
        print()
        
        return report_result
        
    except Exception as e:
        import traceback
        print()
        print("=" * 70)
        print("❌ TEST FAILED!")
        print("=" * 70)
        print(f"Error: {e}")
        print()
        print("Traceback:")
        print(traceback.format_exc())
        return None


async def test_data_extraction_only():
    """Test only the data extraction part (faster for debugging)."""
    
    print("=" * 70)
    print("DATA EXTRACTION TEST (Quick)")
    print("=" * 70)
    print()
    
    api_key = os.getenv("KLAVIYO_API_KEY")
    if not api_key:
        api_key = input("Enter your Klaviyo API key: ").strip()
    
    try:
        klaviyo_service = KlaviyoService(api_key=api_key)
        
        print("Testing connection...")
        if not await klaviyo_service.test_connection():
            print("❌ Connection failed")
            return
        
        print("✓ Connected")
        print()
        print("Extracting audit data...")
        
        audit_data = await klaviyo_service.extract_audit_data(days=90)
        
        print()
        print("✓ Extraction complete")
        print()
        print("Data structure:")
        for key, value in audit_data.items():
            if key != "_raw":
                if isinstance(value, dict):
                    print(f"  {key}: dict with keys {list(value.keys())[:5]}...")
                elif isinstance(value, list):
                    print(f"  {key}: list with {len(value)} items")
                else:
                    print(f"  {key}: {type(value).__name__}")
        
        return audit_data
        
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        print(traceback.format_exc())
        return None


if __name__ == "__main__":
    import sys
    
    # Check for quick test flag
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        asyncio.run(test_data_extraction_only())
    else:
        asyncio.run(test_audit())

