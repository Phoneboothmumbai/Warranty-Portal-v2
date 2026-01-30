"""
Tenant Scoping Helper - Apply organization filters to admin queries
===================================================================
This module provides utilities for automatically scoping queries
by organization_id based on the authenticated admin's organization.
"""
from typing import Optional, Dict, Any
from database import db


async def get_admin_org_id(admin_email: str) -> Optional[str]:
    """
    Get the organization_id for an admin user.
    Returns None for legacy admins without organization membership.
    """
    org_member = await db.organization_members.find_one(
        {"email": admin_email, "is_active": True, "is_deleted": {"$ne": True}},
        {"_id": 0, "organization_id": 1}
    )
    return org_member.get("organization_id") if org_member else None


def scope_query(query: Dict[str, Any], org_id: Optional[str]) -> Dict[str, Any]:
    """
    Add organization_id filter to a query.
    Returns original query if org_id is None (backward compatibility).
    """
    if org_id:
        return {**query, "organization_id": org_id}
    return query


async def get_scoped_query(query: Dict[str, Any], admin: dict) -> Dict[str, Any]:
    """
    Get a tenant-scoped query based on admin's organization.
    Convenience function combining get_admin_org_id and scope_query.
    """
    org_id = await get_admin_org_id(admin.get("email", ""))
    return scope_query(query, org_id)


async def count_with_scope(collection_name: str, query: Dict[str, Any], admin: dict) -> int:
    """Count documents with automatic tenant scoping."""
    org_id = await get_admin_org_id(admin.get("email", ""))
    scoped_query = scope_query(query, org_id)
    collection = db[collection_name]
    return await collection.count_documents(scoped_query)


async def find_with_scope(
    collection_name: str, 
    query: Dict[str, Any], 
    admin: dict,
    projection: Dict[str, Any] = None,
    skip: int = 0,
    limit: int = 100,
    sort: list = None
):
    """Find documents with automatic tenant scoping."""
    org_id = await get_admin_org_id(admin.get("email", ""))
    scoped_query = scope_query(query, org_id)
    collection = db[collection_name]
    
    cursor = collection.find(scoped_query, projection or {"_id": 0})
    
    if sort:
        cursor = cursor.sort(sort)
    if skip:
        cursor = cursor.skip(skip)
    if limit:
        cursor = cursor.limit(limit)
    
    return await cursor.to_list(limit)


async def find_one_with_scope(
    collection_name: str,
    query: Dict[str, Any],
    admin: dict,
    projection: Dict[str, Any] = None
):
    """Find one document with automatic tenant scoping."""
    org_id = await get_admin_org_id(admin.get("email", ""))
    scoped_query = scope_query(query, org_id)
    collection = db[collection_name]
    return await collection.find_one(scoped_query, projection or {"_id": 0})


async def update_with_scope(
    collection_name: str,
    query: Dict[str, Any],
    update: Dict[str, Any],
    admin: dict
):
    """Update document with automatic tenant scoping."""
    org_id = await get_admin_org_id(admin.get("email", ""))
    scoped_query = scope_query(query, org_id)
    collection = db[collection_name]
    return await collection.update_one(scoped_query, update)


async def delete_with_scope(
    collection_name: str,
    query: Dict[str, Any],
    admin: dict
):
    """Delete document with automatic tenant scoping (soft delete)."""
    org_id = await get_admin_org_id(admin.get("email", ""))
    scoped_query = scope_query(query, org_id)
    collection = db[collection_name]
    return await collection.update_one(scoped_query, {"$set": {"is_deleted": True}})


async def insert_with_org_id(
    collection_name: str,
    document: Dict[str, Any],
    admin: dict
):
    """Insert document with organization_id automatically added."""
    org_id = await get_admin_org_id(admin.get("email", ""))
    if org_id:
        document["organization_id"] = org_id
    collection = db[collection_name]
    return await collection.insert_one(document)


# Usage Stats helpers
async def get_org_usage_stats(org_id: str) -> Dict[str, int]:
    """Get usage statistics for an organization."""
    return {
        "companies": await db.companies.count_documents({
            "organization_id": org_id, "is_deleted": {"$ne": True}
        }),
        "devices": await db.devices.count_documents({
            "organization_id": org_id, "is_deleted": {"$ne": True}
        }),
        "users": await db.company_users.count_documents({
            "organization_id": org_id, "is_deleted": {"$ne": True}
        }),
        "tickets": await db.tickets.count_documents({
            "organization_id": org_id
        }),
        "amc_contracts": await db.amc_contracts.count_documents({
            "organization_id": org_id, "is_deleted": {"$ne": True}
        }),
        "engineers": await db.engineers.count_documents({
            "organization_id": org_id, "is_deleted": {"$ne": True}
        })
    }
