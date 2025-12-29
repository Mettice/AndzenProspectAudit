"""
Data formatter for LLM consumption.

Formats Klaviyo data into clean, structured format for LLM prompts.
"""
from typing import Dict, Any, Optional
from datetime import datetime


class LLMDataFormatter:
    """Format Klaviyo data for LLM consumption."""
    
    @staticmethod
    def format_for_kav_analysis(
        kav_data: Dict[str, Any],
        client_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format KAV data with context for LLM.
        
        Args:
            kav_data: KAV data (can be from format_audit_data with "revenue" key, 
                     or raw from get_revenue_time_series with "totals" key)
            client_context: Business context (client_name, industry, etc.)
            
        Returns:
            Formatted data dict for LLM prompt
        """
        client_context = client_context or {}
        
        # Extract period info
        period = kav_data.get("period", {})
        revenue = kav_data.get("revenue", {})
        totals = kav_data.get("totals", {})
        
        # Handle both data structures:
        # 1. From format_audit_data: has "revenue" key and "totals" key
        # 2. From get_revenue_time_series: has "totals" key
        # Prefer totals if available (more complete), otherwise use revenue
        
        if totals:
            # Structure from get_revenue_time_series or format_audit_data with totals
            metrics = {
                "total_revenue": totals.get("total_revenue", 0),
                "attributed_revenue": totals.get("attributed_revenue", 0),
                "kav_percentage": totals.get("kav_percentage", 0),
                "flow_revenue": totals.get("flow_revenue", 0),
                "campaign_revenue": totals.get("campaign_revenue", 0),
                "flow_percentage": totals.get("flow_percentage", 0),  # Ensure percentages are included
                "campaign_percentage": totals.get("campaign_percentage", 0)  # Ensure percentages are included
            }
        elif revenue:
            # Structure from format_audit_data (fallback if totals not available)
            metrics = {
                "total_revenue": revenue.get("total_website", 0),
                "attributed_revenue": revenue.get("attributed", 0),
                "kav_percentage": revenue.get("attributed_percentage", 0),
                "flow_revenue": revenue.get("flow_attributed", 0),
                "campaign_revenue": revenue.get("campaign_attributed", 0),
                "flow_percentage": revenue.get("flow_percentage", 0),
                "campaign_percentage": revenue.get("campaign_percentage", 0)
            }
        else:
            # Fallback if neither structure is available
            metrics = {
                "total_revenue": 0,
                "attributed_revenue": 0,
                "kav_percentage": 0,
                "flow_revenue": 0,
                "campaign_revenue": 0,
                "flow_percentage": 0,
                "campaign_percentage": 0
            }
        
        # Calculate percentages if missing but revenue values exist
        if metrics["flow_percentage"] == 0 and metrics["attributed_revenue"] > 0:
            metrics["flow_percentage"] = (metrics["flow_revenue"] / metrics["attributed_revenue"]) * 100
        
        if metrics["campaign_percentage"] == 0 and metrics["attributed_revenue"] > 0:
            metrics["campaign_percentage"] = (metrics["campaign_revenue"] / metrics["attributed_revenue"]) * 100
        
        # Format context
        context = {
            "client_name": client_context.get("client_name", "the client"),
            "industry": client_context.get("industry", "retail"),
            "date_range": f"{period.get('start_date', 'N/A')} to {period.get('end_date', 'N/A')}",
            "kav_benchmark": client_context.get("kav_benchmark", 30.0)  # Industry standard
        }
        
        return {
            "metrics": metrics,
            "context": context
        }
    
    @staticmethod
    def format_for_flow_analysis(
        flow_data: Dict[str, Any],
        client_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format flow data for LLM analysis.
        
        Handles both old format (with "name" and "statistics") and new format (with "flow_name" and "metrics").
        
        Args:
            flow_data: Flow performance data (can be old or new format)
            client_context: Business context
            
        Returns:
            Formatted data dict for LLM prompt
        """
        client_context = client_context or {}
        
        # Handle both old and new formats
        if "flow_name" in flow_data:
            # New format
            flow_name = flow_data.get("flow_name", "Unknown Flow")
            metrics = flow_data.get("metrics", {})
            benchmark = flow_data.get("benchmark", {})
        elif "name" in flow_data:
            # Old format (backward compatibility)
            flow_name = flow_data.get("name", "Unknown Flow")
            stats = flow_data.get("statistics", {})
            metrics = {
                "open_rate": stats.get("open_rate", 0),
                "click_rate": stats.get("click_rate", 0),
                "conversion_rate": stats.get("conversion_rate", 0),
                "revenue": stats.get("revenue", 0),
                "revenue_per_recipient": stats.get("revenue_per_recipient", 0),
                "conversions": stats.get("conversions", 0)
            }
            benchmark = {}
        else:
            # Handle flows array format
            flows = flow_data.get("flows", [])
            if flows:
                first_flow = flows[0]
                flow_name = first_flow.get("name", "Unknown Flow")
                metrics = {
                    "open_rate": first_flow.get("open_rate", 0),
                    "click_rate": first_flow.get("click_rate", 0),
                    "conversion_rate": first_flow.get("placed_order_rate", first_flow.get("conversion_rate", 0)),
                    "revenue": first_flow.get("revenue", 0),
                    "revenue_per_recipient": first_flow.get("revenue_per_recipient", 0),
                    "conversions": first_flow.get("conversions", 0)
                }
            else:
                flow_name = "Unknown Flow"
                metrics = {}
            benchmark = flow_data.get("benchmark", {})
        
        context = {
            "client_name": client_context.get("client_name", "the client"),
            "industry": client_context.get("industry", "retail"),
            "currency": client_context.get("currency", "USD")
        }
        
        return {
            "flow_name": flow_name,
            "metrics": metrics,
            "benchmark": benchmark,  # Include benchmark for prompt
            "context": context
        }
    
    @staticmethod
    def format_for_campaign_analysis(
        campaign_data: Dict[str, Any],
        client_context: Optional[Dict[str, Any]] = None,
        benchmarks: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Format campaign data for LLM analysis."""
        client_context = client_context or {}
        
        # Handle both campaign object and summary dict
        if "summary" in campaign_data:
            summary = campaign_data.get("summary", {})
            metrics = {
                "total_sent": summary.get("total_sent", 0),
                "open_rate": summary.get("avg_open_rate", 0),
                "click_rate": summary.get("avg_click_rate", 0),
                "revenue": summary.get("total_revenue", 0),
                "conversions": summary.get("total_placed_orders", 0),
                "conversion_rate": summary.get("avg_placed_order_rate", 0)
            }
        else:
            campaign_name = campaign_data.get("name", "Unknown Campaign")
            stats = campaign_data.get("statistics", {})
            metrics = {
                "campaign_name": campaign_name,
                "open_rate": stats.get("open_rate", 0),
                "click_rate": stats.get("click_rate", 0),
                "revenue": stats.get("revenue", 0),
                "conversions": stats.get("conversions", 0),
                "deliveries": stats.get("deliveries", 0)
            }
        
        context = {
            "client_name": client_context.get("client_name", "the client"),
            "industry": client_context.get("industry", "retail"),
            "currency": client_context.get("currency", "USD")
        }
        
        return {
            "summary": summary if "summary" in campaign_data else {},
            "metrics": metrics,
            "context": context,
            "benchmarks": benchmarks or {}
        }
    
    @staticmethod
    def format_for_generic_analysis(
        section: str,
        data: Dict[str, Any],
        client_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format generic data for LLM consumption.
        
        Used for sections like list_growth, automation_overview, etc.
        """
        client_context = client_context or {}
        
        return {
            "section": section,
            "data": data,
            "context": {
                "client_name": client_context.get("client_name", "the client"),
                "industry": client_context.get("industry", "retail"),
                "currency": client_context.get("currency", "USD")
            }
        }

