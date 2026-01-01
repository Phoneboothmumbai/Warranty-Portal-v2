# Warranty & Asset Tracking Portal - PRD

## Original Problem Statement
Build a web-based warranty lookup portal for customers where they can enter a Device Serial Number or Asset Tag and instantly view warranty status of:
- The main device (laptop, CCTV, printer, etc.)
- Any replaced or repaired parts
- AMC or service coverage (if applicable)

Support multiple parts with different warranty periods for the same device.

## User Personas
1. **End Customer** - Checks warranty status via public portal (no login required)
2. **IT Admin** - Manages companies, users, devices, parts, AMC, and portal branding

## Core Requirements
- JWT-based admin authentication
- Clean, light, trust-focused design
- PDF export for warranty reports
- Configurable branding (logo + accent color)
- Public customer portal (search by serial/asset tag only)

## Architecture
- **Frontend**: React 19 + Tailwind CSS + Shadcn/UI
- **Backend**: FastAPI + MongoDB
- **Auth**: JWT tokens (8-hour expiry)
- **PDF**: ReportLab for server-side generation

## Data Model
- Companies → Users (1:N)
- Companies → Devices (1:N)
- Devices → Parts (1:N)
- Devices → AMC (1:1)
- Users ↔ Devices (N:N via assigned_user_id)
- Companies → Sites (1:N)
- Sites → Deployments (1:N)
- Companies → AMC Contracts V2 (1:N)
- AMC_Device (join table for device-contract relationships)

## What's Been Implemented

### Phase 1 - MVP Complete (January 2026)
- [x] Public landing page with warranty search ("The Monolith" layout)
- [x] Warranty result page with device/parts/AMC status ("The Receipt" layout)
- [x] PDF warranty report download
- [x] Admin authentication (setup + login)
- [x] Admin dashboard with stats
- [x] Companies CRUD
- [x] Users CRUD (per company)
- [x] Devices CRUD (with warranty dates, assign to company/user)
- [x] Parts CRUD (with auto-calculated warranty expiry)
- [x] AMC CRUD (per device)
- [x] Settings (portal name + accent color + logo upload)
- [x] Responsive design
- [x] All data-testid attributes for testing

### Phase 1.5 - Extended Features
- [x] Master Data Management page
- [x] AMC Contracts V2 (company-level contracts with coverage rules)
- [x] Site & Deployment Module
- [x] Universal Search in admin header
- [x] Deployment Guide for Vultr server

### Phase 2A - Foundation (January 2026) ✅ COMPLETE
- [x] **SmartSelect Component** - Reusable searchable dropdown using Shadcn Combobox
  - Search-as-you-type with debounce (300ms)
  - Async API loading with pagination (`?q=&limit=20`)
  - Keyboard navigation
  - Inline "➕ Add New" option
  - Auto-select after inline creation
- [x] **DateDurationInput Component** - Dual mode input
  - Radio toggle: End Date / Duration
  - Duration mode: Number + Unit selector (Days/Months/Years)
  - Auto-calculate and display end date
  - Always stores start_date + end_date (no duration stored)
- [x] **Quick Create Forms** - Inline master creation
  - QuickCreateCompany
  - QuickCreateUser
  - QuickCreateSite
  - QuickCreateMaster
- [x] **Backend Search Support** - All list APIs now support `?q=&limit=&page=`
  - /api/admin/companies
  - /api/admin/users
  - /api/admin/sites
  - /api/masters/public
- [x] **Quick Create Endpoints** - For inline creation
  - POST /api/admin/companies/quick-create
  - POST /api/admin/users/quick-create
  - POST /api/admin/sites/quick-create
  - POST /api/admin/masters/quick-create
- [x] **Duration Units Master** - Days, Months, Years for warranty calculations
- [x] **Devices Page Updated** - Now uses SmartSelect with inline creation

## Phase 2 Roadmap (In Progress)

### Phase 2B - Core Modules (Next)
- [ ] Software & License Module (new entity + renewal tracking)
- [ ] Service Record Enhancement (parts used + warranty impact)
- [ ] AMC_Device join table + Bulk Assignment (3 options)

### Phase 2C - Bulk Operations & Polish
- [ ] Bulk Upload System (Template → Upload → Preview → Import)
  - Priority: Devices → Users → Companies → Sites → Parts → Licenses
- [ ] Warranty Check → "Request Support" CTA (https://support.thegoodmen.in)

### Phase 3 - Future
- [ ] WhatsApp Integration (QR-based notifications)
- [ ] PDF Export for Service History
- [ ] Advanced admin list customization
- [ ] Customer login portal
- [ ] Advanced role-based permissions
- [ ] SLA timers and ticket automation

## Design Principles (Phase 2+)
1. **Searchable dropdowns everywhere** - Never load full datasets
2. **Inline master creation** - No context switching
3. **Duration OR End Date** - User chooses, system stores dates
4. **Enterprise-grade bulk uploads** - Template → Preview → Import → Summary
5. **Service records create history** - Parts + warranty impact tracking

## Key Components Created (Phase 2A)
- `/app/frontend/src/components/ui/smart-select.jsx`
- `/app/frontend/src/components/ui/date-duration-input.jsx`
- `/app/frontend/src/components/forms/QuickCreateCompany.jsx`
- `/app/frontend/src/components/forms/QuickCreateUser.jsx`
- `/app/frontend/src/components/forms/QuickCreateSite.jsx`
- `/app/frontend/src/components/forms/QuickCreateMaster.jsx`

## Admin Credentials
- Email: admin@demo.com
- Password: admin123
