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
1. **7-Stage Ticket Lifecycle**: New → Assigned → In Progress → Pending Parts → Completed → Closed → Cancelled
2. **Multi-visit tracking** with start/stop timers for each visit
3. **Inventory/parts management** integrated with tickets
4. **Technician portal** for field engineers
5. **Procurement workflow** for parts requests

### Other Modules
- Device/Asset Management
- Company/Client Management
- AMC (Annual Maintenance Contract) Management
- License Tracking
- Knowledge Base
- Platform Admin (Multi-org management)

## What's Been Implemented

### ✅ Service Module - Backend (COMPLETE)
- All data models: `ServiceTicket`, `ServiceVisit`, `TicketPartRequest`, `TicketPartIssue`, `ProblemMaster`, `ItemMaster`, `InventoryLocation`, `StockLedger`, `VendorMaster`, `PurchaseRequest`
- Full CRUD APIs under `/api/admin/service-module/` prefix
- Workflow APIs: assign, start, complete, close, cancel
- Visit APIs with timer support: start-timer, stop-timer, add-action
- Parts request/approval/issue workflow
- Tested with 100% pass rate (iteration_31.json)

### ✅ Service Module - Frontend Phase 1 (COMPLETE - Dec 2025)
- **Service Tickets List Page** (`/admin/service-requests`):
  - Stats cards (Total, Open, Closed, Urgent)
  - Search, status filter, priority filter
  - Create new ticket modal
  - Click-through to detail page
  
- **Ticket Detail Page** (`/admin/service-requests/:ticketId`):
  - Full ticket information display
  - Customer and contact information
  - Device information (if linked)
  - Assignment details
  - Resolution summary (for completed tickets)
  - **Action Buttons**: Assign, Start Work, Pending Parts, Complete, Close, Cancel
  - **Modals**: Assign Technician, Schedule Visit, Request Parts, Add Comment
  - **Tabs**: Details, Visits, Parts, History
  
- **Technician Portal** (`/engineer/*`):
  - Login page with authentication
  - Dashboard showing visits (Scheduled, In Progress, Completed)
  - Visit detail page with:
    - Live timer for in-progress visits
    - Start/Stop timer functionality
    - Add action during visit
    - Request parts from field
    - Complete visit with summary

### ✅ Codebase Consolidation (COMPLETE)
- Old "Support Tickets" module completely removed
- All related frontend pages, backend routes, and models archived
- Navigation cleaned up to show only new unified "Service Tickets"

### ✅ Production Deployment Support
- Guided user through Vultr deployment issues
- Resolved Python venv requirement (PEP 668)
- Provided working deployment command

## Architecture

```
/app
├── backend/
│   ├── models/
│   │   ├── service_ticket.py      # Main ticket model with 7-stage lifecycle
│   │   ├── service_visit.py       # Visit model with timer support
│   │   ├── ticket_parts.py        # Parts request and issue models
│   │   ├── item_master.py         # Inventory items
│   │   ├── inventory.py           # Stock locations and ledger
│   │   ├── vendor.py              # Vendor management
│   │   └── purchase.py            # Purchase requests
│   ├── routes/
│   │   ├── service_tickets_new.py # Ticket CRUD and workflow
│   │   ├── service_visits.py      # Visit management with timers
│   │   ├── ticket_parts.py        # Parts request/issue flow
│   │   ├── item_master.py         # Item CRUD
│   │   ├── inventory_new.py       # Inventory operations
│   │   ├── vendor_master.py       # Vendor CRUD
│   │   └── problem_master.py      # Problem types
│   └── server.py                  # Main FastAPI app
└── frontend/
    └── src/
        └── pages/
            ├── admin/
            │   ├── ServiceRequests.js     # Ticket list page
            │   └── ServiceTicketDetail.js # Ticket detail page (NEW)
            └── engineer/
                ├── TechnicianDashboard.js # New technician dashboard
                └── TechnicianVisitDetail.js # Visit detail with timer
```

## Key API Endpoints

### Service Tickets
- `GET /api/admin/service-module/tickets` - List tickets
- `GET /api/admin/service-module/tickets/{id}` - Get ticket detail
- `POST /api/admin/service-module/tickets` - Create ticket
- `POST /api/admin/service-module/tickets/{id}/assign` - Assign technician
- `POST /api/admin/service-module/tickets/{id}/start` - Start work
- `POST /api/admin/service-module/tickets/{id}/pending-parts` - Mark pending parts
- `POST /api/admin/service-module/tickets/{id}/complete` - Complete ticket
- `POST /api/admin/service-module/tickets/{id}/close` - Close ticket
- `POST /api/admin/service-module/tickets/{id}/cancel` - Cancel ticket
- `POST /api/admin/service-module/tickets/{id}/comments` - Add comment

### Service Visits
- `GET /api/admin/visits` - List visits
- `GET /api/admin/visits/{id}` - Get visit detail
- `GET /api/admin/visits/technician/{id}` - Get technician's visits
- `POST /api/admin/visits` - Create visit
- `POST /api/admin/visits/{id}/start-timer` - Start work timer
- `POST /api/admin/visits/{id}/stop-timer` - Stop timer and complete
- `POST /api/admin/visits/{id}/add-action` - Record action taken

### Parts Management
- `POST /api/admin/ticket-parts/requests` - Request parts
- `POST /api/admin/ticket-parts/requests/{id}/approve` - Approve request
- `POST /api/admin/ticket-parts/issue` - Issue parts

## Prioritized Backlog

### P0 - Immediate
- None (Phase 1 complete and tested)

### P1 - Next Sprint
- **Service Module Phase 2**: Automated vendor communication (Email/WhatsApp), Quotation PDF generation, Invoice generation
- **RMM Integration**: Install and configure Tactical RMM on dedicated server (`64.176.171.108`)
- **Payments**: Finalize Razorpay integration

### P2 - Future
- CompanySwitcher.js component implementation
- AI Ticket Summary feature completion
- Plan Versioning and Audit Logs
- ESLint warnings cleanup across frontend components
- server.py refactoring (move routes to /routes directory)

## Test Reports
- `/app/test_reports/iteration_31.json` - Backend API tests (100% pass)
- `/app/test_reports/iteration_32.json` - Frontend and route removal verification
- `/app/test_reports/iteration_33.json` - Service Module Frontend Phase 1 (100% pass, 28/28 tests)

## Credentials (Preview Environment)
- Admin: `ck@motta.in` / `Charu@123@`
- Portal User: `portal@acme.com` / `Portal@123`

## 3rd Party Integrations
- **OpenAI GPT-4o-mini**: AI features (uses Emergent LLM Key)
- **Razorpay**: Payments (partial)
- **Cloudflare**: DNS and SSL

---
Last Updated: December 2025
Phase 1 Service Module Frontend COMPLETE
