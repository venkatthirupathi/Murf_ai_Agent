#!/usr/bin/env python3
"""
Script to help update the .env file with actual API keys
"""

import os
import sys

def update_env_file():
    """Update the .env file with actual API keys"""
    
    # Read the current .env file
    env_path = ".env"
    
    if not os.path.exists(env_path):
        print("❌ .env file not found!")
        return False
    
    try:
        with open(env_path, 'r') as f:
            content = f.read()
        
        print("🔧 Updating .env file with your API keys")
        print("=" * 50)
        
        # Get API keys from user input
        murf_key = input("Enter your Murf AI API key: ").strip()
        assemblyai_key = input("Enter your AssemblyAI API key: ").strip()
        gemini_key = input("Enter your Google Gemini API key: ").strip()
        
        # Replace placeholder values
        updated_content = content.replace(
            "MURF_API_KEY=your_actual_murf_api_key_here",
            f"MURF_API_KEY={murf_key}"
        ).replace(
            "ASSEMBLYAI_API_KEY=your_actual_assemblyai_api_key_here",
            f"ASSEMBLYAI_API_KEY={assemblyai_key}"
        ).replace(
            "GEMINI_API_KEY=your_actual_gemini_api_key_here",
            f"GEMINI_API_KEY={gemini_key}"
        )
        
        # Write updated content
        with open(env_path, 'w') as f:
            f.write(updated_content)
        
        print("✅ .env file updated successfully!")
        print("🔑 API keys have been set")
        print("🚀 You can now run the application with: python run.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

if __name__ == "__main__":
    update_env_file()
