"""
Migration: Add Multi-tenancy Support
====================================
This script adds organization_id to existing collections for multi-tenancy support.

For existing installations, this creates a "default" organization and links all
existing data to it.

Usage:
    python scripts/migrate_to_multitenancy.py
"""
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os

# Get MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "warranty_portal")


async def migrate():
    """Main migration function"""
    print("=" * 60)
    print("Multi-tenancy Migration Script")
    print("=" * 60)
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Check if migration already done
    existing_org = await db.organizations.find_one({})
    if existing_org:
        print("\n⚠️  Organizations collection already exists.")
        print(f"   Found organization: {existing_org.get('name', 'Unknown')}")
        
        # Check if we need to add organization_id to collections
        sample_company = await db.companies.find_one({"organization_id": {"$exists": False}})
        if not sample_company:
            print("   All collections already have organization_id.")
            print("   Migration already complete. Exiting.")
            return
        else:
            print("   Some collections need organization_id. Continuing...")
            org_id = existing_org["id"]
            org_name = existing_org["name"]
    else:
        # Create default organization
        print("\n📦 Creating default organization...")
        
        # Get first admin
        admin = await db.admins.find_one({}, {"_id": 0})
        
        if not admin:
            print("❌ No admin found. Please create an admin first.")
            return
        
        org_id = str(uuid.uuid4())
        org_name = "Default Organization"
        
        # Calculate trial period
        trial_ends = datetime.now(timezone.utc) + timedelta(days=30)  # Extended trial for existing users
        
        organization = {
            "id": org_id,
            "name": org_name,
            "slug": "default",
            "owner_user_id": admin.get("id", ""),
            "owner_email": admin.get("email", ""),
            "status": "active",  # Give existing users active status
            "subscription": {
                "plan": "professional",  # Give existing users professional plan
                "status": "active",
                "billing_cycle": "monthly",
                "current_period_start": datetime.now(timezone.utc).isoformat(),
                "current_period_end": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
                "companies_count": 0,
                "devices_count": 0,
                "users_count": 0
            },
            "branding": {
                "accent_color": "#0F62FE",
                "company_name": "Warranty Portal"
            },
            "settings": {
                "timezone": "Asia/Kolkata",
                "date_format": "DD/MM/YYYY",
                "currency": "INR",
                "language": "en",
                "enable_public_portal": True,
                "enable_qr_codes": True,
                "enable_ai_features": True
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "is_deleted": False
        }
        
        await db.organizations.insert_one(organization)
        print(f"   ✅ Created organization: {org_name} (ID: {org_id})")
        
        # Migrate admin to organization member
        print("\n👤 Migrating admin to organization member...")
        
        member = {
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "email": admin.get("email"),
            "name": admin.get("name", "Admin"),
            "password_hash": admin.get("password_hash", ""),
            "role": "owner",
            "permissions": ["all"],
            "is_active": True,
            "is_deleted": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Check if member already exists
        existing_member = await db.organization_members.find_one({"email": admin.get("email")})
        if not existing_member:
            await db.organization_members.insert_one(member)
            print(f"   ✅ Created org member: {admin.get('email')}")
        else:
            print(f"   ⚠️  Org member already exists: {admin.get('email')}")
    
    # Collections to migrate
    collections_to_migrate = [
        "companies",
        "devices",
        "parts",
        "company_users",
        "company_employees",
        "service_history",
        "service_tickets",
        "tickets",  # New ticketing system
        "amc_contracts",
        "amc_device_assignments",
        "amc_onboardings",
        "sites",
        "licenses",
        "supply_orders",
        "email_subscriptions",
        "internet_services",
        "asset_groups",
        "audit_logs",
        "quick_service_requests"
    ]
    
    print(f"\n📝 Adding organization_id to collections...")
    print(f"   Using organization: {org_name} ({org_id})")
    
    for collection_name in collections_to_migrate:
        try:
            collection = db[collection_name]
            
            # Count documents without organization_id
            count = await collection.count_documents({
                "organization_id": {"$exists": False}
            })
            
            if count > 0:
                # Update all documents without organization_id
                result = await collection.update_many(
                    {"organization_id": {"$exists": False}},
                    {"$set": {"organization_id": org_id}}
                )
                print(f"   ✅ {collection_name}: Updated {result.modified_count} documents")
            else:
                print(f"   ⏭️  {collection_name}: No documents to update")
                
        except Exception as e:
            print(f"   ⚠️  {collection_name}: Error - {str(e)}")
    
    # Update organization usage counts
    print("\n📊 Updating organization usage counts...")
    
    companies_count = await db.companies.count_documents({
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    devices_count = await db.devices.count_documents({
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    users_count = await db.company_users.count_documents({
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    
    await db.organizations.update_one(
        {"id": org_id},
        {"$set": {
            "subscription.companies_count": companies_count,
            "subscription.devices_count": devices_count,
            "subscription.users_count": users_count
        }}
    )
    
    print(f"   Companies: {companies_count}")
    print(f"   Devices: {devices_count}")
    print(f"   Users: {users_count}")
    
    # Create indexes for organization_id
    print("\n🔍 Creating indexes...")
    
    for collection_name in collections_to_migrate:
        try:
            collection = db[collection_name]
            await collection.create_index("organization_id")
            print(f"   ✅ Created index on {collection_name}.organization_id")
        except Exception as e:
            print(f"   ⚠️  {collection_name}: Index error - {str(e)}")
    
    # Create compound indexes for common queries
    compound_indexes = [
        ("companies", [("organization_id", 1), ("is_deleted", 1)]),
        ("devices", [("organization_id", 1), ("company_id", 1), ("is_deleted", 1)]),
        ("tickets", [("organization_id", 1), ("status", 1)]),
    ]
    
    for coll_name, index_fields in compound_indexes:
        try:
            await db[coll_name].create_index(index_fields)
            print(f"   ✅ Created compound index on {coll_name}")
        except Exception as e:
            pass  # Ignore if index already exists
    
    print("\n" + "=" * 60)
    print("✅ Migration Complete!")
    print("=" * 60)
    print(f"\nOrganization ID: {org_id}")
    print(f"Organization Name: {org_name}")
    print("\nNext steps:")
    print("1. Update your JWT tokens to include organization_id")
    print("2. Test the new /api/org/* endpoints")
    print("3. Gradually migrate routes to use tenant middleware")


if __name__ == "__main__":
    asyncio.run(migrate())
