# CloudForet APIs - Practical Implementation Examples

Complete, production-ready code snippets for each CloudForet API usage.

---

## 1️⃣ IDENTITY API - Complete Authentication Flow

### Example 1.1: Plugin Initialization with Token Management

```python
# src/connector/identity_connector.py

import grpc
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from spaceone.core.error import ERROR_AUTHENTICATE_FAILURE
from spaceone.core.utils import parse_grpc_error

logger = logging.getLogger(__name__)

class IdentityConnector:
    """
    Handles authentication with CloudForet Identity service.
    Manages token lifecycle and credential rotation.
    """
    
    def __init__(self, identity_endpoint: str, plugin_api_key: str):
        self.identity_endpoint = identity_endpoint
        self.plugin_api_key = plugin_api_key
        self.plugin_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self._lock = asyncio.Lock()
    
    async def get_valid_token(self) -> str:
        """
        Get a valid token, refreshing if necessary.
        Thread-safe token management.
        """
        async with self._lock:
            # Check if token is still valid (with 5 min buffer)
            if self.plugin_token and self.token_expiry:
                time_until_expiry = self.token_expiry - datetime.utcnow()
                if time_until_expiry > timedelta(minutes=5):
                    return self.plugin_token
            
            # Token expired or doesn't exist, get new one
            self.plugin_token = await self._authenticate()
            return self.plugin_token
    
    async def _authenticate(self) -> str:
        """
        Call Identity API to get authentication token.
        
        gRPC Call: identity.v1.Auth.login
        """
        try:
            channel = grpc.aio.secure_channel(
                self.identity_endpoint,
                grpc.ssl_channel_credentials()
            )
            
            # Import generated gRPC stub
            from spaceone.identity.v1 import auth_pb2_grpc, auth_pb2
            
            stub = auth_pb2_grpc.AuthStub(channel)
            
            # Create login request
            request = auth_pb2.LoginRequest(
                domain_id=os.getenv('DOMAIN_ID', 'domain-default'),
                user_id='plugin-service-account',
                password=self.plugin_api_key
            )
            
            # Call Identity API
            response = await stub.login(request)
            
            self.token_expiry = datetime.fromisoformat(
                response.expires_at.rstrip('Z')
            )
            
            logger.info("Plugin authenticated successfully", extra={
                'expires_at': self.token_expiry.isoformat(),
                'identity_endpoint': self.identity_endpoint
            })
            
            return response.token
            
        except grpc.RpcError as e:
            error_details = parse_grpc_error(e)
            logger.error(f"Authentication failed: {error_details}")
            raise ERROR_AUTHENTICATE_FAILURE(
                reason=f"Identity service error: {error_details}"
            )
        finally:
            await channel.close()
    
    async def fetch_secret(self, secret_id: str) -> Dict[str, Any]:
        """
        Fetch and decrypt a secret from Identity service.
        
        gRPC Call: identity.v1.Secret.get
        """
        try:
            token = await self.get_valid_token()
            
            channel = grpc.aio.secure_channel(
                self.identity_endpoint,
                grpc.ssl_channel_credentials()
            )
            
            from spaceone.identity.v1 import secret_pb2_grpc, secret_pb2
            
            stub = secret_pb2_grpc.SecretStub(channel)
            
            request = secret_pb2.SecretRequest(
                secret_id=secret_id
            )
            
            # Add auth metadata
            metadata = [('authorization', f'Bearer {token}')]
            response = await stub.get(request, metadata=metadata)
            
            secret_data = json.loads(response.data)
            
            logger.info(f"Secret retrieved: {secret_id}")
            
            return secret_data
            
        except grpc.RpcError as e:
            error_details = parse_grpc_error(e)
            logger.error(f"Failed to fetch secret {secret_id}: {error_details}")
            raise
        finally:
            await channel.close()
    
    async def create_service_account(self, 
                                    account_name: str, 
                                    service_type: str) -> Dict[str, str]:
        """
        Create a new service account for a Nutanix cluster.
        
        gRPC Call: identity.v1.ServiceAccount.create
        """
        try:
            token = await self.get_valid_token()
            
            channel = grpc.aio.secure_channel(
                self.identity_endpoint,
                grpc.ssl_channel_credentials()
            )
            
            from spaceone.identity.v1 import service_account_pb2_grpc
            from spaceone.identity.v1 import service_account_pb2
            
            stub = service_account_pb2_grpc.ServiceAccountStub(channel)
            
            request = service_account_pb2.CreateServiceAccountRequest(
                name=account_name,
                service_type=service_type,  # 'nutanix-collector'
                workspace_id=os.getenv('WORKSPACE_ID'),
            )
            
            metadata = [('authorization', f'Bearer {token}')]
            response = await stub.create(request, metadata=metadata)
            
            logger.info(f"Service account created: {response.service_account_id}")
            
            return {
                'service_account_id': response.service_account_id,
                'api_key': response.api_key
            }
            
        except grpc.RpcError as e:
            error_details = parse_grpc_error(e)
            logger.error(f"Failed to create service account: {error_details}")
            raise
        finally:
            await channel.close()

```

---

## 2️⃣ INVENTORY API - Complete Job Management

### Example 2.1: Job Lifecycle Management

```python
# src/connector/inventory_connector.py

import grpc
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, AsyncGenerator
from spaceone.core.utils import parse_grpc_error

logger = logging.getLogger(__name__)

class InventoryConnector:
    """
    Manages interaction with CloudForet Inventory service.
    Handles Job, JobTask, and CloudService operations.
    """
    
    def __init__(self, inventory_endpoint: str, identity_connector):
        self.inventory_endpoint = inventory_endpoint
        self.identity_connector = identity_connector
    
    async def create_collection_job(self, 
                                    collector_id: str,
                                    service_account_ids: List[str],
                                    options: Dict[str, Any] = None) -> str:
        """
        Create a new collection job for one or more service accounts.
        
        gRPC Call: inventory.v1.Job.create
        
        Returns: job_id
        """
        try:
            token = await self.identity_connector.get_valid_token()
            
            channel = grpc.aio.secure_channel(
                self.inventory_endpoint,
                grpc.ssl_channel_credentials()
            )
            
            from spaceone.inventory.v1 import job_pb2_grpc, job_pb2
            
            stub = job_pb2_grpc.JobStub(channel)
            
            # Build request
            request = job_pb2.CreateJobRequest(
                collector_id=collector_id,
                service_account_ids=service_account_ids,
                options=json.dumps(options or {})
            )
            
            metadata = [('authorization', f'Bearer {token}')]
            response = await stub.create(request, metadata=metadata)
            
            job_id = response.job_id
            
            logger.info(f"Collection job created", extra={
                'job_id': job_id,
                'collector_id': collector_id,
                'service_account_count': len(service_account_ids)
            })
            
            return job_id
            
        except grpc.RpcError as e:
            error_details = parse_grpc_error(e)
            logger.error(f"Failed to create job: {error_details}")
            raise
        finally:
            await channel.close()
    
    async def create_job_tasks(self, 
                               job_id: str,
                               service_accounts: List[Dict[str, str]]) -> List[str]:
        """
        Create JobTask for each service account.
        Each task represents collection for one account.
        
        gRPC Call: inventory.v1.JobTask.create
        
        service_accounts format:
        [
            {'service_account_id': 'sa-123', 'secret_id': 'secret-456'},
            {'service_account_id': 'sa-789', 'secret_id': 'secret-012'}
        ]
        
        Returns: List of job_task_ids
        """
        job_task_ids = []
        
        try:
            token = await self.identity_connector.get_valid_token()
            
            channel = grpc.aio.secure_channel(
                self.inventory_endpoint,
                grpc.ssl_channel_credentials()
            )
            
            from spaceone.inventory.v1 import job_task_pb2_grpc, job_task_pb2
            
            stub = job_task_pb2_grpc.JobTaskStub(channel)
            metadata = [('authorization', f'Bearer {token}')]
            
            for account in service_accounts:
                request = job_task_pb2.CreateJobTaskRequest(
                    job_id=job_id,
                    service_account_id=account['service_account_id'],
                    secret_id=account['secret_id'],
                    status='CREATED'
                )
                
                response = await stub.create(request, metadata=metadata)
                job_task_ids.append(response.job_task_id)
                
                logger.info(f"Job task created", extra={
                    'job_task_id': response.job_task_id,
                    'service_account_id': account['service_account_id']
                })
            
            return job_task_ids
            
        except grpc.RpcError as e:
            error_details = parse_grpc_error(e)
            logger.error(f"Failed to create job tasks: {error_details}")
            raise
        finally:
            await channel.close()
    
    async def update_job_task_progress(self,
                                      job_task_id: str,
                                      status: str,
                                      progress: int = None) -> None:
        """
        Update job task progress during collection.
        
        Status values: CREATED, STARTED, IN_PROGRESS, FINISHED, ERROR, CANCELED
        
        gRPC Call: inventory.v1.JobTask.update
        """
        try:
            token = await self.identity_connector.get_valid_token()
            
            channel = grpc.aio.secure_channel(
                self.inventory_endpoint,
                grpc.ssl_channel_credentials()
            )
            
            from spaceone.inventory.v1 import job_task_pb2_grpc, job_task_pb2
            
            stub = job_task_pb2_grpc.JobTaskStub(channel)
            
            update_data = {
                'job_task_id': job_task_id,
                'status': status,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if progress is not None:
                update_data['progress'] = progress
            
            request = job_task_pb2.UpdateJobTaskRequest(
                **update_data
            )
            
            metadata = [('authorization', f'Bearer {token}')]
            await stub.update(request, metadata=metadata)
            
            logger.debug(f"Job task updated", extra={
                'job_task_id': job_task_id,
                'status': status,
                'progress': progress
            })
            
        except grpc.RpcError as e:
            error_details = parse_grpc_error(e)
            logger.error(f"Failed to update job task: {error_details}")
            # Don't raise - this is non-critical progress update
        finally:
            await channel.close()
    
    async def complete_job_task(self,
                               job_task_id: str,
                               stats: Dict[str, int],
                               errors: List[Dict[str, str]] = None) -> None:
        """
        Mark job task as completed with statistics.
        
        stats format:
        {
            'created_count': 42,
            'updated_count': 15,
            'deleted_count': 3,
            'error_count': 0,
            'disconnected_count': 0
        }
        
        gRPC Call: inventory.v1.JobTask.update
        """
        try:
            token = await self.identity_connector.get_valid_token()
            
            channel = grpc.aio.secure_channel(
                self.inventory_endpoint,
                grpc.ssl_channel_credentials()
            )
            
            from spaceone.inventory.v1 import job_task_pb2_grpc, job_task_pb2
            
            stub = job_task_pb2_grpc.JobTaskStub(channel)
            
            request = job_task_pb2.CompleteJobTaskRequest(
                job_task_id=job_task_id,
                status='FINISHED',
                created_count=stats.get('created_count', 0),
                updated_count=stats.get('updated_count', 0),
                deleted_count=stats.get('deleted_count', 0),
                error_count=stats.get('error_count', 0),
                disconnected_count=stats.get('disconnected_count', 0),
                finished_at=datetime.utcnow().isoformat()
            )
            
            metadata = [('authorization', f'Bearer {token}')]
            await stub.complete(request, metadata=metadata)
            
            logger.info(f"Job task completed", extra={
                'job_task_id': job_task_id,
                'stats': stats
            })
            
        except grpc.RpcError as e:
            error_details = parse_grpc_error(e)
            logger.error(f"Failed to complete job task: {error_details}")
            raise
        finally:
            await channel.close()
```

### Example 2.2: Streaming Resources to CloudForet

```python
# src/service/resource_pusher.py

import grpc
import logging
from typing import List, Dict, Any, AsyncGenerator
from datetime import datetime

logger = logging.getLogger(__name__)

class ResourcePusher:
    """
    Streams discovered resources to CloudForet Inventory service.
    Uses bidirectional streaming for efficiency.
    """
    
    def __init__(self, inventory_endpoint: str, identity_connector):
        self.inventory_endpoint = inventory_endpoint
        self.identity_connector = identity_connector
    
    async def stream_resources(self,
                              job_task_id: str,
                              resources: AsyncGenerator[Dict[str, Any], None]):
        """
        Stream resources to CloudForet using bidirectional streaming.
        
        gRPC Call: inventory.v1.CloudService.create (streaming)
        
        This is more efficient than individual creates for large resource counts.
        """
        try:
            token = await self.identity_connector.get_valid_token()
            
            channel = grpc.aio.secure_channel(
                self.inventory_endpoint,
                grpc.ssl_channel_credentials()
            )
            
            from spaceone.inventory.v1 import cloud_service_pb2_grpc
            from spaceone.inventory.v1 import cloud_service_pb2
            
            stub = cloud_service_pb2_grpc.CloudServiceStub(channel)
            metadata = [('authorization', f'Bearer {token}')]
            
            # Create request generator
            async def request_generator():
                batch_count = 0
                
                async for resource in resources:
                    # Normalize resource
                    normalized = self._normalize_resource(resource)
                    
                    request = cloud_service_pb2.CreateCloudServiceRequest(
                        job_task_id=job_task_id,
                        cloud_service_type=normalized['type'],
                        cloud_service_group='Nutanix',
                        cloud_service_name=normalized['name'],
                        provider='nutanix',
                        account=normalized['account'],
                        data=self._dict_to_struct(normalized['data']),
                        tags=self._dict_to_struct(normalized['tags']),
                        reference=self._dict_to_struct(normalized['reference'])
                    )
                    
                    yield request
                    batch_count += 1
                    
                    if batch_count % 100 == 0:
                        logger.info(f"Streamed {batch_count} resources")
            
            # Stream resources
            async for response in stub.create(
                request_generator(),
                metadata=metadata
            ):
                logger.debug(f"Resource created: {response.cloud_service_id}")
                
        except grpc.RpcError as e:
            error_details = parse_grpc_error(e)
            logger.error(f"Failed to stream resources: {error_details}")
            raise
        finally:
            await channel.close()
    
    def _normalize_resource(self, raw_resource: Dict) -> Dict[str, Any]:
        """Convert raw Nutanix API response to CloudForet format."""
        return {
            'type': 'compute.Instance',
            'id': raw_resource['metadata']['uuid'],
            'name': raw_resource['spec']['name'],
            'account': raw_resource.get('account_id', 'default'),
            'data': {
                'state': raw_resource['spec']['resources']['power_state'],
                'cpu_cores': (
                    raw_resource['spec']['resources']['num_sockets'] *
                    raw_resource['spec']['resources']['num_vcpus_per_socket']
                ),
                'memory_gb': (
                    raw_resource['spec']['resources']['memory_size_mib'] / 1024
                ),
                'cluster': raw_resource['spec']['cluster_reference']['name'],
                'created_at': raw_resource['metadata']['creation_time'],
            },
            'tags': {
                'environment': 'nutanix',
                'cluster': raw_resource['spec']['cluster_reference']['name'],
            },
            'reference': {
                'resource_id': raw_resource['metadata']['uuid'],
                'external_link': (
                    f"https://prism.local/console/#page/vm_details/"
                    f"{raw_resource['metadata']['uuid']}"
                )
            }
        }
    
    def _dict_to_struct(self, data: Dict) -> Any:
        """Convert Python dict to protobuf Struct."""
        from google.protobuf.json_format import ParseDict
        from google.protobuf.struct_pb2 import Struct
        
        return ParseDict(data, Struct())
```

---

## 3️⃣ REPOSITORY API - Plugin Management

### Example 3.1: Plugin Registration and Schema Management

```python
# src/connector/repository_connector.py

import grpc
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RepositoryConnector:
    """
    Manages plugin registration and schema publication to Repository service.
    """
    
    def __init__(self, repository_endpoint: str, identity_connector):
        self.repository_endpoint = repository_endpoint
        self.identity_connector = identity_connector
    
    async def register_plugin(self,
                             plugin_name: str,
                             image: str,
                             provider: str,
                             service_type: str) -> str:
        """
        Register plugin with Repository service.
        
        gRPC Call: repository.v1.Plugin.register
        
        Returns: plugin_id
        """
        try:
            token = await self.identity_connector.get_valid_token()
            
            channel = grpc.aio.secure_channel(
                self.repository_endpoint,
                grpc.ssl_channel_credentials()
            )
            
            from spaceone.repository.v1 import plugin_pb2_grpc, plugin_pb2
            
            stub = plugin_pb2_grpc.PluginStub(channel)
            
            request = plugin_pb2.RegisterPluginRequest(
                name=plugin_name,
                image=image,
                provider=provider,
                service_type=service_type,
                registry_type='DOCKER_HUB',
                capability={
                    'supported_resource_types': [
                        'compute.Instance',
                        'compute.Disk',
                        'compute.Network'
                    ],
                    'filter_format': [],
                    'supported_schedules': ['daily', 'hourly'],
                }
            )
            
            metadata = [('authorization', f'Bearer {token}')]
            response = await stub.register(request, metadata=metadata)
            
            logger.info(f"Plugin registered", extra={
                'plugin_id': response.plugin_id,
                'name': plugin_name
            })
            
            return response.plugin_id
            
        except grpc.RpcError as e:
            error_details = parse_grpc_error(e)
            logger.error(f"Failed to register plugin: {error_details}")
            raise
        finally:
            await channel.close()
    
    async def publish_schema(self,
                            plugin_id: str,
                            schema_type: str,
                            schema_definition: Dict[str, Any]) -> None:
        """
        Publish JSON schema for plugin secrets/options.
        
        Schema types: 'secret', 'options'
        
        gRPC Call: repository.v1.Schema.publish
        """
        try:
            token = await self.identity_connector.get_valid_token()
            
            channel = grpc.aio.secure_channel(
                self.repository_endpoint,
                grpc.ssl_channel_credentials()
            )
            
            from spaceone.repository.v1 import schema_pb2_grpc, schema_pb2
            
            stub = schema_pb2_grpc.SchemaStub(channel)
            
            request = schema_pb2.PublishSchemaRequest(
                plugin_id=plugin_id,
                schema_type=schema_type,
                schema=json.dumps(schema_definition)
            )
            
            metadata = [('authorization', f'Bearer {token}')]
            await stub.publish(request, metadata=metadata)
            
            logger.info(f"Schema published", extra={
                'plugin_id': plugin_id,
                'schema_type': schema_type
            })
            
        except grpc.RpcError as e:
            error_details = parse_grpc_error(e)
            logger.error(f"Failed to publish schema: {error_details}")
            raise
        finally:
            await channel.close()
    
    def get_secret_schema(self) -> Dict[str, Any]:
        """
        Define the secret schema for Nutanix credentials.
        This is published to Repository.
        """
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
                    'description': 'Verify SSL certificate when connecting to Prism Central'
                }
            },
            'required': [
                'nutanix_host',
                'nutanix_username',
                'nutanix_password'
            ],
            'additionalProperties': False
        }
```

---

## 4️⃣ COST ANALYSIS API - Cost Data Integration

### Example 4.1: Cost Data Collection

```python
# src/connector/cost_connector.py

import grpc
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class CostConnector:
    """
    Manages cost data collection and synchronization with Cost Analysis service.
    """
    
    def __init__(self, cost_endpoint: str, identity_connector):
        self.cost_endpoint = cost_endpoint
        self.identity_connector = identity_connector
    
    async def push_cost_data(self,
                            data_source_id: str,
                            costs: List[Dict[str, Any]]) -> int:
        """
        Push collected cost data to CloudForet.
        
        gRPC Call: cost_analysis.v1.Cost.create
        
        Returns: Number of cost records created
        """
        try:
            token = await self.identity_connector.get_valid_token()
            
            channel = grpc.aio.secure_channel(
                self.cost_endpoint,
                grpc.ssl_channel_credentials()
            )
            
            from spaceone.cost_analysis.v1 import cost_pb2_grpc, cost_pb2
            
            stub = cost_pb2_grpc.CostStub(channel)
            metadata = [('authorization', f'Bearer {token}')]
            
            created_count = 0
            
            for cost in costs:
                try:
                    request = cost_pb2.CreateCostRequest(
                        data_source_id=data_source_id,
                        date=cost['date'],
                        cost=cost['cost'],
                        currency=cost.get('currency', 'USD'),
                        resource_id=cost.get('resource_id'),
                        resource_type=cost.get('resource_type'),
                        region=cost.get('region'),
                        tags=self._dict_to_struct(cost.get('tags', {}))
                    )
                    
                    response = await stub.create(request, metadata=metadata)
                    created_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to create cost record: {str(e)}")
                    continue
            
            logger.info(f"Cost data pushed", extra={
                'data_source_id': data_source_id,
                'record_count': created_count
            })
            
            return created_count
            
        except grpc.RpcError as e:
            error_details = parse_grpc_error(e)
            logger.error(f"Failed to push cost data: {error_details}")
            raise
        finally:
            await channel.close()
    
    async def get_cost_statistics(self,
                                 data_source_id: str,
                                 start_date: str,
                                 end_date: str) -> Dict[str, Any]:
        """
        Query cost statistics from CloudForet.
        
        gRPC Call: cost_analysis.v1.Cost.stat
        
        start_date/end_date format: 'YYYY-MM-DD'
        """
        try:
            token = await self.identity_connector.get_valid_token()
            
            channel = grpc.aio.secure_channel(
                self.cost_endpoint,
                grpc.ssl_channel_credentials()
            )
            
            from spaceone.cost_analysis.v1 import cost_pb2_grpc, cost_pb2
            
            stub = cost_pb2_grpc.CostStub(channel)
            
            request = cost_pb2.StatCostRequest(
                query={
                    'aggregate': [
                        {
                            'group': {'keys': ['resource_type']},
                            'statistics': {
                                'total_cost': {'key': 'cost'}
                            }
                        }
                    ],
                    'filter': [
                        {'k': 'data_source_id', 'v': data_source_id, 'o': 'eq'},
                        {'k': 'date', 'v': [start_date, end_date], 'o': 'between'},
                    ]
                }
            )
            
            metadata = [('authorization', f'Bearer {token}')]
            response = await stub.stat(request, metadata=metadata)
            
            return json.loads(response.result)
            
        except grpc.RpcError as e:
            error_details = parse_grpc_error(e)
            logger.error(f"Failed to get cost statistics: {error_details}")
            raise
        finally:
            await channel.close()
    
    def _dict_to_struct(self, data: Dict) -> Any:
        from google.protobuf.json_format import ParseDict
        from google.protobuf.struct_pb2 import Struct
        
        return ParseDict(data, Struct())
```

---

## 5️⃣ MONITORING API - Metrics Integration

### Example 5.1: Metrics Collection and Reporting

```python
# src/connector/monitoring_connector.py

import grpc
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class MonitoringConnector:
    """
    Manages metric collection and reporting to Monitoring service.
    """
    
    def __init__(self, monitoring_endpoint: str, identity_connector):
        self.monitoring_endpoint = monitoring_endpoint
        self.identity_connector = identity_connector
    
    async def push_metrics(self,
                          resource_id: str,
                          metrics: Dict[str, float],
                          timestamp: Optional[str] = None) -> None:
        """
        Push metrics for a resource to CloudForet.
        
        gRPC Call: monitoring.v1.MetricData.create
        
        metrics format:
        {
            'cpu.utilization': 45.2,
            'memory.utilization': 62.5,
            'disk.read_iops': 150,
            'disk.write_iops': 85,
            'network.received_throughput': 1024000,
            'network.sent_throughput': 512000
        }
        """
        try:
            token = await self.identity_connector.get_valid_token()
            
            channel = grpc.aio.secure_channel(
                self.monitoring_endpoint,
                grpc.ssl_channel_credentials()
            )
            
            from spaceone.monitoring.v1 import metric_pb2_grpc, metric_pb2
            
            stub = metric_pb2_grpc.MetricStub(channel)
            metadata = [('authorization', f'Bearer {token}')]
            
            if timestamp is None:
                timestamp = datetime.utcnow().isoformat()
            
            for metric_name, value in metrics.items():
                request = metric_pb2.CreateMetricRequest(
                    resource_id=resource_id,
                    metric_name=metric_name,
                    value=value,
                    timestamp=timestamp
                )
                
                try:
                    await stub.create(request, metadata=metadata)
                except Exception as e:
                    logger.warning(f"Failed to push metric {metric_name}: {str(e)}")
                    continue
            
            logger.debug(f"Metrics pushed for {resource_id}", extra={
                'metric_count': len(metrics)
            })
            
        except grpc.RpcError as e:
            error_details = parse_grpc_error(e)
            logger.error(f"Failed to push metrics: {error_details}")
            raise
        finally:
            await channel.close()
    
    async def get_metric_data(self,
                             resource_id: str,
                             metric_names: List[str],
                             start_time: str,
                             end_time: str) -> Dict[str, List[Dict]]:
        """
        Query metric data for a resource.
        
        gRPC Call: monitoring.v1.MetricData.list
        
        Returns:
        {
            'cpu.utilization': [
                {'timestamp': '2024-01-15T10:00:00Z', 'value': 45.2},
                {'timestamp': '2024-01-15T11:00:00Z', 'value': 48.1},
            ]
        }
        """
        try:
            token = await self.identity_connector.get_valid_token()
            
            channel = grpc.aio.secure_channel(
                self.monitoring_endpoint,
                grpc.ssl_channel_credentials()
            )
            
            from spaceone.monitoring.v1 import metric_pb2_grpc, metric_pb2
            
            stub = metric_pb2_grpc.MetricStub(channel)
            
            request = metric_pb2.ListMetricDataRequest(
                query={
                    'filter': [
                        {'k': 'resource_id', 'v': resource_id, 'o': 'eq'},
                        {'k': 'metric_name', 'v': metric_names, 'o': 'in'},
                        {'k': 'timestamp', 'v': [start_time, end_time], 'o': 'between'},
                    ],
                    'sort': {'key': 'timestamp', 'desc': False}
                }
            )
            
            metadata = [('authorization', f'Bearer {token}')]
            response = await stub.list(request, metadata=metadata)
            
            # Organize by metric name
            metrics_by_name = {}
            for metric in response.results:
                metric_name = metric.metric_name
                if metric_name not in metrics_by_name:
                    metrics_by_name[metric_name] = []
                
                metrics_by_name[metric_name].append({
                    'timestamp': metric.timestamp,
                    'value': metric.value
                })
            
            return metrics_by_name
            
        except grpc.RpcError as e:
            error_details = parse_grpc_error(e)
            logger.error(f"Failed to get metric data: {error_details}")
            raise
        finally:
            await channel.close()
```

---

## 6️⃣ NOTIFICATION API - Alert Management

### Example 6.1: Notification Delivery

```python
# src/connector/notification_connector.py

import grpc
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class NotificationConnector:
    """
    Manages notifications and alerts to be sent to users.
    """
    
    def __init__(self, notification_endpoint: str, identity_connector):
        self.notification_endpoint = notification_endpoint
        self.identity_connector = identity_connector
    
    async def send_notification(self,
                               title: str,
                               message: str,
                               severity: str = 'INFO',
                               notification_type: str = 'USER',
                               tags: Dict[str, str] = None) -> str:
        """
        Send a notification to users.
        
        gRPC Call: notification.v1.Notification.create
        
        severity: INFO, WARNING, ERROR, CRITICAL
        notification_type: USER, SYSTEM
        
        Returns: notification_id
        """
        try:
            token = await self.identity_connector.get_valid_token()
            
            channel = grpc.aio.secure_channel(
                self.notification_endpoint,
                grpc.ssl_channel_credentials()
            )
            
            from spaceone.notification.v1 import notification_pb2_grpc
            from spaceone.notification.v1 import notification_pb2
            
            stub = notification_pb2_grpc.NotificationStub(channel)
            
            request = notification_pb2.CreateNotificationRequest(
                title=title,
                message=message,
                severity=severity,
                notification_type=notification_type,
                tags=self._dict_to_struct(tags or {}),
                is_read=False,
                created_at=datetime.utcnow().isoformat()
            )
            
            metadata = [('authorization', f'Bearer {token}')]
            response = await stub.create(request, metadata=metadata)
            
            logger.info(f"Notification sent", extra={
                'notification_id': response.notification_id,
                'severity': severity
            })
            
            return response.notification_id
            
        except grpc.RpcError as e:
            error_details = parse_grpc_error(e)
            logger.error(f"Failed to send notification: {error_details}")
            raise
        finally:
            await channel.close()
    
    async def send_collection_complete_notification(self,
                                                    collector_name: str,
                                                    resource_count: int,
                                                    error_count: int) -> str:
        """Send collection completion notification."""
        message = f"""
        Collection completed for {collector_name}
        
        Resources:
        - Collected: {resource_count}
        - Errors: {error_count}
        
        Timestamp: {datetime.utcnow().isoformat()}
        """
        
        return await self.send_notification(
            title=f'Collection Complete: {collector_name}',
            message=message,
            severity='INFO' if error_count == 0 else 'WARNING',
            notification_type='USER',
            tags={
                'collector': collector_name,
                'resource_count': str(resource_count),
                'error_count': str(error_count)
            }
        )
    
    async def send_collection_error_notification(self,
                                                 collector_name: str,
                                                 error_message: str) -> str:
        """Send collection failure notification."""
        return await self.send_notification(
            title=f'Collection Failed: {collector_name}',
            message=error_message,
            severity='CRITICAL',
            notification_type='SYSTEM',
            tags={'collector': collector_name}
        )
    
    def _dict_to_struct(self, data: Dict) -> Any:
        from google.protobuf.json_format import ParseDict
        from google.protobuf.struct_pb2 import Struct
        
        return ParseDict(data, Struct())
```

---

## 🧩 Complete Plugin Main Loop

```python
# src/server.py - Orchestrates all APIs

import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NutanixCollectorPlugin:
    """
    Main plugin class that orchestrates all API interactions.
    """
    
    def __init__(self):
        # Initialize connectors
        self.identity_connector = IdentityConnector(
            os.getenv('IDENTITY_ENDPOINT'),
            os.getenv('PLUGIN_API_KEY')
        )
        self.inventory_connector = InventoryConnector(
            os.getenv('INVENTORY_ENDPOINT'),
            self.identity_connector
        )
        self.resource_pusher = ResourcePusher(
            os.getenv('INVENTORY_ENDPOINT'),
            self.identity_connector
        )
        self.repository_connector = RepositoryConnector(
            os.getenv('REPOSITORY_ENDPOINT'),
            self.identity_connector
        )
        self.cost_connector = CostConnector(
            os.getenv('COST_ENDPOINT'),
            self.identity_connector
        )
        self.monitoring_connector = MonitoringConnector(
            os.getenv('MONITORING_ENDPOINT'),
            self.identity_connector
        )
        self.notification_connector = NotificationConnector(
            os.getenv('NOTIFICATION_ENDPOINT'),
            self.identity_connector
        )
    
    async def collect(self, job_params):
        """
        Main collection workflow orchestrating all APIs.
        """
        job_id = job_params['job_id']
        collector_id = job_params['collector_id']
        service_account_ids = job_params['service_account_ids']
        
        total_resources = 0
        total_errors = 0
        
        try:
            # Step 1: Create job tasks
            logger.info("Creating job tasks...")
            job_tasks = await self.inventory_connector.create_job_tasks(
                job_id,
                service_account_ids
            )
            
            # Step 2: Process each account
            for idx, task_id in enumerate(job_tasks):
                account_id = service_account_ids[idx]['service_account_id']
                
                try:
                    await self.inventory_connector.update_job_task_progress(
                        task_id, 'STARTED'
                    )
                    
                    # Get credentials
                    secret_id = service_account_ids[idx]['secret_id']
                    credentials = await self.identity_connector.fetch_secret(
                        secret_id
                    )
                    
                    # Collect from Nutanix
                    logger.info(f"Collecting from account {account_id}...")
                    resources = await self._collect_from_nutanix(credentials)
                    
                    # Stream to CloudForet
                    logger.info(f"Pushing {len(resources)} resources...")
                    await self.resource_pusher.stream_resources(task_id, resources)
                    
                    # Push cost data
                    logger.info("Pushing cost data...")
                    cost_count = await self.cost_connector.push_cost_data(
                        collector_id,
                        self._extract_costs(resources)
                    )
                    
                    # Push metrics
                    logger.info("Pushing metrics...")
                    await self._push_metrics(resources)
                    
                    # Complete task
                    stats = {
                        'created_count': len(resources),
                        'updated_count': 0,
                        'deleted_count': 0,
                        'error_count': 0
                    }
                    
                    await self.inventory_connector.complete_job_task(
                        task_id, stats
                    )
                    
                    total_resources += len(resources)
                    
                except Exception as e:
                    logger.error(f"Error processing account {account_id}: {str(e)}")
                    total_errors += 1
                    
                    await self.inventory_connector.update_job_task_progress(
                        task_id, 'ERROR'
                    )
            
            # Step 3: Send completion notification
            await self.notification_connector.send_collection_complete_notification(
                collector_id,
                total_resources,
                total_errors
            )
            
            logger.info(f"Collection completed", extra={
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
    
    async def _collect_from_nutanix(self, credentials):
        """Collect resources from Nutanix."""
        # Implementation
        pass
    
    async def _push_metrics(self, resources):
        """Push metrics for collected resources."""
        for resource in resources:
            await self.monitoring_connector.push_metrics(
                resource['id'],
                {
                    'cpu.utilization': resource['cpu_utilization'],
                    'memory.utilization': resource['memory_utilization'],
                }
            )
    
    def _extract_costs(self, resources):
        """Extract cost data from resources."""
        # Implementation
        pass

# Start plugin
if __name__ == '__main__':
    plugin = NutanixCollectorPlugin()
    asyncio.run(plugin.collect(job_params))
```

---

## 📊 API Call Summary Table

| API Service | Method | Purpose | Frequency |
|---|---|---|---|
| **Identity** | Auth.login | Authenticate plugin | Startup + Token refresh |
| **Identity** | Secret.get | Get credentials | Per collection |
| **Inventory** | Job.create | Create collection job | Per collection |
| **Inventory** | JobTask.create | Create per-account task | Per account |
| **Inventory** | JobTask.update | Update progress | During collection |
| **Inventory** | CloudService.create | Save resources | Per resource |
| **Repository** | Plugin.register | Register plugin | Startup |
| **Repository** | Schema.publish | Publish schemas | Startup |
| **Cost** | Cost.create | Save cost data | Per resource |
| **Monitoring** | MetricData.create | Save metrics | Per metric |
| **Notification** | Notification.create | Send alerts | On completion/error |

