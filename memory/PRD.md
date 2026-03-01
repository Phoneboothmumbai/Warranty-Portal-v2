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

### Completed (Feb 2026)
- Full admin portal with dashboard, company/site/device management
- Full engineer portal with dashboard, calendar, ticket detail view
- Ticketing V2 system with seed data auto-provisioning + auto-deduplication
- Job acceptance/decline/reschedule workflow (both admin and engineer auth)
- Central calendar for admins, personal calendar for engineers
- Workforce overview for admins
- Notification system for declined jobs
- Smart scheduling with 30-min slots and 1-hour buffer
- Enhanced ticket creation (multi-step: Company > Site > Employee > Device)
- Item Master module (Categories, Products, Bundles)
- Quotation system (CRUD, GST calc, company approve/reject)
- Security hardening (scope_query, bulk imports, composite indexes)
- Homepage redesign with corporate aesthetic
- Production data isolation fix with migration script

### Engineer Reschedule Fix (Mar 1, 2026)
- Slot-based scheduling with 30-min intervals within working hours
- Backend validation: past date, blocked slots, working hours

### Engineer Visit Workflow (Mar 1, 2026)
- Start Visit (check-in timer), Service Report, Check Out
- Parts Request flow: auto-creates quotation draft for back office
- Resolution types: Fixed/Parts Needed/Escalation with auto stage transition
- Calendar floating popup with full ticket/company/device/history details

### Admin Parts Requests Management (Mar 1, 2026)
- Full management page at `/admin/parts-requests`
- Status filter pills: All/Pending/Quoted/Approved/Procured/Delivered
- Expandable rows with items table, pricing, engineer info, quotation link
- Status advancement buttons (Mark as Approved/Procured/Delivered)
- **Testing: 100% backend (16/16), 100% frontend**

### Item Master Bulk Upload (Mar 1, 2026)
- Sample CSV download with all fields (name, SKU, category, part_number, brand, manufacturer, description, unit_price, gst_slab, hsn_code, unit_of_measure, initial_stock, reorder_level)
- CSV upload with duplicate detection (by SKU or product name within tenant)
- Auto-creates categories if not existing
- Creates initial inventory records + transactions if initial_stock specified
- Error report for rejected rows

### Inventory Management (Mar 1, 2026)
- New "Inventory" tab in Item Master alongside Categories/Products/Bundles
- Table: Product, Category, SKU, In Stock (green/red), Purchased, Used, Price, Adjust
- Low Stock indicator for items at/below reorder level
- Search functionality
- Stock adjustment modal (Purchase/Return/Manual Adjustment/Initial Stock)
- Click any item → history panel showing:
  - Summary: In Stock, Purchased, Used counts
  - Transaction log with type badges and +/- quantities
  - Job details (ticket number, company name) for 'used' transactions
- Auto-deduct inventory when engineer checks out with resolution "fixed"
- Engineer inventory view endpoint
- **Testing: 100% backend (16/16), 100% frontend**

## Architecture
- Frontend: React + Tailwind + Shadcn/UI
- Backend: FastAPI + Motor (MongoDB async)
- Database: MongoDB
- Auth: JWT-based, separate admin/engineer tokens
- Multi-tenancy: organization_id on all collections

## Key Collections
- `tickets_v2` - Main ticket data
- `visits` - Engineer field visit records
- `parts_requests` - Parts requested by engineers
- `quotations` - Auto-created from parts requests
- `inventory` - Stock levels per product
- `inventory_transactions` - Transaction log (purchase/use/return/adjustment)
- `item_products` - Product catalog
- `item_categories` - Product categories
- `item_bundles` - Product bundles

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
- Backend unit tests with pytest

## Credentials
- Admin: ck@motta.in / Charu@123@
- Test Engineer: testeng@test.com / Test@123
- Production domain: aftersales.support
