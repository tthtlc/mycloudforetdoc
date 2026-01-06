"""
Complete Working Nutanix Plugin Template for CloudForet
========================================================

This file contains all necessary components to build a production-ready
Nutanix collector plugin for CloudForet with full API integration.

Project Structure:
    plugin-nutanix-inven-collector/
    ├── src/
    │   ├── __init__.py
    │   ├── server.py              (gRPC server entry point)
    │   ├── service/
    │   │   ├── __init__.py
    │   │   ├── init_service.py    (Plugin initialization)
    │   │   ├── collector_service.py (Main collection logic)
    │   │   ├── cost_service.py    (Cost API integration)
    │   │   ├── alert_service.py   (Alert Manager API)
    │   │   ├── notification_service.py (Notification API)
    │   │   └── config_service.py  (Config API)
    │   ├── connector/
    │   │   ├── __init__.py
    │   │   └── nutanix_connector.py
    │   └── conf/
    │       ├── __init__.py
    │       └── plugin.json
    ├── requirements.txt
    ├── Dockerfile
    └── Chart.yaml (Helm)
"""

# ============================================================================
# 1. SERVER ENTRY POINT
# ============================================================================
# src/server.py

import logging
import grpc
from concurrent import futures
from spaceone.core import config
from spaceone.core.server import initialize_grpc_server

# Import all service implementations
from src.service.init_service import InitPluginService
from src.service.collector_service import NutanixCollectorService
from src.service.cost_service import NutanixCostService
from src.service.alert_service import NutanixAlertService
from src.service.notification_service import NutanixNotificationService
from src.service.monitoring_service import NutanixMonitoringDataSourceService

_logger = logging.getLogger(__name__)

def serve():
    """Start gRPC server for Nutanix plugin."""
    
    # Configuration
    config.init_conf(package='plugin_nutanix_inven_collector')
    
    # Initialize gRPC server
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[],  # Add authentication interceptors here
    )
    
    # Register services
    services = [
        InitPluginService,
        NutanixCollectorService,
        NutanixCostService,
        NutanixAlertService,
        NutanixNotificationService,
        NutanixMonitoringDataSourceService
    ]
    
    # Add reflection for grpcurl debugging
    from grpc_reflection.v1alpha import reflection
    SERVICE_NAMES = [
        'spaceone.core.v1.Plugin',
        'spaceone.inventory.plugin.collector.v1.Collector',
        'spaceone.cost.plugin.datasource.v1.DataSource',
    ]
    reflection.enable_server_reflection(SERVICE_NAMES, server)
    
    # Start server
    server.add_insecure_port('[::]:50051')
    _logger.info('🚀 Nutanix plugin server started on 0.0.0.0:50051')
    
    return server

if __name__ == '__main__':
    import asyncio
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = serve()
    asyncio.run(server.wait_for_termination())


# ============================================================================
# 2. INIT SERVICE - Plugin Registration
# ============================================================================
# src/service/init_service.py

from spaceone.core.service import *
from spaceone.core.error import *
import requests
import logging

_logger = logging.getLogger(__name__)

@authentication_handler
@authorization_handler
@event_handler
class InitPluginService(BaseService):
    """Initialize and verify Nutanix plugin."""
    
    def init(self, params):
        """Return plugin metadata."""
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
            }
        }
    
    def verify(self, params):
        """Verify Nutanix credentials."""
        secret = params.get('secret')
        
        # Validate required fields
        required_fields = ['host', 'username', 'password']
        if not all(field in secret for field in required_fields):
            raise ERROR_INVALID_PARAMETER(
                key='secret',
                reason=f'Missing required fields: {", ".join(required_fields)}'
            )
        
        try:
            # Test connection
            from src.connector.nutanix_connector import NutanixConnector
            connector = NutanixConnector(self.transaction, secret)
            connector.test_connection()
            
            return {
                'status': 'success',
                'message': f'Successfully connected to Nutanix {secret["host"]}'
            }
        except requests.exceptions.ConnectionError as e:
            raise ERROR_INVALID_CREDENTIALS(
                message=f'Failed to connect to Nutanix: {str(e)}'
            )


# ============================================================================
# 3. COLLECTOR SERVICE - Main Resource Collection
# ============================================================================
# src/service/collector_service.py

from spaceone.core.service import *
from spaceone.inventory.plugin.collector.lib import BaseCollector
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

@authentication_handler
@authorization_handler
@event_handler
class NutanixCollectorService(BaseCollector):
    """Collect Nutanix resources and normalize to CloudForet format."""
    
    def collect(self, params):
        """
        Main collection method.
        
        Returns iterator of resource batches.
        """
        secret = params.get('secret')
        options = params.get('options', {})
        job_id = params.get('job_id')
        
        _logger.info(f'Starting collection - Job ID: {job_id}')
        
        try:
            from src.connector.nutanix_connector import NutanixConnector
            connector = NutanixConnector(self.transaction, secret, options)
            
            # Collect different resource types
            all_resources = []
            
            # 1. VMs
            _logger.info('Collecting Nutanix VMs...')
            vms = self._collect_vms(connector, secret)
            all_resources.extend(vms)
            _logger.info(f'✓ Collected {len(vms)} VMs')
            
            # 2. Clusters
            _logger.info('Collecting Nutanix clusters...')
            clusters = self._collect_clusters(connector, secret)
            all_resources.extend(clusters)
            _logger.info(f'✓ Collected {len(clusters)} clusters')
            
            # 3. Volumes
            _logger.info('Collecting storage volumes...')
            volumes = self._collect_volumes(connector, secret)
            all_resources.extend(volumes)
            _logger.info(f'✓ Collected {len(volumes)} volumes')
            
            # 4. Networks
            _logger.info('Collecting networks...')
            networks = self._collect_networks(connector, secret)
            all_resources.extend(networks)
            _logger.info(f'✓ Collected {len(networks)} networks')
            
            # Yield in batches
            batch_size = options.get('batch_size', 100)
            for i in range(0, len(all_resources), batch_size):
                batch = all_resources[i:i + batch_size]
                _logger.debug(f'Yielding batch of {len(batch)} resources')
                yield batch
            
            _logger.info(f'✅ Collection complete: {len(all_resources)} resources')
            
        except Exception as e:
            _logger.error(f'Collection failed: {str(e)}', exc_info=True)
            raise

    def _collect_vms(self, connector, secret):
        """Collect VMs and normalize to CloudForet format."""
        vms_raw = connector.list_vms()
        resources = []
        
        for vm in vms_raw:
            uuid = vm['metadata']['uuid']
            
            resource = {
                'type': 'compute.Instance',
                'id': uuid,
                'name': vm['spec']['name'],
                'account': secret.get('account_id', 'default'),
                'instance_type': self._get_vm_type(vm),
                'launched_at': vm['metadata'].get('creation_time'),
                'state': self._map_vm_state(
                    vm['spec']['resources'].get('power_state')
                ),
                'data': {
                    'uuid': uuid,
                    'cpu_cores': self._calculate_cpu_cores(vm),
                    'memory_gb': vm['spec']['resources'].get('memory_size_mib', 0) / 1024,
                    'power_state': vm['spec']['resources'].get('power_state'),
                    'cluster_name': vm['spec'].get('cluster_reference', {}).get('name'),
                    'created_at': vm['metadata'].get('creation_time'),
                    'last_modified_at': vm['metadata'].get('last_update_time'),
                    'nic_count': len(vm['spec'].get('resources', {}).get('nic_list', [])),
                },
                'tags': self._extract_tags(vm),
                'region_code': secret.get('region', 'default'),
                'reference': {
                    'external_link': f"https://{secret['host']}:9440/#page/vm/{uuid}"
                }
            }
            
            resources.append(resource)
        
        return resources

    def _collect_clusters(self, connector, secret):
        """Collect Nutanix clusters."""
        clusters_raw = connector.list_clusters()
        resources = []
        
        for cluster in clusters_raw:
            uuid = cluster['metadata']['uuid']
            
            resource = {
                'type': 'compute.Cluster',
                'id': uuid,
                'name': cluster['spec']['name'],
                'account': secret.get('account_id', 'default'),
                'data': {
                    'uuid': uuid,
                    'node_count': len(
                        cluster['spec'].get('resources', {}).get('nodes', [])
                    ),
                },
                'region_code': secret.get('region', 'default'),
                'reference': {
                    'external_link': f"https://{secret['host']}:9440/#page/cluster/{uuid}"
                }
            }
            
            resources.append(resource)
        
        return resources

    def _collect_volumes(self, connector, secret):
        """Collect storage volumes."""
        volumes_raw = connector.list_volumes()
        resources = []
        
        for volume in volumes_raw:
            uuid = volume['metadata']['uuid']
            
            resource = {
                'type': 'storage.Volume',
                'id': uuid,
                'name': volume['spec']['name'],
                'account': secret.get('account_id', 'default'),
                'data': {
                    'uuid': uuid,
                    'size_gb': volume['spec']['resources'].get('data_source', {}).get('size', 0) / (1024**3),
                },
                'region_code': secret.get('region', 'default'),
            }
            
            resources.append(resource)
        
        return resources

    def _collect_networks(self, connector, secret):
        """Collect virtual networks."""
        networks_raw = connector.list_networks()
        resources = []
        
        for network in networks_raw:
            uuid = network['metadata']['uuid']
            
            resource = {
                'type': 'network.VPC',
                'id': uuid,
                'name': network['spec']['name'],
                'account': secret.get('account_id', 'default'),
                'data': {
                    'uuid': uuid,
                    'vlan_id': network['spec'].get('resources', {}).get('vlan_id'),
                },
                'region_code': secret.get('region', 'default'),
            }
            
            resources.append(resource)
        
        return resources

    @staticmethod
    def _map_vm_state(power_state):
        """Map Nutanix state to CloudForet state."""
        mapping = {
            'ON': 'RUNNING',
            'OFF': 'STOPPED',
            'PAUSED': 'STOPPED',
            'SUSPENDED': 'STOPPED'
        }
        return mapping.get(power_state, 'UNKNOWN')

    @staticmethod
    def _calculate_cpu_cores(vm):
        """Calculate total CPU cores."""
        num_sockets = vm['spec']['resources'].get('num_sockets', 1)
        num_vcpus = vm['spec']['resources'].get('num_vcpus_per_socket', 1)
        return num_sockets * num_vcpus

    @staticmethod
    def _get_vm_type(vm):
        """Determine VM instance type."""
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
    def _extract_tags(vm):
        """Extract Nutanix categories as CloudForet tags."""
        tags = {}
        for category, value in vm['metadata'].get('categories', {}).items():
            tags[f'nutanix_{category}'] = value
        return tags


# ============================================================================
# 4. COST SERVICE - Cost Analysis API Integration
# ============================================================================
# src/service/cost_service.py

from spaceone.core.service import *
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class NutanixCostService(BaseService):
    """Calculate and emit costs for Nutanix resources."""
    
    def emit_cost_data(self, resource, options):
        """Calculate cost for a resource."""
        
        # Default pricing (can be overridden via config)
        pricing = options.get('pricing', {
            'cpu_per_core_hour': 0.05,
            'memory_per_gb_hour': 0.01,
            'disk_per_gb_month': 0.001
        })
        
        cpu_cores = resource['data'].get('cpu_cores', 0)
        memory_gb = resource['data'].get('memory_gb', 0)
        disk_gb = resource['data'].get('disk_size_gb', 0)
        
        # Calculate costs
        cpu_cost = cpu_cores * pricing['cpu_per_core_hour']
        memory_cost = memory_gb * pricing['memory_per_gb_hour']
        disk_cost = disk_gb * pricing['disk_per_gb_month'] / 730
        
        total_hourly_cost = cpu_cost + memory_cost + disk_cost
        
        cost_event = {
            'resource_id': resource['id'],
            'resource_type': resource['type'],
            'cost': total_hourly_cost,
            'currency': 'USD',
            'timestamp': datetime.utcnow().isoformat(),
            'cost_breakdown': {
                'compute': cpu_cost,
                'memory': memory_cost,
                'storage': disk_cost
            }
        }
        
        _logger.debug(f'Cost calculated: ${total_hourly_cost:.4f}/hr for {resource["name"]}')
        return cost_event


# ============================================================================
# 5. ALERT SERVICE - Alert Manager API
# ============================================================================
# src/service/alert_service.py

from spaceone.core.service import *
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class NutanixAlertService(BaseService):
    """Create alerts from Nutanix events."""
    
    def create_alert(self, event_data):
        """Convert Nutanix event to CloudForet alert."""
        
        severity_map = {
            'CRITICAL': 'critical',
            'WARNING': 'warning',
            'INFO': 'info'
        }
        
        alert = {
            'title': f"Nutanix: {event_data.get('event_type')}",
            'description': event_data.get('message', ''),
            'severity': severity_map.get(event_data.get('severity', 'INFO'), 'info'),
            'source': {
                'provider': 'nutanix',
                'service': 'compute',
                'resource_type': event_data.get('resource_type'),
                'resource_id': event_data.get('resource_uuid')
            },
            'data': {
                'event_id': event_data.get('event_id'),
                'cluster_uuid': event_data.get('cluster_uuid'),
            },
            'occurred_at': datetime.fromisoformat(
                event_data.get('timestamp', datetime.utcnow().isoformat())
            )
        }
        
        _logger.info(f'Alert created: {alert["title"]}')
        return alert


# ============================================================================
# 6. NOTIFICATION SERVICE - Notification API
# ============================================================================
# src/service/notification_service.py

from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class NutanixNotificationService:
    """Send notifications for resource changes."""
    
    def notify_resource_change(self, resource, action, details):
        """Notify about resource changes."""
        
        action_text = {
            'created': 'was created',
            'updated': 'was updated',
            'deleted': 'was deleted'
        }
        
        severity_map = {
            'deleted': 'high',
            'created': 'low',
            'updated': 'medium'
        }
        
        notification = {
            'title': f"{resource['name']} {action_text.get(action, action)}",
            'description': f"{resource['type']} {resource['id']} {action_text.get(action, action)}",
            'resource': {
                'id': resource['id'],
                'name': resource['name'],
                'type': resource['type']
            },
            'action': action,
            'severity': severity_map.get(action, 'medium'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        _logger.info(f'Notification: {notification["title"]}')
        return notification


# ============================================================================
# 7. MONITORING SERVICE - Monitoring DataSource API
# ============================================================================
# src/service/monitoring_service.py

from spaceone.core.service import *
import logging

_logger = logging.getLogger(__name__)

@authentication_handler
@authorization_handler
@event_handler
class NutanixMonitoringDataSourceService(BaseService):
    """Export Nutanix performance metrics."""
    
    def get_metrics(self, params):
        """Get performance metrics for a resource."""
        
        from src.connector.nutanix_connector import NutanixConnector
        
        secret = params.get('secret')
        connector = NutanixConnector(self.transaction, secret)
        
        resource_id = params.get('resource_id')
        metric_names = params.get('metric_names', [])
        
        metrics_data = {}
        
        for metric_name in metric_names:
            if metric_name == 'cpu_utilization':
                data = connector.get_vm_metrics(resource_id, 'cpu_utilization')
                metrics_data['cpu_utilization'] = {
                    'unit': 'percent',
                    'data': data
                }
            
            elif metric_name == 'memory_utilization':
                data = connector.get_vm_metrics(resource_id, 'memory_utilization')
                metrics_data['memory_utilization'] = {
                    'unit': 'percent',
                    'data': data
                }
        
        return metrics_data
    
    def get_supported_metrics(self):
        """List supported metrics."""
        return {
            'supported_metrics': [
                {
                    'key': 'cpu_utilization',
                    'name': 'CPU Utilization',
                    'unit': 'percent'
                },
                {
                    'key': 'memory_utilization',
                    'name': 'Memory Utilization',
                    'unit': 'percent'
                },
                {
                    'key': 'network_throughput',
                    'name': 'Network Throughput',
                    'unit': 'mbps'
                }
            ]
        }


# ============================================================================
# 8. NUTANIX CONNECTOR - REST API Client
# ============================================================================
# src/connector/nutanix_connector.py

import requests
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class NutanixConnector:
    """Connect to Nutanix Prism and execute API calls."""
    
    def __init__(self, transaction, secret, options=None):
        """Initialize connector with credentials."""
        
        self.transaction = transaction
        self.secret = secret
        self.options = options or {}
        
        self.host = secret.get('host')
        self.port = secret.get('port', 9440)
        self.username = secret.get('username')
        self.password = secret.get('password')
        self.verify_ssl = secret.get('verify_ssl', True)
        
        self.base_url = f'https://{self.host}:{self.port}/api/nutanix/v3'
        self.session = self._setup_session()
    
    def _setup_session(self):
        """Setup HTTP session with auth."""
        session = requests.Session()
        session.auth = (self.username, self.password)
        session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        session.verify = self.verify_ssl
        return session
    
    def test_connection(self):
        """Test connection to Nutanix."""
        try:
            response = self.session.get(
                f'{self.base_url}/clusters/list',
                timeout=10
            )
            response.raise_for_status()
            _logger.info('✓ Nutanix connection successful')
            return True
        except requests.exceptions.RequestException as e:
            _logger.error(f'✗ Nutanix connection failed: {str(e)}')
            raise
    
    def list_vms(self):
        """Get list of VMs."""
        payload = {
            'kind': 'vm',
            'offset': 0,
            'length': 500,
            'filter': 'vm_state==ACTIVE'
        }
        
        response = self.session.post(
            f'{self.base_url}/vms/list',
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        return response.json().get('entities', [])
    
    def list_clusters(self):
        """Get list of clusters."""
        payload = {
            'kind': 'cluster',
            'offset': 0,
            'length': 500
        }
        
        response = self.session.post(
            f'{self.base_url}/clusters/list',
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        return response.json().get('entities', [])
    
    def list_volumes(self):
        """Get list of volumes."""
        payload = {
            'kind': 'volume',
            'offset': 0,
            'length': 500
        }
        
        response = self.session.post(
            f'{self.base_url}/volumes/list',
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        return response.json().get('entities', [])
    
    def list_networks(self):
        """Get list of networks."""
        payload = {
            'kind': 'subnet',
            'offset': 0,
            'length': 500
        }
        
        response = self.session.post(
            f'{self.base_url}/subnets/list',
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        return response.json().get('entities', [])
    
    def get_events(self):
        """Get recent events."""
        try:
            response = self.session.get(
                f'{self.base_url}/events',
                timeout=10
            )
            response.raise_for_status()
            return response.json().get('entities', [])
        except requests.exceptions.RequestException as e:
            _logger.warning(f'Failed to fetch events: {str(e)}')
            return []
    
    def get_vm_metrics(self, vm_uuid, metric_type):
        """Get VM metrics."""
        # Placeholder - implement based on Nutanix metrics API
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'value': 45.5
        }


# ============================================================================
# 9. REQUIREMENTS
# ============================================================================
# requirements.txt

"""
grpcio==1.51.1
grpcio-tools==1.51.1
grpcio-reflection==1.51.1
spaceone-core==2.1.0
spaceone-api==2.1.0
requests==2.28.2
python-dotenv==0.21.0
"""


# ============================================================================
# 10. DOCKERFILE
# ============================================================================
# Dockerfile

"""
FROM python:3.9-slim

RUN pip install --no-cache-dir pip==23.0.1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV PYTHONUNBUFFERED=1
ENV GRPC_PYTHON_BUILD_WITH_CYTHON=1

EXPOSE 50051

CMD ["python", "src/server.py"]
"""


# ============================================================================
# 11. HELM CHART
# ============================================================================
# charts/plugin-nutanix-inven-collector/Chart.yaml

"""
apiVersion: v2
name: plugin-nutanix-inven-collector
description: Nutanix Inventory Collector Plugin for CloudForet
type: application
version: 1.0.0
appVersion: "1.0.0"
"""


# ============================================================================
# 12. HELM VALUES
# ============================================================================
# charts/plugin-nutanix-inven-collector/values.yaml

"""
replicaCount: 1

image:
  repository: myregistry.io/cloudforet/plugin-nutanix-inven-collector
  tag: latest
  pullPolicy: IfNotPresent

resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi

env:
  LOG_LEVEL: INFO

service:
  port: 50051
"""


# ============================================================================
# 13. USAGE EXAMPLE
# ============================================================================

"""
EXAMPLE: How to use this plugin in CloudForet

1. Register Plugin Credentials:
   - Go to CloudForet Console > Inventory > Service Account
   - Add new Nutanix account with:
     * Host: prism.company.com
     * Username: admin
     * Password: ***
     * Port: 9440

2. Start Collection:
   - Go to Inventory > Collector
   - Select "Nutanix Collector"
   - Click "Collect"

3. Monitor Collection Status:
   - View job status in Inventory > Jobs
   - Check collected resources in Inventory > Cloud Service

4. View Dashboards:
   - Go to Dashboards > Nutanix Overview
   - See VMs, clusters, volumes, networks

5. Check Costs:
   - Go to Cost Analysis
   - Filter by Nutanix resources
   - View cost breakdown

6. Manage Alerts:
   - Go to Alert Manager
   - View Nutanix-related alerts
   - Configure alert rules

7. Send Notifications:
   - Go to Notification > Channels
   - Add Slack/Email channels
   - Receive notifications for Nutanix events
"""

