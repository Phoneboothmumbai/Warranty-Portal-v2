# Warranty & Asset Tracking Portal - PRD

## Original Problem Statement
Build an enterprise-grade Warranty & Asset Tracking Portal with a highly configurable, master-driven, multi-workflow ticketing system with strict multi-tenant data isolation. Targeted at MSPs offering IT services (CCTV, servers, networking, etc.).

## What's Been Implemented

### Project Management Module (Mar 4, 2026) - NEW
- **Template-driven task system**: Add a task type (CCTV, Server, Network, etc.) and all subtasks auto-generate
- **5 default MSP templates**: CCTV Installation (10 subtasks), Server Deployment (11), Computer Setup (8), Network Setup (10), Firewall Deployment (8)
- **Custom templates**: Create/edit/delete templates with configurable subtask sequences
- **Sequential workflow**: Subtasks follow order — complete step 1 before step 2 unlocks
- **Subtask features**: Start/Done actions, remarks, employee assignment, timestamps, estimated/actual hours
- **Auto-completion**: Task auto-completes when all mandatory subtasks done; project auto-completes when all tasks done
- **Gantt chart view**: CSS-based horizontal timeline showing tasks and subtasks
- **Navigation**: New top-level "Projects" module with sidebar (All Projects, Task Templates)
- **Testing: 100% (20/20 backend, all frontend flows verified)**

### Multi-tenant Customer Portal (Mar 4, 2026)
- Path-based multi-tenancy: /portal/{tenant_code} URL structure
- Login, Dashboard (KPIs + charts), Tickets, Devices, Contracts, Profile pages
- 6 new backend endpoints with real data
- **Testing: 100% (18/18 backend, all frontend flows verified)**

### Navigation Restructuring (Mar 4, 2026)
- Dual-nav: Top module bar (7 modules now including Projects) + contextual sidebar
- **Testing: 100%**

### Device Profitability Module (Mar 4, 2026)
- Password-protected profitability tab, per-device cost analysis
- **Testing: 100%**

### Analytics Dashboard (Mar 4, 2026)
- 12-module analytics (Ticket Intelligence, Workforce, Financial, etc.)
- **Testing: 100%**

### Previous Features (Feb-Mar 2026)
- P0: Quotation Approval, Engineer Workflow Sync, Form Linking
- Help Topics, Workflows, WhatsApp/Email Notifications
- Engineer portal, bulk upload, parts/inventory management

## Architecture
- Frontend: React + Tailwind + Shadcn/UI + Recharts
- Backend: FastAPI + Motor (MongoDB async)
- Database: MongoDB | Auth: JWT-based
- Layout: Top module bar + contextual sidebar

## Navigation Structure
```
Top Bar: [Dashboard] [Service Desk] [Projects] [Assets] [Contracts] [Analytics] [Settings]

Service Desk -> Tickets, Workforce, Calendar, Ticketing Setup, Renewal Alerts
Projects     -> All Projects, Task Templates
Assets       -> Devices, Accessories, Asset Groups, Parts, Deployments, Catalog
Contracts    -> AMC, AMC Requests, Licenses, Subscriptions, Internet, History
Analytics    -> (full-width, 12 internal tabs)
Settings     -> Organization, Portal, Master Data, Item Master, etc.
```

## Project Management Data Model
```
project_templates: { id, name, category, description, subtasks[] }
projects:          { id, name, company_id, status, priority, start/end_date }
project_tasks:     { id, project_id, template_id, name, status, assigned_to }
project_subtasks:  { id, task_id, order, name, status, assigned_to, remarks, timestamps }
```

## Prioritized Backlog

### P0 (Next)
- Form Builder UI for dynamic form creation
- Workflow Designer UI for visual lifecycle editing
- Email Inbox UI

### P1
- Full CRUD for SLAs, Priorities, Canned Responses
- Quotation PDF Generation
- Razorpay Integration
- Time Tracking & Billing (for MSP hourly billing)
- Recurring Invoicing for managed services

### P2
- CompanySwitcher for platform admins
- server.py refactor, ESLint cleanup
- Runbook/Playbook automation

## Credentials
- Admin: ck@motta.in / Charu@123@
- Engineer: test_engineer_1bfa72f0@test.com / Test@123
- Portal (Test Company 085831): portal@test.com / Welcome@123
- Portal (Acme Corporation): admin@acme.com / Welcome@123
- Profitability Password: owner123
