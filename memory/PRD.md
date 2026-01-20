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
- ✅ **Collapsible/Grouped Sidebar Navigation** - Admin portal sidebar now groups navigation items into collapsible sections:
  - Organization (Companies, Sites, Users, Employees)
  - Assets (Devices, Accessories, Asset Groups, Parts, Deployments)
  - Contracts & Licenses (Licenses, AMC Contracts, Subscriptions, Service History)
  - Office Supplies (Products, Orders)
  - Settings (Master Data, Settings)
- ✅ **Asset Transfer Feature** - Admins can transfer devices between employees with:
  - POST /api/admin/asset-transfers endpoint
  - GET /api/admin/asset-transfers history endpoint
  - Transfer modal in Devices page
  - Support for transfer with reason, date, notes
  - Support for unassigning devices (to_employee_id = null)
- ✅ Dynamic subscription dropdowns from Master Data
- ✅ Subscription user change tracking with history

## Prioritized Backlog

### P0 - Critical (In Progress)
- [ ] Build out **Asset Groups/Bundles** - Full CRUD UI for grouping devices (e.g., Desktop = CPU + Monitor + Keyboard)
- [ ] Build out **Renewal Alerts Dashboard** - Backend API + Frontend to track expiring warranties/AMCs/licenses

### P1 - High Priority
- [ ] Complete **Accessories & Peripherals Module** - Backend model, CRUD APIs, and frontend UI
- [ ] Add two location fields to devices: `site` and `office_location`
- [ ] Enhanced Employee search page (search by name/email/phone, company filtering)
- [ ] Company-side Subscriptions page with "Raise Ticket" feature

### P2 - Medium Priority  
- [ ] Engineer Field Visit workflow mobile UI
- [ ] Admin & User Role Management (RBAC)
- [ ] Linting cleanup (eslint, backend lint warnings)

### P3 - Low Priority/Future
- [ ] PDF Export for service history reports
- [ ] Backend route refactoring (move handlers from server.py to routes/)
- [ ] Email notifications

## Tech Stack
- Frontend: React + Tailwind CSS + Shadcn/UI
- Backend: FastAPI + Motor (async MongoDB)
- Database: MongoDB
- AI: OpenAI GPT-4o-mini via emergentintegrations
- File Processing: pandas, openpyxl

## Key API Endpoints
- `/api/admin/asset-transfers` - Asset transfer between employees
- `/api/admin/subscriptions` - Full CRUD for email subscriptions
- `/api/admin/company-employees` - Employee management with bulk upload
- `/api/admin/employees/{emp_id}/details` - Comprehensive employee view
- `/api/admin/devices/{device_id}` - Device details with AMC info
- `/api/company/subscriptions` - Company view of their subscriptions
- `/api/company/subscriptions/{id}/tickets` - Raise support tickets

## Test Credentials
- Admin: admin@demo.com / admin123
- Company: jane@acme.com / company123
- Engineer: raj@example.com / password

## Test Reports
- `/app/test_reports/iteration_11.json` - Sidebar & Asset Transfer tests (14/14 passed)
