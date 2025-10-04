#!/usr/bin/env python3
"""
Test script for AI service integration
"""
import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from api.ai_service import ai_service

def test_ai_service():
    """Test the AI service functionality"""
    print("🤖 Testing AI Service Integration")
    print("=" * 50)
    
    # Test 1: Check if AI service is available
    print("1. Checking AI service availability...")
    is_available = ai_service.is_available()
    print(f"   AI Service Available: {'✅ Yes' if is_available else '❌ No'}")
    
    if not is_available:
        print("\n⚠️  AI service is not available. Please ensure:")
        print("   - Ollama is installed and running")
        print("   - Mistral model is pulled: ollama pull mistral:7b-instruct")
        print("   - Ollama service is running: ollama serve")
        return False
    
    # Test 2: Generate a simple response
    print("\n2. Testing AI response generation...")
    test_message = "Hello, I'm feeling a bit anxious today. Can you help me?"
    
    try:
        result = ai_service.generate_response(test_message)
        
        if result['success']:
            print("   ✅ AI response generated successfully")
            print(f"   Model: {result.get('model', 'unknown')}")
            print(f"   Response: {result['message'][:100]}...")
        else:
            print("   ❌ Failed to generate AI response")
            print(f"   Error: {result.get('error', 'unknown')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception during AI response generation: {e}")
        return False
    
    print("\n🎉 All tests passed! AI service is working correctly.")
    return True

if __name__ == "__main__":
    success = test_ai_service()
    sys.exit(0 if success else 1)
