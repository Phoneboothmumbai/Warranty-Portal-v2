"""
Ticket Types & Workflow Models
==============================
Multi-workflow ticket system supporting various business processes:
- Technical Support (with Job Lifecycle)
- Sales Inquiry
- Quote Request
- Order/Purchase Tracking
- General Inquiry
- Feedback/Suggestion
- Return/Refund
- Callback Request
- Partnership Inquiry
- Complaint
- Installation Request
- Training Request
- Renewal Request
- Billing Inquiry
- Maintenance Request
- Site Visit Request
- Demo Request
- Onboarding Request
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from utils.helpers import get_ist_isoformat


# ==================== WORKFLOW STATUS ====================

class WorkflowStatus(BaseModel):
    """Individual status in a workflow"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str
    color: str = "#6B7280"  # Default gray
    order: int = 0
    is_initial: bool = False  # First status in workflow
    is_terminal: bool = False  # Marks ticket as closed/complete
    is_success: bool = False  # Positive outcome (Won, Completed, etc.)
    is_failure: bool = False  # Negative outcome (Lost, Cancelled, etc.)
    can_transition_to: List[str] = Field(default_factory=list)  # List of status slugs


class CustomField(BaseModel):
    """Custom field definition for ticket type"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str
    field_type: str  # text, textarea, number, date, datetime, select, multiselect, checkbox, email, phone, url, currency
    required: bool = False
    order: int = 0
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    default_value: Optional[Any] = None
    options: List[Dict[str, str]] = Field(default_factory=list)  # For select/multiselect: [{value, label}]
    validation: Optional[Dict[str, Any]] = None  # {min, max, pattern, etc.}
    show_in_list: bool = False  # Show in ticket list view
    show_in_create: bool = True  # Show during ticket creation


# ==================== TICKET TYPE ====================

class TicketType(BaseModel):
    """
    Ticket Type definition with workflow
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    
    # Basic Info
    name: str
    slug: str
    description: Optional[str] = None
    icon: str = "ticket"  # Lucide icon name
    color: str = "#3B82F6"  # Primary color
    
    # Category for grouping
    category: str = "general"  # support, sales, operations, hr, finance, general
    
    # Workflow
    workflow_statuses: List[WorkflowStatus] = Field(default_factory=list)
    
    # Custom Fields
    custom_fields: List[CustomField] = Field(default_factory=list)
    
    # Defaults
    default_department_id: Optional[str] = None
    default_sla_id: Optional[str] = None
    default_priority: str = "medium"
    
    # Special Flags
    requires_job_lifecycle: bool = False  # Only for technical support
    requires_device: bool = False  # Needs device selection
    requires_company: bool = True  # Needs company selection
    requires_contact: bool = True  # Needs contact info
    enable_customer_portal: bool = True  # Visible in customer portal
    
    # Auto-assignment rules
    auto_assign_enabled: bool = False
    auto_assign_rules: Dict[str, Any] = Field(default_factory=dict)
    
    # Notifications
    notify_on_create: bool = True
    notify_on_update: bool = True
    notify_on_close: bool = True
    
    # Status
    is_active: bool = True
    is_system: bool = False  # System types can't be deleted
    is_deleted: bool = False
    
    # Metadata
    created_at: str = Field(default_factory=get_ist_isoformat)
    created_by_id: Optional[str] = None
    updated_at: str = Field(default_factory=get_ist_isoformat)
    updated_by_id: Optional[str] = None
    
    # Usage stats (computed)
    ticket_count: int = 0


class TicketTypeCreate(BaseModel):
    """Create ticket type request"""
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    icon: str = "ticket"
    color: str = "#3B82F6"
    category: str = "general"
    default_priority: str = "medium"
    requires_device: bool = False
    requires_company: bool = True
    requires_contact: bool = True


class TicketTypeUpdate(BaseModel):
    """Update ticket type request"""
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    category: Optional[str] = None
    default_department_id: Optional[str] = None
    default_sla_id: Optional[str] = None
    default_priority: Optional[str] = None
    requires_device: Optional[bool] = None
    requires_company: Optional[bool] = None
    requires_contact: Optional[bool] = None
    enable_customer_portal: Optional[bool] = None
    is_active: Optional[bool] = None


# ==================== DEFAULT TICKET TYPES ====================

def get_default_ticket_types(organization_id: str) -> List[Dict]:
    """
    Generate all default ticket types for a new organization.
    Each type has its own workflow statuses and custom fields.
    """
    
    ticket_types = []
    
    # ========== 1. TECHNICAL SUPPORT ==========
    ticket_types.append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "Technical Support",
        "slug": "technical-support",
        "description": "Technical issues, repairs, and service requests requiring field visits or device repair",
        "icon": "wrench",
        "color": "#EF4444",
        "category": "support",
        "requires_job_lifecycle": True,
        "requires_device": True,
        "requires_company": True,
        "requires_contact": True,
        "default_priority": "high",
        "is_system": True,
        "is_active": True,
        "is_deleted": False,
        "enable_customer_portal": True,
        "workflow_statuses": [
            {"id": str(uuid.uuid4()), "name": "New", "slug": "new", "color": "#6B7280", "order": 0, "is_initial": True, "can_transition_to": ["assigned", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Assigned", "slug": "assigned", "color": "#3B82F6", "order": 1, "can_transition_to": ["in_progress", "new", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "In Progress", "slug": "in_progress", "color": "#F59E0B", "order": 2, "can_transition_to": ["pending_parts", "device_pickup", "completed", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Pending Parts", "slug": "pending_parts", "color": "#8B5CF6", "order": 3, "can_transition_to": ["in_progress", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Device Pickup", "slug": "device_pickup", "color": "#EC4899", "order": 4, "can_transition_to": ["device_under_repair", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Under Repair", "slug": "device_under_repair", "color": "#F97316", "order": 5, "can_transition_to": ["ready_for_delivery", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Ready for Delivery", "slug": "ready_for_delivery", "color": "#14B8A6", "order": 6, "can_transition_to": ["out_for_delivery"]},
            {"id": str(uuid.uuid4()), "name": "Out for Delivery", "slug": "out_for_delivery", "color": "#06B6D4", "order": 7, "can_transition_to": ["completed"]},
            {"id": str(uuid.uuid4()), "name": "Completed", "slug": "completed", "color": "#22C55E", "order": 8, "can_transition_to": ["closed"]},
            {"id": str(uuid.uuid4()), "name": "Closed", "slug": "closed", "color": "#10B981", "order": 9, "is_terminal": True, "is_success": True},
            {"id": str(uuid.uuid4()), "name": "Cancelled", "slug": "cancelled", "color": "#EF4444", "order": 10, "is_terminal": True, "is_failure": True}
        ],
        "custom_fields": [
            {"id": str(uuid.uuid4()), "name": "Issue Type", "slug": "issue_type", "field_type": "select", "required": True, "order": 1, "show_in_list": True, "show_in_create": True,
             "options": [{"value": "hardware", "label": "Hardware Issue"}, {"value": "software", "label": "Software Issue"}, {"value": "network", "label": "Network Issue"}, {"value": "peripheral", "label": "Peripheral Issue"}, {"value": "other", "label": "Other"}]},
            {"id": str(uuid.uuid4()), "name": "Error Message", "slug": "error_message", "field_type": "textarea", "required": False, "order": 2, "placeholder": "Copy any error messages here..."},
            {"id": str(uuid.uuid4()), "name": "Steps to Reproduce", "slug": "steps_to_reproduce", "field_type": "textarea", "required": False, "order": 3}
        ],
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # ========== 2. SALES INQUIRY ==========
    ticket_types.append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "Sales Inquiry",
        "slug": "sales-inquiry",
        "description": "New business inquiries, product interest, and sales opportunities",
        "icon": "trending-up",
        "color": "#10B981",
        "category": "sales",
        "requires_job_lifecycle": False,
        "requires_device": False,
        "requires_company": True,
        "requires_contact": True,
        "default_priority": "medium",
        "is_system": True,
        "workflow_statuses": [
            {"id": str(uuid.uuid4()), "name": "New Lead", "slug": "new", "color": "#6B7280", "order": 0, "is_initial": True, "can_transition_to": ["contacted", "qualified", "disqualified"]},
            {"id": str(uuid.uuid4()), "name": "Contacted", "slug": "contacted", "color": "#3B82F6", "order": 1, "can_transition_to": ["qualified", "demo_scheduled", "disqualified"]},
            {"id": str(uuid.uuid4()), "name": "Qualified", "slug": "qualified", "color": "#8B5CF6", "order": 2, "can_transition_to": ["demo_scheduled", "proposal_sent", "disqualified"]},
            {"id": str(uuid.uuid4()), "name": "Demo Scheduled", "slug": "demo_scheduled", "color": "#F59E0B", "order": 3, "can_transition_to": ["demo_completed", "disqualified"]},
            {"id": str(uuid.uuid4()), "name": "Demo Completed", "slug": "demo_completed", "color": "#14B8A6", "order": 4, "can_transition_to": ["proposal_sent", "disqualified"]},
            {"id": str(uuid.uuid4()), "name": "Proposal Sent", "slug": "proposal_sent", "color": "#EC4899", "order": 5, "can_transition_to": ["negotiation", "won", "lost"]},
            {"id": str(uuid.uuid4()), "name": "Negotiation", "slug": "negotiation", "color": "#F97316", "order": 6, "can_transition_to": ["won", "lost"]},
            {"id": str(uuid.uuid4()), "name": "Won", "slug": "won", "color": "#22C55E", "order": 7, "is_terminal": True, "is_success": True},
            {"id": str(uuid.uuid4()), "name": "Lost", "slug": "lost", "color": "#EF4444", "order": 8, "is_terminal": True, "is_failure": True},
            {"id": str(uuid.uuid4()), "name": "Disqualified", "slug": "disqualified", "color": "#6B7280", "order": 9, "is_terminal": True, "is_failure": True}
        ],
        "custom_fields": [
            {"id": str(uuid.uuid4()), "name": "Products Interested", "slug": "products_interested", "field_type": "multiselect", "required": True, "order": 1, "show_in_list": True,
             "options": [{"value": "hardware", "label": "Hardware"}, {"value": "software", "label": "Software"}, {"value": "services", "label": "Services"}, {"value": "amc", "label": "AMC/Support"}, {"value": "other", "label": "Other"}]},
            {"id": str(uuid.uuid4()), "name": "Budget Range", "slug": "budget_range", "field_type": "select", "required": False, "order": 2, "show_in_list": True,
             "options": [{"value": "under_50k", "label": "Under ₹50,000"}, {"value": "50k_1l", "label": "₹50,000 - ₹1 Lakh"}, {"value": "1l_5l", "label": "₹1 - ₹5 Lakh"}, {"value": "5l_10l", "label": "₹5 - ₹10 Lakh"}, {"value": "above_10l", "label": "Above ₹10 Lakh"}]},
            {"id": str(uuid.uuid4()), "name": "Expected Timeline", "slug": "expected_timeline", "field_type": "select", "required": False, "order": 3,
             "options": [{"value": "immediate", "label": "Immediate"}, {"value": "1_month", "label": "Within 1 Month"}, {"value": "3_months", "label": "1-3 Months"}, {"value": "6_months", "label": "3-6 Months"}, {"value": "future", "label": "Future Planning"}]},
            {"id": str(uuid.uuid4()), "name": "Lead Source", "slug": "lead_source", "field_type": "select", "required": False, "order": 4, "show_in_list": True,
             "options": [{"value": "website", "label": "Website"}, {"value": "referral", "label": "Referral"}, {"value": "cold_call", "label": "Cold Call"}, {"value": "exhibition", "label": "Exhibition"}, {"value": "social_media", "label": "Social Media"}, {"value": "google", "label": "Google"}, {"value": "other", "label": "Other"}]},
            {"id": str(uuid.uuid4()), "name": "Estimated Value", "slug": "estimated_value", "field_type": "currency", "required": False, "order": 5, "show_in_list": True},
            {"id": str(uuid.uuid4()), "name": "Competition", "slug": "competition", "field_type": "text", "required": False, "order": 6, "placeholder": "Known competitors in this deal"},
            {"id": str(uuid.uuid4()), "name": "Decision Maker", "slug": "decision_maker", "field_type": "text", "required": False, "order": 7},
            {"id": str(uuid.uuid4()), "name": "Next Follow-up Date", "slug": "next_followup_date", "field_type": "date", "required": False, "order": 8}
        ],
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # ========== 3. QUOTE REQUEST ==========
    ticket_types.append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "Quote Request",
        "slug": "quote-request",
        "description": "Customer requests for pricing quotations",
        "icon": "file-text",
        "color": "#8B5CF6",
        "category": "sales",
        "requires_job_lifecycle": False,
        "requires_device": False,
        "requires_company": True,
        "requires_contact": True,
        "default_priority": "high",
        "is_system": True,
        "workflow_statuses": [
            {"id": str(uuid.uuid4()), "name": "New Request", "slug": "new", "color": "#6B7280", "order": 0, "is_initial": True, "can_transition_to": ["preparing_quote", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Preparing Quote", "slug": "preparing_quote", "color": "#3B82F6", "order": 1, "can_transition_to": ["quote_sent", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Quote Sent", "slug": "quote_sent", "color": "#F59E0B", "order": 2, "can_transition_to": ["awaiting_response", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Awaiting Response", "slug": "awaiting_response", "color": "#8B5CF6", "order": 3, "can_transition_to": ["negotiation", "accepted", "rejected"]},
            {"id": str(uuid.uuid4()), "name": "Negotiation", "slug": "negotiation", "color": "#EC4899", "order": 4, "can_transition_to": ["revised_quote", "accepted", "rejected"]},
            {"id": str(uuid.uuid4()), "name": "Revised Quote", "slug": "revised_quote", "color": "#14B8A6", "order": 5, "can_transition_to": ["awaiting_response", "accepted", "rejected"]},
            {"id": str(uuid.uuid4()), "name": "Accepted", "slug": "accepted", "color": "#22C55E", "order": 6, "is_terminal": True, "is_success": True},
            {"id": str(uuid.uuid4()), "name": "Rejected", "slug": "rejected", "color": "#EF4444", "order": 7, "is_terminal": True, "is_failure": True},
            {"id": str(uuid.uuid4()), "name": "Cancelled", "slug": "cancelled", "color": "#6B7280", "order": 8, "is_terminal": True, "is_failure": True}
        ],
        "custom_fields": [
            {"id": str(uuid.uuid4()), "name": "Products/Services Required", "slug": "products_required", "field_type": "textarea", "required": True, "order": 1, "placeholder": "List products or services needed with quantities"},
            {"id": str(uuid.uuid4()), "name": "Quantity", "slug": "quantity", "field_type": "number", "required": False, "order": 2},
            {"id": str(uuid.uuid4()), "name": "Delivery Location", "slug": "delivery_location", "field_type": "text", "required": False, "order": 3},
            {"id": str(uuid.uuid4()), "name": "Required By Date", "slug": "required_by_date", "field_type": "date", "required": False, "order": 4},
            {"id": str(uuid.uuid4()), "name": "Special Requirements", "slug": "special_requirements", "field_type": "textarea", "required": False, "order": 5},
            {"id": str(uuid.uuid4()), "name": "Quote Amount", "slug": "quote_amount", "field_type": "currency", "required": False, "order": 6, "show_in_list": True},
            {"id": str(uuid.uuid4()), "name": "Quote Reference", "slug": "quote_reference", "field_type": "text", "required": False, "order": 7, "show_in_list": True}
        ],
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # ========== 4. ORDER/PURCHASE ==========
    ticket_types.append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "Order / Purchase",
        "slug": "order-purchase",
        "description": "Track customer orders and purchases from placement to delivery",
        "icon": "shopping-cart",
        "color": "#F59E0B",
        "category": "operations",
        "requires_job_lifecycle": False,
        "requires_device": False,
        "requires_company": True,
        "requires_contact": True,
        "default_priority": "high",
        "is_system": True,
        "workflow_statuses": [
            {"id": str(uuid.uuid4()), "name": "Order Received", "slug": "new", "color": "#6B7280", "order": 0, "is_initial": True, "can_transition_to": ["confirmed", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Confirmed", "slug": "confirmed", "color": "#3B82F6", "order": 1, "can_transition_to": ["processing", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Processing", "slug": "processing", "color": "#8B5CF6", "order": 2, "can_transition_to": ["ready_to_ship", "on_hold", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "On Hold", "slug": "on_hold", "color": "#F97316", "order": 3, "can_transition_to": ["processing", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Ready to Ship", "slug": "ready_to_ship", "color": "#14B8A6", "order": 4, "can_transition_to": ["shipped"]},
            {"id": str(uuid.uuid4()), "name": "Shipped", "slug": "shipped", "color": "#EC4899", "order": 5, "can_transition_to": ["out_for_delivery"]},
            {"id": str(uuid.uuid4()), "name": "Out for Delivery", "slug": "out_for_delivery", "color": "#06B6D4", "order": 6, "can_transition_to": ["delivered", "delivery_failed"]},
            {"id": str(uuid.uuid4()), "name": "Delivered", "slug": "delivered", "color": "#22C55E", "order": 7, "is_terminal": True, "is_success": True},
            {"id": str(uuid.uuid4()), "name": "Delivery Failed", "slug": "delivery_failed", "color": "#EF4444", "order": 8, "can_transition_to": ["out_for_delivery", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Cancelled", "slug": "cancelled", "color": "#EF4444", "order": 9, "is_terminal": True, "is_failure": True}
        ],
        "custom_fields": [
            {"id": str(uuid.uuid4()), "name": "Order Number", "slug": "order_number", "field_type": "text", "required": False, "order": 1, "show_in_list": True},
            {"id": str(uuid.uuid4()), "name": "Items Ordered", "slug": "items_ordered", "field_type": "textarea", "required": True, "order": 2, "placeholder": "List items with quantities"},
            {"id": str(uuid.uuid4()), "name": "Order Amount", "slug": "order_amount", "field_type": "currency", "required": False, "order": 3, "show_in_list": True},
            {"id": str(uuid.uuid4()), "name": "Payment Status", "slug": "payment_status", "field_type": "select", "required": False, "order": 4, "show_in_list": True,
             "options": [{"value": "pending", "label": "Pending"}, {"value": "partial", "label": "Partial"}, {"value": "paid", "label": "Paid"}, {"value": "refunded", "label": "Refunded"}]},
            {"id": str(uuid.uuid4()), "name": "Delivery Address", "slug": "delivery_address", "field_type": "textarea", "required": True, "order": 5},
            {"id": str(uuid.uuid4()), "name": "Expected Delivery", "slug": "expected_delivery", "field_type": "date", "required": False, "order": 6},
            {"id": str(uuid.uuid4()), "name": "Tracking Number", "slug": "tracking_number", "field_type": "text", "required": False, "order": 7, "show_in_list": True},
            {"id": str(uuid.uuid4()), "name": "Courier/Logistics", "slug": "courier", "field_type": "text", "required": False, "order": 8}
        ],
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # ========== 5. GENERAL INQUIRY ==========
    ticket_types.append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "General Inquiry",
        "slug": "general-inquiry",
        "description": "General questions and information requests",
        "icon": "help-circle",
        "color": "#3B82F6",
        "category": "general",
        "requires_job_lifecycle": False,
        "requires_device": False,
        "requires_company": False,
        "requires_contact": True,
        "default_priority": "low",
        "is_system": True,
        "workflow_statuses": [
            {"id": str(uuid.uuid4()), "name": "New", "slug": "new", "color": "#6B7280", "order": 0, "is_initial": True, "can_transition_to": ["in_progress", "closed"]},
            {"id": str(uuid.uuid4()), "name": "In Progress", "slug": "in_progress", "color": "#3B82F6", "order": 1, "can_transition_to": ["awaiting_response", "resolved"]},
            {"id": str(uuid.uuid4()), "name": "Awaiting Response", "slug": "awaiting_response", "color": "#F59E0B", "order": 2, "can_transition_to": ["in_progress", "resolved"]},
            {"id": str(uuid.uuid4()), "name": "Resolved", "slug": "resolved", "color": "#22C55E", "order": 3, "can_transition_to": ["closed"]},
            {"id": str(uuid.uuid4()), "name": "Closed", "slug": "closed", "color": "#10B981", "order": 4, "is_terminal": True, "is_success": True}
        ],
        "custom_fields": [
            {"id": str(uuid.uuid4()), "name": "Inquiry Category", "slug": "inquiry_category", "field_type": "select", "required": True, "order": 1, "show_in_list": True,
             "options": [{"value": "product_info", "label": "Product Information"}, {"value": "pricing", "label": "Pricing"}, {"value": "availability", "label": "Availability"}, {"value": "hours", "label": "Business Hours"}, {"value": "location", "label": "Location/Directions"}, {"value": "other", "label": "Other"}]},
            {"id": str(uuid.uuid4()), "name": "Question", "slug": "question", "field_type": "textarea", "required": True, "order": 2}
        ],
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # ========== 6. FEEDBACK / SUGGESTION ==========
    ticket_types.append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "Feedback / Suggestion",
        "slug": "feedback-suggestion",
        "description": "Customer feedback, suggestions, and reviews",
        "icon": "message-square",
        "color": "#14B8A6",
        "category": "general",
        "requires_job_lifecycle": False,
        "requires_device": False,
        "requires_company": False,
        "requires_contact": True,
        "default_priority": "low",
        "is_system": True,
        "workflow_statuses": [
            {"id": str(uuid.uuid4()), "name": "Received", "slug": "new", "color": "#6B7280", "order": 0, "is_initial": True, "can_transition_to": ["acknowledged", "closed"]},
            {"id": str(uuid.uuid4()), "name": "Acknowledged", "slug": "acknowledged", "color": "#3B82F6", "order": 1, "can_transition_to": ["under_review", "closed"]},
            {"id": str(uuid.uuid4()), "name": "Under Review", "slug": "under_review", "color": "#8B5CF6", "order": 2, "can_transition_to": ["action_planned", "no_action", "closed"]},
            {"id": str(uuid.uuid4()), "name": "Action Planned", "slug": "action_planned", "color": "#F59E0B", "order": 3, "can_transition_to": ["implemented", "closed"]},
            {"id": str(uuid.uuid4()), "name": "Implemented", "slug": "implemented", "color": "#22C55E", "order": 4, "is_terminal": True, "is_success": True},
            {"id": str(uuid.uuid4()), "name": "No Action Required", "slug": "no_action", "color": "#6B7280", "order": 5, "is_terminal": True},
            {"id": str(uuid.uuid4()), "name": "Closed", "slug": "closed", "color": "#10B981", "order": 6, "is_terminal": True, "is_success": True}
        ],
        "custom_fields": [
            {"id": str(uuid.uuid4()), "name": "Feedback Type", "slug": "feedback_type", "field_type": "select", "required": True, "order": 1, "show_in_list": True,
             "options": [{"value": "compliment", "label": "Compliment"}, {"value": "suggestion", "label": "Suggestion"}, {"value": "complaint", "label": "Complaint"}, {"value": "review", "label": "Review"}, {"value": "other", "label": "Other"}]},
            {"id": str(uuid.uuid4()), "name": "Rating", "slug": "rating", "field_type": "select", "required": False, "order": 2, "show_in_list": True,
             "options": [{"value": "5", "label": "5 - Excellent"}, {"value": "4", "label": "4 - Good"}, {"value": "3", "label": "3 - Average"}, {"value": "2", "label": "2 - Poor"}, {"value": "1", "label": "1 - Very Poor"}]},
            {"id": str(uuid.uuid4()), "name": "Area of Feedback", "slug": "feedback_area", "field_type": "select", "required": False, "order": 3,
             "options": [{"value": "product", "label": "Product"}, {"value": "service", "label": "Service"}, {"value": "staff", "label": "Staff"}, {"value": "pricing", "label": "Pricing"}, {"value": "website", "label": "Website/App"}, {"value": "other", "label": "Other"}]},
            {"id": str(uuid.uuid4()), "name": "Feedback Details", "slug": "feedback_details", "field_type": "textarea", "required": True, "order": 4}
        ],
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # ========== 7. RETURN / REFUND ==========
    ticket_types.append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "Return / Refund",
        "slug": "return-refund",
        "description": "Product returns, exchanges, and refund requests",
        "icon": "rotate-ccw",
        "color": "#EF4444",
        "category": "operations",
        "requires_job_lifecycle": False,
        "requires_device": False,
        "requires_company": True,
        "requires_contact": True,
        "default_priority": "high",
        "is_system": True,
        "workflow_statuses": [
            {"id": str(uuid.uuid4()), "name": "Request Received", "slug": "new", "color": "#6B7280", "order": 0, "is_initial": True, "can_transition_to": ["under_review", "rejected"]},
            {"id": str(uuid.uuid4()), "name": "Under Review", "slug": "under_review", "color": "#3B82F6", "order": 1, "can_transition_to": ["approved", "rejected"]},
            {"id": str(uuid.uuid4()), "name": "Approved", "slug": "approved", "color": "#22C55E", "order": 2, "can_transition_to": ["pickup_scheduled", "item_received"]},
            {"id": str(uuid.uuid4()), "name": "Pickup Scheduled", "slug": "pickup_scheduled", "color": "#8B5CF6", "order": 3, "can_transition_to": ["item_received"]},
            {"id": str(uuid.uuid4()), "name": "Item Received", "slug": "item_received", "color": "#14B8A6", "order": 4, "can_transition_to": ["inspection", "refund_processing", "exchange_processing"]},
            {"id": str(uuid.uuid4()), "name": "Under Inspection", "slug": "inspection", "color": "#F59E0B", "order": 5, "can_transition_to": ["refund_processing", "exchange_processing", "rejected"]},
            {"id": str(uuid.uuid4()), "name": "Refund Processing", "slug": "refund_processing", "color": "#EC4899", "order": 6, "can_transition_to": ["refund_completed"]},
            {"id": str(uuid.uuid4()), "name": "Exchange Processing", "slug": "exchange_processing", "color": "#06B6D4", "order": 7, "can_transition_to": ["exchange_shipped"]},
            {"id": str(uuid.uuid4()), "name": "Refund Completed", "slug": "refund_completed", "color": "#22C55E", "order": 8, "is_terminal": True, "is_success": True},
            {"id": str(uuid.uuid4()), "name": "Exchange Shipped", "slug": "exchange_shipped", "color": "#22C55E", "order": 9, "is_terminal": True, "is_success": True},
            {"id": str(uuid.uuid4()), "name": "Rejected", "slug": "rejected", "color": "#EF4444", "order": 10, "is_terminal": True, "is_failure": True}
        ],
        "custom_fields": [
            {"id": str(uuid.uuid4()), "name": "Original Order Number", "slug": "original_order", "field_type": "text", "required": True, "order": 1, "show_in_list": True},
            {"id": str(uuid.uuid4()), "name": "Return Type", "slug": "return_type", "field_type": "select", "required": True, "order": 2, "show_in_list": True,
             "options": [{"value": "refund", "label": "Refund"}, {"value": "exchange", "label": "Exchange"}, {"value": "repair", "label": "Repair"}]},
            {"id": str(uuid.uuid4()), "name": "Return Reason", "slug": "return_reason", "field_type": "select", "required": True, "order": 3,
             "options": [{"value": "defective", "label": "Defective Product"}, {"value": "wrong_item", "label": "Wrong Item Received"}, {"value": "not_as_described", "label": "Not as Described"}, {"value": "changed_mind", "label": "Changed Mind"}, {"value": "better_price", "label": "Found Better Price"}, {"value": "other", "label": "Other"}]},
            {"id": str(uuid.uuid4()), "name": "Items to Return", "slug": "items_to_return", "field_type": "textarea", "required": True, "order": 4},
            {"id": str(uuid.uuid4()), "name": "Purchase Date", "slug": "purchase_date", "field_type": "date", "required": False, "order": 5},
            {"id": str(uuid.uuid4()), "name": "Refund Amount", "slug": "refund_amount", "field_type": "currency", "required": False, "order": 6, "show_in_list": True},
            {"id": str(uuid.uuid4()), "name": "Refund Method", "slug": "refund_method", "field_type": "select", "required": False, "order": 7,
             "options": [{"value": "original", "label": "Original Payment Method"}, {"value": "bank", "label": "Bank Transfer"}, {"value": "credit", "label": "Store Credit"}, {"value": "cheque", "label": "Cheque"}]}
        ],
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # ========== 8. CALLBACK REQUEST ==========
    ticket_types.append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "Callback Request",
        "slug": "callback-request",
        "description": "Customer requests for callback from sales or support",
        "icon": "phone-callback",
        "color": "#06B6D4",
        "category": "general",
        "requires_job_lifecycle": False,
        "requires_device": False,
        "requires_company": False,
        "requires_contact": True,
        "default_priority": "medium",
        "is_system": True,
        "workflow_statuses": [
            {"id": str(uuid.uuid4()), "name": "Requested", "slug": "new", "color": "#6B7280", "order": 0, "is_initial": True, "can_transition_to": ["scheduled", "called"]},
            {"id": str(uuid.uuid4()), "name": "Scheduled", "slug": "scheduled", "color": "#3B82F6", "order": 1, "can_transition_to": ["called", "no_answer"]},
            {"id": str(uuid.uuid4()), "name": "Called", "slug": "called", "color": "#22C55E", "order": 2, "can_transition_to": ["resolved", "follow_up_needed"]},
            {"id": str(uuid.uuid4()), "name": "No Answer", "slug": "no_answer", "color": "#F59E0B", "order": 3, "can_transition_to": ["scheduled", "closed"]},
            {"id": str(uuid.uuid4()), "name": "Follow-up Needed", "slug": "follow_up_needed", "color": "#8B5CF6", "order": 4, "can_transition_to": ["scheduled", "resolved"]},
            {"id": str(uuid.uuid4()), "name": "Resolved", "slug": "resolved", "color": "#22C55E", "order": 5, "is_terminal": True, "is_success": True},
            {"id": str(uuid.uuid4()), "name": "Closed", "slug": "closed", "color": "#10B981", "order": 6, "is_terminal": True}
        ],
        "custom_fields": [
            {"id": str(uuid.uuid4()), "name": "Callback Topic", "slug": "callback_topic", "field_type": "select", "required": True, "order": 1, "show_in_list": True,
             "options": [{"value": "sales", "label": "Sales Inquiry"}, {"value": "support", "label": "Support"}, {"value": "billing", "label": "Billing"}, {"value": "complaint", "label": "Complaint"}, {"value": "other", "label": "Other"}]},
            {"id": str(uuid.uuid4()), "name": "Preferred Date", "slug": "preferred_date", "field_type": "date", "required": False, "order": 2},
            {"id": str(uuid.uuid4()), "name": "Preferred Time", "slug": "preferred_time", "field_type": "select", "required": False, "order": 3,
             "options": [{"value": "morning", "label": "Morning (9 AM - 12 PM)"}, {"value": "afternoon", "label": "Afternoon (12 PM - 4 PM)"}, {"value": "evening", "label": "Evening (4 PM - 7 PM)"}, {"value": "anytime", "label": "Anytime"}]},
            {"id": str(uuid.uuid4()), "name": "Brief Description", "slug": "brief_description", "field_type": "textarea", "required": False, "order": 4},
            {"id": str(uuid.uuid4()), "name": "Call Notes", "slug": "call_notes", "field_type": "textarea", "required": False, "order": 5}
        ],
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # ========== 9. PARTNERSHIP INQUIRY ==========
    ticket_types.append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "Partnership Inquiry",
        "slug": "partnership-inquiry",
        "description": "Business partnership, reseller, and collaboration inquiries",
        "icon": "handshake",
        "color": "#8B5CF6",
        "category": "sales",
        "requires_job_lifecycle": False,
        "requires_device": False,
        "requires_company": True,
        "requires_contact": True,
        "default_priority": "medium",
        "is_system": True,
        "workflow_statuses": [
            {"id": str(uuid.uuid4()), "name": "Inquiry Received", "slug": "new", "color": "#6B7280", "order": 0, "is_initial": True, "can_transition_to": ["initial_review", "not_suitable"]},
            {"id": str(uuid.uuid4()), "name": "Initial Review", "slug": "initial_review", "color": "#3B82F6", "order": 1, "can_transition_to": ["meeting_scheduled", "not_suitable"]},
            {"id": str(uuid.uuid4()), "name": "Meeting Scheduled", "slug": "meeting_scheduled", "color": "#F59E0B", "order": 2, "can_transition_to": ["meeting_completed", "not_suitable"]},
            {"id": str(uuid.uuid4()), "name": "Meeting Completed", "slug": "meeting_completed", "color": "#8B5CF6", "order": 3, "can_transition_to": ["proposal_stage", "not_suitable"]},
            {"id": str(uuid.uuid4()), "name": "Proposal Stage", "slug": "proposal_stage", "color": "#EC4899", "order": 4, "can_transition_to": ["negotiation", "not_suitable"]},
            {"id": str(uuid.uuid4()), "name": "Negotiation", "slug": "negotiation", "color": "#14B8A6", "order": 5, "can_transition_to": ["partnership_active", "not_suitable"]},
            {"id": str(uuid.uuid4()), "name": "Partnership Active", "slug": "partnership_active", "color": "#22C55E", "order": 6, "is_terminal": True, "is_success": True},
            {"id": str(uuid.uuid4()), "name": "Not Suitable", "slug": "not_suitable", "color": "#EF4444", "order": 7, "is_terminal": True, "is_failure": True}
        ],
        "custom_fields": [
            {"id": str(uuid.uuid4()), "name": "Partnership Type", "slug": "partnership_type", "field_type": "select", "required": True, "order": 1, "show_in_list": True,
             "options": [{"value": "reseller", "label": "Reseller"}, {"value": "distributor", "label": "Distributor"}, {"value": "technology", "label": "Technology Partner"}, {"value": "integration", "label": "Integration Partner"}, {"value": "referral", "label": "Referral Partner"}, {"value": "other", "label": "Other"}]},
            {"id": str(uuid.uuid4()), "name": "Company Website", "slug": "company_website", "field_type": "url", "required": False, "order": 2},
            {"id": str(uuid.uuid4()), "name": "Years in Business", "slug": "years_in_business", "field_type": "number", "required": False, "order": 3},
            {"id": str(uuid.uuid4()), "name": "Current Business", "slug": "current_business", "field_type": "textarea", "required": False, "order": 4, "placeholder": "Describe your current business"},
            {"id": str(uuid.uuid4()), "name": "Partnership Goals", "slug": "partnership_goals", "field_type": "textarea", "required": False, "order": 5},
            {"id": str(uuid.uuid4()), "name": "Geographic Coverage", "slug": "geographic_coverage", "field_type": "text", "required": False, "order": 6}
        ],
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # ========== 10. COMPLAINT ==========
    ticket_types.append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "Complaint",
        "slug": "complaint",
        "description": "Customer complaints requiring investigation and resolution",
        "icon": "alert-triangle",
        "color": "#EF4444",
        "category": "support",
        "requires_job_lifecycle": False,
        "requires_device": False,
        "requires_company": False,
        "requires_contact": True,
        "default_priority": "high",
        "is_system": True,
        "workflow_statuses": [
            {"id": str(uuid.uuid4()), "name": "Complaint Received", "slug": "new", "color": "#EF4444", "order": 0, "is_initial": True, "can_transition_to": ["acknowledged", "closed"]},
            {"id": str(uuid.uuid4()), "name": "Acknowledged", "slug": "acknowledged", "color": "#3B82F6", "order": 1, "can_transition_to": ["investigating"]},
            {"id": str(uuid.uuid4()), "name": "Investigating", "slug": "investigating", "color": "#F59E0B", "order": 2, "can_transition_to": ["action_required", "resolved"]},
            {"id": str(uuid.uuid4()), "name": "Action Required", "slug": "action_required", "color": "#8B5CF6", "order": 3, "can_transition_to": ["action_taken", "escalated"]},
            {"id": str(uuid.uuid4()), "name": "Escalated", "slug": "escalated", "color": "#EC4899", "order": 4, "can_transition_to": ["action_taken"]},
            {"id": str(uuid.uuid4()), "name": "Action Taken", "slug": "action_taken", "color": "#14B8A6", "order": 5, "can_transition_to": ["resolved", "customer_followup"]},
            {"id": str(uuid.uuid4()), "name": "Customer Follow-up", "slug": "customer_followup", "color": "#06B6D4", "order": 6, "can_transition_to": ["resolved", "reopened"]},
            {"id": str(uuid.uuid4()), "name": "Reopened", "slug": "reopened", "color": "#F97316", "order": 7, "can_transition_to": ["investigating"]},
            {"id": str(uuid.uuid4()), "name": "Resolved", "slug": "resolved", "color": "#22C55E", "order": 8, "is_terminal": True, "is_success": True},
            {"id": str(uuid.uuid4()), "name": "Closed", "slug": "closed", "color": "#10B981", "order": 9, "is_terminal": True}
        ],
        "custom_fields": [
            {"id": str(uuid.uuid4()), "name": "Complaint Category", "slug": "complaint_category", "field_type": "select", "required": True, "order": 1, "show_in_list": True,
             "options": [{"value": "product_quality", "label": "Product Quality"}, {"value": "service_quality", "label": "Service Quality"}, {"value": "delivery", "label": "Delivery Issues"}, {"value": "staff_behavior", "label": "Staff Behavior"}, {"value": "billing", "label": "Billing/Pricing"}, {"value": "communication", "label": "Communication"}, {"value": "other", "label": "Other"}]},
            {"id": str(uuid.uuid4()), "name": "Severity", "slug": "severity", "field_type": "select", "required": True, "order": 2, "show_in_list": True,
             "options": [{"value": "minor", "label": "Minor"}, {"value": "moderate", "label": "Moderate"}, {"value": "major", "label": "Major"}, {"value": "critical", "label": "Critical"}]},
            {"id": str(uuid.uuid4()), "name": "Related Order/Ticket", "slug": "related_reference", "field_type": "text", "required": False, "order": 3},
            {"id": str(uuid.uuid4()), "name": "Complaint Details", "slug": "complaint_details", "field_type": "textarea", "required": True, "order": 4},
            {"id": str(uuid.uuid4()), "name": "Expected Resolution", "slug": "expected_resolution", "field_type": "textarea", "required": False, "order": 5},
            {"id": str(uuid.uuid4()), "name": "Compensation Offered", "slug": "compensation", "field_type": "text", "required": False, "order": 6},
            {"id": str(uuid.uuid4()), "name": "Root Cause", "slug": "root_cause", "field_type": "textarea", "required": False, "order": 7},
            {"id": str(uuid.uuid4()), "name": "Preventive Action", "slug": "preventive_action", "field_type": "textarea", "required": False, "order": 8}
        ],
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # ========== 11. INSTALLATION REQUEST ==========
    ticket_types.append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "Installation Request",
        "slug": "installation-request",
        "description": "Product installation and setup requests",
        "icon": "package-plus",
        "color": "#14B8A6",
        "category": "operations",
        "requires_job_lifecycle": False,
        "requires_device": True,
        "requires_company": True,
        "requires_contact": True,
        "default_priority": "medium",
        "is_system": True,
        "workflow_statuses": [
            {"id": str(uuid.uuid4()), "name": "Request Received", "slug": "new", "color": "#6B7280", "order": 0, "is_initial": True, "can_transition_to": ["scheduled", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Scheduled", "slug": "scheduled", "color": "#3B82F6", "order": 1, "can_transition_to": ["technician_assigned", "rescheduled", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Technician Assigned", "slug": "technician_assigned", "color": "#8B5CF6", "order": 2, "can_transition_to": ["en_route", "rescheduled"]},
            {"id": str(uuid.uuid4()), "name": "Rescheduled", "slug": "rescheduled", "color": "#F59E0B", "order": 3, "can_transition_to": ["scheduled", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "En Route", "slug": "en_route", "color": "#EC4899", "order": 4, "can_transition_to": ["installation_started"]},
            {"id": str(uuid.uuid4()), "name": "Installation Started", "slug": "installation_started", "color": "#F97316", "order": 5, "can_transition_to": ["installation_completed", "issues_found"]},
            {"id": str(uuid.uuid4()), "name": "Issues Found", "slug": "issues_found", "color": "#EF4444", "order": 6, "can_transition_to": ["installation_started", "rescheduled"]},
            {"id": str(uuid.uuid4()), "name": "Installation Completed", "slug": "installation_completed", "color": "#22C55E", "order": 7, "can_transition_to": ["customer_training"]},
            {"id": str(uuid.uuid4()), "name": "Customer Training", "slug": "customer_training", "color": "#06B6D4", "order": 8, "can_transition_to": ["closed"]},
            {"id": str(uuid.uuid4()), "name": "Closed", "slug": "closed", "color": "#10B981", "order": 9, "is_terminal": True, "is_success": True},
            {"id": str(uuid.uuid4()), "name": "Cancelled", "slug": "cancelled", "color": "#EF4444", "order": 10, "is_terminal": True, "is_failure": True}
        ],
        "custom_fields": [
            {"id": str(uuid.uuid4()), "name": "Installation Type", "slug": "installation_type", "field_type": "select", "required": True, "order": 1, "show_in_list": True,
             "options": [{"value": "new", "label": "New Installation"}, {"value": "relocation", "label": "Relocation"}, {"value": "upgrade", "label": "Upgrade"}, {"value": "replacement", "label": "Replacement"}]},
            {"id": str(uuid.uuid4()), "name": "Preferred Date", "slug": "preferred_date", "field_type": "date", "required": True, "order": 2},
            {"id": str(uuid.uuid4()), "name": "Preferred Time Slot", "slug": "preferred_time", "field_type": "select", "required": False, "order": 3,
             "options": [{"value": "morning", "label": "Morning (9 AM - 12 PM)"}, {"value": "afternoon", "label": "Afternoon (12 PM - 4 PM)"}, {"value": "evening", "label": "Evening (4 PM - 7 PM)"}]},
            {"id": str(uuid.uuid4()), "name": "Installation Address", "slug": "installation_address", "field_type": "textarea", "required": True, "order": 4},
            {"id": str(uuid.uuid4()), "name": "Site Readiness", "slug": "site_readiness", "field_type": "checkbox", "required": False, "order": 5, "help_text": "Is the site ready for installation?"},
            {"id": str(uuid.uuid4()), "name": "Special Requirements", "slug": "special_requirements", "field_type": "textarea", "required": False, "order": 6}
        ],
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # ========== 12. TRAINING REQUEST ==========
    ticket_types.append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "Training Request",
        "slug": "training-request",
        "description": "Product training and knowledge transfer requests",
        "icon": "graduation-cap",
        "color": "#F59E0B",
        "category": "operations",
        "requires_job_lifecycle": False,
        "requires_device": False,
        "requires_company": True,
        "requires_contact": True,
        "default_priority": "low",
        "is_system": True,
        "workflow_statuses": [
            {"id": str(uuid.uuid4()), "name": "Request Received", "slug": "new", "color": "#6B7280", "order": 0, "is_initial": True, "can_transition_to": ["scheduled", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Scheduled", "slug": "scheduled", "color": "#3B82F6", "order": 1, "can_transition_to": ["confirmed", "rescheduled", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Confirmed", "slug": "confirmed", "color": "#8B5CF6", "order": 2, "can_transition_to": ["in_progress", "rescheduled"]},
            {"id": str(uuid.uuid4()), "name": "Rescheduled", "slug": "rescheduled", "color": "#F59E0B", "order": 3, "can_transition_to": ["scheduled", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "In Progress", "slug": "in_progress", "color": "#EC4899", "order": 4, "can_transition_to": ["completed"]},
            {"id": str(uuid.uuid4()), "name": "Completed", "slug": "completed", "color": "#22C55E", "order": 5, "can_transition_to": ["feedback_collected"]},
            {"id": str(uuid.uuid4()), "name": "Feedback Collected", "slug": "feedback_collected", "color": "#10B981", "order": 6, "is_terminal": True, "is_success": True},
            {"id": str(uuid.uuid4()), "name": "Cancelled", "slug": "cancelled", "color": "#EF4444", "order": 7, "is_terminal": True, "is_failure": True}
        ],
        "custom_fields": [
            {"id": str(uuid.uuid4()), "name": "Training Type", "slug": "training_type", "field_type": "select", "required": True, "order": 1, "show_in_list": True,
             "options": [{"value": "product", "label": "Product Training"}, {"value": "technical", "label": "Technical Training"}, {"value": "onboarding", "label": "Onboarding"}, {"value": "refresher", "label": "Refresher Course"}, {"value": "advanced", "label": "Advanced Training"}]},
            {"id": str(uuid.uuid4()), "name": "Training Mode", "slug": "training_mode", "field_type": "select", "required": True, "order": 2,
             "options": [{"value": "onsite", "label": "On-site"}, {"value": "online", "label": "Online/Virtual"}, {"value": "classroom", "label": "Classroom"}]},
            {"id": str(uuid.uuid4()), "name": "Number of Participants", "slug": "participants", "field_type": "number", "required": True, "order": 3, "show_in_list": True},
            {"id": str(uuid.uuid4()), "name": "Preferred Date", "slug": "preferred_date", "field_type": "date", "required": True, "order": 4},
            {"id": str(uuid.uuid4()), "name": "Duration (hours)", "slug": "duration", "field_type": "number", "required": False, "order": 5},
            {"id": str(uuid.uuid4()), "name": "Topics to Cover", "slug": "topics", "field_type": "textarea", "required": False, "order": 6},
            {"id": str(uuid.uuid4()), "name": "Training Feedback", "slug": "feedback", "field_type": "textarea", "required": False, "order": 7}
        ],
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # ========== 13. RENEWAL REQUEST ==========
    ticket_types.append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "Renewal Request",
        "slug": "renewal-request",
        "description": "Contract, subscription, and AMC renewal requests",
        "icon": "refresh-cw",
        "color": "#EC4899",
        "category": "sales",
        "requires_job_lifecycle": False,
        "requires_device": False,
        "requires_company": True,
        "requires_contact": True,
        "default_priority": "high",
        "is_system": True,
        "workflow_statuses": [
            {"id": str(uuid.uuid4()), "name": "Renewal Due", "slug": "new", "color": "#F59E0B", "order": 0, "is_initial": True, "can_transition_to": ["contacted", "not_interested"]},
            {"id": str(uuid.uuid4()), "name": "Contacted", "slug": "contacted", "color": "#3B82F6", "order": 1, "can_transition_to": ["quote_sent", "not_interested"]},
            {"id": str(uuid.uuid4()), "name": "Quote Sent", "slug": "quote_sent", "color": "#8B5CF6", "order": 2, "can_transition_to": ["negotiation", "approved", "not_interested"]},
            {"id": str(uuid.uuid4()), "name": "Negotiation", "slug": "negotiation", "color": "#EC4899", "order": 3, "can_transition_to": ["approved", "not_interested"]},
            {"id": str(uuid.uuid4()), "name": "Approved", "slug": "approved", "color": "#14B8A6", "order": 4, "can_transition_to": ["payment_pending", "renewed"]},
            {"id": str(uuid.uuid4()), "name": "Payment Pending", "slug": "payment_pending", "color": "#F97316", "order": 5, "can_transition_to": ["renewed", "not_interested"]},
            {"id": str(uuid.uuid4()), "name": "Renewed", "slug": "renewed", "color": "#22C55E", "order": 6, "is_terminal": True, "is_success": True},
            {"id": str(uuid.uuid4()), "name": "Not Interested", "slug": "not_interested", "color": "#EF4444", "order": 7, "is_terminal": True, "is_failure": True}
        ],
        "custom_fields": [
            {"id": str(uuid.uuid4()), "name": "Renewal Type", "slug": "renewal_type", "field_type": "select", "required": True, "order": 1, "show_in_list": True,
             "options": [{"value": "amc", "label": "AMC Contract"}, {"value": "warranty", "label": "Extended Warranty"}, {"value": "subscription", "label": "Subscription"}, {"value": "license", "label": "License"}, {"value": "support", "label": "Support Contract"}]},
            {"id": str(uuid.uuid4()), "name": "Current Contract End Date", "slug": "contract_end_date", "field_type": "date", "required": True, "order": 2, "show_in_list": True},
            {"id": str(uuid.uuid4()), "name": "Current Contract Value", "slug": "current_value", "field_type": "currency", "required": False, "order": 3},
            {"id": str(uuid.uuid4()), "name": "Proposed Renewal Value", "slug": "renewal_value", "field_type": "currency", "required": False, "order": 4, "show_in_list": True},
            {"id": str(uuid.uuid4()), "name": "Renewal Period", "slug": "renewal_period", "field_type": "select", "required": False, "order": 5,
             "options": [{"value": "1_year", "label": "1 Year"}, {"value": "2_years", "label": "2 Years"}, {"value": "3_years", "label": "3 Years"}, {"value": "monthly", "label": "Monthly"}, {"value": "quarterly", "label": "Quarterly"}]},
            {"id": str(uuid.uuid4()), "name": "Reason for Non-Renewal", "slug": "non_renewal_reason", "field_type": "textarea", "required": False, "order": 6}
        ],
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # ========== 14. BILLING INQUIRY ==========
    ticket_types.append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "Billing Inquiry",
        "slug": "billing-inquiry",
        "description": "Invoice queries, payment issues, and billing disputes",
        "icon": "receipt",
        "color": "#F97316",
        "category": "finance",
        "requires_job_lifecycle": False,
        "requires_device": False,
        "requires_company": True,
        "requires_contact": True,
        "default_priority": "medium",
        "is_system": True,
        "workflow_statuses": [
            {"id": str(uuid.uuid4()), "name": "Inquiry Received", "slug": "new", "color": "#6B7280", "order": 0, "is_initial": True, "can_transition_to": ["under_review", "resolved"]},
            {"id": str(uuid.uuid4()), "name": "Under Review", "slug": "under_review", "color": "#3B82F6", "order": 1, "can_transition_to": ["info_needed", "adjustment_required", "resolved"]},
            {"id": str(uuid.uuid4()), "name": "Info Needed", "slug": "info_needed", "color": "#F59E0B", "order": 2, "can_transition_to": ["under_review", "resolved"]},
            {"id": str(uuid.uuid4()), "name": "Adjustment Required", "slug": "adjustment_required", "color": "#8B5CF6", "order": 3, "can_transition_to": ["adjustment_processed", "resolved"]},
            {"id": str(uuid.uuid4()), "name": "Adjustment Processed", "slug": "adjustment_processed", "color": "#14B8A6", "order": 4, "can_transition_to": ["resolved"]},
            {"id": str(uuid.uuid4()), "name": "Resolved", "slug": "resolved", "color": "#22C55E", "order": 5, "is_terminal": True, "is_success": True}
        ],
        "custom_fields": [
            {"id": str(uuid.uuid4()), "name": "Inquiry Type", "slug": "inquiry_type", "field_type": "select", "required": True, "order": 1, "show_in_list": True,
             "options": [{"value": "invoice_copy", "label": "Invoice Copy Request"}, {"value": "payment_status", "label": "Payment Status"}, {"value": "dispute", "label": "Billing Dispute"}, {"value": "adjustment", "label": "Credit/Adjustment Request"}, {"value": "payment_terms", "label": "Payment Terms"}, {"value": "other", "label": "Other"}]},
            {"id": str(uuid.uuid4()), "name": "Invoice Number", "slug": "invoice_number", "field_type": "text", "required": False, "order": 2, "show_in_list": True},
            {"id": str(uuid.uuid4()), "name": "Invoice Amount", "slug": "invoice_amount", "field_type": "currency", "required": False, "order": 3},
            {"id": str(uuid.uuid4()), "name": "Disputed Amount", "slug": "disputed_amount", "field_type": "currency", "required": False, "order": 4},
            {"id": str(uuid.uuid4()), "name": "Query Details", "slug": "query_details", "field_type": "textarea", "required": True, "order": 5},
            {"id": str(uuid.uuid4()), "name": "Resolution Notes", "slug": "resolution_notes", "field_type": "textarea", "required": False, "order": 6}
        ],
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # ========== 15. MAINTENANCE REQUEST ==========
    ticket_types.append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "Maintenance Request",
        "slug": "maintenance-request",
        "description": "Scheduled maintenance and preventive service requests",
        "icon": "settings",
        "color": "#06B6D4",
        "category": "operations",
        "requires_job_lifecycle": False,
        "requires_device": True,
        "requires_company": True,
        "requires_contact": True,
        "default_priority": "medium",
        "is_system": True,
        "workflow_statuses": [
            {"id": str(uuid.uuid4()), "name": "Request Received", "slug": "new", "color": "#6B7280", "order": 0, "is_initial": True, "can_transition_to": ["scheduled", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Scheduled", "slug": "scheduled", "color": "#3B82F6", "order": 1, "can_transition_to": ["technician_assigned", "rescheduled"]},
            {"id": str(uuid.uuid4()), "name": "Technician Assigned", "slug": "technician_assigned", "color": "#8B5CF6", "order": 2, "can_transition_to": ["in_progress", "rescheduled"]},
            {"id": str(uuid.uuid4()), "name": "Rescheduled", "slug": "rescheduled", "color": "#F59E0B", "order": 3, "can_transition_to": ["scheduled", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "In Progress", "slug": "in_progress", "color": "#EC4899", "order": 4, "can_transition_to": ["completed", "parts_needed"]},
            {"id": str(uuid.uuid4()), "name": "Parts Needed", "slug": "parts_needed", "color": "#F97316", "order": 5, "can_transition_to": ["in_progress"]},
            {"id": str(uuid.uuid4()), "name": "Completed", "slug": "completed", "color": "#22C55E", "order": 6, "is_terminal": True, "is_success": True},
            {"id": str(uuid.uuid4()), "name": "Cancelled", "slug": "cancelled", "color": "#EF4444", "order": 7, "is_terminal": True, "is_failure": True}
        ],
        "custom_fields": [
            {"id": str(uuid.uuid4()), "name": "Maintenance Type", "slug": "maintenance_type", "field_type": "select", "required": True, "order": 1, "show_in_list": True,
             "options": [{"value": "preventive", "label": "Preventive Maintenance"}, {"value": "scheduled", "label": "Scheduled Service"}, {"value": "inspection", "label": "Inspection"}, {"value": "cleaning", "label": "Cleaning"}, {"value": "calibration", "label": "Calibration"}]},
            {"id": str(uuid.uuid4()), "name": "Preferred Date", "slug": "preferred_date", "field_type": "date", "required": True, "order": 2},
            {"id": str(uuid.uuid4()), "name": "Last Maintenance Date", "slug": "last_maintenance_date", "field_type": "date", "required": False, "order": 3},
            {"id": str(uuid.uuid4()), "name": "Checklist Completed", "slug": "checklist_completed", "field_type": "checkbox", "required": False, "order": 4},
            {"id": str(uuid.uuid4()), "name": "Work Performed", "slug": "work_performed", "field_type": "textarea", "required": False, "order": 5},
            {"id": str(uuid.uuid4()), "name": "Next Maintenance Due", "slug": "next_maintenance", "field_type": "date", "required": False, "order": 6}
        ],
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # ========== 16. SITE VISIT REQUEST ==========
    ticket_types.append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "Site Visit Request",
        "slug": "site-visit-request",
        "description": "On-site visit requests for assessment, survey, or consultation",
        "icon": "map-pin",
        "color": "#84CC16",
        "category": "operations",
        "requires_job_lifecycle": False,
        "requires_device": False,
        "requires_company": True,
        "requires_contact": True,
        "default_priority": "medium",
        "is_system": True,
        "workflow_statuses": [
            {"id": str(uuid.uuid4()), "name": "Request Received", "slug": "new", "color": "#6B7280", "order": 0, "is_initial": True, "can_transition_to": ["scheduled", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Scheduled", "slug": "scheduled", "color": "#3B82F6", "order": 1, "can_transition_to": ["confirmed", "rescheduled"]},
            {"id": str(uuid.uuid4()), "name": "Confirmed", "slug": "confirmed", "color": "#8B5CF6", "order": 2, "can_transition_to": ["en_route", "rescheduled"]},
            {"id": str(uuid.uuid4()), "name": "Rescheduled", "slug": "rescheduled", "color": "#F59E0B", "order": 3, "can_transition_to": ["scheduled", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "En Route", "slug": "en_route", "color": "#EC4899", "order": 4, "can_transition_to": ["on_site"]},
            {"id": str(uuid.uuid4()), "name": "On Site", "slug": "on_site", "color": "#14B8A6", "order": 5, "can_transition_to": ["visit_completed"]},
            {"id": str(uuid.uuid4()), "name": "Visit Completed", "slug": "visit_completed", "color": "#06B6D4", "order": 6, "can_transition_to": ["report_submitted"]},
            {"id": str(uuid.uuid4()), "name": "Report Submitted", "slug": "report_submitted", "color": "#22C55E", "order": 7, "is_terminal": True, "is_success": True},
            {"id": str(uuid.uuid4()), "name": "Cancelled", "slug": "cancelled", "color": "#EF4444", "order": 8, "is_terminal": True, "is_failure": True}
        ],
        "custom_fields": [
            {"id": str(uuid.uuid4()), "name": "Visit Purpose", "slug": "visit_purpose", "field_type": "select", "required": True, "order": 1, "show_in_list": True,
             "options": [{"value": "assessment", "label": "Site Assessment"}, {"value": "survey", "label": "Survey"}, {"value": "consultation", "label": "Consultation"}, {"value": "audit", "label": "Audit"}, {"value": "inspection", "label": "Inspection"}, {"value": "other", "label": "Other"}]},
            {"id": str(uuid.uuid4()), "name": "Preferred Date", "slug": "preferred_date", "field_type": "date", "required": True, "order": 2},
            {"id": str(uuid.uuid4()), "name": "Site Address", "slug": "site_address", "field_type": "textarea", "required": True, "order": 3},
            {"id": str(uuid.uuid4()), "name": "Site Contact Person", "slug": "site_contact", "field_type": "text", "required": False, "order": 4},
            {"id": str(uuid.uuid4()), "name": "Site Contact Phone", "slug": "site_phone", "field_type": "phone", "required": False, "order": 5},
            {"id": str(uuid.uuid4()), "name": "Visit Report", "slug": "visit_report", "field_type": "textarea", "required": False, "order": 6},
            {"id": str(uuid.uuid4()), "name": "Recommendations", "slug": "recommendations", "field_type": "textarea", "required": False, "order": 7}
        ],
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # ========== 17. DEMO REQUEST ==========
    ticket_types.append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "Demo Request",
        "slug": "demo-request",
        "description": "Product demonstration requests",
        "icon": "play-circle",
        "color": "#A855F7",
        "category": "sales",
        "requires_job_lifecycle": False,
        "requires_device": False,
        "requires_company": True,
        "requires_contact": True,
        "default_priority": "medium",
        "is_system": True,
        "workflow_statuses": [
            {"id": str(uuid.uuid4()), "name": "Request Received", "slug": "new", "color": "#6B7280", "order": 0, "is_initial": True, "can_transition_to": ["contacted", "not_interested"]},
            {"id": str(uuid.uuid4()), "name": "Contacted", "slug": "contacted", "color": "#3B82F6", "order": 1, "can_transition_to": ["demo_scheduled", "not_interested"]},
            {"id": str(uuid.uuid4()), "name": "Demo Scheduled", "slug": "demo_scheduled", "color": "#8B5CF6", "order": 2, "can_transition_to": ["demo_completed", "rescheduled", "no_show"]},
            {"id": str(uuid.uuid4()), "name": "Rescheduled", "slug": "rescheduled", "color": "#F59E0B", "order": 3, "can_transition_to": ["demo_scheduled", "not_interested"]},
            {"id": str(uuid.uuid4()), "name": "No Show", "slug": "no_show", "color": "#EF4444", "order": 4, "can_transition_to": ["rescheduled", "not_interested"]},
            {"id": str(uuid.uuid4()), "name": "Demo Completed", "slug": "demo_completed", "color": "#14B8A6", "order": 5, "can_transition_to": ["interested", "not_interested"]},
            {"id": str(uuid.uuid4()), "name": "Interested", "slug": "interested", "color": "#22C55E", "order": 6, "is_terminal": True, "is_success": True},
            {"id": str(uuid.uuid4()), "name": "Not Interested", "slug": "not_interested", "color": "#EF4444", "order": 7, "is_terminal": True, "is_failure": True}
        ],
        "custom_fields": [
            {"id": str(uuid.uuid4()), "name": "Products for Demo", "slug": "demo_products", "field_type": "textarea", "required": True, "order": 1, "placeholder": "Which products/features would you like to see?"},
            {"id": str(uuid.uuid4()), "name": "Demo Type", "slug": "demo_type", "field_type": "select", "required": True, "order": 2, "show_in_list": True,
             "options": [{"value": "online", "label": "Online/Virtual"}, {"value": "onsite", "label": "On-site"}, {"value": "showroom", "label": "At Showroom"}]},
            {"id": str(uuid.uuid4()), "name": "Preferred Date", "slug": "preferred_date", "field_type": "date", "required": False, "order": 3},
            {"id": str(uuid.uuid4()), "name": "Number of Attendees", "slug": "attendees", "field_type": "number", "required": False, "order": 4},
            {"id": str(uuid.uuid4()), "name": "Demo Outcome", "slug": "demo_outcome", "field_type": "textarea", "required": False, "order": 5},
            {"id": str(uuid.uuid4()), "name": "Follow-up Actions", "slug": "followup_actions", "field_type": "textarea", "required": False, "order": 6}
        ],
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # ========== 18. ONBOARDING REQUEST ==========
    ticket_types.append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "Onboarding Request",
        "slug": "onboarding-request",
        "description": "New customer/employee onboarding process",
        "icon": "user-plus",
        "color": "#0EA5E9",
        "category": "operations",
        "requires_job_lifecycle": False,
        "requires_device": False,
        "requires_company": True,
        "requires_contact": True,
        "default_priority": "high",
        "is_system": True,
        "workflow_statuses": [
            {"id": str(uuid.uuid4()), "name": "Request Received", "slug": "new", "color": "#6B7280", "order": 0, "is_initial": True, "can_transition_to": ["documentation", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Documentation", "slug": "documentation", "color": "#3B82F6", "order": 1, "can_transition_to": ["verification", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Verification", "slug": "verification", "color": "#8B5CF6", "order": 2, "can_transition_to": ["account_setup", "documentation", "cancelled"]},
            {"id": str(uuid.uuid4()), "name": "Account Setup", "slug": "account_setup", "color": "#F59E0B", "order": 3, "can_transition_to": ["training_scheduled"]},
            {"id": str(uuid.uuid4()), "name": "Training Scheduled", "slug": "training_scheduled", "color": "#EC4899", "order": 4, "can_transition_to": ["training_completed"]},
            {"id": str(uuid.uuid4()), "name": "Training Completed", "slug": "training_completed", "color": "#14B8A6", "order": 5, "can_transition_to": ["go_live"]},
            {"id": str(uuid.uuid4()), "name": "Go Live", "slug": "go_live", "color": "#22C55E", "order": 6, "is_terminal": True, "is_success": True},
            {"id": str(uuid.uuid4()), "name": "Cancelled", "slug": "cancelled", "color": "#EF4444", "order": 7, "is_terminal": True, "is_failure": True}
        ],
        "custom_fields": [
            {"id": str(uuid.uuid4()), "name": "Onboarding Type", "slug": "onboarding_type", "field_type": "select", "required": True, "order": 1, "show_in_list": True,
             "options": [{"value": "new_customer", "label": "New Customer"}, {"value": "new_product", "label": "New Product/Service"}, {"value": "migration", "label": "Migration"}]},
            {"id": str(uuid.uuid4()), "name": "Target Go-Live Date", "slug": "golive_date", "field_type": "date", "required": False, "order": 2, "show_in_list": True},
            {"id": str(uuid.uuid4()), "name": "Products/Services", "slug": "products_services", "field_type": "textarea", "required": True, "order": 3},
            {"id": str(uuid.uuid4()), "name": "Key Stakeholders", "slug": "stakeholders", "field_type": "textarea", "required": False, "order": 4},
            {"id": str(uuid.uuid4()), "name": "Special Requirements", "slug": "special_requirements", "field_type": "textarea", "required": False, "order": 5},
            {"id": str(uuid.uuid4()), "name": "Onboarding Checklist", "slug": "checklist", "field_type": "textarea", "required": False, "order": 6}
        ],
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    return ticket_types
