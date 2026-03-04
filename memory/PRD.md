# Warranty & Asset Tracking Portal - PRD

## Original Problem Statement
Build an enterprise-grade Warranty & Asset Tracking Portal with a highly configurable, master-driven, multi-workflow ticketing system with strict multi-tenant data isolation.

## What's Been Implemented

### P0 Feature Verification Complete (Mar 4, 2026)
- **Customer Quotation Approval via Email**: Token-based public endpoints for approve/reject. Admin can send quotation emails from ticket detail. Customers click approve/deny buttons in email. Backend: POST /api/ticketing/tickets/{id}/send-quotation-email, GET /api/ticketing/quotation-response/{token}?action=approve|reject
- **Engineer Portal Workflow Sync**: Progress bar with 13 stages, current stage highlighted, available transitions displayed. Backend: GET /api/engineer/ticket/{id}/workflow
- **Help Topic -> Form Linking**: All 43 topics linked to forms. Dynamic form fields shown in Create Ticket modal when topic selected.
- **Testing: 100% backend (10/10), 100% frontend (all flows verified)**

### Comprehensive Help Topic System (Mar 4, 2026)
- **8 master categories**: Hardware & Devices, Software & OS, Network & Connectivity, Peripherals & Accessories, Service Requests, Warranty & AMC, Commercial & Billing, General
- **43 help topics** covering all MSP/warranty scenarios with searchable tags
- Full CRUD for categories and topics
- Searchable topic selector in ticket creation (grouped by category, fuzzy search)
- **Testing: 100% (14/14 backend, all frontend)**

### Warranty-Based Workflow System (Mar 4, 2026)
- 3 device-type workflows: OEM Warranty (8 stages), AMC Support (10 stages), Non-Warranty (12 stages)
- Auto-detection engine: checks warranty dates + AMC contracts -> assigns workflow
- OEM Tracking Panel on ticket detail
- **Testing: 100% (9/9 backend, all frontend)**

### WhatsApp + Email Notifications (Mar 2, 2026)
- Stage-based notification panel with 5 team options via wa.me/ links
- Configurable team phone numbers and emails in Settings
- **Testing: 100% (15/15 backend, all frontend)**

### Admin Ticket Dashboard Redesign (Mar 2, 2026)
- "To Be Assigned" / "Assigned Tickets" split with status filter pills
- **Testing: 100% (13/13 backend, all frontend)**

### Previous Work (Feb-Mar 2026)
- Engineer reschedule, visit workflow, inventory, pending bills, bulk upload, parts requests, branding

## Architecture
- Frontend: React + Tailwind + Shadcn/UI
- Backend: FastAPI + Motor (MongoDB async)
- Database: MongoDB | Auth: JWT-based

## Key Collections
- `help_topic_categories` - 8 master categories (CRUD)
- `ticket_help_topics` - 43+ topics with category_id, tags, parent_id, workflow_id, form_id
- `ticket_workflows` - 7 workflows including OEM, AMC, Non-Warranty
- `tickets_v2` - with device_warranty_type, OEM tracking fields
- `quotation_approvals` - token-based customer approval records

## Prioritized Backlog

### P0 (Next)
- Multi-tenant Customer Facing Portal (portal.aftersales.support/{tenant_code})
- Form Builder UI (admin dynamic form creation/editing)
- Workflow Designer UI (visual workflow editor)
- Email Inbox UI (IMAP/SMTP)

### P1
- Full CRUD for SLAs, Priorities, Canned Responses
- Notification Engine (Email/In-app)
- Quotation PDF Generation
- Razorpay Integration

### P2
- CompanySwitcher for platform admins
- server.py refactor & User/Staff model unification
- ESLint warnings cleanup & legacy-peer-deps fix

## Credentials
- Admin: ck@motta.in / Charu@123@
- Test Engineer: test_engineer_1bfa72f0@test.com / Test@123
