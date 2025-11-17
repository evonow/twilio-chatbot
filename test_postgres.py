#!/usr/bin/env python3
"""
Test script to verify PostgreSQL configuration for user storage
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Check PostgreSQL availability
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    print("✅ psycopg2 is installed")
    POSTGRESQL_AVAILABLE = True
except ImportError:
    print("❌ psycopg2 is NOT installed")
    POSTGRESQL_AVAILABLE = False
    exit(1)

# Check DATABASE_URL
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("❌ DATABASE_URL environment variable is NOT set")
    print("   This means users will be stored in JSON file (ephemeral)")
    print("   Users will be lost on each deployment!")
    exit(1)
else:
    print(f"✅ DATABASE_URL is set")
    # Mask password in URL for display
    if '@' in database_url:
        parts = database_url.split('@')
        if '://' in parts[0]:
            protocol_user = parts[0].split('://')
            if ':' in protocol_user[1]:
                user_pass = protocol_user[1].split(':')
                masked_url = f"{protocol_user[0]}://{user_pass[0]}:****@{parts[1]}"
                print(f"   URL: {masked_url}")
            else:
                print(f"   URL: {database_url.split('@')[0]}@****")
        else:
            print(f"   URL: ****@{parts[1]}")
    else:
        print(f"   URL: {database_url}")

# Test connection
print("\n🔌 Testing PostgreSQL connection...")
try:
    conn = psycopg2.connect(database_url, sslmode='require')
    print("✅ Successfully connected to PostgreSQL!")
    
    # Check if users table exists
    cur = conn.cursor()
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'users'
        );
    """)
    table_exists = cur.fetchone()[0]
    
    if table_exists:
        print("✅ 'users' table exists")
        
        # Count users
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        print(f"✅ Found {user_count} user(s) in database")
        
        # List users
        cur.execute("SELECT pin, name, role, created_at FROM users ORDER BY created_at")
        users = cur.fetchall()
        if users:
            print("\n📋 Current users:")
            for pin, name, role, created_at in users:
                print(f"   - PIN: {pin}, Name: {name}, Role: {role}, Created: {created_at}")
        else:
            print("   (No users found)")
    else:
        print("⚠️  'users' table does NOT exist")
        print("   It will be created on first app startup")
    
    cur.close()
    conn.close()
    print("\n✅ PostgreSQL is properly configured!")
    print("   Users will persist across deployments")
    
except Exception as e:
    print(f"❌ Error connecting to PostgreSQL: {e}")
    import traceback
    traceback.print_exc()
    print("\n⚠️  PostgreSQL connection failed!")
    print("   Users will fall back to JSON file storage (ephemeral)")
    exit(1)

