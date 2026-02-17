"""
Test script to verify Gemini AI API key and check for quota/limits
"""
import asyncio
from google import genai
from google.genai import types
import os
import sys
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings
from app.services.ai_service import gemini_service


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_status(label, status, details=""):
    """Print a status line"""
    symbol = "✅" if status else "❌"
    print(f"{symbol} {label}: {details}")


async def test_api_key_validity():
    """Test if the API key is valid and working"""
    print_header("Testing Gemini API Key")
    
    api_key = settings.GEMINI_API_KEY
    model_name = settings.GEMINI_MODEL
    
    # Check if API key is configured
    if not api_key or api_key == "your-gemini-api-key-here":
        print_status("API Key Configuration", False, "API key not configured in .env file")
        return False
    
    print_status("API Key Found", True, f"Key: {api_key[:20]}...{api_key[-4:]}")
    print_status("Model", True, model_name)
    
    try:
        # Initialize client
        client = genai.Client(api_key=api_key)
        print_status("Client Initialization", True, "Successfully created Gemini client")
        
        # Test with a simple prompt
        print("\n🔄 Testing API call with simple prompt...")
        
        test_prompt = "Say 'API is working' in exactly 3 words."
        
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=model_name,
            contents=test_prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=50,
            )
        )
        
        response_text = response.text.strip()
        print_status("API Call", True, f"Response: '{response_text}'")
        
        # Check response metadata
        if hasattr(response, 'usage_metadata'):
            print("\n📊 Token Usage:")
            metadata = response.usage_metadata
            if hasattr(metadata, 'prompt_token_count'):
                print(f"   - Prompt tokens: {metadata.prompt_token_count}")
            if hasattr(metadata, 'candidates_token_count'):
                print(f"   - Response tokens: {metadata.candidates_token_count}")
            if hasattr(metadata, 'total_token_count'):
                print(f"   - Total tokens: {metadata.total_token_count}")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print_status("API Call", False, f"Error: {error_msg}")
        
        # Check for specific error types
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg.upper():
            print("\n⚠️  QUOTA/RATE LIMIT ERROR DETECTED!")
            print("   Your API key has exceeded its quota or rate limit.")
            print("   Solutions:")
            print("   1. Wait for quota to reset (usually resets daily)")
            print("   2. Check your quota at: https://aistudio.google.com/app/apikey")
            print("   3. Upgrade your API plan if needed")
            
        elif "401" in error_msg or "UNAUTHENTICATED" in error_msg.upper():
            print("\n⚠️  AUTHENTICATION ERROR!")
            print("   Your API key is invalid or has been revoked.")
            print("   Solutions:")
            print("   1. Generate a new API key at: https://aistudio.google.com/app/apikey")
            print("   2. Update your .env file with the new key")
            
        elif "403" in error_msg or "PERMISSION_DENIED" in error_msg.upper():
            print("\n⚠️  PERMISSION ERROR!")
            print("   Your API key doesn't have permission to use this model.")
            print("   Solutions:")
            print("   1. Check if the model name is correct in .env")
            print("   2. Verify your API key has access to Gemini models")
            
        elif "INVALID_ARGUMENT" in error_msg.upper():
            print("\n⚠️  INVALID ARGUMENT ERROR!")
            print("   The request parameters are invalid.")
            print("   Check your model name and API configuration.")
        
        return False


async def test_leave_evaluation():
    """Test actual leave evaluation functionality"""
    print_header("Testing Leave Evaluation with AI")
    
    if not gemini_service.is_configured():
        print_status("AI Service", False, "AI service not configured")
        return False
    
    print_status("AI Service", True, "AI service is configured")
    
    # Create a test leave request
    test_data = {
        "leave_type": "SICK_LEAVE",
        "start_date": "2026-02-18",
        "end_date": "2026-02-19",
        "requested_days": 2.0,
        "reason_text": "I have a severe fever and need rest as advised by my doctor.",
        "policy": {
            "SICK_LEAVE": {"allocation": 5, "balance": 3}
        },
        "history_stats": {
            "sick_leaves_taken": 2,
            "total_leaves_taken": 5
        },
        "employee_context": {
            "name": "Test Employee",
            "department": "IT"
        }
    }
    
    print("\n🔄 Evaluating test leave request...")
    print(f"   Leave Type: {test_data['leave_type']}")
    print(f"   Duration: {test_data['requested_days']} days")
    print(f"   Reason: {test_data['reason_text']}")
    
    try:
        result = await gemini_service.evaluate_leave_request(**test_data)
        
        if result.get("error"):
            print_status("Leave Evaluation", False, f"Error: {result['error']}")
            return False
        
        print_status("Leave Evaluation", True, "Successfully evaluated")
        print("\n📋 AI Evaluation Results:")
        print(f"   - Category: {result.get('reason_category', 'N/A')}")
        print(f"   - Validity Score: {result.get('validity_score', 0)}/100")
        print(f"   - Recommended Action: {result.get('recommended_action', 'N/A')}")
        print(f"   - Risk Flags: {', '.join(result.get('risk_flags', [])) or 'None'}")
        print(f"   - Rationale: {result.get('rationale', 'N/A')}")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print_status("Leave Evaluation", False, f"Error: {error_msg}")
        
        # Check for quota/limit errors
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg.upper():
            print("\n⚠️  API QUOTA EXCEEDED!")
            print("   You've hit your daily API request limit.")
        
        return False


def print_quota_info():
    """Print information about how to check API quota"""
    print_header("How to Check API Quota and Limits")
    
    print("\n📊 Checking Your Gemini API Quota:")
    print("   1. Visit: https://aistudio.google.com/app/apikey")
    print("   2. Click on your API key")
    print("   3. View usage statistics and limits")
    
    print("\n💡 Understanding Gemini API Limits (Free Tier):")
    print("   - Requests per minute (RPM): 15")
    print("   - Requests per day (RPD): 1,500")
    print("   - Tokens per minute (TPM): 1,000,000")
    
    print("\n⚠️  Common Quota Error Messages:")
    print("   • '429 Resource Exhausted' - Rate limit exceeded")
    print("   • 'Quota exceeded' - Daily limit reached")
    print("   • 'RESOURCE_EXHAUSTED' - Too many requests")
    
    print("\n🔧 Solutions for Quota Issues:")
    print("   1. Wait for quota to reset (usually at midnight UTC)")
    print("   2. Implement request throttling in your application")
    print("   3. Cache AI responses for similar requests")
    print("   4. Upgrade to a paid tier for higher limits")
    print("   5. Use multiple API keys with load balancing")
    
    print("\n📝 Error Handling in Code:")
    print("   The system automatically handles quota errors by:")
    print("   - Catching exceptions during API calls")
    print("   - Routing to MANUAL_REVIEW when AI fails")
    print("   - Logging error details for debugging")
    print("   - Providing fallback mechanisms")


async def main():
    """Main test function"""
    print("\n" + "=" * 80)
    print("  GEMINI AI API KEY AND QUOTA TESTER")
    print("  " + str(datetime.now()))
    print("=" * 80)
    
    # Test 1: API Key Validity
    api_working = await test_api_key_validity()
    
    # Test 2: Leave Evaluation (only if API is working)
    if api_working:
        await test_leave_evaluation()
    
    # Print quota information
    print_quota_info()
    
    # Final summary
    print_header("Test Summary")
    if api_working:
        print("✅ All tests passed! Your Gemini AI integration is working correctly.")
        print("   You can now use AI-powered leave evaluation in the system.")
    else:
        print("❌ Tests failed. Please check the errors above and fix the issues.")
        print("   The system will fall back to MANUAL_REVIEW for leave requests.")
    
    print("\n" + "=" * 80)
    print()


if __name__ == "__main__":
    asyncio.run(main())
