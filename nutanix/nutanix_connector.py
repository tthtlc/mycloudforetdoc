"""
Nutanix Prism Central Connector

Handles communication with Nutanix Prism Central API to discover and collect
VM, disk, and network resources.
"""

import logging
import httpx
import asyncio
from typing import Dict, List, Any, AsyncGenerator, Optional
from urllib.parse import urljoin
from datetime import datetime

logger = logging.getLogger(__name__)


class NutanixConnector:
    """Handles interaction with Nutanix Prism Central API."""
    
    def __init__(self, 
                 host: str,
                 username: str,
                 password: str,
                 port: int = 9440,
                 verify_ssl: bool = True):
        """
        Initialize Nutanix connector.
        
        Args:
            host: Prism Central hostname/IP
            username: API username
            password: API password
            port: API port (default 9440)
            verify_ssl: Verify SSL certificates
        """
        self.host = host
        self.port = port
        self.base_url = f"https://{host}:{port}/api/nutanix/v3"
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self._client: Optional[httpx.AsyncClient] = None
    
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                auth=(self.username, self.password),
                verify=self.verify_ssl,
                timeout=30.0,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
        return self._client
    
    async def test_connection(self) -> bool:
        """
        Test connection to Nutanix Prism Central.
        
        Returns:
            True if connection successful
        """
        try:
            logger.info(f"Testing connection to Nutanix: {self.host}:{self.port}")
            
            client = await self.get_client()
            response = await client.get(
                urljoin(self.base_url, "/clusters"),
                params={"length": 1}
            )
            
            if response.status_code == 200:
                logger.info("✅ Connection to Nutanix successful")
                return True
            else:
                logger.error(f"Connection failed with status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Nutanix: {str(e)}")
            return False
    
    async def list_vms(self, 
                      cluster_name: Optional[str] = None,
                      limit: int = 500) -> AsyncGenerator[Dict[str, Any], None]:
        """
        List all VMs from Prism Central with pagination.
        
        gRPC Call: [Nutanix API] GET /vms
        
        Args:
            cluster_name: Optional filter by cluster name
            limit: Batch size for pagination
            
        Yields:
            VM dictionaries
        """
        try:
            logger.info("Starting VM collection...")
            
            offset = 0
            total_collected = 0
            
            while True:
                try:
                    response_data = await self._fetch_vms(offset, limit, cluster_name)
                    
                    vms = response_data.get('entities', [])
                    if not vms:
                        break
                    
                    for vm in vms:
                        total_collected += 1
                        yield vm
                        
                        if total_collected % 100 == 0:
                            logger.debug(f"Collected {total_collected} VMs so far")
                    
                    # Check if there are more results
                    metadata = response_data.get('metadata', {})
                    if metadata.get('offset', 0) + metadata.get('length', 0) >= metadata.get('total_matches', 0):
                        break
                    
                    offset += limit
                    await asyncio.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Error fetching VMs: {str(e)}")
                    raise
            
            logger.info(f"VM collection completed. Total: {total_collected}")
            
        except Exception as e:
            logger.error(f"Failed to list VMs: {str(e)}")
            raise
    
    async def _fetch_vms(self, 
                        offset: int,
                        limit: int,
                        cluster_name: Optional[str] = None) -> Dict[str, Any]:
        """Fetch a batch of VMs from API."""
        try:
            client = await self.get_client()
            
            payload = {
                "kind": "vm",
                "offset": offset,
                "length": limit
            }
            
            if cluster_name:
                payload["filter"] = f"cluster_name=={cluster_name}"
            
            response = await client.post(
                urljoin(self.base_url, "/vms/list"),
                json=payload
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to fetch VMs batch: {str(e)}")
            raise
    
    async def list_clusters(self) -> List[Dict[str, Any]]:
        """
        List all clusters in Prism Central.
        
        Returns:
            List of cluster dictionaries
        """
        try:
            logger.info("Fetching cluster list...")
            
            client = await self.get_client()
            response = await client.get(
                urljoin(self.base_url, "/clusters"),
                params={"length": 1000}
            )
            
            response.raise_for_status()
            data = response.json()
            
            clusters = data.get('entities', [])
            logger.info(f"Found {len(clusters)} clusters")
            
            return clusters
            
        except Exception as e:
            logger.error(f"Failed to list clusters: {str(e)}")
            raise
    
    def normalize_vm(self, vm_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Nutanix VM data to CloudForet resource format.
        
        Args:
            vm_data: Raw VM data from Nutanix API
            
        Returns:
            Normalized resource dictionary
        """
        try:
            spec = vm_data.get('spec', {})
            metadata = vm_data.get('metadata', {})
            resources = spec.get('resources', {})
            
            # Extract resource configuration
            vcpu_count = 0
            memory_gb = 0
            disk_total_gb = 0
            
            vcpu_per_socket = resources.get('vcpu_per_socket', 0)
            num_sockets = resources.get('num_sockets', 0)
            if vcpu_per_socket and num_sockets:
                vcpu_count = vcpu_per_socket * num_sockets
            
            memory_mib = resources.get('memory_size_mib', 0)
            if memory_mib:
                memory_gb = memory_mib / 1024
            
            disk_list = resources.get('disk_list', [])
            for disk in disk_list:
                disk_size_bytes = disk.get('disk_size_bytes', 0)
                disk_total_gb += disk_size_bytes / (1024**3)
            
            # Get cluster reference
            cluster_reference = spec.get('cluster_reference', {})
            cluster_name = cluster_reference.get('name', 'Unknown')
            
            # Power state
            power_state = resources.get('power_state', 'OFF')
            
            return {
                'type': 'compute.Instance',
                'id': metadata.get('uuid', ''),
                'name': spec.get('name', ''),
                'account_id': self.host,
                'data': {
                    'state': 'ON' if power_state == 'ON' else 'OFF',
                    'power_state': power_state,
                    'cpu_cores': vcpu_count,
                    'memory_gb': memory_gb,
                    'disk_total_gb': disk_total_gb,
                    'cluster': cluster_name,
                    'cluster_uuid': cluster_reference.get('uuid', ''),
                    'created_at': metadata.get('creation_time', ''),
                    'updated_at': metadata.get('update_time', ''),
                    'nutanix_uuid': metadata.get('uuid', ''),
                    'hypervisor_type': resources.get('hypervisor_type', 'AHV'),
                    'num_vcpu_per_socket': vcpu_per_socket,
                    'num_sockets': num_sockets,
                    'numa_node_count': resources.get('numa_node_count', 0),
                    'nic_count': len(resources.get('nic_list', [])),
                    'disk_count': len(disk_list),
                    'gpu_count': len(resources.get('gpu_list', [])),
                },
                'tags': {
                    'environment': 'nutanix',
                    'cluster': cluster_name,
                    'hypervisor': resources.get('hypervisor_type', 'AHV'),
                },
                'reference': {
                    'resource_id': metadata.get('uuid', ''),
                    'external_link': f"https://{self.host}/console/#page/vm_details/{metadata.get('uuid', '')}"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to normalize VM: {str(e)}")
            raise
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            logger.info("Nutanix connector closed")


class NutanixResourceCollector:
    """Collects resources from Nutanix and normalizes them."""
    
    def __init__(self, nutanix_connector: NutanixConnector):
        self.connector = nutanix_connector
    
    async def collect_all_resources(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Collect all resources from Nutanix.
        
        Yields:
            Normalized resource dictionaries
        """
        try:
            logger.info("Starting resource collection from Nutanix...")
            
            # Collect VMs
            resource_count = 0
            async for vm in self.connector.list_vms():
                try:
                    normalized = self.connector.normalize_vm(vm)
                    resource_count += 1
                    yield normalized
                    
                except Exception as e:
                    logger.warning(f"Failed to normalize VM: {str(e)}")
                    continue
            
            logger.info(f"Resource collection completed. Total: {resource_count}")
            
        except Exception as e:
            logger.error(f"Failed to collect resources: {str(e)}")
            raise
