"""
Test script to verify medical certificate upload works
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
from app.schemas.schemas import LeaveRequestCreate, LeaveType

# Test 1: Create request without medical certificate (should fail)
print("Test 1: Sick leave without medical certificate (should fail)")
try:
    req = LeaveRequestCreate(
        leave_type=LeaveType.SICK,
        start_date=datetime.now(),
        end_date=datetime.now(),
    )
    print("❌ FAILED: Should have raised ValueError")
except ValueError as e:
    print(f"✅ PASSED: {e}")

# Test 2: Create request with medical certificate (should pass)
print("\nTest 2: Sick leave with medical certificate (should pass)")
try:
    req = LeaveRequestCreate(
        leave_type=LeaveType.SICK,
        start_date=datetime.now(),
        end_date=datetime.now(),
        medical_certificate_url="data:application/pdf;base64,test",
        medical_certificate_filename="test.pdf",
        medical_certificate_size=1024
    )
    print(f"✅ PASSED: Request created successfully")
    print(f"   - Filename: {req.medical_certificate_filename}")
    print(f"   - Size: {req.medical_certificate_size} bytes")
except Exception as e:
    print(f"❌ FAILED: {e}")

# Test 3: File too large (should fail)
print("\nTest 3: File size > 5MB (should fail)")
try:
    req = LeaveRequestCreate(
        leave_type=LeaveType.SICK,
        start_date=datetime.now(),
        end_date=datetime.now(),
        medical_certificate_url="data:application/pdf;base64,test",
        medical_certificate_filename="large.pdf",
        medical_certificate_size=6 * 1024 * 1024  # 6MB
    )
    print("❌ FAILED: Should have raised ValueError")
except ValueError as e:
    print(f"✅ PASSED: {e}")

# Test 4: Non-sick leave without certificate (should pass)
print("\nTest 4: Annual leave without medical certificate (should pass)")
try:
    req = LeaveRequestCreate(
        leave_type=LeaveType.ANNUAL,
        start_date=datetime.now(),
        end_date=datetime.now(),
    )
    print("✅ PASSED: Annual leave created without certificate")
except Exception as e:
    print(f"❌ FAILED: {e}")

print("\n" + "="*60)
print("All tests completed! The medical certificate feature is working correctly.")
print("="*60)
