"""
Quick test script to verify email sending works
Run with: python test_email.py
"""
import sys
sys.path.append(".")

import asyncio
from app.services.email_service import email_service


async def test_email():
    print("=" * 60)
    print("EMAIL TEST - PROFESSIONAL TEMPLATE WITH REASON")
    print("=" * 60)
    print(f"SMTP Host: {email_service.host}")
    print(f"SMTP Port: {email_service.port}")
    print(f"SMTP User: {email_service.username}")
    print(f"From Name: {email_service.from_name}")
    print(f"From Email: {email_service.from_email}")
    print("=" * 60)
    
    # Test sending to the same email (yourself)
    test_to_email = email_service.username  # Send to yourself for testing
    
    print(f"\n📧 Sending test APPROVAL email to: {test_to_email}")
    
    result = await email_service.send_leave_approved(
        to_email=test_to_email,
        employee_name="Alex Rivera",
        leave_type="ANNUAL",
        start_date="2026-02-10",
        end_date="2026-02-12",
        total_days=3,
        reason_text="I need to attend my sister's wedding in Mumbai. It's a family event and very important to me.",
        explanation="Your leave balance is sufficient and dates are approved. Enjoy the wedding!"
    )
    
    if result:
        print("\n✅ SUCCESS! Approval email sent.")
    else:
        print("\n❌ FAILED! Approval email not sent.")
    
    print("\n📧 Sending test REJECTION email to: {test_to_email}")
    
    result2 = await email_service.send_leave_rejected(
        to_email=test_to_email,
        employee_name="Alex Rivera",
        leave_type="SICK",
        start_date="2026-02-15",
        end_date="2026-02-17",
        total_days=3,
        reason="Insufficient sick leave balance remaining for this period.",
        employee_reason="I have been experiencing severe back pain and need to consult a specialist."
    )
    
    if result2:
        print("\n✅ SUCCESS! Rejection email sent.")
    else:
        print("\n❌ FAILED! Rejection email not sent.")
    
    print("\n📧 Sending test PENDING REVIEW email to: {test_to_email}")
    
    result3 = await email_service.send_leave_pending_review(
        to_email=test_to_email,
        employee_name="Alex Rivera",
        leave_type="ANNUAL",
        start_date="2026-03-01",
        end_date="2026-03-15",
        total_days=11,
        reason_text="Extended vacation to Europe - visiting family and exploring historical sites."
    )
    
    if result3:
        print("\n✅ SUCCESS! Pending review email sent.")
    else:
        print("\n❌ FAILED! Pending review email not sent.")
    
    print("\n" + "=" * 60)
    print("Check your inbox at:", test_to_email)
    print("You should see 3 professional emails with employee reasons!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_email())
