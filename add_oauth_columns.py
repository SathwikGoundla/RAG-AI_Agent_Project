#!/usr/bin/env python
"""Add missing oauth columns to existing users table"""

import sqlite3
import sys

try:
    conn = sqlite3.connect('sql_app.db')
    cursor = conn.cursor()
    
    # Check if columns exist
    cursor.execute("PRAGMA table_info(users);")
    columns = {row[1] for row in cursor.fetchall()}
    
    print(f"Current columns: {columns}")
    
    # Add missing columns if they don't exist
    if 'oauth_provider' not in columns:
        print("Adding oauth_provider column...")
        cursor.execute("ALTER TABLE users ADD COLUMN oauth_provider VARCHAR;")
    
    if 'oauth_id' not in columns:
        print("Adding oauth_id column...")
        cursor.execute("ALTER TABLE users ADD COLUMN oauth_id VARCHAR;")
    
    conn.commit()
    
    # Verify columns were added
    cursor.execute("PRAGMA table_info(users);")
    columns = cursor.fetchall()
    print(f"\nFinal columns ({len(columns)}):")
    for c in columns:
        print(f"  {c[1]}: {c[2]}")
    
    if any('oauth' in str(c) for c in columns):
        print("\n✓ OAuth columns successfully added!")
    else:
        print("\n✗ OAuth columns still missing!")
        sys.exit(1)
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
