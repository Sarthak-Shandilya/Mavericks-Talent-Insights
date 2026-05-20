import uuid
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, joinedload

# Setup
engine = create_engine("sqlite:///./mavericks.db")

# Import after engine creation
from models.user import User

# The UUID from the database
user_id_str = "7be5a440-f7c8-4397-bc96-11b6eba26243"
user_id = uuid.UUID(user_id_str)

print(f"Looking up user with ID: {user_id}")
print(f"ID type: {type(user_id)}")
print(f"ID str: {str(user_id)}")

with Session(engine) as db:
    # Try the repository method
    stmt = select(User).options(joinedload(User.role)).where(User.id == user_id)
    user = db.execute(stmt).unique().scalar_one_or_none()
    
    if user:
        print(f"\n✓ User found!")
        print(f"  Email: {user.email}")
        print(f"  Name: {user.full_name}")
        print(f"  Role: {user.role.name if user.role else 'No role'}")
    else:
        print("\n✗ User NOT found via SQLAlchemy")
        
    # Try raw SQL
    import sqlite3
    conn = sqlite3.connect('mavericks.db')
    cursor = conn.cursor()
    cursor.execute('SELECT email, full_name FROM users WHERE id = ?', (str(user_id),))
    row = cursor.fetchone()
    if row:
        print(f"\n✓ User found via raw SQL: {row[0]}")
    conn.close()
