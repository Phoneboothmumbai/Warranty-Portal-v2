"""
MeshCentral API Routes
======================
Endpoints for MeshCentral integration management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any
from services.meshcentral_service import MeshCentralService
from models.meshcentral import MeshCentralConfigCreate, MeshCentralConfigUpdate
from utils.auth import get_current_admin

router = APIRouter(prefix="/api/admin/meshcentral", tags=["MeshCentral"])


# ==================== FEATURE CHECK ====================

async def check_meshcentral_enabled(current_admin: dict = Depends(get_current_admin)):
    """Check if MeshCentral feature is enabled for this organization"""
    org = current_admin.get("organization", {})
    feature_flags = org.get("feature_flags", {})
    
    # Default to True if not explicitly disabled
    if not feature_flags.get("meshcentral", True):
        raise HTTPException(
            status_code=403,
            detail="MeshCentral integration is not enabled for your organization"
        )
    
    return current_admin


# ==================== CONFIGURATION ====================

@router.get("/config")
async def get_meshcentral_config(current_admin: dict = Depends(check_meshcentral_enabled)):
    """Get MeshCentral configuration for current organization"""
    organization_id = current_admin.get("organization_id")
    config = await MeshCentralService.get_config(organization_id)
    
    if not config:
        return {"configured": False, "config": None}
    
    # Remove sensitive data
    safe_config = {**config}
    safe_config.pop("password_encrypted", None)
    if safe_config.get("api_token"):
        safe_config["api_token"] = "***configured***"
    
    return {"configured": True, "config": safe_config}


@router.post("/config")
async def create_meshcentral_config(
    data: MeshCentralConfigCreate,
    current_admin: dict = Depends(check_meshcentral_enabled)
):
    """Create MeshCentral configuration"""
    organization_id = current_admin.get("organization_id")
    user_id = current_admin.get("id")
    
    try:
        config = await MeshCentralService.create_config(organization_id, data, user_id)
        
        # Remove sensitive data
        config.pop("password_encrypted", None)
        if config.get("api_token"):
            config["api_token"] = "***configured***"
        
        return {"success": True, "config": config}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/config")
async def update_meshcentral_config(
    data: MeshCentralConfigUpdate,
    current_admin: dict = Depends(check_meshcentral_enabled)
):
    """Update MeshCentral configuration"""
    organization_id = current_admin.get("organization_id")
    user_id = current_admin.get("id")
    
    try:
        config = await MeshCentralService.update_config(organization_id, data, user_id)
        
        # Remove sensitive data
        config.pop("password_encrypted", None)
        if config.get("api_token"):
            config["api_token"] = "***configured***"
        
        return {"success": True, "config": config}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/config")
async def delete_meshcentral_config(current_admin: dict = Depends(check_meshcentral_enabled)):
    """Delete MeshCentral configuration"""
    organization_id = current_admin.get("organization_id")
    
    success = await MeshCentralService.delete_config(organization_id)
    if not success:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return {"success": True, "message": "MeshCentral configuration deleted"}


# ==================== CONNECTION TEST ====================

@router.post("/test-connection")
async def test_meshcentral_connection(current_admin: dict = Depends(check_meshcentral_enabled)):
    """Test connection to MeshCentral server"""
    organization_id = current_admin.get("organization_id")
    
    success, message = await MeshCentralService.test_connection(organization_id)
    
    return {"success": success, "message": message}


# ==================== DEVICES ====================

@router.get("/devices")
async def get_meshcentral_devices(
    current_admin: dict = Depends(check_meshcentral_enabled),
    refresh: bool = Query(False, description="Force refresh from MeshCentral")
):
    """Get all devices from MeshCentral"""
    organization_id = current_admin.get("organization_id")
    
    devices = await MeshCentralService.get_devices(organization_id)
    
    return {
        "devices": devices,
        "total": len(devices),
        "online": sum(1 for d in devices if d.get("is_online")),
        "offline": sum(1 for d in devices if not d.get("is_online"))
    }


@router.get("/devices/{device_id}")
async def get_meshcentral_device(
    device_id: str,
    current_admin: dict = Depends(check_meshcentral_enabled)
):
    """Get a specific device from MeshCentral"""
    organization_id = current_admin.get("organization_id")
    
    device = await MeshCentralService.get_device(organization_id, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return device


# ==================== REMOTE ACCESS ====================

@router.get("/devices/{device_id}/remote-desktop")
async def get_remote_desktop_url(
    device_id: str,
    current_admin: dict = Depends(check_meshcentral_enabled)
):
    """Get remote desktop URL for a device"""
    organization_id = current_admin.get("organization_id")
    
    url = await MeshCentralService.get_remote_desktop_url(organization_id, device_id)
    if not url:
        raise HTTPException(status_code=403, detail="Remote desktop not available or disabled")
    
    return {"url": url}


@router.get("/devices/{device_id}/remote-terminal")
async def get_remote_terminal_url(
    device_id: str,
    current_admin: dict = Depends(check_meshcentral_enabled)
):
    """Get remote terminal URL for a device"""
    organization_id = current_admin.get("organization_id")
    
    url = await MeshCentralService.get_remote_terminal_url(organization_id, device_id)
    if not url:
        raise HTTPException(status_code=403, detail="Remote terminal not available or disabled")
    
    return {"url": url}


@router.get("/devices/{device_id}/file-transfer")
async def get_file_transfer_url(
    device_id: str,
    current_admin: dict = Depends(check_meshcentral_enabled)
):
    """Get file transfer URL for a device"""
    organization_id = current_admin.get("organization_id")
    
    url = await MeshCentralService.get_file_transfer_url(organization_id, device_id)
    if not url:
        raise HTTPException(status_code=403, detail="File transfer not available or disabled")
    
    return {"url": url}


# ==================== AGENT DOWNLOADS ====================

@router.get("/agents")
async def get_agent_downloads(current_admin: dict = Depends(check_meshcentral_enabled)):
    """Get agent download links for all platforms"""
    organization_id = current_admin.get("organization_id")
    
    agents = await MeshCentralService.get_agent_downloads(organization_id)
    
    return {"agents": agents}


# ==================== BRANDING ====================

@router.get("/branding")
async def get_meshcentral_branding(current_admin: dict = Depends(check_meshcentral_enabled)):
    """Get white-label branding configuration"""
    organization_id = current_admin.get("organization_id")
    
    config = await MeshCentralService.get_config(organization_id)
    if not config:
        raise HTTPException(status_code=404, detail="MeshCentral not configured")
    
    return {"branding": config.get("branding", {})}


@router.put("/branding")
async def update_meshcentral_branding(
    branding: Dict[str, Any],
    current_admin: dict = Depends(check_meshcentral_enabled)
):
    """Update white-label branding configuration"""
    organization_id = current_admin.get("organization_id")
    user_id = current_admin.get("id")
    
    try:
        config = await MeshCentralService.update_branding(organization_id, branding, user_id)
        return {"success": True, "branding": config.get("branding", {})}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/config-export")
async def export_meshcentral_config(current_admin: dict = Depends(check_meshcentral_enabled)):
    """Export MeshCentral config.json snippet for server configuration"""
    organization_id = current_admin.get("organization_id")
    
    mesh_config = await MeshCentralService.generate_meshcentral_config(organization_id)
    
    return {
        "config_snippet": mesh_config,
        "instructions": "Add this to your MeshCentral config.json under 'domains' section"
    }
