#!/usr/bin/env python3
"""
Admin Account Finder Script
===========================
Use this script to find admin accounts in the database.

Usage:
  python3 find_admin.py
  
Or with custom MongoDB URL:
  MONGO_URL=mongodb://localhost:27017 python3 find_admin.py
"""

import os
import sys
from pymongo import MongoClient

def main():
    # Get MongoDB connection string
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'warranty_portal')
    
    print("=" * 50)
    print("  Admin Account Finder")
    print("=" * 50)
    print(f"\nConnecting to: {mongo_url}")
    print(f"Database: {db_name}\n")
    
    try:
        client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
        # Test connection
        client.server_info()
        db = client[db_name]
        
        # Find all admin users
        admins = list(db.admin_users.find(
            {"is_deleted": {"$ne": True}},
            {"email": 1, "name": 1, "role": 1, "is_active": 1, "created_at": 1}
        ))
        
        if not admins:
            print("No admin accounts found in the database.")
            print("\nYou may need to:")
            print("  1. Check if you're using the correct database name")
            print("  2. Create an admin account via the registration endpoint")
            return
        
        print(f"Found {len(admins)} admin account(s):\n")
        print("-" * 50)
        
        for i, admin in enumerate(admins, 1):
            print(f"\n{i}. {admin.get('name', 'Unknown')}")
            print(f"   Email:    {admin.get('email', 'N/A')}")
            print(f"   Role:     {admin.get('role', 'N/A')}")
            print(f"   Active:   {'Yes' if admin.get('is_active', True) else 'No'}")
            if admin.get('created_at'):
                print(f"   Created:  {admin.get('created_at')}")
        
        print("\n" + "-" * 50)
        print("\nTo reset a password, use the 'Forgot Password' feature")
        print("or contact your system administrator.")
        
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print("\nMake sure:")
        print("  1. MongoDB is running")
        print("  2. MONGO_URL environment variable is correct")
        print("  3. You have network access to the database")
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    main()
