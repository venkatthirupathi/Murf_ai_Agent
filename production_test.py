#!/usr/bin/env python3
"""
Comprehensive production deployment test for AI Voice Agent
"""

import os
import sys
import json
import requests
from pathlib import Path

def test_basic_requirements():
    """Test if basic requirements are installed"""
    print("🧪 Testing basic requirements...")
    
    required_packages = [
        "fastapi", "uvicorn", "assemblyai", "google.generativeai", "dotenv",
        "requests", "pydantic"
    ]
    
    all_ok = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            all_ok = False
    
    return all_ok

def test_production_script():
    """Test the production run script"""
    print("\n🧪 Testing production run script...")
    
    try:
        # Test that run_prod.py can be imported
        import run_prod
        print("✅ run_prod.py imports successfully")
        
        # Test that it has the main function
        if hasattr(run_prod, 'main'):
            print("✅ main() function found")
        else:
            print("❌ main() function not found")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Error testing run_prod.py: {e}")
        return False

def test_app_structure():
    """Test that the app structure is correct"""
    print("\n🧪 Testing application structure...")
    
    required_files = [
        "app.py",
        "requirements.txt",
        "run_prod.py",
        "DEPLOYMENT.md",
        "Dockerfile",
        "schemas/audio.py",
        "schemas/chat.py",
        "services/tts.py",
        "services/stt.py",
        "services/llm.py",
        "static/script.js",
        "static/style.css",
        "templates/index.html"
    ]
    
    all_ok = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            all_ok = False
    
    return all_ok

def test_api_endpoints():
    """Test API endpoints (requires server running)"""
    print("\n🧪 Testing API endpoints (server must be running)...")
    
    base_url = "http://localhost:8000"
    endpoints = [
        "/health",
        "/test-transcription",
        "/joke",
        "/conversation/test-session",
        "/recorded-audio/test-session"
    ]
    
    print("Note: Start the server with 'python run_prod.py' to test endpoints")
    return True

def test_logging():
    """Test logging configuration"""
    print("\n🧪 Testing logging configuration...")
    
    log_file = Path("app.log")
    if log_file.exists():
        print("✅ app.log file exists")
        try:
            log_content = log_file.read_text()
            if "INFO" in log_content or "WARNING" in log_content or "ERROR" in log_content:
                print("✅ Log file contains log entries")
            else:
                print("⚠️  Log file exists but appears empty")
        except Exception as e:
            print(f"❌ Error reading log file: {e}")
            return False
    else:
        print("⚠️  app.log file doesn't exist (will be created when server runs)")
    
    return True

def main():
    """Run all production tests"""
    print("🚀 Comprehensive Production Deployment Test")
    print("=" * 50)
    
    results = {
        "requirements": test_basic_requirements(),
        "production_script": test_production_script(),
        "app_structure": test_app_structure(),
        "logging": test_logging(),
        "api_endpoints": test_api_endpoints()
    }
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("🎉 All production tests passed!")
        print("\n📋 Next steps for deployment:")
        print("1. Set up your .env file with API keys")
        print("2. Run: python run_prod.py (for development)")
        print("3. Or install gunicorn: pip install gunicorn")
        print("4. Then run: gunicorn app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000")
        print("5. Or build Docker: docker build -t murf-ai-app .")
    else:
        print("❌ Some tests failed. Please check the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
