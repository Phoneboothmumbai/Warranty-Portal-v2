"""
Production Data Isolation Migration for aftersales.support
==========================================================
Ensures every record in every collection has the correct organization_id.

Strategy:
1. Build admin → org mapping from organization_members
2. Build company → org mapping from companies that already have org_id
3. For orphaned records: trace via created_by → admin → org
4. For records linked to a company: trace via company_id → company → org
5. NEVER blindly assign to a default org — log and skip unknowns

Usage:
  docker exec -it warranty_backend python3 migrate_org_ids.py
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://mongodb:27017")
DB_NAME = os.environ.get("DB_NAME", "warranty_portal")

# All collections that must be scoped by organization_id
COLLECTIONS_WITH_ORG = [
    "companies", "devices", "parts", "users", "company_users",
    "sites", "employees", "service_history", "amc", "amc_contracts",
    "amc_requests", "tickets", "v2_tickets", "supply_categories",
    "supply_products", "supply_orders", "device_models",
    "item_categories", "item_products", "item_bundles", "quotations",
    "help_topics", "forms", "workflows", "teams", "roles",
    "sla_plans", "priorities", "canned_responses", "admin_settings",
    "credentials", "subscriptions", "accessories", "asset_groups",
    "internet_services", "licenses", "deployments", "knowledge_articles",
    "static_pages", "custom_domains", "email_whitelabel",
]

ORPHAN_QUERY = {"$or": [
    {"organization_id": {"$exists": False}},
    {"organization_id": None},
    {"organization_id": ""},
]}


async def run():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    print(f"Connected to {MONGO_URL}/{DB_NAME}\n{'='*70}")

    # ── Step 1: Load all orgs ──
    orgs = await db.organizations.find(
        {"is_deleted": {"$ne": True}}, {"_id": 0}
    ).to_list(100)
    org_by_id = {o["id"]: o["name"] for o in orgs}
    print(f"\n[1] {len(orgs)} Organizations:")
    for o in orgs:
        print(f"    {o['name']}  →  {o['id']}")

    # ── Step 2: Build admin email → org_id map ──
    members = await db.organization_members.find(
        {"is_active": True, "is_deleted": {"$ne": True}}, {"_id": 0}
    ).to_list(1000)
    admin_to_org = {}
    for m in members:
        email = (m.get("email") or "").strip().lower()
        if email:
            admin_to_org[email] = m.get("organization_id")

    # Also map from admins collection (some records use admin email directly)
    admins = await db.admins.find({}, {"_id": 0, "email": 1, "organization_id": 1}).to_list(1000)
    for a in admins:
        email = (a.get("email") or "").strip().lower()
        if email and email not in admin_to_org and a.get("organization_id"):
            admin_to_org[email] = a["organization_id"]

    print(f"\n[2] Admin → Org mapping ({len(admin_to_org)}):")
    for email, oid in admin_to_org.items():
        print(f"    {email}  →  {org_by_id.get(oid, '???')} ({oid})")

    # ── Step 3: Build company_id → org_id map (from companies that already have org) ──
    all_companies = await db.companies.find(
        {"organization_id": {"$exists": True, "$ne": None, "$ne": ""}},
        {"_id": 0, "id": 1, "organization_id": 1, "name": 1}
    ).to_list(10000)
    company_to_org = {c["id"]: c["organization_id"] for c in all_companies if c.get("id")}

    print(f"\n[3] Company → Org mapping ({len(company_to_org)} companies with org_id)")

    # ── Step 4: Audit + Fix every collection ──
    print(f"\n{'='*70}")
    print("AUDIT & FIX")
    print(f"{'='*70}")

    total_fixed = 0
    total_skipped = 0

    for coll_name in COLLECTIONS_WITH_ORG:
        coll = db[coll_name]
        total = await coll.count_documents({})
        if total == 0:
            continue

        orphan_count = await coll.count_documents(ORPHAN_QUERY)

        # Per-org breakdown
        per_org = {}
        for org in orgs:
            cnt = await coll.count_documents({"organization_id": org["id"]})
            if cnt > 0:
                per_org[org["name"]] = cnt

        print(f"\n  [{coll_name}]  total={total}  orphaned={orphan_count}")
        for name, cnt in per_org.items():
            print(f"    ├── {name}: {cnt}")
        if orphan_count:
            print(f"    └── NO ORG: {orphan_count}")

        if orphan_count == 0:
            continue

        # Fix orphans
        orphans = await coll.find(ORPHAN_QUERY).to_list(50000)
        fixed = 0
        skipped = 0

        for doc in orphans:
            resolved_org = None

            # Strategy A: created_by / admin_email field → admin → org
            for field in ["created_by", "admin_email", "email", "updated_by"]:
                val = (doc.get(field) or "").strip().lower()
                if val and val in admin_to_org:
                    resolved_org = admin_to_org[val]
                    break

            # Strategy B: company_id field → company → org
            if not resolved_org:
                for field in ["company_id", "company"]:
                    cid = doc.get(field)
                    if cid and cid in company_to_org:
                        resolved_org = company_to_org[cid]
                        break

            # Strategy C: For company_users, check their company
            if not resolved_org and coll_name == "company_users":
                cid = doc.get("company_id")
                if cid:
                    comp = await db.companies.find_one(
                        {"id": cid, "organization_id": {"$exists": True}},
                        {"_id": 0, "organization_id": 1}
                    )
                    if comp:
                        resolved_org = comp.get("organization_id")

            if resolved_org:
                await coll.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"organization_id": resolved_org}}
                )
                fixed += 1
            else:
                skipped += 1
                doc_id = doc.get("id", str(doc.get("_id", "?")))
                print(f"    ⚠ SKIPPED (can't resolve org): {coll_name} doc={doc_id}")

        if fixed:
            print(f"    ✓ Fixed {fixed} records")
        if skipped:
            print(f"    ✗ Skipped {skipped} records (manual review needed)")

        total_fixed += fixed
        total_skipped += skipped

    # ── Step 5: Cross-contamination report ──
    print(f"\n{'='*70}")
    print("FINAL STATE: Companies per tenant")
    print(f"{'='*70}")
    for org in orgs:
        companies = await db.companies.find(
            {"organization_id": org["id"], "is_deleted": {"$ne": True}},
            {"_id": 0, "name": 1}
        ).to_list(500)
        print(f"\n  {org['name']} — {len(companies)} companies:")
        for c in companies:
            print(f"    • {c.get('name', 'unnamed')}")

    # Devices per tenant
    print(f"\n{'='*70}")
    print("FINAL STATE: Devices per tenant")
    print(f"{'='*70}")
    for org in orgs:
        count = await db.devices.count_documents(
            {"organization_id": org["id"], "is_deleted": {"$ne": True}}
        )
        print(f"  {org['name']}: {count} devices")

    # Users per tenant
    print(f"\n{'='*70}")
    print("FINAL STATE: Users per tenant")
    print(f"{'='*70}")
    for org in orgs:
        count = await db.users.count_documents(
            {"organization_id": org["id"], "is_deleted": {"$ne": True}}
        )
        cu = await db.company_users.count_documents(
            {"organization_id": org["id"], "is_deleted": {"$ne": True}}
        )
        print(f"  {org['name']}: {count} users, {cu} company_users")

    print(f"\n{'='*70}")
    print(f"DONE — Fixed {total_fixed} | Skipped {total_skipped}")
    if total_skipped > 0:
        print("⚠ Skipped records need manual review in MongoDB")
    print(f"{'='*70}")

    client.close()


if __name__ == "__main__":
    asyncio.run(run())
