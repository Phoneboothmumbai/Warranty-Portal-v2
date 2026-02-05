"""
TGMS API Routes
======================
Endpoints for TGMS integration management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any
from services.tgms_service import TGMSService
from models.tgms import TGMSConfigCreate, TGMSConfigUpdate
from services.auth import get_current_admin

router = APIRouter(prefix="/api/admin/tgms", tags=["TGMS"])


# ==================== FEATURE CHECK ====================

async def check_tgms_enabled(current_admin: dict = Depends(get_current_admin)):
    """Check if TGMS feature is enabled for this organization"""
    org = current_admin.get("organization", {})
    feature_flags = org.get("feature_flags", {})
    
    # Default to True if not explicitly disabled
    if not feature_flags.get("tgms", True):
        raise HTTPException(
            status_code=403,
            detail="TGMS integration is not enabled for your organization"
        )
    
    return current_admin


# ==================== CONFIGURATION ====================

@router.get("/config")
async def get_tgms_config(current_admin: dict = Depends(check_tgms_enabled)):
    """Get TGMS configuration for current organization"""
    organization_id = current_admin.get("organization_id")
    config = await TGMSService.get_config(organization_id)
    
    if not config:
        return {"configured": False, "config": None}
    
    # Remove sensitive data
    safe_config = {**config}
    safe_config.pop("password_encrypted", None)
    if safe_config.get("api_token"):
        safe_config["api_token"] = "***configured***"
    
    return {"configured": True, "config": safe_config}


@router.post("/config")
async def create_tgms_config(
    data: TGMSConfigCreate,
    current_admin: dict = Depends(check_tgms_enabled)
):
    """Create TGMS configuration"""
    organization_id = current_admin.get("organization_id")
    user_id = current_admin.get("id")
    
    try:
        config = await TGMSService.create_config(organization_id, data, user_id)
        
        # Remove sensitive data
        config.pop("password_encrypted", None)
        if config.get("api_token"):
            config["api_token"] = "***configured***"
        
        return {"success": True, "config": config}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/config")
async def update_tgms_config(
    data: TGMSConfigUpdate,
    current_admin: dict = Depends(check_tgms_enabled)
):
    """Update TGMS configuration"""
    organization_id = current_admin.get("organization_id")
    user_id = current_admin.get("id")
    
    try:
        config = await TGMSService.update_config(organization_id, data, user_id)
        
        # Remove sensitive data
        config.pop("password_encrypted", None)
        if config.get("api_token"):
            config["api_token"] = "***configured***"
        
        return {"success": True, "config": config}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/config")
async def delete_tgms_config(current_admin: dict = Depends(check_tgms_enabled)):
    """Delete TGMS configuration"""
    organization_id = current_admin.get("organization_id")
    
    success = await TGMSService.delete_config(organization_id)
    if not success:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return {"success": True, "message": "TGMS configuration deleted"}


# ==================== CONNECTION TEST ====================

@router.post("/test-connection")
async def test_tgms_connection(current_admin: dict = Depends(check_tgms_enabled)):
    """Test connection to TGMS server"""
    organization_id = current_admin.get("organization_id")
    
    success, message = await TGMSService.test_connection(organization_id)
    
    return {"success": success, "message": message}


# ==================== DEVICES ====================

@router.get("/devices")
async def get_tgms_devices(
    current_admin: dict = Depends(check_tgms_enabled),
    refresh: bool = Query(False, description="Force refresh from TGMS")
):
    """Get all devices from TGMS"""
    organization_id = current_admin.get("organization_id")
    
    devices = await TGMSService.get_devices(organization_id)
    
    return {
        "devices": devices,
        "total": len(devices),
        "online": sum(1 for d in devices if d.get("is_online")),
        "offline": sum(1 for d in devices if not d.get("is_online"))
    }


@router.get("/devices/{device_id}")
async def get_tgms_device(
    device_id: str,
    current_admin: dict = Depends(check_tgms_enabled)
):
    """Get a specific device from TGMS"""
    organization_id = current_admin.get("organization_id")
    
    device = await TGMSService.get_device(organization_id, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return device


# ==================== REMOTE ACCESS ====================

@router.get("/devices/{device_id}/remote-desktop")
async def get_remote_desktop_url(
    device_id: str,
    current_admin: dict = Depends(check_tgms_enabled)
):
    """Get remote desktop URL for a device"""
    organization_id = current_admin.get("organization_id")
    
    url = await TGMSService.get_remote_desktop_url(organization_id, device_id)
    if not url:
        raise HTTPException(status_code=403, detail="Remote desktop not available or disabled")
    
    return {"url": url}


@router.get("/devices/{device_id}/remote-terminal")
async def get_remote_terminal_url(
    device_id: str,
    current_admin: dict = Depends(check_tgms_enabled)
):
    """Get remote terminal URL for a device"""
    organization_id = current_admin.get("organization_id")
    
    url = await TGMSService.get_remote_terminal_url(organization_id, device_id)
    if not url:
        raise HTTPException(status_code=403, detail="Remote terminal not available or disabled")
    
    return {"url": url}


@router.get("/devices/{device_id}/file-transfer")
async def get_file_transfer_url(
    device_id: str,
    current_admin: dict = Depends(check_tgms_enabled)
):
    """Get file transfer URL for a device"""
    organization_id = current_admin.get("organization_id")
    
    url = await TGMSService.get_file_transfer_url(organization_id, device_id)
    if not url:
        raise HTTPException(status_code=403, detail="File transfer not available or disabled")
    
    return {"url": url}


# ==================== AGENT DOWNLOADS ====================

@router.get("/agents")
async def get_agent_downloads(current_admin: dict = Depends(check_tgms_enabled)):
    """Get agent download links for all platforms"""
    organization_id = current_admin.get("organization_id")
    
    agents = await TGMSService.get_agent_downloads(organization_id)
    
    return {"agents": agents}


# ==================== BRANDING ====================

@router.get("/branding")
async def get_tgms_branding(current_admin: dict = Depends(check_tgms_enabled)):
    """Get white-label branding configuration"""
    organization_id = current_admin.get("organization_id")
    
    config = await TGMSService.get_config(organization_id)
    if not config:
        raise HTTPException(status_code=404, detail="TGMS not configured")
    
    return {"branding": config.get("branding", {})}


@router.put("/branding")
async def update_tgms_branding(
    branding: Dict[str, Any],
    current_admin: dict = Depends(check_tgms_enabled)
):
    """Update white-label branding configuration"""
    organization_id = current_admin.get("organization_id")
    user_id = current_admin.get("id")
    
    try:
        config = await TGMSService.update_branding(organization_id, branding, user_id)
        return {"success": True, "branding": config.get("branding", {})}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/config-export")
async def export_tgms_config(current_admin: dict = Depends(check_tgms_enabled)):
    """Export TGMS config.json snippet for server configuration"""
    organization_id = current_admin.get("organization_id")
    
    mesh_config = await TGMSService.generate_tgms_config(organization_id)
    
    return {
        "config_snippet": mesh_config,
        "instructions": "Add this to your TGMS config.json under 'domains' section"
    }
