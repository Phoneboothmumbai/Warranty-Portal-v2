# Warranty & Asset Tracking Portal - PRD

## Original Problem Statement
Build an enterprise-grade Warranty & Asset Tracking Portal with a highly configurable, master-driven, multi-workflow ticketing system with strict multi-tenant data isolation.

## What's Been Implemented

### Comprehensive Help Topic System (Mar 4, 2026)
- **8 master categories**: Hardware & Devices, Software & OS, Network & Connectivity, Peripherals & Accessories, Service Requests, Warranty & AMC, Commercial & Billing, General
- **43 help topics** covering all MSP/warranty scenarios with searchable tags
- Full CRUD for categories (create, edit, delete, reorder)
- Full CRUD for topics with: category linking, workflow linking, form linking, tags, priority, device requirement
- Searchable topic selector in ticket creation (grouped by category, fuzzy search by name/description/tags)
- Category filter pills on Ticketing Setup page
- **Testing: 100% backend (14/14), 100% frontend**

### Warranty-Based Workflow System (Mar 4, 2026)
- 3 device-type workflows: OEM Warranty (8 stages), AMC Support (10 stages), Non-Warranty (12 stages)
- Auto-detection engine: checks warranty dates + AMC contracts → assigns workflow
- OEM Tracking Panel on ticket detail (case#, OEM engineer, brand reference, status)
- **Testing: 100% backend (9/9), 100% frontend**

### WhatsApp + Email Notifications (Mar 2, 2026)
- Stage-based notification panel with 5 team options via wa.me/ links
- Configurable team phone numbers and emails in Settings
- **Testing: 100% (15/15 backend, all frontend)**

### Admin Ticket Dashboard Redesign (Mar 2, 2026)
- "To Be Assigned" / "Assigned Tickets" split with status filter pills
- **Testing: 100% (13/13 backend, all frontend)**

### Previous Work (Feb-Mar 2026)
- Engineer reschedule, visit workflow, inventory, pending bills, bulk upload, parts requests, branding

## Architecture
- Frontend: React + Tailwind + Shadcn/UI
- Backend: FastAPI + Motor (MongoDB async)
- Database: MongoDB | Auth: JWT-based

## Key Collections
- `help_topic_categories` — 8 master categories (CRUD)
- `ticket_help_topics` — 43+ topics with category_id, tags, parent_id, workflow_id
- `ticket_workflows` — 7 workflows including OEM, AMC, Non-Warranty
- `tickets_v2` — with device_warranty_type and OEM tracking fields

## Prioritized Backlog

### P0 (Next)
- Customer Quotation Approval via Email (approve/deny buttons for non-warranty flow)
- Engineer portal sync with workflow-specific stages
- Form Builder improvements (link forms to help topics)

### P1
- Full CRUD for SLAs, Priorities, Canned Responses
- Notification Engine (Email/In-app)
- Quotation PDF Generation, Razorpay Integration
- Email Inbox UI (IMAP/SMTP)

### P2
- CompanySwitcher, server.py refactor, ESLint cleanup, scalability

## Credentials
- Admin: ck@motta.in / Charu@123@
- Test Engineer: testeng@test.com / Test@123
