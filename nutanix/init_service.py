"""
Plugin Init Service

Handles plugin initialization and metadata reporting to CloudForet.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class InitService:
    """Plugin initialization service."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def init(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize plugin and return metadata.
        
        CloudForet calls this when plugin starts to get plugin capabilities.
        
        Args:
            params: Request parameters
            
        Returns:
            Plugin metadata and capabilities
        """
        try:
            logger.info("Plugin initialization called")
            
            metadata = {
                'metadata': {
                    'provider': 'nutanix',
                    'name': 'Nutanix Inventory Collector',
                    'service_type': 'inventory.Collector',
                    'icon': 'https://www.nutanix.com/favicon.ico',
                    'display_name': 'Nutanix Inventory Collector Plugin',
                    'capability': {
                        'supported_resource_types': [
                            'compute.Instance',
                            'compute.Disk',
                            'compute.Network'
                        ],
                        'filter_format': [],
                        'supported_schedules': ['daily', 'hourly', 'manual'],
                        'supported_environments': ['on-premises'],
                    },
                    'tags': ['inventory', 'collector', 'nutanix', 'hypervisor'],
                    'version': '1.0.0'
                }
            }
            
            logger.info("Plugin metadata returned")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to initialize plugin: {str(e)}")
            raise
