# Warranty & Asset Tracking Portal - PRD

## Original Problem Statement
Build an enterprise-grade Warranty & Asset Tracking Portal with a highly configurable, master-driven, multi-workflow ticketing system with strict multi-tenant data isolation.

## What's Been Implemented

### Device Profitability Module (Mar 4, 2026) - NEW
- **Password-protected "Profitability" tab** in Analytics — owner-only access
- **Per-device cost calculation**: AMC Revenue vs (Labour + Travel + Parts) = Profit/Loss
- **Cost formula**: Labour = engineer hourly_rate × hours spent (configurable per engineer), Travel = zone-based tier system (configurable in Settings), Parts = actual parts cost from tickets. Remote calls estimated at 30min.
- **Engineer hourly_rate field** added to engineer profile (per-engineer override, falls back to system default)
- **Travel Cost Zones**: 4 configurable tiers (Local/City/Outstation/Long Distance) with distance ranges and flat costs
- **Company-level profitability rollup**: revenue vs cost per company, margin %
- **Drill-down**: expandable device rows showing call-by-call breakdown (type, date, engineer, hours, labour, travel, parts)
- **Testing: 100% (10/10 backend, all frontend verified)**

### Comprehensive Analytics Dashboard (Mar 4, 2026)
- **12-module analytics engine** (10 base + Executive Summary + Profitability):
  1. Ticket Intelligence (volume, stages, resolution, bottlenecks, heatmap)
  2. Workforce Performance (scorecards, FTF rate, utilization)
  3. Financial Analytics (quotation pipeline, revenue, aging)
  4. Client Health Score (composite 0-100, at-risk detection)
  5. Asset Intelligence (warranty timeline, failure rates, lifecycle)
  6. SLA Compliance (breach rates, trend, by priority/team)
  7. Workflow Analytics (stage cycle times, backlog, warranty types)
  8. Inventory & Parts (stock alerts, consumption, transactions)
  9. Contract & AMC (expiry pipeline, coverage rate)
  10. Operational Intelligence (AI trend prediction, anomaly alerts, recommendations)
  11. Executive Summary (8 KPIs with period-over-period change)
  12. Device Profitability (password-protected, cost analysis)
- **Testing: 100% across all modules**

### Previous Features (Feb-Mar 2026)
- P0 Features: Quotation Approval, Engineer Workflow Sync, Form Linking
- Help Topic System (8 categories, 43 topics, full CRUD)
- Warranty-Based Workflows (OEM/AMC/Non-Warranty, auto-detection)
- WhatsApp + Email Notifications, Admin Dashboard Redesign
- Engineer reschedule, visit workflow, inventory, pending bills, bulk upload

## Architecture
- Frontend: React + Tailwind + Shadcn/UI + Recharts
- Backend: FastAPI + Motor (MongoDB async)
- Database: MongoDB | Auth: JWT-based
- Analytics: In-memory cached aggregation (5min TTL) + password-protected profitability

## Prioritized Backlog

### P0 (Next)
- Multi-tenant Customer Facing Portal (portal.aftersales.support/{tenant_code}) with company-level analytics
- Form Builder UI (admin dynamic form creation/editing)
- Workflow Designer UI (visual workflow editor)
- Email Inbox UI (IMAP/SMTP)

### P1
- Full CRUD for SLAs, Priorities, Canned Responses
- Quotation PDF Generation
- Razorpay Integration

### P2
- CompanySwitcher for platform admins
- server.py refactor & User/Staff model unification
- ESLint warnings cleanup

## Credentials
- Admin: ck@motta.in / Charu@123@
- Test Engineer: test_engineer_1bfa72f0@test.com / Test@123
- Profitability Password: owner123
