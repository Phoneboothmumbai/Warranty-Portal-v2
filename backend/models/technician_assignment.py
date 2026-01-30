"""
Technician Assignment Model
===========================
Manages MSP Technician to Company assignments.
This enables granular access control for MSP staff.
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from utils.helpers import get_ist_isoformat


class TechnicianAssignment(BaseModel):
    """
    Assigns an MSP Technician to specific companies they can manage.
    
    This model enables:
    - MSP admins to assign technicians to specific clients
    - Technicians to switch between assigned companies
    - Audit trail of who is managing which companies
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # The tenant (MSP)
    
    # The technician (organization_member with role=msp_technician)
    technician_id: str
    technician_email: str
    technician_name: str
    
    # The company they can access
    company_id: str
    company_name: str
    
    # Assignment type determines access level
    assignment_type: str = "full"  # full, readonly, tickets_only, devices_only
    
    # Specific permissions for this assignment (overrides default)
    permissions: List[str] = Field(default_factory=list)
    
    # Status
    is_active: bool = True
    is_deleted: bool = False
    
    # Audit
    assigned_by: str  # User ID who made the assignment
    assigned_by_name: str
    assigned_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    revoked_at: Optional[str] = None
    revoked_by: Optional[str] = None
    
    # Notes
    notes: Optional[str] = None


class TechnicianAssignmentCreate(BaseModel):
    """Create a new technician assignment"""
    technician_id: str
    company_id: str
    assignment_type: str = "full"
    permissions: Optional[List[str]] = None
    notes: Optional[str] = None


class TechnicianAssignmentUpdate(BaseModel):
    """Update an assignment"""
    assignment_type: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class BulkTechnicianAssignment(BaseModel):
    """Bulk assign a technician to multiple companies"""
    technician_id: str
    company_ids: List[str]
    assignment_type: str = "full"
    permissions: Optional[List[str]] = None
    notes: Optional[str] = None
