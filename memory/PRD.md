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

### Recent Additions (Dec 2024)
- ✅ Device User & Configuration feature (conditional config field for laptops/desktops/tablets)
- ✅ Company Employee management with bulk Excel/CSV upload
- ✅ Email & Cloud Subscriptions module (admin side complete)

## Prioritized Backlog

### P0 - Critical
- ✅ DONE: Fix numpy deployment issue (changed to 1.26.4 for Python 3.10)
- ✅ DONE: Complete Subscriptions module frontend integration

### P1 - High Priority
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
- `/api/admin/subscriptions` - Full CRUD for email subscriptions
- `/api/admin/company-employees` - Employee management with bulk upload
- `/api/company/subscriptions` - Company view of their subscriptions
- `/api/company/subscriptions/{id}/tickets` - Raise support tickets

## Test Credentials
- Admin: admin@demo.com / admin123
- Company: jane@acme.com / company123
- Engineer: raj@example.com / password
