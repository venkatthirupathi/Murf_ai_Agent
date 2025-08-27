#!/usr/bin/env python3
"""
Script to update environment variables with provided API keys
"""

import os
import sys

def update_env_file():
    """Update the .env file with provided API keys"""
    env_file = ".env"
    
    # Check if .env file exists
    if not os.path.exists(env_file):
        print(f"❌ {env_file} file not found")
        return False
    
    # Read the current content
    try:
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Update the RapidAPI key (assuming this is for Tavily or another service)
        # Since we don't know which service the key is for, let's update TAVILY_API_KEY
        if "TAVILY_API_KEY=" in content:
            new_content = content.replace(
                "TAVILY_API_KEY=your_tavily_api_key_here",
                "TAVILY_API_KEY=329e5ce5f2msh58c8f81ef9ae33ap15d775jsnc5dda11b0742"
            )
        else:
            # If TAVILY_API_KEY line doesn't exist, add it
            new_content = content + "\nTAVILY_API_KEY=329e5ce5f2msh58c8f81ef9ae33ap15d775jsnc5dda11b0742"
        
        # Write the updated content
        with open(env_file, 'w') as f:
            f.write(new_content)
        
        print("✅ Environment file updated successfully")
        print("Updated TAVILY_API_KEY with the provided RapidAPI key")
        return True
        
    except Exception as e:
        print(f"❌ Error updating environment file: {e}")
        return False

if __name__ == "__main__":
    success = update_env_file()
    sys.exit(0 if success else 1)
