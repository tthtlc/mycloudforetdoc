# CloudForet APIs Integration Guide for Nutanix Plugin Development

This guide demonstrates how to use CloudForet's core APIs to develop and integrate a Nutanix inventory collector plugin. Each section shows a real feature and the corresponding API calls needed.

---

## 📚 Overview of Key CloudForet APIs

```
┌─────────────────────────────────────────────────────────────────┐
│ CORE SERVICE APIS (gRPC-based)                                  │
├─────────────────────────────────────────────────────────────────┤
│ 1. Identity API        → Auth, ServiceAccounts, Tokens          │
│ 2. Inventory API       → Collectors, Jobs, JobTasks, Resources  │
│ 3. Repository API      → Plugin metadata, schemas               │
│ 4. Cost Analysis API   → Cost data collection & reporting       │
│ 5. Monitoring API      → Metrics, DataSources, Webhooks         │
│ 6. Notification API    → Event notifications, channels          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔐 1. Identity API - Authentication & Authorization

**Purpose**: Authenticate the plugin, manage secrets, and validate permissions.

### 1.1 Initialize Plugin Authentication (Core Feature)

```python
# src/server.py - Plugin initialization with Identity service
from spaceone.core.auth.authenticator import Authenticator
from spaceone.core.transaction import Transaction
from spaceone.identity.v1 import Plugin as IdentityPlugin
from spaceone.core.error import ERROR_INVALID_API_KEY

class PluginInitializer:
    def __init__(self):
        self.identity_endpoint = os.getenv('IDENTITY_ENDPOINT', 'grpc://identity:50051')
        self.plugin_api_key = os.getenv('PLUGIN_API_KEY')
    
    async def authenticate_plugin(self):
        """
        Call Identity API to validate plugin credentials and get token.
        This happens once at plugin startup.
        
        API: identity.v1.Auth.login
        """
        try:
            auth_client = await self._get_identity_client()
            
            # Request: Get service account token
            response = await auth_client.login(
                domain_id=os.getenv('DOMAIN_ID'),
                user_id='plugin-service-account',
                password=self.plugin_api_key
            )
            
            # Response: Token to use for subsequent API calls
            self.plugin_token = response.token
            self.plugin_token_expiry = response.expires_at
            
            logger.info(f"Plugin authenticated successfully", extra={
                'plugin_id': 'plugin-nutanix-inven-collector',
                'expires_at': self.plugin_token_expiry
            })
            
            return self.plugin_token
            
        except Exception as e:
            logger.error(f"Failed to authenticate plugin: {str(e)}")
            raise ERROR_INVALID_API_KEY(reason=str(e))
    
    async def _get_identity_client(self):
        """Create gRPC stub for Identity service."""
        channel = grpc.aio.secure_channel(
            self.identity_endpoint,
            grpc.ssl_channel_credentials()
        )
        return IdentityPlugin.Stub(channel)
```

### 1.2 Fetch Secret Credentials (Job Execution)

```python
# src/service/collector_service.py
from spaceone.core.service import *
from spaceone.identity.v1 import Secret

class NutanixCollectorService(BaseService):
    def collect(self, params):
        """
        When a collection job runs, fetch the actual credentials from Identity service.
        
        API: identity.v1.Secret.get
        """
        secret_id = params.get('secret_id')
        transaction = self.transaction
        
        try:
            # Use Identity API to get decrypted secret
            secret_response = transaction.execute(
                'secret.Secret.get',
                {
                    'secret_id': secret_id,
                }
            )
            
            # Response contains decrypted secret data
            secret_data = secret_response.get('data')
            
            nutanix_config = {
                'host': secret_data.get('nutanix_host'),
                'username': secret_data.get('nutanix_username'),
                'password': secret_data.get('nutanix_password'),
                'port': secret_data.get('nutanix_port', 9440),
                'verify_ssl': secret_data.get('verify_ssl', True)
            }
            
            logger.info("Retrieved credentials from Identity service", extra={
                'secret_id': secret_id
            })
            
            return nutanix_config
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret: {str(e)}")
            raise ERROR_INVALID_PARAMETER(key='secret_id', reason=str(e))
```

**Request Format**:
```json
{
  "secret_id": "secret-abc123def456"
}
```

**Response Format**:
```json
{
  "data": {
    "nutanix_host": "prism.nutanix.local",
    "nutanix_username": "admin",
    "nutanix_password": "encrypted_password",
    "nutanix_port": 9440,
    "verify_ssl": true
  },
  "tags": {"environment": "production"}
}
```

---

## 📦 2. Inventory API - Collection Management

**Purpose**: Register collectors, manage jobs, report collection results.

### 2.1 Register Collector Plugin

```python
# src/service/plugin_init_service.py
from spaceone.core.service import *
from spaceone.inventory.v1 import Collector

class PluginInitService(BaseService):
    def init(self, params):
        """
        Plugin initialization - called when plugin starts up.
        Returns metadata that CloudForet uses to register the collector.
        
        API: inventory.v1.Collector.register (called by CloudForet)
        """
        return {
            'metadata': {
                'provider': 'nutanix',
                'service_type': 'compute',
                'icon': 'https://myregistry.io/plugin-icons/nutanix.png',
                'display_name': 'Nutanix Inventory Collector',
                'capability': {
                    'supported_resource_types': [
                        'compute.Instance',
                        'compute.Disk',
                        'compute.Network'
                    ],
                    'filter_format': [],
                    'supported_schedules': ['daily', 'hourly', 'manual'],
                    'supported_environments': ['on-premises'],
                }
            }
        }
```

**CloudForet calls this on plugin startup:**
```python
# Inside CloudForet's Collector service
response = collector_plugin.init(params={})

# Then registers the collector
collector_info = await inventory_service.Collector.register(
    name='Nutanix Inventory Collector',
    plugin_id=response['plugin_id'],
    provider='nutanix',
    capability=response['metadata']['capability']
)
```

### 2.2 Create and Manage Collection Jobs

```python
# src/service/job_handler.py
from spaceone.inventory.v1 import Job, JobTask

class JobHandler:
    def __init__(self, transaction):
        self.transaction = transaction
    
    def create_collection_job(self, collector_id, service_account_ids):
        """
        Create a new collection job.
        
        API: inventory.v1.Job.create
        """
        try:
            # CloudForet creates a Job when user clicks "Collect Now"
            job_response = self.transaction.execute(
                'inventory.Job.create',
                {
                    'collector_id': collector_id,
                    'service_accounts': service_account_ids,
                    'options': {
                        'include_resources': ['compute.Instance', 'compute.Disk'],
                        'timeout': 3600  # 1 hour timeout
                    }
                }
            )
            
            job_id = job_response['job_id']
            logger.info(f"Collection job created", extra={
                'job_id': job_id,
                'collector_id': collector_id,
                'service_account_count': len(service_account_ids)
            })
            
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to create job: {str(e)}")
            raise ERROR_INVALID_PARAMETER(reason=str(e))
    
    def update_job_status(self, job_id, status, progress=None):
        """
        Update job status during collection.
        
        API: inventory.v1.Job.update
        """
        self.transaction.execute(
            'inventory.Job.update',
            {
                'job_id': job_id,
                'status': status,  # CREATED, STARTED, FINISHED, ERROR
                'progress': progress,  # 0-100
                'updated_at': datetime.utcnow().isoformat()
            }
        )
    
    def complete_job(self, job_id, total_collected, error_count=0):
        """
        Mark job as completed.
        
        API: inventory.v1.Job.update
        """
        self.transaction.execute(
            'inventory.Job.update',
            {
                'job_id': job_id,
                'status': 'FINISHED',
                'total_count': total_collected,
                'error_count': error_count,
                'finished_at': datetime.utcnow().isoformat()
            }
        )
```

### 2.3 Create and Manage Job Tasks

```python
# src/service/job_task_handler.py
from spaceone.inventory.v1 import JobTask

class JobTaskHandler:
    def __init__(self, transaction):
        self.transaction = transaction
    
    def create_job_task(self, job_id, service_account_id, secret_id):
        """
        Create a JobTask for each service account.
        A Job can have multiple JobTasks (one per account).
        
        API: inventory.v1.JobTask.create
        """
        task_response = self.transaction.execute(
            'inventory.JobTask.create',
            {
                'job_id': job_id,
                'service_account_id': service_account_id,
                'secret_id': secret_id,
                'status': 'CREATED'
            }
        )
        
        return task_response['job_task_id']
    
    def report_task_results(self, job_task_id, resources, stats):
        """
        Report collection results for a specific task.
        
        API: inventory.v1.JobTask.update
        """
        self.transaction.execute(
            'inventory.JobTask.update',
            {
                'job_task_id': job_task_id,
                'status': 'FINISHED',
                'created_count': stats['created'],
                'updated_count': stats['updated'],
                'deleted_count': stats['deleted'],
                'failure_count': stats['failures'],
                'resource_summary': {
                    'compute.Instance': len([r for r in resources if r['type'] == 'compute.Instance']),
                    'compute.Disk': len([r for r in resources if r['type'] == 'compute.Disk']),
                }
            }
        )
    
    def report_task_error(self, job_task_id, error_message, error_code):
        """
        Report error for a failed task.
        
        API: inventory.v1.JobTask.update
        """
        self.transaction.execute(
            'inventory.JobTask.update',
            {
                'job_task_id': job_task_id,
                'status': 'ERROR',
                'error_code': error_code,
                'error_message': error_message
            }
        )
```

---

## 📝 3. Cloud Service & Resource Management API

**Purpose**: Save collected resources to CloudForet inventory.

### 3.1 Create/Update Cloud Service Resources

```python
# src/service/resource_handler.py
from spaceone.inventory.v1 import CloudService

class ResourceHandler:
    def __init__(self, transaction):
        self.transaction = transaction
    
    def save_resources(self, job_id, service_account_id, resources):
        """
        Save discovered Nutanix resources to CloudForet inventory.
        
        API: inventory.v1.CloudService.create
        """
        created_resources = []
        
        for resource in resources:
            try:
                # Create or update resource
                saved_resource = self.transaction.execute(
                    'inventory.CloudService.create',
                    {
                        'cloud_service_type': resource['type'],
                        'cloud_service_group': 'Nutanix',
                        'cloud_service_name': resource['name'],
                        'provider': 'nutanix',
                        'account': service_account_id,
                        'data': resource['data'],
                        'tags': resource.get('tags', {}),
                        'reference': {
                            'resource_id': resource['id'],
                            'external_link': resource.get('external_link'),
                        },
                        'project_id': resource.get('project_id'),
                    }
                )
                
                created_resources.append(saved_resource)
                
            except Exception as e:
                logger.error(f"Failed to save resource {resource['id']}: {str(e)}")
        
        return created_resources
    
    def normalize_vm_resource(self, vm_data, service_account_id):
        """
        Convert raw Nutanix API response to CloudForet resource format.
        
        This matches the schema defined in init()
        """
        return {
            'type': 'compute.Instance',
            'id': vm_data['metadata']['uuid'],
            'name': vm_data['spec']['name'],
            'data': {
                'state': vm_data['spec']['resources']['power_state'],
                'cpu': vm_data['spec']['resources']['num_sockets'] * 
                       vm_data['spec']['resources']['num_vcpus_per_socket'],
                'memory_gb': vm_data['spec']['resources']['memory_size_mib'] / 1024,
                'disk_total_gb': sum([
                    disk['disk_size_bytes'] / (1024**3) 
                    for disk in vm_data['spec']['resources'].get('disk_list', [])
                ]),
                'cluster': vm_data['spec']['cluster_reference']['name'],
                'created_at': vm_data['metadata']['creation_time'],
                'updated_at': vm_data['metadata']['update_time'],
                'nutanix_uuid': vm_data['metadata']['uuid'],
            },
            'tags': {
                'environment': 'nutanix',
                'cluster': vm_data['spec']['cluster_reference']['name'],
            },
            'external_link': f"https://prism.nutanix.local/console/#page/vm_details/{vm_data['metadata']['uuid']}"
        }
```

**Request Format**:
```json
{
  "cloud_service_type": "compute.Instance",
  "cloud_service_group": "Nutanix",
  "cloud_service_name": "prod-web-01",
  "provider": "nutanix",
  "account": "service-account-123",
  "data": {
    "state": "ON",
    "cpu": 8,
    "memory_gb": 32,
    "cluster": "cluster-01"
  },
  "tags": {"environment": "production"},
  "reference": {
    "resource_id": "vm-uuid-12345",
    "external_link": "https://prism.nutanix.local/vm"
  }
}
```

### 3.2 Query Collected Resources

```python
# src/service/inventory_query_service.py
from spaceone.inventory.v1 import CloudService

class InventoryQueryService:
    def __init__(self, transaction):
        self.transaction = transaction
    
    def list_resources(self, resource_type='compute.Instance', provider='nutanix', **filters):
        """
        Query collected resources from CloudForet inventory.
        
        API: inventory.v1.CloudService.list
        """
        query = {
            'filter': [
                {'k': 'cloud_service_type', 'v': resource_type, 'o': 'eq'},
                {'k': 'provider', 'v': provider, 'o': 'eq'},
            ],
            'only': ['cloud_service_id', 'name', 'state', 'account'],
            'sort': {'key': 'name', 'desc': False}
        }
        
        # Add additional filters
        for key, value in filters.items():
            query['filter'].append({
                'k': key,
                'v': value,
                'o': 'eq'
            })
        
        response = self.transaction.execute(
            'inventory.CloudService.list',
            query
        )
        
        return response['results']
    
    def get_resource_stats(self, provider='nutanix'):
        """
        Get statistics on collected resources.
        
        API: inventory.v1.CloudService.stat
        """
        stat_query = {
            'query': {
                'aggregate': [
                    {
                        'group': {
                            'keys': ['cloud_service_type']
                        },
                        'statistics': {
                            'count': {'key': 'cloud_service_id'}
                        }
                    }
                ],
                'filter': [
                    {'k': 'provider', 'v': provider, 'o': 'eq'}
                ]
            }
        }
        
        response = self.transaction.execute(
            'inventory.CloudService.stat',
            stat_query
        )
        
        return response
```

---

## 📊 4. Repository API - Plugin Management

**Purpose**: Store and retrieve plugin metadata, schemas, and versions.

### 4.1 Register Plugin Metadata

```python
# src/service/repository_service.py
from spaceone.repository.v1 import Plugin

class RepositoryService:
    def __init__(self, transaction):
        self.transaction = transaction
    
    def register_plugin(self, plugin_info):
        """
        Register plugin metadata with Repository service.
        CloudForet uses this to list available plugins.
        
        API: repository.v1.Plugin.register
        """
        response = self.transaction.execute(
            'repository.Plugin.register',
            {
                'name': 'plugin-nutanix-inven-collector',
                'image': 'myregistry.io/cloudforet/plugin-nutanix-inven-collector:1.0.0',
                'service_type': 'inventory.Collector',
                'registry_type': 'DOCKER_HUB',
                'provider': 'nutanix',
                'capability': {
                    'supported_resource_types': [
                        'compute.Instance',
                        'compute.Disk',
                        'compute.Network'
                    ],
                    'supported_schedules': ['daily', 'hourly'],
                }
            }
        )
        
        logger.info("Plugin registered with Repository", extra={
            'plugin_id': response['plugin_id']
        })
        
        return response
    
    def get_plugin_schema(self, plugin_id):
        """
        Retrieve JSON schema for plugin secrets.
        
        API: repository.v1.Schema.get
        """
        schema_response = self.transaction.execute(
            'repository.Schema.get',
            {
                'plugin_id': plugin_id,
                'name': 'secret'
            }
        )
        
        return schema_response['schema']
    
    def publish_plugin_version(self, plugin_id, version, changelog):
        """
        Publish a new version of plugin.
        
        API: repository.v1.Plugin.update
        """
        response = self.transaction.execute(
            'repository.Plugin.update',
            {
                'plugin_id': plugin_id,
                'version': version,
                'changelog': changelog,
                'tags': ['v1.0.0', 'latest']
            }
        )
        
        return response
```

### 4.2 Fetch Plugin Configuration

```python
# src/service/plugin_config_service.py

class PluginConfigService:
    def __init__(self, transaction):
        self.transaction = transaction
    
    def get_collector_rule(self, collector_id):
        """
        Get collector rule which defines how plugin should behave.
        
        API: inventory.v1.CollectorRule.get
        """
        rule_response = self.transaction.execute(
            'inventory.CollectorRule.get',
            {'collector_id': collector_id}
        )
        
        return {
            'collect_scope': rule_response.get('collect_scope'),
            'filters': rule_response.get('filters'),
            'conditions': rule_response.get('conditions'),
        }
    
    def get_plugin_options(self, collector_id):
        """
        Get additional options for plugin execution.
        
        Defined by user when creating collector, returned during job execution.
        """
        # These come as parameters in collect() method
        return {
            'collect_timeout': 3600,
            'batch_size': 50,
            'incremental_sync': True,
        }
```

---

## 💰 5. Cost Analysis API - Cost Integration

**Purpose**: Integrate Nutanix cost data with CloudForet cost analysis.

### 5.1 Register Cost Data Source

```python
# src/service/cost_datasource_service.py
from spaceone.cost_analysis.v1 import DataSource

class CostDataSourceService:
    def __init__(self, transaction):
        self.transaction = transaction
    
    def register_cost_datasource(self):
        """
        Register a cost data source for Nutanix.
        This allows CloudForet to call the plugin for cost collection.
        
        API: cost_analysis.v1.DataSource.register
        """
        response = self.transaction.execute(
            'cost_analysis.DataSource.register',
            {
                'name': 'Nutanix Cost DataSource',
                'data_source_type': 'external',  # vs 'billing', 'usage', etc.
                'provider': 'nutanix',
                'plugin_info': {
                    'plugin_id': 'plugin-nutanix-cost-datasource',
                    'version': '1.0.0',
                    'options': {
                        'cost_metric': 'vcpu_hours',
                        'cost_unit': 'USD'
                    }
                }
            }
        )
        
        return response['data_source_id']
    
    def collect_cost_data(self, data_source_id, start_date, end_date):
        """
        Collect cost data from Nutanix.
        
        CloudForet calls cost.DataSource.collect on schedule.
        """
        nutanix_costs = self._query_nutanix_costs(start_date, end_date)
        
        # Normalize to CloudForet cost format
        costs = []
        for cost_record in nutanix_costs:
            costs.append({
                'cost': cost_record['amount'],
                'currency': 'USD',
                'date': cost_record['date'],
                'resource_id': cost_record['vm_id'],
                'resource_type': 'compute.Instance',
                'metric': {
                    'vcpu_hours': cost_record['vcpu_count'] * cost_record['hours'],
                    'memory_gb_hours': cost_record['memory_gb'] * cost_record['hours'],
                },
                'tags': {
                    'cluster': cost_record['cluster'],
                    'department': cost_record['department'],
                }
            })
        
        # Push to CloudForet
        for cost in costs:
            self.transaction.execute(
                'cost_analysis.Cost.create',
                cost
            )
        
        return len(costs)
    
    def _query_nutanix_costs(self, start_date, end_date):
        """Query Nutanix API for cost data."""
        # Implementation depends on Nutanix API
        pass
```

### 5.2 Sync Cost Data

```python
# src/service/cost_sync_service.py

class CostSyncService:
    def __init__(self, transaction):
        self.transaction = transaction
    
    def sync_data_source(self, data_source_id):
        """
        Manually trigger cost data source sync.
        
        API: cost_analysis.v1.DataSource.sync
        """
        job_response = self.transaction.execute(
            'cost_analysis.DataSource.sync',
            {
                'data_source_id': data_source_id,
                'start_date': (datetime.now() - timedelta(days=30)).date(),
                'end_date': datetime.now().date()
            }
        )
        
        job_id = job_response['job_id']
        logger.info(f"Cost data sync started", extra={'job_id': job_id})
        
        return job_id
    
    def check_sync_status(self, job_id):
        """
        Check status of cost sync job.
        
        API: cost_analysis.v1.Job.get
        """
        job_info = self.transaction.execute(
            'cost_analysis.Job.get',
            {'job_id': job_id}
        )
        
        return {
            'status': job_info['status'],
            'total_count': job_info['total_count'],
            'succeeded_count': job_info['succeeded_count'],
            'failed_count': job_info['failed_count'],
        }
```

---

## 📡 6. Monitoring API - Metrics Integration

**Purpose**: Collect and expose Nutanix metrics via CloudForet monitoring.

### 6.1 Register Monitoring Data Source

```python
# src/service/monitoring_service.py
from spaceone.monitoring.v1 import DataSource

class MonitoringDataSourceService:
    def __init__(self, transaction):
        self.transaction = transaction
    
    def register_monitoring_datasource(self):
        """
        Register Nutanix as a monitoring data source.
        
        API: monitoring.v1.DataSource.register
        """
        response = self.transaction.execute(
            'monitoring.DataSource.register',
            {
                'name': 'Nutanix Monitoring DataSource',
                'plugin_info': {
                    'plugin_id': 'plugin-nutanix-mon-datasource',
                    'version': '1.0.0',
                }
            }
        )
        
        return response['data_source_id']
    
    def get_metrics(self, resource_id, metric_names, start_time, end_time):
        """
        Retrieve metrics for a resource (e.g., VM).
        
        API: monitoring.v1.Metric.list
        """
        metrics_response = self.transaction.execute(
            'monitoring.Metric.list',
            {
                'query': {
                    'filter': [
                        {'k': 'resource_id', 'v': resource_id, 'o': 'eq'},
                        {'k': 'metric_name', 'v': metric_names, 'o': 'in'},
                        {'k': 'timestamp', 'v': [start_time, end_time], 'o': 'between'},
                    ]
                }
            }
        )
        
        # Process metrics
        metrics_data = {}
        for metric in metrics_response['results']:
            metric_name = metric['metric_name']
            if metric_name not in metrics_data:
                metrics_data[metric_name] = []
            
            metrics_data[metric_name].append({
                'timestamp': metric['timestamp'],
                'value': metric['value'],
                'unit': metric['unit']
            })
        
        return metrics_data
    
    def create_metric_data(self, resource_id, metric_name, value, unit='percent'):
        """
        Push metric data for a resource.
        
        API: monitoring.v1.MetricData.create
        """
        self.transaction.execute(
            'monitoring.MetricData.create',
            {
                'resource_id': resource_id,
                'metric_name': metric_name,
                'value': value,
                'unit': unit,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
```

### 6.2 Create Webhooks for Alerts

```python
# src/service/webhook_service.py

class WebhookService:
    def __init__(self, transaction):
        self.transaction = transaction
    
    def register_webhook(self, plugin_id, webhook_name, webhook_url):
        """
        Register webhook to receive Nutanix alerts.
        
        API: monitoring.v1.Webhook.create
        """
        response = self.transaction.execute(
            'monitoring.Webhook.create',
            {
                'name': webhook_name,
                'plugin_id': plugin_id,
                'webhook_url': webhook_url,
                'protocol': 'https',
                'verify_ssl': True,
                'headers': {
                    'X-API-Key': 'plugin-api-key',
                    'Content-Type': 'application/json'
                }
            }
        )
        
        return response['webhook_id']
    
    def handle_alert_webhook(self, alert_data):
        """
        Process incoming alert from Nutanix.
        
        This would be called when Nutanix sends an alert to the webhook.
        """
        alert_event = {
            'severity': alert_data.get('severity'),
            'message': alert_data.get('message'),
            'source': 'nutanix',
            'resource_id': alert_data.get('vm_id'),
            'timestamp': datetime.utcnow().isoformat(),
            'additional_info': {
                'cluster': alert_data.get('cluster_name'),
                'alert_type': alert_data.get('type'),
            }
        }
        
        # Push event to CloudForet
        self.transaction.execute(
            'monitoring.Event.create',
            alert_event
        )
```

---

## 🔔 7. Notification API - Event Management

**Purpose**: Send plugin status updates and collection results as notifications.

### 7.1 Send Collection Notifications

```python
# src/service/notification_service.py
from spaceone.notification.v1 import Notification

class NotificationService:
    def __init__(self, transaction):
        self.transaction = transaction
    
    def notify_collection_complete(self, collector_id, job_id, stats):
        """
        Send notification when collection completes.
        
        API: notification.v1.Notification.create
        """
        message = f"""
        Collection completed for {collector_id}
        
        Resources collected:
        - Created: {stats['created']}
        - Updated: {stats['updated']}
        - Deleted: {stats['deleted']}
        - Errors: {stats['errors']}
        
        Job ID: {job_id}
        """
        
        notification = self.transaction.execute(
            'notification.Notification.create',
            {
                'title': f'Collection Complete: {collector_id}',
                'message': message,
                'notifiable_type': 'inventory.Collector',
                'notifiable_id': collector_id,
                'severity': 'INFO',
                'notification_type': 'USER',  # vs SYSTEM
                'tags': {'job_id': job_id}
            }
        )
        
        return notification['notification_id']
    
    def notify_collection_error(self, collector_id, error_message):
        """
        Send alert notification on collection failure.
        
        API: notification.v1.Notification.create
        """
        self.transaction.execute(
            'notification.Notification.create',
            {
                'title': f'Collection Failed: {collector_id}',
                'message': error_message,
                'notifiable_type': 'inventory.Collector',
                'notifiable_id': collector_id,
                'severity': 'CRITICAL',
                'notification_type': 'SYSTEM',
            }
        )
    
    def setup_notification_channels(self, collector_id):
        """
        Configure which channels to send notifications to.
        
        API: notification.v1.ProjectChannel.list
        """
        channels = self.transaction.execute(
            'notification.ProjectChannel.list',
            {
                'query': {
                    'filter': [
                        {'k': 'protocol', 'v': 'slack', 'o': 'eq'},
                        {'k': 'is_subscribe', 'v': True, 'o': 'eq'},
                    ]
                }
            }
        )
        
        return channels['results']
```

---

## 🎯 Complete Plugin Architecture with All APIs

```python
# src/server.py - Complete plugin with all API integrations

from spaceone.core.service import BaseService
from spaceone.core.service_loader import get_service

class PluginServer:
    def __init__(self):
        self.identity_service = get_service('identity.v1.Identity')
        self.inventory_service = get_service('inventory.v1.Inventory')
        self.repository_service = get_service('repository.v1.Repository')
        self.cost_service = get_service('cost_analysis.v1.CostAnalysis')
        self.monitoring_service = get_service('monitoring.v1.Monitoring')
        self.notification_service = get_service('notification.v1.Notification')
    
    async def execute_collection_workflow(self, job_params):
        """
        Complete collection workflow using all APIs.
        """
        
        # Step 1: Get credentials from Identity API
        secret_data = await self.identity_service.fetch_secret(
            job_params['secret_id']
        )
        
        # Step 2: Create/update resources via Inventory API
        resources = await self._collect_from_nutanix(secret_data)
        
        for resource in resources:
            await self.inventory_service.create_resource(
                self._normalize_resource(resource)
            )
        
        # Step 3: Register cost data via Cost Analysis API
        await self.cost_service.sync_costs(resources)
        
        # Step 4: Push metrics via Monitoring API
        for resource in resources:
            await self.monitoring_service.push_metrics(resource)
        
        # Step 5: Send notifications via Notification API
        await self.notification_service.send_completion_notice(
            len(resources),
            job_params['collector_id']
        )
        
        # Step 6: Update plugin metadata via Repository API
        await self.repository_service.update_plugin_stats(
            resources_collected=len(resources)
        )
        
        return {'status': 'COMPLETED', 'resources_count': len(resources)}

server = PluginServer()
```

---

## 📋 Summary: API Usage by Feature

| Feature | API | Method | Purpose |
|---------|-----|--------|---------|
| **Authentication** | Identity | Auth.login | Validate plugin credentials |
| **Secret Retrieval** | Identity | Secret.get | Get encrypted credentials |
| **Create Collector** | Inventory | Collector.register | Register plugin capability |
| **Create Collection Job** | Inventory | Job.create | Start resource collection |
| **Create Job Task** | Inventory | JobTask.create | Track per-account collection |
| **Save Resources** | Inventory | CloudService.create | Store discovered resources |
| **Query Resources** | Inventory | CloudService.list/stat | Retrieve collected data |
| **Register Plugin** | Repository | Plugin.register | Publish plugin info |
| **Manage Schemas** | Repository | Schema.get/update | Define data structures |
| **Collect Costs** | Cost Analysis | Cost.create | Store Nutanix cost data |
| **Sync Costs** | Cost Analysis | DataSource.sync | Trigger cost collection |
| **Push Metrics** | Monitoring | MetricData.create | Send performance metrics |
| **Get Metrics** | Monitoring | Metric.list | Retrieve metric history |
| **Send Alerts** | Monitoring | Event.create | Report critical issues |
| **Notify Users** | Notification | Notification.create | Send completion/error messages |

---

## 🔗 Cross-Service Flow Diagram

```
User clicks "Collect Now" in UI
         ↓
  Inventory.Job.create
         ↓
  Identity.Secret.get ← Fetch credentials
         ↓
  Plugin.collect() ← Call our plugin
         ↓
  Inventory.CloudService.create ← Save resources
         ↓
  Cost Analysis.Cost.create ← Save costs
         ↓
  Monitoring.MetricData.create ← Save metrics
         ↓
  Notification.Notification.create ← Send alert
         ↓
  Dashboard displays results
```

---

## 🚀 Implementation Checklist

- [ ] Implement Identity API for authentication
- [ ] Use Inventory API for Job/JobTask management
- [ ] Store resources via CloudService API
- [ ] Register plugin metadata with Repository API
- [ ] Integrate with Cost Analysis API for cost data
- [ ] Push metrics via Monitoring API
- [ ] Setup notifications via Notification API
- [ ] Test all API calls in integration environment
- [ ] Add error handling for all API calls
- [ ] Implement retry logic for failed operations
- [ ] Add comprehensive logging for all API interactions
- [ ] Document API contracts and expected responses
