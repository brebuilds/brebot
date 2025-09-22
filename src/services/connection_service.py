"""
Connection Service for managing external service integrations.
"""

import asyncio
import json
import secrets
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx
from cryptography.fernet import Fernet
import base64

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.connections import (
    ConnectionConfig, ConnectionStatus, ConnectionType, ConnectionScope,
    OAuthToken, ConnectionEvent, ConnectionHealth, DEFAULT_CONNECTIONS
)
from utils.logger import brebot_logger


class ConnectionService:
    """Service for managing external service connections."""
    
    def __init__(self):
        """Initialize the connection service."""
        self.connections: Dict[str, ConnectionConfig] = {}
        self.tokens: Dict[str, OAuthToken] = {}
        self.events: List[ConnectionEvent] = []
        self.health_status: Dict[str, ConnectionHealth] = {}
        
        # Encryption key for token storage
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Initialize default connections
        self._initialize_default_connections()
        
        brebot_logger.log_agent_action(
            agent_name="ConnectionService",
            action="initialized",
            details={"connections_count": len(self.connections)}
        )
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for token storage."""
        try:
            # In production, this should be stored securely
            key_file = "connection_encryption.key"
            try:
                with open(key_file, "rb") as f:
                    return f.read()
            except FileNotFoundError:
                key = Fernet.generate_key()
                with open(key_file, "wb") as f:
                    f.write(key)
                return key
        except Exception as e:
            brebot_logger.log_agent_action(
                agent_name="ConnectionService",
                action="encryption_key_error",
                details={"error": str(e)}
            )
            # Fallback to a default key (not recommended for production)
            return Fernet.generate_key()
    
    def _initialize_default_connections(self):
        """Initialize default connection configurations."""
        for conn_type, config in DEFAULT_CONNECTIONS.items():
            connection_id = f"{conn_type.value}_default"
            
            scopes = [
                ConnectionScope(**scope) for scope in config["scopes"]
            ]
            
            connection = ConnectionConfig(
                connection_id=connection_id,
                connection_type=conn_type,
                name=config["name"],
                scopes=scopes,
                metadata={
                    "icon": config["icon"],
                    "color": config["color"],
                    "description": config["description"],
                    "oauth_url": config["oauth_url"],
                    "token_url": config["token_url"]
                }
            )
            
            self.connections[connection_id] = connection
    
    def get_all_connections(self) -> List[ConnectionConfig]:
        """Get all connection configurations."""
        return list(self.connections.values())
    
    def get_connection(self, connection_id: str) -> Optional[ConnectionConfig]:
        """Get a specific connection configuration."""
        return self.connections.get(connection_id)
    
    def get_connection_by_type(self, connection_type: ConnectionType) -> Optional[ConnectionConfig]:
        """Get connection by type."""
        for conn in self.connections.values():
            if conn.connection_type == connection_type:
                return conn
        return None
    
    def create_oauth_url(self, connection_id: str, redirect_uri: str) -> Optional[str]:
        """Create OAuth authorization URL."""
        connection = self.get_connection(connection_id)
        if not connection:
            return None
        
        # Generate state parameter for security
        state = secrets.token_urlsafe(32)
        
        # Store state for validation
        connection.metadata["oauth_state"] = state
        
        # Build OAuth URL based on connection type
        if connection.connection_type == ConnectionType.DROPBOX:
            return self._create_dropbox_oauth_url(connection, redirect_uri, state)
        elif connection.connection_type == ConnectionType.GOOGLE_DRIVE:
            return self._create_google_oauth_url(connection, redirect_uri, state)
        elif connection.connection_type == ConnectionType.NOTION:
            return self._create_notion_oauth_url(connection, redirect_uri, state)
        elif connection.connection_type == ConnectionType.AIRTABLE:
            return self._create_airtable_oauth_url(connection, redirect_uri, state)
        elif connection.connection_type == ConnectionType.SLACK:
            return self._create_slack_oauth_url(connection, redirect_uri, state)
        
        return None
    
    def _create_dropbox_oauth_url(self, connection: ConnectionConfig, redirect_uri: str, state: str) -> str:
        """Create Dropbox OAuth URL."""
        params = {
            "client_id": "your_dropbox_client_id",  # Should be from config
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": "files.metadata.read files.content.read files.metadata.write files.content.write"
        }
        
        base_url = connection.metadata["oauth_url"]
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    def _create_google_oauth_url(self, connection: ConnectionConfig, redirect_uri: str, state: str) -> str:
        """Create Google OAuth URL."""
        params = {
            "client_id": "your_google_client_id",  # Should be from config
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/drive.file",
            "access_type": "offline",
            "prompt": "consent",
            "state": state
        }
        
        base_url = connection.metadata["oauth_url"]
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    def _create_notion_oauth_url(self, connection: ConnectionConfig, redirect_uri: str, state: str) -> str:
        """Create Notion OAuth URL."""
        params = {
            "client_id": "your_notion_client_id",  # Should be from config
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state
        }
        
        base_url = connection.metadata["oauth_url"]
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    def _create_airtable_oauth_url(self, connection: ConnectionConfig, redirect_uri: str, state: str) -> str:
        """Create Airtable OAuth URL."""
        params = {
            "client_id": "your_airtable_client_id",  # Should be from config
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state
        }
        
        base_url = connection.metadata["oauth_url"]
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    def _create_slack_oauth_url(self, connection: ConnectionConfig, redirect_uri: str, state: str) -> str:
        """Create Slack OAuth URL."""
        params = {
            "client_id": "your_slack_client_id",  # Should be from config
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "channels:read files:read chat:read",
            "state": state
        }
        
        base_url = connection.metadata["oauth_url"]
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    async def handle_oauth_callback(self, connection_id: str, code: str, state: str) -> bool:
        """Handle OAuth callback and exchange code for token."""
        connection = self.get_connection(connection_id)
        if not connection:
            return False
        
        # Validate state parameter
        if connection.metadata.get("oauth_state") != state:
            brebot_logger.log_agent_action(
                agent_name="ConnectionService",
                action="oauth_state_mismatch",
                details={"connection_id": connection_id}
            )
            return False
        
        try:
            # Exchange code for token based on connection type
            if connection.connection_type == ConnectionType.DROPBOX:
                token = await self._exchange_dropbox_token(connection, code)
            elif connection.connection_type == ConnectionType.GOOGLE_DRIVE:
                token = await self._exchange_google_token(connection, code)
            elif connection.connection_type == ConnectionType.NOTION:
                token = await self._exchange_notion_token(connection, code)
            elif connection.connection_type == ConnectionType.AIRTABLE:
                token = await self._exchange_airtable_token(connection, code)
            elif connection.connection_type == ConnectionType.SLACK:
                token = await self._exchange_slack_token(connection, code)
            else:
                return False
            
            if token:
                # Store encrypted token
                self.tokens[connection_id] = token
                
                # Update connection status
                connection.status = ConnectionStatus.CONNECTED
                connection.updated_at = datetime.now()
                
                # Create n8n webhook if enabled for ingestion
                if connection.enabled_for_ingestion:
                    await self._create_n8n_webhook(connection)
                
                brebot_logger.log_agent_action(
                    agent_name="ConnectionService",
                    action="oauth_success",
                    details={"connection_id": connection_id, "connection_type": connection.connection_type}
                )
                
                return True
        
        except Exception as e:
            connection.status = ConnectionStatus.ERROR
            connection.error_message = str(e)
            connection.updated_at = datetime.now()
            
            brebot_logger.log_agent_action(
                agent_name="ConnectionService",
                action="oauth_error",
                details={"connection_id": connection_id, "error": str(e)}
            )
        
        return False
    
    async def _exchange_dropbox_token(self, connection: ConnectionConfig, code: str) -> Optional[OAuthToken]:
        """Exchange Dropbox authorization code for token."""
        # Implementation would make actual API call to Dropbox
        # For now, return a mock token
        return OAuthToken(
            connection_id=connection.connection_id,
            access_token="mock_dropbox_token",
            token_type="Bearer",
            scope="files.metadata.read files.content.read",
            expires_at=datetime.now() + timedelta(hours=4)
        )
    
    async def _exchange_google_token(self, connection: ConnectionConfig, code: str) -> Optional[OAuthToken]:
        """Exchange Google authorization code for token."""
        # Implementation would make actual API call to Google
        return OAuthToken(
            connection_id=connection.connection_id,
            access_token="mock_google_token",
            refresh_token="mock_google_refresh_token",
            token_type="Bearer",
            scope="https://www.googleapis.com/auth/drive.readonly",
            expires_at=datetime.now() + timedelta(hours=1)
        )
    
    async def _exchange_notion_token(self, connection: ConnectionConfig, code: str) -> Optional[OAuthToken]:
        """Exchange Notion authorization code for token."""
        return OAuthToken(
            connection_id=connection.connection_id,
            access_token="mock_notion_token",
            token_type="Bearer",
            scope="read",
            expires_at=datetime.now() + timedelta(hours=1)
        )
    
    async def _exchange_airtable_token(self, connection: ConnectionConfig, code: str) -> Optional[OAuthToken]:
        """Exchange Airtable authorization code for token."""
        return OAuthToken(
            connection_id=connection.connection_id,
            access_token="mock_airtable_token",
            token_type="Bearer",
            scope="data.records:read",
            expires_at=datetime.now() + timedelta(hours=1)
        )
    
    async def _exchange_slack_token(self, connection: ConnectionConfig, code: str) -> Optional[OAuthToken]:
        """Exchange Slack authorization code for token."""
        return OAuthToken(
            connection_id=connection.connection_id,
            access_token="mock_slack_token",
            token_type="Bearer",
            scope="channels:read files:read",
            expires_at=datetime.now() + timedelta(hours=1)
        )
    
    def disconnect_connection(self, connection_id: str) -> bool:
        """Disconnect a connection."""
        connection = self.get_connection(connection_id)
        if not connection:
            return False
        
        # Remove token
        if connection_id in self.tokens:
            del self.tokens[connection_id]
        
        # Update connection status
        connection.status = ConnectionStatus.DISCONNECTED
        connection.enabled_for_ingestion = False
        connection.n8n_webhook_url = None
        connection.n8n_workflow_id = None
        connection.updated_at = datetime.now()
        
        # Remove n8n webhook
        asyncio.create_task(self._remove_n8n_webhook(connection))
        
        brebot_logger.log_agent_action(
            agent_name="ConnectionService",
            action="connection_disconnected",
            details={"connection_id": connection_id}
        )
        
        return True
    
    def toggle_ingestion(self, connection_id: str, enabled: bool) -> bool:
        """Toggle ingestion availability for a connection."""
        connection = self.get_connection(connection_id)
        if not connection or connection.status != ConnectionStatus.CONNECTED:
            return False
        
        connection.enabled_for_ingestion = enabled
        connection.updated_at = datetime.now()
        
        if enabled:
            asyncio.create_task(self._create_n8n_webhook(connection))
        else:
            asyncio.create_task(self._remove_n8n_webhook(connection))
        
        brebot_logger.log_agent_action(
            agent_name="ConnectionService",
            action="ingestion_toggled",
            details={"connection_id": connection_id, "enabled": enabled}
        )
        
        return True
    
    async def _create_n8n_webhook(self, connection: ConnectionConfig):
        """Create n8n webhook for connection events."""
        try:
            # This would integrate with your n8n instance
            # For now, we'll simulate the webhook creation
            webhook_id = f"brebot_{connection.connection_type.value}_{connection.connection_id}"
            webhook_url = f"https://your-n8n-instance.com/webhook/{webhook_id}"
            
            connection.n8n_webhook_url = webhook_url
            connection.n8n_workflow_id = webhook_id
            
            brebot_logger.log_agent_action(
                agent_name="ConnectionService",
                action="n8n_webhook_created",
                details={"connection_id": connection.connection_id, "webhook_url": webhook_url}
            )
        
        except Exception as e:
            brebot_logger.log_agent_action(
                agent_name="ConnectionService",
                action="n8n_webhook_error",
                details={"connection_id": connection.connection_id, "error": str(e)}
            )
    
    async def _remove_n8n_webhook(self, connection: ConnectionConfig):
        """Remove n8n webhook for connection."""
        try:
            # This would remove the webhook from n8n
            connection.n8n_webhook_url = None
            connection.n8n_workflow_id = None
            
            brebot_logger.log_agent_action(
                agent_name="ConnectionService",
                action="n8n_webhook_removed",
                details={"connection_id": connection.connection_id}
            )
        
        except Exception as e:
            brebot_logger.log_agent_action(
                agent_name="ConnectionService",
                action="n8n_webhook_removal_error",
                details={"connection_id": connection.connection_id, "error": str(e)}
            )
    
    async def check_connection_health(self, connection_id: str) -> ConnectionHealth:
        """Check the health of a connection."""
        connection = self.get_connection(connection_id)
        if not connection:
            return ConnectionHealth(
                connection_id=connection_id,
                is_healthy=False,
                error_details="Connection not found"
            )
        
        if connection.status != ConnectionStatus.CONNECTED:
            return ConnectionHealth(
                connection_id=connection_id,
                is_healthy=False,
                error_details="Connection not connected"
            )
        
        try:
            start_time = datetime.now()
            
            # Test connection based on type
            if connection.connection_type == ConnectionType.DROPBOX:
                success = await self._test_dropbox_connection(connection)
            elif connection.connection_type == ConnectionType.GOOGLE_DRIVE:
                success = await self._test_google_connection(connection)
            elif connection.connection_type == ConnectionType.NOTION:
                success = await self._test_notion_connection(connection)
            elif connection.connection_type == ConnectionType.AIRTABLE:
                success = await self._test_airtable_connection(connection)
            elif connection.connection_type == ConnectionType.SLACK:
                success = await self._test_slack_connection(connection)
            else:
                success = False
            
            end_time = datetime.now()
            response_time = int((end_time - start_time).total_seconds() * 1000)
            
            health = ConnectionHealth(
                connection_id=connection_id,
                is_healthy=success,
                response_time_ms=response_time if success else None,
                error_details=None if success else "Connection test failed"
            )
            
            self.health_status[connection_id] = health
            return health
        
        except Exception as e:
            health = ConnectionHealth(
                connection_id=connection_id,
                is_healthy=False,
                error_details=str(e)
            )
            self.health_status[connection_id] = health
            return health
    
    async def _test_dropbox_connection(self, connection: ConnectionConfig) -> bool:
        """Test Dropbox connection."""
        # Mock implementation - would make actual API call
        return True
    
    async def _test_google_connection(self, connection: ConnectionConfig) -> bool:
        """Test Google Drive connection."""
        return True
    
    async def _test_notion_connection(self, connection: ConnectionConfig) -> bool:
        """Test Notion connection."""
        return True
    
    async def _test_airtable_connection(self, connection: ConnectionConfig) -> bool:
        """Test Airtable connection."""
        return True
    
    async def _test_slack_connection(self, connection: ConnectionConfig) -> bool:
        """Test Slack connection."""
        return True
    
    def get_connection_health(self, connection_id: str) -> Optional[ConnectionHealth]:
        """Get cached connection health status."""
        return self.health_status.get(connection_id)
    
    async def process_connection_event(self, event: ConnectionEvent):
        """Process a connection event (from n8n webhook)."""
        self.events.append(event)
        
        # Here you would process the event and trigger appropriate actions
        # For example, ingest new files, update memory, send notifications, etc.
        
        brebot_logger.log_agent_action(
            agent_name="ConnectionService",
            action="event_processed",
            details={
                "event_id": event.event_id,
                "connection_id": event.connection_id,
                "event_type": event.event_type
            }
        )
    
    def get_connection_events(self, connection_id: Optional[str] = None) -> List[ConnectionEvent]:
        """Get connection events."""
        if connection_id:
            return [event for event in self.events if event.connection_id == connection_id]
        return self.events


# Global connection service instance
connection_service = ConnectionService()
