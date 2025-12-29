"""
Flow data extraction module.
"""
import asyncio
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class FlowExtractor:
    """Extracts flow data from Klaviyo."""
    
    def __init__(self, flows, flow_stats):
        """
        Initialize flow extractor.
        
        Args:
            flows: FlowsService instance
            flow_stats: FlowStatisticsService instance
        """
        self.flows = flows
        self.flow_stats = flow_stats
    
    async def extract(
        self,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Extract flow data, statistics, and detailed flow information.
        
        Args:
            verbose: Whether to print progress messages
            
        Returns:
            Dict with 'flows', 'flow_statistics', and 'flow_details' keys
        """
        if verbose:
            print("\n🔄 SECTION 3: Flow Data")
            print("-" * 40)
        
        flows = await self.flows.get_flows()
        if verbose:
            print(f"  ✓ Fetched {len(flows)} flows")
        
        flow_statistics = {}
        if flows:
            flow_ids = [f["id"] for f in flows[:50]]
            if verbose:
                print(f"  Fetching statistics for {len(flow_ids)} flows...")
            flow_statistics = await self.flow_stats.get_statistics(
                flow_ids=flow_ids,
                timeframe="last_365_days"
            )
            if flow_statistics and verbose:
                print(f"  ✓ Flow statistics extracted")
        
        # Detailed flow data
        if verbose:
            print(f"  Fetching detailed data for first 5 flows...")
        flow_data = []
        for i, flow in enumerate(flows[:5]):
            try:
                actions = await self.flows.get_flow_actions(flow["id"])
                await asyncio.sleep(0.5)
                
                limited_actions = actions[:3]
                flow_messages = []
                
                for action in limited_actions:
                    try:
                        messages = await self.flows.get_flow_action_messages(action["id"])
                        flow_messages.extend(messages)
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        if verbose:
                            print(f"    ✗ Error fetching messages for action {action['id']}: {e}")
                        break
                
                flow_data.append({
                    "flow": flow,
                    "actions": limited_actions,
                    "messages": flow_messages
                })
                if verbose:
                    print(f"    ✓ Flow {i+1}/5: {len(limited_actions)} actions, {len(flow_messages)} messages")
            except Exception as e:
                if verbose:
                    print(f"    ✗ Error fetching data for flow {flow['id']}: {e}")
        
        return {
            "flows": flows,
            "flow_statistics": flow_statistics,
            "flow_details": flow_data
        }

