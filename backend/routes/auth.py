"""
Authentication endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, status, Request

from database import db
from models.auth import Token, AdminUser, AdminLogin, AdminCreate
from services.auth import verify_password, get_password_hash, create_access_token, get_current_admin
from utils.helpers import get_ist_isoformat
from utils.security import limiter, RATE_LIMITS, validate_password_strength

router = APIRouter(tags=["Authentication"])


@router.post("/auth/login", response_model=Token)
@limiter.limit(RATE_LIMITS["login"])
async def admin_login(request: Request, login: AdminLogin):
    """Admin login with rate limiting (5 attempts/minute per IP)"""
    admin = await db.admins.find_one({"email": login.email.lower()}, {"_id": 0})
    if not admin or not verify_password(login.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": admin["email"]})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/auth/me")
async def get_current_admin_info(admin: dict = Depends(get_current_admin)):
    return {
        "email": admin["email"],
        "name": admin.get("name", "Admin"),
        "role": admin.get("role", "admin")
    }


@router.post("/auth/setup")
@limiter.limit(RATE_LIMITS["register"])
async def setup_first_admin(request: Request, admin_data: AdminCreate):
    """First admin setup with password validation"""
    existing = await db.admins.find_one({})
    if existing:
        raise HTTPException(status_code=400, detail="Admin already exists. Use login instead.")
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(admin_data.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    admin = AdminUser(
        email=admin_data.email.lower(),
        password_hash=get_password_hash(admin_data.password),
        name=admin_data.name,
        created_at=get_ist_isoformat()
    )
    await db.admins.insert_one(admin.model_dump())
    return {"message": "Admin account created successfully"}
