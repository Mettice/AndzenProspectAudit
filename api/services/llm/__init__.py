"""
Multi-LLM Service for generating strategic insights.

This service provides a unified interface to multiple LLM providers
(Claude, OpenAI, Gemini) for generating audit insights.

Claude 4.5 Models (set via CLAUDE_MODEL env var):
- claude-sonnet-4-5 (alias - auto-updates to latest, recommended)
  or claude-sonnet-4-5-20250929 (specific version)
- claude-haiku-4-5 (alias - fastest, cheapest)
  or claude-haiku-4-5-20251001 (specific version)
- claude-opus-4-5 (alias - most capable)
  or claude-opus-4-5-20251101 (specific version)

Default: claude-sonnet-4-5 (recommended for audit insights)
"""
import os
import logging
import re
import json
from typing import Dict, Any, Optional, Literal, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import Pydantic for structured output
try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    logger.warning("Pydantic not available. Structured output will be disabled.")

# LLM Provider type
LLMProvider = Literal["claude", "openai", "gemini"]


class LLMService:
    """
    Multi-LLM service for generating strategic insights.
    
    Provides a simple interface: generate_insights(section, data, context)
    """
    
    def __init__(
        self,
        default_provider: LLMProvider = "claude",
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        claude_model: Optional[str] = None,
        openai_model: Optional[str] = None,
        gemini_model: Optional[str] = None,
        llm_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize LLM service.
        
        Args:
            default_provider: Default LLM to use ("claude", "openai", or "gemini")
            anthropic_api_key: Anthropic API key (or from ANTHROPIC_API_KEY env)
            openai_api_key: OpenAI API key (or from OPENAI_API_KEY env)
            gemini_api_key: Google Gemini API key (or from GOOGLE_API_KEY env)
            claude_model: Claude model name (e.g., "claude-sonnet-4-5")
            openai_model: OpenAI model name (e.g., "gpt-4o")
            gemini_model: Gemini model name (e.g., "gemini-2.0-flash-exp")
            llm_config: Optional dict with LLM configuration (overrides individual params)
        """
        # If llm_config is provided, use it to override individual params
        if llm_config:
            default_provider = llm_config.get("provider", default_provider)
            anthropic_api_key = llm_config.get("anthropic_api_key") or anthropic_api_key
            openai_api_key = llm_config.get("openai_api_key") or openai_api_key
            gemini_api_key = llm_config.get("gemini_api_key") or gemini_api_key
            claude_model = llm_config.get("claude_model") or claude_model
            openai_model = llm_config.get("openai_model") or openai_model
            gemini_model = llm_config.get("gemini_model") or gemini_model
        
        self.default_provider = default_provider
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = gemini_api_key or os.getenv("GOOGLE_API_KEY")
        self.claude_model = claude_model
        self.openai_model = openai_model
        self.gemini_model = gemini_model
        
        # Initialize LLM clients (will be created dynamically when needed)
        # This allows each request to use its own API keys from the UI
        self._claude_client = None
        self._openai_client = None
        self._gemini_client = None
        
        # Initialize client creation methods (clients created on-demand)
        self._init_clients()
    
    def _init_clients(self):
        """Initialize LLM clients if packages are available and API keys are provided."""
        # Clients will be created dynamically when needed to use API keys from UI
        # This allows each request to use its own API keys without relying on environment variables
        self._claude_client = None
        self._openai_client = None
        self._gemini_client = None
        logger.info("LLM clients will be initialized dynamically with API keys from request")
    
    async def generate_insights(
        self,
        section: str,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        provider: Optional[LLMProvider] = None
    ) -> Dict[str, Any]:
        """
        Generate strategic insights for a specific audit section.
        
        Args:
            section: Section name (e.g., "kav", "flow_performance", "campaign")
            data: Formatted data for the section
            context: Additional context (industry, benchmarks, etc.)
            provider: LLM provider to use (defaults to self.default_provider)
            
        Returns:
            Dict with insights, typically:
            {
                "primary": "Main narrative text",
                "secondary": "Secondary narrative text",
                "strategic_focus": "focus_area",
                ...
            }
        """
        provider = provider or self.default_provider
        
        # Get prompt template for this section
        from .prompts import get_prompt_template
        prompt = get_prompt_template(section, data, context or {})
        
        # Select client based on provider
        client = self._get_client(provider)
        if not client:
            logger.error(f"No {provider} client available. Falling back to default.")
            provider = "claude" if self._claude_client else "openai"
            client = self._get_client(provider)
        
        if not client:
            logger.error("No LLM clients available. Returning fallback response.")
            return self._get_fallback_response(section, data)
        
        try:
            # Invoke LLM
            response = await client.ainvoke(prompt)
            
            # Parse response
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Log raw response for debugging (first 500 chars)
            logger.info(f"Raw LLM response for {section} (first 500 chars):\n{content[:500]}")
            
            # Parse structured response (JSON or text)
            insights = self._parse_response(content, section)
            
            # Validate that insights is a dict
            if not isinstance(insights, dict):
                logger.error(f"Parsed insights is not a dict for {section}, got {type(insights)}. Using fallback.")
                return self._get_fallback_response(section, data)
            
            # Final validation: ensure primary is actual text, not JSON
            # Use a simpler, more forgiving approach
            if "primary" in insights:
                # Handle case where primary might be a dict (nested JSON object)
                if isinstance(insights["primary"], dict):
                    # If primary is a dict, try to extract text from it
                    if "primary" in insights["primary"]:
                        nested_primary = insights["primary"]["primary"]
                        if isinstance(nested_primary, str) and len(nested_primary.strip()) > 20:
                            insights["primary"] = nested_primary
                            logger.info(f"✓ Extracted primary from nested dict for {section}")
                        else:
                            logger.warning(f"Primary is a dict but nested primary is invalid for {section}")
                            return self._get_fallback_response(section, data)
                    else:
                        # Try to find any string value in the dict
                        for key, val in insights["primary"].items():
                            if isinstance(val, str) and len(val.strip()) > 20:
                                insights["primary"] = val
                                logger.info(f"✓ Extracted primary from dict value for {section}")
                                break
                        else:
                            logger.warning(f"Primary is a dict but no valid text found for {section}")
                            return self._get_fallback_response(section, data)
                
                # Handle case where primary is a string (most common)
                elif isinstance(insights["primary"], str):
                    primary_str = insights["primary"].strip()
                    
                    # If it looks like JSON (starts with {), try to extract text from it
                    if primary_str.startswith('{'):
                        logger.debug(f"Primary appears to be JSON for {section}, attempting extraction...")
                        
                        # Try multiple decode passes (the method now handles this internally)
                        decoded = self._decode_nested_json_string(primary_str, max_depth=10)
                        
                        # Check if we got actual text (not more JSON)
                        if isinstance(decoded, str):
                            decoded_clean = decoded.strip()
                            # If decoded result is still JSON-like, try multiple extraction strategies
                            if decoded_clean.startswith('{') and '"primary"' in decoded_clean[:500]:
                                logger.debug(f"Decoded result still looks like JSON for {section}, trying extraction strategies...")
                                logger.debug(f"Decoded content (first 500 chars): {decoded_clean[:500]}")
                                
                                # Strategy 1: Try parsing as JSON first (handles formatted JSON)
                                extracted_text = None
                                try:
                                    parsed_json = json.loads(decoded_clean)
                                    if isinstance(parsed_json, dict) and "primary" in parsed_json:
                                        extracted_text = parsed_json["primary"]
                                        if isinstance(extracted_text, str):
                                            extracted_clean = extracted_text.strip()
                                            # If it's plain text (not JSON), use it
                                            if not extracted_clean.startswith('{') and not extracted_clean.startswith('[') and len(extracted_clean) > 20:
                                                insights["primary"] = extracted_text
                                                logger.info(f"✓ Extracted text via JSON parse for {section}")
                                                extracted_text = "SUCCESS"  # Mark as success to skip other strategies
                                            else:
                                                extracted_text = None
                                        elif isinstance(extracted_text, list) and all(isinstance(item, str) for item in extracted_text):
                                            # Primary is an array of strings
                                            insights["primary"] = '\n\n'.join(extracted_text)
                                            logger.info(f"✓ Extracted text from array via JSON parse for {section}")
                                            extracted_text = "SUCCESS"  # Mark as success
                                        else:
                                            extracted_text = None
                                except (json.JSONDecodeError, ValueError, TypeError) as e:
                                    logger.debug(f"JSON parse failed for {section}: {e}")
                                    pass
                                
                                # If Strategy 1 succeeded, skip other strategies
                                if extracted_text == "SUCCESS":
                                    pass  # Continue to final validation
                                
                                # Strategy 2: Try regex extraction (handles malformed JSON)
                                if not extracted_text:
                                    # More flexible regex that handles multiline and escaped quotes
                                    patterns = [
                                        r'"primary"\s*:\s*"((?:[^"\\]|\\.|\\n|\\t)*)"',  # Standard pattern
                                        r'"primary"\s*:\s*"([^"]*)"',  # Simpler pattern for unescaped text
                                        r'"primary"\s*:\s*"((?:.|\\n|\\t)*?)"(?=\s*[,}])',  # Non-greedy with lookahead
                                    ]
                                    for pattern in patterns:
                                        match = re.search(pattern, decoded_clean, re.DOTALL | re.MULTILINE)
                                        if match:
                                            extracted = match.group(1)
                                            # Unescape JSON escape sequences
                                            extracted = extracted.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                                            extracted = extracted.replace('\\\\', '\\').replace('\\r', '\r')
                                            extracted = extracted.strip()
                                            if len(extracted) > 20:  # Only use if we got substantial text
                                                extracted_text = extracted
                                                logger.info(f"✓ Extracted text via regex pattern for {section}")
                                                break
                                
                                # Strategy 3: Try to find text between quotes after "primary":
                                if not extracted_text:
                                    # Look for the pattern: "primary": "text" or "primary":\n    "text"
                                    match = re.search(r'"primary"\s*:\s*"([^"]{50,})"', decoded_clean, re.DOTALL)
                                    if match:
                                        extracted_text = match.group(1)
                                        extracted_text = extracted_text.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\').strip()
                                        if len(extracted_text) > 20:
                                            logger.info(f"✓ Extracted text via simple regex for {section}")
                                
                                # Strategy 4: Last resort - find any substantial quoted text (likely the actual content)
                                if not extracted_text:
                                    # Find the longest quoted string that looks like actual text (not JSON structure)
                                    all_quoted = re.findall(r'"((?:[^"\\]|\\.){50,})"', decoded_clean, re.DOTALL)
                                    for quoted_text in all_quoted:
                                        # Unescape
                                        text = quoted_text.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                                        text = text.replace('\\\\', '\\').replace('\\r', '\r').strip()
                                        # Skip if it looks like JSON structure
                                        if not text.startswith('{') and '"primary"' not in text[:100] and len(text) > 50:
                                            extracted_text = text
                                            logger.info(f"✓ Extracted text via fallback extraction for {section}")
                                            break
                                
                                # Check if extraction succeeded (either got text or marked as SUCCESS)
                                if extracted_text and extracted_text != "SUCCESS" and len(extracted_text.strip()) > 20:
                                    insights["primary"] = extracted_text
                                elif extracted_text == "SUCCESS":
                                    # Already set in Strategy 1, continue
                                    pass
                                else:
                                    logger.warning(f"Could not extract text from JSON for {section}, using fallback")
                                    logger.warning(f"Primary content (first 500 chars):\n{primary_str[:500]}")
                                    logger.warning(f"Decoded content (first 500 chars):\n{decoded_clean[:500]}")
                                    return self._get_fallback_response(section, data)
                            else:
                                # Successfully decoded to text
                                insights["primary"] = decoded
                                logger.debug(f"✓ Successfully decoded primary for {section}")
                        else:
                            logger.warning(f"Decoded primary is not a string for {section}, using fallback")
                            return self._get_fallback_response(section, data)
                    else:
                        # Primary is a string but doesn't start with {, so it's already text
                        pass  # No action needed, already valid text
            
            logger.info(f"✓ Generated {section} insights using {provider}")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights for {section}: {e}", exc_info=True)
            return self._get_fallback_response(section, data)
    
    def _get_client(self, provider: LLMProvider):
        """Get or create LLM client for provider using API keys from instance."""
        if provider == "claude":
            if not self._claude_client and self.anthropic_api_key:
                self._claude_client = self._create_claude_client()
            return self._claude_client
        elif provider == "openai":
            if not self._openai_client and self.openai_api_key:
                self._openai_client = self._create_openai_client()
            return self._openai_client
        elif provider == "gemini":
            if not self._gemini_client and self.gemini_api_key:
                self._gemini_client = self._create_gemini_client()
            return self._gemini_client
        else:
            return None
    
    def _create_claude_client(self):
        """Create Claude client with API key from UI (not environment)."""
        try:
            from langchain_anthropic import ChatAnthropic
            # Use full version ID instead of alias for older LangChain versions
            # Alias 'claude-sonnet-4-5' not recognized by langchain-anthropic < 0.2.0
            claude_model = self.claude_model or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
            
            # Update outdated Claude 3 models to Claude 4
            if claude_model and "claude-3-" in claude_model:
                logger.warning(f"Updating outdated Claude 3 model {claude_model} to Claude 4")
                claude_model = "claude-sonnet-4-20250514"
            # Use environment variable temporarily during client creation
            # This is the only way langchain-anthropic accepts the key
            original_key = os.getenv("ANTHROPIC_API_KEY")
            try:
                if self.anthropic_api_key:
                    os.environ["ANTHROPIC_API_KEY"] = self.anthropic_api_key
                client = ChatAnthropic(
                    model=claude_model,
                    temperature=0.7,
                    max_tokens=4096
                )
                logger.info(f"✓ Claude client created with model: {claude_model} (using API key from request)")
                return client
            finally:
                # Restore original key if it existed
                if original_key:
                    os.environ["ANTHROPIC_API_KEY"] = original_key
                elif "ANTHROPIC_API_KEY" in os.environ and not original_key:
                    # Only delete if we set it and it wasn't there before
                    del os.environ["ANTHROPIC_API_KEY"]
        except ImportError:
            logger.warning("langchain-anthropic not installed. Claude support unavailable.")
            return None
        except Exception as e:
            logger.warning(f"Failed to create Claude client: {e}")
            return None
    
    def _create_openai_client(self):
        """Create OpenAI client with API key from UI (not environment)."""
        try:
            from langchain_openai import ChatOpenAI
            openai_model = self.openai_model or os.getenv("OPENAI_MODEL", "gpt-4o")
            
            # Newer OpenAI models (gpt-4o, o1, o3, etc.) require max_completion_tokens
            # instead of max_tokens. Pass via model_kwargs to avoid deprecation warning.
            # Older models will accept max_completion_tokens as well.
            client = ChatOpenAI(
                model=openai_model,
                api_key=self.openai_api_key,
                temperature=0.7,
                model_kwargs={"max_completion_tokens": 4096}  # Pass via model_kwargs for newer LangChain versions
            )
            logger.info(f"✓ OpenAI client created with model: {openai_model} (using API key from request)")
            return client
        except ImportError:
            logger.warning("langchain-openai not installed. OpenAI support unavailable.")
            return None
        except Exception as e:
            logger.warning(f"Failed to create OpenAI client: {e}")
            # If max_completion_tokens fails, try without it (let LangChain use defaults)
            try:
                logger.info(f"Retrying OpenAI client creation without max_completion_tokens...")
                client = ChatOpenAI(
                    model=openai_model,
                    api_key=self.openai_api_key,
                    temperature=0.7
                )
                logger.info(f"✓ OpenAI client created with model: {openai_model} (using defaults)")
                return client
            except Exception as e2:
                logger.warning(f"Failed to create OpenAI client on retry: {e2}")
                return None
    
    def _create_gemini_client(self):
        """Create Gemini client with API key from UI (not environment)."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            gemini_model = self.gemini_model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
            client = ChatGoogleGenerativeAI(
                model=gemini_model,
                google_api_key=self.gemini_api_key,  # Gemini supports direct google_api_key parameter
                temperature=0.7,
                max_tokens=4096
            )
            logger.info(f"✓ Gemini client created with model: {gemini_model} (using API key from request)")
            return client
        except ImportError:
            logger.warning("langchain-google-genai not installed. Gemini support unavailable.")
            return None
        except Exception as e:
            logger.warning(f"Failed to create Gemini client: {e}")
            return None
    
    def _decode_nested_json_string(self, value: str, max_depth: int = 10) -> str:
        """
        Recursively decode nested JSON strings until we get actual text.
        
        Handles cases like: "{\"primary\": \"text\"}" -> "text"
        Also handles formatted JSON with newlines and indentation.
        
        This is a simpler, more aggressive approach that tries multiple strategies.
        """
        if not isinstance(value, str) or max_depth <= 0:
            return value
        
        original_value = value
        value = value.strip()
        
        # Strategy 1: Try parsing as JSON object directly
        if value.startswith('{'):
            try:
                # Try parsing with json.loads (handles formatted JSON with newlines)
                nested = json.loads(value)
                if isinstance(nested, dict):
                    # Priority: look for "primary" key first
                    if "primary" in nested:
                        primary_val = nested["primary"]
                        if isinstance(primary_val, str):
                            # Check if it's already plain text (not JSON)
                            primary_clean = primary_val.strip()
                            if not primary_clean.startswith('{') and not primary_clean.startswith('['):
                                # It's already plain text, return it
                                return primary_val
                            # Otherwise, recursively decode
                            decoded = self._decode_nested_json_string(primary_val, max_depth - 1)
                            # Return the decoded value (even if it's still JSON, we'll handle it in the caller)
                            return decoded
                        elif isinstance(primary_val, list) and all(isinstance(item, str) for item in primary_val):
                            # Primary is an array of strings, join them
                            return '\n\n'.join(primary_val)
                        elif not isinstance(primary_val, (dict, list)):
                            # If primary is not a string but also not a complex type, return it as string
                            return str(primary_val)
                    
                    # Fallback: find first meaningful string value
                    for key, val in nested.items():
                        if isinstance(val, str) and len(val.strip()) > 10:
                            val_clean = val.strip()
                            # If it's already plain text, return it
                            if not val_clean.startswith('{') and not val_clean.startswith('['):
                                return val
                            # Otherwise, recursively decode
                            decoded = self._decode_nested_json_string(val, max_depth - 1)
                            if isinstance(decoded, str) and not decoded.strip().startswith('{'):
                                return decoded
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                # JSON parsing failed, try regex extraction
                pass
        
        # Strategy 2: Try parsing as JSON-encoded string (double-quoted)
        if value.startswith('"') and value.endswith('"') and len(value) > 2:
            try:
                decoded = json.loads(value)
                if isinstance(decoded, str) and decoded != value:
                    # Recursively decode the decoded string
                    return self._decode_nested_json_string(decoded, max_depth - 1)
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Strategy 3: Try to extract text from malformed JSON using regex
        # Look for "primary": "..." pattern and extract the text (JSON uses double quotes)
        if '"primary"' in value:
            # Try multiple regex patterns to handle different JSON formats
            patterns = [
                # Pattern 1: Standard JSON with escaped quotes: "primary": "text"
                r'"primary"\s*:\s*"((?:[^"\\]|\\.)*)"',
                # Pattern 2: Handle multiline with newlines: "primary":\n    "text"
                r'"primary"\s*:\s*["\']((?:[^"\'\\]|\\.)*)["\']',
                # Pattern 3: Non-greedy match to stop at next key or closing brace
                r'"primary"\s*:\s*"((?:[^"\\]|\\.)*?)"(?=\s*[,}])',
            ]
            for pattern in patterns:
                match = re.search(pattern, value, re.DOTALL | re.MULTILINE)
                if match:
                    extracted = match.group(1)
                    # Unescape JSON escape sequences
                    try:
                        # Replace common escape sequences in order
                        extracted = extracted.replace('\\\\', '\\')  # Must be first
                        extracted = extracted.replace('\\"', '"')
                        extracted = extracted.replace('\\n', '\n')
                        extracted = extracted.replace('\\t', '\t')
                        extracted = extracted.replace('\\r', '\r')
                        extracted = extracted.strip()
                        # Recursively decode if it's still JSON
                        if extracted.startswith('{') and max_depth > 1:
                            return self._decode_nested_json_string(extracted, max_depth - 1)
                        # Only return if we got substantial text
                        if len(extracted) > 10:
                            return extracted
                    except Exception:
                        pass
        
        # Strategy 4: If it looks like JSON but parsing failed, try to extract text between quotes
        # This is a last resort for malformed JSON
        if value.startswith('{') and '"primary"' in value:
            # Try to find text after "primary": and before the next key or closing brace
            # Match: "primary": "any text here" (handling escaped quotes and multiline)
            patterns = [
                r'"primary"\s*:\s*"((?:[^"\\]|\\.)*?)"(?=\s*[,}])',  # Non-greedy with lookahead
                r'"primary"\s*:\s*"((?:[^"\\]|\\.)*)"',  # Greedy match
            ]
            for pattern in patterns:
                match = re.search(pattern, value, re.DOTALL | re.MULTILINE)
                if match:
                    extracted = match.group(1)
                    # Unescape
                    extracted = extracted.replace('\\\\', '\\').replace('\\"', '"')
                    extracted = extracted.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
                    extracted = extracted.strip()
                    # If extracted text is still JSON-like, decode again
                    if extracted.startswith('{') and max_depth > 1:
                        return self._decode_nested_json_string(extracted, max_depth - 1)
                    # Only return if we got substantial text
                    if len(extracted) > 10:
                        return extracted
        
        # Strategy 5: Last resort - try to extract any substantial text content
        # Look for text that's not JSON structure (not just braces, quotes, keys)
        if value.startswith('{') and len(value) > 50:
            # Try to find any quoted string that's longer than 30 chars (likely actual content)
            text_matches = re.findall(r'"(?:[^"\\]|\\.){30,}"', value, re.DOTALL)
            for match in text_matches:
                # Remove quotes and unescape
                text = match[1:-1]  # Remove surrounding quotes
                text = text.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                text = text.replace('\\\\', '\\').replace('\\r', '\r').strip()
                # If it doesn't look like JSON structure and is substantial
                if len(text) > 30 and not text.strip().startswith('{') and '"primary"' not in text[:50]:
                    return text
        
        # Return as-is if we can't decode it
        return original_value
    
    def _parse_response(self, content: str, section: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured format.
        
        Tries to parse as JSON first, falls back to text extraction.
        Handles markdown code blocks, extra text, and malformed JSON.
        """
        # Clean content: remove markdown code blocks
        content = re.sub(r'```json\s*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'```\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^```\s*', '', content, flags=re.MULTILINE)
        content = content.strip()
        
        # Try to parse as JSON
        try:
            # Look for JSON in response
            if "{" in content and "}" in content:
                # Try to find the JSON object boundaries more accurately
                # Look for the first { and matching }
                start = content.find("{")
                if start != -1:
                    # Find matching closing brace
                    brace_count = 0
                    end = start
                    for i in range(start, len(content)):
                        if content[i] == '{':
                            brace_count += 1
                        elif content[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end = i + 1
                                break
                    
                    if end > start:
                        json_str = content[start:end]
                        # Clean up common JSON issues
                        json_str = json_str.strip()
                        # Remove trailing commas before closing braces/brackets
                        json_str = re.sub(r',\s*}', '}', json_str)
                        json_str = re.sub(r',\s*]', ']', json_str)
                        
                        parsed = json.loads(json_str)
                        logger.info(f"✓ Successfully parsed JSON for {section} ({len(json_str)} chars)")
                        
                        # Ensure we return a dict, not a string
                        if isinstance(parsed, dict):
                            # Check if primary contains JSON (nested JSON response)
                            if "primary" in parsed and isinstance(parsed["primary"], str):
                                primary_str = parsed["primary"].strip()
                                
                                # Check if primary contains JSON (array or object)
                                if primary_str.startswith('[') or primary_str.startswith('{'):
                                    logger.debug(f"Primary field contains JSON for {section}, attempting to extract actual primary text...")
                                    
                                    # Strategy 1: If it starts with [, try to extract array of strings
                                    if primary_str.startswith('['):
                                        try:
                                            # Find the end of the array
                                            bracket_count = 0
                                            array_end = -1
                                            for i, char in enumerate(primary_str):
                                                if char == '[':
                                                    bracket_count += 1
                                                elif char == ']':
                                                    bracket_count -= 1
                                                    if bracket_count == 0:
                                                        array_end = i + 1
                                                        break
                                            
                                            if array_end > 0:
                                                array_str = primary_str[:array_end]
                                                array_parsed = json.loads(array_str)
                                                if isinstance(array_parsed, list) and all(isinstance(item, str) for item in array_parsed):
                                                    # Join array items into paragraphs
                                                    parsed["primary"] = '\n\n'.join(array_parsed)
                                                    logger.info(f"✓ Extracted primary text from JSON array for {section}")
                                                else:
                                                    # Not a simple string array, decode it
                                                    parsed["primary"] = self._decode_nested_json_string(primary_str)
                                            else:
                                                parsed["primary"] = self._decode_nested_json_string(primary_str)
                                        except (json.JSONDecodeError, ValueError, TypeError):
                                            # Can't parse as array, decode it
                                            parsed["primary"] = self._decode_nested_json_string(primary_str)
                                    
                                    # Strategy 2: If it starts with {, try to parse and extract primary field
                                    elif primary_str.startswith('{'):
                                        try:
                                            nested_parsed = json.loads(primary_str)
                                            if isinstance(nested_parsed, dict) and "primary" in nested_parsed:
                                                # Extract the actual primary text
                                                actual_primary = nested_parsed.get("primary", "")
                                                if isinstance(actual_primary, str):
                                                    actual_clean = actual_primary.strip()
                                                    # If it's plain text (not JSON), use it
                                                    if not actual_clean.startswith('{') and not actual_clean.startswith('['):
                                                        parsed["primary"] = actual_primary
                                                        logger.info(f"✓ Extracted actual primary text from nested JSON for {section}")
                                                    else:
                                                        # Still nested, decode it
                                                        parsed["primary"] = self._decode_nested_json_string(actual_primary)
                                                elif isinstance(actual_primary, list) and all(isinstance(item, str) for item in actual_primary):
                                                    # Primary is an array of strings
                                                    parsed["primary"] = '\n\n'.join(actual_primary)
                                                    logger.info(f"✓ Extracted primary text from array in nested response for {section}")
                                                else:
                                                    # Not a string or array, decode the whole thing
                                                    parsed["primary"] = self._decode_nested_json_string(primary_str)
                                                # Also extract other fields if they exist
                                                for key in ["secondary", "root_cause_analysis", "risk_flags", "quick_wins", "recommendations", "areas_of_opportunity"]:
                                                    if key in nested_parsed and key not in parsed:
                                                        parsed[key] = nested_parsed[key]
                                            else:
                                                # Not the structure we expected, decode normally
                                                parsed["primary"] = self._decode_nested_json_string(primary_str)
                                        except (json.JSONDecodeError, ValueError, TypeError) as e:
                                            logger.debug(f"Failed to parse nested JSON in primary for {section}: {e}")
                                            # Can't parse, decode normally
                                            parsed["primary"] = self._decode_nested_json_string(primary_str)
                                else:
                                    # Primary is already plain text, no decoding needed
                                    logger.debug(f"Primary field is already plain text for {section}")
                                logger.debug(f"Processed primary field for {section}")
                            
                            if "secondary" in parsed and isinstance(parsed["secondary"], str):
                                parsed["secondary"] = self._decode_nested_json_string(parsed["secondary"])
                                logger.debug(f"Decoded secondary field for {section}")
                            
                            return parsed
                        else:
                            logger.warning(f"Parsed JSON is not a dict for {section}, got {type(parsed)}")
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed for {section}: {e}")
            logger.debug(f"Failed JSON content (first 500 chars): {content[:500]}")
            # Try to extract just the JSON part more carefully
            try:
                # Look for JSON between ```json and ``` - use proper brace counting
                json_start_marker = content.find('```json')
                if json_start_marker == -1:
                    json_start_marker = content.find('```')
                json_end_marker = content.find('```', json_start_marker + 7) if json_start_marker != -1 else -1
                if json_start_marker != -1 and json_end_marker != -1:
                    json_block = content[json_start_marker + 7:json_end_marker].strip()
                    # Now find the actual JSON object within the block
                    if "{" in json_block:
                        start = json_block.find("{")
                        brace_count = 0
                        end = start
                        for i in range(start, len(json_block)):
                            if json_block[i] == '{':
                                brace_count += 1
                            elif json_block[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end = i + 1
                                    break
                        if end > start:
                            json_str = json_block[start:end]
                            json_str = re.sub(r',\s*}', '}', json_str)
                            json_str = re.sub(r',\s*]', ']', json_str)
                            parsed = json.loads(json_str)
                            if isinstance(parsed, dict):
                                logger.info(f"✓ Successfully parsed JSON from markdown block for {section}")
                                return parsed
            except Exception as e2:
                logger.debug(f"Markdown block extraction also failed: {e2}")
                # Try one more time with a more aggressive approach
                try:
                    # Remove all markdown code block markers first
                    cleaned = re.sub(r'```json\s*', '', content, flags=re.IGNORECASE)
                    cleaned = re.sub(r'```\s*', '', cleaned)
                    cleaned = cleaned.strip()
                    # Try to find JSON again
                    if "{" in cleaned and "}" in cleaned:
                        start = cleaned.find("{")
                        brace_count = 0
                        end = start
                        for i in range(start, len(cleaned)):
                            if cleaned[i] == '{':
                                brace_count += 1
                            elif cleaned[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end = i + 1
                                    break
                        if end > start:
                            json_str = cleaned[start:end]
                            json_str = re.sub(r',\s*}', '}', json_str)
                            json_str = re.sub(r',\s*]', ']', json_str)
                            parsed = json.loads(json_str)
                            if isinstance(parsed, dict):
                                logger.info(f"✓ Successfully parsed JSON after aggressive cleaning for {section}")
                                return parsed
                except Exception as e3:
                    logger.debug(f"Aggressive cleaning also failed: {e3}")
        except Exception as e:
            logger.warning(f"Error parsing JSON for {section}: {e}")
            logger.debug(f"Error content (first 500 chars): {content[:500]}")
        
        # Fallback: extract text and structure it
        # For KAV section, we expect primary and secondary narratives
        if section == "kav":
            lines = content.split("\n")
            primary = ""
            secondary = ""
            
            in_primary = False
            in_secondary = False
            
            for line in lines:
                line_lower = line.lower()
                if "primary" in line_lower or "overview" in line_lower or "performance" in line_lower:
                    in_primary = True
                    in_secondary = False
                    continue
                if "secondary" in line_lower or "implications" in line_lower or "strategic" in line_lower:
                    in_primary = False
                    in_secondary = True
                    continue
                
                if in_primary:
                    primary += line.strip() + " "
                elif in_secondary:
                    secondary += line.strip() + " "
            
            return {
                "primary": primary.strip() or content[:500],  # Fallback to first 500 chars
                "secondary": secondary.strip() or "",
                "strategic_focus": "optimization"  # Default
            }
        
        # For data_capture section, we expect primary and recommendations
        if section == "data_capture":
            lines = content.split("\n")
            primary = ""
            recommendations = []
            
            in_primary = False
            in_recommendations = False
            
            for line in lines:
                line_lower = line.lower().strip()
                line_stripped = line.strip()
                
                if not line_stripped:
                    continue
                    
                if "primary" in line_lower or ("analysis" in line_lower and "performance" in line_lower):
                    in_primary = True
                    in_recommendations = False
                    continue
                if "recommendation" in line_lower or "suggest" in line_lower or "opportunit" in line_lower:
                    in_recommendations = True
                    in_primary = False
                    # Check if this line itself is a recommendation
                    if line_stripped and not line_stripped.lower().startswith("recommendation"):
                        # Extract recommendation text (remove bullets, numbers, etc.)
                        rec_text = line_stripped.lstrip("- •*1234567890. ").strip()
                        if rec_text:
                            recommendations.append(rec_text)
                    continue
                
                if in_primary:
                    primary += line_stripped + " "
                elif in_recommendations:
                    # Extract recommendation text
                    rec_text = line_stripped.lstrip("- •*1234567890. ").strip()
                    if rec_text and len(rec_text) > 20:  # Only add substantial recommendations
                        recommendations.append(rec_text)
            
            return {
                "primary": primary.strip() or content[:500],
                "recommendations": recommendations[:5] if recommendations else []  # Limit to 5 recommendations
            }
        
        # Generic fallback
        return {
            "primary": content[:1000] if len(content) > 1000 else content,
            "secondary": "",
            "strategic_focus": "analysis"
        }
    
    def _get_fallback_response(self, section: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Return fallback response if LLM fails."""
        logger.warning(f"Using fallback response for {section} section")
        
        if section == "kav":
            kav_pct = data.get("metrics", {}).get("kav_percentage", 0)
            return {
                "primary": f"Klaviyo Attributed Value (KAV) represents {kav_pct:.1f}% of total revenue, indicating the impact of email and SMS marketing efforts.",
                "secondary": "Strategic analysis requires LLM service to be properly configured.",
                "strategic_focus": "optimization"
            }
        elif section == "list_growth":
            # Get list growth data from context
            list_data = data.get("data", {})
            current_total = list_data.get("current_total", 0)
            net_change = list_data.get("net_change", 0)
            period_months = list_data.get("period_months", 6)
            client_name = data.get("context", {}).get("client_name", "the client")
            
            if current_total > 0:
                primary = f"Email List Growth Overview: {client_name} has {current_total:,} total subscribers as of the analysis period. Over the last {period_months} months, the list has shown a net change of {net_change:+,} subscribers."
            else:
                primary = f"Email List Growth Overview: Analysis of list growth data for {client_name} over the last {period_months} months."
            
            return {
                "primary": primary,
                "secondary": "Detailed analysis requires LLM service to be properly configured.",
                "strategic_focus": "analysis"
            }
        
        return {
            "primary": "Analysis pending LLM service configuration.",
            "secondary": "",
            "strategic_focus": "analysis"
        }

