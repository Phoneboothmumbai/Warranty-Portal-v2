"""
Authentication endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, status

from database import db
from models.auth import Token, AdminUser, AdminLogin, AdminCreate
from services.auth import verify_password, get_password_hash, create_access_token, get_current_admin
from utils.helpers import get_ist_isoformat

router = APIRouter(tags=["Authentication"])


@router.post("/auth/login", response_model=Token)
async def admin_login(login: AdminLogin):
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
async def setup_first_admin(admin_data: AdminCreate):
    existing = await db.admins.find_one({})
    if existing:
        raise HTTPException(status_code=400, detail="Admin already exists. Use login instead.")
    
    admin = AdminUser(
        email=admin_data.email.lower(),
        password_hash=get_password_hash(admin_data.password),
        name=admin_data.name,
        created_at=get_ist_isoformat()
    )
    await db.admins.insert_one(admin.model_dump())
    return {"message": "Admin account created successfully"}
