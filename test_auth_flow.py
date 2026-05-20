import uuid
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, joinedload

# Setup
engine = create_engine("sqlite:///./mavericks.db")

# Import after engine creation
from models.user import User

# First, let's login and get a token, then test
print("=== Testing Full Auth Flow ===\n")

# Get user by email (this is what login does)
with Session(engine) as db:
    stmt = select(User).options(joinedload(User.role)).where(User.email == "sarthaks3@hexaware.com")
    user = db.execute(stmt).unique().scalar_one_or_none()
    
    if user:
        print(f"✓ User found by email!")
        print(f"  ID: {user.id}")
        print(f"  ID type: {type(user.id)}")
        print(f"  Email: {user.email}")
        print(f"  Role: {user.role.name if user.role else 'No role'}")
        
        # Now try to find by ID (this is what the token validation does)
        print(f"\nAttempting lookup by ID: {user.id}")
        stmt2 = select(User).options(joinedload(User.role)).where(User.id == user.id)
        user2 = db.execute(stmt2).unique().scalar_one_or_none()
        
        if user2:
            print(f"✓ User also found by ID!")
        else:
            print(f"✗ User NOT found by ID")
    else:
        print("✗ User not found by email")
