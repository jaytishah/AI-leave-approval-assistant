"""Test JWT token generation and validation"""
import sys
sys.path.append(".")

from app.core import create_access_token, decode_token, settings
from datetime import timedelta

# Create a test token
test_data = {"sub": 1, "email": "admin@leaveai.com", "role": "ADMIN"}
token = create_access_token(data=test_data, expires_delta=timedelta(minutes=30))

print(f"Generated token: {token[:50]}...")
print(f"SECRET_KEY: {settings.SECRET_KEY[:20]}...")
print(f"ALGORITHM: {settings.ALGORITHM}")

# Try to decode it
decoded = decode_token(token)
print(f"Decoded payload: {decoded}")

# Now test from the auth endpoint manually
from app.core import SessionLocal, verify_password
from app.models import User

db = SessionLocal()
user = db.query(User).filter(User.email == "admin@leaveai.com").first()
if user:
    print(f"\nUser: {user.email}, Role: {user.role}")
    print(f"Password verify: {verify_password('admin123', user.hashed_password)}")
    
    # Create token like the login endpoint does
    login_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role.value}
    )
    print(f"\nLogin token: {login_token[:50]}...")
    
    # Decode it
    login_decoded = decode_token(login_token)
    print(f"Login decoded: {login_decoded}")
db.close()
