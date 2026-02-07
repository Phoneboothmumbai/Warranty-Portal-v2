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
5. **Quotation workflow** for pending parts (auto-generated, admin managed, customer approval)
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

### ✅ Admin Quotation Management UI - NEW (Feb 2026)

**Features Implemented:**
- Quotation list view with summary cards (Draft, Awaiting Response, Approved, Total)
- Detailed quotation view modal with items, prices, totals
- Edit quotation modal to add/remove/modify line items
- Send quotation functionality (changes status from draft → sent)
- Record customer response (approve/reject) with notes
- Navigation link added to admin sidebar

**API Endpoints:**
- `GET /api/admin/quotations` - List quotations with filtering
- `GET /api/admin/quotations/{id}` - Get quotation detail
- `PUT /api/admin/quotations/{id}` - Update quotation items/prices
- `POST /api/admin/quotations/{id}/send` - Send to customer
- `POST /api/admin/quotations/{id}/approve` - Record approval/rejection

### ✅ Customer Portal Quotations - NEW (Feb 2026)

**Features Implemented:**
- Company users can view quotations sent to them
- Approve or reject quotations with notes
- Summary cards showing pending/approved counts
- Alert banner for pending quotations
- Draft quotations are hidden from company users

**API Endpoints:**
- `GET /api/company/quotations` - List quotations for company
- `GET /api/company/quotations/{id}` - Get quotation detail (no internal notes)
- `POST /api/company/quotations/{id}/respond` - Approve/reject quotation

### ✅ Strict Ticket Workflow Enforcement - NEW (Feb 2026)

**Workflow Rules Implemented:**
```
1️⃣ Ticket Created (NEW)
2️⃣ Technician Assigned (PENDING_ACCEPTANCE)
3️⃣ Technician Accepts (ASSIGNED)
4️⃣ Visit & Diagnosis (IN_PROGRESS)
5️⃣ Parts Required (PENDING_PARTS) → Quotation workflow
6️⃣ Work Completed (COMPLETED)
7️⃣ Ticket Closed (CLOSED)
```

**Validation Rules:**
- Can only assign: `new`, `pending_acceptance` tickets
- Cannot reassign: `assigned`, `in_progress`, `pending_parts`, `completed`, `closed` tickets
- Clear error messages for each blocked scenario
- Workflow progress indicator on ticket detail page

**Error Messages:**
- assigned: "Engineer has already accepted this ticket. Cannot reassign - work must proceed."
- in_progress: "Work is in progress. Cannot reassign ticket at this stage."
- pending_parts: "Ticket is pending parts. Complete the quotation workflow before any changes."

### Ticket Detail Enhancements - NEW (Feb 2026)

- **Quotation Alert Banner**: Shows quotation status when ticket is pending_parts
- **Workflow Progress Indicator**: Visual 7-step progress bar
- **View Quotation Button**: Quick access to quotation from ticket

## Architecture

```
/app
├── backend/
│   ├── models/
│   │   └── service_ticket.py      # PENDING_ACCEPTANCE status, assignment fields
│   ├── routes/
│   │   ├── engineer_portal.py     # Comprehensive engineer API
│   │   ├── service_tickets_new.py # Ticket workflow with strict validation
│   │   └── quotations.py          # Admin + Company quotation APIs
│   └── server.py                  # Router registrations
├── frontend/
│   └── src/
│       └── pages/
│           ├── admin/
│           │   ├── Quotations.js           # Admin quotation management
│           │   └── ServiceTicketDetail.js  # Workflow progress, quotation banner
│           ├── company/
│           │   └── CompanyQuotations.js    # Customer quotation portal
│           └── engineer/
│               ├── TechnicianDashboard.js    # Engineer dashboard
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

### P0 - COMPLETE
- ✅ Admin Quotation Management UI
- ✅ Customer Portal Quotations
- ✅ Strict Ticket Workflow Enforcement
- ✅ Workflow Progress Indicator

### P1 - Next Sprint
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
- `/app/test_reports/iteration_36.json` - Quotation & Workflow tests (100% pass)

## Test Files
- `/app/backend/tests/test_quotation_workflow.py` - Quotation and workflow validation tests

## Credentials (Preview Environment)
- Admin: `ck@motta.in` / `Charu@123@`
- Engineer: `john.tech@test.com` / `Tech@123`
- Company: `testuser@testcompany.com` / `Test@123`

## 3rd Party Integrations
- **OpenAI GPT-4o-mini**: AI features (uses Emergent LLM Key)
- **Razorpay**: Payments (partial)
- **Cloudflare**: DNS and SSL

---
Last Updated: February 2026
- Admin Quotation Management UI - COMPLETE
- Customer Portal Quotations - COMPLETE  
- Strict Workflow Enforcement - COMPLETE
