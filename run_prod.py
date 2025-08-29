#!/usr/bin/env python3
"""
Production startup script for AI Voice Agent
"""

import os
import uvicorn
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    required_vars = ["MURF_API_KEY", "ASSEMBLYAI_API_KEY", "GEMINI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("⚠️  Warning: Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease create a .env file with your API keys.")
        print("See SETUP.md for instructions.")
        print("\nContinuing anyway... (some features may not work)")
    
    # Production server configuration
    print("🚀 Starting AI Voice Agent in production mode...")
    print("📱 Open http://localhost:8000 in your browser")
    print("🛑 Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=False,  # Disable auto-reload in production
        log_level=os.getenv("LOG_LEVEL", "info"),
        workers=int(os.getenv("WORKERS", 1)),  # Use 1 worker by default
        timeout_keep_alive=30,
    )

if __name__ == "__main__":
    main()
