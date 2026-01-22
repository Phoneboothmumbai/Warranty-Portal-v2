"""
Warranty & Asset Tracking Portal - Main Server
==============================================
This server uses a modular architecture with routes being
incrementally extracted into the routes/ directory.

Extracted Routes (see routes/__init__.py):
- public, auth, masters, webhooks, qr_service, companies

Remaining routes in this file will be migrated incrementally.
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Query
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from typing import List, Optional, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import base64
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import shutil
import json
import qrcode
from pydantic import BaseModel, Field

# Import from modular structure
from config import ROOT_DIR, UPLOAD_DIR, OSTICKET_URL, OSTICKET_API_KEY, SECRET_KEY, ALGORITHM, IST
from database import db, client
from utils.helpers import get_ist_now, get_ist_isoformat, calculate_warranty_expiry, is_warranty_active, days_until_expiry
from services.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_admin, get_current_company_user, require_company_admin,
    log_audit, security
)
from services.osticket import create_osticket
from services.seeding import seed_default_masters, seed_default_supplies

# Import all models
from models.auth import Token, AdminUser, AdminLogin, AdminCreate
from models.common import MasterItem, MasterItemCreate, MasterItemUpdate, AuditLog, Settings, SettingsUpdate
from models.company import (
    Company, CompanyCreate, CompanyUpdate,
    User, UserCreate, UserUpdate,
    CompanyUser, CompanyUserCreate, CompanyUserUpdate,
    CompanyUserRegister, CompanyLogin,
    CompanyEmployee, CompanyEmployeeCreate, CompanyEmployeeUpdate
)
from models.device import (
    ConsumableItem, Device, DeviceCreate, DeviceUpdate,
    AssignmentHistory, Part, PartCreate, PartUpdate,
    ConsumableOrderItem, ConsumableOrder
)
from models.service import (
    ServiceTicket, ServiceTicketCreate, ServiceTicketComment,
    RenewalRequest, RenewalRequestCreate,
    ServiceAttachment, ServiceHistory, ServiceHistoryCreate, ServiceHistoryUpdate,
    ServicePartUsed
)
from models.amc import (
    AMC, AMCCreate, AMCUpdate,
    AMCCoverageIncludes, AMCExclusions, AMCEntitlements, AMCAssetMapping,
    AMCContract, AMCContractCreate, AMCContractUpdate,
    AMCUsageRecord, AMCDeviceAssignment, AMCDeviceAssignmentCreate,
    AMCBulkAssignmentPreview
)
from models.site import (
    Site, SiteCreate, SiteUpdate,
    DeploymentItem, Deployment, DeploymentCreate, DeploymentUpdate
)
from models.license import License, LicenseCreate, LicenseUpdate
from models.supplies import (
    SupplyCategory, SupplyCategoryCreate, SupplyCategoryUpdate,
    SupplyProduct, SupplyProductCreate, SupplyProductUpdate,
    SupplyOrderItem, SupplyOrderLocation, SupplyOrder
)
from models.subscription import (
    EmailSubscription, EmailSubscriptionCreate, EmailSubscriptionUpdate,
    SubscriptionTicket, SubscriptionTicketCreate
)
from models.internet_service import (
    InternetService, InternetServiceCreate, InternetServiceUpdate
)

# Import modular routes
from routes import api_router as modular_api_router

# Create the main app
app = FastAPI(title="Warranty & Asset Tracking Portal")

# Create a router for remaining legacy endpoints
legacy_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
