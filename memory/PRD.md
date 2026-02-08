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

### ✅ Comprehensive Device Dashboard - NEW (Feb 2026)

**6-Tab Professional Dashboard:**

1. **Overview Tab**
   - Quick Stats Row: Total Tickets, Open Tickets, Avg TAT, Total Spend, Warranty Days, Parts Replaced
   - Device Information Card
   - Warranty Status Card with visual indicator
   - Financial Summary Card
   - Recent Activity timeline

2. **Tickets Tab**
   - Ticket statistics (Total, Open, Resolved, Avg Resolution Time)
   - Complete ticket list with status badges
   - Direct link to create new ticket

3. **Lifecycle Tab**
   - Visual timeline of device history
   - Color-coded events (Device Registered, Warranty, AMC, Tickets, Parts)
   - Chronological order with dates and costs

4. **AMC Tab** (when device enrolled)
   - AMC Active status card
   - Days Remaining progress bar
   - PM Compliance circular gauge (% of scheduled visits completed)
   - Contract Details (Name, Type, Schedule, Value)
   - Coverage Includes list
   - Entitlements display

5. **RMM Tab** (WatchTower)
   - WatchTower agent status display
   - Real-time monitoring metrics (when agent installed)
   - Download Agent inline button for self-service installation
   - Icons for CPU Usage, Memory, Disk Space, Network

### ✅ WatchTower Self-Service Agent Download - NEW (Feb 2026)

**Complete multi-portal integration for tenant self-service:**

1. **Company Portal - Dashboard**
   - WatchTower Monitoring card showing agent stats (Total, Online, Offline)
   - "Download Agent for New Device" button
   - Full download dialog with OS selection and site assignment

2. **Company Portal - Devices Page**
   - "Download WatchTower Agent" button in header
   - Same download dialog as dashboard

3. **Company Portal - Device Dashboard (RMM Tab)**
   - Inline download option for individual devices
   - Installation instructions embedded

4. **Admin Portal - WatchTower Integration Page**
   - Agent list from WatchTower
   - "Download Agent for Companies" section
   - Per-company download link generation
   - Shows provisioning status (provisioned/not provisioned in WatchTower)

**Backend Implementation:**
- `/api/watchtower/company/agent-status` - Get WatchTower status for company
- `/api/watchtower/company/sites-for-agent` - Get sites for agent assignment
- `/api/watchtower/company/agent-download` - Generate download link for company (self-service)
- `/api/watchtower/agent-download/{company_id}` - Admin generates download for any company
- Auto-provisioning: Creates WatchTower Client/Site if not exists
- Graceful error handling with manual download fallback when API fails

6. **Details Tab**
   - Configuration (Processor, RAM, Storage, OS)
   - Assignment (User, Department, Location)
   - Purchase Information (Date, Price, Vendor, Invoice)
   - Network Information (IP, MAC, Hostname)
   - Parts Replaced history

**API Endpoint:**
- `GET /api/company/devices/:id/analytics` - Returns comprehensive device analytics

### ✅ Company Service Tickets - NEW (Feb 2026)

**Features:**
- Service Tickets list page at `/company/tickets`
- Ticket Detail page at `/company/tickets/:id`
- Create ticket from company portal
- Create ticket from device dashboard (device pre-selected)
- Filter by status, search functionality
- Stats cards (Open, Pending Parts, Completed, Total)
- Workflow progress indicator on detail page

**API Endpoints:**
- `GET /api/company/service-tickets` - List tickets with filtering
- `GET /api/company/service-tickets/:id` - Get ticket detail
- `POST /api/company/service-tickets` - Create new ticket

### ✅ Previous Implementations

**Admin Quotation Management UI** (`/admin/quotations`)
- List, view, edit quotations with full CRUD
- Send quotation to customer functionality
- Navigation link in admin sidebar

**Strict Ticket Workflow Enforcement**
- Can only assign `new` or `pending_acceptance` tickets
- Cannot reassign once engineer accepted
- Clear error messages for each blocked scenario
- Workflow progress indicator on ticket detail page

**Customer Portal Quotations** (`/company/quotations`)
- Company users can view sent quotations
- Approve/reject quotations with notes

**Engineer Portal** - Complete 9-feature implementation

## Architecture

```
/app
├── backend/
│   ├── routes/
│   │   ├── engineer_portal.py     # Engineer API
│   │   ├── service_tickets_new.py # Ticket workflow
│   │   └── quotations.py          # Quotations + Company tickets API
│   └── server.py                  # Device analytics API, router registrations
├── frontend/
│   └── src/
│       └── pages/
│           ├── admin/
│           │   ├── Quotations.js
│           │   └── ServiceTicketDetail.js
│           ├── company/
│           │   ├── DeviceDashboard.js      # NEW: Comprehensive device dashboard
│           │   ├── CompanyTickets.js       # NEW: Service tickets list
│           │   ├── CompanyTicketDetail.js  # NEW: Ticket detail
│           │   └── CompanyQuotations.js
│           └── engineer/
│               ├── TechnicianDashboard.js
│               └── TechnicianVisitDetail.js
└── ...
```

## Prioritized Backlog

### P0 - COMPLETE
- ✅ Device Dashboard with analytics, lifecycle, AMC metrics
- ✅ Company Service Tickets functionality
- ✅ Admin Quotation Management UI
- ✅ Customer Portal Quotations
- ✅ Strict Ticket Workflow Enforcement
- ✅ Engineer Portal (all 9 features)
- ✅ **Critical Bug Fixes (Feb 2026)** - See "Recent Bug Fixes" section below

### P1 - Next Sprint
- **Email Notifications** - Assignment, quotation events
- **Quotation PDF Generation**
- **Admin Device Dashboard** - Same dashboard view for admin panel
- **WatchTower Shared Deployment Links** - Admin creates a deployment link in WatchTower and stores it for seamless tenant downloads

### P2 - Future
- Razorpay payments finalization
- AI Ticket Summary completion
- Backend model unification
- server.py refactoring

## Recent Bug Fixes (Feb 9, 2026)

### ✅ Bug 1: Engineer Accept/Decline Workflow
**Issue:** Tickets were assigned but engineers couldn't accept/decline them via API.
**Fix:** Added two new endpoints in `/app/backend/routes/engineer_portal.py`:
- `POST /api/engineer/tickets/{id}/accept` - Engineer accepts ticket, moves to 'assigned' status
- `POST /api/engineer/tickets/{id}/decline` - Engineer declines with reason, moves back to 'new' status

### ✅ Bug 2: Multiple Visits Prevention
**Issue:** System allowed scheduling multiple visits for a single ticket simultaneously.
**Fix:** Updated `create_visit()` in `/app/backend/routes/service_visits.py` to check for existing active visits (scheduled/in_progress) before creating a new one.

### ✅ Bug 3: Workflow Lock Enforcement
**Issue:** Actions were possible when they should be disabled (e.g., starting work on unassigned tickets).
**Fix:** Updated `start_timer()` in `/app/backend/routes/service_visits.py` to validate ticket status before allowing work to start. Only tickets in 'assigned', 'in_progress', or 'pending_parts' states can have work started.

### ✅ Bug 4: Service History Display
**Issue:** Device page showed "No service history" even when tickets existed.
**Fix:** Updated `get_device_service_history()` in `/app/backend/server.py` to query BOTH `service_tickets` (old) AND `service_tickets_new` (new) collections.

## Test Reports
- `/app/test_reports/iteration_36.json` - Quotation & Workflow tests (100% pass)
- `/app/test_reports/iteration_37.json` - Device Dashboard & Company Tickets (100% pass)
- `/app/test_reports/iteration_38.json` - WatchTower Agent Download Feature (100% backend, 100% company portal UI)
- `/app/test_reports/iteration_39.json` - Critical Bug Fixes (100% pass - 20/20 tests)

## Test Files
- `/app/backend/tests/test_quotation_workflow.py`
- `/app/backend/tests/test_device_dashboard_company_tickets.py`
- `/app/backend/tests/test_watchtower_agent_download.py`
- `/app/backend/tests/test_bug_fixes_iteration_39.py`

## Credentials (Preview Environment)
- Admin: `ck@motta.in` / `Charu@123@`
- Engineer: `test_engineer_1bfa72f0@test.com` / `Engineer@123`
- Company: `testuser@testcompany.com` / `Test@123`
- Test Device ID: `206eb754-b34e-4387-8262-a64543a3c769`
- Test Engineer ID: `22468253-9dad-4fa5-89e3-aeabf0451051`

## 3rd Party Integrations
- **OpenAI GPT-4o-mini**: AI features (uses Emergent LLM Key)
- **Razorpay**: Payments (partial)
- **Cloudflare**: DNS and SSL
- **WatchTower**: INTEGRATED - Self-service agent download feature complete

---
Last Updated: February 9, 2026
- Device Dashboard (6 tabs) - COMPLETE
- Company Service Tickets - COMPLETE  
- WatchTower Integration - COMPLETE (Self-service agent download)
  - Company Portal: Dashboard card + Devices page button
  - Admin Portal: WatchTower Integration page with agent download per company
  - Note: WatchTower API has limitations on POST endpoints (520 errors) - handled gracefully
- **Critical Bug Fixes (Feb 9, 2026)** - COMPLETE
  - Engineer Accept/Decline endpoints added
  - Multiple visits prevention implemented
  - Workflow lock enforcement added
  - Service history now queries both ticket collections
