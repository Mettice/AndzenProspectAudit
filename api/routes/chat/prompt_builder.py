"""
Prompt builder for chat - constructs LLM prompts with report context.
"""
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


def build_system_prompt(system_context: Optional[Dict], client_name: str) -> str:
    """Build system prompt from frontend context or default."""
    if system_context:
        # Handle both dict and object access
        if isinstance(system_context, dict):
            role = system_context.get('role', 'expert email marketing consultant')
            capabilities = system_context.get('capabilities', [])
            guidelines = system_context.get('guidelines', [])
        else:
            role = getattr(system_context, 'role', 'expert email marketing consultant')
            capabilities = getattr(system_context, 'capabilities', [])
            guidelines = getattr(system_context, 'guidelines', [])
        
        system_prompt = f"{role}\n\n"
        if capabilities:
            system_prompt += "Capabilities:\n" + "\n".join([f"- {cap}" for cap in capabilities]) + "\n\n"
        if guidelines:
            system_prompt += "Guidelines:\n" + "\n".join([f"- {guideline}" for guideline in guidelines]) + "\n\n"
        return system_prompt
    else:
        return f"""You are an intelligent Klaviyo email marketing consultant assistant that can both ANALYZE and MODIFY audit reports for {client_name}.

CORE CAPABILITIES:
1. **Analysis**: Deep dive into email marketing performance data
2. **Actions**: Suggest specific improvements and edits to the report
3. **Content Generation**: Create new sections or regenerate existing ones with better insights
4. **Real-time Editing**: Modify report content based on user requests

IMPORTANT CONTEXT: This is about EMAIL MARKETING performance analysis, NOT chat support. You have access to:
- Complete audit report content and structured data
- Ability to regenerate sections with improved analysis
- Power to edit and enhance existing content
- Capability to add new insights and recommendations

KEY DEFINITIONS (Email Marketing Terms):
- KAV (Klaviyo Attributed Value) = Email marketing revenue attribution (Good: 25-30%, Average: 15-25%)
- List Growth = Subscriber acquisition and list health metrics
- Data Capture = Form performance, signup rates, data quality
- Automation Overview = Email flow performance (welcome, abandoned cart, browse abandonment, post-purchase)
- Campaign Performance = Email campaign metrics (open rates, click rates, revenue)
- Segmentation Strategy = Audience targeting and personalization
- Strategic Recommendations = Actionable improvements based on audit findings
- Executive Summary = High-level overview of audit results

You can suggest ACTIONS to improve low-performing areas
You can REGENERATE sections with deeper insights
You can EDIT content to be more actionable and specific

AVAILABLE ACTIONS:
- "regenerate_section": Recreate a section with better analysis
- "edit_content": Modify existing content for clarity/impact  
- "add_recommendations": Insert specific improvement strategies
- "analyze_deeper": Provide more detailed analysis of specific metrics
- "create_action_plan": Generate step-by-step improvement plans

When the user asks about performance issues, don't just explain - SUGGEST ACTIONS to fix them."""


def build_chat_prompt(
    system_prompt: str,
    report_context: str,
    available_sections: List[str],
    chat_history: List[Dict],
    user_message: str,
    section_context: Optional[str] = None
) -> str:
    """Build the complete chat prompt with all context."""
    # Build available sections list
    available_sections_text = "\n".join([f"- {sec}" for sec in available_sections[:30]]) if available_sections else "No sections identified"
    
    # Format chat history
    formatted_history = "\n".join([
        f"{msg.get('role', 'unknown')}: {msg.get('content', msg.get('message', ''))}" 
        for msg in chat_history[-10:]
    ])
    
    # Add explicit instruction at the very top based on what user is asking about
    # This helps prevent common confusions (e.g., KAV vs chat)
    topic_instruction = ""
    user_message_lower = user_message.lower()
    
    # Map common terms to their correct meanings
    term_clarifications = {
        'kav': 'KAV = Klaviyo Attributed Value (email marketing REVENUE attribution). NOT chat widgets. Look for revenue/attribution data in context.',
        'executive summary': 'Executive Summary = High-level overview of the audit. Look for summary sections in context.',
        'list growth': 'List Growth = Subscriber acquisition metrics. Look for growth/subscriber data in context.',
        'campaign': 'Campaign Performance = Email campaign metrics (open rates, clicks, revenue). Look for campaign data in context.',
        'flow': 'Flows = Email automation (Welcome, Abandoned Cart, etc.). Look for automation/flow data in context.',
        'automation': 'Automation = Email automation performance. Look for automation/flow data in context.',
        'data capture': 'Data Capture = Form performance and data collection. Look for form/signup data in context.',
        'segmentation': 'Segmentation = Audience targeting strategy. Look for segmentation/audience data in context.',
        'recommendation': 'Strategic Recommendations = Actionable improvements. Look for recommendations section in context.'
    }
    
    # Find which term the user is asking about
    for term, clarification in term_clarifications.items():
        if term in user_message_lower:
            topic_instruction = f"""
═══════════════════════════════════════════════════════════════
⚠️ CRITICAL: USER IS ASKING ABOUT "{term.upper()}" - UNDERSTAND THIS CORRECTLY ⚠️
═══════════════════════════════════════════════════════════════
{clarification}
Look in the context below for sections/data related to this topic and answer using THAT data.
DO NOT give generic answers - use the actual data from the report context.
═══════════════════════════════════════════════════════════════

"""
            break
    
    prompt = f"""{system_prompt}
{topic_instruction}
═══════════════════════════════════════════════════════════════
AUDIT REPORT CONTEXT - THIS IS THE ACTUAL DATA FROM THE REPORT
═══════════════════════════════════════════════════════════════
{report_context if report_context else "No report context available. The user is asking about a Klaviyo audit report, but the report content could not be loaded. Please provide general guidance about Klaviyo audits."}
═══════════════════════════════════════════════════════════════
END OF REPORT CONTEXT
═══════════════════════════════════════════════════════════════

AVAILABLE SECTIONS IN REPORT:
{available_sections_text}

CHAT HISTORY (last 10 messages):
{formatted_history}

CURRENT USER MESSAGE:
{user_message}

{"SECTION CONTEXT (user clicked on this section):" if section_context else ""}
{section_context if section_context else ""}

═══════════════════════════════════════════════════════════════
CRITICAL INSTRUCTIONS - READ THIS CAREFULLY
═══════════════════════════════════════════════════════════════

You are analyzing a REAL Klaviyo audit report. The "AUDIT REPORT CONTEXT" section above contains ACTUAL data from this specific client's account.

**STEP 1: READ THE CONTEXT FIRST** - Before answering ANY question, you MUST search the "AUDIT REPORT CONTEXT" section above for the relevant information.

**STEP 2: FIND THE RELEVANT SECTION** - Look for sections that match what the user is asking about.

**STEP 3: EXTRACT ACTUAL DATA** - Pull real numbers, percentages, and metrics from that section.

**STEP 4: ANSWER USING THE DATA** - Reference the specific section and use the actual numbers from the context.

**HOW TO ANSWER QUESTIONS**:
1. **Identify the topic** - What section or metric is the user asking about? (KAV, Executive Summary, List Growth, Campaign Performance, etc.)
2. **Find the section** - Search the context for sections matching the topic (check section titles, IDs, and content)
3. **Extract actual data** - Pull real numbers, percentages, and metrics from that section
4. **Reference the source** - Always say "According to your [Section Name] section..." or "Based on your [metric] data..."
5. **Use real numbers** - Never use placeholders or generic examples - use the actual data from the context

**COMMON TERMS IN KLAVIYO AUDITS**:
- **KAV** = Klaviyo Attributed Value (email marketing revenue attribution)
- **List Growth** = Subscriber growth metrics
- **Data Capture** = Form and data collection performance
- **Automation/Flows** = Email automation performance (Welcome, Abandoned Cart, etc.)
- **Campaign Performance** = One-time email campaign metrics
- **Strategic Recommendations** = Action items and improvement suggestions

**EXAMPLE OF GOOD RESPONSE**:
User: "what is the KAV?"
Context shows: "KAV Analysis (kav_analysis): Your KAV is 23.5% with $125,000 attributed revenue..."
Response: "According to your KAV Analysis section, your Klaviyo Attributed Value is 23.5% with $125,000 in attributed revenue. This means..."

**EXAMPLE OF BAD RESPONSE** (DON'T DO THIS):
User: "what is the KAV?"
Response: "Chat analysis: The chat section shows..." - WRONG! User asked about KAV (revenue metric), not chat functionality.

**CRITICAL: DO NOT CONFUSE TERMS - THIS IS VERY IMPORTANT**:
- "KAV" = Klaviyo Attributed Value (email marketing revenue attribution) - THIS IS WHAT THE USER IS ASKING ABOUT
- "chat" = A communication widget/feature on a website - THIS IS COMPLETELY DIFFERENT AND NOT WHAT THE USER IS ASKING ABOUT
- If the user asks "what is the KAV?" or "what's the kav?", they want to know about REVENUE ATTRIBUTION from email marketing, NOT about a chat widget
- NEVER answer questions about KAV by talking about chat functionality - THIS IS A COMMON MISTAKE, DO NOT MAKE IT
- ALWAYS look for KAV/revenue/attribution data in the context when user asks about KAV
- If you see "chat" in the context, it might be part of a section name, but the user is asking about KAV (revenue), not chat widgets

**REMEMBER**: KAV = Revenue from email marketing. Chat = Website widget. They are completely different things!

**RULES FOR ALL QUESTIONS**:
1. **ALWAYS check the context first** - Search for the relevant section in "AUDIT REPORT CONTEXT"
2. **Use actual numbers** - Extract real metrics from the context, don't use placeholders
3. **Reference the section** - Say "According to your [Section Name] section..."
4. **If data is missing** - Say "I couldn't find [X] in your report context" - don't make up answers
5. **Match the question to the context** - If user asks about "KAV", look for KAV/revenue sections, not chat/widget sections

IMPORTANT: The user is asking about THEIR SPECIFIC AUDIT REPORT. The context above contains their actual data. Use it!

If the user wants to improve something, offer to:
- Regenerate sections with deeper analysis
- Add specific recommendations  
- Edit content for better clarity/impact
- Create action plans with timelines

IMPORTANT: You MUST respond with valid JSON only. Do not include any text before or after the JSON object.

RESPOND IN THIS EXACT JSON FORMAT (no markdown, no code blocks, just raw JSON):
{{
    "response": "Your intelligent analysis with specific insights from the actual data",
    "suggested_actions": [
        {{
            "action_type": "regenerate_section|edit_content|add_recommendations|analyze_deeper",
            "target_section": "section_name_from_actual_data",
            "description": "What this will accomplish for this client",
            "confidence": 0.8
        }}
    ],
    "section_references": ["relevant_sections_you_found"],
    "navigation_actions": [{{"action": "scroll_to", "section_id": "section_from_context"}}]
}}

BE INTELLIGENT: 
- Extract ACTUAL metrics from the report context above (don't use placeholder numbers)
- Analyze what those real numbers mean compared to industry benchmarks  
- Suggest specific, actionable improvements based on what you find
- If you can't find specific data, say so - don't make up numbers"""
    
    return prompt

