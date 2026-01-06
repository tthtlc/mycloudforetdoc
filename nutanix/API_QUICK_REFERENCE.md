# CloudForet Nutanix Plugin - API Quick Reference Card

## 🔧 Core API - Plugin Registration

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `init()` | none | metadata dict | Return plugin capabilities |
| `verify()` | `{'secret': {...}}` | `{'status': 'success'}` | Test Nutanix credentials |

```python
# Example
service = InitPluginService(transaction)
service.init({})  # Register with CloudForet
service.verify({'secret': {'host': 'prism.local', ...}})  # Test connection
```

---

## 📦 Inventory API - Resource Collection

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `collect()` | `{'secret': {...}, 'options': {...}, 'job_id': '...'}` | Iterator[List[Resource]] | Collect VMs, clusters, volumes, networks |

```python
# Example
service = NutanixCollectorService(transaction)
for batch in service.collect(params):
    yield batch  # Returns normalized resources

# Resource format
{
  'type': 'compute.Instance',
  'id': 'vm-uuid',
  'name': 'vm-name',
  'account': 'account-id',
  'data': {'cpu_cores': 4, 'memory_gb': 8.0},
  'tags': {'nutanix_category': 'value'}
}
```

---

## 🔐 Secret API - Credential Management

| Service | Method | Input | Output | Purpose |
|---------|--------|-------|--------|---------|
| Secret | `UserSecret.create()` | name, schema_id, data | user_secret_id | Store credentials |
| Secret | `UserSecret.get_data()` | user_secret_id | decrypted data | Retrieve credentials |
| Secret | `UserSecret.list()` | filters | List[UserSecret] | List all secrets |

```python
# Example
helper = SecretHelper(transaction)

# Retrieve Nutanix credentials
secret = helper.get_secret('secret-123')
# Returns: {'host': 'prism.local', 'username': 'admin', 'password': 'decrypted'}

# Store secret schema
secret_schema = {
  'type': 'object',
  'properties': {
    'host': {'type': 'string'},
    'username': {'type': 'string'},
    'password': {'type': 'string', 'format': 'password'}
  },
  'required': ['host', 'username', 'password']
}
```

---

## 💰 Cost Analysis API - Cost Tracking

| Service | Method | Input | Output | Purpose |
|---------|--------|-------|--------|---------|
| Cost | `Cost.create()` | cost_data dict | cost_id | Record resource cost |
| CostReport | `get()` | cost_report_id | report data | Get cost report |

```python
# Example
cost_event = {
  'resource_id': 'vm-001',
  'resource_type': 'compute.Instance',
  'cost': 0.25,
  'currency': 'USD',
  'timestamp': '2024-01-01T12:00:00Z',
  'cost_breakdown': {
    'compute': 0.20,
    'memory': 0.05
  }
}

# Emit to CloudForet
cost_service.emit_cost_data(resource, options)
```

**Cost Calculation Formula:**
```
Total Cost = (CPU Cores × CPU Rate) + (Memory GB × Memory Rate) + (Storage GB × Storage Rate)

Example:
4 cores × $0.05/hr = $0.20/hr
8 GB × $0.01/hr = $0.08/hr
100 GB × $0.001/month ÷ 730 = $0.00014/hr
──────────────────────────────────
Total = $0.28/hr
```

---

## 🚨 Alert Manager API - Alerts

| Service | Method | Input | Output | Purpose |
|---------|--------|-------|--------|---------|
| Alert | `create()` | alert dict | alert_id | Create alert from event |
| Alert | `update()` | alert_id, updates | updated alert | Update alert status |
| Alert | `list()` | filters | List[Alert] | Query alerts |

```python
# Example
alert = {
  'title': 'Nutanix: VM_POWER_OFF',
  'description': 'VM powered off unexpectedly',
  'severity': 'warning',  # critical, warning, info
  'source': {
    'provider': 'nutanix',
    'resource_type': 'compute.Instance',
    'resource_id': 'vm-001'
  },
  'data': {
    'event_id': 'evt-001',
    'timestamp': '2024-01-01T12:00:00Z'
  }
}

alert_service.create_alert(nutanix_event)
```

**Severity Levels:**
- `critical`: Immediate action needed
- `warning`: Requires attention
- `info`: Informational only

---

## 📢 Notification API - Event Notifications

| Service | Method | Input | Output | Purpose |
|---------|--------|-------|--------|---------|
| Notification | `create()` | notification dict | notification_id | Send notification |
| Notification | `list()` | filters | List[Notification] | Query notifications |

```python
# Example
notification = {
  'title': 'VM created: prod-web-01',
  'description': 'New VM added to CloudForet inventory',
  'resource': {
    'id': 'vm-001',
    'name': 'prod-web-01',
    'type': 'compute.Instance'
  },
  'action': 'created',  # created, updated, deleted
  'severity': 'low',
  'channels': ['email', 'slack', 'teams'],
  'timestamp': '2024-01-01T12:00:00Z'
}

notification_service.notify_resource_change(resource, 'created', details)
```

---

## ⚙️ Config API - Configuration

| Service | Method | Input | Output | Purpose |
|---------|--------|-------|--------|---------|
| SharedConfig | `create()` | key, name, data | config_id | Store shared config |
| SharedConfig | `list()` | filters | List[Config] | Query configs |
| SharedConfig | `update()` | config_id, updates | updated config | Update config |

```python
# Example: Store pricing model
config_service.save_plugin_config('nutanix_pricing_model', {
  'cpu_per_core_hour': 0.05,
  'memory_per_gb_hour': 0.01,
  'disk_per_gb_month': 0.001,
  'network_per_gb': 0.02
})

# Example: Get collection schedule
schedule = config_service.get_plugin_config('nutanix_collection_schedule')
# Returns: {'interval_hours': 1, 'batch_size': 100}
```

---

## 👥 Identity API - Access Control

| Service | Method | Input | Output | Purpose |
|---------|--------|-------|--------|---------|
| Endpoint | `create()` | service, name, url | endpoint_id | Register plugin endpoint |
| Role | `create()` | name, permissions | role_id | Create custom role |
| RoleBinding | `create()` | user_id, role_id, scope | binding_id | Assign role to user |

```python
# Example: Register plugin endpoint
identity_service.register_plugin_endpoint(
  plugin_name='plugin-nutanix-inven-collector',
  endpoint_url='grpc://plugin-nutanix:50051'
)

# Example: Create role
identity_service.create_plugin_role(
  role_name='Nutanix Operator',
  permissions=['inventory.read', 'inventory.write']
)
```

---

## 📊 Monitoring API - Metrics

| Service | Method | Input | Output | Purpose |
|---------|--------|-------|--------|---------|
| DataSource | `get_metrics()` | resource_id, metric_names | metrics dict | Fetch metrics |
| DataSource | `get_supported_metrics()` | none | List[Metric] | List available metrics |

```python
# Example: Get VM metrics
metrics = monitoring_service.get_metrics({
  'resource_id': 'vm-001',
  'metric_names': ['cpu_utilization', 'memory_utilization'],
  'start_time': '2024-01-01T00:00:00Z',
  'end_time': '2024-01-02T00:00:00Z'
})

# Returns
{
  'cpu_utilization': {
    'unit': 'percent',
    'data': [
      {'timestamp': '2024-01-01T00:00:00Z', 'value': 45.5},
      {'timestamp': '2024-01-01T01:00:00Z', 'value': 52.3}
    ]
  }
}

# Supported metrics
{
  'cpu_utilization': 'percent',
  'memory_utilization': 'percent',
  'network_throughput': 'mbps',
  'disk_read_latency': 'ms',
  'disk_write_latency': 'ms'
}
```

---

## 📈 Dashboard API - Visualization

| Service | Method | Input | Output | Purpose |
|---------|--------|-------|--------|---------|
| PublicDashboard | `create()` | name, layouts, widgets | dashboard_id | Create shared dashboard |
| PrivateDashboard | `create()` | name, layouts, widgets | dashboard_id | Create private dashboard |
| CustomWidget | `create()` | type, data_source | widget_id | Create custom widget |

```python
# Example: Create overview dashboard
dashboard = {
  'name': 'Nutanix Infrastructure',
  'layouts': [
    {
      'widgets': [
        {
          'type': 'pie_chart',
          'title': 'VMs by State',
          'data_source': {
            'query': {
              'resource_type': 'compute.Instance',
              'group_by': 'state'
            }
          }
        },
        {
          'type': 'bar_chart',
          'title': 'Cost by Resource Type',
          'data_source': {
            'type': 'cost_analysis',
            'group_by': 'resource_type'
          }
        }
      ]
    }
  ]
}

dashboard_service.create_nutanix_overview_dashboard()
```

**Widget Types:**
- `pie_chart`: Show proportions
- `bar_chart`: Compare values
- `line_chart`: Show trends over time
- `heatmap`: Show 2D data distribution
- `metric_card`: Show single metric
- `table`: Show tabular data

---

## 🔌 Nutanix Connector Methods

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `test_connection()` | none | True/raises | Verify connectivity |
| `list_vms()` | filters (optional) | List[VM] | Fetch all VMs |
| `list_clusters()` | filters (optional) | List[Cluster] | Fetch all clusters |
| `list_volumes()` | filters (optional) | List[Volume] | Fetch all volumes |
| `list_networks()` | filters (optional) | List[Network] | Fetch all networks |
| `get_events()` | none | List[Event] | Fetch recent events |
| `get_vm_metrics()` | vm_uuid, metric_type | metric_data | Fetch VM metrics |

```python
# Example usage
connector = NutanixConnector(transaction, secret, options)

# Test connection
connector.test_connection()  # Raises exception if fails

# List resources
vms = connector.list_vms()
clusters = connector.list_clusters()

# Fetch metrics
metrics = connector.get_vm_metrics('vm-001', 'cpu_utilization')
```

---

## 🐛 Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `ERROR_INVALID_CREDENTIALS` | Wrong Nutanix credentials | Verify host, username, password |
| `ERROR_NOT_FOUND` | Resource doesn't exist | Check resource ID is correct |
| `ERROR_PERMISSION_DENIED` | User lacks permission | Verify API key/role permissions |
| `ERROR_SERVICE_UNAVAILABLE` | Service unreachable | Check network, firewall, DNS |
| `ERROR_GRPC_CONNECTION` | Cannot connect to gRPC service | Verify endpoint URL |
| `ERROR_INVALID_PARAMETER` | Missing required field | Check input schema |

```python
# Error handling example
try:
    connector.test_connection()
except requests.ConnectionError:
    raise ERROR_INVALID_CREDENTIALS(message='Failed to connect to Nutanix')
except Exception as e:
    _logger.error(f'Unexpected error: {str(e)}')
    raise ERROR_INTERNAL(message=str(e))
```

---

## 📋 Resource Schema Examples

### Compute Instance
```json
{
  "type": "compute.Instance",
  "id": "vm-001",
  "name": "prod-web-01",
  "account": "account-123",
  "instance_type": "large",
  "launched_at": "2024-01-01T00:00:00Z",
  "state": "RUNNING",
  "data": {
    "uuid": "vm-001",
    "cpu_cores": 4,
    "memory_gb": 8.0,
    "power_state": "ON"
  },
  "tags": {
    "environment": "production",
    "team": "platform"
  },
  "region_code": "cluster-1"
}
```

### Cluster
```json
{
  "type": "compute.Cluster",
  "id": "cluster-001",
  "name": "nutanix-cluster-1",
  "account": "account-123",
  "data": {
    "node_count": 3
  },
  "region_code": "datacenter-us-east"
}
```

### Storage Volume
```json
{
  "type": "storage.Volume",
  "id": "volume-001",
  "name": "storage-vol-1",
  "account": "account-123",
  "data": {
    "size_gb": 1000,
    "replication_factor": 3
  }
}
```

---

## 🔄 Complete Collection Workflow

```
Step 1: Initialize
  └─► Core API: init() → return plugin metadata

Step 2: Verify
  └─► Core API: verify(secret) → test connection

Step 3: Collect Resources
  ├─► Get credentials from Secret API
  ├─► Connect to Nutanix REST API
  ├─► Fetch resources (VMs, clusters, volumes, networks)
  ├─► Normalize to CloudForet format
  └─► Inventory API: emit resources

Step 4: Calculate Costs
  ├─► For each VM resource
  ├─► Calculate CPU + Memory + Storage cost
  └─► Cost Analysis API: emit cost events

Step 5: Check for Alerts
  ├─► Fetch recent Nutanix events
  ├─► Create CloudForet alerts from events
  └─► Alert Manager API: emit alerts

Step 6: Store Configuration
  └─► Config API: save collection metadata

Step 7: Send Notifications
  └─► Notification API: notify about new resources

Step 8: Create Dashboards
  └─► Dashboard API: create visualizations

Result: Complete Nutanix infrastructure visible in CloudForet! ✅
```

---

## 🎯 Performance Targets

| Metric | Target | Typical |
|--------|--------|---------|
| Collection time for 100 VMs | < 5 min | 2-3 min |
| Cost calculation (per resource) | < 100 ms | 50 ms |
| API response time | < 500 ms | 200 ms |
| Memory usage | < 512 Mi | 256 Mi |
| CPU usage (idle) | < 100m | 50m |

---

## 📚 Code Templates Available

1. **InitPluginService** - Plugin registration and verification
2. **NutanixCollectorService** - Resource collection and normalization
3. **NutanixCostService** - Cost calculation and emission
4. **NutanixAlertService** - Alert creation
5. **NutanixNotificationService** - Notification handling
6. **NutanixMonitoringDataSourceService** - Metrics export
7. **NutanixConnector** - REST API client
8. **SecretHelper** - Credential management

All templates included in `nutanix_plugin_template.py`

---

## 🚀 Common Tasks Cheat Sheet

```python
# Task: Collect VMs
for batch in collector_service.collect({'secret': secret}):
    yield batch

# Task: Calculate cost
cost = cost_service.emit_cost_data(resource, options)

# Task: Create alert
alert = alert_service.create_alert(nutanix_event)

# Task: Send notification
notification = notification_service.notify_resource_change(resource, 'created', {})

# Task: Get VM metrics
metrics = monitoring_service.get_metrics({'resource_id': 'vm-001'})

# Task: Store config
config_service.save_plugin_config('key', {'value': 'data'})

# Task: Retrieve credentials
secret = secret_helper.get_secret('secret-id')
```

---

## 🎓 Next Steps

1. Review `cloudforet_nutanix_api_integration.md` for detailed explanations
2. Study `nutanix_plugin_template.py` for complete implementations
3. Run tests from `nutanix_plugin_testing_guide.md`
4. Customize for your Nutanix environment
5. Deploy to Kubernetes

Happy coding! 🚀

