# Warranty & Asset Tracking Portal - PRD

## Original Problem Statement
Build an enterprise-grade Warranty & Asset Tracking Portal with a highly configurable, master-driven, multi-workflow ticketing system with strict multi-tenant data isolation.

## Core Requirements
- Role-based access: Admin vs Engineer portals
- Master-driven ticketing: Help Topics, Forms, Workflows, Teams, Roles, SLA, Canned Responses
- Job acceptance/decline/reschedule workflow for technicians
- Central calendar (admin) and personal calendar (engineer)
- Workforce management with working hours, holidays, salary
- Strict multi-tenant data isolation - all data scoped by organization_id
- Enhanced ticket creation: Company > Site > Employee > Device with inline "Add New"

## What's Been Implemented

### Engineer Reschedule Fix (Mar 1, 2026)
- Slot-based scheduling with 30-min intervals within working hours
- Backend validation: past date, blocked slots, working hours

### Engineer Visit Workflow (Mar 1, 2026)
- Start Visit (check-in timer), Service Report, Check Out
- Parts Request flow: auto-creates quotation draft for back office
- Resolution types: Fixed/Parts Needed/Escalation with auto stage transition
- Calendar floating popup with full ticket/company/device/history details

### Admin Parts Requests Management (Mar 1, 2026)
- Full management page at /admin/parts-requests
- Status filter pills, expandable rows with items/pricing, status advancement

### Item Master Bulk Upload (Mar 1, 2026)
- Sample CSV download with all 13 fields
- CSV upload with duplicate detection (by SKU or product name)
- Auto-creates categories, error report for rejected rows

### Inventory Management (Mar 1, 2026)
- Inventory tab in Item Master with stock levels (In Stock/Purchased/Used)
- Low Stock alerts, search, stock adjustment modal
- Click item → history panel with transaction log + job details
- Auto-deduct inventory when engineer uses parts during checkout

### Pending Bills System (Mar 1, 2026)
- Auto-created when engineer uses parts during visit checkout
- Bills aggregated per ticket (multiple visits → same bill)
- Available at both /admin/pending-bills AND Item Master "Pending Bills" tab
- Stats dashboard: Pending count, Billed count, Pending Amount
- Filter pills: All/Pending/Billed
- Expandable rows with items table (Part, Added By, Qty, Price, GST, Total)
- "Mark as Done" requires Bill/Invoice Number → status changes to "billed"
- Timeline entry added to ticket when bill is completed
- Billing Team Email config in Settings (multiple emails)
- Email notification sent to billing team when parts are consumed (uses SMTP)
- **Testing: 100% backend, 100% frontend**

### Previous Work (Feb 2026)
- Full admin/engineer portals, ticketing V2, workforce, calendars
- Item Master (Categories/Products/Bundles), Quotation system
- Security hardening, data isolation, composite indexes
- Enhanced ticket creation, homepage redesign

## Architecture
- Frontend: React + Tailwind + Shadcn/UI
- Backend: FastAPI + Motor (MongoDB async)
- Database: MongoDB
- Auth: JWT-based, separate admin/engineer tokens
- Multi-tenancy: organization_id on all collections

## Key Collections
- `tickets_v2`, `visits`, `parts_requests`, `quotations`
- `inventory`, `inventory_transactions`
- `pending_bills` - Per-ticket billing records
- `item_products`, `item_categories`, `item_bundles`
- `settings` - includes billing_emails array

## Prioritized Backlog

### P0 (Next)
- Form Builder UI (drag-and-drop custom ticket forms)
- Workflow Designer UI (visual editor)
- Email Inbox UI (IMAP/SMTP config)

### P1
- Full CRUD for Teams, SLAs, Priorities, Canned Responses
- Notification Engine (Email/In-app)
- Quotation PDF Generation
- Razorpay Integration
- Customer quotation approval portal

### P2
- CompanySwitcher for platform admins
- Refactor server.py / unify User/Staff models
- Fix ESLint warnings and --legacy-peer-deps

## Credentials
- Admin: ck@motta.in / Charu@123@
- Test Engineer: testeng@test.com / Test@123
- Production domain: aftersales.support
