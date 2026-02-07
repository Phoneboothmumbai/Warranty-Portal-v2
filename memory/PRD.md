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
5. **Quotation workflow** for pending parts (auto-generated)
6. **Technician portal** for field engineers

## What's Been Implemented

### ✅ Engineer Portal - Complete Implementation (Dec 2025)

**1. Ticket Dashboard**
- View all assigned tickets (New, Assigned, In Progress, Pending Parts)
- Clear status indicators and priority levels
- Filter tickets by date, status, priority

**2. Ticket Details View**
- Full ticket information: issue description, customer details, location, asset info
- View previous visit history and notes
- SLA timeline visibility

**3. Ticket Acknowledgement**
- Accept or decline assigned tickets
- Status auto-updates to Assigned or returns to New

**4. Visit Management**
- Start Visit / End Visit tracking
- Auto-capture visit timestamps
- Live timer during visits
- Visit history stored per ticket

**5. Issue Diagnosis & Findings**
- Engineer can record problem identified, root cause, and observations
- Photo/document attachment capability (base64 storage)

**6. Resolution Actions**
- Mark ticket as Resolved or Pending for Parts
- Mandatory remarks before status change

**7. Parts Requirement Flow**
- Select required parts from inventory OR add manually
- Submit ticket with Pending for Parts status
- **AUTO-GENERATES draft quotation** for admin review

**8. Revisit Handling**
- Ticket reassigned after customer approval
- Revisit clearly marked in ticket

**9. Ticket Closure**
- Final findings and solution details required
- Validates no incomplete visits
- Cannot close when pending parts

### Backend Endpoints (New)
```
GET  /api/engineer/dashboard/stats      - Dashboard statistics
GET  /api/engineer/tickets              - Ticket list with filtering
GET  /api/engineer/tickets/{id}         - Ticket detail with visits, parts, quotation
POST /api/engineer/tickets/{id}/accept  - Accept assignment
POST /api/engineer/tickets/{id}/decline - Decline with reason
POST /api/engineer/tickets/{id}/close   - Close ticket
GET  /api/engineer/visits               - Visit list
GET  /api/engineer/visits/{id}          - Visit detail with history
POST /api/engineer/visits/{id}/start    - Start visit
POST /api/engineer/visits/{id}/end      - End visit
POST /api/engineer/visits/{id}/diagnosis - Save diagnosis
POST /api/engineer/visits/{id}/resolve  - Resolve visit
POST /api/engineer/visits/{id}/pending-parts - Mark pending + create quotation
POST /api/engineer/visits/{id}/photos   - Upload photo
GET  /api/engineer/inventory/items      - Search inventory
```

### Frontend Components (Updated)
- `TechnicianDashboard.js` - Complete rewrite with stats, tabs, accept/decline UI
- `TechnicianVisitDetail.js` - Full workflow with timer, diagnosis, resolution, parts modals
- `EngineerTicketDetail.js` - Ticket details with accept/decline, SLA info

## Architecture

```
/app
├── backend/
│   ├── models/
│   │   └── service_ticket.py      # PENDING_ACCEPTANCE status, assignment fields
│   ├── routes/
│   │   ├── engineer_portal.py     # NEW - Comprehensive engineer API
│   │   ├── service_tickets_new.py # Ticket workflow
│   │   └── quotations.py          # Quotation management
│   └── server.py                  # Legacy engineer endpoints
├── frontend/
│   └── src/
│       └── pages/
│           └── engineer/
│               ├── TechnicianDashboard.js    # Complete dashboard
│               ├── TechnicianVisitDetail.js  # Full visit workflow
│               └── EngineerTicketDetail.js   # Ticket detail
└── ...
```

## Ticket Status Flow

```
NEW → (admin assigns) → PENDING_ACCEPTANCE → (engineer accepts) → ASSIGNED → 
IN_PROGRESS → (parts needed) → PENDING_PARTS → (quotation approved) → 
IN_PROGRESS → COMPLETED → CLOSED

PENDING_ACCEPTANCE → (engineer declines) → NEW (ready for reassignment)
```

## Prioritized Backlog

### P0 - Immediate
- None (Engineer Portal complete and tested)

### P1 - Next Sprint
- **Admin Quotation Management UI** - Send/approve quotations
- **Email Notifications** - Assignment, quotation events
- **Quotation PDF Generation**
- **RMM Integration** - Tactical RMM

### P2 - Future
- Razorpay payments finalization
- CompanySwitcher.js implementation
- AI Ticket Summary completion
- Backend model unification (staff_users vs organization_members)
- server.py refactoring (move legacy routes)

## Test Reports
- `/app/test_reports/iteration_34.json` - Accept/Decline workflow (100% pass)
- `/app/test_reports/iteration_35.json` - Engineer Portal comprehensive (95% pass)

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
Engineer Portal - All 9 Features COMPLETE
