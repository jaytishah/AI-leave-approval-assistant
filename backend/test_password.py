import bcrypt

# Test hashing and verification
password = "admin123"
h = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(f"Hash: {h}")
print(f"Verify: {bcrypt.checkpw(password.encode('utf-8'), h.encode('utf-8'))}")

# Now test with the actual database
import sys
sys.path.append(".")
from app.core import SessionLocal
from app.models import User

db = SessionLocal()
user = db.query(User).filter(User.email == "admin@leaveai.com").first()
if user:
    print(f"\nUser found: {user.email}")
    print(f"Stored hash: {user.hashed_password}")
    print(f"Hash length: {len(user.hashed_password)}")
    result = bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8'))
    print(f"Password verify result: {result}")
else:
    print("User not found!")
db.close()
