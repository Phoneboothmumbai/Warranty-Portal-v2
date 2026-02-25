"""
Ticketing System v2 - Seed Data
================================
Pre-built help topics, forms, workflows, roles, teams, etc.
"""

import uuid
from datetime import datetime, timezone, timedelta


def get_ist_isoformat():
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).isoformat()


def generate_seed_data(organization_id: str):
    """Generate all seed data for a new organization"""
    
    data = {
        "priorities": [],
        "business_hours": [],
        "sla_policies": [],
        "roles": [],
        "teams": [],
        "task_types": [],
        "forms": [],
        "workflows": [],
        "help_topics": [],
        "canned_responses": [],
        "notification_templates": []
    }
    
    # ============================================================
    # PRIORITIES
    # ============================================================
    priorities = [
        {"name": "Low", "slug": "low", "color": "#6B7280", "order": 0, "sla_multiplier": 2.0, "is_default": False},
        {"name": "Medium", "slug": "medium", "color": "#3B82F6", "order": 1, "sla_multiplier": 1.0, "is_default": True},
        {"name": "High", "slug": "high", "color": "#F59E0B", "order": 2, "sla_multiplier": 0.5, "is_default": False},
        {"name": "Critical", "slug": "critical", "color": "#EF4444", "order": 3, "sla_multiplier": 0.25, "auto_escalate": True, "is_default": False}
    ]
    for p in priorities:
        data["priorities"].append({
            "id": str(uuid.uuid4()),
            "organization_id": organization_id,
            "is_active": True,
            "created_at": get_ist_isoformat(),
            **p
        })
    
    # ============================================================
    # BUSINESS HOURS
    # ============================================================
    data["business_hours"].append({
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "name": "Standard Business Hours",
        "schedule": {
            "monday": {"start": "09:00", "end": "18:00"},
            "tuesday": {"start": "09:00", "end": "18:00"},
            "wednesday": {"start": "09:00", "end": "18:00"},
            "thursday": {"start": "09:00", "end": "18:00"},
            "friday": {"start": "09:00", "end": "18:00"},
            "saturday": {"start": "09:00", "end": "14:00"},
            "sunday": None
        },
        "holidays": [],
        "timezone": "Asia/Kolkata",
        "is_default": True,
        "is_active": True,
        "created_at": get_ist_isoformat()
    })
    
    # ============================================================
    # SLA POLICIES
    # ============================================================
    sla_policies = [
        {"name": "Standard SLA", "response_time_hours": 4, "resolution_time_hours": 24, "is_default": True},
        {"name": "Premium SLA", "response_time_hours": 1, "resolution_time_hours": 8, "is_default": False},
        {"name": "Critical SLA", "response_time_hours": 0.5, "resolution_time_hours": 4, "is_default": False}
    ]
    for sla in sla_policies:
        data["sla_policies"].append({
            "id": str(uuid.uuid4()),
            "organization_id": organization_id,
            "description": None,
            "business_hours_only": True,
            "escalation_enabled": True,
            "escalation_after_hours": 8,
            "priority_multipliers": {"low": 2.0, "medium": 1.0, "high": 0.5, "critical": 0.25},
            "is_active": True,
            "created_at": get_ist_isoformat(),
            **sla
        })
    
    # ============================================================
    # ROLES
    # ============================================================
    roles_data = [
        {
            "name": "Administrator",
            "slug": "admin",
            "description": "Full access to all features",
            "permissions": [
                "tickets.view_all", "tickets.create", "tickets.edit", "tickets.assign",
                "tickets.close", "tickets.delete", "tasks.view_all", "tasks.assign",
                "tasks.complete", "quotes.create", "quotes.send", "quotes.approve",
                "parts.request", "parts.order", "parts.receive",
                "admin.settings", "admin.users", "admin.reports", "admin.masters"
            ],
            "is_system": True
        },
        {
            "name": "Support Manager",
            "slug": "support_manager",
            "description": "Manages support team and tickets",
            "permissions": [
                "tickets.view_all", "tickets.create", "tickets.edit", "tickets.assign",
                "tickets.close", "tasks.view_all", "tasks.assign", "tasks.complete",
                "quotes.create", "quotes.send", "admin.reports"
            ],
            "is_system": True
        },
        {
            "name": "Field Technician",
            "slug": "field_technician",
            "description": "Handles on-site visits and repairs",
            "permissions": [
                "tickets.view_assigned", "tickets.edit", "tasks.view_assigned",
                "tasks.complete", "parts.request"
            ],
            "is_system": True
        },
        {
            "name": "Remote Support",
            "slug": "remote_support",
            "description": "Handles remote support tickets",
            "permissions": [
                "tickets.view_assigned", "tickets.create", "tickets.edit",
                "tickets.close", "tasks.view_assigned", "tasks.complete"
            ],
            "is_system": True
        },
        {
            "name": "Back Office",
            "slug": "back_office",
            "description": "Handles quotations and documentation",
            "permissions": [
                "tickets.view_all", "tickets.edit", "quotes.create", "quotes.send",
                "tasks.view_assigned", "tasks.complete"
            ],
            "is_system": True
        },
        {
            "name": "Procurement",
            "slug": "procurement",
            "description": "Handles parts ordering",
            "permissions": [
                "tickets.view_all", "parts.order", "parts.receive",
                "tasks.view_assigned", "tasks.complete"
            ],
            "is_system": True
        },
        {
            "name": "Sales",
            "slug": "sales",
            "description": "Handles sales inquiries and leads",
            "permissions": [
                "tickets.view_assigned", "tickets.create", "tickets.edit",
                "tickets.close", "quotes.create", "quotes.send"
            ],
            "is_system": True
        },
        {
            "name": "Accounts",
            "slug": "accounts",
            "description": "Handles billing and payments",
            "permissions": [
                "tickets.view_all", "quotes.approve", "tasks.view_assigned", "tasks.complete"
            ],
            "is_system": True
        }
    ]
    for role in roles_data:
        data["roles"].append({
            "id": str(uuid.uuid4()),
            "organization_id": organization_id,
            "dashboard_widgets": [],
            "is_active": True,
            "created_at": get_ist_isoformat(),
            **role
        })
    
    # Store role IDs for reference
    role_ids = {r["slug"]: data["roles"][i]["id"] for i, r in enumerate(roles_data)}
    
    # ============================================================
    # TEAMS
    # ============================================================
    teams_data = [
        {"name": "Support Desk", "slug": "support_desk", "description": "First line of support", "color": "#3B82F6", "icon": "headphones"},
        {"name": "Field Technicians", "slug": "field_technicians", "description": "On-site support team", "color": "#10B981", "icon": "wrench"},
        {"name": "Remote Support", "slug": "remote_support", "description": "Remote assistance team", "color": "#8B5CF6", "icon": "monitor"},
        {"name": "Back Office", "slug": "back_office", "description": "Quotations and documentation", "color": "#F59E0B", "icon": "file-text"},
        {"name": "Procurement", "slug": "procurement", "description": "Parts ordering and inventory", "color": "#EC4899", "icon": "shopping-cart"},
        {"name": "Sales Team", "slug": "sales_team", "description": "Sales and business development", "color": "#06B6D4", "icon": "trending-up"},
        {"name": "Accounts", "slug": "accounts", "description": "Billing and payments", "color": "#84CC16", "icon": "dollar-sign"}
    ]
    for team in teams_data:
        data["teams"].append({
            "id": str(uuid.uuid4()),
            "organization_id": organization_id,
            "members": [],
            "manager_id": None,
            "assignment_method": "round_robin",
            "business_hours_id": None,
            "team_email": None,
            "is_active": True,
            "created_at": get_ist_isoformat(),
            **team
        })
    
    # Store team IDs
    team_ids = {t["slug"]: data["teams"][i]["id"] for i, t in enumerate(teams_data)}
    
    # ============================================================
    # TASK TYPES
    # ============================================================
    task_types_data = [
        {
            "name": "Schedule Site Visit",
            "slug": "schedule_visit",
            "description": "Schedule and confirm customer visit",
            "icon": "calendar",
            "color": "#3B82F6",
            "default_team_id": team_ids["field_technicians"],
            "default_due_hours": 4,
            "checklist": [
                {"text": "Confirm appointment with customer", "required": True},
                {"text": "Check technician availability", "required": True},
                {"text": "Send confirmation to customer", "required": False}
            ]
        },
        {
            "name": "Perform Site Visit",
            "slug": "site_visit",
            "description": "Visit customer site and diagnose issue",
            "icon": "map-pin",
            "color": "#10B981",
            "default_team_id": team_ids["field_technicians"],
            "default_due_hours": 24,
            "checklist": [
                {"text": "Reach customer location", "required": True},
                {"text": "Diagnose the issue", "required": True},
                {"text": "Document findings", "required": True},
                {"text": "Get customer signature", "required": False}
            ]
        },
        {
            "name": "Prepare Quotation",
            "slug": "prepare_quote",
            "description": "Create and send quotation to customer",
            "icon": "file-text",
            "color": "#F59E0B",
            "default_team_id": team_ids["back_office"],
            "default_due_hours": 8,
            "checklist": [
                {"text": "Review parts requirement", "required": True},
                {"text": "Calculate pricing", "required": True},
                {"text": "Create quotation document", "required": True},
                {"text": "Get approval if required", "required": False},
                {"text": "Send to customer", "required": True}
            ]
        },
        {
            "name": "Order Parts",
            "slug": "order_parts",
            "description": "Order required parts from vendor",
            "icon": "shopping-cart",
            "color": "#EC4899",
            "default_team_id": team_ids["procurement"],
            "default_due_hours": 24,
            "checklist": [
                {"text": "Check inventory", "required": True},
                {"text": "Create purchase order", "required": True},
                {"text": "Send PO to vendor", "required": True},
                {"text": "Track delivery", "required": False}
            ]
        },
        {
            "name": "Receive Parts",
            "slug": "receive_parts",
            "description": "Receive and verify parts delivery",
            "icon": "package",
            "color": "#8B5CF6",
            "default_team_id": team_ids["procurement"],
            "default_due_hours": 48,
            "checklist": [
                {"text": "Verify parts received", "required": True},
                {"text": "Check for damage", "required": True},
                {"text": "Update inventory", "required": True},
                {"text": "Notify technician", "required": True}
            ]
        },
        {
            "name": "Perform Installation",
            "slug": "installation",
            "description": "Install parts at customer site",
            "icon": "settings",
            "color": "#06B6D4",
            "default_team_id": team_ids["field_technicians"],
            "default_due_hours": 24,
            "checklist": [
                {"text": "Confirm parts available", "required": True},
                {"text": "Schedule with customer", "required": True},
                {"text": "Install parts", "required": True},
                {"text": "Test functionality", "required": True},
                {"text": "Get customer sign-off", "required": True}
            ]
        },
        {
            "name": "Remote Session",
            "slug": "remote_session",
            "description": "Conduct remote support session",
            "icon": "monitor",
            "color": "#8B5CF6",
            "default_team_id": team_ids["remote_support"],
            "default_due_hours": 4,
            "checklist": [
                {"text": "Connect to customer system", "required": True},
                {"text": "Diagnose issue", "required": True},
                {"text": "Apply fix", "required": False},
                {"text": "Document resolution", "required": True}
            ]
        },
        {
            "name": "Follow Up Call",
            "slug": "follow_up",
            "description": "Follow up with customer",
            "icon": "phone",
            "color": "#84CC16",
            "default_team_id": team_ids["support_desk"],
            "default_due_hours": 24,
            "checklist": [
                {"text": "Call customer", "required": True},
                {"text": "Verify issue resolved", "required": True},
                {"text": "Document feedback", "required": False}
            ]
        },
        {
            "name": "Log with Manufacturer",
            "slug": "log_manufacturer",
            "description": "Log warranty claim with manufacturer",
            "icon": "external-link",
            "color": "#EF4444",
            "default_team_id": team_ids["back_office"],
            "default_due_hours": 24,
            "checklist": [
                {"text": "Gather device details", "required": True},
                {"text": "Contact manufacturer support", "required": True},
                {"text": "Log case/RMA number", "required": True},
                {"text": "Document expected timeline", "required": True}
            ]
        },
        {
            "name": "Contact Customer",
            "slug": "contact_customer",
            "description": "Reach out to customer",
            "icon": "phone-call",
            "color": "#3B82F6",
            "default_team_id": team_ids["sales_team"],
            "default_due_hours": 4,
            "checklist": [
                {"text": "Call/Email customer", "required": True},
                {"text": "Document conversation", "required": True},
                {"text": "Schedule follow-up if needed", "required": False}
            ]
        },
        {
            "name": "Schedule Demo",
            "slug": "schedule_demo",
            "description": "Schedule product demonstration",
            "icon": "play",
            "color": "#8B5CF6",
            "default_team_id": team_ids["sales_team"],
            "default_due_hours": 48,
            "checklist": [
                {"text": "Confirm demo requirements", "required": True},
                {"text": "Schedule time with customer", "required": True},
                {"text": "Prepare demo environment", "required": True},
                {"text": "Send calendar invite", "required": True}
            ]
        }
    ]
    
    for task_type in task_types_data:
        checklist_items = []
        for i, item in enumerate(task_type.pop("checklist", [])):
            checklist_items.append({
                "id": str(uuid.uuid4()),
                "text": item["text"],
                "required": item.get("required", False),
                "order": i
            })
        
        data["task_types"].append({
            "id": str(uuid.uuid4()),
            "organization_id": organization_id,
            "checklist": checklist_items,
            "completion_fields": [],
            "is_active": True,
            "created_at": get_ist_isoformat(),
            **task_type
        })
    
    # Store task type IDs
    task_type_ids = {t["slug"]: data["task_types"][i]["id"] for i, t in enumerate(task_types_data)}
    
    # ============================================================
    # FORMS
    # ============================================================
    
    # 1. On-Site Support Form
    onsite_form_id = str(uuid.uuid4())
    data["forms"].append({
        "id": onsite_form_id,
        "organization_id": organization_id,
        "name": "On-Site Technical Support Form",
        "slug": "onsite_support_form",
        "description": "Form for on-site technical support requests",
        "is_active": True,
        "is_system": True,
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat(),
        "fields": [
            {"id": str(uuid.uuid4()), "name": "issue_type", "slug": "issue_type", "field_type": "select", "label": "Issue Type", "required": True, "order": 0, "width": "half",
             "options": [{"value": "hardware", "label": "Hardware Issue"}, {"value": "software", "label": "Software Issue"}, {"value": "network", "label": "Network Issue"}, {"value": "peripheral", "label": "Peripheral Device"}, {"value": "other", "label": "Other"}]},
            {"id": str(uuid.uuid4()), "name": "device_serial", "slug": "device_serial", "field_type": "text", "label": "Device Serial Number", "required": False, "order": 1, "width": "half"},
            {"id": str(uuid.uuid4()), "name": "problem_description", "slug": "problem_description", "field_type": "textarea", "label": "Problem Description", "required": True, "order": 2, "placeholder": "Describe the issue in detail...", "width": "full"},
            {"id": str(uuid.uuid4()), "name": "error_message", "slug": "error_message", "field_type": "textarea", "label": "Error Messages (if any)", "required": False, "order": 3, "width": "full"},
            {"id": str(uuid.uuid4()), "name": "preferred_date", "slug": "preferred_date", "field_type": "date", "label": "Preferred Visit Date", "required": False, "order": 4, "width": "half"},
            {"id": str(uuid.uuid4()), "name": "preferred_time", "slug": "preferred_time", "field_type": "select", "label": "Preferred Time Slot", "required": False, "order": 5, "width": "half",
             "options": [{"value": "morning", "label": "Morning (9 AM - 12 PM)"}, {"value": "afternoon", "label": "Afternoon (12 PM - 4 PM)"}, {"value": "evening", "label": "Evening (4 PM - 7 PM)"}]},
            {"id": str(uuid.uuid4()), "name": "site_address", "slug": "site_address", "field_type": "textarea", "label": "Site Address", "required": False, "order": 6, "width": "full"}
        ]
    })
    
    # 2. Remote Support Form
    remote_form_id = str(uuid.uuid4())
    data["forms"].append({
        "id": remote_form_id,
        "organization_id": organization_id,
        "name": "Remote Support Form",
        "slug": "remote_support_form",
        "description": "Form for remote support requests",
        "is_active": True,
        "is_system": True,
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat(),
        "fields": [
            {"id": str(uuid.uuid4()), "name": "issue_category", "slug": "issue_category", "field_type": "select", "label": "Issue Category", "required": True, "order": 0, "width": "half",
             "options": [{"value": "software", "label": "Software Issue"}, {"value": "configuration", "label": "Configuration"}, {"value": "connectivity", "label": "Connectivity"}, {"value": "performance", "label": "Performance"}, {"value": "training", "label": "Training/How-to"}]},
            {"id": str(uuid.uuid4()), "name": "remote_access", "slug": "remote_access", "field_type": "select", "label": "Remote Access Available", "required": True, "order": 1, "width": "half",
             "options": [{"value": "yes", "label": "Yes - TeamViewer/AnyDesk"}, {"value": "need_setup", "label": "Need to Setup"}, {"value": "vpn", "label": "VPN Access Required"}]},
            {"id": str(uuid.uuid4()), "name": "problem_description", "slug": "problem_description", "field_type": "textarea", "label": "Problem Description", "required": True, "order": 2, "width": "full"},
            {"id": str(uuid.uuid4()), "name": "availability", "slug": "availability", "field_type": "text", "label": "Your Availability for Remote Session", "required": False, "order": 3, "width": "full"}
        ]
    })
    
    # 3. Warranty Claim Form
    warranty_form_id = str(uuid.uuid4())
    data["forms"].append({
        "id": warranty_form_id,
        "organization_id": organization_id,
        "name": "Warranty / AMC Claim Form",
        "slug": "warranty_claim_form",
        "description": "Form for warranty and AMC claims",
        "is_active": True,
        "is_system": True,
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat(),
        "fields": [
            {"id": str(uuid.uuid4()), "name": "warranty_type", "slug": "warranty_type", "field_type": "select", "label": "Warranty Type", "required": True, "order": 0, "width": "half",
             "options": [{"value": "amc", "label": "AMC (Our Contract)"}, {"value": "oem", "label": "Brand/OEM Warranty"}, {"value": "extended", "label": "Extended Warranty"}, {"value": "none", "label": "No Warranty"}]},
            {"id": str(uuid.uuid4()), "name": "device_serial", "slug": "device_serial", "field_type": "text", "label": "Device Serial Number", "required": True, "order": 1, "width": "half"},
            {"id": str(uuid.uuid4()), "name": "purchase_date", "slug": "purchase_date", "field_type": "date", "label": "Purchase Date", "required": False, "order": 2, "width": "half"},
            {"id": str(uuid.uuid4()), "name": "warranty_end_date", "slug": "warranty_end_date", "field_type": "date", "label": "Warranty End Date", "required": False, "order": 3, "width": "half"},
            {"id": str(uuid.uuid4()), "name": "issue_description", "slug": "issue_description", "field_type": "textarea", "label": "Issue Description", "required": True, "order": 4, "width": "full"},
            {"id": str(uuid.uuid4()), "name": "manufacturer", "slug": "manufacturer", "field_type": "text", "label": "Manufacturer/Brand", "required": False, "order": 5, "width": "half"},
            {"id": str(uuid.uuid4()), "name": "model_number", "slug": "model_number", "field_type": "text", "label": "Model Number", "required": False, "order": 6, "width": "half"}
        ]
    })
    
    # 4. Sales Inquiry Form
    sales_form_id = str(uuid.uuid4())
    data["forms"].append({
        "id": sales_form_id,
        "organization_id": organization_id,
        "name": "Sales Inquiry Form",
        "slug": "sales_inquiry_form",
        "description": "Form for sales inquiries and leads",
        "is_active": True,
        "is_system": True,
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat(),
        "fields": [
            {"id": str(uuid.uuid4()), "name": "inquiry_type", "slug": "inquiry_type", "field_type": "select", "label": "Inquiry Type", "required": True, "order": 0, "width": "half",
             "options": [{"value": "new_purchase", "label": "New Purchase"}, {"value": "upgrade", "label": "Upgrade/Replacement"}, {"value": "bulk_order", "label": "Bulk Order"}, {"value": "pricing", "label": "Pricing Inquiry"}, {"value": "other", "label": "Other"}]},
            {"id": str(uuid.uuid4()), "name": "products_interested", "slug": "products_interested", "field_type": "multiselect", "label": "Products Interested In", "required": True, "order": 1, "width": "half",
             "options": [{"value": "hardware", "label": "Hardware"}, {"value": "software", "label": "Software"}, {"value": "services", "label": "Services"}, {"value": "amc", "label": "AMC/Support"}]},
            {"id": str(uuid.uuid4()), "name": "requirements", "slug": "requirements", "field_type": "textarea", "label": "Requirements Details", "required": True, "order": 2, "width": "full"},
            {"id": str(uuid.uuid4()), "name": "budget_range", "slug": "budget_range", "field_type": "select", "label": "Budget Range", "required": False, "order": 3, "width": "half",
             "options": [{"value": "under_50k", "label": "Under ₹50,000"}, {"value": "50k_1l", "label": "₹50,000 - ₹1 Lakh"}, {"value": "1l_5l", "label": "₹1 - ₹5 Lakh"}, {"value": "5l_10l", "label": "₹5 - ₹10 Lakh"}, {"value": "above_10l", "label": "Above ₹10 Lakh"}]},
            {"id": str(uuid.uuid4()), "name": "timeline", "slug": "timeline", "field_type": "select", "label": "Purchase Timeline", "required": False, "order": 4, "width": "half",
             "options": [{"value": "immediate", "label": "Immediate"}, {"value": "1_month", "label": "Within 1 Month"}, {"value": "3_months", "label": "1-3 Months"}, {"value": "6_months", "label": "3-6 Months"}, {"value": "planning", "label": "Just Planning"}]},
            {"id": str(uuid.uuid4()), "name": "lead_source", "slug": "lead_source", "field_type": "select", "label": "How did you hear about us?", "required": False, "order": 5, "width": "half",
             "options": [{"value": "website", "label": "Website"}, {"value": "referral", "label": "Referral"}, {"value": "google", "label": "Google Search"}, {"value": "social", "label": "Social Media"}, {"value": "exhibition", "label": "Exhibition"}, {"value": "other", "label": "Other"}]}
        ]
    })
    
    # 5. Quote Request Form
    quote_form_id = str(uuid.uuid4())
    data["forms"].append({
        "id": quote_form_id,
        "organization_id": organization_id,
        "name": "Quote Request Form",
        "slug": "quote_request_form",
        "description": "Form for quotation requests",
        "is_active": True,
        "is_system": True,
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat(),
        "fields": [
            {"id": str(uuid.uuid4()), "name": "items_required", "slug": "items_required", "field_type": "textarea", "label": "Items/Services Required", "required": True, "order": 0, "placeholder": "List items with quantities...", "width": "full"},
            {"id": str(uuid.uuid4()), "name": "delivery_location", "slug": "delivery_location", "field_type": "text", "label": "Delivery Location", "required": False, "order": 1, "width": "half"},
            {"id": str(uuid.uuid4()), "name": "required_by", "slug": "required_by", "field_type": "date", "label": "Required By Date", "required": False, "order": 2, "width": "half"},
            {"id": str(uuid.uuid4()), "name": "special_requirements", "slug": "special_requirements", "field_type": "textarea", "label": "Special Requirements", "required": False, "order": 3, "width": "full"}
        ]
    })
    
    # 6. General Inquiry Form
    general_form_id = str(uuid.uuid4())
    data["forms"].append({
        "id": general_form_id,
        "organization_id": organization_id,
        "name": "General Inquiry Form",
        "slug": "general_inquiry_form",
        "description": "Form for general inquiries",
        "is_active": True,
        "is_system": True,
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat(),
        "fields": [
            {"id": str(uuid.uuid4()), "name": "inquiry_category", "slug": "inquiry_category", "field_type": "select", "label": "Category", "required": True, "order": 0, "width": "half",
             "options": [{"value": "product_info", "label": "Product Information"}, {"value": "pricing", "label": "Pricing"}, {"value": "availability", "label": "Availability"}, {"value": "support", "label": "Support"}, {"value": "other", "label": "Other"}]},
            {"id": str(uuid.uuid4()), "name": "question", "slug": "question", "field_type": "textarea", "label": "Your Question", "required": True, "order": 1, "width": "full"}
        ]
    })
    
    # 7. Feedback Form
    feedback_form_id = str(uuid.uuid4())
    data["forms"].append({
        "id": feedback_form_id,
        "organization_id": organization_id,
        "name": "Feedback Form",
        "slug": "feedback_form",
        "description": "Form for customer feedback",
        "is_active": True,
        "is_system": True,
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat(),
        "fields": [
            {"id": str(uuid.uuid4()), "name": "feedback_type", "slug": "feedback_type", "field_type": "select", "label": "Feedback Type", "required": True, "order": 0, "width": "half",
             "options": [{"value": "compliment", "label": "Compliment"}, {"value": "suggestion", "label": "Suggestion"}, {"value": "complaint", "label": "Complaint"}, {"value": "other", "label": "Other"}]},
            {"id": str(uuid.uuid4()), "name": "rating", "slug": "rating", "field_type": "select", "label": "Overall Rating", "required": False, "order": 1, "width": "half",
             "options": [{"value": "5", "label": "⭐⭐⭐⭐⭐ Excellent"}, {"value": "4", "label": "⭐⭐⭐⭐ Good"}, {"value": "3", "label": "⭐⭐⭐ Average"}, {"value": "2", "label": "⭐⭐ Poor"}, {"value": "1", "label": "⭐ Very Poor"}]},
            {"id": str(uuid.uuid4()), "name": "feedback_details", "slug": "feedback_details", "field_type": "textarea", "label": "Your Feedback", "required": True, "order": 2, "width": "full"},
            {"id": str(uuid.uuid4()), "name": "related_ticket", "slug": "related_ticket", "field_type": "text", "label": "Related Ticket # (if any)", "required": False, "order": 3, "width": "half"}
        ]
    })
    
    # 8. Complaint Form
    complaint_form_id = str(uuid.uuid4())
    data["forms"].append({
        "id": complaint_form_id,
        "organization_id": organization_id,
        "name": "Complaint Form",
        "slug": "complaint_form",
        "description": "Form for complaints",
        "is_active": True,
        "is_system": True,
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat(),
        "fields": [
            {"id": str(uuid.uuid4()), "name": "complaint_category", "slug": "complaint_category", "field_type": "select", "label": "Complaint Category", "required": True, "order": 0, "width": "half",
             "options": [{"value": "product", "label": "Product Quality"}, {"value": "service", "label": "Service Quality"}, {"value": "delivery", "label": "Delivery Issues"}, {"value": "staff", "label": "Staff Behavior"}, {"value": "billing", "label": "Billing"}, {"value": "other", "label": "Other"}]},
            {"id": str(uuid.uuid4()), "name": "severity", "slug": "severity", "field_type": "select", "label": "Severity", "required": True, "order": 1, "width": "half",
             "options": [{"value": "minor", "label": "Minor"}, {"value": "moderate", "label": "Moderate"}, {"value": "major", "label": "Major"}, {"value": "critical", "label": "Critical"}]},
            {"id": str(uuid.uuid4()), "name": "complaint_details", "slug": "complaint_details", "field_type": "textarea", "label": "Complaint Details", "required": True, "order": 2, "width": "full"},
            {"id": str(uuid.uuid4()), "name": "expected_resolution", "slug": "expected_resolution", "field_type": "textarea", "label": "Expected Resolution", "required": False, "order": 3, "width": "full"},
            {"id": str(uuid.uuid4()), "name": "related_reference", "slug": "related_reference", "field_type": "text", "label": "Related Order/Ticket #", "required": False, "order": 4, "width": "half"}
        ]
    })
    
    # 9. Return/Refund Form
    return_form_id = str(uuid.uuid4())
    data["forms"].append({
        "id": return_form_id,
        "organization_id": organization_id,
        "name": "Return/Refund Form",
        "slug": "return_refund_form",
        "description": "Form for return and refund requests",
        "is_active": True,
        "is_system": True,
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat(),
        "fields": [
            {"id": str(uuid.uuid4()), "name": "request_type", "slug": "request_type", "field_type": "select", "label": "Request Type", "required": True, "order": 0, "width": "half",
             "options": [{"value": "return", "label": "Return"}, {"value": "exchange", "label": "Exchange"}, {"value": "refund", "label": "Refund"}]},
            {"id": str(uuid.uuid4()), "name": "order_number", "slug": "order_number", "field_type": "text", "label": "Order Number", "required": True, "order": 1, "width": "half"},
            {"id": str(uuid.uuid4()), "name": "return_reason", "slug": "return_reason", "field_type": "select", "label": "Reason", "required": True, "order": 2, "width": "half",
             "options": [{"value": "defective", "label": "Defective Product"}, {"value": "wrong_item", "label": "Wrong Item"}, {"value": "not_as_described", "label": "Not as Described"}, {"value": "changed_mind", "label": "Changed Mind"}, {"value": "other", "label": "Other"}]},
            {"id": str(uuid.uuid4()), "name": "items_to_return", "slug": "items_to_return", "field_type": "textarea", "label": "Items to Return", "required": True, "order": 3, "width": "full"},
            {"id": str(uuid.uuid4()), "name": "additional_notes", "slug": "additional_notes", "field_type": "textarea", "label": "Additional Notes", "required": False, "order": 4, "width": "full"}
        ]
    })
    
    # 10. Installation Request Form
    installation_form_id = str(uuid.uuid4())
    data["forms"].append({
        "id": installation_form_id,
        "organization_id": organization_id,
        "name": "Installation Request Form",
        "slug": "installation_form",
        "description": "Form for installation requests",
        "is_active": True,
        "is_system": True,
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat(),
        "fields": [
            {"id": str(uuid.uuid4()), "name": "installation_type", "slug": "installation_type", "field_type": "select", "label": "Installation Type", "required": True, "order": 0, "width": "half",
             "options": [{"value": "new", "label": "New Installation"}, {"value": "relocation", "label": "Relocation"}, {"value": "upgrade", "label": "Upgrade"}]},
            {"id": str(uuid.uuid4()), "name": "product_details", "slug": "product_details", "field_type": "textarea", "label": "Product/Equipment Details", "required": True, "order": 1, "width": "full"},
            {"id": str(uuid.uuid4()), "name": "preferred_date", "slug": "preferred_date", "field_type": "date", "label": "Preferred Date", "required": True, "order": 2, "width": "half"},
            {"id": str(uuid.uuid4()), "name": "installation_address", "slug": "installation_address", "field_type": "textarea", "label": "Installation Address", "required": True, "order": 3, "width": "full"},
            {"id": str(uuid.uuid4()), "name": "site_contact", "slug": "site_contact", "field_type": "text", "label": "Site Contact Person", "required": False, "order": 4, "width": "half"},
            {"id": str(uuid.uuid4()), "name": "site_phone", "slug": "site_phone", "field_type": "phone", "label": "Site Contact Phone", "required": False, "order": 5, "width": "half"}
        ]
    })
    
    # Store form IDs
    form_ids = {
        "onsite_support": onsite_form_id,
        "remote_support": remote_form_id,
        "warranty_claim": warranty_form_id,
        "sales_inquiry": sales_form_id,
        "quote_request": quote_form_id,
        "general_inquiry": general_form_id,
        "feedback": feedback_form_id,
        "complaint": complaint_form_id,
        "return_refund": return_form_id,
        "installation": installation_form_id
    }
    
    # ============================================================
    # WORKFLOWS
    # ============================================================
    
    # Helper function to create stages
    def create_stage(name, slug, stage_type, color, order, team_slug=None, transitions=None, entry_actions=None):
        return {
            "id": str(uuid.uuid4()),
            "name": name,
            "slug": slug,
            "stage_type": stage_type,
            "color": color,
            "order": order,
            "assigned_team_id": team_ids.get(team_slug) if team_slug else None,
            "transitions": transitions or [],
            "entry_actions": entry_actions or []
        }
    
    # 1. On-Site Support Workflow
    onsite_workflow_id = str(uuid.uuid4())
    onsite_stages = []
    
    # Stage IDs (pre-generate for transitions)
    s_new = str(uuid.uuid4())
    s_assigned = str(uuid.uuid4())
    s_visit_scheduled = str(uuid.uuid4())
    s_diagnosed = str(uuid.uuid4())
    s_fixed_onsite = str(uuid.uuid4())
    s_parts_required = str(uuid.uuid4())
    s_quote_sent = str(uuid.uuid4())
    s_quote_approved = str(uuid.uuid4())
    s_parts_ordered = str(uuid.uuid4())
    s_parts_received = str(uuid.uuid4())
    s_installation_scheduled = str(uuid.uuid4())
    s_closed = str(uuid.uuid4())
    s_cancelled = str(uuid.uuid4())
    
    onsite_stages = [
        {"id": s_new, "name": "New", "slug": "new", "stage_type": "initial", "color": "#6B7280", "order": 0,
         "assigned_team_id": team_ids["support_desk"],
         "transitions": [
             {"id": str(uuid.uuid4()), "to_stage_id": s_assigned, "label": "Assign Technician", "color": "primary", "order": 0, "requires_input": "assign_engineer"}
         ],
         "entry_actions": []},
        
        {"id": s_assigned, "name": "Assigned", "slug": "assigned", "stage_type": "in_progress", "color": "#3B82F6", "order": 1,
         "assigned_team_id": team_ids["field_technicians"],
         "transitions": [
             {"id": str(uuid.uuid4()), "to_stage_id": s_visit_scheduled, "label": "Schedule Visit", "color": "primary", "order": 0, "requires_input": "schedule_visit"}
         ],
         "entry_actions": [
             {"id": str(uuid.uuid4()), "action_type": "create_task", "config": {"task_type_slug": "schedule_visit"}, "order": 0},
             {"id": str(uuid.uuid4()), "action_type": "send_notification", "config": {"event": "ticket_assigned", "recipients": ["assignee"]}, "order": 1}
         ]},
        
        {"id": s_visit_scheduled, "name": "Visit Scheduled", "slug": "visit_scheduled", "stage_type": "in_progress", "color": "#8B5CF6", "order": 2,
         "assigned_team_id": team_ids["field_technicians"],
         "transitions": [
             {"id": str(uuid.uuid4()), "to_stage_id": s_diagnosed, "label": "Submit Diagnosis", "color": "primary", "order": 0, "requires_input": "diagnosis", "allowed_roles": ["field_technician"]}
         ],
         "entry_actions": [
             {"id": str(uuid.uuid4()), "action_type": "create_task", "config": {"task_type_slug": "site_visit"}, "order": 0},
             {"id": str(uuid.uuid4()), "action_type": "send_notification", "config": {"event": "visit_scheduled", "recipients": ["customer"]}, "order": 1}
         ]},
        
        {"id": s_diagnosed, "name": "Diagnosed", "slug": "diagnosed", "stage_type": "in_progress", "color": "#F59E0B", "order": 3,
         "transitions": [
             {"id": str(uuid.uuid4()), "to_stage_id": s_fixed_onsite, "label": "Fixed On-Site", "color": "success", "order": 0, "requires_input": "resolution"},
             {"id": str(uuid.uuid4()), "to_stage_id": s_parts_required, "label": "Parts Required", "color": "warning", "order": 1, "requires_input": "parts_list"}
         ],
         "entry_actions": []},
        
        {"id": s_fixed_onsite, "name": "Fixed On-Site", "slug": "fixed_onsite", "stage_type": "in_progress", "color": "#10B981", "order": 4,
         "transitions": [
             {"id": str(uuid.uuid4()), "to_stage_id": s_closed, "label": "Close Ticket", "color": "success", "order": 0}
         ],
         "entry_actions": [
             {"id": str(uuid.uuid4()), "action_type": "create_task", "config": {"task_type_slug": "follow_up"}, "order": 0}
         ]},
        
        {"id": s_parts_required, "name": "Parts Required", "slug": "parts_required", "stage_type": "waiting", "color": "#EC4899", "order": 5,
         "assigned_team_id": team_ids["back_office"],
         "transitions": [
             {"id": str(uuid.uuid4()), "to_stage_id": s_quote_sent, "label": "Send Quotation", "color": "primary", "order": 0, "requires_input": "quotation"}
         ],
         "entry_actions": [
             {"id": str(uuid.uuid4()), "action_type": "create_task", "config": {"task_type_slug": "prepare_quote"}, "order": 0},
             {"id": str(uuid.uuid4()), "action_type": "send_notification", "config": {"event": "quote_required", "recipients": ["team"]}, "order": 1}
         ]},
        
        {"id": s_quote_sent, "name": "Quote Sent", "slug": "quote_sent", "stage_type": "waiting", "color": "#F97316", "order": 6,
         "transitions": [
             {"id": str(uuid.uuid4()), "to_stage_id": s_quote_approved, "label": "Customer Approved", "color": "success", "order": 0},
             {"id": str(uuid.uuid4()), "to_stage_id": s_cancelled, "label": "Customer Declined", "color": "danger", "order": 1}
         ],
         "entry_actions": [
             {"id": str(uuid.uuid4()), "action_type": "send_notification", "config": {"event": "quote_sent", "recipients": ["customer"]}, "order": 0}
         ]},
        
        {"id": s_quote_approved, "name": "Quote Approved", "slug": "quote_approved", "stage_type": "in_progress", "color": "#14B8A6", "order": 7,
         "assigned_team_id": team_ids["procurement"],
         "transitions": [
             {"id": str(uuid.uuid4()), "to_stage_id": s_parts_ordered, "label": "Order Parts", "color": "primary", "order": 0}
         ],
         "entry_actions": [
             {"id": str(uuid.uuid4()), "action_type": "create_task", "config": {"task_type_slug": "order_parts"}, "order": 0},
             {"id": str(uuid.uuid4()), "action_type": "send_notification", "config": {"event": "quote_approved", "recipients": ["team"]}, "order": 1}
         ]},
        
        {"id": s_parts_ordered, "name": "Parts Ordered", "slug": "parts_ordered", "stage_type": "waiting", "color": "#06B6D4", "order": 8,
         "assigned_team_id": team_ids["procurement"],
         "transitions": [
             {"id": str(uuid.uuid4()), "to_stage_id": s_parts_received, "label": "Parts Received", "color": "success", "order": 0}
         ],
         "entry_actions": [
             {"id": str(uuid.uuid4()), "action_type": "create_task", "config": {"task_type_slug": "receive_parts"}, "order": 0}
         ]},
        
        {"id": s_parts_received, "name": "Parts Received", "slug": "parts_received", "stage_type": "in_progress", "color": "#8B5CF6", "order": 9,
         "assigned_team_id": team_ids["field_technicians"],
         "transitions": [
             {"id": str(uuid.uuid4()), "to_stage_id": s_installation_scheduled, "label": "Schedule Installation", "color": "primary", "order": 0, "requires_input": "schedule_visit"}
         ],
         "entry_actions": [
             {"id": str(uuid.uuid4()), "action_type": "send_notification", "config": {"event": "parts_received", "recipients": ["assignee", "customer"]}, "order": 0}
         ]},
        
        {"id": s_installation_scheduled, "name": "Installation Scheduled", "slug": "installation_scheduled", "stage_type": "in_progress", "color": "#10B981", "order": 10,
         "assigned_team_id": team_ids["field_technicians"],
         "transitions": [
             {"id": str(uuid.uuid4()), "to_stage_id": s_closed, "label": "Installation Complete", "color": "success", "order": 0}
         ],
         "entry_actions": [
             {"id": str(uuid.uuid4()), "action_type": "create_task", "config": {"task_type_slug": "installation"}, "order": 0},
             {"id": str(uuid.uuid4()), "action_type": "send_notification", "config": {"event": "installation_scheduled", "recipients": ["customer"]}, "order": 1}
         ]},
        
        {"id": s_closed, "name": "Closed", "slug": "closed", "stage_type": "terminal_success", "color": "#22C55E", "order": 11,
         "transitions": [],
         "entry_actions": [
             {"id": str(uuid.uuid4()), "action_type": "send_notification", "config": {"event": "ticket_closed", "recipients": ["customer", "assignee"]}, "order": 0}
         ]},
        
        {"id": s_cancelled, "name": "Cancelled", "slug": "cancelled", "stage_type": "terminal_failure", "color": "#EF4444", "order": 12,
         "transitions": [],
         "entry_actions": []}
    ]
    
    data["workflows"].append({
        "id": onsite_workflow_id,
        "organization_id": organization_id,
        "name": "On-Site Technical Support",
        "slug": "onsite_support_workflow",
        "description": "Workflow for field service with parts and installation",
        "stages": onsite_stages,
        "is_active": True,
        "is_system": True,
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # 2. Remote Support Workflow
    remote_workflow_id = str(uuid.uuid4())
    rs_new = str(uuid.uuid4())
    rs_assigned = str(uuid.uuid4())
    rs_session_scheduled = str(uuid.uuid4())
    rs_in_session = str(uuid.uuid4())
    rs_resolved = str(uuid.uuid4())
    rs_escalated = str(uuid.uuid4())
    rs_closed = str(uuid.uuid4())
    
    remote_stages = [
        {"id": rs_new, "name": "New", "slug": "new", "stage_type": "initial", "color": "#6B7280", "order": 0,
         "assigned_team_id": team_ids["remote_support"],
         "transitions": [{"id": str(uuid.uuid4()), "to_stage_id": rs_assigned, "label": "Assign Agent", "color": "primary", "order": 0, "requires_input": "assign_engineer"}],
         "entry_actions": []},
        
        {"id": rs_assigned, "name": "Assigned", "slug": "assigned", "stage_type": "in_progress", "color": "#3B82F6", "order": 1,
         "transitions": [{"id": str(uuid.uuid4()), "to_stage_id": rs_session_scheduled, "label": "Schedule Session", "color": "primary", "order": 0, "requires_input": "schedule_visit"}],
         "entry_actions": [
             {"id": str(uuid.uuid4()), "action_type": "send_notification", "config": {"event": "ticket_assigned", "recipients": ["assignee"]}, "order": 0}
         ]},
        
        {"id": rs_session_scheduled, "name": "Session Scheduled", "slug": "session_scheduled", "stage_type": "in_progress", "color": "#8B5CF6", "order": 2,
         "transitions": [{"id": str(uuid.uuid4()), "to_stage_id": rs_in_session, "label": "Start Session", "color": "primary", "order": 0}],
         "entry_actions": [
             {"id": str(uuid.uuid4()), "action_type": "create_task", "config": {"task_type_slug": "remote_session"}, "order": 0},
             {"id": str(uuid.uuid4()), "action_type": "send_notification", "config": {"event": "session_scheduled", "recipients": ["customer"]}, "order": 1}
         ]},
        
        {"id": rs_in_session, "name": "In Session", "slug": "in_session", "stage_type": "in_progress", "color": "#F59E0B", "order": 3,
         "transitions": [
             {"id": str(uuid.uuid4()), "to_stage_id": rs_resolved, "label": "Resolved", "color": "success", "order": 0},
             {"id": str(uuid.uuid4()), "to_stage_id": rs_escalated, "label": "Escalate to On-Site", "color": "warning", "order": 1}
         ],
         "entry_actions": []},
        
        {"id": rs_resolved, "name": "Resolved", "slug": "resolved", "stage_type": "in_progress", "color": "#10B981", "order": 4,
         "transitions": [{"id": str(uuid.uuid4()), "to_stage_id": rs_closed, "label": "Close Ticket", "color": "success", "order": 0}],
         "entry_actions": [
             {"id": str(uuid.uuid4()), "action_type": "create_task", "config": {"task_type_slug": "follow_up"}, "order": 0}
         ]},
        
        {"id": rs_escalated, "name": "Escalated to On-Site", "slug": "escalated", "stage_type": "waiting", "color": "#EF4444", "order": 5,
         "transitions": [],
         "entry_actions": [
             {"id": str(uuid.uuid4()), "action_type": "send_notification", "config": {"event": "ticket_escalated", "recipients": ["manager"]}, "order": 0}
         ]},
        
        {"id": rs_closed, "name": "Closed", "slug": "closed", "stage_type": "terminal_success", "color": "#22C55E", "order": 6,
         "transitions": [],
         "entry_actions": []}
    ]
    
    data["workflows"].append({
        "id": remote_workflow_id,
        "organization_id": organization_id,
        "name": "Remote Support",
        "slug": "remote_support_workflow",
        "description": "Workflow for remote assistance",
        "stages": remote_stages,
        "is_active": True,
        "is_system": True,
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # 3. Sales Inquiry Workflow
    sales_workflow_id = str(uuid.uuid4())
    sl_new = str(uuid.uuid4())
    sl_contacted = str(uuid.uuid4())
    sl_qualified = str(uuid.uuid4())
    sl_demo = str(uuid.uuid4())
    sl_proposal = str(uuid.uuid4())
    sl_negotiation = str(uuid.uuid4())
    sl_won = str(uuid.uuid4())
    sl_lost = str(uuid.uuid4())
    
    sales_stages = [
        {"id": sl_new, "name": "New Lead", "slug": "new", "stage_type": "initial", "color": "#6B7280", "order": 0,
         "assigned_team_id": team_ids["sales_team"],
         "transitions": [{"id": str(uuid.uuid4()), "to_stage_id": sl_contacted, "label": "Contact Lead", "color": "primary", "order": 0}],
         "entry_actions": [
             {"id": str(uuid.uuid4()), "action_type": "create_task", "config": {"task_type_slug": "contact_customer"}, "order": 0}
         ]},
        
        {"id": sl_contacted, "name": "Contacted", "slug": "contacted", "stage_type": "in_progress", "color": "#3B82F6", "order": 1,
         "transitions": [
             {"id": str(uuid.uuid4()), "to_stage_id": sl_qualified, "label": "Qualify Lead", "color": "primary", "order": 0},
             {"id": str(uuid.uuid4()), "to_stage_id": sl_lost, "label": "Not Interested", "color": "danger", "order": 1}
         ],
         "entry_actions": []},
        
        {"id": sl_qualified, "name": "Qualified", "slug": "qualified", "stage_type": "in_progress", "color": "#8B5CF6", "order": 2,
         "transitions": [
             {"id": str(uuid.uuid4()), "to_stage_id": sl_demo, "label": "Schedule Demo", "color": "primary", "order": 0},
             {"id": str(uuid.uuid4()), "to_stage_id": sl_proposal, "label": "Send Proposal", "color": "primary", "order": 1}
         ],
         "entry_actions": []},
        
        {"id": sl_demo, "name": "Demo Scheduled", "slug": "demo", "stage_type": "in_progress", "color": "#F59E0B", "order": 3,
         "transitions": [
             {"id": str(uuid.uuid4()), "to_stage_id": sl_proposal, "label": "Send Proposal", "color": "primary", "order": 0},
             {"id": str(uuid.uuid4()), "to_stage_id": sl_lost, "label": "Not Interested", "color": "danger", "order": 1}
         ],
         "entry_actions": [
             {"id": str(uuid.uuid4()), "action_type": "create_task", "config": {"task_type_slug": "schedule_demo"}, "order": 0}
         ]},
        
        {"id": sl_proposal, "name": "Proposal Sent", "slug": "proposal", "stage_type": "waiting", "color": "#EC4899", "order": 4,
         "transitions": [
             {"id": str(uuid.uuid4()), "to_stage_id": sl_negotiation, "label": "Negotiate", "color": "warning", "order": 0},
             {"id": str(uuid.uuid4()), "to_stage_id": sl_won, "label": "Won", "color": "success", "order": 1},
             {"id": str(uuid.uuid4()), "to_stage_id": sl_lost, "label": "Lost", "color": "danger", "order": 2}
         ],
         "entry_actions": []},
        
        {"id": sl_negotiation, "name": "Negotiation", "slug": "negotiation", "stage_type": "in_progress", "color": "#F97316", "order": 5,
         "transitions": [
             {"id": str(uuid.uuid4()), "to_stage_id": sl_won, "label": "Won", "color": "success", "order": 0},
             {"id": str(uuid.uuid4()), "to_stage_id": sl_lost, "label": "Lost", "color": "danger", "order": 1}
         ],
         "entry_actions": []},
        
        {"id": sl_won, "name": "Won", "slug": "won", "stage_type": "terminal_success", "color": "#22C55E", "order": 6,
         "transitions": [],
         "entry_actions": [
             {"id": str(uuid.uuid4()), "action_type": "send_notification", "config": {"event": "deal_won", "recipients": ["team", "manager"]}, "order": 0}
         ]},
        
        {"id": sl_lost, "name": "Lost", "slug": "lost", "stage_type": "terminal_failure", "color": "#EF4444", "order": 7,
         "transitions": [],
         "entry_actions": []}
    ]
    
    data["workflows"].append({
        "id": sales_workflow_id,
        "organization_id": organization_id,
        "name": "Sales Pipeline",
        "slug": "sales_pipeline_workflow",
        "description": "Workflow for sales inquiries and leads",
        "stages": sales_stages,
        "is_active": True,
        "is_system": True,
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # 4. Simple Support Workflow (for general inquiries, feedback, etc.)
    simple_workflow_id = str(uuid.uuid4())
    sim_new = str(uuid.uuid4())
    sim_progress = str(uuid.uuid4())
    sim_resolved = str(uuid.uuid4())
    sim_closed = str(uuid.uuid4())
    
    simple_stages = [
        {"id": sim_new, "name": "New", "slug": "new", "stage_type": "initial", "color": "#6B7280", "order": 0,
         "transitions": [{"id": str(uuid.uuid4()), "to_stage_id": sim_progress, "label": "Start Working", "color": "primary", "order": 0}],
         "entry_actions": []},
        
        {"id": sim_progress, "name": "In Progress", "slug": "in_progress", "stage_type": "in_progress", "color": "#3B82F6", "order": 1,
         "transitions": [{"id": str(uuid.uuid4()), "to_stage_id": sim_resolved, "label": "Resolve", "color": "success", "order": 0}],
         "entry_actions": []},
        
        {"id": sim_resolved, "name": "Resolved", "slug": "resolved", "stage_type": "in_progress", "color": "#10B981", "order": 2,
         "transitions": [{"id": str(uuid.uuid4()), "to_stage_id": sim_closed, "label": "Close", "color": "success", "order": 0}],
         "entry_actions": []},
        
        {"id": sim_closed, "name": "Closed", "slug": "closed", "stage_type": "terminal_success", "color": "#22C55E", "order": 3,
         "transitions": [],
         "entry_actions": []}
    ]
    
    data["workflows"].append({
        "id": simple_workflow_id,
        "organization_id": organization_id,
        "name": "Simple Support",
        "slug": "simple_support_workflow",
        "description": "Simple workflow for general requests",
        "stages": simple_stages,
        "is_active": True,
        "is_system": True,
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat()
    })
    
    # Store workflow IDs
    workflow_ids = {
        "onsite_support": onsite_workflow_id,
        "remote_support": remote_workflow_id,
        "sales_pipeline": sales_workflow_id,
        "simple_support": simple_workflow_id
    }
    
    # ============================================================
    # HELP TOPICS
    # ============================================================
    help_topics_data = [
        {"name": "On-Site Technical Support", "slug": "onsite-support", "description": "Request a technician visit for hardware/software issues", 
         "icon": "wrench", "color": "#EF4444", "category": "support", "form_id": form_ids["onsite_support"], "workflow_id": workflow_ids["onsite_support"],
         "default_team_id": team_ids["support_desk"], "require_company": True, "require_device": True},
        
        {"name": "Remote Support", "slug": "remote-support", "description": "Get remote assistance for software and configuration issues",
         "icon": "monitor", "color": "#8B5CF6", "category": "support", "form_id": form_ids["remote_support"], "workflow_id": workflow_ids["remote_support"],
         "default_team_id": team_ids["remote_support"], "require_company": True, "require_device": False},
        
        {"name": "Warranty / AMC Claim", "slug": "warranty-claim", "description": "Report device failure under warranty or AMC",
         "icon": "shield", "color": "#F59E0B", "category": "support", "form_id": form_ids["warranty_claim"], "workflow_id": workflow_ids["onsite_support"],
         "default_team_id": team_ids["support_desk"], "require_company": True, "require_device": True},
        
        {"name": "Sales Inquiry", "slug": "sales-inquiry", "description": "New purchase inquiries and business opportunities",
         "icon": "trending-up", "color": "#10B981", "category": "sales", "form_id": form_ids["sales_inquiry"], "workflow_id": workflow_ids["sales_pipeline"],
         "default_team_id": team_ids["sales_team"], "require_company": True, "require_device": False},
        
        {"name": "Request Quote", "slug": "quote-request", "description": "Request pricing quotation for products/services",
         "icon": "file-text", "color": "#3B82F6", "category": "sales", "form_id": form_ids["quote_request"], "workflow_id": workflow_ids["simple_support"],
         "default_team_id": team_ids["back_office"], "require_company": True, "require_device": False},
        
        {"name": "General Inquiry", "slug": "general-inquiry", "description": "General questions and information requests",
         "icon": "help-circle", "color": "#6B7280", "category": "general", "form_id": form_ids["general_inquiry"], "workflow_id": workflow_ids["simple_support"],
         "default_team_id": team_ids["support_desk"], "require_company": False, "require_device": False},
        
        {"name": "Feedback", "slug": "feedback", "description": "Share your feedback or suggestions",
         "icon": "message-square", "color": "#14B8A6", "category": "general", "form_id": form_ids["feedback"], "workflow_id": workflow_ids["simple_support"],
         "default_team_id": team_ids["support_desk"], "require_company": False, "require_device": False},
        
        {"name": "Complaint", "slug": "complaint", "description": "Report a complaint or issue",
         "icon": "alert-triangle", "color": "#EF4444", "category": "support", "form_id": form_ids["complaint"], "workflow_id": workflow_ids["simple_support"],
         "default_team_id": team_ids["support_desk"], "require_company": False, "require_device": False, "default_priority": "high"},
        
        {"name": "Return / Refund", "slug": "return-refund", "description": "Request product return or refund",
         "icon": "rotate-ccw", "color": "#EC4899", "category": "operations", "form_id": form_ids["return_refund"], "workflow_id": workflow_ids["simple_support"],
         "default_team_id": team_ids["back_office"], "require_company": True, "require_device": False},
        
        {"name": "Installation Request", "slug": "installation", "description": "Request new installation or relocation",
         "icon": "package", "color": "#06B6D4", "category": "operations", "form_id": form_ids["installation"], "workflow_id": workflow_ids["onsite_support"],
         "default_team_id": team_ids["field_technicians"], "require_company": True, "require_device": False}
    ]
    
    for topic in help_topics_data:
        data["help_topics"].append({
            "id": str(uuid.uuid4()),
            "organization_id": organization_id,
            "sla_policy_id": None,
            "default_priority": "medium",
            "auto_assign": False,
            "assignment_method": "manual",
            "require_contact": True,
            "is_public": True,
            "is_active": True,
            "is_system": True,
            "ticket_count": 0,
            "created_at": get_ist_isoformat(),
            "updated_at": get_ist_isoformat(),
            **topic
        })
    
    # ============================================================
    # CANNED RESPONSES
    # ============================================================
    canned_responses_data = [
        {"name": "Acknowledgment", "slug": "acknowledgment", "category": "general",
         "subject": "We've received your request",
         "body": "Thank you for contacting us. We have received your request and a member of our team will review it shortly.\n\nYour ticket number is {{ticket.number}}. Please keep this for your reference.\n\nWe'll get back to you as soon as possible."},
        
        {"name": "Request More Info", "slug": "request_info", "category": "general",
         "subject": "Additional information needed",
         "body": "Thank you for your request. To help us assist you better, could you please provide the following additional information:\n\n1. [Specific information needed]\n2. [Any other details]\n\nOnce we have this information, we'll be able to proceed with your request."},
        
        {"name": "Visit Scheduled", "slug": "visit_scheduled", "category": "support",
         "subject": "Technician visit scheduled",
         "body": "We have scheduled a technician visit for your request.\n\nDate: {{form.preferred_date}}\nTime: {{form.preferred_time}}\n\nOur technician will contact you before arriving. Please ensure someone is available at the location.\n\nIf you need to reschedule, please reply to this message."},
        
        {"name": "Quote Ready", "slug": "quote_ready", "category": "sales",
         "subject": "Your quotation is ready",
         "body": "We have prepared the quotation for your request.\n\nPlease find the attached quotation document. The quote is valid for 15 days.\n\nIf you have any questions or would like to proceed, please let us know."},
        
        {"name": "Parts Ordered", "slug": "parts_ordered", "category": "support",
         "subject": "Parts have been ordered",
         "body": "We have placed the order for the required parts.\n\nEstimated delivery: 3-5 business days\n\nOnce the parts arrive, we will contact you to schedule the installation."},
        
        {"name": "Issue Resolved", "slug": "issue_resolved", "category": "support",
         "subject": "Your issue has been resolved",
         "body": "We're pleased to inform you that your issue has been resolved.\n\nSummary of resolution:\n{{resolution_notes}}\n\nIf you experience any further issues or have questions, please don't hesitate to contact us.\n\nThank you for your patience."},
        
        {"name": "Closing Follow-up", "slug": "closing_followup", "category": "general",
         "subject": "Following up on your ticket",
         "body": "We're following up on your recent support ticket #{{ticket.number}}.\n\nIt has been {{days_since}} days since our last update. If you're still experiencing issues or need assistance, please reply to this message.\n\nIf everything is working well, we'll close this ticket in 48 hours."},
        
        {"name": "Warranty Claim Logged", "slug": "warranty_logged", "category": "support",
         "subject": "Warranty claim logged with manufacturer",
         "body": "We have logged your warranty claim with the manufacturer.\n\nRMA/Case Number: {{rma_number}}\nExpected Timeline: {{expected_timeline}}\n\nWe will keep you updated on the progress. You can also check the status using the reference number above."},
        
        {"name": "Demo Confirmation", "slug": "demo_confirmation", "category": "sales",
         "subject": "Demo scheduled - Confirmation",
         "body": "Your product demonstration has been confirmed.\n\nDate: {{demo_date}}\nTime: {{demo_time}}\nMode: {{demo_mode}}\n\nOur representative will contact you before the demo. If you need to reschedule, please let us know at least 24 hours in advance."}
    ]
    
    for response in canned_responses_data:
        data["canned_responses"].append({
            "id": str(uuid.uuid4()),
            "organization_id": organization_id,
            "help_topic_ids": [],
            "is_active": True,
            "created_at": get_ist_isoformat(),
            **response
        })
    
    # ============================================================
    # NOTIFICATION TEMPLATES
    # ============================================================
    notification_templates_data = [
        {"name": "Ticket Created", "slug": "ticket_created", "event": "ticket_created",
         "channels": ["email", "in_app"],
         "email_subject": "Ticket #{{ticket.number}} - {{ticket.subject}}",
         "email_body": "A new ticket has been created.\n\nTicket: #{{ticket.number}}\nSubject: {{ticket.subject}}\nPriority: {{ticket.priority}}\n\nView ticket: {{ticket.link}}",
         "in_app_title": "New Ticket Created",
         "in_app_body": "Ticket #{{ticket.number}} has been created",
         "recipients": ["creator", "team"]},
        
        {"name": "Ticket Assigned", "slug": "ticket_assigned", "event": "ticket_assigned",
         "channels": ["email", "in_app"],
         "email_subject": "Ticket #{{ticket.number}} assigned to you",
         "email_body": "A ticket has been assigned to you.\n\nTicket: #{{ticket.number}}\nSubject: {{ticket.subject}}\nPriority: {{ticket.priority}}\n\nView ticket: {{ticket.link}}",
         "in_app_title": "Ticket Assigned",
         "in_app_body": "Ticket #{{ticket.number}} has been assigned to you",
         "recipients": ["assignee"]},
        
        {"name": "Task Created", "slug": "task_created", "event": "task_created",
         "channels": ["email", "in_app"],
         "email_subject": "New task: {{task.name}}",
         "email_body": "A new task has been created for you.\n\nTask: {{task.name}}\nTicket: #{{ticket.number}}\nDue: {{task.due_date}}\n\nView task: {{task.link}}",
         "in_app_title": "New Task",
         "in_app_body": "{{task.name}} - Due: {{task.due_date}}",
         "recipients": ["assignee"]},
        
        {"name": "Stage Changed", "slug": "stage_changed", "event": "stage_changed",
         "channels": ["in_app"],
         "in_app_title": "Ticket Status Updated",
         "in_app_body": "Ticket #{{ticket.number}} moved to {{stage.name}}",
         "recipients": ["assignee", "creator"]},
        
        {"name": "Customer Reply", "slug": "customer_reply", "event": "customer_reply",
         "channels": ["email", "in_app"],
         "email_subject": "New reply on Ticket #{{ticket.number}}",
         "email_body": "The customer has replied to the ticket.\n\nTicket: #{{ticket.number}}\nSubject: {{ticket.subject}}\n\nView ticket: {{ticket.link}}",
         "in_app_title": "Customer Reply",
         "in_app_body": "New reply on #{{ticket.number}}",
         "recipients": ["assignee"]},
        
        {"name": "Ticket Closed", "slug": "ticket_closed", "event": "ticket_closed",
         "channels": ["email"],
         "email_subject": "Ticket #{{ticket.number}} - Closed",
         "email_body": "Your ticket has been closed.\n\nTicket: #{{ticket.number}}\nSubject: {{ticket.subject}}\n\nIf you need further assistance, please reply to this email or create a new ticket.",
         "recipients": ["customer"]}
    ]
    
    for template in notification_templates_data:
        data["notification_templates"].append({
            "id": str(uuid.uuid4()),
            "organization_id": organization_id,
            "sms_body": None,
            "whatsapp_template_id": None,
            "is_active": True,
            "created_at": get_ist_isoformat(),
            **template
        })
    
    return data
