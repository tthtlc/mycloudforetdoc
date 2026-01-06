# CloudForet APIs for Nutanix Plugin Development - Complete Guide

This guide shows how to leverage CloudForet's 7 major APIs to build a production-grade Nutanix collector plugin.

---

## 📚 Documents Included

### 1. **cloudforet_api_plugin_guide.md**
   - Overview of all 7 CloudForet APIs
   - Conceptual explanations of each API
   - When to use each API during plugin lifecycle
   - Feature-based API usage examples
   - Complete architecture diagram showing API interactions

### 2. **cloudforet_api_implementations.md**
   - **Production-ready code** for each API
   - Complete connector classes for authentication, resource management, cost tracking, metrics
   - Full error handling patterns
   - Streaming implementations for large-scale data
   - Retry logic and resilience patterns

### 3. **cloudforet_api_responses_errors.md**
   - Actual request/response examples for each API
   - Common error codes and how to handle them
   - Error categorization and recovery strategies
   - Circuit breaker pattern implementation
   - HTTP/gRPC status code mappings

---

## 🎯 Quick Reference: Which API for Which Feature?

| Feature | API | Key Methods | Frequency |
|---------|-----|-------------|-----------|
| **Plugin Authentication** | Identity | Auth.login, Secret.get | Startup + Token refresh |
| **Collection Management** | Inventory | Job.create, JobTask.create, JobTask.update | Per collection cycle |
| **Resource Storage** | Inventory | CloudService.create, CloudService.list | Per resource |
| **Cost Integration** | Cost Analysis | Cost.create, DataSource.sync | Per resource or daily |
| **Metrics Collection** | Monitoring | MetricData.create, Metric.list | Per metric point |
| **Alerts & Events** | Notification | Notification.create | On completion/error |
| **Plugin Registration** | Repository | Plugin.register, Schema.publish | Startup only |

---

## 🔄 Typical Plugin Workflow Using All APIs

```
┌─────────────────────────────────────────────────────────────────┐
│ PLUGIN STARTUP                                                   │
├─────────────────────────────────────────────────────────────────┤
│ 1. Identity API → Authenticate plugin                            │
│ 2. Repository API → Register plugin metadata & schemas           │
│ 3. Listen for collection requests                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ COLLECTION JOB EXECUTION (hourly/daily)                         │
├─────────────────────────────────────────────────────────────────┤
│ 1. Identity API → Fetch encrypted credentials (per account)     │
│ 2. [COLLECT FROM NUTANIX] ← Plugin's core logic                 │
│ 3. Inventory API → Create/update resources                      │
│ 4. Cost Analysis API → Push cost metrics                        │
│ 5. Monitoring API → Push performance metrics                    │
│ 6. Inventory API → Update JobTask status                        │
│ 7. Notification API → Send completion alert                     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ ONGOING OPERATIONS                                               │
├─────────────────────────────────────────────────────────────────┤
│ • Inventory API → Query collected resources (dashboards)         │
│ • Cost Analysis API → Generate cost reports                     │
│ • Monitoring API → Historical metric queries                    │
│ • Repository API → Check for plugin updates                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💻 Implementation Checklist

### Phase 1: Authentication & Registration
- [ ] Implement IdentityConnector for plugin authentication
- [ ] Set up token refresh mechanism
- [ ] Implement RepositoryConnector for plugin registration
- [ ] Define and publish JSON schemas for secrets

### Phase 2: Collection Management
- [ ] Implement InventoryConnector for Job management
- [ ] Create JobTask per service account
- [ ] Implement progress tracking (status, progress %)
- [ ] Handle job completion and error reporting

### Phase 3: Resource Management
- [ ] Normalize Nutanix resources to CloudForet format
- [ ] Stream resources to inventory (CloudService API)
- [ ] Handle bulk resource creation efficiently
- [ ] Query resources for validation

### Phase 4: Cost Integration
- [ ] Extract cost metrics from Nutanix resources
- [ ] Push cost data to Cost Analysis API
- [ ] Implement cost statistics queries
- [ ] Setup automated cost sync schedule

### Phase 5: Monitoring Integration
- [ ] Collect performance metrics from Nutanix
- [ ] Push metrics to Monitoring API (cpu, memory, disk, network)
- [ ] Implement metric query functionality
- [ ] Setup metric retention policies

### Phase 6: Alerts & Notifications
- [ ] Implement NotificationConnector
- [ ] Send completion notifications with statistics
- [ ] Alert on collection failures
- [ ] Setup notification channels (Slack, Email, etc.)

### Phase 7: Error Handling & Resilience
- [ ] Implement retry logic with exponential backoff
- [ ] Add circuit breaker pattern for cascading failures
- [ ] Comprehensive error categorization
- [ ] Structured logging for all API calls

### Phase 8: Testing & Deployment
- [ ] Unit tests for each connector
- [ ] Integration tests with CloudForet APIs
- [ ] Load testing for large resource counts
- [ ] Helm chart for Kubernetes deployment
- [ ] CI/CD pipeline integration

---

## 🔐 Security Considerations

### 1. **Credential Management**
```python
# ✅ DO: Use Identity API to fetch encrypted secrets
secret = await identity_connector.fetch_secret(secret_id)
credentials = secret['data']  # Already decrypted

# ❌ DON'T: Store credentials in environment variables
nutanix_password = os.getenv('NUTANIX_PASSWORD')  # WRONG!
```

### 2. **API Token Lifecycle**
```python
# ✅ DO: Implement token refresh before expiry
if token_expiry - now < timedelta(minutes=5):
    token = await get_new_token()

# ❌ DON'T: Reuse expired tokens
if token_expired:
    # Try to use anyway (will fail)
```

### 3. **Secret Data Handling**
```python
# ✅ DO: Never log passwords
logger.info("Connected to cluster", extra={'host': host})

# ❌ DON'T: Log sensitive data
logger.info(f"Connected with credentials: {credentials}")
```

### 4. **RBAC & Permissions**
```python
# ✅ DO: Check required permissions
required_permissions = ['inventory.Collector.create', 'inventory.Job.create']
for perm in required_permissions:
    if not user_has_permission(perm):
        raise ERROR_PERMISSION_DENIED()

# ❌ DON'T: Assume user has permissions
```

---

## 📊 Performance Optimization Tips

### 1. **Batch API Calls**
```python
# ✅ Better: Batch 100 resources in one streaming call
for batch in chunk_list(resources, 100):
    await stream_resources(task_id, batch)

# ❌ Worse: Individual API calls for each resource
for resource in resources:
    await create_resource(task_id, resource)  # 1000 calls!
```

### 2. **Incremental Collection**
```python
# ✅ Better: Collect only changed resources
last_sync = get_last_sync_time()
resources = query_resources(modified_after=last_sync)

# ❌ Worse: Collect everything every time
resources = query_all_resources()  # Million resources!
```

### 3. **Parallel Processing**
```python
# ✅ Better: Process multiple accounts in parallel
tasks = [
    process_account(account_id)
    for account_id in service_account_ids
]
await asyncio.gather(*tasks)

# ❌ Worse: Sequential processing
for account_id in service_account_ids:
    await process_account(account_id)  # Slow!
```

### 4. **Connection Pooling**
```python
# ✅ Better: Reuse gRPC channels
async def get_channel(endpoint):
    if endpoint not in channel_pool:
        channel_pool[endpoint] = grpc.aio.secure_channel(...)
    return channel_pool[endpoint]

# ❌ Worse: Create new channel for each call
async def api_call():
    channel = grpc.aio.secure_channel(...)
    # Use channel
    await channel.close()
```

---

## 🧪 Testing Strategy

### Unit Tests - Mock CloudForet APIs

```python
# tests/test_identity_connector.py
@pytest.mark.asyncio
async def test_authenticate_plugin():
    with patch('grpc.aio.secure_channel') as mock_channel:
        mock_stub = AsyncMock()
        mock_stub.login.return_value = LoginResponse(
            token='test-token',
            expires_at='2024-01-20T00:00:00Z'
        )
        
        connector = IdentityConnector('endpoint', 'api-key')
        token = await connector._authenticate()
        
        assert token == 'test-token'
        mock_stub.login.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_secret():
    with patch.object(IdentityConnector, 'get_valid_token', return_value='token'):
        connector = IdentityConnector('endpoint', 'api-key')
        secret = await connector.fetch_secret('secret-123')
        
        assert secret['host'] == 'prism.nutanix.local'
```

### Integration Tests - Real CloudForet Instance

```python
# tests/integration/test_collection_workflow.py
@pytest.mark.asyncio
async def test_end_to_end_collection(cloudforet_test_env):
    """Test complete collection workflow."""
    plugin = NutanixCollectorPlugin()
    
    # Create test job
    job_id = await plugin.inventory_connector.create_collection_job(
        collector_id='test-collector',
        service_account_ids=['test-sa']
    )
    
    # Run collection
    await plugin.collect({'job_id': job_id})
    
    # Verify resources were created
    resources = await plugin.inventory_connector.query_resources(
        filter={'provider': 'nutanix'}
    )
    assert len(resources) > 0
```

---

## 🚀 Deployment Guide

### Docker Image

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy plugin code
COPY src/ ./src/

# gRPC port
EXPOSE 50051

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -m grpc_health_probe -addr=:50051 || exit 1

# Start plugin
CMD ["python", "src/server.py"]
```

### Helm Deployment

```bash
# Create namespace
kubectl create namespace cloudforet

# Add CloudForet Helm repo
helm repo add cloudforet https://helm.cloudforet.io
helm repo update

# Install plugin
helm install plugin-nutanix ./charts/plugin-nutanix \
  --namespace cloudforet \
  --values values.yaml

# Verify deployment
kubectl get pods -n cloudforet -l app=plugin-nutanix
```

---

## 📖 API Documentation References

- **CloudForet API Docs**: https://cloudforet.io/api-doc/
- **SpaceONE API Repo**: https://github.com/cloudforet-io/api
- **Plugin Examples**: https://github.com/cloudforet-io/plugin-aws-ec2-inven-collector
- **Developer Guide**: https://spaceone.org/docs/developers/

---

## 🆘 Troubleshooting Common Issues

### Issue 1: "Plugin not found in registry"
```
Solution: Check Repository API registration
- Ensure plugin is registered with correct provider name
- Verify plugin version matches collector configuration
- Check Docker image is accessible
```

### Issue 2: "Authentication failed: Invalid API key"
```
Solution: Check Identity API setup
- Verify PLUGIN_API_KEY environment variable
- Check domain_id is correct
- Ensure service account has correct permissions
```

### Issue 3: "Job stuck in CREATED status"
```
Solution: Check Inventory API job task creation
- Verify service account IDs are valid
- Check secret IDs exist and are accessible
- Ensure JobTask creation succeeded
```

### Issue 4: "Memory leak / High CPU during collection"
```
Solution: Optimize resource streaming
- Batch resources instead of individual creates
- Implement proper connection pooling
- Use async/await correctly to avoid blocking
- Profile code to find bottlenecks
```

### Issue 5: "Cost data not appearing"
```
Solution: Check Cost Analysis API integration
- Verify data_source_id is registered
- Check cost dates are valid (YYYY-MM-DD format)
- Ensure cost values are positive numbers
- Check filter queries for data source
```

---

## 📞 Support & Community

- **GitHub Issues**: https://github.com/cloudforet-io/cloudforet/issues
- **Slack Community**: https://cloudforet-io.slack.com
- **Documentation**: https://spaceone.org/docs/
- **Plugin Forum**: https://forum.cloudforet.io/c/plugins/

---

## ✅ Validation Checklist Before Production

- [ ] All 7 APIs integrated and tested
- [ ] Error handling for all failure scenarios
- [ ] Retry logic with exponential backoff
- [ ] Circuit breaker for cascading failures
- [ ] Structured logging for all operations
- [ ] Unit test coverage >80%
- [ ] Integration tests with CloudForet
- [ ] Load testing (1000+ resources)
- [ ] Security review (no hardcoded secrets)
- [ ] Performance benchmarks documented
- [ ] Helm chart validated
- [ ] CI/CD pipeline configured
- [ ] Documentation complete
- [ ] Team trained on operations
- [ ] Monitoring and alerting setup

---

## 📝 Example: Complete Collection Cycle

```python
# When user clicks "Collect Now" in CloudForet Console:

1. [Identity API]
   - Authenticate plugin with credentials
   - Get API token valid for 1 hour

2. [Inventory API]
   - Create Job for collection request
   - Create JobTask for each service account

3. [Identity API]
   - Fetch encrypted Nutanix credentials from CloudForet

4. [NUTANIX API] (Plugin's responsibility)
   - Query all VMs from Nutanix cluster
   - Query all disks, networks, etc.
   - Format data

5. [Inventory API]
   - Stream 450 resources to CloudForet inventory
   - Update JobTask with progress

6. [Cost Analysis API]
   - Extract cost metrics from resources
   - Push 450 cost records

7. [Monitoring API]
   - Extract performance metrics
   - Push CPU, memory, disk, network metrics

8. [Inventory API]
   - Mark JobTask as FINISHED
   - Report statistics (created, updated, deleted)

9. [Notification API]
   - Send "Collection Complete" notification
   - Include statistics and timestamps

10. [Repository API]
    - Update plugin stats (last run, resource count)
    - Check for plugin updates available

Result: CloudForet dashboard shows 450 new/updated resources
        with cost and performance data ready for analysis
```

---

## 🎓 Learning Path

1. **Start Here**: Read `cloudforet_api_plugin_guide.md` for conceptual overview
2. **Study Examples**: Review `cloudforet_api_implementations.md` for production code
3. **Reference Responses**: Use `cloudforet_api_responses_errors.md` for API details
4. **Implement Connectors**: Build one connector at a time (Identity → Inventory → Cost → Monitoring)
5. **Test Locally**: Use CloudForet dev environment for testing
6. **Deploy to K8s**: Use Helm chart for production deployment
7. **Monitor & Iterate**: Setup alerts and optimize based on metrics

---

## 📄 File Organization

```
plugin-nutanix-inven-collector/
├── src/
│   ├── server.py                 # Plugin entry point
│   ├── connector/
│   │   ├── identity_connector.py # Identity API integration
│   │   ├── inventory_connector.py# Inventory API integration
│   │   ├── cost_connector.py     # Cost Analysis API
│   │   ├── monitoring_connector.py# Monitoring API
│   │   ├── repository_connector.py# Repository API
│   │   └── notification_connector.py# Notification API
│   ├── service/
│   │   ├── collector_service.py  # Core collection logic
│   │   ├── resource_handler.py   # Resource normalization
│   │   └── job_handler.py        # Job orchestration
│   └── tests/
│       ├── test_connectors.py    # Unit tests
│       └── integration/
│           └── test_workflow.py  # End-to-end tests
├── charts/
│   └── plugin-nutanix/          # Helm chart
├── Dockerfile                   # Container image
├── requirements.txt             # Python dependencies
└── README.md                    # Documentation
```

