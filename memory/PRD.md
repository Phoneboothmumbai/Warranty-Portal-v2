# Warranty & Asset Tracking Portal - PRD

## Original Problem Statement
Build an enterprise-grade multi-tenant SaaS platform for Warranty & Asset Tracking. The platform serves MSPs (Managed Service Providers) to manage:
- Asset/device tracking with warranty information
- Service ticket management with full lifecycle support
- Inventory and parts management
- Technician/engineer field service operations
- Multi-company (tenant) support

## Core Requirements

### Service Module (Primary Focus)
A comprehensive MSP-grade service ticket system with:
1. **8-Stage Ticket Lifecycle**: New → Pending Acceptance → Assigned → In Progress → Pending Parts → Completed → Closed → Cancelled
2. **Engineer Accept/Decline Workflow**: When a job is assigned, the engineer is notified and must accept or decline
3. **Multi-visit tracking** with start/stop timers for each visit
4. **Inventory/parts management** integrated with tickets
5. **Quotation workflow** for pending parts
6. **Technician portal** for field engineers

### Other Modules
- Device/Asset Management
- Company/Client Management
- AMC (Annual Maintenance Contract) Management
- License Tracking
- Knowledge Base
- Platform Admin (Multi-org management)

## What's Been Implemented

### ✅ Engineer Accept/Decline Workflow (COMPLETE - Dec 2025)
- **Backend Changes**:
  - New `PENDING_ACCEPTANCE` status added to TicketStatus enum
  - New `AssignmentStatus` enum (pending, accepted, declined)
  - Assignment fields added: `assignment_status`, `assignment_accepted_at`, `assignment_declined_at`, `assignment_decline_reason`
  - New engineer endpoints:
    - `GET /api/engineer/my-tickets` - Get all tickets assigned to engineer
    - `GET /api/engineer/tickets/{id}` - Get ticket detail
    - `POST /api/engineer/tickets/{id}/accept` - Accept assignment
    - `POST /api/engineer/tickets/{id}/decline` - Decline with reason
  - Updated assign endpoint to use `pending_acceptance` status
  
- **Frontend Changes**:
  - Completely rewritten `TechnicianDashboard.js` with:
    - Stats row showing New Jobs, Scheduled, In Progress, Completed
    - Tabs: Tickets, Visits, Done
    - "New Job Assignments - Action Required" section with Accept/Decline buttons
    - "My Active Tickets" section for accepted tickets
  - New `EngineerTicketDetail.js` page for viewing ticket details
  - Status configurations updated in ServiceRequests.js and ServiceTicketDetail.js

### ✅ Service Module - Backend (COMPLETE)
- All data models: `ServiceTicket`, `ServiceVisit`, `TicketPartRequest`, `TicketPartIssue`, `ProblemMaster`, `ItemMaster`, `InventoryLocation`, `StockLedger`, `VendorMaster`, `PurchaseRequest`, `Quotation`
- Full CRUD APIs under `/api/admin/service-module/` and `/api/admin/service-tickets/` prefixes
- Workflow APIs: assign, start, complete, close, cancel
- Visit APIs with timer support: start-timer, stop-timer, add-action
- Parts request/approval/issue workflow
- Quotation CRUD and send/approve/reject workflow

### ✅ Service Module - Frontend (COMPLETE)
- **Service Tickets List Page** (`/admin/service-requests`)
- **Ticket Detail Page** (`/admin/service-requests/:ticketId`)
- **Technician Portal** (`/engineer/*`)

### ✅ Codebase Consolidation (COMPLETE)
- Old "Support Tickets" module removed
- Navigation cleaned up
- Production deployment support provided

## Architecture

```
/app
├── backend/
│   ├── models/
│   │   └── service_ticket.py      # Updated with PENDING_ACCEPTANCE status and assignment fields
│   ├── routes/
│   │   ├── service_tickets_new.py # Updated with pending_acceptance workflow
│   │   └── quotations.py          # Quotation management
│   └── server.py                  # Engineer accept/decline endpoints added
├── frontend/
│   └── src/
│       └── pages/
│           ├── admin/
│           │   ├── ServiceRequests.js     # Updated STATUS_CONFIG
│           │   └── ServiceTicketDetail.js # Updated STATUS_CONFIG
│           └── engineer/
│               ├── TechnicianDashboard.js    # Rewritten with accept/decline UI
│               └── EngineerTicketDetail.js   # New ticket detail page
└── ...
```

## Key API Endpoints

### Engineer Portal
- `POST /api/engineer/auth/login` - Engineer login (supports staff_users)
- `GET /api/engineer/my-tickets` - Get tickets assigned to engineer (grouped by status)
- `GET /api/engineer/tickets/{id}` - Get ticket detail
- `POST /api/engineer/tickets/{id}/accept` - Accept assignment
- `POST /api/engineer/tickets/{id}/decline` - Decline with reason
- `GET /api/engineer/my-visits` - Get visits
- `POST /api/engineer/service-visits/{id}/start` - Start visit
- `POST /api/engineer/service-visits/{id}/complete` - Complete visit

### Admin Service Tickets
- `GET /api/admin/service-tickets` - List tickets
- `POST /api/admin/service-tickets` - Create ticket
- `POST /api/admin/service-tickets/{id}/assign` - Assign to technician (creates pending_acceptance)
- `POST /api/admin/service-tickets/{id}/start` - Start work
- `POST /api/admin/service-tickets/{id}/pending-parts` - Mark pending parts
- `POST /api/admin/service-tickets/{id}/complete` - Complete ticket
- `POST /api/admin/service-tickets/{id}/close` - Close ticket

### Quotations
- `GET /api/admin/quotations` - List quotations
- `POST /api/admin/quotations` - Create quotation for ticket
- `POST /api/admin/quotations/{id}/send` - Send to customer
- `POST /api/admin/quotations/{id}/approve` - Approve/reject quotation

## Ticket Status Flow

```
NEW → (admin assigns) → PENDING_ACCEPTANCE → (engineer accepts) → ASSIGNED → 
IN_PROGRESS → (parts needed) → PENDING_PARTS → (quotation approved) → 
IN_PROGRESS → COMPLETED → CLOSED

PENDING_ACCEPTANCE → (engineer declines) → NEW (ready for reassignment)
```

## Prioritized Backlog

### P0 - Immediate
- None (Accept/Decline workflow complete and tested)

### P1 - Next Sprint
- **Quotation PDF Generation**: Generate and attach PDF when sending quotation
- **RMM Integration**: Tactical RMM on dedicated server
- **Payments**: Finalize Razorpay integration
- **Email Notifications**: Send notifications for assignment, quotation events

### P2 - Future
- CompanySwitcher.js component implementation
- AI Ticket Summary feature completion
- Plan Versioning and Audit Logs
- ESLint warnings cleanup across frontend components
- server.py refactoring (move routes to /routes directory)
- Backend model unification (staff_users vs organization_members)
- Frontend dependency conflicts resolution

## Test Reports
- `/app/test_reports/iteration_31.json` - Backend API tests (100% pass)
- `/app/test_reports/iteration_32.json` - Frontend and route removal verification
- `/app/test_reports/iteration_33.json` - Service Module Frontend Phase 1 (100% pass)
- `/app/test_reports/iteration_34.json` - Engineer Accept/Decline Workflow (100% pass)

## Credentials (Preview Environment)
- Admin: `ck@motta.in` / `Charu@123@`
- Engineer: `john.tech@test.com` / `Tech@123`
- Portal User: `portal@acme.com` / `Portal@123`

## 3rd Party Integrations
- **OpenAI GPT-4o-mini**: AI features (uses Emergent LLM Key)
- **Razorpay**: Payments (partial)
- **Cloudflare**: DNS and SSL

---
Last Updated: December 2025
Engineer Accept/Decline Workflow COMPLETE
