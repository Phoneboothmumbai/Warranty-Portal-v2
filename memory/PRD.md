# Warranty & Asset Tracking Portal - PRD

## Original Problem Statement
Build an enterprise-grade Warranty & Asset Tracking Portal with a highly configurable, master-driven, multi-workflow ticketing system with strict multi-tenant data isolation.

## Core Requirements
- Role-based access: Admin vs Engineer portals
- Master-driven ticketing: Help Topics, Forms, Workflows, Teams, Roles, SLA, Canned Responses
- Job acceptance/decline/reschedule workflow for technicians
- Central calendar (admin) and personal calendar (engineer)
- Workforce management with working hours, holidays, salary
- **Strict multi-tenant data isolation** - all data scoped by organization_id
- Enhanced ticket creation: Company > Site > Employee > Device with inline "Add New"

## What's Been Implemented

### Completed (Feb 2026)
- Full admin portal with dashboard, company/site/device management
- Full engineer portal with dashboard, calendar, ticket detail view
- Ticketing V2 system with seed data auto-provisioning + auto-deduplication
- Job acceptance/decline/reschedule workflow (both admin and engineer auth)
- Central calendar for admins, personal calendar for engineers
- Workforce overview for admins
- Notification system for declined jobs
- Smart scheduling with 30-min slots and 1-hour buffer
- Delete functionality for all master data items
- Engineer ticket detail page showing full customer, device, repair history
- Admin reassignment UI for declined tickets

### Engineer Reschedule Fix - Slot-Based Scheduling (Mar 1, 2026)
- Replaced broken datetime-local input with date picker + slot grid
- New backend endpoint: `GET /api/engineer/available-slots?date=YYYY-MM-DD`
- 30-minute time slots within working hours, blocks past times/booked slots
- Backend validation: past date, 30-min intervals, working hours, slot availability
- Testing: 95% backend (18/19), 100% frontend

### Tenant Name Hardcoding (Mar 1, 2026)
- Hardcoded "aftersales.support" brand name across all portals
- Fixed cross-tenant name leak in BrandingContext.js

### Engineer Visit Workflow - Full Lifecycle (Mar 1, 2026)
- **Phase 1: Calendar Floating Popup** - Event click opens centered modal with full ticket/company/device/history details
- **Phase 2: Visit Workflow** - Start Visit (check-in timer), Service Report (Problem/Diagnosis/Solution/Resolution Type), Check Out
- **Phase 3: Parts Request Flow** - Engineer requests parts → auto-creates quotation draft → admin reviews/sends → customer approves
- New backend file: `/app/backend/routes/engineer_visits.py`
- Endpoints: `POST /api/engineer/visit/start`, `PUT /api/engineer/visit/{id}/update`, `POST /api/engineer/visit/{id}/request-parts`, `POST /api/engineer/visit/{id}/checkout`, `GET /api/engineer/visit/history/{ticket_id}`, `GET /api/admin/parts-requests`, `PUT /api/admin/parts-requests/{id}/status`
- Resolution types: Fixed → "Work Done", Parts Needed → "Awaiting Parts", Escalation → "Escalated"
- **Testing: 100% backend (15/15), 100% frontend - ALL PASS**

### Previous Work
- Homepage redesign with corporate aesthetic
- Production data isolation fix with migration script
- Email uniqueness constraints (composite indexes)
- Item Master module (Categories, Products, Bundles)
- Quotation system (CRUD, GST calc, company approve/reject)
- Security hardening (scope_query, bulk imports)
- Enhanced ticket creation (multi-step cascading flow)

## Architecture
- Frontend: React + Tailwind + Shadcn/UI
- Backend: FastAPI + Motor (MongoDB async)
- Database: MongoDB
- Auth: JWT-based, separate admin/engineer tokens
- Multi-tenancy: organization_id on all collections

## Key Collections
- `tickets_v2` - Main ticket data
- `visits` - Engineer field visit records (NEW)
- `parts_requests` - Parts requested by engineers (NEW)
- `quotations` - Auto-created from parts requests
- `ticket_schedules` - Scheduling data
- `engineers` - Engineer profiles with working hours

## Prioritized Backlog

### P0 (Next)
- Admin UI for Parts Requests management (view, update status, link to quotation)
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
- Backend unit tests with pytest

## Credentials
- Admin: ck@motta.in / Charu@123@
- Test Engineer: testeng@test.com / Test@123
- Production domain: aftersales.support
