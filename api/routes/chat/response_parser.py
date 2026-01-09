"""
Response parser for chat - parses LLM responses into structured format.
"""
import json
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def parse_llm_response(llm_response: Any) -> tuple[str, List[Dict], List[Dict], List[str], List[Dict]]:
    """
    Parse LLM response into structured format.
    
    Returns:
        tuple: (response_text, suggested_actions, suggested_edits, section_references, navigation_actions)
    """
    response_text = ""
    suggested_actions = []
    suggested_edits = []
    section_references = []
    navigation_actions = []
    
    try:
        if isinstance(llm_response, str):
            raw_response = llm_response.strip()
            
            # Try to extract JSON from response
            if raw_response.startswith('{'):
                # Clean up common issues
                cleaned = raw_response
                # Remove markdown code blocks if present
                if '```json' in cleaned:
                    cleaned = cleaned.split('```json')[1].split('```')[0].strip()
                elif '```' in cleaned:
                    cleaned = cleaned.split('```')[1].split('```')[0].strip()
                
                try:
                    parsed = json.loads(cleaned)
                    response_text = parsed.get("response", "")
                    suggested_actions = parsed.get("suggested_actions", [])
                    suggested_edits = parsed.get("suggested_edits", [])
                    section_references = parsed.get("section_references", [])
                    navigation_actions = parsed.get("navigation_actions", [])
                except json.JSONDecodeError:
                    # Try to extract just the response field
                    response_match = re.search(r'"response"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', cleaned, re.DOTALL)
                    if response_match:
                        response_text = response_match.group(1).replace('\\"', '"').replace('\\n', '\n')
                    else:
                        response_text = raw_response
            else:
                # Check for Python dict-like syntax: {'primary': '...', 'secondary': '...'}
                if "'primary':" in raw_response or "primary:" in raw_response:
                    # Extract text between quotes after 'primary':
                    primary_match = re.search(r"['\"]?primary['\"]?\s*:\s*['\"](.+?)['\"](?:,\s*['\"]?secondary|$)", raw_response, re.DOTALL)
                    secondary_match = re.search(r"['\"]?secondary['\"]?\s*:\s*['\"](.+?)['\"](?:}|\]|$)", raw_response, re.DOTALL)
                    
                    parts = []
                    if primary_match:
                        parts.append(primary_match.group(1).strip())
                    if secondary_match:
                        parts.append(secondary_match.group(1).strip())
                    
                    if parts:
                        response_text = '\n\n'.join(parts)
                    else:
                        response_text = raw_response
                else:
                    # Just use the raw response as text
                    response_text = raw_response
        else:
            # llm_response is already a dict
            parsed = llm_response if isinstance(llm_response, dict) else {"response": str(llm_response)}
            
            # Check if it's the old format with 'primary' and 'secondary' keys
            if 'primary' in parsed and 'secondary' in parsed:
                # Old format - combine primary and secondary
                primary = parsed.get('primary', '')
                secondary = parsed.get('secondary', '')
                response_text = primary
                if secondary:
                    response_text += '\n\n' + secondary
            else:
                # New format with 'response' key
                response_text = parsed.get("response", str(llm_response))
                
                # Handle nested JSON - sometimes the response itself contains JSON as a string
                if isinstance(response_text, str):
                    # Check if response_text is a JSON string wrapped in markdown code blocks
                    if '```json' in response_text or (response_text.strip().startswith('{') and '```' in response_text):
                        # Extract JSON from markdown code blocks
                        if '```json' in response_text:
                            json_part = response_text.split('```json')[1].split('```')[0].strip()
                        elif '```' in response_text:
                            json_part = response_text.split('```')[1].split('```')[0].strip()
                        else:
                            json_part = response_text.strip()
                        
                        try:
                            # Parse the nested JSON
                            nested_parsed = json.loads(json_part)
                            # Extract the actual response text
                            response_text = nested_parsed.get("response", response_text)
                            # Also extract other fields if present
                            if "suggested_actions" in nested_parsed:
                                suggested_actions = nested_parsed.get("suggested_actions", [])
                            if "suggested_edits" in nested_parsed:
                                suggested_edits = nested_parsed.get("suggested_edits", [])
                            if "section_references" in nested_parsed:
                                section_references = nested_parsed.get("section_references", [])
                            if "navigation_actions" in nested_parsed:
                                navigation_actions = nested_parsed.get("navigation_actions", [])
                        except json.JSONDecodeError:
                            # If parsing fails, try to extract just the response field using regex
                            response_match = re.search(r'"response"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', json_part, re.DOTALL)
                            if response_match:
                                response_text = response_match.group(1).replace('\\"', '"').replace('\\n', '\n')
                            # Otherwise, keep the original response_text
            
            # Only set these if they weren't already set from nested parsing
            if not suggested_actions:
                suggested_actions = parsed.get("suggested_actions", [])
            if not suggested_edits:
                suggested_edits = parsed.get("suggested_edits", [])
            if not section_references:
                section_references = parsed.get("section_references", [])
            if not navigation_actions:
                navigation_actions = parsed.get("navigation_actions", [])
        
        # Final cleanup - remove any remaining JSON artifacts
        if response_text:
            response_text = response_text.strip()
            # Remove leading/trailing quotes or brackets
            if response_text.startswith('"') and response_text.endswith('"'):
                response_text = response_text[1:-1]
            # Clean up escaped characters
            response_text = response_text.replace('\\n', '\n').replace('\\"', '"')
            
    except Exception as parse_error:
        logger.warning(f"Error parsing LLM response: {parse_error}")
        # Fallback: treat entire response as text
        response_text = str(llm_response) if llm_response else "I'm sorry, I couldn't generate a proper response."
        suggested_actions = []
        suggested_edits = []
        section_references = []
        navigation_actions = []
    
    return response_text, suggested_actions, suggested_edits, section_references, navigation_actions

