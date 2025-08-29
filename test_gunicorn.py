#!/usr/bin/env python3
"""
Test script to verify Gunicorn + Uvicorn setup
"""

import subprocess
import sys
import time

def test_gunicorn():
    """Test if gunicorn can be imported and used"""
    try:
        import gunicorn
        import uvicorn
        print("✅ Gunicorn and Uvicorn are available")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Run: pip install gunicorn uvicorn")
        return False

def check_requirements():
    """Check if all requirements are installed"""
    try:
        import fastapi
        import assemblyai
        import google.generativeai as genai
        import dotenv
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing production deployment setup...")
    
    print("\n1. Checking package availability:")
    gunicorn_ok = test_gunicorn()
    
    print("\n2. Checking requirements:")
    requirements_ok = check_requirements()
    
    print("\n3. Testing production run script:")
    try:
        import run_prod
        print("✅ run_prod.py imports successfully")
    except Exception as e:
        print(f"❌ Error importing run_prod.py: {e}")
    
    print("\n📋 Summary:")
    if gunicorn_ok and requirements_ok:
        print("✅ All tests passed! Ready for production deployment.")
        print("\nTo run with Gunicorn:")
        print("gunicorn app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000")
    else:
        print("❌ Some tests failed. Please check the requirements.")
        sys.exit(1)
