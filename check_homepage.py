#!/usr/bin/env python3
"""Check what the Flask homepage actually returns."""

import subprocess
import time
import requests
import os

def start_server():
    """Start Flask server."""
    env = os.environ.copy()
    env['FLASK_APP'] = 'server.py'
    env['FLASK_ENV'] = 'development'
    
    process = subprocess.Popen(
        ['flask', 'run'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(3)  # Wait for server to start
    return process

def check_homepage():
    """Check homepage content."""
    try:
        response = requests.get('http://127.0.0.1:5000/', timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.text)}")
        print(f"Content Type: {response.headers.get('content-type', 'Not Set')}")
        print("\n--- First 500 characters of response ---")
        print(response.text[:500])
        print("\n--- Last 500 characters of response ---")
        print(response.text[-500:])
        
        # Check for specific content
        if "Rootly" in response.text:
            print("\n✅ Found 'Rootly' in response")
        else:
            print("\n❌ 'Rootly' not found in response")
        
        if "bootstrap" in response.text.lower():
            print("✅ Found Bootstrap reference")
        else:
            print("❌ Bootstrap reference not found")
            
        return True
    except Exception as e:
        print(f"Error checking homepage: {e}")
        return False

def main():
    print("Starting Flask server...")
    server = start_server()
    
    try:
        check_homepage()
    finally:
        print("\nStopping server...")
        server.terminate()
        server.wait()

if __name__ == "__main__":
    main()
