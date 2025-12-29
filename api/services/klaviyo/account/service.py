"""
Account service for fetching Klaviyo account information.

Fetches account settings including currency, timezone, and other metadata.
"""
from typing import Dict, Any, Optional
import logging

from ..client import KlaviyoClient

logger = logging.getLogger(__name__)


class AccountService:
    """Service for fetching Klaviyo account information."""
    
    def __init__(self, client: KlaviyoClient):
        """
        Initialize account service.
        
        Args:
            client: KlaviyoClient instance
        """
        self.client = client
        self._account_cache: Optional[Dict[str, Any]] = None
    
    async def get_account(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get account information from Klaviyo.
        
        Returns account details including:
        - preferred_currency: Account currency (e.g., "AUD", "USD", "GBP")
        - timezone: Account timezone (e.g., "Australia/Sydney")
        - contact_information: Organization details
        - industry: Account industry
        
        Args:
            use_cache: Whether to use cached account data (default: True)
            
        Returns:
            Dict with account attributes
        """
        if use_cache and self._account_cache:
            return self._account_cache
        
        try:
            response = await self.client.request("GET", "/accounts/")
            
            # Extract account data
            accounts = response.get("data", [])
            if accounts:
                account = accounts[0]  # Usually only one account
                self._account_cache = account.get("attributes", {})
                return self._account_cache
            else:
                logger.warning("No account data found in response")
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching account information: {e}", exc_info=True)
            return {}
    
    async def get_currency(self) -> str:
        """
        Get account preferred currency.
        
        Returns:
            Currency code (e.g., "AUD", "USD", "GBP") or "USD" as default
        """
        account = await self.get_account()
        currency = account.get("preferred_currency", "USD")
        return currency
    
    async def get_timezone(self) -> str:
        """
        Get account timezone.
        
        Returns:
            Timezone string (e.g., "Australia/Sydney") or "UTC" as default
        """
        account = await self.get_account()
        timezone = account.get("timezone", "UTC")
        return timezone
    
    async def get_account_context(self) -> Dict[str, Any]:
        """
        Get full account context for LLM and formatting.
        
        Returns:
            Dict with currency, timezone, organization name, etc.
        """
        account = await self.get_account()
        contact = account.get("contact_information", {})
        
        return {
            "currency": account.get("preferred_currency", "USD"),
            "timezone": account.get("timezone", "UTC"),
            "organization_name": contact.get("organization_name", ""),
            "industry": account.get("industry", ""),
            "locale": account.get("locale", "en-US")
        }

