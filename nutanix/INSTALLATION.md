# Installation & Deployment Guide

Complete step-by-step guide for deploying the Nutanix Collector Plugin to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Building Docker Image](#building-docker-image)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Plugin Registration](#plugin-registration)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **Kubernetes**: 1.20 or later
- **Helm**: 3.0 or later
- **Docker**: 20.10 or later
- **Python**: 3.9 or later (for local development)

### CloudForet Requirements

- **CloudForet**: 1.12 or later (installed and running)
- **Core Services**: Identity, Inventory, Repository, Cost Analysis, Monitoring, Notification
- **Network**: Plugin must be able to reach CloudForet services

### Nutanix Requirements

- **Prism Central**: 2020.5 or later
- **Admin Credentials**: API user with VM discovery permissions
- **Network**: Plugin must be able to reach Prism Central on port 9440

### Software Installation

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Verify installations
kubectl version --client
helm version
docker --version
```

---

## Local Development Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/cloudforet-io/plugin-nutanix-inven-collector.git
cd plugin-nutanix-inven-collector
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Verify Python version
python --version  # Should be 3.9+
```

### Step 3: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep spaceone
```

### Step 4: Run Tests

```bash
# Run unit tests
pytest src/tests/unit/ -v

# Run with coverage
pytest src/tests/ --cov=src/ --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Step 5: Code Linting

```bash
# Check code quality
make lint

# Format code
make format
```

### Step 6: Run Locally

```bash
# Set environment variables
export PLUGIN_API_KEY='dev-api-key'
export LOG_LEVEL=DEBUG

# Start plugin
python src/server.py

# Expected output:
# INFO:__main__:Plugin initialized with log level: DEBUG
# INFO:__main__:Initializing plugin services...
# INFO:__main__:Plugin services initialized successfully
# INFO:__main__:✅ Plugin server started on port 50051
```

---

## Building Docker Image

### Step 1: Configure Registry

```bash
# Set your Docker registry
export REGISTRY=myregistry.io/cloudforet
export IMAGE_NAME=plugin-nutanix-inven-collector
export VERSION=1.0.0

# Verify variables
echo $REGISTRY/$IMAGE_NAME:$VERSION
```

### Step 2: Build Image

```bash
# Option 1: Using make
make build

# Option 2: Using docker directly
docker build -t $REGISTRY/$IMAGE_NAME:$VERSION .

# Verify build
docker images | grep nutanix
```

### Step 3: Test Image Locally

```bash
# Run container locally
docker run -it \
  -e PLUGIN_API_KEY='test-key' \
  -e LOG_LEVEL=DEBUG \
  -p 50051:50051 \
  $REGISTRY/$IMAGE_NAME:$VERSION

# Test connection
grpcurl -plaintext localhost:50051 list

# Expected output:
# spaceone.core.plugin.Plugin
# spaceone.inventory.plugin.collector.Collector
```

### Step 4: Push to Registry

```bash
# Login to Docker registry
docker login $REGISTRY

# Push image
make push

# Or manually
docker push $REGISTRY/$IMAGE_NAME:$VERSION

# Verify push
docker pull $REGISTRY/$IMAGE_NAME:$VERSION
```

---

## Kubernetes Deployment

### Step 1: Create Namespace

```bash
# Create CloudForet namespace if it doesn't exist
kubectl create namespace cloudforet

# Verify namespace
kubectl get namespace | grep cloudforet
```

### Step 2: Create API Key Secret

```bash
# Generate API key for plugin service account
# (Must be done in CloudForet console)

# Store API key in environment variable
export PLUGIN_API_KEY='your-plugin-service-account-key'

# Verify key is set
echo $PLUGIN_API_KEY
```

### Step 3: Deploy with Helm

```bash
# Option 1: Using make
make deploy \
  REGISTRY=$REGISTRY \
  VERSION=$VERSION \
  NAMESPACE=cloudforet

# Option 2: Using Helm directly
helm install nutanix-plugin ./charts/plugin-nutanix \
  --namespace cloudforet \
  --set image.repository=$REGISTRY/$IMAGE_NAME \
  --set image.tag=$VERSION \
  --set-string secrets.pluginApiKey=$PLUGIN_API_KEY \
  --set apiEndpoints.identity=grpc://identity:50051 \
  --set apiEndpoints.inventory=grpc://inventory:50051

# Verify deployment
kubectl get deployment -n cloudforet -l app.kubernetes.io/name=plugin-nutanix-inven-collector
```

### Step 4: Monitor Deployment

```bash
# Watch pod startup
kubectl get pods -n cloudforet -l app.kubernetes.io/name=plugin-nutanix-inven-collector -w

# View logs
kubectl logs -n cloudforet -l app.kubernetes.io/name=plugin-nutanix-inven-collector -f

# Check pod status
kubectl describe pod -n cloudforet \
  -l app.kubernetes.io/name=plugin-nutanix-inven-collector
```

### Step 5: Verify Service

```bash
# Check service is running
kubectl get svc -n cloudforet -l app.kubernetes.io/name=plugin-nutanix-inven-collector

# Port forward for testing
kubectl port-forward -n cloudforet \
  svc/plugin-nutanix-inven-collector 50051:50051

# Test gRPC connection
grpcurl -plaintext localhost:50051 list
```

---

## Plugin Registration

### Step 1: Access CloudForet Console

```bash
# Port forward console API (if needed)
kubectl port-forward -n cloudforet svc/console-api-v2-rest 8082:80

# Open browser
open http://localhost:8082
# Or: http://your-cloudforet-instance
```

### Step 2: Register Plugin

1. Login to CloudForet Console
2. Navigate to **Inventory** → **Plugin** → **Plugin**
3. Click **Register Plugin**
4. Fill in details:
   - **Name**: Nutanix Inventory Collector
   - **Service Type**: inventory.Collector
   - **Provider**: nutanix
   - **Image URL**: `$REGISTRY/$IMAGE_NAME:$VERSION`
   - **Image Type**: Docker Hub
5. Click **Register**

### Step 3: Create Service Account

1. Navigate to **Identity** → **Service Account**
2. Click **Create Service Account**
3. Fill in details:
   - **Name**: nutanix-collector-account
   - **Type**: Collector
   - **Role**: Collector Admin (or custom role)
4. Click **Create**

### Step 4: Create Collector

1. Navigate to **Inventory** → **Collector**
2. Click **Create Collector**
3. Fill in details:
   - **Collector**: Nutanix Inventory Collector
   - **Service Account**: nutanix-collector-account
   - **Name**: Nutanix Production (or custom name)
4. Click **Next**

### Step 5: Add Nutanix Credentials

1. In **Service Account**, click **Add**
2. Fill in Nutanix credentials:
   - **Nutanix Host**: prism.nutanix.local
   - **Port**: 9440
   - **Username**: admin
   - **Password**: [password]
   - **Verify SSL**: ✓
3. Click **Verify** to test connection
4. Click **Save**

### Step 6: Configure Schedule

1. Set collection schedule:
   - **Type**: Daily
   - **Time**: 02:00 UTC (off-peak)
   - **Timezone**: UTC
2. Optional: Enable **Auto Upgrade** for plugin updates
3. Click **Create**

---

## Verification

### Step 1: Check Pods

```bash
# Verify plugin pod is running
kubectl get pods -n cloudforet -l app.kubernetes.io/name=plugin-nutanix-inven-collector

# Expected output:
# NAME                                                READY   STATUS    RESTARTS   AGE
# plugin-nutanix-inven-collector-abc123def456-xyz    1/1     Running   0          2m
```

### Step 2: Check Logs

```bash
# View plugin logs
kubectl logs -n cloudforet \
  -l app.kubernetes.io/name=plugin-nutanix-inven-collector

# Expected log messages:
# - Plugin initialized with log level: INFO
# - Plugin services initialized successfully
# - ✅ Plugin server started on port 50051
```

### Step 3: Test Collection

1. In CloudForet Console, go to **Inventory** → **Collector**
2. Click on your Nutanix collector
3. Click **Collect Now**
4. Monitor collection progress in **Jobs** section
5. View collected resources in **Cloud Service**

### Step 4: Verify Resources

```bash
# Query resources via API (if kubectl port-forward is active)
grpcurl -plaintext \
  -d '{"query":{"filter":[{"k":"provider","v":"nutanix","o":"eq"}]}}' \
  localhost:50051 \
  inventory.v1.CloudService.list
```

### Step 5: Check Metrics

```bash
# View Prometheus metrics (if Prometheus is deployed)
kubectl port-forward -n cloudforet svc/prometheus 9090:9090

# Visit http://localhost:9090
# Query: plugin_resources_collected_total{provider="nutanix"}
```

---

## Troubleshooting

### Issue: Pod won't start

```bash
# Check pod events
kubectl describe pod -n cloudforet \
  -l app.kubernetes.io/name=plugin-nutanix-inven-collector

# Common causes:
# - Image not found: Check image repository and tag
# - Insufficient resources: Increase resource limits
# - API key not set: Check secret creation

# View detailed logs
kubectl logs -n cloudforet \
  -l app.kubernetes.io/name=plugin-nutanix-inven-collector \
  --previous  # Previous pod if it crashed
```

### Issue: Collection fails

```bash
# Check collection job logs
kubectl logs -n cloudforet \
  -l app.kubernetes.io/name=plugin-nutanix-inven-collector \
  | grep -i "collection\|error"

# Common causes:
# - Cannot connect to Nutanix
# - Invalid credentials
# - Nutanix API error

# Test Nutanix connectivity
kubectl exec -it <pod-name> -n cloudforet -- \
  curl -k https://<nutanix-host>:9440/api/nutanix/v3/clusters
```

### Issue: High memory usage

```bash
# Check resource usage
kubectl top pods -n cloudforet \
  -l app.kubernetes.io/name=plugin-nutanix-inven-collector

# Increase resource limits in values.yaml
resources:
  limits:
    memory: 1Gi  # Increase from 512Mi

# Redeploy
helm upgrade nutanix-plugin ./charts/plugin-nutanix \
  -n cloudforet -f charts/plugin-nutanix/values.yaml
```

### Issue: gRPC connection refused

```bash
# Verify service is running
kubectl get svc -n cloudforet \
  -l app.kubernetes.io/name=plugin-nutanix-inven-collector

# Check network policies
kubectl get networkpolicies -n cloudforet

# Test DNS resolution
kubectl exec -it <pod-name> -n cloudforet -- \
  nslookup plugin-nutanix-inven-collector.cloudforet.svc.cluster.local
```

---

## Next Steps

1. **Monitor Collection**: Set up dashboards to monitor collection metrics
2. **Configure Alerts**: Set up notifications for collection failures
3. **Optimize Performance**: Tune resource limits based on environment
4. **Add More Clusters**: Register additional Nutanix clusters
5. **Enable Cost Analysis**: Start tracking Nutanix infrastructure costs

For more details, see [README.md](README.md).
