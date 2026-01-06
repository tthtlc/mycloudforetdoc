"""
Identity API Connector

Handles authentication with CloudForet Identity service and secret management.
"""

import grpc
import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TokenInfo:
    """Token information."""
    token: str
    expires_at: datetime
    
    @property
    def is_valid(self) -> bool:
        """Check if token is still valid (with 5-min buffer)."""
        return datetime.utcnow() + timedelta(minutes=5) < self.expires_at


class IdentityConnector:
    """Handles interaction with CloudForet Identity service."""
    
    def __init__(self, identity_endpoint: str, plugin_api_key: str, domain_id: str = 'domain-default'):
        self.identity_endpoint = identity_endpoint.replace('grpc://', '').replace('grpcs://', '')
        self.plugin_api_key = plugin_api_key
        self.domain_id = domain_id
        self.token_info: Optional[TokenInfo] = None
        self._lock = asyncio.Lock()
        self._channel: Optional[grpc.aio.Channel] = None
    
    async def get_valid_token(self) -> str:
        """Get a valid API token, refreshing if necessary."""
        async with self._lock:
            # Check if current token is valid
            if self.token_info and self.token_info.is_valid:
                return self.token_info.token
            
            # Get new token
            await self._authenticate()
            return self.token_info.token
    
    async def _authenticate(self) -> None:
        """
        Authenticate with Identity service and get API token.
        
        gRPC Call: identity.v1.Auth.login
        """
        try:
            logger.info(f"Authenticating plugin with Identity service: {self.identity_endpoint}")
            
            # For development, we'll use a simple token validation
            # In production, this would call the actual Identity gRPC service
            
            self.token_info = TokenInfo(
                token=self.plugin_api_key,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            
            logger.info(f"Plugin authenticated. Token expires at: {self.token_info.expires_at}")
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise
    
    async def fetch_secret(self, secret_id: str) -> Dict[str, Any]:
        """
        Fetch and decrypt a secret from Identity service.
        
        gRPC Call: identity.v1.Secret.get
        
        Args:
            secret_id: The secret identifier
            
        Returns:
            Decrypted secret data dictionary
        """
        try:
            token = await self.get_valid_token()
            
            logger.debug(f"Fetching secret: {secret_id}")
            
            # In development, simulate secret retrieval
            # In production, this would call the actual Identity gRPC service
            
            # For now, return mock data
            mock_secret = {
                'secret_id': secret_id,
                'data': {
                    'nutanix_host': os.getenv('NUTANIX_HOST', 'prism.nutanix.local'),
                    'nutanix_port': int(os.getenv('NUTANIX_PORT', 9440)),
                    'nutanix_username': os.getenv('NUTANIX_USERNAME', 'admin'),
                    'nutanix_password': os.getenv('NUTANIX_PASSWORD', 'password'),
                    'verify_ssl': os.getenv('VERIFY_SSL', 'true').lower() == 'true',
                },
                'tags': {
                    'environment': 'production',
                    'provider': 'nutanix'
                }
            }
            
            logger.info(f"Secret retrieved: {secret_id}")
            return mock_secret
            
        except Exception as e:
            logger.error(f"Failed to fetch secret {secret_id}: {str(e)}")
            raise
    
    async def close(self) -> None:
        """Close gRPC channel."""
        if self._channel:
            await self._channel.close()


class SecretManager:
    """Manages secret caching and rotation."""
    
    def __init__(self, identity_connector: IdentityConnector):
        self.connector = identity_connector
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(hours=1)
    
    async def get_secret(self, secret_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get secret with caching.
        
        Args:
            secret_id: The secret identifier
            force_refresh: Force refresh from server
            
        Returns:
            Secret data dictionary
        """
        # Check cache
        if not force_refresh and secret_id in self._cache:
            if datetime.utcnow() < self._cache_expiry.get(secret_id, datetime.min):
                logger.debug(f"Using cached secret: {secret_id}")
                return self._cache[secret_id]
        
        # Fetch from server
        secret = await self.connector.fetch_secret(secret_id)
        
        # Cache result
        self._cache[secret_id] = secret
        self._cache_expiry[secret_id] = datetime.utcnow() + self._cache_ttl
        
        logger.debug(f"Cached secret: {secret_id}")
        return secret
    
    def clear_cache(self, secret_id: Optional[str] = None) -> None:
        """Clear cache."""
        if secret_id:
            self._cache.pop(secret_id, None)
            self._cache_expiry.pop(secret_id, None)
        else:
            self._cache.clear()
            self._cache_expiry.clear()
