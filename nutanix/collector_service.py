"""
Collector Service

Main service that orchestrates collection workflow using all CloudForet API connectors.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta

from connector.identity_connector import IdentityConnector, SecretManager
from connector.inventory_connector import InventoryConnector
from connector.nutanix_connector import NutanixConnector, NutanixResourceCollector
from connector.other_connectors import (
    CostConnector, MonitoringConnector, NotificationConnector, RepositoryConnector
)

logger = logging.getLogger(__name__)


class CollectorService:
    """Main collection service."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize connectors
        self.identity_connector = IdentityConnector(
            config['identity_endpoint'],
            config['plugin_api_key'],
            config['domain_id']
        )
        
        self.secret_manager = SecretManager(self.identity_connector)
        
        self.inventory_connector = InventoryConnector(
            config['inventory_endpoint'],
            self.identity_connector
        )
        
        self.cost_connector = CostConnector(
            config['cost_endpoint'],
            self.identity_connector
        )
        
        self.monitoring_connector = MonitoringConnector(
            config['monitoring_endpoint'],
            self.identity_connector
        )
        
        self.notification_connector = NotificationConnector(
            config['notification_endpoint'],
            self.identity_connector
        )
        
        self.repository_connector = RepositoryConnector(
            config['repository_endpoint'],
            self.identity_connector
        )
    
    async def collect(self, params: Dict[str, Any]) -> None:
        """
        Main collection workflow.
        
        CloudForet calls this when a collection job is triggered.
        
        gRPC Call: inventory.Collector.collect
        
        Args:
            params: Collection parameters containing:
                - job_id: Collection job ID
                - collector_id: Collector ID
                - service_account_ids: List of service accounts to collect from
                - secret_id: Secret containing Nutanix credentials
        """
        job_id = params.get('job_id')
        collector_id = params.get('collector_id')
        service_account_ids = params.get('service_account_ids', [])
        
        logger.info("Starting collection", extra={
            'job_id': job_id,
            'collector_id': collector_id,
            'account_count': len(service_account_ids)
        })
        
        total_resources = 0
        total_errors = 0
        
        try:
            # Step 1: Create job tasks for each service account
            logger.info("Creating job tasks...")
            job_tasks = await self.inventory_connector.create_job_tasks(
                job_id,
                service_account_ids
            )
            
            # Step 2: Process each account
            for idx, task_id in enumerate(job_tasks):
                account_info = service_account_ids[idx]
                account_id = account_info.get('service_account_id')
                secret_id = account_info.get('secret_id')
                
                try:
                    task_result = await self._process_account(
                        task_id,
                        account_id,
                        secret_id,
                        collector_id
                    )
                    
                    total_resources += task_result['resource_count']
                    total_errors += task_result['error_count']
                    
                except Exception as e:
                    logger.error(f"Error processing account {account_id}: {str(e)}")
                    total_errors += 1
                    
                    # Mark task as failed
                    await self.inventory_connector.update_job_task_progress(
                        task_id, 'ERROR'
                    )
            
            # Step 3: Send completion notification
            await self.notification_connector.send_collection_complete_notification(
                collector_id,
                total_resources,
                total_errors
            )
            
            logger.info("Collection completed successfully", extra={
                'job_id': job_id,
                'total_resources': total_resources,
                'total_errors': total_errors
            })
            
        except Exception as e:
            logger.error(f"Collection failed: {str(e)}")
            await self.notification_connector.send_collection_error_notification(
                collector_id,
                str(e)
            )
            raise
    
    async def _process_account(self,
                              task_id: str,
                              account_id: str,
                              secret_id: str,
                              collector_id: str) -> Dict[str, int]:
        """
        Process collection for a single account.
        
        Args:
            task_id: Job task ID
            account_id: Service account ID
            secret_id: Secret ID with Nutanix credentials
            collector_id: Collector ID
            
        Returns:
            Dictionary with resource_count and error_count
        """
        logger.info(f"Processing account {account_id}")
        
        try:
            # Mark task as started
            await self.inventory_connector.update_job_task_progress(
                task_id, 'STARTED'
            )
            
            # Step 1: Fetch credentials
            logger.info("Fetching credentials...")
            secret_data = await self.secret_manager.get_secret(secret_id)
            credentials = secret_data.get('data', {})
            
            # Step 2: Create Nutanix connector
            nutanix = NutanixConnector(
                host=credentials.get('nutanix_host'),
                username=credentials.get('nutanix_username'),
                password=credentials.get('nutanix_password'),
                port=credentials.get('nutanix_port', 9440),
                verify_ssl=credentials.get('verify_ssl', True)
            )
            
            # Test connection
            if not await nutanix.test_connection():
                raise Exception("Failed to connect to Nutanix")
            
            # Step 3: Collect resources
            logger.info("Collecting resources from Nutanix...")
            collector = NutanixResourceCollector(nutanix)
            
            resources_gen = collector.collect_all_resources()
            
            # Step 4: Stream resources to CloudForet
            resource_count = await self._stream_resources(
                task_id,
                resources_gen,
                collector_id
            )
            
            # Step 5: Mark task as completed
            await self.inventory_connector.complete_job_task(
                task_id,
                {
                    'created_count': resource_count,
                    'updated_count': 0,
                    'deleted_count': 0,
                    'error_count': 0
                }
            )
            
            # Close Nutanix connection
            await nutanix.close()
            
            logger.info(f"Account {account_id} processing completed", extra={
                'resource_count': resource_count
            })
            
            return {
                'resource_count': resource_count,
                'error_count': 0
            }
            
        except Exception as e:
            logger.error(f"Failed to process account {account_id}: {str(e)}")
            return {
                'resource_count': 0,
                'error_count': 1
            }
    
    async def _stream_resources(self,
                               task_id: str,
                               resources_gen: AsyncGenerator,
                               collector_id: str) -> int:
        """
        Stream resources to CloudForet and extract cost/metrics data.
        
        Args:
            task_id: Job task ID
            resources_gen: Async generator of resources
            collector_id: Collector ID
            
        Returns:
            Number of resources processed
        """
        try:
            resource_count = 0
            costs = []
            
            async for resource in resources_gen:
                try:
                    # Create cloud service in inventory
                    await self.inventory_connector.create_cloud_service(
                        task_id,
                        resource
                    )
                    
                    # Extract cost data
                    cost = self.cost_connector.extract_cost_from_resource(
                        resource,
                        datetime.now().date().isoformat()
                    )
                    costs.append(cost)
                    
                    # Extract and push metrics
                    metrics = self.monitoring_connector.extract_metrics_from_resource(
                        resource
                    )
                    await self.monitoring_connector.push_metrics(
                        resource.get('id'),
                        metrics
                    )
                    
                    resource_count += 1
                    
                    if resource_count % 100 == 0:
                        await self.inventory_connector.update_job_task_progress(
                            task_id,
                            'IN_PROGRESS',
                            progress=min(resource_count // 10, 99)
                        )
                        
                        logger.info(f"Progress: {resource_count} resources processed")
                    
                except Exception as e:
                    logger.warning(f"Failed to process resource: {str(e)}")
                    continue
            
            # Push all cost data
            if costs:
                logger.info(f"Pushing {len(costs)} cost records...")
                await self.cost_connector.push_cost_data(
                    'data-source-nutanix',
                    costs
                )
            
            logger.info(f"Resource streaming completed: {resource_count} resources")
            return resource_count
            
        except Exception as e:
            logger.error(f"Failed to stream resources: {str(e)}")
            raise
    
    async def verify(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify plugin can connect to Nutanix.
        
        CloudForet calls this to test plugin configuration.
        
        Args:
            params: Verification parameters (contains secret_id)
            
        Returns:
            Verification result
        """
        try:
            logger.info("Starting plugin verification...")
            
            secret_id = params.get('secret_id')
            secret_data = await self.secret_manager.get_secret(secret_id)
            credentials = secret_data.get('data', {})
            
            # Create Nutanix connector
            nutanix = NutanixConnector(
                host=credentials.get('nutanix_host'),
                username=credentials.get('nutanix_username'),
                password=credentials.get('nutanix_password'),
                port=credentials.get('nutanix_port', 9440),
                verify_ssl=credentials.get('verify_ssl', True)
            )
            
            # Test connection
            if await nutanix.test_connection():
                await nutanix.close()
                
                logger.info("Plugin verification successful")
                
                return {
                    'result': 'SUCCESS',
                    'message': 'Connected to Nutanix successfully'
                }
            else:
                raise Exception("Failed to connect to Nutanix")
            
        except Exception as e:
            logger.error(f"Plugin verification failed: {str(e)}")
            return {
                'result': 'FAILURE',
                'message': str(e)
            }
