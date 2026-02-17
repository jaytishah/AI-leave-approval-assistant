"""
Real-time API Quota Monitor
Helps you check current API status and provides detailed quota information
"""
import asyncio
from google import genai
from google.genai import types
import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
from app.core.config import settings


class QuotaMonitor:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.client = None
    
    def print_box(self, title, content, status="info"):
        """Print a formatted box"""
        symbols = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "quota": "📊"
        }
        symbol = symbols.get(status, "•")
        
        print(f"\n{symbol}  {title}")
        print("─" * 70)
        for line in content:
            print(f"  {line}")
    
    async def check_api_status(self):
        """Check if API is currently accessible"""
        try:
            self.client = genai.Client(api_key=self.api_key)
            
            # Try a minimal request
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents="Hi",
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=10,
                )
            )
            
            return True, "API is working", response
            
        except Exception as e:
            error_msg = str(e)
            
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg.upper():
                return False, "QUOTA_EXCEEDED", error_msg
            elif "401" in error_msg or "UNAUTHENTICATED" in error_msg.upper():
                return False, "INVALID_KEY", error_msg
            elif "403" in error_msg or "PERMISSION_DENIED" in error_msg.upper():
                return False, "PERMISSION_DENIED", error_msg
            else:
                return False, "API_ERROR", error_msg
    
    def get_quota_info(self):
        """Get quota information based on plan"""
        return {
            "free_tier": {
                "rpm": 15,  # Requests Per Minute
                "rpd": 1500,  # Requests Per Day
                "tpm": 1000000,  # Tokens Per Minute
                "reset": "Daily at 00:00 UTC"
            },
            "pay_as_you_go": {
                "rpm": 1000,
                "rpd": 50000,
                "tpm": 4000000,
                "reset": "Per minute"
            }
        }
    
    def calculate_reset_time(self):
        """Calculate when quota might reset"""
        now = datetime.utcnow()
        midnight_utc = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        time_until_reset = midnight_utc - now
        
        hours = int(time_until_reset.total_seconds() // 3600)
        minutes = int((time_until_reset.total_seconds() % 3600) // 60)
        
        return f"{hours}h {minutes}m"
    
    async def run(self):
        """Run the quota monitor"""
        print("\n" + "=" * 70)
        print("         GEMINI API QUOTA MONITOR")
        print("         " + str(datetime.now()))
        print("=" * 70)
        
        # Check API Status
        print("\n🔍 Checking API Status...")
        is_working, status, details = await self.check_api_status()
        
        if is_working:
            self.print_box(
                "API STATUS: WORKING ✅",
                [
                    "Your Gemini API is operational and accepting requests.",
                    "AI-powered leave evaluation is available.",
                    "",
                    f"Response received successfully from {self.model_name}"
                ],
                "success"
            )
        else:
            if status == "QUOTA_EXCEEDED":
                self.print_box(
                    "API STATUS: QUOTA EXCEEDED ⚠️",
                    [
                        "Your API key has exceeded its quota limit.",
                        "All AI evaluations will route to MANUAL_REVIEW.",
                        "",
                        f"Time until estimated reset: {self.calculate_reset_time()}",
                        "",
                        "Error details:",
                        str(details)[:200] + "..."
                    ],
                    "error"
                )
            elif status == "INVALID_KEY":
                self.print_box(
                    "API STATUS: INVALID KEY ❌",
                    [
                        "Your API key is invalid or has been revoked.",
                        "Please generate a new key at:",
                        "https://aistudio.google.com/app/apikey"
                    ],
                    "error"
                )
            elif status == "PERMISSION_DENIED":
                self.print_box(
                    "API STATUS: PERMISSION DENIED ❌",
                    [
                        "Your API key doesn't have permission for this model.",
                        "Check your model name in .env file:",
                        f"Current: {self.model_name}"
                    ],
                    "error"
                )
            else:
                self.print_box(
                    "API STATUS: ERROR ❌",
                    [
                        "An unexpected error occurred:",
                        str(details)[:200] + "..."
                    ],
                    "error"
                )
        
        # Show Quota Information
        quota_info = self.get_quota_info()
        
        self.print_box(
            "FREE TIER LIMITS",
            [
                f"Requests Per Minute (RPM): {quota_info['free_tier']['rpm']}",
                f"Requests Per Day (RPD): {quota_info['free_tier']['rpd']}",
                f"Tokens Per Minute (TPM): {quota_info['free_tier']['tpm']:,}",
                f"Quota Reset: {quota_info['free_tier']['reset']}",
                "",
                "Common causes of quota exhaustion:",
                "  • Made more than 1,500 requests today",
                "  • Made more than 15 requests in the last minute",
                "  • Multiple instances of the app running"
            ],
            "quota"
        )
        
        self.print_box(
            "PAID TIER LIMITS",
            [
                f"Requests Per Minute (RPM): {quota_info['pay_as_you_go']['rpm']}",
                f"Requests Per Day (RPD): {quota_info['pay_as_you_go']['rpd']:,}",
                f"Tokens Per Minute (TPM): {quota_info['pay_as_you_go']['tpm']:,}",
                f"Quota Reset: {quota_info['pay_as_you_go']['reset']}",
                "",
                "To upgrade, visit:",
                "https://ai.google.dev/pricing"
            ],
            "info"
        )
        
        # Solutions
        self.print_box(
            "SOLUTIONS & NEXT STEPS",
            [
                "1️⃣  Check Your Usage Dashboard:",
                "   → Visit: https://aistudio.google.com/app/apikey",
                "   → Click on your API key to view usage statistics",
                "",
                "2️⃣  Wait for Quota Reset:",
                f"   → Estimated time: {self.calculate_reset_time()} (until midnight UTC)",
                "   → Free tier resets daily at 00:00 UTC",
                "",
                "3️⃣  Get a New API Key (if testing heavily):",
                "   → Generate at: https://aistudio.google.com/app/apikey",
                "   → Update backend/.env with new GEMINI_API_KEY",
                "",
                "4️⃣  Upgrade to Paid Tier:",
                "   → 66x more RPM (15 → 1,000)",
                "   → 33x more RPD (1,500 → 50,000)",
                "   → Visit: https://ai.google.dev/pricing",
                "",
                "5️⃣  Implement Caching (for production):",
                "   → Cache similar leave requests",
                "   → Reduce duplicate AI calls",
                "   → Store common evaluation patterns"
            ],
            "info"
        )
        
        # System Behavior
        self.print_box(
            "SYSTEM BEHAVIOR WHEN QUOTA EXCEEDED",
            [
                "✓ Application continues to work normally",
                "✓ Leave requests are accepted",
                "✓ AI evaluation automatically routes to: MANUAL_REVIEW",
                "✓ HR managers can still approve/reject manually",
                "✓ No data loss or system errors",
                "",
                "Impact:",
                "  • AI recommendations not available",
                "  • Validity scores not computed",
                "  • Risk flags not detected by AI",
                "  • Manual review required for all requests"
            ],
            "warning"
        )
        
        print("\n" + "=" * 70)
        print()


async def main():
    monitor = QuotaMonitor()
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())
