# Nutanix Plugin Testing & Integration Guide

## Quick Reference: API Integration Testing

This guide shows how to test and validate each CloudForet API integration in your Nutanix plugin.

---

## 1. LOCAL DEVELOPMENT & TESTING

### 1.1 Setup Local Development Environment

```bash
# Clone plugin repository
git clone https://github.com/yourorg/plugin-nutanix-inven-collector.git
cd plugin-nutanix-inven-collector

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio

# Set environment variables
export CLOUDFORET_API_KEY=your_api_key
export NUTANIX_HOST=prism.company.com
export NUTANIX_USERNAME=admin
export NUTANIX_PASSWORD=password
```

### 1.2 Run Plugin Locally

```bash
# Start gRPC server
python src/server.py

# In another terminal, test with grpcurl
grpcurl -plaintext localhost:50051 list
grpcurl -plaintext localhost:50051 spaceone.core.v1.Plugin/init
```

---

## 2. UNIT TESTS FOR API INTEGRATION

### 2.1 Test Core API (Plugin Initialization)

```python
# src/tests/test_init_service.py

import pytest
from unittest.mock import MagicMock, patch
from src.service.init_service import InitPluginService

class TestInitPluginService:
    
    @pytest.fixture
    def mock_transaction(self):
        transaction = MagicMock()
        transaction.get_meta.return_value = {
            'transaction_id': 'txn-123'
        }
        return transaction
    
    def test_init_returns_metadata(self, mock_transaction):
        """Test that init() returns plugin metadata."""
        service = InitPluginService(mock_transaction)
        result = service.init({})
        
        assert result['metadata']['service_name'] == 'plugin-nutanix-inven-collector'
        assert result['metadata']['service_type'] == 'inventory.Collector'
        assert result['metadata']['provider'] == 'nutanix'
    
    @patch('src.connector.nutanix_connector.NutanixConnector')
    def test_verify_success(self, mock_connector_class, mock_transaction):
        """Test that verify() succeeds with valid credentials."""
        mock_connector = MagicMock()
        mock_connector.test_connection.return_value = True
        mock_connector_class.return_value = mock_connector
        
        service = InitPluginService(mock_transaction)
        secret = {
            'host': 'prism.local',
            'username': 'admin',
            'password': 'secret'
        }
        
        result = service.verify({'secret': secret})
        
        assert result['status'] == 'success'
        mock_connector.test_connection.assert_called_once()
    
    def test_verify_missing_credentials(self, mock_transaction):
        """Test that verify() fails with missing credentials."""
        from spaceone.core.error import ERROR_INVALID_PARAMETER
        
        service = InitPluginService(mock_transaction)
        secret = {'host': 'prism.local'}  # Missing username and password
        
        with pytest.raises(ERROR_INVALID_PARAMETER):
            service.verify({'secret': secret})
```

### 2.2 Test Inventory API (Resource Collection)

```python
# src/tests/test_collector_service.py

import pytest
from unittest.mock import MagicMock, patch
from src.service.collector_service import NutanixCollectorService
from datetime import datetime

class TestNutanixCollectorService:
    
    @pytest.fixture
    def mock_connector(self):
        connector = MagicMock()
        connector.list_vms.return_value = [
            {
                'metadata': {'uuid': 'vm-001', 'creation_time': '2024-01-01T00:00:00Z'},
                'spec': {
                    'name': 'test-vm-1',
                    'resources': {
                        'power_state': 'ON',
                        'num_sockets': 2,
                        'num_vcpus_per_socket': 2,
                        'memory_size_mib': 8192,
                        'nic_list': [{}, {}]
                    },
                    'cluster_reference': {'name': 'cluster-1'}
                }
            }
        ]
        connector.list_clusters.return_value = []
        connector.list_volumes.return_value = []
        connector.list_networks.return_value = []
        return connector
    
    @patch('src.connector.nutanix_connector.NutanixConnector')
    def test_collect_vms(self, mock_connector_class, mock_connector):
        """Test that collect() returns VMs in CloudForet format."""
        mock_connector_class.return_value = mock_connector
        
        service = NutanixCollectorService(MagicMock())
        secret = {'host': 'prism.local', 'account_id': 'account-1', 'region': 'us-east'}
        
        params = {
            'secret': secret,
            'options': {'batch_size': 100},
            'job_id': 'job-123'
        }
        
        # Collect resources
        batches = list(service.collect(params))
        
        assert len(batches) > 0
        resources = batches[0]
        
        assert len(resources) == 1
        vm = resources[0]
        
        # Verify normalized format
        assert vm['type'] == 'compute.Instance'
        assert vm['id'] == 'vm-001'
        assert vm['name'] == 'test-vm-1'
        assert vm['state'] == 'RUNNING'
        assert vm['account'] == 'account-1'
        assert vm['data']['cpu_cores'] == 4
        assert vm['data']['memory_gb'] == 8.0
```

### 2.3 Test Secret API Integration

```python
# src/tests/test_secret_helper.py

import pytest
from unittest.mock import MagicMock, patch
from src.connector.secret_helper import SecretHelper

class TestSecretHelper:
    
    def test_get_secret(self):
        """Test fetching secret from CloudForet Secret service."""
        mock_transaction = MagicMock()
        
        with patch('src.connector.secret_helper.get_grpc_service') as mock_get_service:
            mock_secret_service = MagicMock()
            mock_get_service.return_value = mock_secret_service
            
            # Mock the response
            mock_secret_service.UserSecret.get_data.return_value = {
                'data': {
                    'host': 'prism.local',
                    'username': 'admin',
                    'password': 'decrypted_password'
                }
            }
            
            helper = SecretHelper(mock_transaction)
            secret = helper.get_secret('secret-123')
            
            assert secret['host'] == 'prism.local'
            assert secret['password'] == 'decrypted_password'
            mock_secret_service.UserSecret.get_data.assert_called()
```

### 2.4 Test Cost Analysis API

```python
# src/tests/test_cost_service.py

import pytest
from unittest.mock import MagicMock
from src.service.cost_service import NutanixCostService

class TestNutanixCostService:
    
    def test_emit_cost_data(self):
        """Test cost calculation."""
        service = NutanixCostService(MagicMock())
        
        resource = {
            'id': 'vm-001',
            'name': 'test-vm',
            'type': 'compute.Instance',
            'data': {
                'cpu_cores': 4,
                'memory_gb': 8.0,
                'disk_size_gb': 100
            }
        }
        
        options = {
            'pricing': {
                'cpu_per_core_hour': 0.05,
                'memory_per_gb_hour': 0.01,
                'disk_per_gb_month': 0.001
            }
        }
        
        cost_event = service.emit_cost_data(resource, options)
        
        # Expected: (4 * 0.05) + (8 * 0.01) + (100 * 0.001 / 730)
        # = 0.20 + 0.08 + 0.000137 = 0.280137
        
        assert cost_event['resource_id'] == 'vm-001'
        assert cost_event['currency'] == 'USD'
        assert cost_event['cost'] > 0
        assert 'cost_breakdown' in cost_event
        assert cost_event['cost_breakdown']['compute'] == 0.20
        assert cost_event['cost_breakdown']['memory'] == 0.08
```

### 2.5 Test Alert Manager API

```python
# src/tests/test_alert_service.py

import pytest
from unittest.mock import MagicMock
from src.service.alert_service import NutanixAlertService

class TestNutanixAlertService:
    
    def test_create_alert_from_event(self):
        """Test alert creation from Nutanix event."""
        service = NutanixAlertService(MagicMock())
        
        event = {
            'event_id': 'evt-001',
            'event_type': 'VM_CREATED',
            'severity': 'WARNING',
            'message': 'VM test-vm-1 was created',
            'resource_type': 'compute.Instance',
            'resource_uuid': 'vm-001',
            'cluster_uuid': 'cluster-1',
            'timestamp': '2024-01-01T12:00:00Z'
        }
        
        alert = service.create_alert(event)
        
        assert alert['title'] == 'Nutanix: VM_CREATED'
        assert alert['severity'] == 'warning'
        assert alert['source']['provider'] == 'nutanix'
        assert alert['data']['event_id'] == 'evt-001'
```

### 2.6 Test Notification API

```python
# src/tests/test_notification_service.py

import pytest
from unittest.mock import MagicMock
from src.service.notification_service import NutanixNotificationService

class TestNutanixNotificationService:
    
    def test_notify_resource_created(self):
        """Test notification for resource creation."""
        service = NutanixNotificationService()
        
        resource = {
            'id': 'vm-001',
            'name': 'new-vm',
            'type': 'compute.Instance'
        }
        
        notification = service.notify_resource_change(resource, 'created', {})
        
        assert 'new-vm' in notification['title']
        assert notification['action'] == 'created'
        assert notification['severity'] == 'low'
```

---

## 3. INTEGRATION TESTS

### 3.1 Test with Real CloudForet Instance (Docker Compose)

```yaml
# docker-compose.yml for local testing

version: '3.8'

services:
  # CloudForet core services
  mongo:
    image: mongo:5.0
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: password
    ports:
      - "27017:27017"
  
  identity:
    image: cloudforet/identity:latest
    environment:
      MONGODB_URL: mongodb://root:password@mongo:27017
    ports:
      - "50051:50051"
    depends_on:
      - mongo
  
  inventory:
    image: cloudforet/inventory:latest
    environment:
      MONGODB_URL: mongodb://root:password@mongo:27017
    ports:
      - "50052:50051"
    depends_on:
      - mongo
  
  # Nutanix plugin
  plugin-nutanix:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      LOG_LEVEL: DEBUG
    ports:
      - "50053:50051"
    depends_on:
      - identity
      - inventory
```

Start local CloudForet:

```bash
docker-compose up -d

# Wait for services to start
sleep 10

# Test plugin endpoint
grpcurl -plaintext localhost:50053 list
```

### 3.2 End-to-End Collection Test

```python
# tests/integration/test_e2e_collection.py

import pytest
import grpc
from spaceone.api.inventory.v1 import collector_pb2_grpc, collector_pb2

class TestE2ECollection:
    """End-to-end collection workflow."""
    
    @pytest.fixture
    def grpc_channel(self):
        """Connect to local plugin."""
        channel = grpc.aio.secure_channel(
            'localhost:50053',
            grpc.ssl_channel_credentials()
        )
        yield channel
        channel.close()
    
    @pytest.mark.asyncio
    async def test_collect_nutanix_resources(self, grpc_channel):
        """Test full collection workflow."""
        stub = collector_pb2_grpc.CollectorStub(grpc_channel)
        
        # Prepare collection parameters
        params = collector_pb2.CollectRequest(
            secret={
                'host': 'prism.test.local',
                'username': 'admin',
                'password': 'test123',
            },
            options={
                'batch_size': '100'
            }
        )
        
        # Call collect()
        resources = []
        async for response in stub.collect(params):
            resources.extend(response.resources)
        
        # Verify results
        assert len(resources) > 0
        assert any(r.type == 'compute.Instance' for r in resources)
```

---

## 4. VALIDATION CHECKLIST

### 4.1 Pre-Deployment Validation

```bash
# Run all tests
pytest tests/ -v --cov=src --cov-report=html

# Lint code
flake8 src/ --count --select=E9,F63,F7,F82

# Type checking
mypy src/ --ignore-missing-imports

# Build Docker image
docker build -t plugin-nutanix-inven-collector:test .

# Test Docker image
docker run -p 50051:50051 plugin-nutanix-inven-collector:test &
sleep 5
grpcurl -plaintext localhost:50051 spaceone.core.v1.Plugin/init
kill %1
```

### 4.2 Kubernetes Deployment Validation

```bash
# Verify Helm chart
helm lint charts/plugin-nutanix-inven-collector/

# Generate manifests
helm template plugin-nutanix-inven-collector charts/plugin-nutanix-inven-collector/ > manifests.yaml

# Validate manifests
kubectl --dry-run=client -f manifests.yaml apply

# Deploy to test cluster
kubectl apply -f manifests.yaml -n cloudforet-test

# Verify deployment
kubectl get pods -n cloudforet-test
kubectl logs -f deployment/plugin-nutanix-inven-collector -n cloudforet-test
```

### 4.3 API Integration Validation

```bash
# Test with spacectl
spacectl config set api_key <your_api_key>

# Register secret
spacectl create secret plugin_nutanix_secret \
  --data '{
    "host": "prism.test.local",
    "username": "admin",
    "password": "secret"
  }'

# Verify plugin initialization
spacectl exec --plugin plugin-nutanix-inven-collector --method Plugin/init

# Test collection
spacectl exec --plugin plugin-nutanix-inven-collector \
  --method Collector/collect \
  --params '{
    "secret_id": "secret-xxx",
    "options": {"batch_size": 100}
  }' | jq '.resources | length'
```

---

## 5. PERFORMANCE & LOAD TESTING

### 5.1 Load Testing Script

```python
# tests/load_test.py

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

async def load_test_collection(num_iterations=10):
    """
    Load test: Simulate multiple concurrent collections.
    """
    import grpc
    from spaceone.api.inventory.v1 import collector_pb2_grpc, collector_pb2
    
    channel = grpc.aio.secure_channel(
        'localhost:50051',
        grpc.ssl_channel_credentials()
    )
    stub = collector_pb2_grpc.CollectorStub(channel)
    
    start_time = time.time()
    results = []
    
    async def single_collection():
        resources = []
        async for response in stub.collect(
            collector_pb2.CollectRequest(
                secret={'host': 'prism.test.local', 'username': 'admin'}
            )
        ):
            resources.extend(response.resources)
        return len(resources)
    
    # Run concurrent collections
    tasks = [single_collection() for _ in range(num_iterations)]
    results = await asyncio.gather(*tasks)
    
    elapsed = time.time() - start_time
    
    print(f'Load Test Results:')
    print(f'  Iterations: {num_iterations}')
    print(f'  Total resources: {sum(results)}')
    print(f'  Total time: {elapsed:.2f}s')
    print(f'  Avg time per iteration: {elapsed/num_iterations:.2f}s')
    print(f'  Resources/sec: {sum(results)/elapsed:.0f}')

# Run test
if __name__ == '__main__':
    asyncio.run(load_test_collection(10))
```

---

## 6. MONITORING & OBSERVABILITY

### 6.1 Plugin Health Check

```python
# src/health_check.py

import os
import logging
from prometheus_client import Counter, Gauge, Histogram
import time

# Prometheus metrics
collection_total = Counter(
    'nutanix_collection_total',
    'Total collections',
    ['status']
)

resources_collected = Gauge(
    'nutanix_resources_collected',
    'Number of resources collected'
)

collection_duration = Histogram(
    'nutanix_collection_duration_seconds',
    'Collection duration in seconds'
)

def log_collection_start(job_id):
    logging.info(f'Collection started: {job_id}')

def log_collection_end(job_id, resource_count, duration):
    logging.info(
        f'Collection ended: {job_id}, '
        f'resources={resource_count}, duration={duration:.2f}s'
    )
    
    collection_total.labels(status='success').inc()
    resources_collected.set(resource_count)
    collection_duration.observe(duration)

def log_collection_error(job_id, error):
    logging.error(f'Collection failed: {job_id}, error={str(error)}')
    collection_total.labels(status='error').inc()
```

### 6.2 Structured Logging

```python
# src/logger_config.py

import logging
import json

class StructuredLogger:
    """Emit structured logs for monitoring."""
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def info(self, message, **kwargs):
        log_entry = {'message': message, **kwargs}
        self.logger.info(json.dumps(log_entry))
    
    def error(self, message, error=None, **kwargs):
        log_entry = {
            'message': message,
            'error': str(error) if error else None,
            **kwargs
        }
        self.logger.error(json.dumps(log_entry))

# Usage
logger = StructuredLogger(__name__)
logger.info(
    'Collection completed',
    job_id='job-123',
    resource_count=42,
    duration=5.2
)
```

---

## 7. TROUBLESHOOTING

### 7.1 Common Issues & Solutions

| Issue | Root Cause | Solution |
|-------|-----------|----------|
| `Connection refused on localhost:50051` | Plugin not running | `python src/server.py` |
| `ERROR_INVALID_CREDENTIALS` | Wrong Nutanix credentials | Verify host, username, password |
| `gRPC connection timeout` | Plugin service unavailable | Check pod logs: `kubectl logs deployment/plugin-nutanix-inven-collector` |
| `MemoryError during collection` | Batch size too large | Reduce `batch_size` in options |
| `SSL certificate verification failed` | SSL/TLS issue | Set `verify_ssl: false` in secret or use valid cert |

### 7.2 Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python src/server.py

# Monitor logs in real-time
kubectl logs -f deployment/plugin-nutanix-inven-collector -n cloudforet
```

---

## 8. CI/CD PIPELINE

### 8.1 GitHub Actions Workflow

```yaml
# .github/workflows/test-and-build.yml

name: Test and Build

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Lint
      run: flake8 src/
    
    - name: Run tests
      run: pytest tests/ -v --cov=src
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: docker/setup-buildx-action@v2
    
    - name: Build Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: false
        tags: plugin-nutanix-inven-collector:${{ github.sha }}
```

---

## Summary

Use this guide to:
1. ✅ Test each CloudForet API integration
2. ✅ Validate plugin functionality locally
3. ✅ Deploy to Kubernetes with confidence
4. ✅ Monitor plugin health in production
5. ✅ Troubleshoot integration issues

All tests and validation should pass before deploying to production!

