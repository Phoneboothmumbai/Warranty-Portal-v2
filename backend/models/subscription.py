"""
Email & Cloud Subscription models
"""
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from utils.helpers import get_ist_isoformat


class EmailSubscription(BaseModel):
    """Email/Cloud subscription (Google Workspace, Titan, Microsoft 365, etc.)"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    provider: str  # google_workspace, titan, microsoft_365, zoho, other
    provider_name: str  # Display name: "Google Workspace", "Titan Email", etc.
    domain: str  # e.g., acme.com
    plan_type: str  # basic, business_starter, business_standard, enterprise, etc.
    plan_name: Optional[str] = None  # Display name: "Business Starter", etc.
    num_users: int = 1  # Number of licenses/users
    price_per_user: Optional[float] = None  # Price per user
    billing_cycle: str = "yearly"  # monthly, yearly
    total_price: Optional[float] = None  # Total subscription cost
    currency: str = "INR"
    start_date: str  # Subscription start date
    renewal_date: Optional[str] = None  # Next renewal date
    status: str = "active"  # active, expiring_soon, expired, cancelled
    admin_email: Optional[str] = None  # Primary admin email
    secondary_admin: Optional[str] = None  # Secondary admin
    notes: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: Optional[str] = None


class EmailSubscriptionCreate(BaseModel):
    company_id: str
    provider: str
    provider_name: Optional[str] = None
    domain: str
    plan_type: str
    plan_name: Optional[str] = None
    num_users: int = 1
    price_per_user: Optional[float] = None
    billing_cycle: str = "yearly"
    total_price: Optional[float] = None
    currency: str = "INR"
    start_date: str
    renewal_date: Optional[str] = None
    status: str = "active"
    admin_email: Optional[str] = None
    secondary_admin: Optional[str] = None
    notes: Optional[str] = None


class EmailSubscriptionUpdate(BaseModel):
    company_id: Optional[str] = None
    provider: Optional[str] = None
    provider_name: Optional[str] = None
    domain: Optional[str] = None
    plan_type: Optional[str] = None
    plan_name: Optional[str] = None
    num_users: Optional[int] = None
    price_per_user: Optional[float] = None
    billing_cycle: Optional[str] = None
    total_price: Optional[float] = None
    currency: Optional[str] = None
    start_date: Optional[str] = None
    renewal_date: Optional[str] = None
    status: Optional[str] = None
    admin_email: Optional[str] = None
    secondary_admin: Optional[str] = None
    notes: Optional[str] = None


class SubscriptionTicket(BaseModel):
    """Ticket for subscription issues"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_number: str
    subscription_id: str
    company_id: str
    subject: str
    description: str
    issue_type: str  # login_issue, email_not_working, storage_full, billing, dns_issue, other
    priority: str = "medium"  # low, medium, high, urgent
    status: str = "open"  # open, in_progress, resolved, closed
    reported_by: str  # User ID who reported
    reported_by_name: str
    reported_by_email: str
    osticket_id: Optional[str] = None
    resolution: Optional[str] = None
    resolved_at: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: Optional[str] = None


class SubscriptionTicketCreate(BaseModel):
    subscription_id: str
    subject: str
    description: str
    issue_type: str = "other"
    priority: str = "medium"


class SubscriptionUserChange(BaseModel):
    """Track user additions/removals for a subscription"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subscription_id: str
    change_type: str  # "add" or "remove"
    user_count: int  # Number of users added/removed
    previous_count: int  # User count before change
    new_count: int  # User count after change
    effective_date: str  # When the change took effect
    reason: Optional[str] = None  # e.g., "New hires", "Resignations", "Department expansion"
    notes: Optional[str] = None
    changed_by: str  # Admin user ID who made the change
    changed_by_name: str  # Admin user name
    created_at: str = Field(default_factory=get_ist_isoformat)


class SubscriptionUserChangeCreate(BaseModel):
    change_type: str  # "add" or "remove"
    user_count: int  # Number of users to add/remove
    effective_date: str
    reason: Optional[str] = None
    notes: Optional[str] = None
