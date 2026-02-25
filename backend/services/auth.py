"""
Authentication service functions
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from database import db
from models.common import AuditLog

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security dependency for JWT authentication
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    admin = await db.admins.find_one({"email": email}, {"_id": 0})
    if admin is None:
        raise credentials_exception
    
    # Fetch organization_id from organization_members for multi-tenancy
    org_member = await db.organization_members.find_one(
        {"email": email, "is_active": True, "is_deleted": {"$ne": True}},
        {"_id": 0, "organization_id": 1}
    )
    if org_member and org_member.get("organization_id"):
        admin["organization_id"] = org_member["organization_id"]
    
    return admin


async def get_current_company_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current company portal user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("type")
        if user_id is None or user_type != "company_user":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.company_users.find_one(
        {"id": user_id, "is_active": True, "is_deleted": {"$ne": True}}, 
        {"_id": 0, "password_hash": 0}
    )
    if user is None:
        raise credentials_exception
    return user


def require_company_admin(user: dict = Depends(get_current_company_user)):
    """Dependency to require company_admin role"""
    if user.get("role") != "company_admin":
        raise HTTPException(status_code=403, detail="Admin role required for this action")
    return user


async def log_audit(entity_type: str, entity_id: str, action: str, changes: dict, admin: dict):
    """Log audit entry - silent, no failures"""
    try:
        audit = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            changes=changes,
            performed_by=admin.get("id", "unknown"),
            performed_by_name=admin.get("name", "Unknown")
        )
        await db.audit_logs.insert_one(audit.model_dump())
    except Exception as e:
        logger.error(f"Audit log failed: {e}")


async def get_admin_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract admin from JWT token - supports both org_member and legacy admin tokens"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        token_type = payload.get("type", "admin")
        organization_id = payload.get("organization_id")

        if token_type == "org_member":
            member_id = payload.get("org_member_id")
            email = payload.get("sub")
            return {
                "id": member_id,
                "email": email,
                "organization_id": organization_id,
                "role": payload.get("role"),
                "name": email
            }
        else:
            admin_id = payload.get("sub")
            admin = await db.admins.find_one({"id": admin_id})
            if admin:
                return {
                    "id": admin["id"],
                    "organization_id": admin.get("organization_id"),
                    "email": admin.get("email"),
                    "name": admin.get("name")
                }
            admin = await db.admins.find_one({"email": admin_id})
            if admin:
                org_member = await db.organization_members.find_one(
                    {"email": admin.get("email"), "is_active": True, "is_deleted": {"$ne": True}},
                    {"_id": 0, "organization_id": 1}
                )
                return {
                    "id": admin.get("id", admin_id),
                    "organization_id": org_member.get("organization_id") if org_member else admin.get("organization_id", organization_id),
                    "email": admin.get("email", admin_id),
                    "name": admin.get("name", admin_id)
                }
            return {
                "id": admin_id,
                "email": admin_id,
                "organization_id": organization_id,
                "name": admin_id
            }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_engineer(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current engineer from JWT token - supports both engineers and staff_users"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        engineer_id: str = payload.get("sub")
        user_type: str = payload.get("type")
        if engineer_id is None or user_type != "engineer":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # First check engineers collection
    engineer = await db.engineers.find_one(
        {"id": engineer_id, "is_active": True, "is_deleted": {"$ne": True}}, 
        {"_id": 0, "password_hash": 0}
    )
    
    # If not found in engineers, check staff_users
    if engineer is None:
        staff_user = await db.staff_users.find_one(
            {"id": engineer_id, "state": "active", "is_deleted": {"$ne": True}},
            {"_id": 0, "password_hash": 0}
        )
        if staff_user:
            # Return staff user in engineer format
            engineer = {
                "id": staff_user["id"],
                "name": staff_user.get("name"),
                "email": staff_user.get("email"),
                "phone": staff_user.get("phone"),
                "is_active": True,
                "organization_id": staff_user.get("organization_id"),
                "source": "staff_user"
            }
    
    if engineer is None:
        raise credentials_exception
    return engineer
