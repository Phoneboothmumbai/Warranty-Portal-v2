"""
WatchTower Integration Service
================================
Provides integration with WatchTower for MSPs to sync agents/devices,
run scripts, and pull system information.
"""
import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WatchTowerConfig(BaseModel):
    """Configuration for WatchTower API connection"""
    api_url: str  # e.g., https://api.yourdomain.com
    api_key: str
    enabled: bool = True


class WatchTowerAgent(BaseModel):
    """WatchTower Agent model"""
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


class WatchTowerService:
    """Service class for WatchTower API integration"""
    
    def __init__(self, config: WatchTowerConfig):
        self.config = config
        self.headers = {
            "X-API-KEY": config.api_key,
            "Content-Type": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Make authenticated request to WatchTower API"""
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
                logger.error(f"WatchTower API error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"WatchTower API request failed: {str(e)}")
                raise
    
    async def test_connection(self) -> bool:
        """Test API connection with credentials check"""
        try:
            await self._request("POST", "/v2/checkcreds/")
            return True
        except Exception as e:
            logger.error(f"WatchTower connection test failed: {str(e)}")
            return False
    
    async def get_agents(self) -> List[Dict[str, Any]]:
        """Get all agents from WatchTower"""
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
    
    # ==================== CLIENT/SITE MANAGEMENT ====================
    
    async def create_client(self, name: str) -> Dict[str, Any]:
        """
        Create a new client (organization) in WatchTower.
        Returns the created client with its ID.
        Note: This may fail on some Tactical RMM configurations - use get_or_create_client instead.
        """
        data = {"name": name}
        try:
            return await self._request("POST", "/clients/", data)
        except Exception as e:
            logger.warning(f"Failed to create client {name}: {e}")
            raise
    
    async def get_client_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a client by name (case-insensitive)"""
        clients = await self.get_clients()
        name_lower = name.lower().strip()
        for client in clients:
            if client.get("name", "").lower().strip() == name_lower:
                return client
        return None
    
    async def create_site(self, client_id: int, name: str) -> Dict[str, Any]:
        """
        Create a new site under a client in WatchTower.
        Returns the created site with its ID.
        """
        data = {
            "client": client_id,
            "name": name
        }
        try:
            return await self._request("POST", "/sites/", data)
        except Exception as e:
            logger.warning(f"Failed to create site {name} for client {client_id}: {e}")
            raise
    
    async def get_site_by_name(self, client_id: int, name: str) -> Optional[Dict[str, Any]]:
        """Find a site by name under a specific client"""
        # Get client info which includes sites
        clients = await self.get_clients()
        for client in clients:
            if client.get("id") == client_id:
                sites = client.get("sites", [])
                name_lower = name.lower().strip()
                for site in sites:
                    if site.get("name", "").lower().strip() == name_lower:
                        return site
                # If no matching site but client has sites, return first one
                if sites:
                    return sites[0]
        return None
    
    async def get_first_site_for_client(self, client_id: int) -> Optional[Dict[str, Any]]:
        """Get the first site for a client (from embedded sites in clients response)"""
        clients = await self.get_clients()
        for client in clients:
            if client.get("id") == client_id:
                sites = client.get("sites", [])
                if sites:
                    return sites[0]
        return None
    
    async def get_or_create_client(self, name: str) -> Dict[str, Any]:
        """
        Get existing client by name or create a new one.
        Returns the client dict with 'id' and 'name'.
        """
        existing = await self.get_client_by_name(name)
        if existing:
            return existing
        # Try to create, but this may fail on some configurations
        return await self.create_client(name)
    
    async def get_or_create_site(self, client_id: int, name: str) -> Dict[str, Any]:
        """
        Get existing site by name or create a new one under the client.
        Returns the site dict with 'id' and 'name'.
        """
        existing = await self.get_site_by_name(client_id, name)
        if existing:
            return existing
        # Try to create new site
        return await self.create_site(client_id, name)
    
    # ==================== AGENT DEPLOYMENT ====================
    
    async def get_agent_download_link(
        self, 
        site_id: int, 
        platform: str = "windows",
        arch: str = "64"
    ) -> Dict[str, Any]:
        """
        Generate agent installer download link for a specific site.
        
        Args:
            site_id: The WatchTower site ID
            platform: 'windows' or 'linux'
            arch: '64' or '32' (for Windows)
        
        Returns:
            Dict with download_url and other deployment info
        """
        data = {
            "site": site_id,
            "goarch": arch,
            "plat": platform
        }
        
        # Try multiple endpoint variations
        endpoints = [
            "/agents/installer/",
            "/core/installer/",
            "/agents/deploy/"
        ]
        
        for endpoint in endpoints:
            try:
                response = await self._request("POST", endpoint, data)
                if response:
                    return response
            except Exception as e:
                logger.warning(f"Endpoint {endpoint} failed: {e}")
                continue
        
        # If all API endpoints fail, provide manual download instructions
        # The user needs to download from the WatchTower web UI
        base_url = self.config.api_url.replace("/api.", "/rmm.").replace("api.", "rmm.")
        return {
            "download_url": None,
            "manual_download_required": True,
            "web_ui_url": base_url,
            "site_id": site_id,
            "instructions": f"Please log into WatchTower at {base_url}, go to Agents > Add Agent, select site ID {site_id}, and generate the installer manually."
        }
    
    async def provision_company_for_agent(
        self, 
        company_name: str, 
        site_name: str = "Default Site"
    ) -> Dict[str, Any]:
        """
        Full provisioning flow: Create client and site in WatchTower,
        then generate the agent download link.
        
        Args:
            company_name: Name of the company (maps to WatchTower Client)
            site_name: Name of the site (defaults to "Default Site")
        
        Returns:
            Dict with client_id, site_id, and download_url
        """
        # Step 1: Try to find existing client by name first
        client = await self.get_client_by_name(company_name)
        
        if not client:
            # Try to create new client
            try:
                client = await self.create_client(company_name)
            except Exception as e:
                logger.error(f"Failed to create client {company_name}: {e}")
                raise ValueError(f"Cannot create new client in WatchTower. Please create client '{company_name}' manually in WatchTower first.")
        
        client_id = client.get("id")
        actual_client_name = client.get("name", company_name)
        
        if not client_id:
            raise ValueError(f"Failed to get client ID for {company_name}")
        
        # Step 2: Try to find existing site or use first available
        site = await self.get_site_by_name(client_id, site_name)
        
        if not site:
            # Try to create new site
            try:
                site = await self.create_site(client_id, site_name)
            except Exception as e:
                logger.warning(f"Failed to create site, trying to get first available: {e}")
                # Try to get first available site for this client
                site = await self.get_first_site_for_client(client_id)
                if not site:
                    raise ValueError(f"No sites available for client '{actual_client_name}'. Please create a site in WatchTower first.")
        
        site_id = site.get("id")
        actual_site_name = site.get("name", site_name)
        
        if not site_id:
            raise ValueError(f"Failed to get site ID for {site_name}")
        
        # Step 3: Generate download link
        try:
            download_info = await self.get_agent_download_link(site_id)
        except Exception as e:
            logger.error(f"Failed to generate download link: {e}")
            raise ValueError(f"Failed to generate agent download link. Please check WatchTower configuration.")
        
        download_url = download_info.get("download_url") or download_info.get("exe_url") or download_info.get("download")
        
        return {
            "client_id": client_id,
            "client_name": actual_client_name,
            "site_id": site_id,
            "site_name": actual_site_name,
            "download_url": download_url,
            "download_info": download_info
        }


def map_agent_to_device(agent: Dict[str, Any], company_id: str, organization_id: str = None) -> Dict[str, Any]:
    """Map WatchTower agent data to our device schema"""
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
        "notes": f"Synced from WatchTower. OS: {agent.get('operating_system', 'Unknown')}",
        "rmm_agent_id": agent.get("agent_id"),
        "rmm_source": "watchtower",
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
