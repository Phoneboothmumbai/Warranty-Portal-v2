"""
Tactical RMM Integration Service
================================
Provides integration with Tactical RMM for MSPs to sync agents/devices,
run scripts, and pull system information.
"""
import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TacticalRMMConfig(BaseModel):
    """Configuration for Tactical RMM API connection"""
    api_url: str  # e.g., https://api.yourdomain.com
    api_key: str
    enabled: bool = True


class TacticalRMMAgent(BaseModel):
    """Tactical RMM Agent model"""
    agent_id: str
    hostname: str
    site_name: Optional[str] = None
    client_name: Optional[str] = None
    operating_system: Optional[str] = None
    plat: Optional[str] = None  # windows/linux/darwin
    version: Optional[str] = None
    public_ip: Optional[str] = None
    total_ram: Optional[float] = None
    boot_time: Optional[str] = None
    logged_in_username: Optional[str] = None
    last_seen: Optional[str] = None
    status: Optional[str] = None  # online/offline
    needs_reboot: Optional[bool] = False
    overdue_email_alert: Optional[bool] = False
    overdue_text_alert: Optional[bool] = False


class TacticalRMMService:
    """Service class for Tactical RMM API integration"""
    
    def __init__(self, config: TacticalRMMConfig):
        self.config = config
        self.headers = {
            "X-API-KEY": config.api_key,
            "Content-Type": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Make authenticated request to Tactical RMM API"""
        url = f"{self.config.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self.headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=self.headers, json=data)
                elif method.upper() == "PATCH":
                    response = await client.patch(url, headers=self.headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=self.headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json() if response.text else {}
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Tactical RMM API error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Tactical RMM API request failed: {str(e)}")
                raise
    
    async def test_connection(self) -> bool:
        """Test API connection with credentials check"""
        try:
            await self._request("POST", "/v2/checkcreds/")
            return True
        except Exception as e:
            logger.error(f"Tactical RMM connection test failed: {str(e)}")
            return False
    
    async def get_agents(self) -> List[Dict[str, Any]]:
        """Get all agents from Tactical RMM"""
        return await self._request("GET", "/agents/")
    
    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get single agent details"""
        return await self._request("GET", f"/agents/{agent_id}/")
    
    async def get_agent_details(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed agent information including hardware/software"""
        return await self._request("GET", f"/agents/{agent_id}/details/")
    
    async def run_command(self, agent_id: str, shell: str, cmd: str, timeout: int = 30) -> Dict[str, Any]:
        """Run a command on an agent"""
        data = {
            "shell": shell,  # powershell, cmd, bash
            "cmd": cmd,
            "timeout": timeout
        }
        return await self._request("POST", f"/agents/{agent_id}/cmd/", data)
    
    async def run_script(self, agent_id: str, script_id: int, args: List[str] = None, timeout: int = 120) -> Dict[str, Any]:
        """Run a script on an agent"""
        data = {
            "script": script_id,
            "timeout": timeout
        }
        if args:
            data["args"] = args
        return await self._request("POST", f"/agents/{agent_id}/runscript/", data)
    
    async def get_clients(self) -> List[Dict[str, Any]]:
        """Get all clients (organizations)"""
        return await self._request("GET", "/clients/")
    
    async def get_sites(self, client_id: int = None) -> List[Dict[str, Any]]:
        """Get all sites, optionally filtered by client"""
        endpoint = f"/clients/{client_id}/sites/" if client_id else "/sites/"
        return await self._request("GET", endpoint)
    
    async def get_scripts(self) -> List[Dict[str, Any]]:
        """Get all scripts"""
        return await self._request("GET", "/scripts/")
    
    async def send_agent_recovery(self, agent_id: str) -> Dict[str, Any]:
        """Send recovery command to an agent"""
        return await self._request("POST", f"/agents/{agent_id}/recover/")
    
    async def reboot_agent(self, agent_id: str) -> Dict[str, Any]:
        """Reboot an agent"""
        return await self._request("POST", f"/agents/{agent_id}/reboot/")


def map_agent_to_device(agent: Dict[str, Any], company_id: str, organization_id: str = None) -> Dict[str, Any]:
    """Map Tactical RMM agent data to our device schema"""
    import uuid
    
    # Determine device type based on OS and platform
    plat = agent.get("plat", "").lower()
    os_name = agent.get("operating_system", "").lower()
    
    if "server" in os_name:
        device_type = "Server"
    elif plat == "darwin":
        device_type = "Apple Device"
    elif "windows" in os_name:
        device_type = "Desktop"
    else:
        device_type = "Desktop"
    
    device = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "serial_number": agent.get("agent_id"),  # Use agent_id as serial
        "asset_tag": f"TRMM-{agent.get('agent_id', '')[:8]}",
        "device_type": device_type,
        "brand": "Various",  # Could be enhanced with WMI data
        "model": agent.get("hostname", "Unknown"),
        "status": "active" if agent.get("status") == "online" else "inactive",
        "notes": f"Synced from Tactical RMM. OS: {agent.get('operating_system', 'Unknown')}",
        "rmm_agent_id": agent.get("agent_id"),
        "rmm_source": "tactical_rmm",
        "rmm_last_sync": datetime.utcnow().isoformat(),
        "rmm_data": {
            "hostname": agent.get("hostname"),
            "site_name": agent.get("site_name"),
            "client_name": agent.get("client_name"),
            "operating_system": agent.get("operating_system"),
            "platform": plat,
            "public_ip": agent.get("public_ip"),
            "total_ram_gb": agent.get("total_ram"),
            "last_seen": agent.get("last_seen"),
            "needs_reboot": agent.get("needs_reboot", False),
            "logged_in_user": agent.get("logged_in_username")
        }
    }
    
    if organization_id:
        device["organization_id"] = organization_id
    
    return device
