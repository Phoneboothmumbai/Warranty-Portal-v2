# Warranty & Asset Tracking Portal - PRD

## Original Problem Statement
Build an enterprise-grade Warranty & Asset Tracking Portal with a highly configurable, master-driven, multi-workflow ticketing system with strict multi-tenant data isolation.

## What's Been Implemented

### Multi-tenant Customer Portal (Mar 4, 2026) - NEW
- **Path-based multi-tenancy**: `/portal/{tenant_code}` URL structure for each company
- **Portal Login**: Branded login page per company with `company_portal_users` auth
- **Dashboard**: Full analytics (KPIs, charts, trends) scoped to company data
- **Tickets Page**: Searchable ticket list with status/priority filters, pagination
- **Devices Page**: Device inventory with warranty status cards (active/expiring/expired), search
- **Contracts Page**: AMC contract list with active/expired status badges
- **Profile Page**: User profile, company details, and summary stats
- **Portal Layout**: Branded top navigation with company logo, user info, and logout
- **Backend**: 6 new endpoints (`/tickets`, `/devices`, `/contracts`, `/profile`, `/analytics`, `/login`)
- **Testing: 100% (18/18 backend, all frontend flows verified)**

### Navigation Restructuring (Mar 4, 2026)
- **Dual-nav pattern**: Horizontal top module bar (6 primary modules) + contextual left sidebar
- **6 Modules**: Dashboard, Service Desk, Assets, Contracts, Analytics, Settings
- **Testing: 100%**

### Device Profitability Module (Mar 4, 2026)
- Password-protected "Profitability" tab — owner-only access
- Per-device cost: AMC Revenue vs (Labour + Travel + Parts) = Profit/Loss
- **Testing: 100%**

### Analytics Dashboard (Mar 4, 2026)
- 12-module analytics: Ticket Intelligence, Workforce, Financial, Client Health, Assets, SLA, Workflows, Inventory, Contracts, Operational Intelligence, Executive Summary, Profitability
- **Testing: 100%**

### Previous Features (Feb-Mar 2026)
- P0: Quotation Approval, Engineer Workflow Sync, Form Linking (100% tested)
- Help Topics (8 categories, 43 topics), Workflows (OEM/AMC/Non-Warranty)
- WhatsApp + Email Notifications, Admin Dashboard Redesign
- Engineer reschedule, visit workflow, inventory, pending bills, bulk upload

## Architecture
- Frontend: React + Tailwind + Shadcn/UI + Recharts
- Backend: FastAPI + Motor (MongoDB async)
- Database: MongoDB | Auth: JWT-based
- Layout: Top module bar + contextual sidebar (ServiceNow/Freshdesk pattern)
- Portal: Path-based multi-tenancy with TenantProvider context

## Navigation Structure
```
Top Bar: [Dashboard] [Service Desk] [Assets] [Contracts] [Analytics] [Settings]

Service Desk -> Tickets, Workforce, Calendar, Ticketing Setup, Renewal Alerts
Assets       -> Devices, Accessories, Asset Groups, Parts, Deployments, Catalog
Contracts    -> AMC, AMC Requests, Licenses, Subscriptions, Internet, History
Analytics    -> (full-width, 12 internal tabs)
Settings     -> Organization, Portal, Master Data, Item Master, Credentials, Products, Orders, Parts, Bills, Usage, Integrations
```

## Portal Structure
```
/portal/{tenant_code}/login     -> Branded login page
/portal/{tenant_code}/          -> Dashboard (KPIs, charts, trends)
/portal/{tenant_code}/tickets   -> Company ticket list
/portal/{tenant_code}/devices   -> Company device inventory
/portal/{tenant_code}/contracts -> AMC contracts
/portal/{tenant_code}/profile   -> User & company profile
```

## Resolved Issues
- Analytics Workforce Discrepancy: CLOSED (user confirmed active-only is correct behavior)

## Prioritized Backlog

### P0 (Next)
- Form Builder UI for dynamic form creation
- Workflow Designer UI for visual lifecycle editing
- Email Inbox UI

### P1
- Full CRUD for SLAs, Priorities, Canned Responses
- Quotation PDF Generation
- Razorpay Integration

### P2
- CompanySwitcher for platform admins
- server.py refactor, ESLint cleanup

## Credentials
- Admin: ck@motta.in / Charu@123@
- Engineer: test_engineer_1bfa72f0@test.com / Test@123
- Portal (Test Company 085831): portal@test.com / Welcome@123
- Portal (Acme Corporation): admin@acme.com / Welcome@123
- Profitability Password: owner123
