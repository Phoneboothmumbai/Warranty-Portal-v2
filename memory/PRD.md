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
- Enhanced ticket creation: Company → Site → Employee → Device with inline "Add New"

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

### Enhanced Ticket Creation (Feb 27, 2026)
- Multi-step: Company → Site → Employee → Device cascading flow
- "Add New Site" inline form saves to DB, syncs across portal
- "Add New Employee" inline form saves to DB, syncs across portal
- Employee auto-fills contact fields
- Device universal search + manual entry toggle
- Custom form fields load dynamically per help topic

### Security Hardening (Feb 26, 2026)
- scope_query() hard-fails when org_id is None
- masters.py, companies.py, amc_requests.py, amc_onboarding.py, qr_service.py all scoped
- All bulk import endpoints scoped by organization_id

## Architecture
- Frontend: React + Tailwind + Shadcn/UI
- Backend: FastAPI + Motor (MongoDB async)
- Database: MongoDB
- Auth: JWT-based, separate admin/engineer tokens
- Multi-tenancy: organization_id on all collections, hard-fail scope enforcement

### Item Master Module (Feb 27, 2026)
- **Categories**: CRUD for product categories (e.g., Security, Networking)
- **Products**: Full CRUD with SKU, part number, brand, manufacturer, pricing, GST slabs (0/5/12/18/28%), HSN code
- **Product Bundles**: Link products as recommendations (e.g., CCTV Camera suggests NVR, HDD, POE Switch)
- **Quotation Integration**: `/api/admin/item-master/products/{id}/suggestions` returns bundle recommendations
- **Collections**: `item_categories`, `item_products`, `item_bundles`
- **Frontend**: 3-tab interface at `/admin/item-master` under Settings group
- **Testing**: 25/25 backend tests passed, all frontend flows verified

### Quotation System with Item Master Integration (Feb 27, 2026)
- **Backend Quotation API**: Full CRUD at `/api/admin/quotations/*` — create, list, get, update, send, delete
- **Per-line GST**: Each line item has its own GST slab (0/5/12/18/28%), with auto-calculated gst_amount and line_total
- **Totals**: Auto-calculated subtotal, total_gst, grand_total on every quotation
- **Company Endpoints**: `/api/company/quotations` (list), `/{id}/respond` (approve/reject)
- **Enhanced QuotationModal** in ticket detail: Product picker from Item Master, bundle suggestions, real-time GST calc, Save Draft/Send
- **Enhanced PartsListModal**: Quick add from Item Master catalog search
- **CompanyQuotations.js**: Per-item GST column in detail modal, enhanced totals display
- **Collection**: `quotations`
- **Testing**: 17/17 backend tests passed, all frontend flows verified

### Complete Tenant Isolation Hardening (Feb 27, 2026)
- **Scope**: Every single admin endpoint in server.py (115+ functions) now enforces `organization_id` via `scope_query()`
- **Read isolation**: All find/find_one/count_documents queries wrapped with `scope_query(query, org_id)`  
- **Write isolation**: All insert_one calls now stamp `organization_id = org_id` on new records
- **Update/Delete isolation**: All update_one/update_many calls scoped by org_id
- **Dashboard**: Stats and alerts now strictly tenant-scoped (was global before)
- **Create Employee**: Now stamps org_id on new records + validates company within tenant
- **Settings**: Admin settings now isolated per organization
- **Supply Catalog (company portal)**: Scoped by org_id
- **Data migration**: Backfilled `organization_id` on 191 existing records missing it
- **Audit result**: 0 unscoped admin endpoints, 2 company endpoints (safe by design: AI summary + self-profile update)

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

### P2
- CompanySwitcher for platform admins
- Refactor server.py / unify User/Staff models
- Fix ESLint warnings and --legacy-peer-deps
- Backend unit tests with pytest

## Credentials
- Admin: ck@motta.in / Charu@123@
- Production domain: aftersales.support
