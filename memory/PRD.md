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

## What's Been Implemented

### WhatsApp + Email Notifications (Mar 2, 2026)
- Stage-based notification system on ticket detail page
- wa.me/ links open WhatsApp on user's computer with pre-filled messages
- 5 notification options: Engineer, Parts Team, Billing Team, Quote Team, Backend Team
- Recommended option auto-highlighted based on current ticket stage
- Configurable team phone numbers and email lists in Settings
- Backend sends email via SMTP + returns wa.me link data
- Timeline entries added for each notification sent
- Fallback: message copied to clipboard if no phone configured
- **Testing: 100% backend (15/15), 100% frontend**

### Admin Ticket Dashboard Redesign (Mar 2, 2026)
- Split ticket list into "To Be Assigned" (unassigned) and "Assigned Tickets" sections
- Status filter pills (New, Assigned, In Progress, Awaiting Parts, etc.)
- Stats cards: Unassigned, Open, Closed, Total
- Backend: assigned boolean filter + status stage filter
- **Testing: 100% backend (13/13), 100% frontend**

### Engineer Reschedule Fix (Mar 1, 2026)
- Slot-based scheduling with 30-min intervals within working hours
- Backend validation: past date, blocked slots, working hours

### Engineer Visit Workflow (Mar 1, 2026)
- Start Visit (check-in timer), Service Report, Check Out
- Parts Request flow: auto-creates quotation draft for back office
- Resolution types: Fixed/Parts Needed/Escalation with auto stage transition

### Admin Parts Requests Management (Mar 1, 2026)
- Full management page at /admin/parts-requests
- Status filter pills, expandable rows with items/pricing

### Item Master Bulk Upload (Mar 1, 2026)
- CSV upload with duplicate detection, auto-creates categories

### Inventory Management (Mar 1, 2026)
- Inventory tab with stock levels, low stock alerts
- Auto-deduct inventory when engineer uses parts during checkout

### Pending Bills System (Mar 1, 2026)
- Auto-created when engineer uses parts during visit checkout
- Bills aggregated per ticket, billing team email notifications

### Previous Work (Feb 2026)
- Full admin/engineer portals, ticketing V2, workforce, calendars
- Item Master, Quotation system, Security hardening, data isolation

## Architecture
- Frontend: React + Tailwind + Shadcn/UI
- Backend: FastAPI + Motor (MongoDB async)
- Database: MongoDB
- Auth: JWT-based, separate admin/engineer tokens
- Multi-tenancy: organization_id on all collections

## Key Collections
- `tickets_v2`, `visits`, `parts_requests`, `quotations`
- `inventory`, `inventory_transactions`, `pending_bills`
- `item_products`, `item_categories`, `item_bundles`
- `settings` - includes billing_emails, phone numbers for all teams
- `engineers`, `staff_users`

## Key API Endpoints
- POST /api/ticketing/tickets/{id}/send-notification - Send WhatsApp + Email notification
- GET /api/ticketing/tickets?assigned=true/false&status=X - Filtered ticket listing
- GET /api/ticketing/stats - Dashboard stats with by_stage and unassigned counts
- PUT /api/admin/settings - Save team phone numbers and email lists

## Prioritized Backlog

### P0 (Next)
- Form Builder UI (drag-and-drop custom ticket forms)
- Workflow Designer UI (visual editor)
- Email Inbox UI (IMAP/SMTP config)

### P1
- Full CRUD for Teams, SLAs, Priorities, Canned Responses
- Notification Engine (Email/In-app)
- Quotation PDF Generation
- Razorpay Integration
- Customer quotation approval portal

### P2
- CompanySwitcher for platform admins
- Refactor server.py / unify User/Staff models
- Fix ESLint warnings and --legacy-peer-deps

## Credentials
- Admin: ck@motta.in / Charu@123@
- Test Engineer: testeng@test.com / Test@123
- Production domain: aftersales.support
