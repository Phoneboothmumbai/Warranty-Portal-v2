"""
Routes module - Modular API endpoints

This module provides a modular structure for API routes.
Routes are being incrementally migrated from the monolithic server.py.

Currently Extracted Routes:
- public.py: Public endpoints (warranty search, settings, masters)
- auth.py: Authentication endpoints
- masters.py: Master data management
- webhooks.py: osTicket webhooks
- qr_service.py: QR code generation and quick service requests
- companies.py: Company management + bulk imports + portal users

Pending Migration (still in server.py):
- users, employees, devices, services, parts, amc, sites
- deployments, search, settings, licenses, dashboard
- engineer, subscriptions, asset_groups, company_portal
- internet_services, credentials, supplies
"""
from fastapi import APIRouter

# Create main router that will include all sub-routers
api_router = APIRouter(prefix="/api")

# Import completed route modules
from .public import router as public_router
from .auth import router as auth_router
from .masters import router as masters_router
from .webhooks import router as webhooks_router
from .qr_service import router as qr_service_router
from .companies import router as companies_router

# Include completed routers
api_router.include_router(public_router)
api_router.include_router(auth_router)
api_router.include_router(masters_router)
api_router.include_router(webhooks_router)
api_router.include_router(qr_service_router)
api_router.include_router(companies_router)

# Note: Remaining routes are still in server.py
# They will be migrated incrementally
