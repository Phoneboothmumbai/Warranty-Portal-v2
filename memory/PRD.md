# Warranty & Asset Tracking Portal - PRD

## Original Problem Statement
Build an enterprise-grade Warranty & Asset Tracking Portal with a highly configurable, master-driven, multi-workflow ticketing system with strict multi-tenant data isolation.

## What's Been Implemented

### Comprehensive Analytics Dashboard (Mar 4, 2026)
- **10-module analytics engine** covering all business intelligence needs:
  1. **Ticket Intelligence**: Volume trends, stage funnel, resolution times (avg/P95), bottleneck detection, source analysis, priority distribution, heatmap, reopen rate
  2. **Workforce Performance**: Engineer scorecards (tickets, resolution time, FTF rate), workload distribution, parts cost per engineer, visit tracking
  3. **Financial Analytics**: Quotation pipeline (sent/approved/rejected), revenue by month, parts cost tracking, pending bills aging, AMC revenue
  4. **Client Health Score**: Composite health scoring (0-100) based on tickets, SLA breaches, device ratios. At-risk company identification
  5. **Asset Intelligence**: Warranty expiry timeline (30/60/90d), failure rate by brand/model, device age distribution, lifecycle cost
  6. **SLA Compliance**: Compliance rate, breach by priority/team, breach trend (weekly), escalation tracking
  7. **Workflow Analytics**: Stage cycle times, stage backlog per workflow, warranty type distribution, transition patterns
  8. **Inventory & Parts**: Stock level alerts, consumption trends, transaction volume (in/out), part request status
  9. **Contract & AMC**: Active/expired/expiring contracts, type distribution, coverage rate, renewal pipeline, by-company breakdown
  10. **Operational Intelligence (AI)**: Trend prediction, anomaly detection (company spike alerts), actionable recommendations, top issue clustering
- **Executive Summary**: 8 top-level KPIs with period-over-period change percentages
- **Period selector**: 7d / 30d / 90d / 365d with dynamic data refresh
- **In-memory caching**: 5-minute TTL for performance optimization
- **Interactive charts**: Recharts library (Area, Bar, Pie, Line, Radar charts)
- **Testing: 100% backend (16/16), 100% frontend (all 11 tabs verified)**

### P0 Feature Verification Complete (Mar 4, 2026)
- **Customer Quotation Approval via Email**: Token-based public approve/reject endpoints
- **Engineer Portal Workflow Sync**: 13-stage progress bar with transitions
- **Help Topic -> Form Linking**: All 43 topics linked to dynamic forms
- **Testing: 100% (10/10 backend, all frontend)**

### Previous Features (Feb-Mar 2026)
- Help Topic System (8 categories, 43 topics, full CRUD)
- Warranty-Based Workflows (OEM/AMC/Non-Warranty, auto-detection)
- WhatsApp + Email Notifications (stage-based, 5 teams)
- Admin Ticket Dashboard Redesign (split sections, filter pills)
- Engineer reschedule, visit workflow, inventory, pending bills, bulk upload

## Architecture
- Frontend: React + Tailwind + Shadcn/UI + Recharts
- Backend: FastAPI + Motor (MongoDB async)
- Database: MongoDB | Auth: JWT-based
- Analytics: In-memory cached aggregation endpoints (5min TTL)

## Key Collections
- `tickets_v2` - Main tickets with workflows, timelines
- `ticket_workflows` - 7 configurable workflows
- `ticket_help_topics` - 43+ topics with category/form/workflow links
- `devices` - 58 devices with warranty tracking
- `companies` - 34 client companies
- `engineers` - 12 field technicians
- `quotations` - Financial pipeline
- `amc_contracts` - AMC/warranty contracts
- `inventory` / `stock_ledger` - Inventory management

## Prioritized Backlog

### P0 (Next)
- Multi-tenant Customer Facing Portal (portal.aftersales.support/{tenant_code})
- Form Builder UI (admin dynamic form creation/editing)
- Workflow Designer UI (visual workflow editor)
- Email Inbox UI (IMAP/SMTP)
- Company-level analytics view for customer portal

### P1
- Full CRUD for SLAs, Priorities, Canned Responses
- Quotation PDF Generation
- Razorpay Integration

### P2
- CompanySwitcher for platform admins
- server.py refactor & User/Staff model unification
- ESLint warnings cleanup & legacy-peer-deps fix

## Credentials
- Admin: ck@motta.in / Charu@123@
- Test Engineer: test_engineer_1bfa72f0@test.com / Test@123
