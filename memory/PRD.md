# Warranty & Asset Tracking Portal - PRD

## Original Problem Statement
Build an enterprise-grade Warranty & Asset Tracking Portal with:
- B2B office supplies ordering system
- Bulk data import capabilities
- QR code generation for asset tagging
- Mobile-friendly portal for field service engineers
- AI-powered triage bot
- Device configuration and employee assignment
- Email & Cloud Subscription management module
- Asset Grouping/Bundles feature
- Renewal Alerts Dashboard
- Accessories & Peripherals module
- Asset Transfer between employees
- Comprehensive Credentials Management

## What's Been Implemented

### Core Features (Complete)
- ✅ Admin Portal with dashboard, companies, users, devices management
- ✅ Company Portal for end-users to view devices, raise tickets
- ✅ Engineer Portal for field service visits
- ✅ QR Code generation for asset tagging
- ✅ AI Support Triage Bot (GPT-4o-mini via Emergent LLM Key)
- ✅ osTicket integration for ticket creation
- ✅ Office Supplies ordering system
- ✅ AMC Contract management
- ✅ License management
- ✅ Site management
- ✅ Device User & Configuration feature
- ✅ Company Employee management with bulk Excel/CSV upload
- ✅ Email & Cloud Subscriptions module with user tracking
- ✅ Employee Detail Page (360-degree view)
- ✅ Admin Device Detail Page

### Recent Additions (Jan 2025)
- ✅ **Collapsible/Grouped Sidebar Navigation** - Admin portal sidebar now groups items
- ✅ **Asset Transfer Feature** - Transfer devices between employees
- ✅ **Credentials Management System** - Device-specific credentials for NVRs, routers, etc.
- ✅ **Internet Services/ISP Module** - Track ISP connections with credentials
- ✅ **Admin Credentials Dashboard** - Central view of all credentials
- ✅ **Company Portal Credentials Page** - Company users can view their credentials
- ✅ **Enhanced Parts Module** - Track component warranties with brand, model, capacity, serial number
- ✅ **Public Warranty Check for Parts** - Search parts by serial number on public page
- ✅ **Bulk Import with Employee Assignment** - Assign devices to employees during upload
- ✅ **Enhanced Products Module** - Images, prices, SKUs for office supplies
- ✅ **Warranty Calculation Fix** - Corrected warranty expiry (install date + months - 1 day)
- ✅ **Accessories & Peripherals Module** - Full CRUD with 12 accessory types seeded
- ✅ **AI-Powered Device Model Catalog** - Automatically fetch device specs and compatible consumables

### Security Enhancements (Jan 25, 2025)
- ✅ **Rate Limiting** - Brute-force protection (5 login attempts/minute per IP) using slowapi
- ✅ **Strong Password Requirements** - 8+ chars, uppercase, lowercase, digit, special character required
- ✅ **Password Validation** - Applied to all user creation, registration, and password reset endpoints
- ✅ **Security Info API** - `/api/security/info` exposes password requirements and rate limiting config
- ✅ **Full Part Details Display** - Admin Device Details page now shows comprehensive part info including brand, model, serial number, capacity, purchase/install dates, warranty status badges, vendor, cost, and notes

### AMC Self-Service Request System (Jan 25, 2025)
- ✅ **Company Portal: Request AMC** - Users can submit AMC requests with package/device selection

### Technician Panel for OEM Service Records (Jan 28, 2025)
- ✅ **Enhanced Service History Page** - Complete rewrite with modern UI, stats cards, filters
- ✅ **Service Classification System** - Categories: Internal, OEM Warranty, Third-Party, Inspection
- ✅ **OEM Warranty Service Tracking** - Full workflow for tracking OEM warranty cases
- ✅ **Auto-locked OEM Fields** - OEM services auto-lock Responsibility=OEM, Role=Coordinator, Billing=Warranty Covered
- ✅ **AMC Protection** - OEM services don't count toward AMC quota
- ✅ **OEM Details Section** - OEM Name, Case Number, Warranty Type, Priority, Status, Engineer, Visit Date
- ✅ **Service Outcome Tracking** - Resolution summary, parts replaced, cost incurred for closures
- ✅ **Attachment Management** - Upload/view attachments with OEM proof requirement warning
- ✅ **Backend Validation** - Comprehensive validation for OEM service requirements

### Production Deployment Support (Jan 28, 2025)
- ✅ **deploy.sh Script** - One-command deployment for production server
- ✅ **Admin Finder Script** - find_admin.py to locate admin accounts in database
- ✅ **AMC Packages** - Admin can create predefined packages (Basic, Standard, Premium) with pricing
- ✅ **Company-Specific Pricing** - Set custom pricing per company for each package
- ✅ **Device Selection** - Users can select specific devices, all devices, or by category
- ✅ **Duration Options** - 1, 2, or 3 year contracts with multi-year discounts
- ✅ **Admin Review Panel** - View requests, set pricing, add notes
- ✅ **Status Workflow** - Pending Review → Under Review → Approved/Rejected/Changes Requested
- ✅ **Approval Creates Contract** - Automatic AMC contract creation upon approval
- ✅ **In-App Notifications** - Users notified when request status changes
- ✅ **Payment Tracking** - Admin can mark payment as received

### Backend Refactoring (Jan 22, 2025)
- ✅ Created `routes/` directory structure for modular endpoints
- ✅ Extracted routes: public, auth, masters, webhooks, qr_service, companies
- ✅ Documented refactoring plan in `routes/REFACTORING_PLAN.md`
- ✅ Backed up original server.py to server_original.py

## Prioritized Backlog

### P0 - Critical (Verified)
- ✅ **Public Warranty Check for Parts** - Backend searches both devices and parts collections
- ✅ **Warranty Calculation Fix** - Corrected warranty expiry calculation (install date + months - 1 day)
  - Example: Jan 22, 2026 + 12 months = Jan 21, 2027

### P0 - Critical (Verified Complete - Jan 28, 2025)
- ✅ **Technician Panel for OEM Service Records** - Complete service history page with OEM tracking
  - Backend: 18 test cases passing (100%)
  - Frontend: Full UI with conditional OEM fields, auto-locking, filters

### P0 - Critical (In Progress)
- [ ] **Renewal Alerts Dashboard** - Backend API + Frontend to track expiring warranties/AMCs/licenses/parts

### P1 - Verified Complete
- ✅ **Accessories & Peripherals Module** - Full CRUD implementation
  - Backend: `/api/admin/accessories` with full CRUD
  - Frontend: `/admin/accessories` page with search, filters, stats
  - Master data: 12 accessory types seeded (Keyboard, Mouse, Headset, etc.)

### P1 - High Priority
- [ ] Add two location fields to devices: `site` and `office_location`
- [ ] Enhanced Employee search page (search by name/email/phone, company filtering)
- [ ] Complete Orders page enhancement (show product images, calculate totals)

### P2 - Medium Priority  
- [ ] Continue backend route refactoring (remaining sections in server.py)
- [ ] Engineer Field Visit workflow mobile UI
- [ ] Admin & User Role Management (RBAC)
- [ ] Fix frontend eslint warnings

### P3 - Low Priority/Future
- [ ] PDF Export for service history reports
- [ ] Email notifications

## Backend Routes Refactoring Status

### Extracted Routes (Complete)
| Route File | Description | Status |
|------------|-------------|--------|
| public.py | Warranty search, public settings | ✅ Complete |
| auth.py | Authentication endpoints | ✅ Complete |
| masters.py | Master data management | ✅ Complete |
| webhooks.py | osTicket webhooks | ✅ Complete |
| qr_service.py | QR codes, quick service | ✅ Complete |
| companies.py | Companies, bulk imports, portal users | ✅ Complete |

### Pending Migration (In server.py)
| Route File | Lines in server.py | Status |
|------------|-------------------|--------|
| users.py | 1907-2008 | Placeholder |
| employees.py | 2010-2350 | Placeholder |
| devices.py | 2350-2760 | Placeholder |
| services.py | 2758-2885 | Placeholder |
| parts.py | 2885-2947 | Placeholder |
| amc.py | 2947-3337 | Placeholder |
| sites.py | 3337-3505 | Placeholder |
| deployments.py | 3505-3926 | Placeholder |
| search.py | 3926-4158 | Placeholder |
| settings.py | 4158-4197 | Placeholder |
| licenses.py | 4197-4407 | Placeholder |
| dashboard.py | 4607-4785 | Placeholder |
| engineer.py | 4785-5231 | Placeholder |
| subscriptions.py | 5231-5626 | Placeholder |
| asset_groups.py | 5626-6096 | Placeholder |
| company_portal.py | 6096-7945 | Placeholder |
| internet_services.py | 7945-8036 | Placeholder |
| credentials.py | 8036-8121 | Placeholder |
| supplies.py | 8121-8501 | Placeholder |

## Tech Stack
- Frontend: React + Tailwind CSS + Shadcn/UI
- Backend: FastAPI + Motor (async MongoDB)
- Database: MongoDB
- AI: OpenAI GPT-4o-mini via emergentintegrations
- File Processing: pandas, openpyxl
- Security: slowapi (rate limiting), bcrypt (password hashing), JWT (authentication)

## Key API Endpoints
- `/api/security/info` - Security settings (password requirements, rate limits)
- `/api/warranty/search?q={serial}` - Search devices AND parts by serial number
- `/api/admin/asset-transfers` - Asset transfer between employees
- `/api/admin/credentials` - Central credentials dashboard
- `/api/admin/internet-services` - ISP management
- `/api/company/credentials` - Company-facing credentials page
- `/api/admin/parts` - Enhanced parts with warranty tracking
- `/api/device-models/lookup` - AI-powered device specification lookup
- `/api/device-models` - Device model catalog CRUD
- `/api/device-models/consumables/search` - Search compatible consumables
- `/api/admin/amc-packages` - AMC package management (CRUD)
- `/api/admin/amc-company-pricing` - Company-specific AMC pricing
- `/api/admin/amc-requests` - Admin AMC request management
- `/api/admin/amc-requests/{id}/approve` - Approve and create contract
- `/api/company/amc-packages` - Available packages for company
- `/api/company/amc-requests` - Company AMC request CRUD
- `/api/company/notifications` - In-app notifications
- `/api/admin/notifications` - Admin notifications
- `/api/admin/services/options` - Service form dropdown options (OEM names, statuses, etc.)
- `/api/admin/services` - Full CRUD with OEM service support
- `/api/admin/services?service_category=oem_warranty_service` - Filter by category

## Test Credentials
- Admin: admin@demo.com / admin123
- Company: jane@acme.com / company123
- Engineer: raj@example.com / password

## Test Data
- Test Part Serial: WGS5T1234567 (Seagate IronWolf 4TB HDD)

## Test Reports
- `/app/test_reports/iteration_11.json` - Sidebar & Asset Transfer tests (14/14 passed)
- `/app/test_reports/iteration_12.json` - Security Enhancements & Part Details tests (21/21 passed)
- `/app/test_reports/iteration_13.json` - AMC Self-Service Request System tests (25/25 passed, 100%)
- `/app/test_reports/iteration_14.json` - Technician Panel for OEM Service Records (18/18 backend, 100%)

## Deployment Scripts
- `/app/deploy.sh` - One-command production deployment script
- `/app/scripts/find_admin.py` - Find admin accounts in database

## File Structure
```
/app/backend/
├── routes/
│   ├── __init__.py          # Route aggregator
│   ├── REFACTORING_PLAN.md  # Migration documentation
│   ├── public.py            # ✅ Extracted
│   ├── auth.py              # ✅ Extracted
│   ├── masters.py           # ✅ Extracted
│   ├── webhooks.py          # ✅ Extracted
│   ├── qr_service.py        # ✅ Extracted
│   ├── companies.py         # ✅ Extracted
│   └── [other placeholders] # Pending migration
├── server.py                # Main server (8500+ lines)
├── server_original.py       # Backup before refactoring
└── ...
```
