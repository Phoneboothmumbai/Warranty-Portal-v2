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

### Enhanced Ticket Creation (Feb 27, 2026)
- Multi-step: Company > Site > Employee > Device cascading flow
- "Add New Site" inline form saves to DB, syncs across portal
- "Add New Employee" inline form saves to DB, syncs across portal
- Employee auto-fills contact fields
- Device universal search + manual entry toggle
- Custom form fields load dynamically per help topic

### Security Hardening (Feb 26, 2026)
- scope_query() hard-fails when org_id is None
- masters.py, companies.py, amc_requests.py, amc_onboarding.py, qr_service.py all scoped
- All bulk import endpoints scoped by organization_id

### Item Master Module (Feb 27, 2026)
- Categories, Products, Product Bundles CRUD
- Quotation Integration with bundle recommendations
- Frontend: 3-tab interface at /admin/item-master
- Testing: 25/25 backend tests passed

### Quotation System (Feb 27, 2026)
- Full CRUD at /api/admin/quotations/*
- Per-line GST, auto-calculated totals
- Company endpoints for list/approve/reject
- Testing: 17/17 backend tests passed

### Complete Tenant Isolation (Feb 27, 2026)
- Every admin endpoint scoped by organization_id
- Dashboard stats strictly tenant-scoped
- Data migration backfilled 191 records

### Composite Email Uniqueness (Mar 1, 2026)
- UNIQUE(organization_id, email) across companies, users, engineers, staff_users
- DB-level composite unique indexes

### Homepage Redesign (Feb 28, 2026)
- Corporate hero, animated KPIs, bento grid features, testimonial section
- Updated branding to "aftersales.support"

### Engineer Reschedule Fix - Slot-Based Scheduling (Mar 1, 2026)
- **Completely rebuilt** the reschedule UI in PendingCard component
- Replaced broken datetime-local input with date picker + slot grid
- New backend endpoint: `GET /api/engineer/available-slots?date=YYYY-MM-DD`
- Shows 30-minute time slots within engineer's working hours
- Blocks past times, holidays, non-working days
- Blocks already-booked slots with 1-hour buffer (greyed out + line-through)
- Available slots clickable with blue highlight on selection
- Backend validation: past date, 30-min intervals, working hours, slot availability
- **Testing: 95% backend (18/19), 100% frontend - ALL PASS**

## Architecture
- Frontend: React + Tailwind + Shadcn/UI
- Backend: FastAPI + Motor (MongoDB async)
- Database: MongoDB
- Auth: JWT-based, separate admin/engineer tokens
- Multi-tenancy: organization_id on all collections

## Prioritized Backlog

### P0 (Next)
- Integrate Item Master into full Quotation/CRM flow
- Form Builder UI (drag-and-drop custom ticket forms)
- Workflow Designer UI (visual editor)
- Email Inbox UI (IMAP/SMTP config)

### P1
- Full CRUD for Teams, SLAs, Priorities, Canned Responses
- Notification Engine (Email/In-app)
- Quotation PDF Generation
- Razorpay Integration

### P2
- CompanySwitcher for platform admins
- Refactor server.py / unify User/Staff models
- Fix ESLint warnings and --legacy-peer-deps
- Backend unit tests with pytest

## Credentials
- Admin: ck@motta.in / Charu@123@
- Test Engineer: testeng@test.com / Test@123
- Production domain: aftersales.support
