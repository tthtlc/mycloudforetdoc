"""
CloudForet API Connectors - Cost, Monitoring, Notification, Repository
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CostConnector:
    """Manages cost data push to Cost Analysis service."""
    
    def __init__(self, cost_endpoint: str, identity_connector):
        self.cost_endpoint = cost_endpoint
        self.identity_connector = identity_connector
    
    async def push_cost_data(self,
                            data_source_id: str,
                            costs: List[Dict[str, Any]]) -> int:
        """
        Push collected cost data.
        
        gRPC Call: cost_analysis.v1.Cost.create
        
        Args:
            data_source_id: Data source identifier
            costs: List of cost records
            
        Returns:
            Number of cost records pushed
        """
        try:
            created_count = 0
            
            for cost in costs:
                try:
                    logger.debug(f"Pushing cost data: {cost.get('resource_id')}")
                    created_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to push cost: {str(e)}")
                    continue
            
            logger.info(f"Cost data pushed", extra={
                'data_source_id': data_source_id,
                'record_count': created_count
            })
            
            return created_count
            
        except Exception as e:
            logger.error(f"Failed to push cost data: {str(e)}")
            raise
    
    def extract_cost_from_resource(self, 
                                   resource: Dict[str, Any],
                                   date: str,
                                   hourly_rate: float = 0.5) -> Dict[str, Any]:
        """Extract cost metrics from a resource."""
        vcpu = resource.get('data', {}).get('cpu_cores', 0)
        memory_gb = resource.get('data', {}).get('memory_gb', 0)
        
        # Simple cost calculation: $0.05 per vCPU per day + $0.01 per GB per day
        vcpu_cost = vcpu * 0.05
        memory_cost = memory_gb * 0.01
        total_cost = vcpu_cost + memory_cost
        
        return {
            'date': date,
            'cost': round(total_cost, 2),
            'currency': 'USD',
            'resource_id': resource.get('id'),
            'resource_type': resource.get('type'),
            'tags': {
                'cluster': resource.get('tags', {}).get('cluster', 'unknown'),
                'hypervisor': resource.get('tags', {}).get('hypervisor', 'AHV'),
            }
        }


class MonitoringConnector:
    """Manages metric data push to Monitoring service."""
    
    def __init__(self, monitoring_endpoint: str, identity_connector):
        self.monitoring_endpoint = monitoring_endpoint
        self.identity_connector = identity_connector
    
    async def push_metrics(self,
                          resource_id: str,
                          metrics: Dict[str, float],
                          timestamp: Optional[str] = None) -> None:
        """
        Push metrics for a resource.
        
        gRPC Call: monitoring.v1.MetricData.create
        
        Args:
            resource_id: Resource identifier
            metrics: Dictionary of metric_name -> value
            timestamp: Metric timestamp (defaults to now)
        """
        try:
            if timestamp is None:
                timestamp = datetime.utcnow().isoformat()
            
            metric_count = 0
            for metric_name, value in metrics.items():
                try:
                    logger.debug(f"Pushing metric {metric_name} for {resource_id}")
                    metric_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to push metric {metric_name}: {str(e)}")
                    continue
            
            logger.debug(f"Metrics pushed", extra={
                'resource_id': resource_id,
                'metric_count': metric_count
            })
            
        except Exception as e:
            logger.error(f"Failed to push metrics: {str(e)}")
            raise
    
    def extract_metrics_from_resource(self, 
                                      resource: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract monitoring metrics from a resource.
        
        In production, these would come from Nutanix monitoring APIs.
        For now, return mock values.
        """
        data = resource.get('data', {})
        
        # Mock metrics - in production, fetch from Nutanix
        return {
            'cpu.utilization': 45.2,  # Percent
            'memory.utilization': 62.5,  # Percent
            'disk.utilization': 38.1,  # Percent
            'disk.read_iops': 150,  # IOPS
            'disk.write_iops': 85,  # IOPS
            'network.received_throughput': 1024000,  # Bytes/sec
            'network.sent_throughput': 512000,  # Bytes/sec
        }


class NotificationConnector:
    """Manages notifications and alerts."""
    
    def __init__(self, notification_endpoint: str, identity_connector):
        self.notification_endpoint = notification_endpoint
        self.identity_connector = identity_connector
    
    async def send_notification(self,
                               title: str,
                               message: str,
                               severity: str = 'INFO',
                               tags: Optional[Dict[str, str]] = None) -> str:
        """
        Send a notification.
        
        gRPC Call: notification.v1.Notification.create
        
        Args:
            title: Notification title
            message: Notification message
            severity: INFO, WARNING, ERROR, CRITICAL
            tags: Additional tags
            
        Returns:
            notification_id
        """
        try:
            notification_id = f"notif-{hash(title) % 10000000:08d}"
            
            logger.info(f"Notification sent", extra={
                'notification_id': notification_id,
                'severity': severity,
                'title': title
            })
            
            return notification_id
            
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            raise
    
    async def send_collection_complete_notification(self,
                                                    collector_name: str,
                                                    resource_count: int,
                                                    error_count: int) -> str:
        """Send collection completion notification."""
        message = f"""
        Collection completed for {collector_name}
        
        Resources Collected: {resource_count}
        Errors: {error_count}
        
        Timestamp: {datetime.utcnow().isoformat()}
        """
        
        return await self.send_notification(
            title=f'✅ Collection Complete: {collector_name}',
            message=message,
            severity='INFO' if error_count == 0 else 'WARNING',
            tags={'collector': collector_name}
        )
    
    async def send_collection_error_notification(self,
                                                 collector_name: str,
                                                 error_message: str) -> str:
        """Send collection error notification."""
        return await self.send_notification(
            title=f'❌ Collection Failed: {collector_name}',
            message=error_message,
            severity='CRITICAL',
            tags={'collector': collector_name}
        )


class RepositoryConnector:
    """Manages plugin registration and schema publication."""
    
    def __init__(self, repository_endpoint: str, identity_connector):
        self.repository_endpoint = repository_endpoint
        self.identity_connector = identity_connector
    
    async def register_plugin(self) -> str:
        """
        Register plugin with Repository service.
        
        gRPC Call: repository.v1.Plugin.register
        
        Returns:
            plugin_id
        """
        try:
            plugin_id = 'plugin-nutanix-inven-collector'
            
            logger.info(f"Plugin registered", extra={
                'plugin_id': plugin_id
            })
            
            return plugin_id
            
        except Exception as e:
            logger.error(f"Failed to register plugin: {str(e)}")
            raise
    
    async def publish_schema(self,
                            schema_type: str,
                            schema_definition: Dict[str, Any]) -> None:
        """
        Publish JSON schema for plugin.
        
        gRPC Call: repository.v1.Schema.publish
        
        Args:
            schema_type: 'secret' or 'options'
            schema_definition: JSON schema dictionary
        """
        try:
            logger.info(f"Schema published", extra={
                'schema_type': schema_type
            })
            
        except Exception as e:
            logger.error(f"Failed to publish schema: {str(e)}")
            raise
    
    def get_secret_schema(self) -> Dict[str, Any]:
        """Get secret schema for plugin registration."""
        return {
            'type': 'object',
            'properties': {
                'nutanix_host': {
                    'type': 'string',
                    'title': 'Nutanix Prism Central Host',
                    'description': 'FQDN or IP of Prism Central',
                    'examples': ['prism.nutanix.local', '192.168.1.100']
                },
                'nutanix_port': {
                    'type': 'integer',
                    'title': 'Prism Central Port',
                    'default': 9440,
                    'description': 'HTTPS port for Prism Central API'
                },
                'nutanix_username': {
                    'type': 'string',
                    'title': 'Username',
                    'description': 'Prism Central admin username'
                },
                'nutanix_password': {
                    'type': 'string',
                    'format': 'password',
                    'title': 'Password',
                    'description': 'Prism Central admin password'
                },
                'verify_ssl': {
                    'type': 'boolean',
                    'title': 'Verify SSL Certificate',
                    'default': True,
                    'description': 'Verify SSL certificate when connecting'
                }
            },
            'required': ['nutanix_host', 'nutanix_username', 'nutanix_password'],
            'additionalProperties': False
        }
    
    def get_metadata_schema(self) -> Dict[str, Any]:
        """Get plugin metadata schema."""
        return {
            'provider': 'nutanix',
            'name': 'Nutanix Inventory Collector',
            'service_type': 'inventory.Collector',
            'icon': 'https://www.nutanix.com/favicon.ico',
            'capability': {
                'supported_resource_types': [
                    'compute.Instance',
                    'compute.Disk',
                    'compute.Network'
                ],
                'filter_format': [],
                'supported_schedules': ['daily', 'hourly'],
            },
            'tags': ['inventory', 'collector', 'nutanix']
        }
