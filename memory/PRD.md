# Warranty & Asset Tracking Portal - PRD

## Target Market
**MSPs (Managed Service Providers) and IT Support Companies** - Organizations that manage IT assets, warranties, and service tickets across multiple client organizations.

## CHANGELOG
- **2026-01-30**: Complete Tenant Scoping & Tactical RMM Integration
  - **Full Tenant Scoping**: All major admin routes now filter by `organization_id`:
    - AMC Contracts (`list_amc_contracts`, `create_amc_contract`)
    - Engineers (`list_engineers`, `create_engineer`, `update_engineer`, `delete_engineer`)
    - Parts Inventory (`list_parts`, `create_part`, `get_part`, `update_part`, `delete_part`)
    - Services (`list_services`, `create_service`)
    - AMC Legacy (`list_amc`, `create_amc`)
  - **Tactical RMM Integration**:
    - Backend service: `/app/backend/services/tactical_rmm.py` - Full API client for Tactical RMM v2 API
    - Backend routes: `/app/backend/routes/tactical_rmm.py` - Configuration, agent sync, remote commands
    - Frontend: `/app/frontend/src/pages/admin/TacticalRMMIntegration.js` - Setup UI, agent list, sync controls
    - Features: Agent sync to devices, remote commands, reboot, recovery, client/site listing
  - **Admin Sidebar**: Added "Tactical RMM" link under Settings

- **2026-01-30**: MSP-Focused Landing Pages & Tenant Scoping
  - **Homepage Copy Update**: Rebranded for MSPs - "Manage All Your Clients. One Powerful Platform."
  - **MSP-Specific Features**: Multi-Client Management, Client Reports, Per-client SLAs, White-label options
  - **Trusted By Section**: Updated with MSP/IT company placeholders (TechServe Solutions, CloudIT Partners, etc.)
  - **Stats Updated**: 50,000+ Assets Managed, 200+ MSPs & IT Teams, 99.9% Uptime, < 2hr Avg Response
  - **Features Page**: Rewritten for MSP use cases - multi-client management, cross-client alerts, field engineer app
  - **Pricing Page**: Updated terminology (Clients instead of Companies, Technicians instead of Users)
  - **Ticketing Tenant Scoping**: Added `organization_id` filter to `list_tickets_admin()` endpoint

- **2026-01-30**: Beautiful SaaS Landing Pages Implementation
  - **Homepage Redesign**: Modern hero section with dashboard preview, features grid (6 cards), "How It Works" section (3 steps), pricing preview (4 plans), CTA section, and professional footer
  - **Features Page** (`/features`): Detailed feature breakdown with main features (Multi-Client Management, Warranty Tracking, Ticketing, AMC Contracts) and 12 additional feature cards
  - **Pricing Page** (`/pricing`): Monthly/Yearly toggle with 17% discount badge, 4 pricing tiers with feature comparison table and FAQs
  - **About Page** (`/about`): Company story, values, and stats
  - **Design System**: Outfit font for headings, Manrope for body, IBM Blue (#0F62FE) primary color, glassmorphism navigation, responsive mobile menu
  - Test report: `/app/test_reports/iteration_20.json` (30/30 frontend tests passed)

- **2026-01-30**: Multi-Tenant Admin Authentication Fix (P0 Blocker Resolved)
  - **Root Cause**: `get_org_from_token()` in `/app/backend/services/tenant.py` was querying `organization_members` by email (`user_id=payload.sub`) instead of the actual member ID
  - **Backend Fix**: Updated function to use `org_member_id` from JWT payload for member lookup
  - **Frontend Fix**: Updated localStorage key from `'token'` to `'admin_token'` in:
    - UsageDashboard.js
    - OrganizationSettings.js
    - StaticPages.js
    - CompanyDomains.js
    - BrandingContext.js
    - DeviceModelCatalog.js
  - **Tenant Scoping Added**: `list_companies()`, `create_company()`, `update_company()`, `delete_company()`, `list_devices()`, `create_device()` now filter by organization_id
  - Test report: `/app/test_reports/iteration_19.json` (17/17 backend, 100% frontend)

- **2026-01-30**: Editable Static Pages Implementation
  - **5 Default Pages**: Contact Us, Privacy Policy, Terms of Service, Refund Policy, Disclaimer
  - **Admin Editor**: HTML content editor with publish/unpublish toggle
  - **Public Display**: Clean page rendering at `/page/[slug]`
  - **Landing Page Footer**: Added all legal and quick links
  - Backend: `/api/pages/*`, `/api/admin/pages/*` routes
  - Frontend: StaticPage.js (public), StaticPages.js (admin)

- **2026-01-30**: Self-Signup & Razorpay Billing Implementation
  - **Public Signup Page** (`/signup`): 3-step wizard (Plan Selection → Account Details → Payment)
  - **Razorpay Integration**: Subscription billing with webhooks for payment events
  - **Organization Branding**: BrandingContext for tenant-specific logos and colors
  - **Tenant Scoping Utilities**: Helper functions for organization-filtered queries
  - Backend: `/api/billing/*` routes, Razorpay subscription and order handling
  - Frontend: SignupPage.js, BrandingContext.js

- **2026-01-30**: Multi-tenant SaaS Architecture Implementation
  - **Platform Super Admin Layer**: Separate login (`/platform/login`), dashboard, organization management
  - **Organization (Tenant) Model**: Complete data isolation with `organization_id` on all collections
  - **Migration Script**: `scripts/migrate_to_multitenancy.py` adds org_id to existing data
  - **Subscription Plans**: Trial, Starter (₹2,999/mo), Professional (₹7,999/mo), Enterprise
  - **Backend**: `/api/platform/*` routes, `/api/org/*` routes, tenant middleware
  - **Frontend**: `/platform/login`, `/platform/dashboard`, `/platform/organizations`
  - **User Hierarchy**: Platform Super Admin → Organization Admin → Company User

- **2026-01-30**: Enhanced AMC Onboarding Wizard
  - **Conditional Fields**: Step 5 (has_static_ip → static_ip_addresses), Step 6 (has_vpn → vpn_type, has_password_manager → password_manager_name)
  - **Multi-Tab Excel Template**: Device template now generates category-specific sheets based on Step 3 selections (Desktops, Laptops, Apple Devices, Servers, Network Devices, Printers, CCTV, Wi-Fi APs, UPS)
  - **Multi-Sheet Excel Import**: Upload handler parses all sheets, filters sample data, combines devices
  - Backend: CATEGORY_CONFIG mapping, _create_device_sheet() helper
  - Test report: `/app/test_reports/iteration_18.json` (13/13 backend, 100% frontend)

- **2026-01-29**: Implemented comprehensive AMC Onboarding Wizard (8-step flow)
  - Company portal multi-step form with draft save
  - Excel device inventory template & import
  - Admin approval workflow with "Request Changes" flow
  - Auto-conversion to AMC contract with device import
  - Backend: `/api/portal/onboarding`, `/api/admin/onboardings/*`
  - Frontend: `/company/amc-onboarding`

- **2026-01-29**: Added SLA configuration to Company model
  - Response & resolution times per priority level
  - Auto-applied to tickets based on company config
  - UI in company create/edit form

- **2026-01-29**: Added AMC Contract document attachments feature
  - New "Documents" tab in AMC Contract modal
  - Support for SLA, NDA, AMC agreements, quotes, invoices, POs
  - Upload, download, and remove functionality
  - Backend model updated with `documents` field
  
- **2026-01-29**: Added bulk edit/delete functionality for Office Supply Products
  - Checkbox selection (individual + select all)
  - Bulk action bar with Edit/Delete buttons
  - Bulk edit modal for Category, Status, Unit, Price
  - Backend endpoints: `/api/admin/supply-products/bulk-delete`, `/api/admin/supply-products/bulk-update`

## Original Problem Statement
Build an enterprise-grade Warranty & Asset Tracking Portal with:
- **Multi-tenant SaaS Platform** with independent organizations
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

### Enterprise Ticketing System - Phase 1 (Jan 28, 2025)
- ✅ **Core Ticket Model** - Complete ticket structure with unique IDs, sources, statuses, priorities
- ✅ **Department System** - Customizable departments with default SLAs and auto-assignment
- ✅ **SLA Engine** - Response & Resolution SLA tracking with priority multipliers, pause conditions
- ✅ **Immutable Audit Trail** - Ticket thread with customer messages, technician replies, internal notes, system events
- ✅ **Ticket CRUD** - Full create/read/update for admin and customer portals
- ✅ **Assignment System** - Assign/reassign tickets with audit logging
- ✅ **Dashboard Stats** - Open tickets by status, priority, unassigned count, SLA breach count
- ✅ **Categories** - Customizable ticket categories with auto-routing
- ✅ **Multi-tenant** - Company-scoped tickets, customers only see their own

#### Frontend Implementation (Jan 28, 2025)
- ✅ **Admin Ticket List** (`/admin/tickets`) - Dashboard stats, filters, sortable table with SLA indicators
- ✅ **Admin Ticket Detail** (`/admin/tickets/:id`) - Thread view, reply form, internal notes, quick actions
- ✅ **Company Portal Tickets** (`/company/support-tickets`) - Create/view/reply to tickets
- ✅ **Company Ticket Detail** (`/company/support-tickets/:id`) - Customer-friendly thread view
- ✅ **Sidebar Navigation** - Added "Support Tickets" to admin and company sidebars

### Enterprise Ticketing System - Phase 2 (Jan 28, 2025)
- ✅ **Admin Ticketing Settings** (`/admin/ticketing-settings`) - Manage Departments, SLA Policies, Categories
- ✅ **Departments Tab** - Create/edit/delete departments with default SLA, priority, auto-assignment settings
- ✅ **SLA Policies Tab** - Configure response/resolution times, business hours, priority multipliers
- ✅ **Categories Tab** - Define ticket categories with auto-routing to departments
- ✅ **Public Support Portal** (`/support`) - Anonymous ticket submission for non-company users
- ✅ **Submit Request Form** - Name, email, phone, subject, description, department, category, priority
- ✅ **Check Ticket Status** - Lookup by ticket number + email verification
- ✅ **Public Ticket Reply** - Customers can add replies to their tickets
- ✅ **Ticket Number Generation** - Unique TKT-YYYYMMDD-XXXXXX format

### Enterprise Ticketing System - Phase 3: osTicket-Inspired Features (Jan 28, 2025)
- ✅ **Help Topics** (replaces Categories) - Issue types that drive smart routing and form selection
  - Auto-routing: Department, Priority, SLA, Assignee
  - Custom Form linking per Help Topic
  - Icon support for visual identification
  - 10 Help Topics created
- ✅ **Custom Forms** (Dynamic Forms per Help Topic)
  - Form builder with 10 field types: text, textarea, number, email, phone, select, multiselect, checkbox, date, file
  - Version tracking for immutable ticket data
  - Customer-visible and staff-only field options
  - 6 Custom Forms created (Hardware Issue Form, AppleCare+ Request Form, etc.)
- ✅ **Canned Responses** (Predefined Replies)
  - Variable replacement: {{customer_name}}, {{ticket_number}}, {{subject}}, {{department_name}}, {{assigned_to}}, {{sla_due}}
  - Personal vs Shared responses
  - Department-scoped responses
  - Usage tracking
  - Dropdown integration in ticket detail reply form
  - 8 Canned Responses created
- ✅ **Ticket Participants (CC/Collaboration)**
  - Add/remove participants to tickets
  - Both customers and technicians can add participants
  - External participants (email-only)
  - Participant types: cc, collaborator, watcher
  - Duplicate prevention
  - All participants receive notifications (pending email integration)

### Enterprise Ticketing System - Phase 4: Email Integration (Jan 28, 2025)
- ✅ **Public Support Portal Updated** - Now uses Help Topics dropdown instead of legacy Categories
  - Dynamic custom form fields load when Help Topic selected
  - Help Topic auto-routing (priority, department, SLA) applied to public tickets
  - Form data saved with versioned snapshot
- ✅ **Email Service** (`/app/backend/services/email_service.py`)
  - SMTP support for Google Workspace (smtp.gmail.com:587 with TLS)
  - IMAP support for inbox monitoring (imap.gmail.com:993 with SSL)
  - HTML email templates with branded design
  - Variable replacement in email content
- ✅ **Email Notifications**
  - Ticket created notification
  - Reply added notification
  - Status changed notification
  - Ticket closed notification
  - Sends to all participants (requester + CC)
- ✅ **IMAP Email Sync**
  - Fetch unread emails from inbox
  - Parse email subject for ticket number (`[TKT-XXXXXXXX-XXXXXX]`)
  - Create new ticket from new emails
  - Add replies to existing tickets from email responses
  - Clean reply content (remove quoted text, signatures)
  - Sender validation against requester/participants
- ✅ **Admin Email Settings Tab**
  - Connection status display
  - Test Connection button (SMTP + IMAP)
  - Sync Now button for manual email sync
  - Send Test Email functionality
  - Configuration instructions for Google Workspace

#### Phase 4 API Endpoints:
- `GET /api/ticketing/admin/email/status` - Email configuration status
- `POST /api/ticketing/admin/email/test` - Test SMTP and IMAP connections
- `POST /api/ticketing/admin/email/sync` - Manually trigger email sync
- `POST /api/ticketing/admin/email/send-test` - Send test email

#### Phase 3 API Endpoints:
- `GET/POST/PUT/DELETE /api/ticketing/admin/help-topics` - Help Topic CRUD
- `GET /api/ticketing/public/help-topics` - Public Help Topics for ticket creation
- `GET/POST/PUT/DELETE /api/ticketing/admin/custom-forms` - Custom Form CRUD
- `GET /api/ticketing/public/custom-forms/{id}` - Get form for public ticket creation
- `GET/POST/PUT/DELETE /api/ticketing/admin/canned-responses` - Canned Response CRUD
- `POST /api/ticketing/admin/canned-responses/{id}/use` - Apply canned response with variable replacement
- `GET/POST/DELETE /api/ticketing/admin/tickets/{id}/participants` - Ticket Participants management
- `POST /api/ticketing/portal/tickets/{id}/participants` - Customer add participants

#### Phase 2 API Endpoints:
- `GET /api/ticketing/public/departments` - Public departments (no auth)
- `GET /api/ticketing/public/categories` - Public categories (no auth)
- `POST /api/ticketing/public/tickets` - Create public ticket (no auth)
- `GET /api/ticketing/public/tickets/{ticket_number}?email=` - Check ticket status
- `POST /api/ticketing/public/tickets/{ticket_number}/reply?content=&email=` - Add reply

#### Ticketing API Endpoints:
- `GET /api/ticketing/enums` - All dropdown values
- `GET/POST /api/ticketing/admin/departments` - Department management
- `GET/POST /api/ticketing/admin/sla-policies` - SLA policy management
- `GET/POST /api/ticketing/admin/categories` - Category management
- `GET/POST /api/ticketing/admin/tickets` - Admin ticket management
- `PUT /api/ticketing/admin/tickets/{id}` - Update ticket status/priority/assignment
- `POST /api/ticketing/admin/tickets/{id}/reply` - Add reply or internal note
- `POST /api/ticketing/admin/tickets/{id}/assign` - Assign ticket
- `GET /api/ticketing/admin/dashboard` - Dashboard statistics
- `GET/POST /api/ticketing/portal/tickets` - Customer ticket management
- `GET /api/ticketing/portal/departments` - Public departments for ticket creation

### AMC Self-Service Enhancements (Jan 25, 2025)

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
- ✅ **Enterprise Ticketing System Phase 2** - Admin settings + Public portal
  - Backend: 28 test cases passing (100%)
  - Admin Settings: Departments, SLA Policies, Categories management
  - Public Portal: Anonymous ticket submission and status check
- ✅ **Enterprise Ticketing System Phase 3** - osTicket-Inspired Features
  - Backend: 28 test cases passing (100%)
  - Help Topics with auto-routing (replaces Categories)
  - Custom Forms with dynamic field builder (10 field types)
  - Canned Responses with variable replacement
  - Ticket Participants (CC/Collaboration)
- ✅ **Enterprise Ticketing System Phase 4** - Email Integration
  - Backend: 12/12 test cases passing (100%)
  - Public Support Portal updated to use Help Topics
  - SMTP notifications to all ticket participants
  - IMAP sync for creating/replying to tickets from email
  - Admin Email Settings tab with test/sync controls

### P0 - Critical (In Progress)
- [ ] **Renewal Alerts Dashboard** - Backend API + Frontend to track expiring warranties/AMCs/licenses/parts

### P1 - Next Up
- [ ] **Scheduled Email Sync** - Background task to periodically sync IMAP emails
- [ ] **SLA Breach Checking** - Automated background task to check SLA deadlines
- [ ] **Auto-Escalation** - Escalate tickets on SLA breach

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
- ✅ ~~Fix frontend eslint warnings~~ - Reduced from 47 to 36 (3 errors remain in third-party shadcn components)

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
- `/app/test_reports/iteration_15.json` - Enterprise Ticketing Phase 2 (28/28 backend + frontend, 100%)
- `/app/test_reports/iteration_16.json` - Enterprise Ticketing Phase 3: osTicket Features (28/28, 100%)
- `/app/test_reports/iteration_17.json` - Enterprise Ticketing Phase 4: Email + Help Topics (12/12 backend + frontend, 100%)

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
