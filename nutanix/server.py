"""
Nutanix Inventory Collector Plugin - Main Server

This is the entry point for the gRPC-based Nutanix collector plugin.
It implements the SpaceONE Collector interface to discover and collect
Nutanix resources (VMs, disks, networks, etc.).
"""

import os
import sys
import asyncio
import logging
import json
from concurrent import futures
from typing import Optional, Dict, Any
from datetime import datetime

import grpc
from spaceone.core.error import ERROR_UNKNOWN
from spaceone.core.service_loader import ServiceLoader
from spaceone.core.logger import set_log_level
from spaceone.core.auth.authenticator import Authenticator
from spaceone.core.utils import parse_grpc_error

# Import service implementations
from service.collector_service import CollectorService
from service.init_service import InitService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PluginServer:
    """Main plugin server managing gRPC services."""
    
    def __init__(self):
        self.port = os.getenv('PLUGIN_PORT', 50051)
        self.server: Optional[grpc.aio.Server] = None
        self.service_loader = ServiceLoader()
        
        # Configuration
        self.config = {
            'identity_endpoint': os.getenv('IDENTITY_ENDPOINT', 'grpc://identity:50051'),
            'inventory_endpoint': os.getenv('INVENTORY_ENDPOINT', 'grpc://inventory:50051'),
            'repository_endpoint': os.getenv('REPOSITORY_ENDPOINT', 'grpc://repository:50051'),
            'cost_endpoint': os.getenv('COST_ENDPOINT', 'grpc://cost-analysis:50051'),
            'monitoring_endpoint': os.getenv('MONITORING_ENDPOINT', 'grpc://monitoring:50051'),
            'notification_endpoint': os.getenv('NOTIFICATION_ENDPOINT', 'grpc://notification:50051'),
            'domain_id': os.getenv('DOMAIN_ID', 'domain-default'),
            'workspace_id': os.getenv('WORKSPACE_ID', 'workspace-default'),
            'plugin_api_key': os.getenv('PLUGIN_API_KEY', ''),
        }
        
        # Set log level
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        set_log_level(log_level)
        logger.info(f"Plugin initialized with log level: {log_level}")
    
    async def initialize(self) -> None:
        """Initialize plugin services."""
        try:
            logger.info("Initializing plugin services...")
            
            # Validate configuration
            self._validate_config()
            
            # Initialize services
            self.init_service = InitService(self.config)
            self.collector_service = CollectorService(self.config)
            
            logger.info("Plugin services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize plugin: {str(e)}", exc_info=True)
            raise
    
    def _validate_config(self) -> None:
        """Validate required configuration."""
        if not self.config['plugin_api_key']:
            raise ValueError("PLUGIN_API_KEY environment variable not set")
    
    async def run(self) -> None:
        """Start the gRPC server."""
        try:
            # Create server
            self.server = grpc.aio.server(
                futures.ThreadPoolExecutor(max_workers=10),
                interceptors=[]
            )
            
            # Add services
            from spaceone.core.pygrpc import serve_impl
            
            serve_impl(
                self.server,
                [
                    ('spaceone.inventory.plugin.collector.Collector', self.collector_service),
                    ('spaceone.core.plugin.Plugin', self.init_service),
                ]
            )
            
            # Add gRPC health check
            from grpc_health.v1 import health_pb2_grpc
            from grpc_health.v1 import health_pb2
            
            health_servicer = HealthServicer()
            health_pb2_grpc.add_HealthStub(self.server, health_servicer)
            
            # Bind port
            self.server.add_insecure_port(f'0.0.0.0:{self.port}')
            
            # Start server
            await self.server.start()
            logger.info(f"✅ Plugin server started on port {self.port}")
            
            # Wait for termination
            await self.server.wait_for_termination()
            
        except Exception as e:
            logger.error(f"Server error: {str(e)}", exc_info=True)
            raise
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the server."""
        try:
            logger.info("Shutting down plugin server...")
            if self.server:
                await self.server.stop(0)
            logger.info("Plugin server shut down successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")


class HealthServicer:
    """gRPC Health Check Servicer."""
    
    async def Check(self, request, context):
        """Health check endpoint."""
        from grpc_health.v1 import health_pb2
        
        return health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.SERVING
        )
    
    async def Watch(self, request, context):
        """Health check watch endpoint."""
        from grpc_health.v1 import health_pb2
        
        yield health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.SERVING
        )


async def main():
    """Main entry point."""
    server = PluginServer()
    
    try:
        await server.initialize()
        await server.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        await server.shutdown()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    # Run async main
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped")
        sys.exit(0)
