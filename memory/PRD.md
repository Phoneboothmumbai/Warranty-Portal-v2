# Warranty & Asset Tracking Portal - PRD

## Original Problem Statement
Build an enterprise-grade Warranty & Asset Tracking Portal with a highly configurable, master-driven, multi-workflow ticketing system with strict multi-tenant data isolation.

## What's Been Implemented

### Navigation Restructuring (Mar 4, 2026) - NEW
- **Dual-nav pattern**: Horizontal top module bar (6 primary modules) + contextual left sidebar
- **6 Modules**: Dashboard, Service Desk, Assets, Contracts, Analytics, Settings
- **Full-width pages**: Dashboard & Analytics (no sidebar — maximum chart space)
- **Contextual sidebars**: Service Desk (5 items), Assets (6), Contracts (6), Settings (15)
- **Mobile responsive**: Hamburger menu + horizontal scrolling tabs at 768px
- **Reduced clutter**: From 30+ items in one sidebar to max 6-15 focused items per module
- **Testing: 100% (10/10 frontend flows verified)**

### Device Profitability Module (Mar 4, 2026)
- Password-protected "Profitability" tab — owner-only access
- Per-device cost: AMC Revenue vs (Labour + Travel + Parts) = Profit/Loss
- Engineer hourly_rate field, zone-based travel tiers (4 configurable), expandable call details
- Company-level profitability rollup with margin %
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

## Navigation Structure
```
Top Bar: [Dashboard] [Service Desk] [Assets] [Contracts] [Analytics] [Settings]

Service Desk → Tickets, Workforce, Calendar, Ticketing Setup, Renewal Alerts
Assets       → Devices, Accessories, Asset Groups, Parts, Deployments, Catalog
Contracts    → AMC, AMC Requests, Licenses, Subscriptions, Internet, History
Analytics    → (full-width, 12 internal tabs)
Settings     → Organization, Portal, Master Data, Item Master, Credentials, Products, Orders, Parts, Bills, Usage, Integrations
```

## Prioritized Backlog

### P0 (Next)
- Multi-tenant Customer Facing Portal (with company-level analytics)
- Form Builder UI, Workflow Designer UI, Email Inbox UI

### P1
- Full CRUD for SLAs, Priorities, Canned Responses
- Quotation PDF Generation, Razorpay Integration

### P2
- CompanySwitcher for platform admins
- server.py refactor, ESLint cleanup

## Credentials
- Admin: ck@motta.in / Charu@123@
- Engineer: test_engineer_1bfa72f0@test.com / Test@123
- Profitability Password: owner123
