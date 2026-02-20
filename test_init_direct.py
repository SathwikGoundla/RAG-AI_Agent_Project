#!/usr/bin/env python
"""Direct test of init_db"""

import sys
import os

# Verify imports work
print("[1] Testing imports...")
try:
    from backend.database import init_db, Base, User, engine
    print("[1] OK - All imports successful")
except Exception as e:
    print(f"[1] ERROR - Import failed: {e}")
    sys.exit(1)

# Verify metadata has tables
print("[2] Checking Base.metadata...")
print(f"    Tables in metadata: {[t.name for t in Base.metadata.tables.values()]}")

# Test init_db()
print("[3] Calling init_db()...")
try:
    init_db()
    print("[3] OK - init_db completed")
except Exception as e:
    print(f"[3] ERROR - init_db failed: {e}")
    import traceback
    traceback.print_exc()

# Check if database was created
print("[4] Checking created database...")
import sqlite3
conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"    Tables in DB: {tables}")
if tables:
    cursor.execute("PRAGMA table_info(users);")
    cols = cursor.fetchall()
    print(f"    Users columns: {len(cols)}")
    if cols and any('oauth' in str(c) for c in cols):
        print("    ✓ OAuth columns found!")
    else:
        print("    ✗ No oauth columns!")
conn.close()

print("\n[DONE]")
