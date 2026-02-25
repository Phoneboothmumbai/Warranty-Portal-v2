# Warranty & Asset Tracking Portal - PRD

## Original Problem Statement
Enterprise-grade Warranty & Asset Tracking Portal with a fully configurable, master-driven, multi-workflow ticketing system inspired by osTicket.

## Core Requirements
1. **Help Topic Driven Architecture**: System logic controlled by Help Topics - each defines which Form, Workflow, Department, and SLA to use
2. **Fully Configurable Masters**: All components customizable via admin UI (Help Topics, Forms, Workflows, Stages, Roles, Teams, SLAs, Priorities, Canned Responses, Notification Templates)
3. **Multi-Role Workflows**: Complex workflows spanning multiple teams with role-specific dashboards
4. **Pre-built Defaults**: Pre-loaded with comprehensive default configurations
5. **Clean Slate**: Complete rebuild of ticketing system (V2)

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn UI (port 3000, craco build)
- **Backend**: FastAPI + MongoDB (port 8001)
- **Auth**: JWT-based admin auth
- **Database**: MongoDB via MONGO_URL, DB_NAME from .env

## V2 Ticketing System Collections
- `ticket_help_topics` - Help topic configurations
- `ticket_forms` - Custom form definitions with fields
- `ticket_workflows` - Workflow stages and transitions
- `ticket_teams` - Team configurations
- `ticket_roles` - Role permissions
- `ticket_sla_policies` - SLA policy definitions
- `ticket_priorities` - Priority levels
- `ticket_canned_responses` - Pre-built response templates
- `ticket_notification_templates` - Notification templates
- `ticket_task_types` - Task type definitions
- `ticket_business_hours` - Business hours config
- `tickets_v2` - Core ticket documents
- `ticket_tasks` - Individual task documents

## What's Been Implemented

### V2 Ticketing System (Feb 25, 2026)
- **Backend Models**: Complete Pydantic models for all entities
- **Seed Data**: 10 help topics, 10 forms, 7 workflows, 5 teams, 5 roles, 4 SLA policies, 4 priorities, 9 canned responses, 6 notification templates
- **Backend API Routes** (`/app/backend/routes/ticketing_v2.py`):
  - CRUD for all master data (help topics, forms, workflows, teams, roles, SLAs, priorities, canned responses)
  - Ticket lifecycle: create, list, get detail, comment, transition, assign, stats
  - Task management: list, get, create, complete
  - Seed endpoint for initial data population
- **Frontend Pages**:
  - Tickets List (`ServiceRequestsV2.js`) - stats cards, search, filters, pagination, create modal
  - Ticket Detail (`ServiceTicketDetailV2.js`) - workflow progress, timeline, comments, assignment, transitions
  - Ticketing Setup (`TicketingConfigV2.js`) - 8-tab config page for all masters
  - Company Tickets (`CompanyTicketsV2.js`, `CompanyTicketDetailV2.js`) - customer portal views
- **Old System Cleanup**: Deleted all V1 ticketing routes, models, and frontend pages

### Pre-existing Modules (Working)
- Asset Management (devices, inventory)
- Company Management (CRUD, contacts)
- AMC/Warranty tracking
- Dashboard with analytics
- Knowledge Base
- User/Organization management
- WatchTower RMM integration
- AI Chat (GPT-4o-mini via Emergent key)

### Technician Management & Smart Scheduling (Feb 25, 2026)
- **Technicians Tab**: New tab in Ticketing Setup for managing technicians (CRUD)
- **Working Hours**: Per-day schedule config (Mon-Sun, start/end times, working day toggle)
- **Holidays**: Date-based holiday management per technician
- **Salary**: Monthly salary field
- **Smart Time Slots**: `GET /api/ticketing/engineers/{id}/available-slots?date=YYYY-MM-DD`
  - 30-minute interval time slot generation within working hours
  - Blocks slots for existing bookings + 1-hour buffer
  - Respects holidays and non-working days
- **Schedule Visit Modal**: Revamped with visual 30-min time slot grid, blocked slots shown in red

### Central Calendar & Engineer Portal (Feb 25, 2026)
- **Admin Central Calendar** (`/admin/calendar`): Month/Week/Day views with all technician schedules
- **Sidebar panels**: Events, Org Holidays (CRUD), Standard Working Hours, Emergency Working Hours (CRUD)
- **Technician filter**: Filter calendar by specific engineer with color-coded legend
- **Engineer Portal**: `/engineer/dashboard` + `/engineer/calendar` with personal schedule view
- **Backend APIs**: `/api/calendar/holidays`, `/api/calendar/standard-hours`, `/api/calendar/emergency-hours`, `/api/calendar/events`, `/api/engineer/calendar/my-schedule`
- **New DB collections**: `org_holidays`, `org_standard_hours`, `org_emergency_hours`

## Testing Status
- V2 Backend: 17/17 tests passed (100%)
- Technicians & Slots: 12/12 backend tests passed (100%), Frontend 100% verified
- Test reports: `/app/test_reports/iteration_41.json`, `/app/test_reports/iteration_42.json`

## Pending/Backlog

### P0 - High Priority
- Email Inbox Integration (backend API exists, frontend UI pending)
- Build Form Builder UI (drag/drop field editor in Ticketing Setup)
- Build Workflow Designer (visual stage/transition editor)
- Role-Based Dashboards (Technician, Back Office views)

### P1 - Medium Priority
- Notification Engine (email/in-app for ticket events)
- Quotation PDF Generation
- Full CRUD for all master entities in admin UI
- Razorpay finalization

### P2 - Low Priority
- CompanySwitcher for platform admins
- Refactor server.py (break into modules)
- ESLint warnings cleanup
- Fix `--legacy-peer-deps` issue
- Unify User/Staff models

## Credentials
- Admin: ck@motta.in / Charu@123@
- Production: Vultr server with warranty-backend.service

## Key Files
- `/app/backend/routes/ticketing_v2.py` - V2 API routes
- `/app/backend/models/ticketing_v2.py` - V2 data models
- `/app/backend/models/ticketing_v2_seed.py` - Seed data
- `/app/frontend/src/pages/admin/ServiceRequestsV2.js` - Tickets list
- `/app/frontend/src/pages/admin/ServiceTicketDetailV2.js` - Ticket detail
- `/app/frontend/src/pages/admin/TicketingConfigV2.js` - Config page
