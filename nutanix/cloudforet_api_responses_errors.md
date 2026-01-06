# CloudForet API Request/Response Examples & Error Handling

Complete examples of API calls, expected responses, and error handling patterns.

---

## 1️⃣ IDENTITY API Examples

### Request: Authenticate Plugin

```grpc
// Proto Definition
service Auth {
  rpc login(LoginRequest) returns (LoginResponse);
}

message LoginRequest {
  string domain_id = 1;
  string user_id = 2;
  string password = 3;
}

message LoginResponse {
  string token = 1;
  string expires_at = 2;
  string domain_id = 3;
}
```

### Python Implementation:

```python
async def authenticate_plugin():
    request = {
        'domain_id': 'domain-default',
        'user_id': 'plugin-service-account',
        'password': 'plugin-api-key-12345'
    }
    
    # Response
    {
        'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
        'expires_at': '2024-02-15T14:30:00Z',
        'domain_id': 'domain-default'
    }
```

### Error Handling:

```python
async def authenticate_with_error_handling():
    try:
        response = await identity_service.auth.login(request)
        return response.token
    
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            logger.error("Invalid API key")
            raise ERROR_INVALID_API_KEY("Invalid plugin credentials")
        
        elif e.code() == grpc.StatusCode.NOT_FOUND:
            logger.error("Domain not found")
            raise ERROR_DOMAIN_NOT_FOUND(domain_id=request['domain_id'])
        
        elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
            logger.error("Identity service timeout")
            raise ERROR_SERVICE_UNAVAILABLE("Identity service unreachable")
        
        else:
            logger.error(f"Unknown error: {e.details()}")
            raise ERROR_UNKNOWN(reason=e.details())
```

### Request: Fetch Secret

```python
# Request
{
    'secret_id': 'secret-abc123def456',
    'domain_id': 'domain-default'
}

# Response (Decrypted)
{
    'secret_id': 'secret-abc123def456',
    'name': 'nutanix-prism-creds',
    'data': {
        'nutanix_host': 'prism.nutanix.local',
        'nutanix_username': 'admin@nutanix.com',
        'nutanix_password': 'DecryptedPassword123!',
        'nutanix_port': 9440,
        'verify_ssl': True
    },
    'tags': {
        'environment': 'production',
        'region': 'us-east-1'
    },
    'domain_id': 'domain-default',
    'created_at': '2024-01-10T10:00:00Z',
    'updated_at': '2024-01-15T10:00:00Z'
}
```

### Error Cases:

```python
# Case 1: Secret doesn't exist
{
    'code': 'ERROR_NOT_FOUND',
    'message': 'Secret not found',
    'secret_id': 'secret-invalid'
}

# Case 2: Access denied (wrong workspace)
{
    'code': 'ERROR_PERMISSION_DENIED',
    'message': 'Access denied for secret in different workspace',
    'secret_id': 'secret-abc123def456'
}

# Case 3: Secret expired
{
    'code': 'ERROR_INVALID_PARAMETER',
    'message': 'Secret has expired',
    'secret_id': 'secret-abc123def456'
}
```

---

## 2️⃣ INVENTORY API Examples

### Request: Create Job

```python
# Request
{
    'collector_id': 'collector-nutanix-001',
    'name': 'Nutanix Collection Job',
    'service_account_ids': ['sa-prod-cluster-01', 'sa-prod-cluster-02'],
    'options': {
        'include_resources': ['compute.Instance', 'compute.Disk', 'compute.Network'],
        'timeout': 3600,
        'batch_size': 100,
        'incremental': False
    }
}

# Response (201 Created)
{
    'job_id': 'job-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    'collector_id': 'collector-nutanix-001',
    'status': 'CREATED',
    'created_at': '2024-01-15T10:00:00Z',
    'started_at': None,
    'finished_at': None,
    'total_task_count': 2,
    'succeeded_task_count': 0,
    'failed_task_count': 0
}
```

### Error Cases:

```python
# Case 1: Collector not found
{
    'code': 'ERROR_NOT_FOUND',
    'message': 'Collector not found',
    'collector_id': 'collector-invalid'
}

# Case 2: Invalid service account
{
    'code': 'ERROR_INVALID_PARAMETER',
    'message': 'Service account not found or not accessible',
    'parameter': 'service_account_ids',
    'service_account_id': 'sa-invalid'
}

# Case 3: Job already running
{
    'code': 'ERROR_CONFLICT',
    'message': 'Another job is already running for this collector',
    'collector_id': 'collector-nutanix-001'
}
```

### Request: Create JobTask

```python
# Request
{
    'job_id': 'job-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    'service_account_id': 'sa-prod-cluster-01',
    'secret_id': 'secret-nutanix-creds-01',
    'status': 'CREATED'
}

# Response (201 Created)
{
    'job_task_id': 'task-yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy',
    'job_id': 'job-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    'service_account_id': 'sa-prod-cluster-01',
    'secret_id': 'secret-nutanix-creds-01',
    'status': 'CREATED',
    'created_count': 0,
    'updated_count': 0,
    'deleted_count': 0,
    'error_count': 0,
    'created_at': '2024-01-15T10:00:00Z',
    'started_at': None,
    'finished_at': None
}
```

### Request: Update JobTask Progress

```python
# Request (During Collection)
{
    'job_task_id': 'task-yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy',
    'status': 'IN_PROGRESS',
    'progress': 35,  # Percent complete
    'updated_at': '2024-01-15T10:15:00Z'
}

# Response (200 OK)
{
    'job_task_id': 'task-yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy',
    'status': 'IN_PROGRESS',
    'progress': 35
}
```

### Request: Complete JobTask

```python
# Request
{
    'job_task_id': 'task-yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy',
    'status': 'FINISHED',
    'created_count': 450,
    'updated_count': 125,
    'deleted_count': 12,
    'error_count': 3,
    'disconnected_count': 0,
    'finished_at': '2024-01-15T10:45:00Z'
}

# Response (200 OK)
{
    'job_task_id': 'task-yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy',
    'status': 'FINISHED',
    'created_count': 450,
    'updated_count': 125,
    'deleted_count': 12,
    'error_count': 3,
    'success': True
}
```

---

## 3️⃣ CLOUD SERVICE API Examples

### Request: Create Cloud Service (Resource)

```python
# Request - Single Resource
{
    'cloud_service_type': 'compute.Instance',
    'cloud_service_group': 'Nutanix',
    'cloud_service_name': 'prod-web-server-01',
    'provider': 'nutanix',
    'account': 'sa-prod-cluster-01',
    'data': {
        'state': 'ON',
        'cpu_cores': 8,
        'memory_gb': 32,
        'disk_total_gb': 500,
        'cluster': 'cluster-prod-01',
        'created_at': '2023-06-15T08:30:00Z',
        'updated_at': '2024-01-10T14:20:00Z',
        'nutanix_uuid': 'vm-abc123def456',
        'power_state': 'ON',
        'vcpu_count': 8,
        'numa_node_count': 1,
        'hypervisor_type': 'AHV',
        'network_interfaces': 3,
        'disk_count': 4
    },
    'tags': {
        'environment': 'production',
        'owner': 'devops-team',
        'department': 'infrastructure',
        'cost_center': 'CC-001',
        'cluster': 'cluster-prod-01'
    },
    'reference': {
        'resource_id': 'vm-abc123def456',
        'external_link': 'https://prism.local/console/#page/vm_details/vm-abc123def456'
    },
    'project_id': 'project-prod-001'
}

# Response (201 Created)
{
    'cloud_service_id': 'cs-zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz',
    'name': 'prod-web-server-01',
    'cloud_service_type': 'compute.Instance',
    'cloud_service_group': 'Nutanix',
    'provider': 'nutanix',
    'account': 'sa-prod-cluster-01',
    'state': 'ON',
    'created_at': '2024-01-15T10:00:00Z',
    'updated_at': '2024-01-15T10:00:00Z'
}
```

### Error Cases:

```python
# Case 1: Duplicate resource (already exists)
{
    'code': 'ERROR_CONFLICT',
    'message': 'Resource already exists',
    'resource_id': 'vm-abc123def456'
}

# Case 2: Invalid cloud service type
{
    'code': 'ERROR_INVALID_PARAMETER',
    'message': 'Unknown cloud service type',
    'parameter': 'cloud_service_type',
    'value': 'compute.InvalidType'
}

# Case 3: Missing required fields
{
    'code': 'ERROR_INVALID_PARAMETER',
    'message': 'Missing required field',
    'parameter': 'provider'
}
```

### Request: Query Cloud Services

```python
# Request - List with Filter
{
    'query': {
        'filter': [
            {'k': 'provider', 'v': 'nutanix', 'o': 'eq'},
            {'k': 'cloud_service_type', 'v': 'compute.Instance', 'o': 'eq'},
            {'k': 'state', 'v': 'ON', 'o': 'eq'},
            {'k': 'account', 'v': 'sa-prod-cluster-01', 'o': 'eq'},
            {'k': 'tags.environment', 'v': 'production', 'o': 'eq'}
        ],
        'sort': {'key': 'name', 'desc': False},
        'page': {'start': 0, 'limit': 50},
        'only': ['cloud_service_id', 'name', 'state', 'account', 'data']
    }
}

# Response (200 OK)
{
    'results': [
        {
            'cloud_service_id': 'cs-zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz',
            'name': 'prod-web-server-01',
            'state': 'ON',
            'account': 'sa-prod-cluster-01',
            'data': {
                'cpu_cores': 8,
                'memory_gb': 32,
                'cluster': 'cluster-prod-01'
            }
        },
        {
            'cloud_service_id': 'cs-wwwwwwww-wwww-wwww-wwww-wwwwwwwwwwww',
            'name': 'prod-web-server-02',
            'state': 'ON',
            'account': 'sa-prod-cluster-01',
            'data': {
                'cpu_cores': 16,
                'memory_gb': 64,
                'cluster': 'cluster-prod-01'
            }
        }
    ],
    'total_count': 45
}
```

### Request: Statistics Query

```python
# Request - Get stats by cluster
{
    'query': {
        'aggregate': [
            {
                'group': {
                    'keys': ['data.cluster', 'state']
                },
                'statistics': {
                    'count': {'key': 'cloud_service_id'},
                    'avg_cpu': {'field': 'data.cpu_cores'},
                    'avg_memory': {'field': 'data.memory_gb'},
                    'total_disk': {'field': 'data.disk_total_gb'}
                }
            }
        ],
        'filter': [
            {'k': 'provider', 'v': 'nutanix', 'o': 'eq'},
            {'k': 'cloud_service_type', 'v': 'compute.Instance', 'o': 'eq'}
        ]
    }
}

# Response (200 OK)
{
    'results': [
        {
            'cluster': 'cluster-prod-01',
            'state': 'ON',
            'count': 42,
            'avg_cpu': 12.5,
            'avg_memory': 48.0,
            'total_disk': 21000.0
        },
        {
            'cluster': 'cluster-prod-01',
            'state': 'OFF',
            'count': 8,
            'avg_cpu': 4.0,
            'avg_memory': 16.0,
            'total_disk': 2000.0
        },
        {
            'cluster': 'cluster-dev-01',
            'state': 'ON',
            'count': 15,
            'avg_cpu': 8.0,
            'avg_memory': 32.0,
            'total_disk': 1500.0
        }
    ]
}
```

---

## 4️⃣ COST ANALYSIS API Examples

### Request: Push Cost Data

```python
# Request - Single Cost Record
{
    'data_source_id': 'ds-cost-nutanix-001',
    'date': '2024-01-15',
    'cost': 12.50,
    'currency': 'USD',
    'resource_id': 'vm-abc123def456',
    'resource_type': 'compute.Instance',
    'region': 'on-premises',
    'tags': {
        'cluster': 'cluster-prod-01',
        'department': 'engineering',
        'environment': 'production'
    }
}

# Response (201 Created)
{
    'cost_id': 'cost-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    'date': '2024-01-15',
    'cost': 12.50,
    'resource_id': 'vm-abc123def456',
    'created_at': '2024-01-15T11:00:00Z'
}
```

### Batch Request: Multiple Costs

```python
# Request - Batch Push
{
    'costs': [
        {
            'date': '2024-01-15',
            'cost': 12.50,
            'resource_id': 'vm-abc123def456',
            'tags': {'cluster': 'cluster-prod-01'}
        },
        {
            'date': '2024-01-15',
            'cost': 8.75,
            'resource_id': 'vm-def789ghi012',
            'tags': {'cluster': 'cluster-prod-01'}
        },
        {
            'date': '2024-01-15',
            'cost': 5.25,
            'resource_id': 'vm-jkl345mno678',
            'tags': {'cluster': 'cluster-dev-01'}
        }
    ]
}

# Response (202 Accepted)
{
    'created_count': 3,
    'failed_count': 0,
    'total_cost': 26.50,
    'job_id': 'job-cost-batch-001'
}
```

### Error Cases:

```python
# Case 1: Invalid cost value
{
    'code': 'ERROR_INVALID_PARAMETER',
    'message': 'Cost must be a positive number',
    'parameter': 'cost',
    'value': -5.0
}

# Case 2: Invalid date format
{
    'code': 'ERROR_INVALID_PARAMETER',
    'message': 'Date must be in YYYY-MM-DD format',
    'parameter': 'date',
    'value': '15-01-2024'
}

# Case 3: Data source not found
{
    'code': 'ERROR_NOT_FOUND',
    'message': 'Data source not found',
    'data_source_id': 'ds-invalid'
}
```

---

## 5️⃣ MONITORING API Examples

### Request: Push Metrics

```python
# Request - Single Metric
{
    'resource_id': 'vm-abc123def456',
    'metric_name': 'cpu.utilization',
    'value': 45.2,
    'unit': 'percent',
    'timestamp': '2024-01-15T10:30:00Z',
    'dimensions': {
        'cluster': 'cluster-prod-01',
        'environment': 'production'
    }
}

# Response (201 Created)
{
    'metric_id': 'metric-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    'resource_id': 'vm-abc123def456',
    'metric_name': 'cpu.utilization',
    'value': 45.2,
    'created_at': '2024-01-15T10:30:00Z'
}
```

### Batch Request: Multiple Metrics

```python
# Request - Multiple Metrics for Single Resource
{
    'resource_id': 'vm-abc123def456',
    'metrics': [
        {
            'metric_name': 'cpu.utilization',
            'value': 45.2,
            'unit': 'percent'
        },
        {
            'metric_name': 'memory.utilization',
            'value': 62.5,
            'unit': 'percent'
        },
        {
            'metric_name': 'disk.read_iops',
            'value': 150,
            'unit': 'iops'
        },
        {
            'metric_name': 'disk.write_iops',
            'value': 85,
            'unit': 'iops'
        },
        {
            'metric_name': 'network.received_throughput',
            'value': 1024000,
            'unit': 'bytes_per_sec'
        },
        {
            'metric_name': 'network.sent_throughput',
            'value': 512000,
            'unit': 'bytes_per_sec'
        }
    ],
    'timestamp': '2024-01-15T10:30:00Z'
}

# Response (202 Accepted)
{
    'created_count': 6,
    'failed_count': 0,
    'resource_id': 'vm-abc123def456'
}
```

### Request: Query Metrics

```python
# Request - Fetch Historical Metrics
{
    'query': {
        'filter': [
            {'k': 'resource_id', 'v': 'vm-abc123def456', 'o': 'eq'},
            {'k': 'metric_name', 'v': ['cpu.utilization', 'memory.utilization'], 'o': 'in'},
            {'k': 'timestamp', 'v': ['2024-01-15T00:00:00Z', '2024-01-15T23:59:59Z'], 'o': 'between'}
        ],
        'sort': {'key': 'timestamp', 'desc': False},
        'page': {'start': 0, 'limit': 1000}
    }
}

# Response (200 OK)
{
    'results': [
        {
            'metric_id': 'metric-xxxxxxxx',
            'resource_id': 'vm-abc123def456',
            'metric_name': 'cpu.utilization',
            'value': 42.1,
            'unit': 'percent',
            'timestamp': '2024-01-15T10:00:00Z'
        },
        {
            'metric_id': 'metric-yyyyyyyy',
            'resource_id': 'vm-abc123def456',
            'metric_name': 'cpu.utilization',
            'value': 45.2,
            'unit': 'percent',
            'timestamp': '2024-01-15T10:30:00Z'
        },
        {
            'metric_id': 'metric-zzzzzzzz',
            'resource_id': 'vm-abc123def456',
            'metric_name': 'cpu.utilization',
            'value': 48.7,
            'unit': 'percent',
            'timestamp': '2024-01-15T11:00:00Z'
        },
        {
            'metric_id': 'metric-wwwwwwww',
            'resource_id': 'vm-abc123def456',
            'metric_name': 'memory.utilization',
            'value': 60.0,
            'unit': 'percent',
            'timestamp': '2024-01-15T10:00:00Z'
        }
    ],
    'total_count': 48
}
```

---

## 6️⃣ NOTIFICATION API Examples

### Request: Send Notification

```python
# Request
{
    'title': 'Collection Complete: Nutanix Plugin',
    'message': 'Successfully collected 450 resources. 3 errors occurred.',
    'severity': 'WARNING',
    'notification_type': 'USER',
    'tags': {
        'collector_id': 'collector-nutanix-001',
        'job_id': 'job-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
        'resource_count': '450',
        'error_count': '3'
    },
    'channels': ['slack', 'email'],
    'recipients': ['ops-team@company.com', '#cloud-ops']
}

# Response (201 Created)
{
    'notification_id': 'notif-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    'title': 'Collection Complete: Nutanix Plugin',
    'severity': 'WARNING',
    'created_at': '2024-01-15T10:45:00Z',
    'is_read': False
}
```

---

## ⚠️ Common Error Handling Patterns

### Pattern 1: Retry Logic with Exponential Backoff

```python
import asyncio
from datetime import datetime, timedelta

async def api_call_with_retry(api_func, *args, max_retries=3, base_delay=1):
    """
    Retry API calls with exponential backoff.
    Handles transient errors (timeout, connection errors).
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await api_func(*args)
        
        except grpc.RpcError as e:
            last_exception = e
            
            # Don't retry on client errors (4xx)
            if e.code() in [
                grpc.StatusCode.INVALID_ARGUMENT,
                grpc.StatusCode.NOT_FOUND,
                grpc.StatusCode.PERMISSION_DENIED,
                grpc.StatusCode.UNAUTHENTICATED,
            ]:
                raise
            
            # Retry on server/network errors (5xx, transient)
            if e.code() in [
                grpc.StatusCode.UNAVAILABLE,
                grpc.StatusCode.DEADLINE_EXCEEDED,
                grpc.StatusCode.INTERNAL,
            ]:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"API call failed, retrying in {delay}s",
                        extra={'attempt': attempt + 1, 'error': e.details()}
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise
            else:
                raise
    
    raise last_exception
```

### Pattern 2: Error Categorization

```python
class APIErrorCategory:
    """Categorize errors for appropriate handling."""
    
    @staticmethod
    def categorize(error: Exception) -> str:
        if isinstance(error, grpc.RpcError):
            code = error.code()
            
            # Authentication errors
            if code == grpc.StatusCode.UNAUTHENTICATED:
                return 'AUTH_ERROR'
            
            # Permission errors
            elif code == grpc.StatusCode.PERMISSION_DENIED:
                return 'PERMISSION_ERROR'
            
            # Validation errors
            elif code == grpc.StatusCode.INVALID_ARGUMENT:
                return 'VALIDATION_ERROR'
            
            # Not found errors
            elif code == grpc.StatusCode.NOT_FOUND:
                return 'NOT_FOUND_ERROR'
            
            # Resource conflict
            elif code == grpc.StatusCode.ALREADY_EXISTS:
                return 'CONFLICT_ERROR'
            
            # Transient/Retry errors
            elif code in [grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED]:
                return 'TRANSIENT_ERROR'
            
            # Server errors
            elif code == grpc.StatusCode.INTERNAL:
                return 'SERVER_ERROR'
        
        return 'UNKNOWN_ERROR'
    
    @staticmethod
    def should_retry(category: str) -> bool:
        return category in ['TRANSIENT_ERROR', 'SERVER_ERROR']
    
    @staticmethod
    def should_alert(category: str) -> bool:
        return category in ['AUTH_ERROR', 'PERMISSION_ERROR', 'SERVER_ERROR']
```

### Pattern 3: Circuit Breaker Pattern

```python
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = 'closed'          # Normal operation
    OPEN = 'open'              # Failing, reject requests
    HALF_OPEN = 'half_open'    # Testing if service recovered

class CircuitBreaker:
    """Prevent cascading failures with circuit breaker pattern."""
    
    def __init__(self, failure_threshold=5, timeout_seconds=60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
    
    async def call(self, api_func, *args):
        """Execute API call with circuit breaker protection."""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker: attempting recovery")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await api_func(*args)
            self._on_success()
            return result
        
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Record successful call."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        logger.info("Circuit breaker: CLOSED (healthy)")
    
    def _on_failure(self):
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(f"Circuit breaker: OPEN (threshold reached)")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to retry."""
        if not self.last_failure_time:
            return False
        
        time_since_failure = datetime.utcnow() - self.last_failure_time
        return time_since_failure.total_seconds() > self.timeout_seconds
```

### Pattern 4: Comprehensive Error Response

```python
class APIError(Exception):
    """Standardized API error."""
    
    def __init__(self, code, message, details=None, request_id=None, retry=False):
        self.code = code
        self.message = message
        self.details = details or {}
        self.request_id = request_id
        self.retry = retry
        super().__init__(message)
    
    def to_dict(self):
        return {
            'error_code': self.code,
            'error_message': self.message,
            'error_details': self.details,
            'request_id': self.request_id,
            'should_retry': self.retry
        }

# Usage
async def safe_api_call(api_func, request, context=None):
    try:
        return await api_func(request)
    
    except grpc.RpcError as e:
        error_code = e.code().name
        error_message = e.details()
        
        should_retry = error_code in [
            'UNAVAILABLE',
            'DEADLINE_EXCEEDED',
            'INTERNAL'
        ]
        
        raise APIError(
            code=error_code,
            message=error_message,
            details={'grpc_code': e.code()},
            request_id=context.get('request_id') if context else None,
            retry=should_retry
        )
```

---

## 📋 API Response Status Codes

| HTTP Code | gRPC Code | Meaning | Retry? |
|-----------|-----------|---------|--------|
| 200 | OK | Success | No |
| 201 | OK | Created | No |
| 202 | OK | Accepted (async) | No |
| 400 | INVALID_ARGUMENT | Bad request | No |
| 401 | UNAUTHENTICATED | Auth failed | No |
| 403 | PERMISSION_DENIED | Access denied | No |
| 404 | NOT_FOUND | Not found | No |
| 409 | ALREADY_EXISTS | Conflict | No |
| 429 | RESOURCE_EXHAUSTED | Rate limited | Yes (with backoff) |
| 500 | INTERNAL | Server error | Yes |
| 502 | UNAVAILABLE | Service unavailable | Yes |
| 503 | UNAVAILABLE | Service unavailable | Yes |
| 504 | DEADLINE_EXCEEDED | Timeout | Yes |

