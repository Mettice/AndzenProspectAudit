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
            # Batch flows to reduce API load - process in smaller chunks
            all_flow_ids = [f["id"] for f in flows[:50]]
            batch_size = 10  # Process 10 flows at a time to reduce rate limiting
            
            if verbose:
                print(f"  Fetching statistics for {len(all_flow_ids)} flows in batches of {batch_size}...")
            
            # Process flows in batches with delays
            for i in range(0, len(all_flow_ids), batch_size):
                batch_ids = all_flow_ids[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(all_flow_ids) + batch_size - 1) // batch_size
                
                if verbose and total_batches > 1:
                    print(f"    Processing batch {batch_num}/{total_batches} ({len(batch_ids)} flows)...")
                
                try:
                    batch_stats = await self.flow_stats.get_statistics(
                        flow_ids=batch_ids,
                        timeframe="last_365_days"
                    )
                    
                    # Merge batch results
                    if batch_stats:
                        if not flow_statistics:
                            flow_statistics = batch_stats
                        else:
                            # Merge results if multiple batches
                            batch_results = batch_stats.get("data", {}).get("attributes", {}).get("results", [])
                            if batch_results and "data" in flow_statistics:
                                existing_results = flow_statistics["data"]["attributes"].get("results", [])
                                existing_results.extend(batch_results)
                    
                    # Add delay between batches to avoid rate limiting
                    if i + batch_size < len(all_flow_ids):
                        await asyncio.sleep(2.0)  # 2 second delay between batches
                        
                except Exception as e:
                    if verbose:
                        print(f"    ⚠️ Batch {batch_num} failed: {e}")
                    continue
            
            if flow_statistics and verbose:
                total_results = 0
                if "data" in flow_statistics and "attributes" in flow_statistics["data"]:
                    total_results = len(flow_statistics["data"]["attributes"].get("results", []))
                print(f"  ✓ Flow statistics extracted for {total_results} flows")
        
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

