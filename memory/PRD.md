# Warranty & Asset Tracking Portal - PRD

## Original Problem Statement
Build an enterprise-grade Warranty & Asset Tracking Portal with a highly configurable, master-driven, multi-workflow ticketing system. Features include admin portal, engineer portal, job acceptance workflows, calendars, and ticketing configuration.

## Core Requirements
- Role-based access: Admin vs Engineer portals
- Master-driven ticketing: Help Topics, Forms, Workflows, Teams, Roles, SLA, Canned Responses
- Job acceptance/decline/reschedule workflow for technicians
- Central calendar (admin) and personal calendar (engineer)
- Workforce management with working hours, holidays, salary

## What's Been Implemented

### Completed (Feb 2026)
- Full admin portal with dashboard, company/site/device management
- Full engineer portal with dashboard, calendar, ticket detail view
- Ticketing V2 system with seed data auto-provisioning
- Job acceptance/decline/reschedule workflow (both admin and engineer auth)
- Central calendar for admins, personal calendar for engineers
- Workforce overview for admins
- Notification system for declined jobs
- Smart scheduling with 30-min slots and 1-hour buffer
- Auto-deduplication of seed data on startup
- Delete functionality for all master data items
- Engineer ticket detail page showing full customer, device, repair history

### Bug Fixes (Feb 26, 2026)
- Fixed: Technician couldn't view job details → Created EngineerTicketDetail page
- Fixed: Calendar not syncing after job acceptance → Backend now creates schedule records on accept
- Fixed: Duplicate seed data on production → Auto-deduplicate on startup
- Fixed: No delete buttons on system items → Removed is_system restriction

## Architecture
- Frontend: React + Tailwind + Shadcn/UI
- Backend: FastAPI + Motor (MongoDB async)
- Database: MongoDB
- Auth: JWT-based, separate admin/engineer tokens

## Prioritized Backlog

### P0 (Next)
- Enhanced Ticket Creation Flow (Company → Site → Employee → Device with "Add New")
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

## 3rd Party Integrations
- OpenAI GPT-4o-mini (Emergent LLM Key)
- Razorpay (partial)
- WatchTower (Tactical RMM)
- Email (IMAP/SMTP - in progress)

## Credentials
- Admin: ck@motta.in / Charu@123@
- Production domain: aftersales.support
