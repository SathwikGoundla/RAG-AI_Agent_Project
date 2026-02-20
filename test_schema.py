from backend.database import Base, engine, User, SessionLocal

print("Creating all tables...")
Base.metadata.create_all(bind=engine)

print("Tables created. Checking User table:")
print(f"User columns: {[c.name for c in User.__table__.columns]}")

# Now check the database file
import sqlite3
conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(users);")
columns = cursor.fetchall()
print('\nColumns in sqlite users table:')
for col in columns:
    print(f'  {col[1]}: {col[2]}')
conn.close()

print("\nDone!")
