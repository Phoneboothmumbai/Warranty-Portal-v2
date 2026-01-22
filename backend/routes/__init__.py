"""
Routes module - Modular API endpoints
"""
from fastapi import APIRouter

# Create main router that will include all sub-routers
api_router = APIRouter(prefix="/api")

# Import and include all route modules
from .public import router as public_router
from .auth import router as auth_router
from .masters import router as masters_router
from .companies import router as companies_router
from .users import router as users_router
from .employees import router as employees_router
from .devices import router as devices_router
from .services import router as services_router
from .parts import router as parts_router
from .amc import router as amc_router
from .sites import router as sites_router
from .deployments import router as deployments_router
from .search import router as search_router
from .settings import router as settings_router
from .licenses import router as licenses_router
from .dashboard import router as dashboard_router
from .engineer import router as engineer_router
from .subscriptions import router as subscriptions_router
from .asset_groups import router as asset_groups_router
from .company_portal import router as company_portal_router
from .internet_services import router as internet_services_router
from .credentials import router as credentials_router
from .supplies import router as supplies_router
from .webhooks import router as webhooks_router
from .qr_service import router as qr_service_router

# Include all routers
api_router.include_router(public_router)
api_router.include_router(auth_router)
api_router.include_router(masters_router)
api_router.include_router(companies_router)
api_router.include_router(users_router)
api_router.include_router(employees_router)
api_router.include_router(devices_router)
api_router.include_router(services_router)
api_router.include_router(parts_router)
api_router.include_router(amc_router)
api_router.include_router(sites_router)
api_router.include_router(deployments_router)
api_router.include_router(search_router)
api_router.include_router(settings_router)
api_router.include_router(licenses_router)
api_router.include_router(dashboard_router)
api_router.include_router(engineer_router)
api_router.include_router(subscriptions_router)
api_router.include_router(asset_groups_router)
api_router.include_router(company_portal_router)
api_router.include_router(internet_services_router)
api_router.include_router(credentials_router)
api_router.include_router(supplies_router)
api_router.include_router(webhooks_router)
api_router.include_router(qr_service_router)
