# Warranty & Asset Tracking Portal - PRD

## Project Overview
Multi-tenant SaaS platform for warranty management, asset tracking, and service operations.

## User Personas
- **Platform Admin**: Full system access, manages organizations
- **Company Admin**: Manages their organization's assets, tickets, and staff
- **Technician/Engineer**: Handles service visits, ticket resolution

## Core Requirements

### 1. Company & Contact Management ✅
- Multi-tenant company management
- Contact persons per company
- Site/location management

### 2. Device & Asset Management ✅
- Device catalog and tracking
- Asset tagging and grouping
- Device model catalog

### 3. Service & Inventory Module (NEW - PHASE 1 COMPLETE) ✅
**Backend APIs Complete:**
- Problem Master - Problem types/categories (8 default types seeded)
- Item Master - Parts/items catalog with pricing
- Inventory Location - Warehouses, vans, offices, etc.
- Stock Ledger - Immutable ledger for all stock movements
- Vendor Master - Vendor management with item-price mappings
- Service Tickets (New) - 7-state lifecycle (NEW → ASSIGNED → IN_PROGRESS → PENDING_PARTS → COMPLETED → CLOSED, CANCELLED)
- Service Visits - Multi-visit per ticket with timer functionality
- Ticket Parts - Parts request, approval, and issuance workflow

**Test Results:** 65/65 tests passed (100%)

### 4. AMC Contracts ✅
- Annual maintenance contract management
- Renewal tracking and alerts

### 5. Staff Management ✅
- Employee/technician management
- Role-based access control
- Department management

## What's Been Implemented

### Backend (Phase 1 - Service Module) - December 2025
| Feature | Status | Test Coverage |
|---------|--------|---------------|
| Problem Master API | ✅ Complete | 7 tests |
| Item Master API | ✅ Complete | 8 tests |
| Inventory Location API | ✅ Complete | 6 tests |
| Stock Ledger API | ✅ Complete | 5 tests |
| Vendor Master API | ✅ Complete | 8 tests |
| Service Tickets (New) API | ✅ Complete | 12 tests |
| Service Visits API | ✅ Complete | 9 tests |
| Ticket Parts API | ✅ Complete | 9 tests |
| Stock Transfer API | ✅ Complete | 1 test |

### API Endpoints Reference
```
# Problem Master
GET/POST /api/admin/problems
GET/PUT/DELETE /api/admin/problems/{id}
POST /api/admin/problems/seed

# Item Master
GET/POST /api/admin/items
GET/PUT/DELETE /api/admin/items/{id}
GET /api/admin/items/{id}/stock
GET /api/admin/items/search

# Inventory
GET/POST /api/admin/inventory/locations
GET/PUT/DELETE /api/admin/inventory/locations/{id}
GET /api/admin/inventory/stock
POST /api/admin/inventory/stock/transfer
POST /api/admin/inventory/stock/adjustment
GET /api/admin/inventory/ledger

# Vendors
GET/POST /api/admin/vendors
GET/PUT/DELETE /api/admin/vendors/{id}
POST /api/admin/vendors/{id}/items
GET /api/admin/vendors/for-item/{item_id}

# Service Tickets (New)
GET/POST /api/admin/service-tickets
GET/PUT/DELETE /api/admin/service-tickets/{id}
GET /api/admin/service-tickets/stats
POST /api/admin/service-tickets/{id}/assign
POST /api/admin/service-tickets/{id}/start
POST /api/admin/service-tickets/{id}/pending-parts
POST /api/admin/service-tickets/{id}/complete
POST /api/admin/service-tickets/{id}/close
POST /api/admin/service-tickets/{id}/cancel
POST /api/admin/service-tickets/{id}/comments

# Service Visits
GET/POST /api/admin/visits
GET/PUT/DELETE /api/admin/visits/{id}
GET /api/admin/visits/today
GET /api/admin/visits/technician/{id}
POST /api/admin/visits/{id}/start-timer
POST /api/admin/visits/{id}/stop-timer
POST /api/admin/visits/{id}/add-action

# Ticket Parts
GET/POST /api/admin/ticket-parts/requests
GET /api/admin/ticket-parts/requests/pending
GET /api/admin/ticket-parts/requests/{id}
POST /api/admin/ticket-parts/requests/{id}/approve
DELETE /api/admin/ticket-parts/requests/{id}
GET/POST /api/admin/ticket-parts/issues
GET /api/admin/ticket-parts/issues/{id}
POST /api/admin/ticket-parts/issues/{id}/return
```

## Prioritized Backlog

### P0 - In Progress
- **Frontend for Service Module**: Create UI for new service tickets, visits, inventory, vendors

### P1 - Next
- Service Module Phase 2: Automated vendor communication, Quotation PDFs, Invoice generation
- RMM Integration with Tactical RMM
- Razorpay payments finalization

### P2 - Future
- Fix ESLint warnings in frontend
- CompanySwitcher component
- server.py refactoring
- AI Ticket Summary completion

## Technical Architecture
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Backend**: FastAPI + Python 3.11
- **Database**: MongoDB with motor async driver
- **Authentication**: JWT tokens
- **Multi-tenancy**: organization_id scoping

## Key Data Models (New)
- `ProblemMaster` - Problem/issue type definitions
- `ItemMaster` - Parts/items catalog
- `InventoryLocation` - Physical/logical stock locations
- `StockLedger` - Immutable stock movement records
- `VendorMaster` - Vendor/supplier management
- `VendorItemMapping` - Vendor-item price mappings
- `ServiceTicketNew` - Service ticket (new 7-state model)
- `ServiceVisitNew` - Visit records with timer
- `TicketPartRequest` - Parts request from tickets
- `TicketPartIssue` - Parts issued to tickets

## Test Reports
- Latest: /app/test_reports/iteration_31.json (65/65 tests passed)

## Credentials
- Admin: ck@motta.in / Charu@123@
