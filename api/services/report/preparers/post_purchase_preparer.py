"""
Post purchase flow data preparer.
"""
from typing import Dict, Any, Optional
import logging
from ..chart_generator import get_chart_generator

logger = logging.getLogger(__name__)

# Import intent analysis function
from .flow_preparer import analyze_flow_intent_level


async def prepare_post_purchase_data(
    post_raw: Dict[str, Any],
    benchmarks: Dict[str, Any],
    client_name: str = "the client",
    account_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Prepare post purchase flow data with LLM-generated insights."""
    if not post_raw:
        return {}
    
    # Get account context
    account_context = account_context or {}
    currency = account_context.get("currency", "USD")
    
    # Get benchmark
    post_benchmarks = benchmarks.get("flows", {}).get("post_purchase", {})
    
    # Get first flow or create default structure
    flows = post_raw.get("flows", [])
    if flows:
        flow_data = flows[0]
    else:
        flow_data = {}
    
    # Step 1: Analyze flow intent level (before LLM call)
    intent_analysis = analyze_flow_intent_level(flow_data, "post_purchase")
    
    if intent_analysis.get("intent_level"):
        logger.info(
            f"Post purchase intent analysis: {intent_analysis.get('intent_level')} intent - "
            f"Timing: {intent_analysis.get('recommended_timing')}"
        )
    
    # Try to use LLM service for insights
    narrative = ""
    secondary_narrative = ""
    recommendations = []
    try:
        from ...llm import LLMService
        from ...llm.formatter import LLMDataFormatter
        
        # Initialize LLM service with config from account_context if available
        llm_config = account_context.get("llm_config", {}) if account_context else {}
        default_provider = llm_config.get("provider", "claude")
        llm_service = LLMService(
            default_provider=default_provider,
            anthropic_api_key=llm_config.get("anthropic_api_key"),
            openai_api_key=llm_config.get("openai_api_key"),
            gemini_api_key=llm_config.get("gemini_api_key"),
            claude_model=llm_config.get("claude_model"),
            openai_model=llm_config.get("openai_model"),
            gemini_model=llm_config.get("gemini_model"),
            llm_config=llm_config if llm_config else None
        )
        
        # Get industry from account_context
        industry = account_context.get("industry", "retail") if account_context else "retail"
        
        # Format data for LLM - use flow_analysis format
        formatted_data = LLMDataFormatter.format_for_flow_analysis(
            flow_data={
                "flow_name": "Post Purchase",
                "flows": flows,
                "performance": {
                    "open_rate": flow_data.get("open_rate", 0),
                    "click_rate": flow_data.get("click_rate", 0),
                    "conversion_rate": flow_data.get("placed_order_rate", 0),
                    "revenue": flow_data.get("revenue", 0)
                }
            },
            client_context={
                "client_name": client_name,
                "industry": industry,
                "currency": currency
            }
        )
        
        # Add intent analysis to context for LLM
        if "context" not in formatted_data:
            formatted_data["context"] = {}
        formatted_data["context"]["intent_analysis"] = intent_analysis
        
        # Generate insights using LLM - use post_purchase section for proper prompt
        strategic_insights = await llm_service.generate_insights(
            section="post_purchase",  # Use specific section for post purchase prompt
            data=formatted_data,
            context=formatted_data.get("context", {})
        )
        
        # Extract narratives - filter out raw JSON strings
        primary_raw = strategic_insights.get("primary", "")
        if isinstance(primary_raw, str) and (primary_raw.strip().startswith('{') or (primary_raw.strip().startswith('"') and '"primary"' in primary_raw[:100])):
            logger.warning("Primary narrative appears to be JSON string, JSON parsing may have failed")
            narrative = ""
        else:
            narrative = str(primary_raw) if primary_raw else ""
        
        secondary_raw = strategic_insights.get("secondary", "")
        if isinstance(secondary_raw, str) and (secondary_raw.strip().startswith('{') or (secondary_raw.strip().startswith('"') and '"secondary"' in secondary_raw[:100])):
            logger.warning("Secondary narrative appears to be JSON string, JSON parsing may have failed")
            secondary_narrative = ""
        else:
            secondary_narrative = str(secondary_raw) if secondary_raw else ""
        
        recommendations = strategic_insights.get("recommendations", [])
        if not isinstance(recommendations, list):
            recommendations = []
        
        areas_of_opportunity = strategic_insights.get("areas_of_opportunity", [])
        if not isinstance(areas_of_opportunity, list):
            areas_of_opportunity = []
        
        # Extract enhanced strategic value elements
        root_cause_analysis = strategic_insights.get("root_cause_analysis", {})
        if not isinstance(root_cause_analysis, dict):
            root_cause_analysis = {}
        
        risk_flags = strategic_insights.get("risk_flags", [])
        if not isinstance(risk_flags, list):
            risk_flags = []
        
        quick_wins = strategic_insights.get("quick_wins", [])
        if not isinstance(quick_wins, list):
            quick_wins = []
        
        # Format as HTML paragraphs
        if narrative:
            paragraphs = [p.strip() for p in narrative.split('\n\n') if p.strip()]
            narrative = '\n'.join([f'<p>{p}</p>' for p in paragraphs])
        if secondary_narrative:
            paragraphs = [p.strip() for p in secondary_narrative.split('\n\n') if p.strip()]
            secondary_narrative = '\n'.join([f'<p>{p}</p>' for p in paragraphs])
        
    except Exception as e:
        # Fallback if LLM fails
        logger.error(f"LLM service unavailable for post purchase analysis: {e}", exc_info=True)
        narrative = ""
        secondary_narrative = ""
        recommendations = post_raw.get("recommendations", [])
        areas_of_opportunity = []
        root_cause_analysis = {}
        risk_flags = []
        quick_wins = []
    
    # Generate performance chart
    performance_chart = None
    try:
        chart_generator = get_chart_generator()
        flows = post_raw.get("flows", [])
        
        if flows:
            # Get the first (main) flow for performance comparison
            main_flow = flows[0] if flows else {}
            
            # Prepare flow data for chart
            flow_data = {
                'open_rate': main_flow.get('open_rate', 0),
                'click_rate': main_flow.get('click_rate', 0), 
                'conversion_rate': main_flow.get('placed_order_rate', 0),  # Use placed_order_rate as conversion
                'revenue_per_recipient': main_flow.get('revenue_per_recipient', 0)
            }
            
            # Prepare benchmark data
            benchmarks = {
                'average': {
                    'open_rate': post_benchmarks.get("open_rate", {}).get("average", 65.30),
                    'click_rate': post_benchmarks.get("click_rate", {}).get("average", 8.90),
                    'conversion_rate': post_benchmarks.get("conversion_rate", {}).get("average", 4.20),
                    'revenue_per_recipient': post_benchmarks.get("revenue_per_recipient", {}).get("average", 5.75)
                }
            }
            
            performance_chart_image = chart_generator.generate_flow_performance_chart(
                flow_data=flow_data,
                benchmarks=benchmarks,
                flow_name=main_flow.get('name', 'Post Purchase Flow')
            )
            
            if performance_chart_image:
                performance_chart = f"data:image/png;base64,{performance_chart_image}"
                logger.info("✅ Generated post purchase performance chart")
            
    except Exception as e:
        logger.warning(f"Failed to generate post purchase performance chart: {e}")
        performance_chart = None
    
    return {
        "flows": flows,
        "benchmark": post_raw.get("benchmark", {
            "name": "Post Purchase",
            "open_rate": post_benchmarks.get("open_rate", {}).get("average", 65.30),
            "click_rate": post_benchmarks.get("click_rate", {}).get("average", 8.90),
            "conversion_rate": post_benchmarks.get("conversion_rate", {}).get("average", 4.20),
            "revenue_per_recipient": post_benchmarks.get("revenue_per_recipient", {}).get("average", 5.75)
        }),
        "industry": post_raw.get("industry", "Apparel and Accessories"),
        "intent_analysis": intent_analysis,  # Flow intent level analysis
        "narrative": narrative,  # LLM-generated narrative (HTML formatted)
        "secondary_narrative": secondary_narrative,  # LLM-generated secondary insights (HTML formatted)
        "recommendations": recommendations,  # LLM-generated recommendations
        "areas_of_opportunity": areas_of_opportunity if isinstance(areas_of_opportunity, list) else [],  # LLM-generated areas of opportunity table
        "root_cause_analysis": root_cause_analysis,  # LLM-generated root cause analysis
        "risk_flags": risk_flags,  # LLM-generated risk flags
        "quick_wins": quick_wins,  # LLM-generated quick wins
        "performance_chart": performance_chart  # Generated performance chart
    }

