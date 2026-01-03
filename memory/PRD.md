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

## Upcoming Tasks
- P1: Admin & User Role Management (Super Admin, Admin, Staff, Service Engineer)
- P2: Engineer Field Visit Support

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
- Customer login portal
- Fix eslint/lint warnings
