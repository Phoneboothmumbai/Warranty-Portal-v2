# Warranty & Asset Tracking Portal - PRD

## Original Problem Statement
Build an enterprise-grade Warranty & Asset Tracking Portal with:
- Public warranty search portal
- Comprehensive admin panel with JWT authentication
- Management of Companies, Users, Devices, Parts, and AMC (Annual Maintenance Contract) data

## Current Status: DEPLOYED & LIVE
- **Production URL:** http://65.20.78.143
- **Admin Credentials:** ck@motta.in / admin123

## What's Been Implemented

### Phase 1 (MVP) - COMPLETED
- Public warranty search by serial number/asset tag
- Admin authentication (JWT)
- CRUD for Companies, Users, Devices, Parts
- Service history tracking

### Phase 2A (Foundation Components) - COMPLETED
- SmartSelect component for searchable dropdowns
- DateDurationInput component for date/duration entry
- Quick-create APIs for inline master creation

### Phase 2B (Core Modules) - COMPLETED
- Software & License Management module
- "Request Support" CTA on warranty page

### P0 (Architecture Fixes) - COMPLETED
- AMC as first-class entity via `amc_device_assignments` join table
- AMC status reflected in device views and warranty checks
- AMC override rule (AMC coverage takes precedence over device warranty)

### Vultr Deployment - COMPLETED (Jan 2, 2026)
- Full deployment on Ubuntu server
- Nginx reverse proxy configured
- Systemd service for backend
- MongoDB with admin user created

## Database Schema (Key Collections)
- `admins` - Admin users for login
- `companies`, `users`, `devices`, `parts`
- `amc_contracts` - AMC contract definitions
- `amc_device_assignments` - Links devices to AMC contracts (requires `id` field)
- `licenses`, `software_products`
- `service_history`

## Known Issues Fixed This Session
1. **bcrypt compatibility** - Downgrade to bcrypt==4.0.1
2. **Wrong database** - Backend uses `warranty_portal`, not `warranty_db`
3. **Wrong collection** - Login uses `admins`, not `users`
4. **AMC not showing** - `amc_device_assignments` needs `id` field (not just `assignment_id`)

## Recent Updates (Jan 4, 2026)
- **Parts Page:** Added SmartSelect dropdowns with search for Device and Part Name, plus "Add New Part Type" option and optional Serial Number field
- **Deployments Page:** Added SmartSelect dropdowns with search for Company, Site, Category (with "Add New"), and Brand (with "Add New")
- **PDF Export:** Fixed AMC details not showing in warranty PDF download
- **Company Login Portal (COMPLETED):**
  - Full authentication system (login, registration with company code)
  - Dashboard with stats (devices, warranties, AMC, tickets)
  - Devices page with search/filter and detail view
  - Warranty & Coverage page with expiry tracking
  - Service Requests page (create, view, add comments)
  - AMC Contracts page
  - Deployments page
  - Users/Contacts page
  - Sites page
  - Profile page with password change
  - All tested with 22/22 backend tests passing

## Recent Updates (Jan 9, 2026)
- **Order Consumables Feature (COMPLETED):**
  - Admin Panel: Added consumable fields (Type, Model/Part No, Brand, Notes) to Device form - visible when device type is "Printer"
  - Company Portal: Added "Order Consumables" button on device details page for printers
  - Company Portal: Order modal with quantity and notes fields
  - Backend: `POST /api/company/devices/{device_id}/order-consumable` endpoint creates order in `consumable_orders` collection
  - Backend: osTicket integration sends detailed order request ticket (IP-restricted to production server)
  - All 11 backend API tests passing
  - All frontend UI features verified working

- **Multi-Consumable Support Enhancement (COMPLETED):**
  - Admin Panel: Can add MULTIPLE consumables per printer (Black, Cyan, Magenta, Yellow toners)
  - Each consumable has: Name, Type, Model/Part No., Color, Brand, Notes
  - Company Portal: Shows list of all available consumables with checkboxes
  - Company Portal: Users select which consumables to order with individual quantities
  - Order Summary shows total items and units
  - osTicket ticket includes table of all ordered items
  - Backward compatible - legacy single-item orders still work
  - All 13 backend API tests passing (100%)
  - All frontend UI features verified working

- **Office Supplies Feature (COMPLETED):**
  - **Company Portal** (`/company/office-supplies`):
    - Catalog view with categories (Stationery, Printer Consumables)
    - **Search bar** to filter products across categories
    - Add items to cart with +/- quantity controls
    - "View Cart" button appears when items are added
    - Place Order modal with delivery location selection
    - Can use registered site OR enter new address
    - Notes/Special Instructions field for urgent requests
    - My Orders tab shows order history with status
  - **Admin Panel** (`/admin/supply-products`, `/admin/supply-orders`):
    - Supply Products page: Manage categories and products
    - Categories section with inline edit/delete
    - Products table with status toggle, search, filter by category
    - Supply Orders page: View all orders with status cards
    - Filter by status, company, search by order number
    - Update order status (Requested → Approved → Processing → Delivered)
    - Add admin notes to orders
    - Order details modal with full information
  - **Backend:**
    - Auto-seeded 2 categories, 16 products on startup
    - osTicket integration for order tickets
    - Full CRUD APIs for categories, products, orders
  - **Testing:** 22/22 backend tests passed (100%)

- **Bulk Import Feature (COMPLETED):**
  - **Reusable BulkImport Component** (`/app/frontend/src/components/ui/bulk-import.jsx`)
  - **Admin Panel Pages with Bulk Import:**
    - Companies: CSV import with template download
    - Sites: Import linked to companies by code or name
    - Devices: Import linked to companies by code or name
    - Supply Products: Import with auto-create category
  - **Features:**
    - Download CSV template with sample data
    - Preview data before import
    - Validation errors shown per row
    - Import progress and results summary
    - Duplicate detection (company code, serial numbers)
  - **Testing:** 17/17 backend tests passed (100%)

## Company Portal Credentials
- **URL:** /company/login
- **Test Company Code:** ACME001
- **Test User:** jane@acme.com / company123

## Upcoming Tasks (Updated Jan 10, 2026)
- P1: Complete Engineer Field Visit Workflow (check-in/out, actions, parts, photos)
- P1: Admin & User Role Management (Super Admin, Admin, Staff, Service Engineer)
- P2: Email Notifications (ticket updates, warranty alerts)
- P3: Company Portal Email Notifications

## Phase 2C: Bulk Import System (Next Phase)
All bulk imports will include: Download Template → Upload & Preview → Validation → Confirm & Import → Summary

### High Priority
| Entity | Import Fields |
|--------|---------------|
| **Devices** | Serial No, Asset Tag, Brand, Model, Company, Site, Purchase Date, Warranty End |
| **Companies** | Name, Contact Person, Email, Phone, Address, GST No |
| **Users/Contacts** | Name, Email, Phone, Department, Company, Site |
| **AMC Device Assignments** | AMC Contract ID, Device Serial Numbers |

### Medium Priority
| Entity | Import Fields |
|--------|---------------|
| **Parts** | Part Name, Serial No, Device Serial, Warranty End, Supplier |
| **Sites/Locations** | Site Name, Company, Address, Contact |
| **Licenses** | Software Name, License Key, Seats, Company, Expiry Date |
| **Service History** | Device Serial, Service Date, Type, Notes, Technician |

### Low Priority (Master Data)
| Entity | Import Fields |
|--------|---------------|
| **Device Types** | Name |
| **Brands** | Name |
| **Models** | Name, Brand |
| **Software Products** | Name, Vendor |

**File Formats:** Both CSV and Excel (.xlsx)

## Future/Backlog
- WhatsApp Integration
- PDF Export for Service History
- Fix eslint/lint warnings (P2)

## QR Code Asset Labels & Quick Service Request (COMPLETED - Jan 9, 2026)
New feature for IT teams to quickly access device info and report issues via QR scan.

### Features Implemented
1. **QR Code Generation**
   - Endpoint: `GET /api/device/{serial}/qr` returns PNG QR code
   - QR links to public device page `/device/{serial}`
   - Custom size support via `?size=` parameter
   - Admin can download QR from Devices page dropdown menu

2. **Public Device Page** (`/device/:identifier`)
   - Shows device details, warranty status, AMC coverage
   - Displays recent service history
   - Shows replaced parts with warranty status
   - No login required

3. **Quick Service Request (No Login)**
   - Endpoint: `POST /api/device/{serial}/quick-request`
   - Form: Name, Email, Phone (optional), Issue Category, Description
   - Creates ticket with QSR- prefix (e.g., QSR-20260109-ABC123)
   - Stores in `quick_service_requests` collection
   - Integrates with osTicket (IP restricted to production)

### Backend Test Results
- 20/20 tests passed (100%)
- Test file: `/app/tests/test_qr_code_quick_request.py`

## Backend Refactoring (COMPLETED - Jan 9, 2026)
The monolithic `server.py` has been refactored into a modular architecture:

### New Structure
```
/app/backend/
├── server.py              # Main server (routes only, ~5300 lines)
├── config.py              # Environment variables & constants
├── database.py            # MongoDB connection
├── models/                # Pydantic models
│   ├── auth.py            # Token, AdminUser
│   ├── common.py          # MasterItem, AuditLog, Settings
│   ├── company.py         # Company, User, CompanyUser
│   ├── device.py          # Device, Part, ConsumableOrder
│   ├── service.py         # ServiceTicket, ServiceHistory
│   ├── amc.py             # AMC, AMCContract
│   ├── site.py            # Site, Deployment
│   ├── license.py         # License
│   └── supplies.py        # SupplyCategory, SupplyProduct, SupplyOrder
├── services/              # Business logic
│   ├── auth.py            # Auth helpers (password hashing, JWT)
│   ├── osticket.py        # osTicket integration
│   └── seeding.py         # Default data seeding
└── utils/
    └── helpers.py         # Utility functions (IST time, warranty calc)
```

### Benefits
- **Reduced main file**: From 6547 lines to 5314 lines (~19% reduction)
- **Better maintainability**: Models, services, and utilities are now separate
- **Easier testing**: Individual modules can be unit tested
- **Clearer separation of concerns**: Config, DB, models, services all isolated

## osTicket Manual Sync Feature (REMOVED - Jan 11, 2026)
Feature was removed as osTicket's standard API doesn't support reading tickets without additional plugins.
- The "Ticket #" badge still displays the osTicket reference number on ticket details page

## AI Support Triage Bot (COMPLETED - Jan 11, 2026)
AI-powered chatbot that helps users troubleshoot issues BEFORE creating support tickets.

### Flow
1. User clicks "New Request" → AI Chat modal opens
2. AI greets user and asks about their issue
3. User describes problem → AI provides troubleshooting steps
4. If resolved → User clicks "Issue Resolved" → No ticket created
5. If not resolved → User clicks "Create Ticket" → Ticket form pre-filled with AI conversation

### Features Implemented
1. **Backend AI Service** (`backend/services/ai_support.py`)
   - Uses GPT-4o-mini via Emergent LLM Key
   - Context-aware: knows about selected device/warranty info
   - Escalation detection: suggests creating ticket when needed
   - System prompt optimized for IT support troubleshooting

2. **Backend Endpoints**
   - `POST /api/company/ai-support/chat` - Send message, get AI response
   - `POST /api/company/ai-support/generate-summary` - Generate ticket subject/description from chat

3. **Frontend AI Chat Modal** (`frontend/src/components/AISupportChat.js`)
   - Purple-themed chat interface
   - Device selector dropdown (optional context)
   - "Skip to ticket" option for users who want to bypass AI
   - "Issue Resolved" and "Create Ticket" buttons appear after 3+ messages
   - Pre-fills ticket form with AI conversation when escalating

### Test Results
- 10/10 backend tests passed
- 100% frontend UI tests passed
- Full end-to-end flow verified

### Benefits
- Reduces L1 support ticket volume
- Users get instant help for common issues
- Tickets include troubleshooting context for technicians

## Individual QR Download Bug Fix (COMPLETED - Jan 10, 2026)
Fixed recurring bug where clicking "Download QR Code" for single device downloaded all devices.

### Issue
- User reported that individual QR download was downloading bulk QR PDF with all devices
- Root cause: Simple link approach didn't properly handle blob response

### Fix Applied
- Changed `handleDownloadQR` function in `Devices.js` to use axios blob approach
- Same pattern as bulk QR download - fetch blob, create object URL, trigger download
- PDF size verified: ~8.8KB for single device vs ~23KB for 3 devices

### Test Results
- Individual QR download returns correct PDF (8,835 bytes)
- PDF filename contains serial number
- Frontend dropdown option works correctly
- Success toast notification shows

## Engineer Field Visit Portal (In Progress)
Foundation built for service engineers to manage assigned tickets and field visits.

### Completed
- Backend models for Engineers and Field Visits
- Engineer authentication (login/register)
- Mobile-friendly Engineer Dashboard (list assigned tickets)
- Public route `/engineer` for login

### Pending
- Check-in/Check-out forms for site visits
- Action logging (work performed)
- Parts used tracking
- Photo upload for completed work
- Admin ticket assignment UI

## Upcoming Tasks (Priority Order)
1. **P1: Complete Engineer Field Visit Workflow**
   - Check-in/out forms, action logs, parts tracking, photo uploads
   - Admin UI to assign tickets to engineers

2. **P1: Admin & User Role Management**
   - Role-based access control (Super Admin, Admin, Staff, Service Engineer)
   - Permission system for different user types

3. **P2: Email Notifications**
   - Ticket status updates
   - Warranty expiry alerts
   - Order confirmations

## Future/Backlog
- WhatsApp Integration (user deferred)
- PDF Export for Service History
- Warranty Expiry Dashboard (calendar view)
- Backend route refactoring (move routes from server.py to routes/ directory)
- Fix eslint/lint warnings
