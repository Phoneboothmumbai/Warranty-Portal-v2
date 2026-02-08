"""
WatchTower Integration Routes
===============================
API endpoints for managing WatchTower integration settings and syncing agents.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import logging

from services.auth import get_current_admin, get_current_company_user
from utils.tenant_scope import get_admin_org_id, scope_query
from services.watchtower import WatchTowerService, WatchTowerConfig, map_agent_to_device

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/watchtower", tags=["WatchTower Integration"])

# Database reference - will be injected
_db = None


def init_watchtower_router(database):
    """Initialize the router with database dependency"""
    global _db
    _db = database


# ==================== REQUEST/RESPONSE MODELS ====================

class WatchTowerSetup(BaseModel):
    """Setup WatchTower integration"""
    api_url: str  # e.g., https://api.yourdomain.com
    api_key: str
    enabled: bool = True


class AgentSyncRequest(BaseModel):
    """Request to sync agents from WatchTower"""
    company_id: str  # Which company to assign synced devices to
    sync_all: bool = True
    agent_ids: Optional[List[str]] = None  # Specific agents to sync (if not sync_all)


class RunCommandRequest(BaseModel):
    """Request to run command on an agent"""
    shell: str = "powershell"  # powershell, cmd, bash
    cmd: str
    timeout: int = 30


# ==================== HELPER FUNCTIONS ====================

async def get_rmm_config(org_id: str) -> Optional[WatchTowerConfig]:
    """Get WatchTower configuration for an organization"""
    config = await _db.integrations.find_one({
        "organization_id": org_id,
        "type": "watchtower",
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if config and config.get("enabled"):
        return WatchTowerConfig(
            api_url=config.get("api_url"),
            api_key=config.get("api_key"),
            enabled=config.get("enabled", True)
        )
    return None


async def get_rmm_service(org_id: str) -> WatchTowerService:
    """Get authenticated WatchTower service for an organization"""
    config = await get_rmm_config(org_id)
    if not config:
        raise HTTPException(status_code=400, detail="WatchTower integration not configured")
    return WatchTowerService(config)


# ==================== CONFIGURATION ENDPOINTS ====================

@router.get("/config")
async def get_watchtower_config(admin: dict = Depends(get_current_admin)):
    """Get current WatchTower configuration (hides sensitive key)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    
    config = await _db.integrations.find_one({
        "organization_id": org_id,
        "type": "watchtower",
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not config:
        return {"configured": False}
    
    return {
        "configured": True,
        "enabled": config.get("enabled", False),
        "api_url": config.get("api_url"),
        "api_key_masked": f"****{config.get('api_key', '')[-4:]}" if config.get("api_key") else None,
        "last_sync": config.get("last_sync"),
        "agents_count": config.get("agents_count", 0)
    }


@router.post("/config")
async def setup_watchtower(setup: WatchTowerSetup, admin: dict = Depends(get_current_admin)):
    """Configure WatchTower integration"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    
    # Test connection first
    try:
        service = WatchTowerService(WatchTowerConfig(
            api_url=setup.api_url,
            api_key=setup.api_key,
            enabled=True
        ))
        connected = await service.test_connection()
        if not connected:
            raise HTTPException(status_code=400, detail="Failed to connect to WatchTower API. Please check your credentials.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection test failed: {str(e)}")
    
    # Save or update configuration
    config_data = {
        "organization_id": org_id,
        "type": "watchtower",
        "api_url": setup.api_url,
        "api_key": setup.api_key,
        "enabled": setup.enabled,
        "updated_at": datetime.utcnow().isoformat(),
        "is_deleted": False
    }
    
    existing = await _db.integrations.find_one({
        "organization_id": org_id,
        "type": "watchtower"
    })
    
    if existing:
        await _db.integrations.update_one(
            {"organization_id": org_id, "type": "watchtower"},
            {"$set": config_data}
        )
    else:
        config_data["id"] = str(uuid.uuid4())
        config_data["created_at"] = datetime.utcnow().isoformat()
        await _db.integrations.insert_one(config_data)
    
    return {"success": True, "message": "WatchTower integration configured successfully"}


@router.delete("/config")
async def disable_watchtower(admin: dict = Depends(get_current_admin)):
    """Disable WatchTower integration"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    
    await _db.integrations.update_one(
        {"organization_id": org_id, "type": "watchtower"},
        {"$set": {"enabled": False, "is_deleted": True}}
    )
    
    return {"success": True, "message": "WatchTower integration disabled"}


# ==================== AGENT ENDPOINTS ====================

@router.get("/agents")
async def list_rmm_agents(admin: dict = Depends(get_current_admin)):
    """List all agents from WatchTower"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    service = await get_rmm_service(org_id)
    
    agents = await service.get_agents()
    
    # Enrich with sync status from our database
    for agent in agents:
        existing_device = await _db.devices.find_one({
            "rmm_agent_id": agent.get("agent_id"),
            "organization_id": org_id,
            "is_deleted": {"$ne": True}
        }, {"_id": 0, "id": 1, "serial_number": 1, "company_id": 1})
        
        agent["synced"] = existing_device is not None
        agent["device_id"] = existing_device.get("id") if existing_device else None
    
    return agents


@router.get("/agents/{agent_id}")
async def get_rmm_agent(agent_id: str, admin: dict = Depends(get_current_admin)):
    """Get detailed agent information"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    service = await get_rmm_service(org_id)
    
    agent = await service.get_agent_details(agent_id)
    return agent


@router.post("/agents/sync")
async def sync_rmm_agents(request: AgentSyncRequest, admin: dict = Depends(get_current_admin)):
    """Sync agents from WatchTower to our device inventory"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    service = await get_rmm_service(org_id)
    
    # Verify company exists and belongs to this org
    company = await _db.companies.find_one({
        "id": request.company_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get agents from WatchTower
    all_agents = await service.get_agents()
    
    # Filter agents if specific IDs provided
    if not request.sync_all and request.agent_ids:
        agents_to_sync = [a for a in all_agents if a.get("agent_id") in request.agent_ids]
    else:
        agents_to_sync = all_agents
    
    synced = 0
    updated = 0
    errors = []
    
    for agent in agents_to_sync:
        try:
            agent_id = agent.get("agent_id")
            
            # Check if device already exists
            existing = await _db.devices.find_one({
                "rmm_agent_id": agent_id,
                "organization_id": org_id,
                "is_deleted": {"$ne": True}
            }, {"_id": 0})
            
            if existing:
                # Update existing device
                update_data = {
                    "status": "active" if agent.get("status") == "online" else "inactive",
                    "rmm_last_sync": datetime.utcnow().isoformat(),
                    "rmm_data": {
                        "hostname": agent.get("hostname"),
                        "site_name": agent.get("site_name"),
                        "client_name": agent.get("client_name"),
                        "operating_system": agent.get("operating_system"),
                        "platform": agent.get("plat"),
                        "public_ip": agent.get("public_ip"),
                        "total_ram_gb": agent.get("total_ram"),
                        "last_seen": agent.get("last_seen"),
                        "needs_reboot": agent.get("needs_reboot", False),
                        "logged_in_user": agent.get("logged_in_username")
                    }
                }
                await _db.devices.update_one(
                    {"id": existing["id"]},
                    {"$set": update_data}
                )
                updated += 1
            else:
                # Create new device
                device = map_agent_to_device(agent, request.company_id, org_id)
                await _db.devices.insert_one(device)
                synced += 1
                
        except Exception as e:
            errors.append({"agent_id": agent.get("agent_id"), "error": str(e)})
    
    # Update integration last sync time
    await _db.integrations.update_one(
        {"organization_id": org_id, "type": "watchtower"},
        {"$set": {
            "last_sync": datetime.utcnow().isoformat(),
            "agents_count": len(all_agents)
        }}
    )
    
    return {
        "success": True,
        "synced": synced,
        "updated": updated,
        "total_agents": len(agents_to_sync),
        "errors": errors if errors else None
    }


# ==================== REMOTE ACTIONS ====================

@router.post("/agents/{agent_id}/command")
async def run_agent_command(
    agent_id: str, 
    request: RunCommandRequest,
    admin: dict = Depends(get_current_admin)
):
    """Run a command on a specific agent"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    service = await get_rmm_service(org_id)
    
    result = await service.run_command(
        agent_id=agent_id,
        shell=request.shell,
        cmd=request.cmd,
        timeout=request.timeout
    )
    
    return result


@router.post("/agents/{agent_id}/reboot")
async def reboot_agent(agent_id: str, admin: dict = Depends(get_current_admin)):
    """Reboot a specific agent"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    service = await get_rmm_service(org_id)
    
    result = await service.reboot_agent(agent_id)
    return {"success": True, "message": "Reboot command sent", "result": result}


@router.post("/agents/{agent_id}/recover")
async def recover_agent(agent_id: str, admin: dict = Depends(get_current_admin)):
    """Send recovery command to an agent"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    service = await get_rmm_service(org_id)
    
    result = await service.send_agent_recovery(agent_id)
    return {"success": True, "message": "Recovery command sent", "result": result}


# ==================== CLIENTS/SITES ====================

@router.get("/clients")
async def list_rmm_clients(admin: dict = Depends(get_current_admin)):
    """List all clients from WatchTower"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    service = await get_rmm_service(org_id)
    
    return await service.get_clients()


@router.get("/sites")
async def list_rmm_sites(
    client_id: Optional[int] = None,
    admin: dict = Depends(get_current_admin)
):
    """List all sites from WatchTower"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    service = await get_rmm_service(org_id)
    
    return await service.get_sites(client_id)


@router.get("/scripts")
async def list_rmm_scripts(admin: dict = Depends(get_current_admin)):
    """List all available scripts from WatchTower"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    service = await get_rmm_service(org_id)
    
    return await service.get_scripts()



# ==================== COMPANY PORTAL ENDPOINTS ====================
# These use environment variables for WatchTower access

import os

def get_global_watchtower_service() -> WatchTowerService:
    """Get WatchTower service using environment variables"""
    api_url = os.environ.get("WATCHTOWER_API_URL")
    api_key = os.environ.get("WATCHTOWER_API_KEY")
    
    if not api_url or not api_key:
        return None
    
    return WatchTowerService(WatchTowerConfig(
        api_url=api_url,
        api_key=api_key,
        enabled=True
    ))


@router.get("/device/{device_id}/status")
async def get_device_watchtower_status(device_id: str, user: dict = Depends(get_current_company_user)):
    """Get WatchTower agent status for a device (Company Portal)"""
    company_id = user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="Company context required")
    
    # Get device
    device = await _db.devices.find_one({
        "id": device_id,
        "company_id": company_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Check if device has RMM agent linked
    rmm_agent_id = device.get("rmm_agent_id")
    hostname = device.get("hostname") or device.get("computer_name") or device.get("serial_number")
    
    service = get_global_watchtower_service()
    if not service:
        return {
            "integrated": False,
            "message": "WatchTower not configured",
            "agent_status": None
        }
    
    try:
        # If we have an agent_id, get that agent directly
        if rmm_agent_id:
            agent = await service.get_agent(rmm_agent_id)
            if agent:
                return {
                    "integrated": True,
                    "agent_status": "online" if agent.get("status") == "online" else "offline",
                    "agent_data": {
                        "agent_id": agent.get("agent_id"),
                        "hostname": agent.get("hostname"),
                        "operating_system": agent.get("operating_system"),
                        "platform": agent.get("plat"),
                        "public_ip": agent.get("public_ip"),
                        "total_ram_gb": agent.get("total_ram"),
                        "last_seen": agent.get("last_seen"),
                        "logged_in_user": agent.get("logged_in_username"),
                        "needs_reboot": agent.get("needs_reboot", False),
                        "version": agent.get("version"),
                        "client_name": agent.get("client_name"),
                        "site_name": agent.get("site_name")
                    }
                }
        
        # Otherwise, try to find agent by hostname
        agents = await service.get_agents()
        for agent in agents:
            if agent.get("hostname", "").lower() == hostname.lower():
                # Found matching agent - save the mapping
                await _db.devices.update_one(
                    {"id": device_id},
                    {"$set": {
                        "rmm_agent_id": agent.get("agent_id"),
                        "rmm_source": "watchtower",
                        "rmm_last_sync": datetime.utcnow().isoformat()
                    }}
                )
                
                return {
                    "integrated": True,
                    "agent_status": "online" if agent.get("status") == "online" else "offline",
                    "agent_data": {
                        "agent_id": agent.get("agent_id"),
                        "hostname": agent.get("hostname"),
                        "operating_system": agent.get("operating_system"),
                        "platform": agent.get("plat"),
                        "public_ip": agent.get("public_ip"),
                        "total_ram_gb": agent.get("total_ram"),
                        "last_seen": agent.get("last_seen"),
                        "logged_in_user": agent.get("logged_in_username"),
                        "needs_reboot": agent.get("needs_reboot", False),
                        "version": agent.get("version"),
                        "client_name": agent.get("client_name"),
                        "site_name": agent.get("site_name")
                    }
                }
        
        # Agent not found
        return {
            "integrated": True,
            "agent_status": "not_installed",
            "message": "WatchTower agent not installed on this device",
            "agent_data": None
        }
        
    except Exception as e:
        logger.error(f"Error fetching WatchTower status for device {device_id}: {str(e)}")
        return {
            "integrated": True,
            "agent_status": "error",
            "message": f"Error connecting to WatchTower: {str(e)}",
            "agent_data": None
        }


@router.get("/device/{device_id}/details")
async def get_device_watchtower_details(device_id: str, user: dict = Depends(get_current_company_user)):
    """Get detailed WatchTower agent info including hardware/software (Company Portal)"""
    company_id = user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="Company context required")
    
    # Get device
    device = await _db.devices.find_one({
        "id": device_id,
        "company_id": company_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    rmm_agent_id = device.get("rmm_agent_id")
    if not rmm_agent_id:
        return {
            "integrated": False,
            "message": "Device not linked to WatchTower agent"
        }
    
    service = get_global_watchtower_service()
    if not service:
        return {
            "integrated": False,
            "message": "WatchTower not configured"
        }
    
    try:
        details = await service.get_agent_details(rmm_agent_id)
        
        # Extract useful metrics
        return {
            "integrated": True,
            "agent_id": rmm_agent_id,
            "system_info": {
                "hostname": details.get("hostname"),
                "operating_system": details.get("operating_system"),
                "cpu": details.get("cpu_model", []),
                "cpu_count": details.get("cpu_count"),
                "total_ram_gb": details.get("total_ram"),
                "boot_time": details.get("boot_time"),
                "public_ip": details.get("public_ip"),
                "local_ips": details.get("local_ips", [])
            },
            "disk_info": details.get("disks", []),
            "memory_info": {
                "total": details.get("total_ram"),
                "used_percent": details.get("mem_used_percent")
            },
            "cpu_usage": details.get("cpu_usage"),
            "installed_software": details.get("software", [])[:50],  # Limit to 50
            "pending_updates": details.get("pending_actions", {}).get("patches", []),
            "alerts": details.get("alerts", []),
            "last_seen": details.get("last_seen"),
            "needs_reboot": details.get("needs_reboot", False)
        }
        
    except Exception as e:
        logger.error(f"Error fetching WatchTower details for device {device_id}: {str(e)}")
        return {
            "integrated": True,
            "error": str(e),
            "message": "Error fetching detailed information"
        }



# ==================== AUTOMATIC SYNC ENDPOINTS ====================

@router.post("/auto-sync")
async def auto_sync_all_agents(admin: dict = Depends(get_current_admin)):
    """
    Automatically sync ALL agents from WatchTower to Warranty Portal.
    Maps WatchTower Client → Company (by name match)
    Maps WatchTower Site → Site (by name match)
    Creates devices with real serial numbers from WMI data.
    """
    org_id = await get_admin_org_id(admin.get("email", ""))
    
    service = get_global_watchtower_service()
    if not service:
        raise HTTPException(status_code=400, detail="WatchTower not configured")
    
    try:
        # Get all agents
        agents = await service.get_agents()
        
        if not agents:
            return {"success": True, "message": "No agents found in WatchTower", "synced": 0, "updated": 0}
        
        # Get all companies for this organization
        companies = await _db.companies.find({
            "organization_id": org_id,
            "is_deleted": {"$ne": True}
        }, {"_id": 0}).to_list(1000)
        
        # Build company name lookup (case-insensitive)
        company_lookup = {c["name"].lower().strip(): c for c in companies}
        
        # Get all sites
        sites = await _db.sites.find({
            "organization_id": org_id,
            "is_deleted": {"$ne": True}
        }, {"_id": 0}).to_list(5000)
        
        # Build site lookup by company_id and name
        site_lookup = {}
        for site in sites:
            key = f"{site['company_id']}:{site['name'].lower().strip()}"
            site_lookup[key] = site
        
        synced = 0
        updated = 0
        skipped = 0
        errors = []
        created_companies = []
        created_sites = []
        
        for agent in agents:
            try:
                agent_id = agent.get("agent_id")
                client_name = agent.get("client_name", "").strip()
                site_name = agent.get("site_name", "").strip()
                hostname = agent.get("hostname", "")
                
                # Find or create company
                company = company_lookup.get(client_name.lower())
                if not company:
                    # Auto-create company
                    import uuid as uuid_module
                    new_company_id = str(uuid_module.uuid4())
                    company = {
                        "id": new_company_id,
                        "name": client_name,
                        "organization_id": org_id,
                        "source": "watchtower_sync",
                        "created_at": datetime.utcnow().isoformat(),
                        "is_deleted": False
                    }
                    await _db.companies.insert_one(company)
                    company_lookup[client_name.lower()] = company
                    created_companies.append(client_name)
                
                company_id = company["id"]
                
                # Find or create site
                site_key = f"{company_id}:{site_name.lower()}"
                site = site_lookup.get(site_key)
                if not site and site_name:
                    # Auto-create site
                    import uuid as uuid_module
                    new_site_id = str(uuid_module.uuid4())
                    site = {
                        "id": new_site_id,
                        "name": site_name,
                        "company_id": company_id,
                        "organization_id": org_id,
                        "source": "watchtower_sync",
                        "created_at": datetime.utcnow().isoformat(),
                        "is_deleted": False
                    }
                    await _db.sites.insert_one(site)
                    site_lookup[site_key] = site
                    created_sites.append(f"{client_name}/{site_name}")
                
                site_id = site["id"] if site else None
                
                # Try to get real serial number from agent details
                serial_number = None
                try:
                    details = await service.get_agent_details(agent_id)
                    # WMI serial number is usually in wmi_detail
                    wmi = details.get("wmi_detail", {})
                    serial_number = wmi.get("serialnumber") or wmi.get("SerialNumber")
                    if not serial_number:
                        # Try BIOS info
                        bios = wmi.get("bios", {})
                        serial_number = bios.get("SerialNumber")
                except:
                    pass
                
                # Fallback to hostname if no serial
                if not serial_number:
                    serial_number = hostname or agent_id[:16]
                
                # Check if device already exists (by rmm_agent_id OR serial_number OR hostname)
                existing = await _db.devices.find_one({
                    "$or": [
                        {"rmm_agent_id": agent_id},
                        {"serial_number": serial_number, "company_id": company_id},
                        {"hostname": hostname, "company_id": company_id}
                    ],
                    "organization_id": org_id,
                    "is_deleted": {"$ne": True}
                }, {"_id": 0})
                
                # Determine device type
                plat = agent.get("plat", "").lower()
                os_name = agent.get("operating_system", "").lower()
                if "server" in os_name:
                    device_type = "Server"
                elif plat == "darwin":
                    device_type = "Mac"
                elif "windows" in os_name:
                    device_type = "Desktop"
                else:
                    device_type = "Desktop"
                
                now = datetime.utcnow().isoformat()
                
                if existing:
                    # Update existing device
                    update_data = {
                        "rmm_agent_id": agent_id,
                        "rmm_source": "watchtower",
                        "rmm_last_sync": now,
                        "status": "active" if agent.get("status") == "online" else "offline",
                        "hostname": hostname,
                        "computer_name": hostname,
                        "operating_system": agent.get("operating_system"),
                        "public_ip": agent.get("public_ip"),
                        "rmm_data": {
                            "hostname": hostname,
                            "site_name": site_name,
                            "client_name": client_name,
                            "operating_system": agent.get("operating_system"),
                            "platform": plat,
                            "public_ip": agent.get("public_ip"),
                            "total_ram_gb": agent.get("total_ram"),
                            "last_seen": agent.get("last_seen"),
                            "needs_reboot": agent.get("needs_reboot", False),
                            "logged_in_user": agent.get("logged_in_username")
                        },
                        "updated_at": now
                    }
                    await _db.devices.update_one({"id": existing["id"]}, {"$set": update_data})
                    updated += 1
                else:
                    # Create new device
                    import uuid as uuid_module
                    new_device = {
                        "id": str(uuid_module.uuid4()),
                        "organization_id": org_id,
                        "company_id": company_id,
                        "site_id": site_id,
                        "site_name": site_name,
                        "serial_number": serial_number,
                        "hostname": hostname,
                        "computer_name": hostname,
                        "asset_tag": f"WT-{agent_id[:8].upper()}",
                        "device_type": device_type,
                        "category": device_type,
                        "brand": "Auto-Detected",
                        "model": hostname,
                        "status": "active" if agent.get("status") == "online" else "offline",
                        "operating_system": agent.get("operating_system"),
                        "os": agent.get("operating_system"),
                        "public_ip": agent.get("public_ip"),
                        "ram": f"{agent.get('total_ram', 0):.1f} GB" if agent.get("total_ram") else None,
                        "rmm_agent_id": agent_id,
                        "rmm_source": "watchtower",
                        "rmm_last_sync": now,
                        "rmm_data": {
                            "hostname": hostname,
                            "site_name": site_name,
                            "client_name": client_name,
                            "operating_system": agent.get("operating_system"),
                            "platform": plat,
                            "public_ip": agent.get("public_ip"),
                            "total_ram_gb": agent.get("total_ram"),
                            "last_seen": agent.get("last_seen"),
                            "needs_reboot": agent.get("needs_reboot", False),
                            "logged_in_user": agent.get("logged_in_username")
                        },
                        "notes": f"Auto-synced from WatchTower on {now}",
                        "created_at": now,
                        "updated_at": now,
                        "is_deleted": False
                    }
                    await _db.devices.insert_one(new_device)
                    synced += 1
                    
            except Exception as e:
                errors.append({"agent_id": agent.get("agent_id"), "hostname": agent.get("hostname"), "error": str(e)})
        
        return {
            "success": True,
            "total_agents": len(agents),
            "devices_created": synced,
            "devices_updated": updated,
            "companies_created": created_companies,
            "sites_created": created_sites,
            "errors": errors[:10]  # Limit errors returned
        }
        
    except Exception as e:
        logger.error(f"Auto-sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/clients-mapping")
async def get_clients_mapping(admin: dict = Depends(get_current_admin)):
    """Get WatchTower clients and their mapping to portal companies"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    
    service = get_global_watchtower_service()
    if not service:
        raise HTTPException(status_code=400, detail="WatchTower not configured")
    
    try:
        # Get clients from WatchTower
        clients = await service.get_clients()
        
        # Get companies from portal
        companies = await _db.companies.find({
            "organization_id": org_id,
            "is_deleted": {"$ne": True}
        }, {"_id": 0, "id": 1, "name": 1}).to_list(1000)
        
        company_lookup = {c["name"].lower().strip(): c for c in companies}
        
        result = []
        for client in clients:
            client_name = client.get("name", "").strip()
            matched_company = company_lookup.get(client_name.lower())
            
            result.append({
                "watchtower_client_id": client.get("id"),
                "watchtower_client_name": client_name,
                "portal_company_id": matched_company["id"] if matched_company else None,
                "portal_company_name": matched_company["name"] if matched_company else None,
                "is_mapped": matched_company is not None
            })
        
        return {
            "clients": result,
            "total_clients": len(clients),
            "mapped_count": len([r for r in result if r["is_mapped"]]),
            "unmapped_count": len([r for r in result if not r["is_mapped"]])
        }
        
    except Exception as e:
        logger.error(f"Error fetching clients mapping: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SELF-SERVICE AGENT DOWNLOAD ====================

class AgentDownloadRequest(BaseModel):
    """Request body for generating agent download link"""
    site_name: Optional[str] = "Default Site"
    platform: str = "windows"  # windows or linux
    arch: str = "64"  # 64 or 32


class CompanyAgentDownloadRequest(BaseModel):
    """Request for company portal agent download"""
    site_id: Optional[str] = None  # Portal site ID (optional)
    platform: str = "windows"
    arch: str = "64"


@router.post("/agent-download/{company_id}")
async def generate_agent_download_for_company(
    company_id: str,
    request: AgentDownloadRequest,
    admin: dict = Depends(get_current_admin)
):
    """
    Admin endpoint: Generate WatchTower agent download link for a company.
    This will auto-create the Client/Site in WatchTower if they don't exist.
    """
    org_id = await get_admin_org_id(admin.get("email", ""))
    
    # Get company
    company = await _db.companies.find_one({
        "id": company_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    service = get_global_watchtower_service()
    if not service:
        raise HTTPException(status_code=400, detail="WatchTower not configured. Please configure WatchTower integration first.")
    
    try:
        # Provision company in WatchTower and get download link
        result = await service.provision_company_for_agent(
            company_name=company["name"],
            site_name=request.site_name
        )
        
        # Store the WatchTower mapping in the company record
        await _db.companies.update_one(
            {"id": company_id},
            {"$set": {
                "watchtower_client_id": result["client_id"],
                "watchtower_site_id": result["site_id"],
                "watchtower_site_name": result["site_name"],
                "watchtower_provisioned_at": datetime.utcnow().isoformat()
            }}
        )
        
        return {
            "success": True,
            "company_id": company_id,
            "company_name": company["name"],
            "watchtower_client_id": result["client_id"],
            "watchtower_site_id": result["site_id"],
            "site_name": result["site_name"],
            "download_url": result["download_url"],
            "platform": request.platform,
            "arch": request.arch,
            "instructions": {
                "windows": "Download the .exe file and run it as Administrator on the target device.",
                "linux": "Download the installer and run with sudo: sudo bash ./installer.sh"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to generate agent download for company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate download link: {str(e)}")


@router.get("/agent-download/{company_id}/status")
async def get_company_watchtower_status(
    company_id: str,
    admin: dict = Depends(get_current_admin)
):
    """
    Admin endpoint: Check if a company is already provisioned in WatchTower.
    """
    org_id = await get_admin_org_id(admin.get("email", ""))
    
    company = await _db.companies.find_one({
        "id": company_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "id": 1, "name": 1, "watchtower_client_id": 1, "watchtower_site_id": 1, 
        "watchtower_site_name": 1, "watchtower_provisioned_at": 1})
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    is_provisioned = bool(company.get("watchtower_client_id"))
    
    # If provisioned, get current agent count from WatchTower
    agent_count = 0
    if is_provisioned:
        service = get_global_watchtower_service()
        if service:
            try:
                agents = await service.get_agents()
                # Count agents matching this company's client name
                agent_count = len([
                    a for a in agents 
                    if a.get("client_name", "").lower().strip() == company["name"].lower().strip()
                ])
            except Exception as e:
                logger.warning(f"Could not fetch agent count: {e}")
    
    return {
        "company_id": company["id"],
        "company_name": company["name"],
        "is_provisioned": is_provisioned,
        "watchtower_client_id": company.get("watchtower_client_id"),
        "watchtower_site_id": company.get("watchtower_site_id"),
        "watchtower_site_name": company.get("watchtower_site_name"),
        "provisioned_at": company.get("watchtower_provisioned_at"),
        "installed_agents": agent_count
    }


# ==================== COMPANY PORTAL SELF-SERVICE ====================

@router.post("/company/agent-download")
async def company_generate_agent_download(
    request: CompanyAgentDownloadRequest,
    user: dict = Depends(get_current_company_user)
):
    """
    Company Portal endpoint: Self-service agent download.
    Tenants can generate their own WatchTower agent installer.
    """
    company_id = user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="Company context required")
    
    # Get company info
    company = await _db.companies.find_one({
        "id": company_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    service = get_global_watchtower_service()
    if not service:
        raise HTTPException(status_code=400, detail="WatchTower monitoring is not enabled for this organization.")
    
    # Determine site name
    site_name = "Default Site"
    if request.site_id:
        site = await _db.sites.find_one({
            "id": request.site_id,
            "company_id": company_id,
            "is_deleted": {"$ne": True}
        }, {"_id": 0, "name": 1})
        if site:
            site_name = site["name"]
    
    try:
        # Check if already provisioned
        if company.get("watchtower_client_id") and company.get("watchtower_site_id"):
            # Already provisioned, just regenerate download link
            download_info = await service.get_agent_download_link(
                site_id=company["watchtower_site_id"],
                platform=request.platform,
                arch=request.arch
            )
            download_url = download_info.get("download_url") or download_info.get("exe_url")
            manual_download = download_info.get("manual_download_required", False)
            web_ui_url = download_info.get("web_ui_url")
        else:
            # First time - provision and get link
            result = await service.provision_company_for_agent(
                company_name=company["name"],
                site_name=site_name
            )
            download_url = result.get("download_url")
            manual_download = result.get("manual_download_required", False)
            web_ui_url = result.get("web_ui_url")
            
            # Store WatchTower mapping
            await _db.companies.update_one(
                {"id": company_id},
                {"$set": {
                    "watchtower_client_id": result["client_id"],
                    "watchtower_site_id": result["site_id"],
                    "watchtower_site_name": result["site_name"],
                    "watchtower_provisioned_at": datetime.utcnow().isoformat()
                }}
            )
        
        response = {
            "success": True,
            "download_url": download_url,
            "company_name": company["name"],
            "site_name": site_name,
            "platform": request.platform,
            "instructions": get_installation_instructions(request.platform)
        }
        
        if manual_download:
            response["manual_download_required"] = True
            response["web_ui_url"] = web_ui_url
            response["message"] = f"Automatic download link generation is not available. Please log into WatchTower to generate the installer manually."
        
        return response
        
    except Exception as e:
        logger.error(f"Company agent download failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate download link: {str(e)}")


@router.get("/company/agent-status")
async def company_get_agent_status(user: dict = Depends(get_current_company_user)):
    """
    Company Portal: Get WatchTower provisioning status and agent count.
    """
    company_id = user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="Company context required")
    
    company = await _db.companies.find_one({
        "id": company_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "name": 1, "watchtower_client_id": 1, "watchtower_site_id": 1,
        "watchtower_site_name": 1, "watchtower_provisioned_at": 1})
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    service = get_global_watchtower_service()
    watchtower_enabled = service is not None
    is_provisioned = bool(company.get("watchtower_client_id"))
    
    # Get agent count for this company
    agent_count = 0
    online_count = 0
    if is_provisioned and service:
        try:
            agents = await service.get_agents()
            company_agents = [
                a for a in agents 
                if a.get("client_name", "").lower().strip() == company["name"].lower().strip()
            ]
            agent_count = len(company_agents)
            online_count = len([a for a in company_agents if a.get("status") == "online"])
        except Exception as e:
            logger.warning(f"Could not fetch agent count for company: {e}")
    
    return {
        "watchtower_enabled": watchtower_enabled,
        "is_provisioned": is_provisioned,
        "watchtower_client_id": company.get("watchtower_client_id"),
        "watchtower_site_name": company.get("watchtower_site_name"),
        "provisioned_at": company.get("watchtower_provisioned_at"),
        "total_agents": agent_count,
        "online_agents": online_count,
        "offline_agents": agent_count - online_count
    }


@router.get("/company/sites-for-agent")
async def company_get_sites_for_agent(user: dict = Depends(get_current_company_user)):
    """
    Company Portal: Get list of portal sites for agent deployment selection.
    """
    company_id = user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="Company context required")
    
    sites = await _db.sites.find({
        "company_id": company_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "id": 1, "name": 1, "address": 1}).to_list(100)
    
    return {
        "sites": sites,
        "total": len(sites)
    }


def get_installation_instructions(platform: str) -> dict:
    """Get platform-specific installation instructions"""
    if platform == "windows":
        return {
            "title": "Windows Installation",
            "steps": [
                "Download the .exe installer file",
                "Right-click the file and select 'Run as Administrator'",
                "Follow the on-screen prompts to complete installation",
                "The agent will automatically connect to WatchTower after installation"
            ],
            "notes": [
                "Administrator privileges are required",
                "The installation may take 1-2 minutes",
                "A system restart is not usually required"
            ]
        }
    else:
        return {
            "title": "Linux Installation", 
            "steps": [
                "Download the installer script",
                "Open a terminal and navigate to the download folder",
                "Make the script executable: chmod +x installer.sh",
                "Run with sudo: sudo ./installer.sh",
                "The agent will automatically connect after installation"
            ],
            "notes": [
                "Root/sudo privileges are required",
                "Supported distributions: Ubuntu, Debian, CentOS, RHEL"
            ]
        }
