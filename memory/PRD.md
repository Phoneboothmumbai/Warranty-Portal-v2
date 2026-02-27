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
- Enhanced ticket creation: Company → Site → Employee → Device with inline "Add New"

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
- Multi-step: Company → Site → Employee → Device cascading flow
- "Add New Site" inline form saves to DB, syncs across portal
- "Add New Employee" inline form saves to DB, syncs across portal
- Employee auto-fills contact fields
- Device universal search + manual entry toggle
- Custom form fields load dynamically per help topic

### Security Hardening (Feb 26, 2026)
- scope_query() hard-fails when org_id is None
- masters.py, companies.py, amc_requests.py, amc_onboarding.py, qr_service.py all scoped
- All bulk import endpoints scoped by organization_id

## Architecture
- Frontend: React + Tailwind + Shadcn/UI
- Backend: FastAPI + Motor (MongoDB async)
- Database: MongoDB
- Auth: JWT-based, separate admin/engineer tokens
- Multi-tenancy: organization_id on all collections, hard-fail scope enforcement

## Prioritized Backlog

### P0 (Next)
- Form Builder UI (drag-and-drop)
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
- Production domain: aftersales.support
