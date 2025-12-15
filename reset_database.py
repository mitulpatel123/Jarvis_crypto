#!/usr/bin/env python3
"""
Database Reset Utility
Truncates the 'feature_store' table to clear all old/bad data.
Run this on the VPS before starting the collector.
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from infrastructure.timescale_db import TimescaleDB

def reset_database():
    print("⚠️  WARNING: This will DELETE ALL DATA in 'crypto_data' database.")
    print("Type 'YES' to confirm: ")
    confirm = input()
    
    if confirm != 'YES':
        print("❌ Operation cancelled.")
        return

    try:
        db = TimescaleDB()
        conn = db.get_conn()
        cur = conn.cursor()
        
        print("🗑️  Truncating table 'feature_store'...")
        cur.execute("TRUNCATE TABLE feature_store CASCADE;")
        conn.commit()
        
        print("✅ Database cleared successfully.")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
    finally:
        if 'db' in locals():
            db.put_conn(conn)

if __name__ == "__main__":
    reset_database()
