"""
Production Data Isolation Migration Script
==========================================
Run this on your Vultr server to fix organization_id on all records.

Usage (inside the warranty-portal docker container or directly on server):
  python3 migrate_org_ids.py

Or via docker:
  docker exec -it warranty_backend python3 migrate_org_ids.py
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://mongodb:27017")
DB_NAME = os.environ.get("DB_NAME", "warranty_portal")

# Collections that need organization_id
COLLECTIONS = [
    "companies", "devices", "parts", "users", "company_users",
    "sites", "employees", "service_history", "amc", "amc_contracts",
    "amc_requests", "tickets", "v2_tickets", "supply_categories",
    "supply_products", "supply_orders", "device_models",
    "item_categories", "item_products", "item_bundles", "quotations",
    "help_topics", "forms", "workflows", "teams", "roles",
    "sla_plans", "priorities", "canned_responses", "admin_settings",
    "credentials", "subscriptions", "accessories", "asset_groups",
    "internet_services", "licenses", "deployments",
]


async def run_migration():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    print(f"Connected to {MONGO_URL}/{DB_NAME}")
    print("=" * 60)

    # Step 1: Get all organizations
    orgs = await db.organizations.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(100)
    print(f"\nFound {len(orgs)} organizations:")
    for org in orgs:
        print(f"  - {org.get('name')} (id: {org.get('id')})")

    if not orgs:
        print("ERROR: No organizations found. Cannot proceed.")
        return

    # Step 2: Build admin → org mapping
    members = await db.organization_members.find(
        {"is_active": True, "is_deleted": {"$ne": True}}, {"_id": 0}
    ).to_list(1000)

    admin_to_org = {}
    for m in members:
        admin_to_org[m.get("email", "").lower()] = m.get("organization_id")
    
    print(f"\nAdmin → Org mapping ({len(admin_to_org)} admins):")
    for email, oid in admin_to_org.items():
        org_name = next((o["name"] for o in orgs if o["id"] == oid), "Unknown")
        print(f"  - {email} → {org_name} ({oid})")

    # Step 3: Audit each collection
    print("\n" + "=" * 60)
    print("AUDIT: Records per collection")
    print("=" * 60)

    total_fixed = 0
    total_orphaned = 0

    for coll_name in COLLECTIONS:
        coll = db[coll_name]
        total = await coll.count_documents({})
        if total == 0:
            continue

        # Count by org
        no_org = await coll.count_documents({"organization_id": {"$exists": False}})
        null_org = await coll.count_documents({"organization_id": None})
        empty_org = await coll.count_documents({"organization_id": ""})
        
        orphaned = no_org + null_org + empty_org

        per_org = {}
        for org in orgs:
            count = await coll.count_documents({"organization_id": org["id"]})
            if count > 0:
                per_org[org["name"]] = count

        print(f"\n  {coll_name}: {total} total, {orphaned} orphaned")
        for org_name, count in per_org.items():
            print(f"    ├── {org_name}: {count}")
        if orphaned > 0:
            print(f"    └── NO ORG: {orphaned}")

        # Step 4: Fix orphaned records
        if orphaned > 0:
            # Try to assign based on created_by field
            orphaned_docs = await coll.find(
                {"$or": [
                    {"organization_id": {"$exists": False}},
                    {"organization_id": None},
                    {"organization_id": ""}
                ]},
                {"_id": 1, "created_by": 1, "admin_email": 1, "email": 1}
            ).to_list(10000)

            fixed_count = 0
            for doc in orphaned_docs:
                # Try to find the org from created_by or admin_email
                creator = (doc.get("created_by") or doc.get("admin_email") or "").lower()
                org_id = admin_to_org.get(creator)

                if not org_id:
                    # If we can't determine the org, assign to the first/default org
                    # This is a safe fallback — better than leaving unscoped
                    org_id = orgs[0]["id"]
                    print(f"    ⚠ Assigning orphaned doc to default org: {orgs[0]['name']}")

                await coll.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"organization_id": org_id}}
                )
                fixed_count += 1

            total_fixed += fixed_count
            print(f"    ✓ Fixed {fixed_count} orphaned records")
        
        total_orphaned += orphaned

    # Step 5: Check for cross-contamination
    print("\n" + "=" * 60)
    print("CROSS-CONTAMINATION CHECK: Companies per org")
    print("=" * 60)

    for org in orgs:
        companies = await db.companies.find(
            {"organization_id": org["id"], "is_deleted": {"$ne": True}},
            {"_id": 0, "name": 1}
        ).to_list(100)
        print(f"\n  {org['name']} ({len(companies)} companies):")
        for c in companies:
            print(f"    - {c.get('name', 'unnamed')}")

    print("\n" + "=" * 60)
    print(f"SUMMARY: Fixed {total_fixed} orphaned records across all collections")
    if total_orphaned == 0:
        print("All records already have organization_id set.")
    print("=" * 60)

    client.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
