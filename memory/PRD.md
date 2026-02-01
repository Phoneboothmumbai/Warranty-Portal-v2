# Warranty & Asset Tracking Portal - PRD

## Target Market
**MSPs (Managed Service Providers) and IT Support Companies** - Organizations that manage IT assets, warranties, and service tickets across multiple client organizations.

## CHANGELOG

### 2026-02-01: Public Pages UI Consistency & Platform Dashboard Fix (Complete)

#### P0: Platform Dashboard Stats Fix
- **Confirmed Working**: `/api/platform/dashboard/stats` endpoint returns correct data
- Dashboard now displays:
  - 6 total organizations
  - 5 trial status organizations
  - 23 companies, 35 devices, 7 users, 24 tickets
  - Revenue metrics (MRR, ARR, conversion rate)
  - Organizations by status and plan breakdown
  - Recent organizations list

#### P1: Shared Header/Footer Components
- **Created**: `frontend/src/components/public/PublicHeader.js`
  - Consistent navigation: Features, Pricing, Contact, Support Portal
  - Sign In link and Get Started CTA button
  - Mobile responsive with hamburger menu
  - Uses company logo and name from settings context
- **Created**: `frontend/src/components/public/PublicFooter.js`
  - Full footer with Product, Company, Legal links
  - Simple footer variant for signup/login pages
  - Social media links and company branding

#### P1: Public Pages Refactored
- **LandingPage.js**: Now uses `PublicHeader` and `PublicFooter` components
- **FeaturesPage.js**: Now uses `PublicHeader` and `PublicFooter` components
- **PricingPage.js**: Now uses `PublicHeader` and `PublicFooter` components
- **SignupPage.js**: Converted from dark purple theme to light white/slate theme
  - Uses `PublicHeader` and `PublicFooter` (simple variant)
  - All form inputs, cards, buttons now use light theme colors
  - Plan cards with white backgrounds and slate borders

**All tests passed**: 100% backend (10/10) and frontend success rate

### 2026-01-30: Full Multi-Tenant SaaS Features (Phases 1-3 Complete)

#### Phase 1: Role System & Team Management
- **5-Tier Role System UI**: Team Members page with role-based user management
  - All 5 roles available in dropdown (MSP Admin, MSP Technician, Company Admin, Company Employee, External Customer)
  - Legacy roles (owner, admin, member) mapped to new roles for display
- **Company Switcher**: Dropdown in admin sidebar for MSP users to switch between companies
  - Shows assigned companies for technicians
  - Persists selection in session storage
  - Only visible when companies exist with organization_id
- **Team Members Management**: Full CRUD for organization members
  - Invite member modal with role selection
  - Edit member role, phone, active status
  - Technician Assignments tab for MSP admin
- **Technician Assignment APIs**: 
  - `GET/POST/PUT/DELETE /api/org/technician-assignments`
  - Assign/unassign technicians to specific companies

#### Phase 2: Custom Domains
- **Custom Domains Page** (`/admin/custom-domains`):
  - Add custom domain with DNS TXT verification
  - Verification token generation
  - Domain status badges (Pending/Verified, SSL status)
  - Delete domain capability
- **Backend APIs**:
  - `GET/POST/DELETE /api/org/custom-domains`
  - `POST /api/org/custom-domains/verify` - DNS TXT record verification using dnspython

#### Phase 3: Email White-labeling
- **Email Settings Page** (`/admin/email-whitelabel`):
  - Enable/disable custom email sending toggle
  - SMTP Settings tab: Provider presets (SendGrid, Mailgun, SES, Gmail, etc.)
  - Sender Info tab: From email, from name, reply-to
  - Branding tab: Logo URL, primary color, footer text, "Powered by" toggle
  - Test email functionality
- **Backend APIs**:
  - `GET/PUT /api/org/email-settings` - SMTP configuration
  - `POST /api/org/email-settings/test` - Send test email

**All tests passed**: 100% backend (17/17) and frontend success rate

### 2026-01-30: P0 Signup Bug Fix & 4-Level SaaS Architecture (Complete)
- **P0 FIX: Signup Flow**: Fixed critical bug where signup created `organization_member` but not `admins` record
  - Now creates records in BOTH `admins` and `organization_members` collections
  - Login at `/api/auth/login` now works immediately after signup
  - Token includes organization context for proper tenant scoping
- **5-Tier Role System Implementation**: Added comprehensive role system to `OrganizationMember` model
  - `msp_admin`: Full tenant access, can manage all companies
  - `msp_technician`: Access to assigned companies only
  - `company_admin`: Admin of specific client company
  - `company_employee`: Regular company user
  - `external_customer`: Limited external access
- **Technician Assignment Model**: Created `/app/backend/models/technician_assignment.py` for granular MSP technician-to-company assignments
- **Platform Admin noindex**: Added SEO protection to prevent search engine indexing of platform admin pages
- **All tests passed**: 100% backend (16/16) and frontend success rate

### 2026-01-30: Subdomain-Based Multi-Tenancy (Complete)
- **Tenant Resolution Middleware**: Extracts tenant from subdomain, X-Tenant-Slug header, or ?_tenant query param
- **Tenant-Aware Login**: Login endpoint validates user belongs to resolved tenant
- **Cross-Tenant Protection**: Generic "Invalid credentials" error for cross-tenant login attempts (no information leakage)
- **Platform Admin Isolation**: Platform routes (/platform/*) completely separate from tenant routes
- **Frontend TenantProvider**: Resolves tenant context and applies branding
- **Tenant Error Pages**: Dedicated pages for suspended/not found workspaces
- **Admin Login Branding**: Shows tenant name, logo, workspace indicator when tenant context present
- **Dev Mode Support**: Query param fallback for local development
- **All tests passed**: 100% backend (16/16) and frontend success rate

### 2026-01-30: Platform Super Admin Portal Build-out (Complete)
- **Enhanced Dashboard**: Added MRR/ARR revenue metrics, new signups this month, trial conversion rate
- **Organizations Management**: Plan change capability in detail modal
- **Revenue & Billing Page**: Detailed revenue analytics by plan
- **Platform Admins Page**: Manage super admin users
- **Audit Logs Page**: Track all platform administrative actions with filters
- **Platform Settings Page**: 5-tab configuration (General, Signup & Trial, Email, Billing, Integrations)
- **Backend API Enhancement**: `/api/platform/dashboard/stats` now returns revenue metrics
- **All tests passed**: 100% backend (16/16) and frontend success rate

### 2026-01-30: Tenant Scoping Audit & Knowledge Base Completion
- **Complete Tenant Scoping**: Applied `organization_id` filter to ALL remaining admin endpoints:
  - Users (`list_users`)
  - Company Employees (`list_company_employees`)
  - Sites (`list_sites`)
  - Licenses (`list_licenses`)
  - Deployments (`list_deployments`)
  - Email/Cloud Subscriptions (`list_subscriptions`)
  - Asset Groups (`list_asset_groups`)
  - Accessories (`list_accessories`)
- **Knowledge Base System Completed**:
  - Added route `/admin/knowledge-base` in App.js
  - Added sidebar link under Settings in AdminLayout.js
  - Full CRUD functionality working for articles and categories
  - Tenant-scoped KB articles and categories

### Previous Updates
- **2026-01-30**: Complete Tenant Scoping & Tactical RMM Integration
- **2026-01-30**: MSP-Focused Landing Pages & Tenant Scoping
- **2026-01-30**: Beautiful SaaS Landing Pages Implementation
- **2026-01-30**: Multi-Tenant Admin Authentication Fix (P0 Blocker Resolved)
- **2026-01-30**: Editable Static Pages Implementation
- **2026-01-30**: Self-Signup & Razorpay Billing Implementation
- **2026-01-30**: Multi-tenant SaaS Architecture Implementation
- **2026-01-30**: Enhanced AMC Onboarding Wizard
- **2026-01-29**: Implemented comprehensive AMC Onboarding Wizard
- **2026-01-29**: Enterprise Ticketing System - All 4 Phases Complete

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
- ✅ **Knowledge Base System** (articles & categories with tenant scoping)

### Multi-Tenant Features (Complete)
- ✅ **Full Tenant Scoping on ALL Admin Routes**
- ✅ Platform Super Admin Layer
- ✅ Organization (Tenant) Model with data isolation
- ✅ Subscription Plans (Trial, Starter, Professional, Enterprise)
- ✅ White-Label UI (logo upload, color picker, custom domain)
- ✅ Organization Settings Page with all tabs functional

### Subdomain-Based Multi-Tenancy (Complete)
- ✅ Tenant Resolution Middleware (subdomain, header, query param)
- ✅ Tenant-Aware Login with cross-tenant protection
- ✅ Platform Admin completely isolated from tenant routes
- ✅ Frontend TenantProvider with branding support
- ✅ Tenant Error Pages (suspended, not found)
- ✅ Dev mode query param fallback

### Platform Super Admin Portal (Complete)
- ✅ Enhanced Dashboard with MRR/ARR/growth metrics
- ✅ Organizations Management with plan change capability
- ✅ Revenue & Billing analytics page
- ✅ Platform Admins management
- ✅ Audit Logs with action/entity filters
- ✅ Platform Settings (General, Signup, Email, Billing, Integrations)

### Enterprise Ticketing System (Complete - All 4 Phases)
- ✅ Core Ticket Model with SLA Engine
- ✅ Department System with auto-assignment
- ✅ Help Topics with auto-routing
- ✅ Custom Forms (dynamic forms per topic)
- ✅ Canned Responses with variable replacement
- ✅ Ticket Participants (CC/Collaboration)
- ✅ Email Integration (SMTP + IMAP)

### Multi-Tenant SaaS Features (Complete - All 3 Phases)
- ✅ **5-Tier Role System UI** - Team Members page with full role management
- ✅ **Company Switcher** - Sidebar dropdown for MSP users
- ✅ **Technician Assignment Management** - Assign technicians to companies
- ✅ **Custom Domains** - DNS TXT verification, domain status tracking
- ✅ **Email White-labeling** - Full SMTP configuration, sender info, branding

## Prioritized Backlog

### P0 - Critical (Complete)
- ✅ **Subdomain-Based Multi-Tenancy** - Full subdomain routing with data isolation
- ✅ **Tenant Scoping Audit** - All admin APIs now filter by organization_id
- ✅ **Knowledge Base System** - Full CRUD with tenant scoping
- ✅ **Platform Super Admin Portal** - Full build-out complete
- ✅ **P0 Signup Bug Fix** - Signup now creates records in both admins and organization_members collections
- ✅ **5-Tier Role System UI** - Complete with Team Members page
- ✅ **Company Switcher** - Complete with session persistence
- ✅ **Technician Assignment Management** - Complete with bulk assignment
- ✅ **Custom Domains** - Complete with DNS verification
- ✅ **Email White-labeling** - Complete with SMTP config and test email

### P1 - In Progress
- [ ] **Finalize Razorpay Integration** - Need API keys (KEY_ID, KEY_SECRET)
- [ ] **Finalize Tactical RMM Integration** - Need API URL & Key
- [ ] **SSL Automation for Custom Domains** - Server-level integration needed

### P2 - Upcoming
- [ ] Scheduled Email Sync - Background task for IMAP
- [ ] SLA Breach Checking - Automated background task
- [ ] Auto-Escalation for tickets
- [ ] Add Dashboard Screenshots to Features Page

### P3 - Future/Backlog
- [ ] Integrations for other RMMs (NinjaRMM, ConnectWise)
- [ ] PDF Export for service history reports
- [ ] Full Refactor of `server.py` into modular routes

## Tech Stack
- Frontend: React + Tailwind CSS + Shadcn/UI
- Backend: FastAPI + Motor (async MongoDB)
- Database: MongoDB
- AI: OpenAI GPT-4o-mini via emergentintegrations
- File Processing: pandas, openpyxl
- Security: slowapi (rate limiting), bcrypt (password hashing), JWT (authentication)
- DNS Verification: dnspython

## Key API Endpoints

### Tenant-Scoped Endpoints (All filtered by organization_id)
- `/api/admin/companies` - Company management
- `/api/admin/users` - User management
- `/api/admin/devices` - Device management
- `/api/admin/company-employees` - Employee management
- `/api/admin/sites` - Site management
- `/api/admin/licenses` - License management
- `/api/admin/deployments` - Deployment management
- `/api/admin/subscriptions` - Email/Cloud subscriptions
- `/api/admin/asset-groups` - Asset groups
- `/api/admin/accessories` - Accessories
- `/api/admin/services` - Service history
- `/api/admin/parts` - Parts inventory
- `/api/admin/amc-contracts` - AMC contracts
- `/api/admin/engineers` - Engineers

### Knowledge Base API
- `GET /api/kb/admin/categories` - List KB categories
- `POST /api/kb/admin/categories` - Create KB category
- `GET /api/kb/admin/articles` - List KB articles
- `POST /api/kb/admin/articles` - Create KB article
- `PUT /api/kb/admin/articles/{id}` - Update KB article
- `POST /api/kb/admin/articles/{id}/publish` - Publish article
- `GET /api/kb/public/articles` - Public articles

### Organization & White-Label
- `GET /api/org/current` - Get current organization
- `PUT /api/org/current/branding` - Update branding
- `PUT /api/org/current/settings` - Update settings

## Test Credentials
- Admin: admin@demo.com / admin123
- Company: jane@acme.com / company123
- Engineer: raj@example.com / password

## Test Reports
- `/app/test_reports/iteration_19.json` - Auth fix tests
- `/app/test_reports/iteration_20.json` - SaaS pages tests

## Code Architecture
```
/app
├── backend/
│   ├── models/
│   │   └── knowledge_base.py     # KB schema
│   ├── routes/
│   │   ├── knowledge_base.py     # KB API (tenant-scoped)
│   │   ├── tactical_rmm.py       # RMM integration
│   │   └── organization.py       # Org management
│   ├── services/
│   │   └── tactical_rmm.py       # RMM service
│   └── server.py                 # Main server (tenant scoping applied)
└── frontend/
    └── src/
        ├── pages/
        │   ├── admin/
        │   │   ├── KnowledgeBase.js      # KB management UI
        │   │   ├── OrganizationSettings.js # White-label UI
        │   │   └── TacticalRMMIntegration.js
        │   └── public/
        │       ├── LandingPage.js        # MSP-focused landing
        │       ├── FeaturesPage.js
        │       └── PricingPage.js
        ├── App.js                # Routes (KB route added)
        └── layouts/
            └── AdminLayout.js    # Sidebar (KB link added)
```

## Project Health Check
- **Working:**
  - All admin endpoints tenant-scoped ✅
  - Knowledge Base CRUD ✅
  - White-Label settings UI ✅
  - Enterprise Ticketing ✅
  - MSP-focused public website ✅
- **Blocked:**
  - Razorpay (needs API keys)
  - Tactical RMM (needs credentials)
- **Mocked:**
  - "Trusted By" logos on landing page (placeholders)
  - Features page (text-only, needs screenshots)
