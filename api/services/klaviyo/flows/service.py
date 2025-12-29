"""Flows service for fetching Klaviyo flows."""
from typing import Dict, List, Optional, Any
import logging

from ..client import KlaviyoClient

logger = logging.getLogger(__name__)


class FlowsService:
    """Service for interacting with Klaviyo flows."""
    
    def __init__(self, client: KlaviyoClient):
        """
        Initialize flows service.
        
        Args:
            client: KlaviyoClient instance
        """
        self.client = client
    
    async def get_flows(self) -> List[Dict[str, Any]]:
        """
        Get all flows.
        
        Returns:
            List of flow objects
        """
        try:
            response = await self.client.request("GET", "/flows/")
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error fetching flows: {e}", exc_info=True)
            return []
    
    async def get_flow(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific flow by ID.
        
        Args:
            flow_id: Flow ID
            
        Returns:
            Flow object if found, None otherwise
        """
        try:
            response = await self.client.request("GET", f"/flows/{flow_id}/")
            return response.get("data")
        except Exception as e:
            logger.error(f"Error fetching flow {flow_id}: {e}", exc_info=True)
            return None
    
    async def get_flow_actions(self, flow_id: str) -> List[Dict[str, Any]]:
        """
        Get actions for a specific flow.
        
        Args:
            flow_id: Flow ID
            
        Returns:
            List of flow action objects
        """
        try:
            response = await self.client.request("GET", f"/flows/{flow_id}/flow-actions/")
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error fetching actions for flow {flow_id}: {e}", exc_info=True)
            return []
    
    async def get_flow_action_messages(self, action_id: str) -> List[Dict[str, Any]]:
        """
        Get messages for a specific flow action.
        
        Args:
            action_id: Flow action ID
            
        Returns:
            List of flow message objects
        """
        try:
            response = await self.client.request("GET", f"/flow-actions/{action_id}/flow-messages/")
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error fetching messages for flow action {action_id}: {e}", exc_info=True)
            return []

