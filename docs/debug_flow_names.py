#!/usr/bin/env python3
"""
Debug script to see actual flow names and understand why pattern matching fails.
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
from api.services.klaviyo.flows.service import FlowsService
from api.services.klaviyo.flows.patterns import FlowPatternMatcher
from api.services.klaviyo.flows.statistics import FlowStatisticsService

async def debug_flow_names():
    """Check actual flow names to understand pattern matching failures."""
    
    api_key = os.getenv("KLAVIYO_API_KEY")
    if not api_key:
        print("❌ KLAVIYO_API_KEY not set")
        return
    
    print("🔍 DEBUGGING FLOW NAMES AND PATTERN MATCHING")
    print("=" * 60)
    
    client = KlaviyoClient(api_key)
    flows_service = FlowsService(client)
    stats_service = FlowStatisticsService(client)
    pattern_matcher = FlowPatternMatcher(flows_service, stats_service)
    
    try:
        # Get all flows
        flows = await flows_service.get_flows()
        print(f"📊 Found {len(flows)} total flows:")
        print()
        
        # Show actual flow names
        for i, flow in enumerate(flows[:15]):  # Show first 15
            attrs = flow.get('attributes', {})
            name = attrs.get('name', 'Unknown')
            status = attrs.get('status', 'Unknown')
            created = attrs.get('created', 'Unknown')[:10]  # Just date part
            
            # Test pattern matching
            identified_type = pattern_matcher.identify_flow_type(name)
            
            print(f"  {i+1:2d}. {name}")
            print(f"      Status: {status} | Created: {created}")
            print(f"      Pattern Match: {identified_type or '❌ No match'}")
            print()
        
        # Test the pattern matching logic
        print("🔍 FLOW PATTERN ANALYSIS")
        print("-" * 40)
        
        patterns = pattern_matcher.FLOW_PATTERNS
        for flow_type, keywords in patterns.items():
            print(f"\n🎯 {flow_type.replace('_', ' ').title()}:")
            print(f"   Keywords: {keywords}")
            
            # Find matches
            matches = []
            for flow in flows:
                name = flow.get('attributes', {}).get('name', '')
                if pattern_matcher.identify_flow_type(name) == flow_type:
                    status = flow.get('attributes', {}).get('status', 'Unknown')
                    matches.append(f"{name} ({status})")
            
            if matches:
                print(f"   ✅ Matches found: {len(matches)}")
                for match in matches:
                    print(f"      • {match}")
            else:
                print(f"   ❌ No matches found")
        
        # Test if we're missing obvious flow names
        print(f"\n🔍 CHECKING FOR COMMON FLOW TYPES")
        print("-" * 40)
        
        common_terms = ['abandon', 'cart', 'checkout', 'welcome', 'browse', 'stock', 'purchase', 'back', 'lapsed']
        
        for term in common_terms:
            matching_flows = []
            for flow in flows:
                name = flow.get('attributes', {}).get('name', '').lower()
                if term in name:
                    status = flow.get('attributes', {}).get('status', 'Unknown')
                    matching_flows.append(f"{flow.get('attributes', {}).get('name', 'Unknown')} ({status})")
            
            if matching_flows:
                print(f"\n'{term}' flows:")
                for flow in matching_flows:
                    print(f"  • {flow}")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_flow_names())