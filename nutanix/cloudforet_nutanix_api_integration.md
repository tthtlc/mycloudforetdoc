# CloudForet APIs in Nutanix Plugin Development
## A Comprehensive Integration Guide with Code Examples

---

## 📋 Overview of CloudForet APIs Used in Plugin Development

Based on CloudForet's API documentation, a Nutanix plugin can integrate with multiple API services:

| API Service | Plugin Feature | Purpose |
|---|---|---|
| **Inventory API** | Resource Collection | Store collected Nutanix VMs, clusters, storage |
| **Secret API** | Credential Management | Store Nutanix API credentials securely |
| **Cost Analysis API** | Cost Attribution | Link resource usage to costs |
| **Alert Manager API** | Alerting | Create alerts for Nutanix events |
| **Notification API** | Event Notification | Send notifications on resource changes |
| **Config API** | Configuration | Store plugin-specific settings |
| **Identity API** | Access Control | Manage plugin user permissions |
| **Core API** | Plugin Registration | Register plugin metadata with CloudForet |
| **Dashboard API** | Visualization | Create custom Nutanix dashboards |

---

# 1. CORE API - Plugin Registration & Initialization

The Core API in CloudForet includes handler.proto, plugin.proto, query.proto, and server_info.proto, which define the plugin contract.

## 1.1 Plugin Initialization

Every plugin must implement the `InitPlugin` interface to tell CloudForet what it can do.

```python
# src/service/init_service.py
from spaceone.core.service import *
from spaceone.core.error import *

@authentication_handler
@authorization_handler
@event_handler
class InitPluginService(BaseService):
    """
    Plugin initialization service that tells CloudForet about Nutanix plugin capabilities.
    """
    
    def init(self, params):
        """
        Return plugin metadata and supported interfaces.
        CloudForet calls this when first registering the plugin.
        """
        return {
            'metadata': {
                'service_name': 'plugin-nutanix-inven-collector',
                'service_type': 'inventory.Collector',
                'provider': 'nutanix',
                'icon': 'https://www.nutanix.com/favicon.ico',
                'capability': {
                    'support_check_secret': True,
                    'support_stat': False
                }
            },
            'metadata_v2': {
                'service': 'inventory.Collector',
                'methods': {
                    'init': {
                        'required': [],
                        'optional': []
                    },
                    'verify': {
                        'required': ['secret'],
                    },
                    'collect': {
                        'required': ['secret'],
                        'optional': ['options']
                    }
                }
            }
        }
```

## 1.2 Plugin Health Check

The plugin must implement a health check that CloudForet calls periodically.

```python
# src/service/init_service.py (continued)

class InitPluginService(BaseService):
    
    def verify(self, params):
        """
        Verify the plugin configuration and credentials.
        Called by CloudForet to ensure the plugin is working.
        """
        secret = params.get('secret')
        options = params.get('options', {})
        
        # Validate secret schema
        if not all(key in secret for key in ['host', 'username', 'password']):
            raise ERROR_INVALID_PARAMETER(
                key='secret',
                reason='Missing required fields: host, username, password'
            )
        
        try:
            from connector.nutanix_connector import NutanixConnector
            
            connector = NutanixConnector(
                self.transaction,
                secret,
                options
            )
            
            # Test connection to Nutanix Prism
            result = connector.test_connection()
            
            return {
                'status': 'success',
                'message': f'Successfully connected to Nutanix {secret["host"]}'
            }
            
        except requests.exceptions.ConnectionError as e:
            raise ERROR_INVALID_CREDENTIALS(
                message=f'Failed to connect to Nutanix Prism: {str(e)}'
            )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connector = None
```

---

# 2. INVENTORY API - Resource Collection & Storage

The Inventory API includes cloud_service.proto, cloud_service_type.proto, collector.proto, job.proto, job_task.proto, region.proto, server.proto, and task_item.proto for managing collected resources.

## 2.1 Collecting Nutanix VMs and Normalizing to CloudForet Format

The plugin collects resources from Nutanix and transforms them into CloudForet's standard resource schema.

```python
# src/service/collector_service.py
from spaceone.core.service import *
from spaceone.inventory.plugin.collector.lib import BaseCollector

@authentication_handler
@authorization_handler
@event_handler
class NutanixCollectorService(BaseCollector):
    """
    Collector for Nutanix resources.
    Implements inventory.Collector interface.
    """
    
    def collect(self, params):
        """
        Main collection method called by CloudForet inventory service.
        Returns resources in CloudForet's standard format.
        
        Args:
            params: {
                'secret': {...},           # Nutanix credentials
                'options': {...},          # Collection options
                'job_id': 'job-12345',     # Tracking ID
                'secret_id': 'secret-123'  # Secret reference
            }
        
        Returns: Iterator of resource batches for bulk insert to CloudForet
        """
        
        secret = params.get('secret')
        options = params.get('options', {})
        job_id = params.get('job_id')
        
        # Initialize connector
        from connector.nutanix_connector import NutanixConnector
        connector = NutanixConnector(
            self.transaction,
            secret,
            options
        )
        
        _logger.info(
            'Starting Nutanix collection',
            extra={
                'job_id': job_id,
                'cluster_host': secret.get('host')
            }
        )
        
        try:
            # Collect different resource types
            resources = []
            
            # 1. Collect VMs
            vm_resources = self._collect_vms(connector, secret, options)
            resources.extend(vm_resources)
            
            # 2. Collect Nutanix clusters themselves
            cluster_resources = self._collect_clusters(connector, secret, options)
            resources.extend(cluster_resources)
            
            # 3. Collect storage volumes
            volume_resources = self._collect_volumes(connector, secret, options)
            resources.extend(volume_resources)
            
            # 4. Collect networks
            network_resources = self._collect_networks(connector, secret, options)
            resources.extend(network_resources)
            
            _logger.info(
                f'Collection completed: {len(resources)} resources collected',
                extra={'job_id': job_id}
            )
            
            # Return resources in batches (CloudForet expects batched yields)
            batch_size = options.get('batch_size', 100)
            for i in range(0, len(resources), batch_size):
                yield resources[i:i + batch_size]
                
        except Exception as e:
            _logger.error(
                f'Collection failed: {str(e)}',
                extra={'job_id': job_id},
                exc_info=True
            )
            raise

    def _collect_vms(self, connector, secret, options):
        """Collect Nutanix VMs."""
        vms_raw = connector.list_vms()
        
        resources = []
        for vm in vms_raw:
            # Normalize to CloudForet resource schema
            resource = {
                'type': 'compute.Instance',
                'id': vm['metadata']['uuid'],  # Unique identifier
                'name': vm['spec']['name'],
                'account': secret.get('account_id', 'default'),
                'instance_type': self._get_vm_type(vm),
                'launched_at': vm['metadata'].get('creation_time'),
                'state': self._map_vm_state(vm['spec']['resources']['power_state']),
                'data': {
                    'nutanix_uuid': vm['metadata']['uuid'],
                    'cpu_cores': self._calculate_cpu_cores(vm),
                    'memory_gb': vm['spec']['resources']['memory_size_mib'] / 1024,
                    'power_state': vm['spec']['resources']['power_state'],
                    'cluster_name': vm['spec'].get('cluster_reference', {}).get('name'),
                    'cluster_uuid': vm['spec'].get('cluster_reference', {}).get('uuid'),
                    'disk_size_gb': self._calculate_disk_size(vm),
                    'nic_count': len(vm['spec'].get('resources', {}).get('nic_list', [])),
                    'created_at': vm['metadata'].get('creation_time'),
                    'last_modified_at': vm['metadata'].get('last_update_time'),
                    'description': vm['spec'].get('description', ''),
                    'owner_id': vm['metadata'].get('owner_reference', {}).get('uuid'),
                },
                'tags': self._extract_tags(vm),
                'region_code': self._get_region(vm),
                'reference': {
                    'external_link': f"https://{secret['host']}:9440/#page/vm/{vm['metadata']['uuid']}"
                }
            }
            resources.append(resource)
        
        return resources

    def _collect_clusters(self, connector, secret, options):
        """Collect Nutanix clusters."""
        clusters_raw = connector.list_clusters()
        
        resources = []
        for cluster in clusters_raw:
            resource = {
                'type': 'compute.Cluster',
                'id': cluster['metadata']['uuid'],
                'name': cluster['spec']['name'],
                'account': secret.get('account_id', 'default'),
                'data': {
                    'cluster_uuid': cluster['metadata']['uuid'],
                    'version': cluster['spec'].get('resources', {}).get('config', {}).get('software_map', {}).get('nutanix', {}).get('version'),
                    'node_count': len(cluster['spec'].get('resources', {}).get('nodes', [])),
                    'hypervisor_type': cluster['spec'].get('resources', {}).get('config', {}).get('hypervisor_type'),
                },
                'region_code': secret.get('region', 'default'),
                'reference': {
                    'external_link': f"https://{secret['host']}:9440/#page/cluster/{cluster['metadata']['uuid']}"
                }
            }
            resources.append(resource)
        
        return resources

    def _collect_volumes(self, connector, secret, options):
        """Collect storage volumes."""
        volumes_raw = connector.list_volumes()
        
        resources = []
        for volume in volumes_raw:
            resource = {
                'type': 'storage.Volume',
                'id': volume['metadata']['uuid'],
                'name': volume['spec']['name'],
                'account': secret.get('account_id', 'default'),
                'data': {
                    'volume_uuid': volume['metadata']['uuid'],
                    'size_gb': volume['spec']['resources'].get('data_source', {}).get('size', 0) / (1024**3),
                    'replication_factor': volume['spec'].get('replication_factor', 1),
                },
                'region_code': secret.get('region', 'default'),
                'reference': {
                    'external_link': f"https://{secret['host']}:9440/#page/volume/{volume['metadata']['uuid']}"
                }
            }
            resources.append(resource)
        
        return resources

    def _collect_networks(self, connector, secret, options):
        """Collect virtual networks."""
        networks_raw = connector.list_networks()
        
        resources = []
        for network in networks_raw:
            resource = {
                'type': 'network.VPC',
                'id': network['metadata']['uuid'],
                'name': network['spec']['name'],
                'account': secret.get('account_id', 'default'),
                'data': {
                    'network_uuid': network['metadata']['uuid'],
                    'vlan_id': network['spec'].get('resources', {}).get('vlan_id'),
                    'subnet': network['spec'].get('resources', {}).get('ipam', {}).get('network_address'),
                },
                'region_code': secret.get('region', 'default'),
                'reference': {
                    'external_link': f"https://{secret['host']}:9440/#page/network/{network['metadata']['uuid']}"
                }
            }
            resources.append(resource)
        
        return resources

    @staticmethod
    def _map_vm_state(power_state):
        """Map Nutanix power states to CloudForet states."""
        mapping = {
            'ON': 'RUNNING',
            'OFF': 'STOPPED',
            'PAUSED': 'STOPPED',
            'SUSPENDED': 'STOPPED'
        }
        return mapping.get(power_state, 'UNKNOWN')

    @staticmethod
    def _calculate_cpu_cores(vm):
        num_sockets = vm['spec']['resources'].get('num_sockets', 1)
        num_vcpus = vm['spec']['resources'].get('num_vcpus_per_socket', 1)
        return num_sockets * num_vcpus

    @staticmethod
    def _calculate_disk_size(vm):
        total_size = 0
        for disk in vm['spec'].get('resources', {}).get('disk_list', []):
            total_size += disk.get('disk_size_bytes', 0)
        return total_size / (1024**3)  # Convert to GB

    @staticmethod
    def _extract_tags(vm):
        """Extract Nutanix categories as tags."""
        tags = {}
        for category, value in vm['metadata'].get('categories', {}).items():
            tags[f'nutanix_{category}'] = value
        return tags

    @staticmethod
    def _get_vm_type(vm):
        """Determine VM type based on CPU/memory."""
        cpu = NutanixCollectorService._calculate_cpu_cores(vm)
        memory = vm['spec']['resources'].get('memory_size_mib', 0) / 1024
        
        if cpu <= 2 and memory <= 4:
            return 'small'
        elif cpu <= 4 and memory <= 8:
            return 'medium'
        elif cpu <= 8 and memory <= 16:
            return 'large'
        else:
            return 'xlarge'

    @staticmethod
    def _get_region(vm):
        """Get region from VM metadata."""
        return vm['spec'].get('cluster_reference', {}).get('name', 'default')
```

---

# 3. SECRET API - Secure Credential Management

CloudForet's Secret API manages credentials securely, and the plugin retrieves them during collection.

## 3.1 Store Nutanix Credentials in CloudForet Secrets

```python
# Register secret schema with CloudForet
# This defines what credentials the plugin needs

SECRET_SCHEMA = {
    'type': 'object',
    'properties': {
        'host': {
            'type': 'string',
            'description': 'Nutanix Prism Central hostname or IP',
            'examples': ['prism.company.com', '10.0.0.100']
        },
        'port': {
            'type': 'integer',
            'description': 'Prism Central port (usually 9440)',
            'default': 9440
        },
        'username': {
            'type': 'string',
            'description': 'Prism Central username'
        },
        'password': {
            'type': 'string',
            'format': 'password',
            'description': 'Prism Central password'
        },
        'verify_ssl': {
            'type': 'boolean',
            'description': 'Verify SSL certificate',
            'default': True
        },
        'account_id': {
            'type': 'string',
            'description': 'CloudForet account ID (for multi-tenancy)',
            'examples': ['account-123']
        },
        'region': {
            'type': 'string',
            'description': 'Region identifier',
            'default': 'default'
        }
    },
    'required': ['host', 'username', 'password'],
    'additionalProperties': False
}

# src/connector/secret_helper.py
from spaceone.core.service import get_grpc_service

class SecretHelper:
    """Helper to interact with CloudForet Secret service."""
    
    def __init__(self, transaction):
        self.transaction = transaction
        self.secret_service = None
    
    def get_secret(self, secret_id):
        """
        Fetch a secret from CloudForet Secret service.
        
        Args:
            secret_id: Secret ID stored in CloudForet
        
        Returns:
            Decrypted secret data
        """
        if not self.secret_service:
            self.secret_service = get_grpc_service(
                'secret',
                'v1',
                self.transaction
            )
        
        # Call Secret service to get decrypted credential
        response = self.secret_service.UserSecret.get_data(
            {
                'user_secret_id': secret_id
            },
            metadata=self.transaction.get_connection_meta()
        )
        
        return response['data']

    def store_secret(self, secret_name, schema_id, data):
        """
        Store a secret in CloudForet Secret service.
        """
        if not self.secret_service:
            self.secret_service = get_grpc_service(
                'secret',
                'v1',
                self.transaction
            )
        
        response = self.secret_service.UserSecret.create(
            {
                'name': secret_name,
                'schema_id': schema_id,
                'data': data
            },
            metadata=self.transaction.get_connection_meta()
        )
        
        return response['user_secret_id']
```

## 3.2 Use Secret in Connector

```python
# src/connector/nutanix_connector.py
import requests
from request.packages.urllib3.exceptions import InsecureRequestWarning

class NutanixConnector:
    """Connect to Nutanix Prism and execute API calls."""
    
    def __init__(self, transaction, secret, options=None):
        """
        Initialize Nutanix connector.
        
        Args:
            transaction: CloudForet transaction object
            secret: Decrypted credentials (host, username, password, etc.)
            options: Collection options (batch_size, filters, etc.)
        """
        self.transaction = transaction
        self.secret = secret
        self.options = options or {}
        
        # Extract credentials
        self.host = secret.get('host')
        self.port = secret.get('port', 9440)
        self.username = secret.get('username')
        self.password = secret.get('password')
        self.verify_ssl = secret.get('verify_ssl', True)
        
        # Setup session
        self.session = self._setup_session()
        self.base_url = f'https://{self.host}:{self.port}/api/nutanix/v3'
    
    def _setup_session(self):
        """Setup requests session with authentication."""
        session = requests.Session()
        session.auth = (self.username, self.password)
        session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        if not self.verify_ssl:
            session.verify = False
            InsecureRequestWarning.disable()
        
        return session
    
    def test_connection(self):
        """Test connection to Nutanix Prism."""
        try:
            response = self.session.get(
                f'{self.base_url}/clusters/list',
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            _logger.error(f'Nutanix connection test failed: {str(e)}')
            raise
    
    def list_vms(self, filter_criteria=None):
        """Fetch list of VMs from Nutanix."""
        payload = {
            'kind': 'vm',
            'offset': 0,
            'length': 500,  # Pagination
            'filter': 'vm_state==ACTIVE'
        }
        
        # Apply custom filters if provided
        if filter_criteria:
            payload['filter'] = filter_criteria
        
        response = self.session.post(
            f'{self.base_url}/vms/list',
            json=payload,
            verify=self.verify_ssl,
            timeout=30
        )
        response.raise_for_status()
        
        return response.json().get('entities', [])
    
    # Similar methods for list_clusters, list_volumes, list_networks...
```

---

# 4. COST ANALYSIS API - Cost Attribution

Link collected resources to costs for chargeback purposes.

## 4.1 Emit Resource Cost Events

```python
# src/service/cost_service.py
from spaceone.core.service import *

class NutanixCostService(BaseService):
    """
    Service for emitting resource costs to CloudForet Cost Analysis.
    Nutanix usage can be mapped to costs for billing.
    """
    
    def emit_cost_data(self, vm_resource, connector, options):
        """
        Calculate and emit cost data for a Nutanix VM.
        
        Cost can be derived from:
        - CPU cores × hourly rate
        - Memory size × hourly rate
        - Storage used × hourly rate
        - Network usage × data rate
        """
        
        cpu_cores = vm_resource['data']['cpu_cores']
        memory_gb = vm_resource['data']['memory_gb']
        disk_gb = vm_resource['data']['disk_size_gb']
        
        # Pricing model (customizable in plugin config)
        pricing = {
            'cpu_per_core_hour': 0.05,
            'memory_per_gb_hour': 0.01,
            'disk_per_gb_month': 0.001
        }
        
        # Calculate hourly cost
        cpu_cost = cpu_cores * pricing['cpu_per_core_hour']
        memory_cost = memory_gb * pricing['memory_per_gb_hour']
        disk_cost = disk_gb * pricing['disk_per_gb_month'] / 730  # Convert monthly to hourly
        
        total_hourly_cost = cpu_cost + memory_cost + disk_cost
        
        # Emit cost data to CloudForet
        cost_event = {
            'resource_id': vm_resource['id'],
            'resource_type': vm_resource['type'],
            'cost': total_hourly_cost,
            'timestamp': datetime.utcnow().isoformat(),
            'cost_breakdown': {
                'compute': cpu_cost,
                'memory': memory_cost,
                'storage': disk_cost
            },
            'tags': vm_resource.get('tags', {}),
            'currency': 'USD'
        }
        
        return cost_event
```

---

# 5. ALERT MANAGER API - Event-Driven Alerts

Create alerts when Nutanix events occur.

## 5.1 Register Nutanix Events as CloudForet Alerts

```python
# src/service/alert_service.py
from spaceone.core.service import *
from datetime import datetime

class NutanixAlertService(BaseService):
    """
    Service for converting Nutanix events to CloudForet alerts.
    """
    
    def create_alert(self, event_data, options):
        """
        Convert a Nutanix event to a CloudForet alert.
        
        Args:
            event_data: Event from Nutanix API
            options: Alert configuration
        
        Returns:
            Alert payload compatible with CloudForet Alert Manager
        """
        
        alert_severity_map = {
            'CRITICAL': 'critical',
            'WARNING': 'warning',
            'INFO': 'info'
        }
        
        alert = {
            'title': f"Nutanix: {event_data.get('event_type')}",
            'description': event_data.get('message', ''),
            'severity': alert_severity_map.get(
                event_data.get('severity', 'INFO'),
                'info'
            ),
            'source': {
                'provider': 'nutanix',
                'service': 'compute',
                'resource_type': event_data.get('resource_type'),
                'resource_id': event_data.get('resource_uuid')
            },
            'data': {
                'nutanix_event_id': event_data.get('event_id'),
                'cluster_uuid': event_data.get('cluster_uuid'),
                'timestamp': event_data.get('timestamp'),
                'user': event_data.get('user'),
                'operation_type': event_data.get('operation_type')
            },
            'occurred_at': datetime.fromisoformat(
                event_data.get('timestamp', datetime.utcnow().isoformat())
            )
        }
        
        return alert

    def watch_nutanix_events(self, connector, interval=60):
        """
        Poll Nutanix for events and create CloudForet alerts.
        
        Args:
            connector: NutanixConnector instance
            interval: Polling interval in seconds
        """
        from time import sleep
        
        while True:
            try:
                events = connector.get_events()
                
                for event in events:
                    if self._should_create_alert(event):
                        alert = self.create_alert(event, {})
                        self._emit_alert(alert)
                
                sleep(interval)
                
            except Exception as e:
                _logger.error(f'Error watching events: {str(e)}')
                sleep(interval)

    @staticmethod
    def _should_create_alert(event):
        """Filter events that should trigger alerts."""
        # Only critical and warning severity events
        return event.get('severity') in ['CRITICAL', 'WARNING']

    def _emit_alert(self, alert):
        """Send alert to CloudForet Alert Manager."""
        from spaceone.core.service import get_grpc_service
        
        alert_service = get_grpc_service(
            'alert_manager',
            'v1',
            self.transaction
        )
        
        alert_service.Alert.create(
            alert,
            metadata=self.transaction.get_connection_meta()
        )
```

---

# 6. NOTIFICATION API - Event Notifications

Send notifications when resources change.

## 6.1 Emit Resource Change Notifications

```python
# src/service/notification_service.py
from spaceone.notification.plugin import NotificationProtocol
from datetime import datetime

class NutanixNotificationService:
    """
    Service for sending notifications about Nutanix resource changes.
    """
    
    def __init__(self, transaction):
        self.transaction = transaction
    
    def notify_resource_change(self, resource, action, details):
        """
        Send notification for resource changes (created, updated, deleted).
        
        Args:
            resource: The CloudForet resource
            action: 'created', 'updated', 'deleted'
            details: Additional details about the change
        """
        
        notification_payload = {
            'notification_type': 'resource_change',
            'title': f"Nutanix {resource['type']} {action}: {resource['name']}",
            'description': self._build_description(resource, action, details),
            'resource': {
                'type': resource['type'],
                'id': resource['id'],
                'name': resource['name'],
                'account': resource['account']
            },
            'action': action,
            'details': details,
            'timestamp': datetime.utcnow().isoformat(),
            'severity': self._determine_severity(action, details),
            'channels': ['email', 'slack', 'teams']  # Where to send
        }
        
        return notification_payload
    
    def notify_resource_state_change(self, resource, old_state, new_state):
        """
        Notify when a resource state changes (e.g., VM stopped unexpectedly).
        """
        
        # Only notify on significant state changes
        if old_state == new_state:
            return None
        
        severity_map = {
            'RUNNING': 'normal',
            'STOPPED': 'warning',
            'ERROR': 'critical',
            'UNKNOWN': 'warning'
        }
        
        notification = {
            'notification_type': 'state_change',
            'title': f"{resource['name']} state changed",
            'description': f"VM state changed from {old_state} to {new_state}",
            'resource': {
                'id': resource['id'],
                'name': resource['name'],
                'type': 'compute.Instance'
            },
            'previous_state': old_state,
            'current_state': new_state,
            'severity': severity_map.get(new_state, 'normal'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return notification

    @staticmethod
    def _build_description(resource, action, details):
        action_text = {
            'created': 'was created',
            'updated': 'was updated',
            'deleted': 'was deleted',
            'moved': 'was moved'
        }
        
        desc = f"{resource['name']} {action_text.get(action, action)}"
        
        if details:
            if 'previous_state' in details:
                desc += f" (from {details['previous_state']} to {details['new_state']})"
            if 'reason' in details:
                desc += f": {details['reason']}"
        
        return desc
    
    @staticmethod
    def _determine_severity(action, details):
        if action == 'deleted':
            return 'high'
        elif action == 'created':
            return 'low'
        elif details.get('error'):
            return 'high'
        else:
            return 'medium'
```

---

# 7. CONFIG API - Plugin Configuration Management

Store and retrieve plugin-specific configurations.

## 7.1 Store Plugin Configuration

```python
# src/service/config_service.py
from spaceone.core.service import *
from spaceone.core.service import get_grpc_service

class PluginConfigService(BaseService):
    """
    Service for managing plugin configurations via CloudForet Config API.
    """
    
    def save_plugin_config(self, config_key, config_value):
        """
        Save plugin configuration to CloudForet Config service.
        
        Args:
            config_key: Configuration key (e.g., 'nutanix_pricing_model')
            config_value: Configuration value (can be complex object)
        """
        
        config_service = get_grpc_service(
            'config',
            'v1',
            self.transaction
        )
        
        # Store in shared config (accessible to all users in workspace)
        config_service.SharedConfig.create(
            {
                'key': config_key,
                'name': f'Nutanix Plugin - {config_key}',
                'data': config_value,
                'tags': ['nutanix', 'plugin']
            },
            metadata=self.transaction.get_connection_meta()
        )

    def get_plugin_config(self, config_key):
        """
        Retrieve plugin configuration from CloudForet.
        """
        
        config_service = get_grpc_service(
            'config',
            'v1',
            self.transaction
        )
        
        configs = config_service.SharedConfig.list(
            {
                'filter': [
                    {
                        'k': 'key',
                        'v': config_key,
                        'o': 'eq'
                    }
                ]
            },
            metadata=self.transaction.get_connection_meta()
        )
        
        if configs.get('results'):
            return configs['results'][0]['data']
        
        return None

    def save_pricing_model(self, pricing_config):
        """
        Save Nutanix pricing model for cost calculation.
        
        Args:
            pricing_config: {
                'cpu_per_core_hour': 0.05,
                'memory_per_gb_hour': 0.01,
                'disk_per_gb_month': 0.001,
                'network_per_gb': 0.02
            }
        """
        self.save_plugin_config('nutanix_pricing_model', pricing_config)

    def get_collection_schedule(self):
        """
        Get resource collection schedule from Config.
        """
        return self.get_plugin_config('nutanix_collection_schedule') or {
            'interval_hours': 1,
            'batch_size': 100,
            'parallel_workers': 5
        }
```

---

# 8. IDENTITY API - Access Control

Manage plugin user permissions and roles.

## 8.1 Register Plugin Endpoints and Policies

```python
# src/service/identity_service.py
from spaceone.core.service import *
from spaceone.core.service import get_grpc_service

class PluginIdentityService(BaseService):
    """
    Service for managing plugin authentication and authorization.
    """
    
    def register_plugin_endpoint(self, plugin_name, endpoint_url):
        """
        Register the plugin endpoint with CloudForet Identity service.
        
        This allows CloudForet to discover and communicate with the plugin.
        """
        
        identity_service = get_grpc_service(
            'identity',
            'v1',
            self.transaction
        )
        
        endpoint = identity_service.Endpoint.create(
            {
                'service': 'plugin',
                'name': plugin_name,
                'url': endpoint_url,
                'extra': {
                    'plugin_type': 'inventory.Collector',
                    'provider': 'nutanix'
                }
            },
            metadata=self.transaction.get_connection_meta()
        )
        
        _logger.info(f'Plugin endpoint registered: {endpoint["endpoint_id"]}')
        return endpoint

    def create_plugin_role(self, role_name, permissions):
        """
        Create a custom role for plugin users.
        
        Args:
            role_name: Role name (e.g., 'Nutanix Operator')
            permissions: List of allowed operations
        """
        
        identity_service = get_grpc_service(
            'identity',
            'v1',
            self.transaction
        )
        
        role = identity_service.Role.create(
            {
                'name': role_name,
                'role_type': 'PROJECT',
                'permissions': permissions,
                'tags': ['nutanix', 'plugin']
            },
            metadata=self.transaction.get_connection_meta()
        )
        
        return role

    def assign_role_to_user(self, user_id, role_id):
        """
        Assign a role to a user for plugin access.
        """
        
        identity_service = get_grpc_service(
            'identity',
            'v1',
            self.transaction
        )
        
        identity_service.RoleBinding.create(
            {
                'user_id': user_id,
                'role_id': role_id,
                'scope': 'project'
            },
            metadata=self.transaction.get_connection_meta()
        )
```

---

# 9. DASHBOARD API - Custom Visualization

Create custom dashboards for Nutanix resources.

## 9.1 Create Nutanix Dashboard Widget

```python
# src/service/dashboard_service.py
from spaceone.core.service import *
from spaceone.core.service import get_grpc_service

class NutanixDashboardService(BaseService):
    """
    Service for creating custom Nutanix dashboards in CloudForet.
    """
    
    def create_nutanix_overview_dashboard(self):
        """
        Create an overview dashboard showing Nutanix inventory summary.
        """
        
        dashboard_service = get_grpc_service(
            'dashboard',
            'v1',
            self.transaction
        )
        
        # Widget 1: VM Count by State
        vm_state_widget = {
            'type': 'pie_chart',
            'name': 'VMs by State',
            'data_source': {
                'type': 'query',
                'query': {
                    'resource_type': 'compute.Instance',
                    'filter': [
                        {'key': 'provider', 'value': 'nutanix'}
                    ],
                    'group_by': ['state'],
                    'aggregation': 'count'
                }
            }
        }
        
        # Widget 2: Resource Utilization Heatmap
        utilization_widget = {
            'type': 'heatmap',
            'name': 'CPU Utilization by Cluster',
            'data_source': {
                'type': 'metric',
                'metric': 'nutanix.vm.cpu_utilization_percent',
                'dimension': 'cluster_name'
            }
        }
        
        # Widget 3: Cost Breakdown
        cost_widget = {
            'type': 'bar_chart',
            'name': 'Nutanix Cost by Resource Type',
            'data_source': {
                'type': 'cost_analysis',
                'filter': [
                    {'key': 'provider', 'value': 'nutanix'}
                ],
                'group_by': 'resource_type'
            }
        }
        
        # Widget 4: Recent Events
        events_widget = {
            'type': 'table',
            'name': 'Recent Nutanix Events',
            'data_source': {
                'type': 'query',
                'query': {
                    'resource_type': 'alert',
                    'filter': [
                        {'key': 'source.provider', 'value': 'nutanix'}
                    ],
                    'sort': ['-occurred_at'],
                    'limit': 10
                }
            }
        }
        
        # Create dashboard
        dashboard = dashboard_service.PublicDashboard.create(
            {
                'name': 'Nutanix Infrastructure Overview',
                'description': 'Complete view of Nutanix resources managed by CloudForet',
                'layouts': [
                    {
                        'name': 'Overview',
                        'widgets': [
                            {'name': 'vm_state_widget', 'size': 'md'},
                            {'name': 'utilization_widget', 'size': 'md'},
                            {'name': 'cost_widget', 'size': 'lg'},
                            {'name': 'events_widget', 'size': 'lg'}
                        ]
                    }
                ],
                'variables': [
                    {
                        'name': 'cluster_filter',
                        'type': 'resource_reference',
                        'resource_type': 'compute.Cluster'
                    }
                ],
                'tags': ['nutanix', 'infrastructure']
            },
            metadata=self.transaction.get_connection_meta()
        )
        
        return dashboard

    def create_vm_detail_dashboard(self, vm_id):
        """
        Create a detailed dashboard for a specific Nutanix VM.
        """
        
        dashboard_service = get_grpc_service(
            'dashboard',
            'v1',
            self.transaction
        )
        
        dashboard = dashboard_service.PrivateDashboard.create(
            {
                'name': f'Nutanix VM Detail: {vm_id}',
                'layouts': [
                    {
                        'widgets': [
                            {
                                'type': 'metric_card',
                                'title': 'CPU Usage',
                                'metric': 'nutanix.vm.cpu_utilization_percent',
                                'filter': {'resource_id': vm_id}
                            },
                            {
                                'type': 'metric_card',
                                'title': 'Memory Usage',
                                'metric': 'nutanix.vm.memory_utilization_percent',
                                'filter': {'resource_id': vm_id}
                            },
                            {
                                'type': 'line_chart',
                                'title': 'Network I/O',
                                'metric': 'nutanix.vm.network_throughput_mbps',
                                'filter': {'resource_id': vm_id},
                                'time_range': '24h'
                            }
                        ]
                    }
                ]
            },
            metadata=self.transaction.get_connection_meta()
        )
        
        return dashboard
```

---

# 10. MONITORING API - Performance Metrics

Export Nutanix performance metrics to CloudForet monitoring.

## 10.1 Register Monitoring Data Source

```python
# src/service/monitoring_service.py
from spaceone.core.service import *

@authentication_handler
@authorization_handler
@event_handler
class NutanixMonitoringDataSourceService(BaseService):
    """
    Data source plugin for monitoring Nutanix resources.
    Implements monitoring.DataSource interface.
    """
    
    def get_metrics(self, params):
        """
        Get performance metrics from Nutanix.
        
        Args:
            params: {
                'resource_id': 'vm-uuid',
                'metric_names': ['cpu_utilization', 'memory_utilization'],
                'start_time': '2024-01-01T00:00:00Z',
                'end_time': '2024-01-02T00:00:00Z'
            }
        """
        
        from connector.nutanix_connector import NutanixConnector
        
        secret = params.get('secret')
        connector = NutanixConnector(self.transaction, secret)
        
        resource_id = params.get('resource_id')
        metric_names = params.get('metric_names', [])
        start_time = params.get('start_time')
        end_time = params.get('end_time')
        
        metrics_data = {}
        
        for metric_name in metric_names:
            if metric_name == 'cpu_utilization':
                data = connector.get_vm_cpu_metrics(
                    resource_id,
                    start_time,
                    end_time
                )
                metrics_data['cpu_utilization'] = {
                    'unit': 'percent',
                    'data': data
                }
            
            elif metric_name == 'memory_utilization':
                data = connector.get_vm_memory_metrics(
                    resource_id,
                    start_time,
                    end_time
                )
                metrics_data['memory_utilization'] = {
                    'unit': 'percent',
                    'data': data
                }
            
            elif metric_name == 'network_throughput':
                data = connector.get_vm_network_metrics(
                    resource_id,
                    start_time,
                    end_time
                )
                metrics_data['network_throughput'] = {
                    'unit': 'mbps',
                    'data': data
                }
        
        return metrics_data

    def get_supported_metrics(self):
        """Return list of supported metrics."""
        return {
            'supported_metrics': [
                {
                    'key': 'cpu_utilization',
                    'name': 'CPU Utilization',
                    'unit': 'percent',
                    'resource_type': 'compute.Instance'
                },
                {
                    'key': 'memory_utilization',
                    'name': 'Memory Utilization',
                    'unit': 'percent',
                    'resource_type': 'compute.Instance'
                },
                {
                    'key': 'network_throughput',
                    'name': 'Network Throughput',
                    'unit': 'mbps',
                    'resource_type': 'compute.Instance'
                },
                {
                    'key': 'disk_read_latency',
                    'name': 'Disk Read Latency',
                    'unit': 'ms',
                    'resource_type': 'compute.Instance'
                },
                {
                    'key': 'disk_write_latency',
                    'name': 'Disk Write Latency',
                    'unit': 'ms',
                    'resource_type': 'compute.Instance'
                }
            ]
        }
```

---

# 11. INTEGRATION EXAMPLE - Complete Workflow

Here's how all APIs work together in a complete collection cycle:

```python
# src/service/orchestrator_service.py
from spaceone.core.service import *
import logging

_logger = logging.getLogger(__name__)

class NutanixOrchestrationService:
    """
    Orchestrates the complete Nutanix collection workflow,
    integrating all CloudForet APIs.
    """
    
    def __init__(self, transaction):
        self.transaction = transaction
    
    def execute_full_collection(self, params):
        """
        Execute complete Nutanix collection and emit to CloudForet.
        
        Workflow:
        1. Initialize plugin via Core API
        2. Fetch credentials via Secret API
        3. Collect resources via Inventory API
        4. Calculate costs via Cost Analysis API
        5. Check for alerts via Alert Manager API
        6. Store config via Config API
        7. Send notifications via Notification API
        """
        
        # Step 1: Initialize
        _logger.info('Step 1: Initializing Nutanix plugin')
        init_service = InitPluginService(self.transaction)
        init_result = init_service.init({})
        _logger.info(f'Plugin initialized: {init_result}')
        
        # Step 2: Fetch and verify credentials
        _logger.info('Step 2: Fetching credentials from Secret API')
        secret_helper = SecretHelper(self.transaction)
        secret = secret_helper.get_secret(params.get('secret_id'))
        
        # Verify credentials
        init_service.verify({'secret': secret, 'options': params.get('options', {})})
        
        # Step 3: Collect resources
        _logger.info('Step 3: Collecting Nutanix resources via Inventory API')
        collector_service = NutanixCollectorService(self.transaction)
        resources = []
        
        for batch in collector_service.collect(params):
            resources.extend(batch)
        
        _logger.info(f'Collected {len(resources)} resources')
        
        # Step 4: Calculate costs
        _logger.info('Step 4: Calculating costs via Cost Analysis API')
        cost_service = NutanixCostService(self.transaction)
        
        from connector.nutanix_connector import NutanixConnector
        connector = NutanixConnector(self.transaction, secret)
        
        for resource in resources:
            if resource['type'] == 'compute.Instance':
                cost_event = cost_service.emit_cost_data(
                    resource,
                    connector,
                    params.get('options', {})
                )
                _logger.debug(f'Cost calculated for {resource["id"]}: ${cost_event["cost"]}')
        
        # Step 5: Check for alerts
        _logger.info('Step 5: Checking for Nutanix alerts')
        alert_service = NutanixAlertService(self.transaction)
        events = connector.get_events()
        
        for event in events:
            if alert_service._should_create_alert(event):
                alert = alert_service.create_alert(event, {})
                alert_service._emit_alert(alert)
                _logger.info(f'Alert created for event: {event.get("event_id")}')
        
        # Step 6: Store collection metadata
        _logger.info('Step 6: Storing configuration via Config API')
        config_service = PluginConfigService(self.transaction)
        config_service.save_plugin_config('last_collection_time', {
            'timestamp': datetime.utcnow().isoformat(),
            'resource_count': len(resources)
        })
        
        # Step 7: Send notifications
        _logger.info('Step 7: Sending notifications for new/updated resources')
        notification_service = NutanixNotificationService(self.transaction)
        
        for resource in resources[:5]:  # Notify for first 5 resources
            notification = notification_service.notify_resource_change(
                resource,
                'collected',
                {'batch_job_id': params.get('job_id')}
            )
            _logger.debug(f'Notification sent for {resource["name"]}')
        
        # Step 8: Create dashboards
        _logger.info('Step 8: Creating Nutanix dashboards via Dashboard API')
        dashboard_service = NutanixDashboardService(self.transaction)
        dashboard = dashboard_service.create_nutanix_overview_dashboard()
        _logger.info(f'Dashboard created: {dashboard.get("dashboard_id")}')
        
        _logger.info('✅ Complete collection workflow finished successfully!')
        
        return {
            'status': 'success',
            'resources_collected': len(resources),
            'alerts_created': len([e for e in events if alert_service._should_create_alert(e)]),
            'dashboard_id': dashboard.get('dashboard_id')
        }
```

---

# 12. API Integration Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    CloudForet Nutanix Plugin                     │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
    ┌─────────┐          ┌─────────┐         ┌─────────┐
    │   Core  │          │ Identity│         │ Secret  │
    │   API   │          │   API   │         │   API   │
    ├─────────┤          ├─────────┤         ├─────────┤
    │ init()  │◄────────►│register │◄────────│ Get     │
    │verify() │          │endpoint │         │secrets  │
    │         │          │assign   │         │         │
    └─────────┘          │role     │         └─────────┘
         │               └─────────┘              │
         │                    │                   │
         │                    └──────────┬────────┘
         │                               │
         ▼                               ▼
    ┌──────────────────────────────────────────────┐
    │        Nutanix Connector (REST API)          │
    │  - list_vms()                                │
    │  - list_clusters()                           │
    │  - list_volumes()                            │
    │  - get_events()                              │
    │  - get_metrics()                             │
    └──────────────────────────────────────────────┘
         │                    │                    │
    ┌────┴────┐          ┌────┴────┐         ┌────┴────┐
    ▼         ▼          ▼         ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Invento-│ │ Cost   │ │ Alert  │ │Notif-  │ │ Config │ │Monitor-│
│   ry   │ │ Analy- │ │Manager │ │ication │ │   API  │ │  ing   │
│  API   │ │ sis    │ │  API   │ │  API   │ │        │ │  API   │
├────────┤ ├────────┤ ├────────┤ ├────────┤ ├────────┤ ├────────┤
│Create  │ │Emit    │ │Create  │ │Send    │ │Store   │ │Export  │
│Resources│ │costs   │ │alerts  │ │notifs  │ │config  │ │metrics │
│Store   │ │for VM  │ │for     │ │for     │ │schemas │ │for VMs │
│VMs     │ │usage  │ │events  │ │changes │ │pricing │ │CPU,mem │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
    │         │          │          │         │         │
    └─────────┴──────────┴──────────┴─────────┴─────────┘
                        │
                        ▼
                ┌─────────────────┐
                │ Dashboard API   │
                │ Create custom   │
                │ Nutanix         │
                │ visualizations  │
                └─────────────────┘
```

---

# 13. Summary Table: API Usage by Feature

| Feature | API | Method | Purpose |
|---------|-----|--------|---------|
| Plugin Registration | Core | `init()`, `verify()` | Register plugin with CloudForet |
| Credential Storage | Secret | `UserSecret.create()`, `UserSecret.get_data()` | Securely store Nutanix credentials |
| Resource Collection | Inventory | `Collector.collect()` | Store VM, cluster, volume resources |
| Cost Tracking | Cost Analysis | `Cost.create()`, `CostReport.get()` | Track resource costs |
| Event Alerts | Alert Manager | `Alert.create()` | Create alerts for Nutanix events |
| Notifications | Notification | `Notification.create()` | Send change notifications |
| Configuration | Config | `SharedConfig.create()`, `SharedConfig.list()` | Store plugin config/pricing |
| Access Control | Identity | `Endpoint.create()`, `Role.create()` | Manage plugin permissions |
| Performance Metrics | Monitoring | `DataSource.get_metrics()` | Export VM metrics (CPU, memory, network) |
| Visualization | Dashboard | `PublicDashboard.create()` | Create Nutanix overview dashboards |

---

# 14. Best Practices for API Integration

## 14.1 Error Handling

```python
# src/utils/error_handler.py
from spaceone.core.error import *

class APIErrorHandler:
    """Handle CloudForet API errors gracefully."""
    
    @staticmethod
    def handle_api_error(error, context=''):
        """
        Map gRPC errors to meaningful CloudForet errors.
        """
        if isinstance(error, grpc.RpcError):
            if error.code() == grpc.StatusCode.NOT_FOUND:
                raise ERROR_NOT_FOUND(key='resource')
            elif error.code() == grpc.StatusCode.PERMISSION_DENIED:
                raise ERROR_PERMISSION_DENIED()
            elif error.code() == grpc.StatusCode.UNAVAILABLE:
                raise ERROR_SERVICE_UNAVAILABLE(service='CloudForet')
            else:
                raise ERROR_INTERNAL(message=f'API error in {context}: {str(error)}')
```

## 14.2 Retry Logic

```python
# src/utils/retry.py
import time
from functools import wraps

def retry_on_transient_error(max_retries=3, backoff_factor=2):
    """
    Decorator for retrying API calls on transient errors.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (TimeoutError, ConnectionError) as e:
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        _logger.warning(
                            f'Retrying {func.__name__} after {wait_time}s '
                            f'(attempt {attempt + 1}/{max_retries}): {str(e)}'
                        )
                        time.sleep(wait_time)
                    else:
                        raise
        return wrapper
    return decorator
```

## 14.3 API Rate Limiting

```python
# src/utils/rate_limiter.py
from time import sleep, time

class APIRateLimiter:
    """Rate limit API calls to avoid throttling."""
    
    def __init__(self, calls_per_second=10):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0
    
    def wait(self):
        elapsed = time() - self.last_call
        if elapsed < self.min_interval:
            sleep(self.min_interval - elapsed)
        self.last_call = time()
```

---

## Conclusion

CloudForet provides a comprehensive set of APIs that enable the Nutanix plugin to:

1. **Collect** resources from Nutanix (Inventory API)
2. **Secure** credentials (Secret API)
3. **Track** costs (Cost Analysis API)
4. **Monitor** performance (Monitoring API)
5. **Alert** on events (Alert Manager API)
6. **Notify** users (Notification API)
7. **Configure** settings (Config API)
8. **Control** access (Identity API)
9. **Visualize** data (Dashboard API)

By leveraging these APIs, developers can create a fully integrated Nutanix management solution within CloudForet's multi-cloud platform.

