import sqlite3

conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"Tables in database: {tables}")

if tables:
    # Check users table
    cursor.execute("PRAGMA table_info(users);")
    cols = cursor.fetchall()
    print(f"\nUsers table columns: {len(cols)} columns")
    if cols:
        for c in cols:
            print(f"  {c[1]}: {c[2]}")
    else:
        print("  (no columns or table doesn't exist)")

conn.close()
