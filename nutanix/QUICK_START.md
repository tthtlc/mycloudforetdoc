# Quick Start Guide

Get the Nutanix Collector Plugin running in 5 minutes.

## 30-Second Overview

This is a production-ready **CloudForet plugin** that:
- Discovers Nutanix VMs, disks, networks
- Integrates with CloudForet's inventory, cost, monitoring systems
- Runs on Kubernetes with Helm
- Uses all 7 CloudForet APIs

## Prerequisites

```bash
# Check prerequisites
which docker      # Docker installed?
which kubectl     # Kubernetes access?
which helm        # Helm installed?

# If missing:
# - Docker: https://docs.docker.com/get-docker/
# - kubectl: https://kubernetes.io/docs/tasks/tools/
# - Helm: https://helm.sh/docs/intro/install/
```

## 5-Minute Setup

### 1. Get Source Code

```bash
cd /path/to/plugin-nutanix-inven-collector
```

### 2. Build Container

```bash
# Build Docker image
docker build -t myregistry.io/cloudforet/plugin-nutanix:1.0.0 .

# Push to registry
docker push myregistry.io/cloudforet/plugin-nutanix:1.0.0
```

### 3. Deploy to Kubernetes

```bash
# Deploy with Helm
helm install nutanix-plugin ./charts/plugin-nutanix \
  -n cloudforet \
  --set image.repository=myregistry.io/cloudforet/plugin-nutanix \
  --set image.tag=1.0.0 \
  --set-string secrets.pluginApiKey='your-api-key'

# Verify deployment
kubectl get pods -n cloudforet -l app.kubernetes.io/name=plugin-nutanix-inven-collector
```

### 4. Register in CloudForet

1. Go to CloudForet Console → Inventory → Plugin
2. Click **Register Plugin**
3. Select **Nutanix Inventory Collector**
4. Add Nutanix credentials (host, username, password)
5. Click **Create**

### 5. Collect Resources

1. Go to Inventory → Collector → Your Nutanix Collector
2. Click **Collect Now**
3. Wait for completion (2-5 minutes depending on resource count)
4. View resources in Inventory → Cloud Service

## Common Commands

```bash
# Development
make install        # Install dependencies
make test          # Run tests
make lint          # Check code quality

# Container
make build         # Build Docker image
make push          # Push to registry

# Deployment
make deploy        # Deploy to Kubernetes
make logs          # View logs
make restart       # Restart pods
make delete        # Remove from Kubernetes

# Troubleshooting
make status        # Check pod status
make describe      # Describe pods
make port-forward  # Enable local access
```

## Architecture

```
Nutanix           Plugin            CloudForet
Cluster           (gRPC)            Services
   │                 │                  │
   ├─ VMs ──────────>│ ◆ Collect       │
   ├─ Disks         │ ◆ Normalize      ├─ Identity
   └─ Networks      │ ◆ Push           ├─ Inventory ◄── Resources
                    │                  ├─ Cost
                    │ ◆ Cost Extract   ├─ Monitoring ◄── Metrics
                    │ ◆ Push           ├─ Notification
                    │ ◆ Alert          └─ Repository
```

## File Structure

```
├── src/                          # Source code
│   ├── server.py                # Main gRPC server
│   ├── connector/               # API connectors
│   │   ├── identity_connector.py
│   │   ├── inventory_connector.py
│   │   ├── nutanix_connector.py
│   │   └── other_connectors.py
│   ├── service/                 # Business logic
│   │   ├── init_service.py
│   │   └── collector_service.py
│   └── tests/                   # Tests
│       ├── unit/
│       └── integration/
├── charts/                       # Kubernetes/Helm
│   └── plugin-nutanix/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
├── Dockerfile                    # Container image
├── requirements.txt              # Python deps
├── Makefile                      # Tasks
└── README.md                     # Documentation
```

## Integration Points

| API | Purpose | Used For |
|-----|---------|----------|
| **Identity** | Auth, Secrets | Get encrypted Nutanix credentials |
| **Inventory** | Jobs, Resources | Store VMs/disks in CloudForet |
| **Cost Analysis** | Cost Data | Track infrastructure costs |
| **Monitoring** | Metrics | CPU/memory/disk/network metrics |
| **Notification** | Alerts | Completion/error notifications |
| **Repository** | Metadata | Plugin registration |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Pod won't start | Check logs: `make logs` |
| Can't reach Nutanix | Verify network connectivity |
| Collection fails | Check credentials, test connection |
| High memory | Increase limits in values.yaml |
| gRPC error | Port-forward: `make port-forward` |

See [INSTALLATION.md](INSTALLATION.md) for detailed troubleshooting.

## Next Steps

1. **Read [README.md](README.md)** - Full documentation
2. **Check [INSTALLATION.md](INSTALLATION.md)** - Step-by-step guide
3. **Review [docs/](docs/)** - API integration details
4. **Explore code** - Start with `src/server.py`

## API Documentation

Comprehensive guides are in the `docs/` folder:

- `cloudforet_api_plugin_guide.md` - API overview
- `cloudforet_api_implementations.md` - Production code examples
- `cloudforet_api_responses_errors.md` - Request/response formats

## Support

- **Issues**: GitHub Issues
- **Questions**: GitHub Discussions
- **Chat**: CloudForet Slack Community
- **Docs**: https://spaceone.org/docs/

## Example Collection Flow

```
User clicks "Collect Now" in CloudForet Console
           ↓
Plugin receives request
           ↓
1. Identity API: Fetch Nutanix credentials
           ↓
2. Nutanix API: Query VMs/disks/networks
           ↓
3. Normalize to CloudForet format
           ↓
4. Inventory API: Store resources
           ↓
5. Cost Analysis: Extract & store costs
           ↓
6. Monitoring: Push performance metrics
           ↓
7. Notification: Send completion alert
           ↓
Dashboard shows 450 new resources!
```

## Production Checklist

- [ ] Tests passing (make test)
- [ ] Code linting (make lint)
- [ ] Container builds (make build)
- [ ] Helm chart validated
- [ ] Credentials secured
- [ ] Resource limits set
- [ ] Monitoring enabled
- [ ] Logging configured
- [ ] Disaster recovery plan

---

**Ready to go!** Start with `make help` to see all available commands.
