"""
Integration Manager for BreBot Platform Integrations
Centralizes management of all platform connections with comprehensive logging
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from utils.logger import brebot_logger
from services.activity_logger import (
    initialize_activity_logger, 
    get_activity_logger, 
    log_platform_activity, 
    Platform, 
    ActivityType
)

# Import all platform services
from services.dropbox_service import initialize_dropbox_service, get_dropbox_service
from services.airtable_service import initialize_airtable_service, get_airtable_service
from services.etsy_service import initialize_etsy_service, get_etsy_service
from services.printify_service import initialize_printify_service, get_printify_service
from services.n8n_service import initialize_n8n_service, get_n8n_service


@dataclass
class IntegrationConfig:
    """Configuration for a platform integration."""
    platform: str
    enabled: bool
    api_key: Optional[str] = None
    additional_config: Dict[str, Any] = None
    last_sync: Optional[datetime] = None
    health_status: str = "unknown"
    error_message: Optional[str] = None


class IntegrationStatus(Enum):
    """Integration health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"


class IntegrationManager:
    """Manages all platform integrations for BreBot."""
    
    def __init__(self):
        """Initialize integration manager."""
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.activity_logger = None
        
        # Initialize activity logger
        self._initialize_activity_logging()
        
        # Load configuration from environment
        self._load_configurations()
        
        brebot_logger.log_agent_action(
            agent_name="IntegrationManager",
            action="initialized",
            details={"platforms_configured": len(self.integrations)}
        )
    
    def _initialize_activity_logging(self):
        """Initialize comprehensive activity logging."""
        try:
            self.activity_logger = initialize_activity_logger()
            brebot_logger.log_agent_action(
                agent_name="IntegrationManager",
                action="activity_logging_initialized",
                details={"status": "success"}
            )
        except Exception as e:
            brebot_logger.log_error(e, context="IntegrationManager._initialize_activity_logging")
    
    def _load_configurations(self):
        """Load integration configurations from environment variables."""
        # Dropbox configuration
        dropbox_token = os.getenv("DROPBOX_ACCESS_TOKEN")
        if dropbox_token:
            self.integrations["dropbox"] = IntegrationConfig(
                platform="dropbox",
                enabled=True,
                api_key=dropbox_token,
                health_status="not_tested"
            )
        
        # Airtable configuration
        airtable_key = os.getenv("AIRTABLE_API_KEY")
        if airtable_key:
            self.integrations["airtable"] = IntegrationConfig(
                platform="airtable",
                enabled=True,
                api_key=airtable_key,
                health_status="not_tested"
            )
        
        # Etsy configuration
        etsy_key = os.getenv("ETSY_API_KEY")
        etsy_shop_id = os.getenv("ETSY_SHOP_ID")
        if etsy_key:
            self.integrations["etsy"] = IntegrationConfig(
                platform="etsy",
                enabled=True,
                api_key=etsy_key,
                additional_config={"shop_id": int(etsy_shop_id) if etsy_shop_id else None},
                health_status="not_tested"
            )
        
        # Printify configuration
        printify_token = os.getenv("PRINTIFY_API_TOKEN")
        printify_shop_id = os.getenv("PRINTIFY_SHOP_ID")
        if printify_token:
            self.integrations["printify"] = IntegrationConfig(
                platform="printify",
                enabled=True,
                api_key=printify_token,
                additional_config={"shop_id": int(printify_shop_id) if printify_shop_id else None},
                health_status="not_tested"
            )
        
        # n8n configuration
        n8n_url = os.getenv("N8N_BASE_URL")
        n8n_key = os.getenv("N8N_API_KEY")
        if n8n_url:
            self.integrations["n8n"] = IntegrationConfig(
                platform="n8n",
                enabled=True,
                api_key=n8n_key,
                additional_config={"base_url": n8n_url},
                health_status="not_tested"
            )
        
        # Email configuration (placeholder for future implementation)
        email_config = {
            "gmail_credentials": os.getenv("GMAIL_CREDENTIALS_PATH"),
            "outlook_client_id": os.getenv("OUTLOOK_CLIENT_ID"),
            "outlook_client_secret": os.getenv("OUTLOOK_CLIENT_SECRET")
        }
        if any(email_config.values()):
            self.integrations["email"] = IntegrationConfig(
                platform="email",
                enabled=False,  # Disabled until implementation
                additional_config=email_config,
                health_status="not_implemented"
            )
        
        # Browser automation configuration (placeholder)
        if os.getenv("ENABLE_BROWSER_AUTOMATION", "false").lower() == "true":
            self.integrations["browser"] = IntegrationConfig(
                platform="browser",
                enabled=False,  # Disabled until implementation
                health_status="not_implemented"
            )
        
        # Desktop file access (always available)
        self.integrations["desktop"] = IntegrationConfig(
            platform="desktop",
            enabled=True,
            health_status="healthy"
        )
        
        brebot_logger.log_agent_action(
            agent_name="IntegrationManager",
            action="configurations_loaded",
            details={
                "configured_platforms": list(self.integrations.keys()),
                "enabled_platforms": [p for p, c in self.integrations.items() if c.enabled]
            }
        )
    
    async def initialize_services(self):
        """Initialize all configured platform services."""
        initialized_services = []
        
        for platform, config in self.integrations.items():
            if not config.enabled:
                continue
            
            try:
                if platform == "dropbox" and config.api_key:
                    initialize_dropbox_service(config.api_key)
                    initialized_services.append(platform)
                
                elif platform == "airtable" and config.api_key:
                    initialize_airtable_service(config.api_key)
                    initialized_services.append(platform)
                
                elif platform == "etsy" and config.api_key:
                    shop_id = config.additional_config.get("shop_id") if config.additional_config else None
                    initialize_etsy_service(config.api_key, shop_id)
                    initialized_services.append(platform)
                
                elif platform == "printify" and config.api_key:
                    shop_id = config.additional_config.get("shop_id") if config.additional_config else None
                    initialize_printify_service(config.api_key, shop_id)
                    initialized_services.append(platform)
                
                elif platform == "n8n" and config.additional_config:
                    base_url = config.additional_config.get("base_url")
                    if base_url:
                        initialize_n8n_service(base_url, config.api_key)
                        initialized_services.append(platform)
                
                # Update health status
                config.health_status = "initialized"
                
                await log_platform_activity(
                    platform=Platform.SYSTEM,
                    activity_type=ActivityType.CREATE,
                    agent_name="IntegrationManager",
                    description=f"Initialized {platform} service",
                    details={"platform": platform, "status": "success"}
                )
                
            except Exception as e:
                config.health_status = "initialization_failed"
                config.error_message = str(e)
                
                await log_platform_activity(
                    platform=Platform.SYSTEM,
                    activity_type=ActivityType.CREATE,
                    agent_name="IntegrationManager",
                    description=f"Failed to initialize {platform} service",
                    success=False,
                    error_message=str(e),
                    details={"platform": platform}
                )
                
                brebot_logger.log_error(e, context=f"IntegrationManager.initialize_services.{platform}")
        
        brebot_logger.log_agent_action(
            agent_name="IntegrationManager",
            action="services_initialized",
            details={
                "initialized_services": initialized_services,
                "total_configured": len(self.integrations),
                "total_initialized": len(initialized_services)
            }
        )
        
        return initialized_services
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health checks on all integrations."""
        health_results = {}
        
        for platform, config in self.integrations.items():
            if not config.enabled:
                health_results[platform] = {
                    "status": IntegrationStatus.DISABLED.value,
                    "message": "Integration disabled",
                    "last_checked": datetime.now().isoformat()
                }
                continue
            
            try:
                await log_platform_activity(
                    platform=Platform.SYSTEM,
                    activity_type=ActivityType.READ,
                    agent_name="IntegrationManager",
                    description=f"Health checking {platform}",
                    details={"platform": platform}
                )
                
                health_result = await self._health_check_platform(platform, config)
                health_results[platform] = health_result
                
                # Update config with health status
                config.health_status = health_result["status"]
                config.last_sync = datetime.now()
                
            except Exception as e:
                health_results[platform] = {
                    "status": IntegrationStatus.UNHEALTHY.value,
                    "message": str(e),
                    "last_checked": datetime.now().isoformat()
                }
                
                config.health_status = "unhealthy"
                config.error_message = str(e)
                
                await log_platform_activity(
                    platform=Platform.SYSTEM,
                    activity_type=ActivityType.READ,
                    agent_name="IntegrationManager",
                    description=f"Health check failed for {platform}",
                    success=False,
                    error_message=str(e),
                    details={"platform": platform}
                )
        
        await log_platform_activity(
            platform=Platform.SYSTEM,
            activity_type=ActivityType.READ,
            agent_name="IntegrationManager",
            description="Completed health check for all integrations",
            details={
                "platforms_checked": len(health_results),
                "healthy_platforms": len([r for r in health_results.values() if r["status"] == "healthy"])
            }
        )
        
        return health_results
    
    async def _health_check_platform(self, platform: str, config: IntegrationConfig) -> Dict[str, Any]:
        """Perform health check for a specific platform."""
        if platform == "dropbox":
            service = get_dropbox_service()
            if service:
                try:
                    account_info = await service.get_account_info("IntegrationManager")
                    return {
                        "status": IntegrationStatus.HEALTHY.value,
                        "message": f"Connected to account: {account_info.get('name', 'Unknown')}",
                        "last_checked": datetime.now().isoformat(),
                        "details": {
                            "account_email": account_info.get("email"),
                            "used_space": account_info.get("used_space"),
                            "account_type": account_info.get("account_type")
                        }
                    }
                except Exception as e:
                    return {
                        "status": IntegrationStatus.UNHEALTHY.value,
                        "message": f"Health check failed: {str(e)}",
                        "last_checked": datetime.now().isoformat()
                    }
        
        elif platform == "airtable":
            service = get_airtable_service()
            if service:
                try:
                    bases = await service.list_bases("IntegrationManager")
                    return {
                        "status": IntegrationStatus.HEALTHY.value,
                        "message": f"Connected to {len(bases)} bases",
                        "last_checked": datetime.now().isoformat(),
                        "details": {
                            "bases_count": len(bases),
                            "base_names": [base.name for base in bases[:5]]  # First 5 base names
                        }
                    }
                except Exception as e:
                    return {
                        "status": IntegrationStatus.UNHEALTHY.value,
                        "message": f"Health check failed: {str(e)}",
                        "last_checked": datetime.now().isoformat()
                    }
        
        elif platform == "etsy":
            service = get_etsy_service()
            if service:
                try:
                    shop_info = await service.get_shop_info(agent_name="IntegrationManager")
                    return {
                        "status": IntegrationStatus.HEALTHY.value,
                        "message": f"Connected to shop: {shop_info.shop_name}",
                        "last_checked": datetime.now().isoformat(),
                        "details": {
                            "shop_name": shop_info.shop_name,
                            "shop_id": shop_info.shop_id,
                            "active_listings": shop_info.listing_active_count,
                            "currency": shop_info.currency_code
                        }
                    }
                except Exception as e:
                    return {
                        "status": IntegrationStatus.UNHEALTHY.value,
                        "message": f"Health check failed: {str(e)}",
                        "last_checked": datetime.now().isoformat()
                    }
        
        elif platform == "printify":
            service = get_printify_service()
            if service:
                try:
                    shops = await service.list_shops("IntegrationManager")
                    return {
                        "status": IntegrationStatus.HEALTHY.value,
                        "message": f"Connected to {len(shops)} shops",
                        "last_checked": datetime.now().isoformat(),
                        "details": {
                            "shops_count": len(shops),
                            "shop_titles": [shop.title for shop in shops[:3]]  # First 3 shop titles
                        }
                    }
                except Exception as e:
                    return {
                        "status": IntegrationStatus.UNHEALTHY.value,
                        "message": f"Health check failed: {str(e)}",
                        "last_checked": datetime.now().isoformat()
                    }
        
        elif platform == "n8n":
            service = get_n8n_service()
            if service:
                try:
                    health = await service.health_check()
                    return {
                        "status": IntegrationStatus.HEALTHY.value if health["status"] == "healthy" else IntegrationStatus.UNHEALTHY.value,
                        "message": f"n8n instance: {health['status']}",
                        "last_checked": datetime.now().isoformat(),
                        "details": health
                    }
                except Exception as e:
                    return {
                        "status": IntegrationStatus.UNHEALTHY.value,
                        "message": f"Health check failed: {str(e)}",
                        "last_checked": datetime.now().isoformat()
                    }
        
        elif platform == "desktop":
            # Desktop access is always healthy
            return {
                "status": IntegrationStatus.HEALTHY.value,
                "message": "Desktop file access available",
                "last_checked": datetime.now().isoformat()
            }
        
        # Default for unimplemented platforms
        return {
            "status": IntegrationStatus.NOT_CONFIGURED.value,
            "message": "Platform not yet implemented",
            "last_checked": datetime.now().isoformat()
        }
    
    async def get_integration_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of all integrations."""
        await log_platform_activity(
            platform=Platform.SYSTEM,
            activity_type=ActivityType.READ,
            agent_name="IntegrationManager",
            description="Generating integration summary"
        )
        
        health_results = await self.health_check_all()
        
        # Get activity statistics
        activity_logger = get_activity_logger()
        activity_summary = {}
        if activity_logger:
            # Get last 24 hours of activity
            since = datetime.now() - timedelta(days=1)
            activity_summary = await activity_logger.get_activity_summary(start_time=since)
        
        summary = {
            "total_integrations": len(self.integrations),
            "enabled_integrations": len([c for c in self.integrations.values() if c.enabled]),
            "healthy_integrations": len([r for r in health_results.values() if r["status"] == "healthy"]),
            "platforms": {
                platform: {
                    "enabled": config.enabled,
                    "health": health_results.get(platform, {}).get("status", "unknown"),
                    "last_sync": config.last_sync.isoformat() if config.last_sync else None,
                    "has_api_key": bool(config.api_key),
                    "error": config.error_message
                }
                for platform, config in self.integrations.items()
            },
            "health_details": health_results,
            "activity_summary": activity_summary,
            "generated_at": datetime.now().isoformat()
        }
        
        await log_platform_activity(
            platform=Platform.SYSTEM,
            activity_type=ActivityType.READ,
            agent_name="IntegrationManager",
            description="Generated integration summary",
            details={
                "total_integrations": summary["total_integrations"],
                "healthy_integrations": summary["healthy_integrations"]
            }
        )
        
        return summary
    
    async def export_activity_logs(
        self, 
        platform: Optional[str] = None,
        hours: int = 24,
        format_type: str = "json"
    ) -> str:
        """Export activity logs for analysis."""
        activity_logger = get_activity_logger()
        if not activity_logger:
            raise Exception("Activity logger not initialized")
        
        since = datetime.now() - timedelta(hours=hours)
        
        await log_platform_activity(
            platform=Platform.SYSTEM,
            activity_type=ActivityType.READ,
            agent_name="IntegrationManager",
            description=f"Exporting activity logs for last {hours} hours",
            details={"platform": platform, "format": format_type, "hours": hours}
        )
        
        export_path = await activity_logger.export_activities(
            format_type=format_type,
            start_time=since,
            platform=platform
        )
        
        await log_platform_activity(
            platform=Platform.SYSTEM,
            activity_type=ActivityType.READ,
            agent_name="IntegrationManager",
            description=f"Successfully exported activity logs to {export_path}",
            details={"export_path": export_path, "hours": hours}
        )
        
        return export_path
    
    def get_platform_config(self, platform: str) -> Optional[IntegrationConfig]:
        """Get configuration for a specific platform."""
        return self.integrations.get(platform)
    
    def update_platform_config(self, platform: str, **updates):
        """Update configuration for a platform."""
        if platform in self.integrations:
            config = self.integrations[platform]
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            brebot_logger.log_agent_action(
                agent_name="IntegrationManager",
                action="config_updated",
                details={"platform": platform, "updates": list(updates.keys())}
            )


# Global integration manager instance
integration_manager: Optional[IntegrationManager] = None

def get_integration_manager() -> IntegrationManager:
    """Get or create the global integration manager instance."""
    global integration_manager
    if integration_manager is None:
        integration_manager = IntegrationManager()
    return integration_manager

async def initialize_all_integrations():
    """Initialize all platform integrations."""
    manager = get_integration_manager()
    await manager.initialize_services()
    return manager