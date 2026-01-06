# CloudForet Nutanix Plugin Development Guide
## Complete Reference with API Integration Examples

---

## 📚 Documentation Overview

This complete guide shows you how to develop, test, package, and deploy a Nutanix plugin for CloudForet, integrating with all major CloudForet APIs.

### Files Included:

1. **cloudforet_nutanix_api_integration.md** (57 KB)
   - Complete guide on all CloudForet APIs and how to use them
   - Covers 9 major APIs: Core, Inventory, Secret, Cost, Alert, Notification, Config, Identity, Monitoring, Dashboard
   - Detailed code examples for each API integration
   - API usage flowchart and summary table
   - Best practices for error handling and rate limiting

2. **nutanix_plugin_template.py** (28 KB)
   - Production-ready complete plugin template
   - All services fully implemented:
     - InitPluginService (Core API)
     - NutanixCollectorService (Inventory API)
     - NutanixCostService (Cost Analysis API)
     - NutanixAlertService (Alert Manager API)
     - NutanixNotificationService (Notification API)
     - NutanixMonitoringDataSourceService (Monitoring API)
     - NutanixConnector (REST API client)
   - Ready to use as starting point for your plugin

3. **nutanix_plugin_testing_guide.md** (20 KB)
   - Complete testing and validation guide
   - Unit tests for each API integration
   - Integration tests with local CloudForet instance
   - Load testing scripts
   - Kubernetes deployment validation
   - CI/CD pipeline examples (GitHub Actions)
   - Troubleshooting guide

---

## 🎯 Quick Start (5 Minutes)

### Step 1: Understand the Plugin Architecture

```
CloudForet Nutanix Plugin Structure:

┌─────────────────────────────────────────┐
│   gRPC Server (src/server.py)           │
│   - Listens on 0.0.0.0:50051            │
│   - Implements CloudForet interfaces    │
└─────────────────────────────────────────┘
           │
    ┌──────┼──────┐
    │      │      │
    ▼      ▼      ▼
┌──────┐┌──────┐┌──────┐
│Init  ││Collect││Cost  │  Services (Python classes)
│Svc   ││Svc    ││Svc   │  Implement CloudForet APIs
└──────┘└──────┘└──────┘
    │      │      │
    └──────┼──────┘
           │
    ┌──────▼───────┐
    │ Nutanix      │
    │ Connector    │  REST API client
    │ (REST API)   │  to Prism Central
    └──────────────┘
           │
    ┌──────▼───────────────────────┐
    │ Nutanix Prism Central API     │
    │ - VMs, Clusters, Storage, Net │
    └───────────────────────────────┘
```

### Step 2: Copy Template and Customize

```bash
# Use the provided template as starting point
cp nutanix_plugin_template.py plugin-nutanix-inven-collector/src/

# Customize for your Nutanix environment
vi src/connector/nutanix_connector.py
```

### Step 3: Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start plugin server
python src/server.py

# In another terminal, test it
grpcurl -plaintext localhost:50051 spaceone.core.v1.Plugin/init
```

---

## 🔌 API Integration Map

### 1. **Core API** - Plugin Registration
- **File**: cloudforet_nutanix_api_integration.md § 1
- **Code Template**: nutanix_plugin_template.py (InitPluginService)
- **What It Does**: Tells CloudForet about plugin capabilities
- **Key Methods**: `init()`, `verify()`

**Example Usage:**
```python
service = InitPluginService(transaction)
metadata = service.init({})  # Returns plugin info
service.verify({'secret': credentials})  # Verify credentials
```

### 2. **Inventory API** - Resource Collection
- **File**: cloudforet_nutanix_api_integration.md § 2
- **Code Template**: nutanix_plugin_template.py (NutanixCollectorService)
- **What It Does**: Collect VMs, clusters, volumes, networks
- **Key Methods**: `collect()`

**Example Usage:**
```python
service = NutanixCollectorService(transaction)
for batch in service.collect(params):
    # Batch contains normalized resources
    yield batch
```

### 3. **Secret API** - Credential Management
- **File**: cloudforet_nutanix_api_integration.md § 3
- **Code Template**: Integrated in collector service
- **What It Does**: Securely store/retrieve Nutanix credentials
- **Key Methods**: `UserSecret.create()`, `UserSecret.get_data()`

**Example Usage:**
```python
helper = SecretHelper(transaction)
secret = helper.get_secret('secret-id')  # Get decrypted credentials
```

### 4. **Cost Analysis API** - Cost Tracking
- **File**: cloudforet_nutanix_api_integration.md § 4
- **Code Template**: nutanix_plugin_template.py (NutanixCostService)
- **What It Does**: Calculate and emit VM costs
- **Key Methods**: `emit_cost_data()`

**Example Usage:**
```python
service = NutanixCostService(transaction)
cost = service.emit_cost_data(vm_resource, options)
# Returns: {'resource_id': 'vm-1', 'cost': 0.25, 'currency': 'USD'}
```

### 5. **Alert Manager API** - Event Alerts
- **File**: cloudforet_nutanix_api_integration.md § 5
- **Code Template**: nutanix_plugin_template.py (NutanixAlertService)
- **What It Does**: Create alerts from Nutanix events
- **Key Methods**: `Alert.create()`

**Example Usage:**
```python
service = NutanixAlertService(transaction)
alert = service.create_alert(nutanix_event)
# Returns alert ready to send to CloudForet
```

### 6. **Notification API** - Event Notifications
- **File**: cloudforet_nutanix_api_integration.md § 6
- **Code Template**: nutanix_plugin_template.py (NutanixNotificationService)
- **What It Does**: Send notifications on resource changes
- **Key Methods**: `Notification.create()`

**Example Usage:**
```python
service = NutanixNotificationService()
notif = service.notify_resource_change(resource, 'created', {})
```

### 7. **Config API** - Configuration Management
- **File**: cloudforet_nutanix_api_integration.md § 7
- **Code Template**: Reference in section 7.1
- **What It Does**: Store plugin settings, pricing models
- **Key Methods**: `SharedConfig.create()`, `SharedConfig.list()`

**Example Usage:**
```python
service = PluginConfigService(transaction)
service.save_pricing_model({
    'cpu_per_core_hour': 0.05,
    'memory_per_gb_hour': 0.01
})
```

### 8. **Identity API** - Access Control
- **File**: cloudforet_nutanix_api_integration.md § 8
- **Code Template**: Reference in section 8.1
- **What It Does**: Register endpoints, manage roles
- **Key Methods**: `Endpoint.create()`, `Role.create()`

**Example Usage:**
```python
service = PluginIdentityService(transaction)
service.register_plugin_endpoint('plugin-nutanix', 'grpc://plugin:50051')
```

### 9. **Monitoring API** - Performance Metrics
- **File**: cloudforet_nutanix_api_integration.md § 9
- **Code Template**: nutanix_plugin_template.py (NutanixMonitoringDataSourceService)
- **What It Does**: Export VM CPU, memory, network metrics
- **Key Methods**: `get_metrics()`, `get_supported_metrics()`

**Example Usage:**
```python
service = NutanixMonitoringDataSourceService(transaction)
metrics = service.get_metrics({
    'resource_id': 'vm-001',
    'metric_names': ['cpu_utilization', 'memory_utilization']
})
```

### 10. **Dashboard API** - Visualization
- **File**: cloudforet_nutanix_api_integration.md § 10
- **Code Template**: Reference in section 10.1
- **What It Does**: Create custom Nutanix dashboards
- **Key Methods**: `PublicDashboard.create()`, `PrivateDashboard.create()`

**Example Usage:**
```python
service = NutanixDashboardService(transaction)
dashboard = service.create_nutanix_overview_dashboard()
```

---

## 🧪 Testing Guide

See **nutanix_plugin_testing_guide.md** for:

### Unit Tests
- Test each API integration independently
- Mock Nutanix API responses
- Verify resource normalization
- Cost calculation validation

### Integration Tests
- Test with local CloudForet instance (Docker Compose)
- End-to-end collection workflow
- Kubernetes deployment validation

### Load Testing
- Concurrent collection performance
- Throughput measurement
- Memory usage monitoring

### CI/CD
- GitHub Actions pipeline
- Automated testing on PR
- Docker image building and pushing

---

## 📦 Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Kubernetes Cluster                      │
│                   (CloudForet namespace)                 │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────┐    ┌──────────────────────────┐   │
│  │ Nutanix Plugin   │    │   CloudForet Core        │   │
│  │ (Deployment)     │───▶│  (Inventory Service)     │   │
│  │                  │    │                          │   │
│  │ - Replicas: 2    │    │  - Handles resource      │   │
│  │ - Port: 50051    │    │    storage and querying  │   │
│  │ - Image: v1.0.0  │    └──────────────────────────┘   │
│  │                  │                                    │
│  │ ┌──────────────┐ │    ┌──────────────────────────┐   │
│  │ │Resource Limits   │    │   Other Services        │   │
│  │ │ CPU: 500m    │ │    │  - Secret Service       │   │
│  │ │ Mem: 512Mi   │ │    │  - Cost Analysis        │   │
│  │ └──────────────┘ │    │  - Alert Manager        │   │
│  │                  │    │  - Config Service       │   │
│  │ ┌──────────────┐ │    └──────────────────────────┘   │
│  │ │Health Checks │ │                                   │
│  │ │ - Liveness   │ │                                   │
│  │ │ - Readiness  │ │                                   │
│  │ └──────────────┘ │                                   │
│  └──────────────────┘                                   │
│           │                                             │
│           │ HTTPS (TLS)                                │
│           │                                             │
│  ┌────────▼───────────────┐                            │
│  │ Nutanix Prism Central   │                            │
│  │ (External)              │                            │
│  │ prism.company.com:9440  │                            │
│  └─────────────────────────┘                            │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Deployment Steps

### 1. Build Plugin

```bash
# Build Docker image
docker build -t myregistry.io/cloudforet/plugin-nutanix-inven-collector:1.0.0 .

# Push to registry
docker push myregistry.io/cloudforet/plugin-nutanix-inven-collector:1.0.0
```

### 2. Deploy with Helm

```bash
# Create values file
cat > values.yaml <<EOF
image:
  repository: myregistry.io/cloudforet/plugin-nutanix-inven-collector
  tag: "1.0.0"
replicaCount: 2
EOF

# Deploy
helm install nutanix-plugin ./charts/plugin-nutanix-inven-collector \
  -n cloudforet -f values.yaml
```

### 3. Register in CloudForet

```bash
# Add secret with Nutanix credentials
spacectl create secret nutanix_prod \
  --data '{"host":"prism.company.com","username":"admin","password":"secret"}'

# Plugin automatically registered and ready to use
```

---

## 🔍 Key Concepts

### Resource Normalization
Nutanix APIs return data in Nutanix format. The plugin normalizes this to CloudForet's standard format:

```python
# Nutanix response
{
  'spec': {
    'name': 'prod-web-01',
    'resources': {'memory_size_mib': 8192}
  }
}

# Normalized to CloudForet
{
  'type': 'compute.Instance',
  'name': 'prod-web-01',
  'data': {'memory_gb': 8.0}
}
```

### Batching
Large collections are split into batches for efficiency:

```python
# Plugin yields resources in batches
for batch in collector.collect(params):
    # Batch typically contains 100 resources
    yield batch
```

### Multi-Tenancy
Support multiple Nutanix clusters/accounts:

```python
# Secret can reference multiple clusters
secret = {
    'account_id': 'company-a',
    'clusters': [
        {'host': 'prism1.company.com'},
        {'host': 'prism2.company.com'}
    ]
}
```

---

## 📊 Example: Complete Workflow

Here's how all APIs work together in a real scenario:

```
1. User adds Nutanix account in CloudForet Console
   └─► Credentials stored via Secret API

2. User clicks "Collect" in Inventory
   └─► Core API calls plugin.init()
   └─► Core API calls plugin.verify(secret)
   └─► Inventory API calls Collector.collect()

3. Collector Service (Our Plugin)
   ├─► Fetch credentials from Secret API
   ├─► Connect to Nutanix via REST API
   ├─► Fetch all VMs, clusters, volumes, networks
   ├─► Normalize resources
   ├─► Emit resources to Inventory API
   ├─► Calculate costs → Cost Analysis API
   └─► Check for events → Alert Manager API

4. Notifications & Dashboards
   ├─► Send notifications via Notification API
   └─► Create dashboard via Dashboard API

5. User sees Nutanix resources in CloudForet console
   └─► Can manage, cost-track, alert, and visualize
```

---

## 💡 Common Patterns

### Pattern 1: Retrying Failed API Calls

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2))
def fetch_vms():
    return connector.list_vms()
```

### Pattern 2: Streaming Large Results

```python
def collect(self, params):
    for batch in self._collect_batches():
        yield batch  # Stream results instead of loading all in memory
```

### Pattern 3: Error Handling

```python
try:
    connector.test_connection()
except requests.ConnectionError:
    raise ERROR_INVALID_CREDENTIALS()
```

---

## ❓ FAQ

**Q: What CloudForet version does this support?**
A: CloudForet v1.12+. Check API compatibility for older versions.

**Q: Can I collect from multiple Nutanix clusters?**
A: Yes, configure multiple secrets or use cluster array in single secret.

**Q: How often should I collect?**
A: Default is hourly. Customize via `collection_schedule` config.

**Q: What happens if collection fails?**
A: Plugin retries automatically with exponential backoff.

**Q: How do I debug the plugin?**
A: Set `LOG_LEVEL=DEBUG` and check plugin logs in Kubernetes.

**Q: Can I extend the plugin for other Nutanix services?**
A: Yes, follow the same pattern for other resource types.

---

## 📞 Support & Resources

- **CloudForet Docs**: https://cloudforet.io/docs/
- **CloudForet API Docs**: https://cloudforet.io/api-doc/
- **Nutanix API Docs**: https://developer.nutanix.com/
- **Plugin Examples**: https://github.com/cloudforet-io/

---

## 🎓 Learning Path

1. **Beginner**: Read this overview + cloudforet_nutanix_api_integration.md § 1-2
2. **Intermediate**: Study nutanix_plugin_template.py + all API sections
3. **Advanced**: Implement custom features from template
4. **Expert**: Deploy to production + optimize performance

---

## ✅ Before Production Checklist

- [ ] All unit tests passing
- [ ] Integration tests with CloudForet instance
- [ ] Load testing completed
- [ ] Documentation updated
- [ ] Security review (no hardcoded secrets)
- [ ] Error handling for all failure cases
- [ ] Helm chart validated
- [ ] Docker image published to registry
- [ ] Kubernetes manifests reviewed
- [ ] Monitoring/alerting configured

---

## 📝 Summary

This comprehensive guide provides everything needed to:
- ✅ Understand CloudForet plugin architecture
- ✅ Integrate with all major CloudForet APIs
- ✅ Build a production-ready Nutanix collector
- ✅ Test and deploy to Kubernetes
- ✅ Monitor and troubleshoot in production

Happy plugin development! 🚀

