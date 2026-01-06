"""
Inventory API Connector

Handles interaction with CloudForet Inventory service for job management,
resource creation, and resource queries.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, AsyncGenerator, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class JobInfo:
    """Job information."""
    job_id: str
    collector_id: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class JobTaskInfo:
    """Job Task information."""
    job_task_id: str
    job_id: str
    service_account_id: str
    status: str
    created_count: int = 0
    updated_count: int = 0
    deleted_count: int = 0
    error_count: int = 0
    created_at: str = ''
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class InventoryConnector:
    """Manages interaction with CloudForet Inventory service."""
    
    def __init__(self, inventory_endpoint: str, identity_connector):
        self.inventory_endpoint = inventory_endpoint
        self.identity_connector = identity_connector
        self._jobs: Dict[str, JobInfo] = {}
        self._tasks: Dict[str, JobTaskInfo] = {}
    
    async def create_collection_job(self,
                                    collector_id: str,
                                    service_account_ids: List[str],
                                    options: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new collection job.
        
        gRPC Call: inventory.v1.Job.create
        
        Args:
            collector_id: Collector identifier
            service_account_ids: List of service account IDs to collect from
            options: Additional collection options
            
        Returns:
            job_id
        """
        try:
            job_id = f"job-{len(self._jobs) + 1:08d}"
            
            job_info = JobInfo(
                job_id=job_id,
                collector_id=collector_id,
                status='CREATED',
                created_at=datetime.utcnow().isoformat()
            )
            
            self._jobs[job_id] = job_info
            
            logger.info(f"Collection job created", extra={
                'job_id': job_id,
                'collector_id': collector_id,
                'service_account_count': len(service_account_ids)
            })
            
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to create job: {str(e)}")
            raise
    
    async def create_job_tasks(self,
                               job_id: str,
                               service_accounts: List[Dict[str, str]]) -> List[str]:
        """
        Create JobTask for each service account.
        
        gRPC Call: inventory.v1.JobTask.create
        
        Args:
            job_id: Parent job ID
            service_accounts: List of {service_account_id, secret_id}
            
        Returns:
            List of job_task_ids
        """
        job_task_ids = []
        
        try:
            for idx, account in enumerate(service_accounts):
                task_id = f"task-{idx+1:08d}"
                
                task_info = JobTaskInfo(
                    job_task_id=task_id,
                    job_id=job_id,
                    service_account_id=account['service_account_id'],
                    status='CREATED',
                    created_at=datetime.utcnow().isoformat()
                )
                
                self._tasks[task_id] = task_info
                job_task_ids.append(task_id)
                
                logger.info(f"Job task created", extra={
                    'job_task_id': task_id,
                    'service_account_id': account['service_account_id']
                })
            
            return job_task_ids
            
        except Exception as e:
            logger.error(f"Failed to create job tasks: {str(e)}")
            raise
    
    async def update_job_task_progress(self,
                                      job_task_id: str,
                                      status: str,
                                      progress: Optional[int] = None) -> None:
        """
        Update job task progress.
        
        gRPC Call: inventory.v1.JobTask.update
        
        Args:
            job_task_id: Task ID
            status: Task status (CREATED, STARTED, IN_PROGRESS, FINISHED, ERROR)
            progress: Completion percentage (0-100)
        """
        try:
            if job_task_id in self._tasks:
                task = self._tasks[job_task_id]
                task.status = status
                
                if status == 'STARTED':
                    task.started_at = datetime.utcnow().isoformat()
                
                logger.debug(f"Job task updated", extra={
                    'job_task_id': job_task_id,
                    'status': status,
                    'progress': progress
                })
            
        except Exception as e:
            logger.error(f"Failed to update job task: {str(e)}")
    
    async def complete_job_task(self,
                               job_task_id: str,
                               stats: Dict[str, int]) -> None:
        """
        Mark job task as completed with statistics.
        
        gRPC Call: inventory.v1.JobTask.update
        
        Args:
            job_task_id: Task ID
            stats: Statistics dict with created_count, updated_count, etc.
        """
        try:
            if job_task_id in self._tasks:
                task = self._tasks[job_task_id]
                task.status = 'FINISHED'
                task.finished_at = datetime.utcnow().isoformat()
                task.created_count = stats.get('created_count', 0)
                task.updated_count = stats.get('updated_count', 0)
                task.deleted_count = stats.get('deleted_count', 0)
                task.error_count = stats.get('error_count', 0)
                
                logger.info(f"Job task completed", extra={
                    'job_task_id': job_task_id,
                    'stats': stats
                })
            
        except Exception as e:
            logger.error(f"Failed to complete job task: {str(e)}")
            raise
    
    async def create_cloud_service(self,
                                  job_task_id: str,
                                  resource: Dict[str, Any]) -> str:
        """
        Create a cloud service resource.
        
        gRPC Call: inventory.v1.CloudService.create
        
        Args:
            job_task_id: Associated job task
            resource: Resource data
            
        Returns:
            cloud_service_id
        """
        try:
            cs_id = f"cs-{hash(resource.get('id', '')) % 10000000:08d}"
            
            logger.debug(f"Cloud service created", extra={
                'cloud_service_id': cs_id,
                'name': resource.get('name'),
                'type': resource.get('type')
            })
            
            return cs_id
            
        except Exception as e:
            logger.error(f"Failed to create cloud service: {str(e)}")
            raise
    
    async def stream_resources(self,
                              job_task_id: str,
                              resources: AsyncGenerator[Dict[str, Any], None]) -> int:
        """
        Stream resources to inventory (batch create).
        
        gRPC Call: inventory.v1.CloudService.create (streaming)
        
        Args:
            job_task_id: Associated job task
            resources: Async generator of resource dicts
            
        Returns:
            Number of resources created
        """
        created_count = 0
        
        try:
            async for resource in resources:
                try:
                    await self.create_cloud_service(job_task_id, resource)
                    created_count += 1
                    
                    if created_count % 100 == 0:
                        logger.info(f"Streamed {created_count} resources for task {job_task_id}")
                
                except Exception as e:
                    logger.warning(f"Failed to create resource: {str(e)}")
                    continue
            
            logger.info(f"Streaming completed", extra={
                'job_task_id': job_task_id,
                'total_resources': created_count
            })
            
            return created_count
            
        except Exception as e:
            logger.error(f"Failed to stream resources: {str(e)}")
            raise
    
    async def query_resources(self,
                             provider: str = 'nutanix',
                             resource_type: Optional[str] = None,
                             filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Query cloud service resources.
        
        gRPC Call: inventory.v1.CloudService.list
        
        Args:
            provider: Provider name
            resource_type: Resource type filter
            filters: Additional filters
            
        Returns:
            List of resources
        """
        try:
            logger.debug(f"Querying resources", extra={
                'provider': provider,
                'resource_type': resource_type,
                'filters': filters
            })
            
            # Mock query result
            return []
            
        except Exception as e:
            logger.error(f"Failed to query resources: {str(e)}")
            raise
    
    async def get_resource_stats(self,
                                provider: str = 'nutanix') -> Dict[str, Any]:
        """
        Get resource statistics.
        
        gRPC Call: inventory.v1.CloudService.stat
        
        Args:
            provider: Provider name
            
        Returns:
            Statistics dictionary
        """
        try:
            logger.debug(f"Getting resource stats for provider: {provider}")
            
            # Mock stats
            return {
                'compute.Instance': 0,
                'compute.Disk': 0,
                'compute.Network': 0,
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            raise
