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

### Security Hardening (Feb 26, 2026)
- `scope_query()` now hard-fails when org_id is None
- `masters.py` fully rewritten with org_id on all operations
- `companies.py` changed from soft to hard org_id enforcement
- `amc_requests.py` all admin endpoints scoped
- `amc_onboarding.py` all admin endpoints scoped
- `qr_service.py` bulk QR generation scoped
- All bulk import endpoints scoped

### Bug Fixes (Feb 26, 2026)
- Fixed: Technician couldn't view job details
- Fixed: Calendar not syncing after job acceptance
- Fixed: Duplicate seed data on production
- Fixed: No delete buttons on system items

## Architecture
- Frontend: React + Tailwind + Shadcn/UI
- Backend: FastAPI + Motor (MongoDB async)
- Database: MongoDB
- Auth: JWT-based, separate admin/engineer tokens
- Multi-tenancy: organization_id on all collections, hard-fail scope enforcement

## Prioritized Backlog

### P0 (Next)
- Enhanced Ticket Creation Flow (Company -> Site -> Employee -> Device with "Add New")
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
