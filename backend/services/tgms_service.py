"""
TGMS Service
===================
API integration with TGMS server for remote device management.
"""
import httpx
import logging
import hashlib
import base64
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone
from database import db
from models.tgms import (
    TGMSConfig, TGMSConfigCreate, TGMSConfigUpdate,
    TGMSDevice, TGMSBranding, AgentDownloadInfo
)
from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)


class TGMSService:
    """Service for interacting with TGMS API"""
    
    COLLECTION = "tgms_configs"
    
    # ==================== CONFIG CRUD ====================
    
    @staticmethod
    async def get_config(organization_id: str) -> Optional[Dict]:
        """Get TGMS config for an organization"""
        config = await db[TGMSService.COLLECTION].find_one(
            {"organization_id": organization_id},
            {"_id": 0}
        )
        return config
    
    @staticmethod
    async def create_config(organization_id: str, data: TGMSConfigCreate, user_id: str) -> Dict:
        """Create TGMS config for an organization"""
        # Check if config already exists
        existing = await TGMSService.get_config(organization_id)
        if existing:
            raise ValueError("TGMS config already exists for this organization")
        
        config = TGMSConfig(
            organization_id=organization_id,
            server_url=data.server_url.rstrip('/'),
            username=data.username or "",
            password_encrypted=TGMSService._encrypt_password(data.password) if data.password else "",
            api_token=data.api_token,
            mesh_domain=data.mesh_domain or "",
            created_by_id=user_id,
            updated_by_id=user_id
        )
        
        await db[TGMSService.COLLECTION].insert_one(config.model_dump())
        return config.model_dump()
    
    @staticmethod
    async def update_config(organization_id: str, data: TGMSConfigUpdate, user_id: str) -> Dict:
        """Update TGMS config"""
        config = await TGMSService.get_config(organization_id)
        if not config:
            raise ValueError("TGMS config not found")
        
        update_data = {"updated_at": get_ist_isoformat(), "updated_by_id": user_id}
        
        if data.server_url is not None:
            update_data["server_url"] = data.server_url.rstrip('/')
        if data.username is not None:
            update_data["username"] = data.username
        if data.password is not None:
            update_data["password_encrypted"] = TGMSService._encrypt_password(data.password)
        if data.api_token is not None:
            update_data["api_token"] = data.api_token
        if data.is_enabled is not None:
            update_data["is_enabled"] = data.is_enabled
        if data.sync_devices is not None:
            update_data["sync_devices"] = data.sync_devices
        if data.allow_remote_desktop is not None:
            update_data["allow_remote_desktop"] = data.allow_remote_desktop
        if data.allow_remote_terminal is not None:
            update_data["allow_remote_terminal"] = data.allow_remote_terminal
        if data.allow_file_transfer is not None:
            update_data["allow_file_transfer"] = data.allow_file_transfer
        if data.mesh_domain is not None:
            update_data["mesh_domain"] = data.mesh_domain
        if data.device_group_id is not None:
            update_data["device_group_id"] = data.device_group_id
        if data.branding is not None:
            # Merge branding updates
            current_branding = config.get("branding", {})
            current_branding.update(data.branding)
            update_data["branding"] = current_branding
        
        await db[TGMSService.COLLECTION].update_one(
            {"organization_id": organization_id},
            {"$set": update_data}
        )
        
        return await TGMSService.get_config(organization_id)
    
    @staticmethod
    async def delete_config(organization_id: str) -> bool:
        """Delete TGMS config"""
        result = await db[TGMSService.COLLECTION].delete_one(
            {"organization_id": organization_id}
        )
        return result.deleted_count > 0
    
    # ==================== API AUTHENTICATION ====================
    
    @staticmethod
    async def _get_auth_headers(config: Dict) -> Dict[str, str]:
        """Get authentication headers for TGMS API"""
        headers = {"Content-Type": "application/json"}
        
        if config.get("api_token"):
            headers["x-tgms-logintoken"] = config["api_token"]
        elif config.get("username") and config.get("password_encrypted"):
            password = TGMSService._decrypt_password(config["password_encrypted"])
            # Basic auth
            credentials = base64.b64encode(f"{config['username']}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"
        
        return headers
    
    @staticmethod
    async def test_connection(organization_id: str) -> Tuple[bool, str]:
        """Test connection to TGMS server"""
        config = await TGMSService.get_config(organization_id)
        if not config:
            return False, "TGMS not configured"
        
        if not config.get("server_url"):
            return False, "Server URL not configured"
        
        try:
            headers = await TGMSService._get_auth_headers(config)
            async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
                # Test server info endpoint
                response = await client.get(
                    f"{config['server_url']}/api/serverinfo",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return True, "Connection successful"
                elif response.status_code == 401:
                    return False, "Authentication failed - check credentials"
                else:
                    return False, f"Server returned status {response.status_code}"
                    
        except httpx.ConnectError:
            return False, "Cannot connect to server - check URL"
        except httpx.TimeoutException:
            return False, "Connection timeout - server not responding"
        except Exception as e:
            logger.error(f"TGMS connection test failed: {e}")
            return False, f"Connection error: {str(e)}"
    
    # ==================== DEVICE OPERATIONS ====================
    
    @staticmethod
    async def get_devices(organization_id: str) -> List[Dict]:
        """Get all devices from TGMS for this organization"""
        config = await TGMSService.get_config(organization_id)
        if not config or not config.get("is_enabled"):
            return []
        
        try:
            headers = await TGMSService._get_auth_headers(config)
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                response = await client.get(
                    f"{config['server_url']}/api/meshes",
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get meshes: {response.status_code}")
                    return []
                
                meshes_data = response.json()
                
                # Get nodes (devices) for each mesh
                devices = []
                response = await client.get(
                    f"{config['server_url']}/api/nodes",
                    headers=headers
                )
                
                if response.status_code == 200:
                    nodes_data = response.json()
                    for mesh_id, nodes in nodes_data.items():
                        for node in nodes:
                            devices.append(TGMSDevice(
                                id=node.get("_id", ""),
                                name=node.get("name", "Unknown"),
                                host=node.get("host", ""),
                                os=node.get("osdesc", ""),
                                agent_version=node.get("agentvers", ""),
                                last_connect=node.get("lastconnect", ""),
                                ip_addresses=node.get("iploc", "").split(",") if node.get("iploc") else [],
                                is_online=node.get("conn", 0) > 0,
                                organization_id=organization_id
                            ).model_dump())
                
                # Update sync status
                await db[TGMSService.COLLECTION].update_one(
                    {"organization_id": organization_id},
                    {"$set": {
                        "last_sync_at": get_ist_isoformat(),
                        "last_sync_status": "success",
                        "last_sync_error": None,
                        "device_count": len(devices)
                    }}
                )
                
                return devices
                
        except Exception as e:
            logger.error(f"Failed to get TGMS devices: {e}")
            await db[TGMSService.COLLECTION].update_one(
                {"organization_id": organization_id},
                {"$set": {
                    "last_sync_at": get_ist_isoformat(),
                    "last_sync_status": "failed",
                    "last_sync_error": str(e)
                }}
            )
            return []
    
    @staticmethod
    async def get_device(organization_id: str, device_id: str) -> Optional[Dict]:
        """Get a specific device from TGMS"""
        devices = await TGMSService.get_devices(organization_id)
        for device in devices:
            if device.get("id") == device_id:
                return device
        return None
    
    # ==================== REMOTE ACCESS ====================
    
    @staticmethod
    async def get_remote_desktop_url(organization_id: str, device_id: str) -> Optional[str]:
        """Get remote desktop URL for a device"""
        config = await TGMSService.get_config(organization_id)
        if not config or not config.get("is_enabled") or not config.get("allow_remote_desktop"):
            return None
        
        # Generate relay URL
        server_url = config.get("server_url", "").rstrip('/')
        return f"{server_url}/?node={device_id}&viewmode=1"
    
    @staticmethod
    async def get_remote_terminal_url(organization_id: str, device_id: str) -> Optional[str]:
        """Get remote terminal URL for a device"""
        config = await TGMSService.get_config(organization_id)
        if not config or not config.get("is_enabled") or not config.get("allow_remote_terminal"):
            return None
        
        server_url = config.get("server_url", "").rstrip('/')
        return f"{server_url}/?node={device_id}&viewmode=2"
    
    @staticmethod
    async def get_file_transfer_url(organization_id: str, device_id: str) -> Optional[str]:
        """Get file transfer URL for a device"""
        config = await TGMSService.get_config(organization_id)
        if not config or not config.get("is_enabled") or not config.get("allow_file_transfer"):
            return None
        
        server_url = config.get("server_url", "").rstrip('/')
        return f"{server_url}/?node={device_id}&viewmode=3"
    
    # ==================== AGENT DOWNLOADS ====================
    
    @staticmethod
    async def get_agent_downloads(organization_id: str) -> List[Dict]:
        """Get agent download links for all platforms"""
        config = await TGMSService.get_config(organization_id)
        if not config or not config.get("server_url"):
            return []
        
        server_url = config.get("server_url", "").rstrip('/')
        mesh_domain = config.get("mesh_domain", "")
        
        # TGMS agent download URLs
        agents = [
            AgentDownloadInfo(
                platform="windows",
                architecture="x64",
                download_url=f"{server_url}/meshagents?id=4&meshname={mesh_domain}",
                filename="MeshAgent-win64.exe",
                instructions="Run as Administrator. The agent will install and start automatically."
            ),
            AgentDownloadInfo(
                platform="windows",
                architecture="x86",
                download_url=f"{server_url}/meshagents?id=3&meshname={mesh_domain}",
                filename="MeshAgent-win32.exe",
                instructions="Run as Administrator. The agent will install and start automatically."
            ),
            AgentDownloadInfo(
                platform="linux",
                architecture="x64",
                download_url=f"{server_url}/meshagents?id=6&meshname={mesh_domain}",
                filename="meshagent_linux64",
                instructions="chmod +x meshagent_linux64 && sudo ./meshagent_linux64 -install"
            ),
            AgentDownloadInfo(
                platform="linux",
                architecture="arm64",
                download_url=f"{server_url}/meshagents?id=26&meshname={mesh_domain}",
                filename="meshagent_arm64",
                instructions="chmod +x meshagent_arm64 && sudo ./meshagent_arm64 -install"
            ),
            AgentDownloadInfo(
                platform="macos",
                architecture="x64",
                download_url=f"{server_url}/meshagents?id=16&meshname={mesh_domain}",
                filename="meshagent_osx64",
                instructions="chmod +x meshagent_osx64 && sudo ./meshagent_osx64 -install"
            ),
            AgentDownloadInfo(
                platform="macos",
                architecture="arm64",
                download_url=f"{server_url}/meshagents?id=29&meshname={mesh_domain}",
                filename="meshagent_osx_arm64",
                instructions="chmod +x meshagent_osx_arm64 && sudo ./meshagent_osx_arm64 -install"
            ),
        ]
        
        return [a.model_dump() for a in agents]
    
    # ==================== BRANDING ====================
    
    @staticmethod
    async def update_branding(organization_id: str, branding: Dict, user_id: str) -> Dict:
        """Update white-label branding for TGMS"""
        config = await TGMSService.get_config(organization_id)
        if not config:
            raise ValueError("TGMS config not found")
        
        current_branding = config.get("branding", {})
        current_branding.update(branding)
        
        await db[TGMSService.COLLECTION].update_one(
            {"organization_id": organization_id},
            {"$set": {
                "branding": current_branding,
                "updated_at": get_ist_isoformat(),
                "updated_by_id": user_id
            }}
        )
        
        return await TGMSService.get_config(organization_id)
    
    @staticmethod
    async def generate_tgms_config(organization_id: str) -> Dict:
        """Generate TGMS config.json snippet for this tenant's branding"""
        config = await TGMSService.get_config(organization_id)
        if not config:
            return {}
        
        branding = config.get("branding", {})
        domain = config.get("mesh_domain", "")
        
        # Generate TGMS domain config
        mesh_config = {
            "title": branding.get("title", "Remote Management"),
            "title2": branding.get("title2", "IT Support"),
            "welcomeText": branding.get("welcome_text", "Welcome"),
            "nightMode": 1 if branding.get("night_mode", True) else 0,
            "siteStyle": 2,
            "agentCustomization": {
                "displayName": branding.get("agent_display_name", "Support Agent"),
                "description": branding.get("agent_description", "Remote Support Agent"),
                "companyName": branding.get("agent_company_name", "IT Support"),
                "serviceName": branding.get("agent_service_name", "SupportAgent"),
                "foregroundColor": branding.get("agent_foreground_color", "#FFFFFF"),
                "backgroundColor": branding.get("agent_background_color", "#0F62FE")
            }
        }
        
        if branding.get("logo_url"):
            mesh_config["welcomePicture"] = branding["logo_url"]
        if branding.get("login_background_url"):
            mesh_config["loginPicture"] = branding["login_background_url"]
        
        return {domain: mesh_config} if domain else {"": mesh_config}
    
    # ==================== HELPER METHODS ====================
    
    @staticmethod
    def _encrypt_password(password: str) -> str:
        """Simple encryption for password storage (use proper encryption in production)"""
        if not password:
            return ""
        # In production, use proper encryption like Fernet
        # For now, base64 encode (NOT secure, just obfuscation)
        return base64.b64encode(password.encode()).decode()
    
    @staticmethod
    def _decrypt_password(encrypted: str) -> str:
        """Decrypt stored password"""
        if not encrypted:
            return ""
        try:
            return base64.b64decode(encrypted.encode()).decode()
        except Exception:
            return ""


# Export service instance
tgms_service = TGMSService()
