import sqlite3

conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(users);")
columns = cursor.fetchall()
print('Columns in users table:')
for col in columns:
    print(f'  {col[1]}: {col[2]}')
conn.close()
