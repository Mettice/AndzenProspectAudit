"""
Context builder for chat - extracts and builds report context from frontend or HTML.
"""
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_frontend_context(message: Any) -> tuple[Optional[Dict], Optional[List[str]], Optional[Dict]]:
    """Extract frontend-provided context from message."""
    msg_dict = message.dict() if hasattr(message, 'dict') else {}
    
    frontend_context = None
    if msg_dict.get('full_context'):
        frontend_context = msg_dict['full_context']
        logger.info(f"✓ Using frontend-provided context (from dict): {len(frontend_context.get('report_summary', []))} summary items, {len(frontend_context.get('full_content', []))} full content pages")
    elif hasattr(message, 'full_context') and message.full_context:
        frontend_context = message.full_context
        logger.info(f"✓ Using frontend-provided context (direct): {len(frontend_context.get('report_summary', []))} summary items")
    
    frontend_sections = None
    if msg_dict.get('available_sections'):
        frontend_sections = msg_dict['available_sections']
        logger.info(f"✓ Using frontend-provided section mapping (from dict): {len(frontend_sections)} sections")
    elif hasattr(message, 'available_sections') and message.available_sections:
        frontend_sections = message.available_sections
        logger.info(f"✓ Using frontend-provided section mapping (direct): {len(frontend_sections)} sections")
    
    frontend_system_context = None
    if msg_dict.get('system_context'):
        frontend_system_context = msg_dict['system_context']
        logger.info(f"✓ Using frontend-provided system context (from dict)")
    elif hasattr(message, 'system_context') and message.system_context:
        frontend_system_context = message.system_context
        logger.info(f"✓ Using frontend-provided system context (direct)")
    
    return frontend_context, frontend_sections, frontend_system_context


def build_context_from_frontend(frontend_context: Dict[str, Any]) -> str:
    """Build report context string from frontend-provided context."""
    context_parts = []
    
    # Prefer full_content if available (most comprehensive)
    if frontend_context.get('full_content'):
        print(f"✓ Frontend provided full_content with {len(frontend_context['full_content'])} pages")
        logger.info(f"✓ Frontend provided full_content with {len(frontend_context['full_content'])} pages")
        kav_found = False
        for page in frontend_context['full_content'][:30]:  # First 30 pages
            if isinstance(page, dict):
                section_id = page.get('sectionId', page.get('section', 'unknown'))
                title = page.get('title', 'Untitled')
                content = page.get('content', '')
                if content:
                    # Send more content for important sections (KAV, strategic recommendations, etc.)
                    important_sections = ['kav', 'strategic', 'executive', 'recommendations']
                    is_important = any(imp in section_id.lower() for imp in important_sections)
                    content_limit = 8000 if is_important else 5000
                    context_parts.append(f"{title} ({section_id}):\n{content[:content_limit]}\n")
                    if 'kav' in section_id.lower():
                        kav_found = True
                        print(f"  ✅ Found KAV section: {section_id} with {len(content)} chars")
                        logger.info(f"  ✓ Found KAV section: {section_id} with {len(content)} chars")
                    logger.debug(f"  - Added {section_id}: {len(content)} chars (limited to {content_limit})")
        print(f"✓ Built context from {len(context_parts)} pages with {sum(len(p) for p in context_parts)} total chars")
        logger.info(f"✓ Built context from {len(context_parts)} pages with {sum(len(p) for p in context_parts)} total chars")
        if not kav_found:
            print(f"⚠ KAV section NOT found in frontend full_content!")
            logger.warning("⚠ KAV section NOT found in frontend full_content!")
    
    # Fallback to report summary
    elif frontend_context.get('report_summary'):
        for item in frontend_context['report_summary'][:20]:  # Limit to 20 sections
            section_id = item.get('section', 'unknown')
            title = item.get('title', 'Untitled')
            preview = item.get('preview', '')
            context_parts.append(f"{title} ({section_id}):\n{preview}\n")
    
    # Fallback to content preview
    elif frontend_context.get('content_preview'):
        for page in frontend_context['content_preview'][:15]:  # First 15 pages
            if isinstance(page, dict):
                section = page.get('section', 'unknown')
                content = page.get('content', '')
                if content:
                    context_parts.append(f"Section {section}:\n{content[:2000]}\n")
    
    if context_parts:
        report_context = '\n'.join(context_parts)
        # Increase context limit to 100k for comprehensive analysis
        if len(report_context) > 100000:
            # Keep first 50k and last 50k, truncate middle
            report_context = report_context[:50000] + "\n[... middle content truncated for length ...]\n" + report_context[-50000:]
            logger.info(f"⚠ Context truncated from {len(''.join(context_parts))} to 100k chars")
        
        logger.info(f"✓ Using frontend-provided context: {len(report_context)} chars from {len(context_parts)} sections")
        
        # Log a sample to verify KAV content is included
        if 'kav' in report_context.lower():
            kav_sample = report_context.lower().find('kav')
            # Extract a sample of KAV content for debugging
            sample_start = max(0, kav_sample - 100)
            sample_end = min(len(report_context), kav_sample + 500)
            kav_sample_text = report_context[sample_start:sample_end]
            logger.info(f"✓ KAV content found in context (position: {kav_sample})")
            logger.info(f"✓ KAV sample: {kav_sample_text[:200]}...")
        else:
            logger.warning("⚠ KAV content NOT found in context - may need to check frontend data")
            logger.warning(f"⚠ Context preview (first 500 chars): {report_context[:500]}")
        
        return report_context
    
    return ""


def build_context_from_html(html_content: str, report_metrics: Dict[str, Any]) -> str:
    """Build report context from HTML content (fallback when frontend context not available)."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        context_parts = []
        
        # Helper functions
        def find_section(section_id):
            """Try multiple ways to find a section."""
            section = soup.find('section', {'data-section': section_id})
            if section:
                return section
            section = soup.find('section', {'id': section_id})
            if section:
                return section
            section = soup.find('div', {'id': section_id})
            if section:
                return section
            section = soup.find('section', {'data-section': lambda x: x and x.lower() == section_id.lower()})
            if section:
                return section
            return None
        
        # Extract key sections (works for all sections, not just KAV)
        key_sections = [
            'kav_analysis', 'executive_summary', 'strategic_recommendations',
            'list_growth', 'data_capture', 'automation_overview',
            'campaign_performance', 'segmentation_strategy'
        ]
        
        for section_id in key_sections:
            section = find_section(section_id)
            if section:
                section_text = section.get_text(separator='\n', strip=True)
                if section_text:
                    context_parts.append(f"{section_id.replace('_', ' ').title()}:\n{section_text[:3000]}\n")
                    logger.info(f"✓ Extracted {section_id}: {len(section_text)} chars")
        
        # Extract flow performance data
        flow_patterns = ['welcome', 'abandoned', 'browse', 'post_purchase', 'post-purchase']
        for pattern in flow_patterns:
            flow_section = soup.find('section', {'data-section': lambda x: x and pattern in x.lower()})
            if not flow_section:
                flow_section = soup.find('section', {'id': lambda x: x and pattern in x.lower()})
            if flow_section:
                flow_name = flow_section.get('data-section') or flow_section.get('id', 'Unknown Flow')
                flow_text = flow_section.get_text(separator='\n', strip=True)
                if flow_text:
                    context_parts.append(f"{flow_name} Performance:\n{flow_text[:2000]}\n")
        
        # If we didn't find structured sections, extract all text content as fallback
        if not context_parts:
            logger.warning("No structured sections found, extracting all text content")
            all_text = soup.get_text(separator='\n', strip=True)
            if all_text:
                context_parts.append(f"Full Report Content:\n{all_text[:20000]}\n")
        
        # Combine all context
        report_context = '\n'.join(context_parts)
        
        # Add real report metrics to context
        if report_metrics:
            summary_lines = []
            if report_metrics.get('client_name'):
                summary_lines.append(f"Client: {report_metrics['client_name']}")
            if report_metrics.get('industry'):
                summary_lines.append(f"Industry: {report_metrics['industry']}")
            if report_metrics.get('analysis_period_days'):
                summary_lines.append(f"Analysis Period: {report_metrics['analysis_period_days']} days")
            if report_metrics.get('total_revenue') and report_metrics.get('attributed_revenue'):
                summary_lines.append(f"Revenue Overview: {report_metrics['attributed_revenue']} attributed out of {report_metrics['total_revenue']} total")
            
            if summary_lines:
                report_context = "REPORT OVERVIEW:\n" + "\n".join(summary_lines) + "\n\n" + report_context
        
        # Increase context limit for comprehensive analysis (100k chars)
        if len(report_context) > 100000:
            lines = report_context.split('\n')
            if len(lines) > 100:
                middle_cut = len(lines) // 2
                kept_lines = lines[:middle_cut//2] + ["[... middle content truncated for length ...]"] + lines[-middle_cut//2:]
                report_context = '\n'.join(kept_lines)
            else:
                report_context = report_context[:100000] + "\n[... content truncated ...]"
        
        logger.info(f"✓ Extracted comprehensive report context: {len(report_context)} chars from {len(context_parts)} sections")
        return report_context
        
    except Exception as e:
        logger.error(f"Error extracting context from HTML: {e}", exc_info=True)
        # Fallback: use raw text
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            report_context = soup.get_text(separator='\n', strip=True)[:20000]
            logger.info(f"✓ Using fallback text extraction: {len(report_context)} chars")
            return report_context
        except:
            return "Report content available but could not be parsed. Please ask general questions about Klaviyo audits."

