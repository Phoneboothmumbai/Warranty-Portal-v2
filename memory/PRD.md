# Warranty & Asset Tracking Portal - PRD

## Original Problem Statement
Build an enterprise-grade Warranty & Asset Tracking Portal with a highly configurable, master-driven, multi-workflow ticketing system with strict multi-tenant data isolation.

## Core Requirements
- Role-based access: Admin vs Engineer portals
- Master-driven ticketing: Help Topics, Forms, Workflows, Teams, Roles, SLA, Canned Responses
- Job acceptance/decline/reschedule workflow for technicians
- Central calendar (admin) and personal calendar (engineer)
- Workforce management with working hours, holidays, salary
- Strict multi-tenant data isolation - all data scoped by organization_id
- Enhanced ticket creation: Company > Site > Employee > Device with inline "Add New"
- Device-type based workflow routing (OEM Warranty, AMC, Non-Warranty)

## What's Been Implemented

### Warranty-Based Workflow System (Mar 4, 2026)
- **3 new workflows** with full stage definitions and transitions:
  - **OEM Warranty**: New → Verified Warranty → Escalated to OEM → OEM Case Logged → OEM Engineer Dispatched → OEM Resolution → Closed
  - **AMC Support**: New → Assigned → Scheduled → In Progress → Diagnosed → Awaiting Parts → Parts Received → Fixed On-Site → Resolved
  - **Non-Warranty**: New → Assigned → Diagnosed → Quotation Sent → Customer Approved/Rejected → Parts Ordered → In Progress → Fixed → Billing Pending → Resolved
- **3 new Help Topics** auto-linked to workflows: Warranty Claim (OEM), AMC Support, Non-Warranty Repair
- **Auto-detection engine**: When device selected during ticket creation, system checks warranty_end_date and AMC contracts to determine device type
- **OEM Tracking fields**: oem_case_number, oem_engineer_name, oem_engineer_phone, oem_brand_reference, oem_status, oem_notes
- **OEM Tracking Panel** on ticket detail page with edit capability
- **Warranty type badge** in ticket sidebar showing coverage status
- **Testing: 100% backend (9/9), 100% frontend**

### WhatsApp + Email Notifications (Mar 2, 2026)
- Stage-based notification panel with 5 team options
- wa.me/ links for WhatsApp (no API), email via SMTP
- Configurable team phone numbers and emails in Settings
- **Testing: 100% backend (15/15), 100% frontend**

### Admin Ticket Dashboard Redesign (Mar 2, 2026)
- Split into "To Be Assigned" and "Assigned Tickets" sections
- Status filter pills, enhanced stats cards
- **Testing: 100% backend (13/13), 100% frontend**

### Previous Work (Feb-Mar 2026)
- Engineer reschedule fix (slot-based scheduling)
- On-site engineer visit workflow (timer, diagnosis, parts request, checkout)
- Inventory management (stock tracking, auto-deduction, history)
- Pending bills system (auto-generated, email notifications)
- Item Master bulk upload (CSV with duplicate detection)
- Parts requests management page
- Brand hardening (aftersales.support)
- Full admin/engineer portals, ticketing V2, workforce, calendars

## Architecture
- Frontend: React + Tailwind + Shadcn/UI
- Backend: FastAPI + Motor (MongoDB async)
- Database: MongoDB
- Auth: JWT-based, separate admin/engineer tokens

## Key Collections
- `tickets_v2` — with device_warranty_type and OEM tracking fields
- `ticket_workflows` — includes oem-warranty, amc-support, non-warranty
- `ticket_help_topics` — linked to workflows
- `engineers`, `staff_users`, `devices`, `amc_contracts`
- `settings` — billing_emails, team phones, team emails

## Key API Endpoints
- POST /api/ticketing/seed-warranty-workflows — Creates 3 warranty workflows + help topics
- GET /api/ticketing/device-warranty-check/{device_id} — Auto-detect warranty type
- POST /api/ticketing/tickets/{id}/send-notification — WhatsApp + Email notifications
- GET /api/ticketing/tickets?assigned=true/false&status=X — Filtered listing

## Prioritized Backlog

### P0 (Next)
- Customer Quotation Approval via Email (approve/deny buttons)
- Engineer portal sync with workflow stages
- Form Builder UI (drag-and-drop custom ticket forms)
- Workflow Designer UI visual improvements

### P1
- Full CRUD for Teams, SLAs, Priorities, Canned Responses
- Notification Engine (Email/In-app)
- Quotation PDF Generation
- Razorpay Integration
- Email Inbox UI (IMAP/SMTP config)

### P2
- CompanySwitcher for platform admins
- Refactor server.py / unify User/Staff models
- Fix ESLint warnings and --legacy-peer-deps
- Scalability improvements (connection pooling, Redis, workers)

## Credentials
- Admin: ck@motta.in / Charu@123@
- Test Engineer: testeng@test.com / Test@123
- Production domain: aftersales.support
