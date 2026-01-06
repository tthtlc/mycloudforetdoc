# Nutanix Inventory Collector Plugin for CloudForet

A production-ready CloudForet plugin for discovering and collecting Nutanix infrastructure resources (VMs, disks, networks) and integrating them with CloudForet's inventory, cost analysis, monitoring, and notification systems.

## Features

✅ **Multi-Cluster Support** - Collect resources from multiple Nutanix clusters  
✅ **Full API Integration** - Uses all 7 CloudForet APIs (Identity, Inventory, Cost, Monitoring, Notification, Repository)  
✅ **Cost Tracking** - Automatic cost extraction and reporting  
✅ **Performance Metrics** - CPU, memory, disk, and network metrics collection  
✅ **Error Handling** - Comprehensive retry logic and error recovery  
✅ **Production Ready** - Kubernetes-native, fully tested, and monitored  

## Architecture

```
┌────────────────────────────────────────┐
│     Nutanix Prism Central API          │
└────────────┬─────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│   Nutanix Collector Plugin (gRPC)     │
│  ┌──────────────────────────────────┐ │
│  │ Connector Layer                  │ │
│  │ ├─ NutanixConnector              │ │
│  │ ├─ IdentityConnector (Auth)      │ │
│  │ ├─ InventoryConnector (Jobs)     │ │
│  │ ├─ CostConnector (Billing)       │ │
│  │ ├─ MonitoringConnector (Metrics) │ │
│  │ ├─ NotificationConnector (Alerts)│ │
│  │ └─ RepositoryConnector (Metadata)│ │
│  └──────────────────────────────────┘ │
│  ┌──────────────────────────────────┐ │
│  │ Service Layer                    │ │
│  │ ├─ CollectorService              │ │
│  │ └─ InitService                   │ │
│  └──────────────────────────────────┘ │
└────────────┬─────────────────────────┘
             │
      ┌──────┼──────┬──────────┬────────┐
      ▼      ▼      ▼          ▼        ▼
  Identity Inventory Cost  Monitoring Notification
   Service  Service   Service Service   Service
```

## Directory Structure

```
plugin-nutanix-inven-collector/
├── src/
│   ├── server.py                          # Main gRPC server
│   ├── connector/
│   │   ├── identity_connector.py          # Auth & secrets
│   │   ├── inventory_connector.py         # Job & resource management
│   │   ├── nutanix_connector.py          # Nutanix API integration
│   │   └── other_connectors.py           # Cost, Monitoring, Notification, Repository
│   ├── service/
│   │   ├── init_service.py               # Plugin initialization
│   │   └── collector_service.py          # Main collection orchestration
│   └── tests/
│       ├── unit/
│       │   └── test_connectors.py
│       └── integration/
│           └── test_workflow.py
├── charts/
│   └── plugin-nutanix/                   # Helm chart
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── _helpers.tpl
│           ├── deployment.yaml
│           └── resources.yaml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Installation

### Prerequisites

- Kubernetes 1.20+
- CloudForet 1.12+
- Helm 3.0+
- Nutanix Prism Central 2020.5+

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/cloudforet-io/plugin-nutanix-inven-collector.git
cd plugin-nutanix-inven-collector

# 2. Build Docker image
docker build -t myregistry.io/cloudforet/plugin-nutanix-inven-collector:1.0.0 .

# 3. Push to registry
docker push myregistry.io/cloudforet/plugin-nutanix-inven-collector:1.0.0

# 4. Deploy to Kubernetes
helm install nutanix-plugin ./charts/plugin-nutanix \
  --namespace cloudforet \
  --set-string secrets.pluginApiKey='<your-api-key>' \
  --set image.repository=myregistry.io/cloudforet/plugin-nutanix-inven-collector \
  --set image.tag=1.0.0

# 5. Verify deployment
kubectl get pods -n cloudforet -l app.kubernetes.io/name=plugin-nutanix-inven-collector
```

## Configuration

### Environment Variables

```bash
# API Endpoints
IDENTITY_ENDPOINT=grpc://identity:50051
INVENTORY_ENDPOINT=grpc://inventory:50051
REPOSITORY_ENDPOINT=grpc://repository:50051
COST_ENDPOINT=grpc://cost-analysis:50051
MONITORING_ENDPOINT=grpc://monitoring:50051
NOTIFICATION_ENDPOINT=grpc://notification:50051

# CloudForet Configuration
DOMAIN_ID=domain-default
WORKSPACE_ID=workspace-default
PLUGIN_API_KEY=<plugin-service-account-key>

# Logging
LOG_LEVEL=INFO
ENABLE_STRUCTURED_LOGS=true
PLUGIN_PORT=50051
```

### Nutanix Credentials

Credentials are provided via CloudForet's Secret Manager. When registering a Nutanix collector in CloudForet, provide:

```json
{
  "nutanix_host": "prism.nutanix.local",
  "nutanix_port": 9440,
  "nutanix_username": "admin",
  "nutanix_password": "password",
  "verify_ssl": true
}
```

## Usage

### Register Plugin

1. Go to CloudForet Console → Inventory → Plugin
2. Click "Register Plugin"
3. Select "Nutanix Inventory Collector"
4. Fill in Nutanix Prism Central credentials
5. Click "Register"

### Create Collector

1. Go to Inventory → Collector
2. Click "Create Collector"
3. Select "Nutanix Inventory Collector" plugin
4. Choose service accounts
5. Set schedule (daily, hourly)
6. Click "Create"

### View Resources

- Go to Inventory → Cloud Service
- Filter by provider="nutanix"
- View collected VMs, disks, networks

## API Integration

The plugin integrates with 7 CloudForet APIs:

### 1. Identity API
- **Purpose**: Authenticate plugin, fetch encrypted credentials
- **Methods**: Auth.login, Secret.get
- **Usage**: Called at startup and during collection

### 2. Inventory API
- **Purpose**: Manage collection jobs and store resources
- **Methods**: Job.create, JobTask.create, JobTask.update, CloudService.create
- **Usage**: Central to collection workflow

### 3. Cost Analysis API
- **Purpose**: Track Nutanix infrastructure costs
- **Methods**: Cost.create
- **Usage**: Push cost metrics extracted from resources

### 4. Monitoring API
- **Purpose**: Collect performance metrics
- **Methods**: MetricData.create, Metric.list
- **Usage**: Push CPU, memory, disk, network metrics

### 5. Notification API
- **Purpose**: Send alerts and notifications
- **Methods**: Notification.create
- **Usage**: Completion and error notifications

### 6. Repository API
- **Purpose**: Register plugin metadata
- **Methods**: Plugin.register, Schema.publish
- **Usage**: Plugin discovery and schema validation

### 7. gRPC Plugin Interface
- **Purpose**: CloudForet calls plugin methods
- **Methods**: Collector.init, Collector.collect, Collector.verify
- **Usage**: Entry points for plugin functionality

## Development

### Setup Development Environment

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run tests
pytest src/tests/ -v

# 4. Run linting
flake8 src/
black src/ --check
```

### Running Locally

```bash
# 1. Set environment variables
export PLUGIN_API_KEY='dev-key'
export LOG_LEVEL=DEBUG

# 2. Start plugin
python src/server.py

# 3. Plugin starts on localhost:50051
```

### Running Tests

```bash
# Unit tests
pytest src/tests/unit/ -v

# Integration tests (requires CloudForet running)
pytest src/tests/integration/ -v

# With coverage
pytest src/tests/ --cov=src/
```

## Monitoring

### Metrics Exported

- `plugin_collection_duration_seconds` - Collection duration
- `plugin_resources_collected_total` - Total resources collected
- `plugin_errors_total` - Total collection errors
- `plugin_api_calls_total` - Total API calls made

### Logging

Structured JSON logging is used for all operations:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "collector_service",
  "message": "Collection started",
  "job_id": "job-12345",
  "collector_id": "collector-nutanix-001"
}
```

### Health Checks

```bash
# Check pod health
kubectl get pods -n cloudforet

# Check logs
kubectl logs -n cloudforet -l app.kubernetes.io/name=plugin-nutanix-inven-collector

# Port forward for testing
kubectl port-forward -n cloudforet svc/plugin-nutanix-inven-collector 50051:50051
```

## Troubleshooting

### Issue: "Plugin not found in registry"

```bash
# Solution: Check plugin registration
kubectl logs -n cloudforet <pod-name> | grep "registered"

# Verify Docker image is accessible
docker pull <registry>/plugin-nutanix-inven-collector:1.0.0
```

### Issue: "Failed to connect to Nutanix"

```bash
# Check connectivity
kubectl exec -it <pod-name> -n cloudforet -- \
  curl -k https://<nutanix-host>:9440/api/nutanix/v3/clusters

# Verify credentials
kubectl get secret plugin-nutanix -n cloudforet -o yaml
```

### Issue: "Job stuck in CREATED state"

```bash
# Check job task logs
kubectl logs -n cloudforet <pod-name> | grep "job_task_id"

# Verify service account permissions
kubectl get serviceaccount plugin-nutanix -n cloudforet -o yaml
```

### Issue: "Out of memory errors"

```bash
# Increase resource limits in values.yaml
resources:
  limits:
    memory: 1Gi  # Increased from 512Mi

# Redeploy
helm upgrade nutanix-plugin ./charts/plugin-nutanix -n cloudforet -f values.yaml
```

## Performance Tuning

### Batch Size Optimization

```yaml
# Increase batch size for faster collection
resources:
  requests:
    memory: 512Mi
  limits:
    memory: 1Gi

# Adjust in collector
options:
  batch_size: 100
  parallel_tasks: 4
```

### Connection Pooling

The plugin uses connection pooling to optimize API calls:

```python
# Configured in nutanix_connector.py
limits=httpx.Limits(
    max_connections=10,
    max_keepalive_connections=5
)
```

### Incremental Collection

Enable incremental collection to reduce API calls:

```python
# Modified in collector_service.py
resources = query_resources(modified_after=last_sync_time)
```

## Security Best Practices

1. **Never log credentials**: Credentials are redacted from logs
2. **SSL/TLS validation**: Enabled by default (verify_ssl=true)
3. **Service accounts**: Minimal RBAC permissions assigned
4. **Secrets encryption**: All secrets encrypted in CloudForet
5. **Network policies**: Restrict traffic to necessary endpoints

## Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

## License

Apache License 2.0

## Support

- **Issues**: https://github.com/cloudforet-io/plugin-nutanix-inven-collector/issues
- **Discussions**: https://github.com/cloudforet-io/plugin-nutanix-inven-collector/discussions
- **Slack**: [CloudForet Community](https://cloudforet-io.slack.com)

## Changelog

### v1.0.0 (2024-01-15)
- Initial release
- Support for VM, disk, and network discovery
- Full 7-API integration
- Kubernetes/Helm deployment
- Comprehensive testing

---

**Last Updated**: January 15, 2024  
**Maintained By**: CloudForet Contributors
