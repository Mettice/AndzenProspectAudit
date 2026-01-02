"""
Test endpoints for API connections.
"""
import os
from fastapi import HTTPException
from httpx import HTTPStatusError

from api.services.klaviyo import KlaviyoService


async def test_klaviyo_connection(api_key: str):
    """
    Internal function to test Klaviyo API connection.
    """
    if not api_key or not api_key.strip():
        raise HTTPException(status_code=400, detail="API key is required")
    
    # Validate API key format (Klaviyo keys start with pk_ or sk_)
    if not (api_key.startswith("pk_") or api_key.startswith("sk_")):
        raise HTTPException(
            status_code=400, 
            detail="Invalid API key format. Klaviyo API keys should start with 'pk_' or 'sk_'"
        )
    
    try:
        klaviyo_service = KlaviyoService(api_key=api_key)
        result = await klaviyo_service.test_connection()
        
        if result:
            return {"success": True, "message": "Connection successful"}
        else:
            return {"success": False, "message": "Connection failed: Invalid API key or insufficient permissions. Please check your API key."}
    except HTTPStatusError as e:
        status_code = e.response.status_code if hasattr(e, 'response') and e.response else 400
        error_msg = "Connection failed"
        
        try:
            if hasattr(e, 'response') and e.response:
                error_data = e.response.json()
                errors = error_data.get("errors", [])
                if errors:
                    error_detail = errors[0].get("detail", "")
                    if error_detail:
                        error_msg = error_detail
        except Exception:
            pass
        
        # Map status codes to user-friendly messages
        if status_code == 401:
            error_msg = "Invalid API key. Please check your Klaviyo API key."
        elif status_code == 403:
            error_msg = "API key does not have sufficient permissions."
        elif status_code == 404:
            error_msg = "API endpoint not found. Please check Klaviyo API version."
        elif status_code == 429:
            error_msg = "Rate limit exceeded. Please try again in a moment."
        elif status_code == 400:
            error_msg = error_msg or "Bad request. Please check your API key format."
        
        return {"success": False, "message": error_msg}
    except Exception as e:
        error_msg = str(e)
        
        # Check for common error patterns
        if "401" in error_msg or "Unauthorized" in error_msg:
            error_msg = "Invalid API key. Please check your Klaviyo API key."
        elif "403" in error_msg or "Forbidden" in error_msg:
            error_msg = "API key does not have sufficient permissions."
        elif "404" in error_msg or "Not Found" in error_msg:
            error_msg = "API endpoint not found. Please check Klaviyo API version."
        elif "429" in error_msg or "Too Many Requests" in error_msg:
            error_msg = "Rate limit exceeded. Please try again in a moment."
        elif "timeout" in error_msg.lower():
            error_msg = "Connection timeout. Please check your internet connection."
        else:
            error_msg = f"Connection failed: {error_msg}"
        
        return {"success": False, "message": error_msg}


async def test_llm_connection(request: dict):
    """
    Test LLM API connection (Claude, OpenAI, or Gemini).
    
    Request Body (JSON):
        provider: LLM provider ("claude", "openai", or "gemini")
        api_key: API key for the provider
        model: Optional model name (uses default if not provided)
    """
    provider = request.get("provider")
    api_key = request.get("api_key")
    model = request.get("model")
    
    if not provider:
        raise HTTPException(status_code=400, detail="Provider is required")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    try:
        from api.services.llm import LLMService
        
        # Initialize LLM service with correct parameters
        if provider == "claude":
            llm_service = LLMService(
                default_provider="claude",
                anthropic_api_key=api_key,
                claude_model=model
            )
        elif provider == "openai":
            llm_service = LLMService(
                default_provider="openai",
                openai_api_key=api_key,
                openai_model=model
            )
        elif provider == "gemini":
            llm_service = LLMService(
                default_provider="gemini",
                gemini_api_key=api_key,
                gemini_model=model
            )
        else:
            raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
        
        # Test by generating a simple response
        test_data = {"test": "This is a test connection"}
        test_context = {"client_name": "Test Client"}
        
        try:
            response = await llm_service.generate_insights(
                section="test",
                data=test_data,
                context=test_context,
                provider=provider
            )
            
            # If we get a response (even if it's a fallback), the connection worked
            if response and response.get("primary"):
                return {
                    "success": True,
                    "message": f"{provider.capitalize()} API connection successful",
                    "provider": provider
                }
            else:
                return {
                    "success": False,
                    "message": f"{provider.capitalize()} API connection failed - no response",
                    "provider": provider
                }
        except Exception as e:
            error_msg = str(e)
            # Check for common API key errors
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
                return {
                    "success": False,
                    "message": f"Invalid {provider.capitalize()} API key",
                    "provider": provider,
                    "error": error_msg
                }
            else:
                return {
                    "success": False,
                    "message": f"{provider.capitalize()} API error: {error_msg}",
                    "provider": provider,
                    "error": error_msg
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing {provider} API: {str(e)}")

