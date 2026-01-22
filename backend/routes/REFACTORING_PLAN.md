# Backend Routes Refactoring Plan

## Overview
The `server.py` file has grown to 8500+ lines with 207 endpoints across 29 sections.
This document outlines the plan for incremental refactoring into a modular `routes/` structure.

## Current Status (Phase 1 Complete)

### Extracted Routes (Ready to Use)
These route files are complete and can be used when server.py is refactored:

1. **routes/public.py** - Public endpoints
   - `GET /` - Root endpoint
   - `GET /settings/public` - Public settings
   - `GET /masters/public` - Public masters
   - `GET /warranty/search` - Warranty search (devices + parts)
   - `GET /warranty/pdf/{serial_number}` - PDF generation

2. **routes/auth.py** - Authentication
   - `POST /auth/login` - Admin login
   - `GET /auth/me` - Current admin info
   - `POST /auth/setup` - First admin setup

3. **routes/masters.py** - Master data management
   - `GET /admin/masters` - List masters
   - `POST /admin/masters` - Create master
   - `PUT /admin/masters/{id}` - Update master
   - `DELETE /admin/masters/{id}` - Disable master
   - `POST /admin/masters/seed` - Seed defaults
   - `POST /admin/masters/quick-create` - Quick create

4. **routes/webhooks.py** - osTicket webhooks
   - `POST /webhooks/osticket` - Webhook handler
   - `GET /webhooks/osticket/test` - Test endpoint

5. **routes/qr_service.py** - QR codes and quick service
   - `GET /device/{identifier}/qr` - Single QR PDF
   - `POST /devices/bulk-qr-pdf` - Bulk QR PDF
   - `GET /device/{identifier}/info` - Public device info
   - `POST /device/{identifier}/quick-request` - Quick service request

6. **routes/companies.py** - Company management
   - Full CRUD for companies
   - Company overview (360° view)
   - Portal users management
   - Bulk imports (companies, sites, devices, products)

### Pending Migration (Still in server.py)
These sections need to be extracted:

- `ADMIN ENDPOINTS - USERS` (lines 1907-2008)
- `ADMIN ENDPOINTS - COMPANY EMPLOYEES` (lines 2010-2350)
- `ADMIN ENDPOINTS - DEVICES` (lines 2350-2760)
- `SERVICE HISTORY ENDPOINTS` (lines 2758-2885)
- `ADMIN ENDPOINTS - PARTS` (lines 2885-2947)
- `ADMIN ENDPOINTS - AMC` (lines 2947-3003)
- `AMC V2 CONTRACTS (Enhanced)` (lines 3003-3337)
- `ADMIN ENDPOINTS - SITES` (lines 3337-3505)
- `ADMIN ENDPOINTS - DEPLOYMENTS` (lines 3505-3926)
- `UNIVERSAL SEARCH` (lines 3926-4158)
- `ADMIN ENDPOINTS - SETTINGS` (lines 4158-4197)
- `ADMIN ENDPOINTS - LICENSES` (lines 4197-4407)
- `ADMIN ENDPOINTS - AMC DEVICE ASSIGNMENTS` (lines 4407-4607)
- `ADMIN DASHBOARD WITH ALERTS` (lines 4607-4785)
- `ENGINEER PORTAL ENDPOINTS` (lines 4785-5231)
- `ADMIN ENDPOINTS - EMAIL SUBSCRIPTIONS` (lines 5231-5626)
- `ASSET GROUPS & ACCESSORIES` (lines 5626-6096)
- `COMPANY PORTAL ENDPOINTS` (lines 6096-7945)
- `INTERNET SERVICES / ISP ENDPOINTS` (lines 7945-8036)
- `CREDENTIALS DASHBOARD ENDPOINTS` (lines 8036-8121)
- `OFFICE SUPPLIES ADMIN ENDPOINTS` (lines 8121-8281)
- `OFFICE SUPPLIES COMPANY ENDPOINTS` (lines 8281-8501)

## Migration Steps (For Future Work)

### Step 1: Extract Users Route
```python
# routes/users.py
# Extract from server.py lines 1907-2008
```

### Step 2: Extract Employees Route
```python
# routes/employees.py
# Extract from server.py lines 2010-2350
```

### Step 3: Extract Devices Route
```python
# routes/devices.py
# Extract from server.py lines 2350-2760
```

... (continue for each section)

### Final Step: Update server.py
```python
# Replace monolithic server.py with:
from routes import api_router
app.include_router(api_router)
```

## Benefits of Refactoring
1. **Maintainability**: Easier to find and modify specific endpoints
2. **Testing**: Can test routes in isolation
3. **Code Review**: Smaller files are easier to review
4. **Team Collaboration**: Multiple developers can work on different routes
5. **Performance**: Faster IDE performance with smaller files

## File Structure After Complete Migration
```
/app/backend/
├── routes/
│   ├── __init__.py      # Combines all routers
│   ├── public.py        # ✅ Complete
│   ├── auth.py          # ✅ Complete
│   ├── masters.py       # ✅ Complete
│   ├── webhooks.py      # ✅ Complete
│   ├── qr_service.py    # ✅ Complete
│   ├── companies.py     # ✅ Complete
│   ├── users.py         # Pending
│   ├── employees.py     # Pending
│   ├── devices.py       # Pending
│   ├── services.py      # Pending
│   ├── parts.py         # Pending
│   ├── amc.py           # Pending
│   ├── sites.py         # Pending
│   ├── deployments.py   # Pending
│   ├── search.py        # Pending
│   ├── settings.py      # Pending
│   ├── licenses.py      # Pending
│   ├── dashboard.py     # Pending
│   ├── engineer.py      # Pending
│   ├── subscriptions.py # Pending
│   ├── asset_groups.py  # Pending
│   ├── company_portal.py # Pending
│   ├── internet_services.py # Pending
│   ├── credentials.py   # Pending
│   └── supplies.py      # Pending
├── server.py            # Minimal, just imports routes
├── server_original.py   # Backup of original monolithic server
└── ...
```

## Notes
- All extracted routes follow the same patterns as the original
- No functional changes - just organizational
- Tests should pass without modification after full migration
