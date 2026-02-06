"""
Service Visit Models
====================
Multi-visit tracking with time management for service tickets.

A ticket can have multiple visits, each with:
- Assigned technician
- Start/End time (timer functionality)
- Actions taken
- Diagnostics
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from utils.helpers import get_ist_isoformat


class VisitStatus(str, Enum):
    """Visit status"""
    SCHEDULED = "scheduled"      # Visit planned
    IN_PROGRESS = "in_progress"  # Timer started, technician on-site
    COMPLETED = "completed"      # Visit completed
    CANCELLED = "cancelled"      # Visit cancelled


class ServiceVisitNew(BaseModel):
    """
    Service Visit - Individual visit record for a ticket.
    
    Supports timer functionality:
    - Start Timer: Sets start_time, status = in_progress
    - Stop Timer: Sets end_time, calculates duration_minutes, status = completed
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Tenant scoping
    
    # Parent ticket
    ticket_id: str
    ticket_number: str  # Denormalized for quick lookup
    
    # Visit number (sequential per ticket)
    visit_number: int = 1
    
    # Status
    status: str = VisitStatus.SCHEDULED.value
    
    # Technician
    technician_id: str
    technician_name: str
    
    # Scheduling
    scheduled_date: Optional[str] = None  # Planned date
    scheduled_time_from: Optional[str] = None  # Planned start time
    scheduled_time_to: Optional[str] = None    # Planned end time
    
    # Actual timing (timer functionality)
    start_time: Optional[str] = None  # When timer was started
    end_time: Optional[str] = None    # When timer was stopped
    duration_minutes: int = 0         # Calculated duration
    
    # Location snapshot (may differ from ticket location)
    visit_location: Optional[str] = None
    
    # Work details
    purpose: Optional[str] = None  # Purpose of this visit
    diagnostics: Optional[str] = None  # What was found/diagnosed
    actions_taken: List[str] = Field(default_factory=list)  # List of actions
    work_summary: Optional[str] = None  # Summary of work done
    
    # Outcome
    outcome: Optional[str] = None  # resolved, parts_needed, followup_needed, etc.
    
    # Parts used in this visit (reference to TicketPartIssue)
    parts_issued_ids: List[str] = Field(default_factory=list)
    
    # Costing for this visit
    labour_cost: float = 0
    travel_cost: float = 0
    parts_cost: float = 0  # Calculated from issued parts
    
    # Customer signature/acknowledgment
    customer_name: Optional[str] = None
    customer_signature: Optional[str] = None  # Base64 signature image
    customer_feedback: Optional[str] = None
    
    # Photos/Attachments
    photos: List[str] = Field(default_factory=list)  # URLs to photos
    attachments: List[Dict[str, str]] = Field(default_factory=list)
    
    # Notes
    internal_notes: Optional[str] = None
    
    # Flags
    is_completed: bool = False
    is_deleted: bool = False
    
    # Audit
    created_at: str = Field(default_factory=get_ist_isoformat)
    created_by_id: Optional[str] = None
    created_by_name: Optional[str] = None
    updated_at: str = Field(default_factory=get_ist_isoformat)


class ServiceVisitCreate(BaseModel):
    """Create a new service visit"""
    ticket_id: str
    technician_id: str
    scheduled_date: Optional[str] = None
    scheduled_time_from: Optional[str] = None
    scheduled_time_to: Optional[str] = None
    purpose: Optional[str] = None
    visit_location: Optional[str] = None


class ServiceVisitUpdate(BaseModel):
    """Update service visit"""
    scheduled_date: Optional[str] = None
    scheduled_time_from: Optional[str] = None
    scheduled_time_to: Optional[str] = None
    purpose: Optional[str] = None
    visit_location: Optional[str] = None
    diagnostics: Optional[str] = None
    work_summary: Optional[str] = None
    outcome: Optional[str] = None
    labour_cost: Optional[float] = None
    travel_cost: Optional[float] = None
    customer_name: Optional[str] = None
    internal_notes: Optional[str] = None


class VisitStartTimerRequest(BaseModel):
    """Request to start visit timer"""
    notes: Optional[str] = None


class VisitStopTimerRequest(BaseModel):
    """Request to stop visit timer and complete visit"""
    diagnostics: Optional[str] = None
    actions_taken: Optional[List[str]] = None
    work_summary: Optional[str] = None
    outcome: Optional[str] = None
    customer_name: Optional[str] = None
    customer_signature: Optional[str] = None
    notes: Optional[str] = None


class VisitAddActionRequest(BaseModel):
    """Add an action to visit"""
    action: str
