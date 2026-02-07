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

from services.auth import get_current_admin
from utils.tenant_scope import get_admin_org_id, scope_query
from services.watchtower import WatchTowerService, WatchTowerConfig, map_agent_to_device

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
from services.auth import get_current_company_user

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
