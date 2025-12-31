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
        
        # Step 3.5: Validate metrics (check for 0 values that shouldn't be 0)
        print("🔍 Step 3.5: Validating metrics...")
        metrics_issues = []
        
        # Check KAV data
        kav_data = audit_data.get("kav_data", {})
        kav_revenue = kav_data.get("revenue", {})
        if kav_revenue.get("total_website", 0) == 0:
            metrics_issues.append("⚠️  Total website revenue is 0")
        if kav_revenue.get("attributed", 0) == 0 and kav_revenue.get("total_website", 0) > 0:
            metrics_issues.append("⚠️  Attributed revenue is 0 but total revenue > 0")
        
        # Check campaign performance
        campaign_data = audit_data.get("campaign_performance_data", {})
        campaign_summary = campaign_data.get("summary", {})
        if campaign_summary.get("avg_open_rate", 0) == 0 and campaign_summary.get("total_sent", 0) > 0:
            metrics_issues.append("⚠️  Campaign open rate is 0% but campaigns were sent")
        if campaign_summary.get("total_sent", 0) == 0:
            metrics_issues.append("⚠️  No campaigns sent in period")
        
        # Check flow performance
        automation_data = audit_data.get("automation_overview_data", {})
        automation_summary = automation_data.get("summary", {})
        if automation_summary.get("total_conversion_value", 0) == 0:
            metrics_issues.append("⚠️  Flow revenue is 0")
        
        # Check list growth
        list_data = audit_data.get("list_growth_data", {})
        if list_data.get("current_total", 0) == 0:
            metrics_issues.append("⚠️  List size is 0")
        
        if metrics_issues:
            print("   ⚠️  Metrics validation issues found:")
            for issue in metrics_issues:
                print(f"      {issue}")
        else:
            print("   ✓ Metrics validation passed")
        print()
        
        # Step 4: Generate audit report
        print("📝 Step 4: Generating  audit report...")
        print("   Rendering templates...")
        print()
        
        # Check if LLM config is available
        llm_config = None
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            llm_config = {
                "provider": "claude",
                "anthropic_api_key": anthropic_key,
                "claude_model": os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
            }
            print("   ✓ LLM configuration detected (Claude)")
        else:
            print("   ⚠️  No LLM configuration - report will use fallback narratives")
        
        report_result = await report_service.generate_audit(
            audit_data=audit_data,
            client_name=client_name,
            auditor_name=auditor_name,
            client_code=client_code,
            llm_config=llm_config
        )
        
        print()
        print("   ✓ Report generation complete!")
        print()
        
        # Step 4.5: Validate strategic features in generated report data
        print("🎯 Step 4.5: Validating strategic features...")
        strategic_features = []
        
        # Check if report data contains strategic features
        # Note: These are added by preparers, so we need to check the report context
        # Since we can't access the internal context, we'll validate the HTML output
        
        print("   ✓ Strategic features validation (will check in HTML output)")
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
            
            # Step 5.5: Validate HTML content for strategic features
            print()
            print("🔍 Step 5.5: Validating HTML content for strategic features...")
            html_content = html_path.read_text(encoding="utf-8")
            
            feature_checks = {
                "Campaign Pattern Diagnosis": "pattern-diagnosis-section" in html_content or "pattern_diagnosis" in html_content,
                "Deliverability Analysis": "deliverability-section" in html_content or "deliverability_analysis" in html_content,
                "Segmentation Recommendation": "segmentation-recommendation-section" in html_content or "segmentation_recommendation" in html_content,
                "Form Categorization": "form-categorization-section" in html_content or "categorized_forms" in html_content,
                "List-Revenue Correlation": "list-correlation-section" in html_content or "list_correlation" in html_content,
                "KAV Interpretation": "kav-interpretation-section" in html_content or "kav_interpretation" in html_content,
                "Flow Intent Analysis": "intent-analysis-section" in html_content or "intent_analysis" in html_content,
                "Flow Issues Detection": "flow-issues-section" in html_content or "flow_issues" in html_content,
                "Strategic Thesis": "strategic-thesis-section" in html_content or "strategic_thesis" in html_content,
                "Integration Opportunities": "integration-opportunities-section" in html_content or "integration_opportunities" in html_content
            }
            
            missing_features = [name for name, found in feature_checks.items() if not found]
            if missing_features:
                print(f"   ⚠️  Missing strategic features in HTML:")
                for feature in missing_features:
                    print(f"      - {feature}")
            else:
                print("   ✓ All strategic features present in HTML")
            
            # Check for zero metrics in HTML (basic check)
            if "0%" in html_content and "avg_open_rate" in html_content:
                print("   ⚠️  Found 0% values in report - verify metrics are correct")
            
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
        
        # Quick metrics validation
        print()
        print("Quick metrics check:")
        kav_revenue = audit_data.get("kav_data", {}).get("revenue", {})
        print(f"  Total revenue: ${kav_revenue.get('total_website', 0):,.2f}")
        print(f"  Attributed revenue: ${kav_revenue.get('attributed', 0):,.2f}")
        print(f"  KAV %: {kav_revenue.get('attributed_percentage', 0):.2f}%")
        
        campaign_summary = audit_data.get("campaign_performance_data", {}).get("summary", {})
        print(f"  Campaign open rate: {campaign_summary.get('avg_open_rate', 0):.2f}%")
        print(f"  Campaigns sent: {campaign_summary.get('total_sent', 0):,}")
        
        return audit_data
        
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        print(traceback.format_exc())
        return None


async def test_strategic_features():
    """Test that strategic features are present in the data."""
    
    print("=" * 70)
    print("STRATEGIC FEATURES VALIDATION TEST")
    print("=" * 70)
    print()
    
    api_key = os.getenv("KLAVIYO_API_KEY")
    if not api_key:
        api_key = input("Enter your Klaviyo API key: ").strip()
    
    try:
        from api.services.klaviyo import KlaviyoService
        from api.services.report import EnhancedReportService
        from api.services.report.data_preparers import (
            prepare_campaign_performance_data,
            prepare_data_capture_data,
            prepare_list_growth_data,
            prepare_kav_data,
            prepare_flow_data,
            prepare_automation_data,
            prepare_strategic_recommendations
        )
        
        klaviyo_service = KlaviyoService(api_key=api_key)
        report_service = EnhancedReportService()
        
        print("Extracting audit data...")
        audit_data = await klaviyo_service.extract_audit_data(days=90)
        
        print("Testing preparers with strategic features...")
        
        # Test campaign preparer
        campaign_data = await prepare_campaign_performance_data(
            audit_data.get("campaign_performance_data", {}),
            {},  # benchmarks
            "Test Client",
            {}
        )
        
        features_found = {
            "Campaign Pattern Diagnosis": "pattern_diagnosis" in campaign_data,
            "Deliverability Analysis": "deliverability_analysis" in campaign_data,
            "Segmentation Recommendation": "segmentation_recommendation" in campaign_data
        }
        
        print("\nCampaign Preparer Features:")
        for feature, found in features_found.items():
            status = "✓" if found else "✗"
            print(f"  {status} {feature}")
        
        # Test data capture preparer
        data_capture_data = await prepare_data_capture_data(
            audit_data.get("data_capture_data", {}),
            "Test Client",
            {}
        )
        
        print("\nData Capture Preparer Features:")
        print(f"  {'✓' if 'categorized_forms' in data_capture_data else '✗'} Form Categorization")
        
        # Test list growth preparer
        list_growth_data = await prepare_list_growth_data(
            audit_data.get("list_growth_data", {}),
            "Test Client",
            {}
        )
        
        print("\nList Growth Preparer Features:")
        print(f"  {'✓' if 'list_correlation' in list_growth_data else '✗'} List-Revenue Correlation")
        
        # Test KAV preparer
        kav_data = await prepare_kav_data(
            audit_data.get("kav_data", {}),
            "Test Client",
            {}
        )
        
        print("\nKAV Preparer Features:")
        print(f"  {'✓' if 'kav_interpretation' in kav_data else '✗'} KAV Strategic Interpretation")
        
        # Test automation preparer
        automation_data = await prepare_automation_data(
            audit_data.get("automation_overview_data", {}),
            {},  # benchmarks
            "Test Client",
            {}
        )
        
        print("\nAutomation Preparer Features:")
        print(f"  {'✓' if 'flow_issues' in automation_data else '✗'} Flow Issues Detection")
        
        # Test strategic preparer
        strategic_data = await prepare_strategic_recommendations(audit_data)
        
        print("\nStrategic Preparer Features:")
        print(f"  {'✓' if 'strategic_thesis' in strategic_data else '✗'} Strategic Thesis")
        print(f"  {'✓' if 'integration_opportunities' in strategic_data else '✗'} Integration Opportunities")
        
        print()
        print("=" * 70)
        print("✅ STRATEGIC FEATURES TEST COMPLETE!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    import sys
    
    # Check for test flags
    if len(sys.argv) > 1:
        if sys.argv[1] == "--quick":
            asyncio.run(test_data_extraction_only())
        elif sys.argv[1] == "--strategic":
            asyncio.run(test_strategic_features())
        else:
            print(f"Unknown flag: {sys.argv[1]}")
            print("Usage: python test_audit.py [--quick|--strategic]")
    else:
        asyncio.run(test_audit())

