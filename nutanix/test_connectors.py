"""
Unit Tests for CloudForet Connectors
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

from connector.identity_connector import IdentityConnector, TokenInfo, SecretManager
from connector.inventory_connector import InventoryConnector
from connector.other_connectors import CostConnector, MonitoringConnector


class TestTokenInfo:
    """Test TokenInfo dataclass."""
    
    def test_token_is_valid(self):
        """Test valid token."""
        future_time = datetime.utcnow() + timedelta(hours=1)
        token_info = TokenInfo(token='test-token', expires_at=future_time)
        
        assert token_info.is_valid is True
    
    def test_token_is_invalid(self):
        """Test expired token."""
        past_time = datetime.utcnow() - timedelta(hours=1)
        token_info = TokenInfo(token='test-token', expires_at=past_time)
        
        assert token_info.is_valid is False
    
    def test_token_near_expiry(self):
        """Test token near expiry (5 min buffer)."""
        near_expiry = datetime.utcnow() + timedelta(minutes=3)
        token_info = TokenInfo(token='test-token', expires_at=near_expiry)
        
        assert token_info.is_valid is False


class TestIdentityConnector:
    """Test Identity connector."""
    
    @pytest.mark.asyncio
    async def test_get_valid_token(self):
        """Test getting valid token."""
        connector = IdentityConnector(
            'grpc://identity:50051',
            'test-api-key',
            'domain-default'
        )
        
        token = await connector.get_valid_token()
        assert token == 'test-api-key'
    
    @pytest.mark.asyncio
    async def test_token_caching(self):
        """Test token is cached."""
        connector = IdentityConnector(
            'grpc://identity:50051',
            'test-api-key'
        )
        
        token1 = await connector.get_valid_token()
        token2 = await connector.get_valid_token()
        
        assert token1 == token2
    
    @pytest.mark.asyncio
    async def test_fetch_secret(self):
        """Test fetching secret."""
        connector = IdentityConnector(
            'grpc://identity:50051',
            'test-api-key'
        )
        
        secret = await connector.fetch_secret('secret-123')
        
        assert 'data' in secret
        assert 'nutanix_host' in secret['data']


class TestSecretManager:
    """Test Secret manager."""
    
    @pytest.mark.asyncio
    async def test_secret_caching(self):
        """Test secret caching."""
        mock_connector = AsyncMock()
        mock_connector.fetch_secret.return_value = {
            'secret_id': 'secret-123',
            'data': {'host': 'test.local'}
        }
        
        manager = SecretManager(mock_connector)
        
        secret1 = await manager.get_secret('secret-123')
        secret2 = await manager.get_secret('secret-123')
        
        assert mock_connector.fetch_secret.call_count == 1
        assert secret1 == secret2
    
    def test_clear_cache(self):
        """Test cache clearing."""
        mock_connector = AsyncMock()
        manager = SecretManager(mock_connector)
        
        manager._cache['secret-123'] = {'data': 'test'}
        manager.clear_cache('secret-123')
        
        assert 'secret-123' not in manager._cache
    
    def test_clear_all_cache(self):
        """Test clearing all cache."""
        mock_connector = AsyncMock()
        manager = SecretManager(mock_connector)
        
        manager._cache['secret-1'] = {'data': 'test1'}
        manager._cache['secret-2'] = {'data': 'test2'}
        manager.clear_cache()
        
        assert len(manager._cache) == 0


class TestInventoryConnector:
    """Test Inventory connector."""
    
    @pytest.mark.asyncio
    async def test_create_job(self):
        """Test creating collection job."""
        mock_identity = AsyncMock()
        connector = InventoryConnector('grpc://inventory:50051', mock_identity)
        
        job_id = await connector.create_collection_job(
            'collector-123',
            ['sa-1', 'sa-2']
        )
        
        assert job_id.startswith('job-')
    
    @pytest.mark.asyncio
    async def test_create_job_tasks(self):
        """Test creating job tasks."""
        mock_identity = AsyncMock()
        connector = InventoryConnector('grpc://inventory:50051', mock_identity)
        
        service_accounts = [
            {'service_account_id': 'sa-1', 'secret_id': 'secret-1'},
            {'service_account_id': 'sa-2', 'secret_id': 'secret-2'}
        ]
        
        task_ids = await connector.create_job_tasks('job-123', service_accounts)
        
        assert len(task_ids) == 2
    
    @pytest.mark.asyncio
    async def test_complete_job_task(self):
        """Test completing job task."""
        mock_identity = AsyncMock()
        connector = InventoryConnector('grpc://inventory:50051', mock_identity)
        
        # Create task first
        service_accounts = [
            {'service_account_id': 'sa-1', 'secret_id': 'secret-1'}
        ]
        task_ids = await connector.create_job_tasks('job-123', service_accounts)
        
        # Complete task
        stats = {
            'created_count': 100,
            'updated_count': 50,
            'deleted_count': 10,
            'error_count': 0
        }
        
        await connector.complete_job_task(task_ids[0], stats)
        
        task = connector._tasks[task_ids[0]]
        assert task.status == 'FINISHED'
        assert task.created_count == 100


class TestCostConnector:
    """Test Cost connector."""
    
    @pytest.mark.asyncio
    async def test_push_cost_data(self):
        """Test pushing cost data."""
        mock_identity = AsyncMock()
        connector = CostConnector('grpc://cost:50051', mock_identity)
        
        costs = [
            {
                'date': '2024-01-15',
                'cost': 12.50,
                'resource_id': 'vm-1'
            },
            {
                'date': '2024-01-15',
                'cost': 8.75,
                'resource_id': 'vm-2'
            }
        ]
        
        count = await connector.push_cost_data('ds-123', costs)
        assert count == 2
    
    def test_extract_cost_from_resource(self):
        """Test extracting cost from resource."""
        mock_identity = AsyncMock()
        connector = CostConnector('grpc://cost:50051', mock_identity)
        
        resource = {
            'id': 'vm-1',
            'data': {
                'cpu_cores': 4,
                'memory_gb': 8
            }
        }
        
        cost = connector.extract_cost_from_resource(
            resource,
            '2024-01-15'
        )
        
        assert cost['resource_id'] == 'vm-1'
        assert cost['cost'] > 0


class TestMonitoringConnector:
    """Test Monitoring connector."""
    
    @pytest.mark.asyncio
    async def test_push_metrics(self):
        """Test pushing metrics."""
        mock_identity = AsyncMock()
        connector = MonitoringConnector('grpc://monitoring:50051', mock_identity)
        
        metrics = {
            'cpu.utilization': 45.2,
            'memory.utilization': 62.5,
            'disk.read_iops': 150
        }
        
        await connector.push_metrics('vm-1', metrics)
        # Should not raise
    
    def test_extract_metrics_from_resource(self):
        """Test extracting metrics from resource."""
        mock_identity = AsyncMock()
        connector = MonitoringConnector('grpc://monitoring:50051', mock_identity)
        
        resource = {
            'id': 'vm-1',
            'data': {
                'cpu_cores': 8,
                'memory_gb': 16
            }
        }
        
        metrics = connector.extract_metrics_from_resource(resource)
        
        assert 'cpu.utilization' in metrics
        assert 'memory.utilization' in metrics
