#!/usr/bin/env python3
"""Quick test script to verify the main Flask app fixes."""

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
        ['python', 'server.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(3)  # Wait for server to start
    return process

def test_endpoints():
    """Test the main Flask endpoints that were fixed."""
    base_url = "http://127.0.0.1:5001"
    
    tests = [
        ("Homepage", f"{base_url}/"),
        ("Browse Plants", f"{base_url}/browse-plants"),
        ("Search Plants", f"{base_url}/search-plants"),
        ("Login Page", f"{base_url}/login"),
        ("Register Page", f"{base_url}/register"),
    ]
    
    results = {}
    
    for name, url in tests:
        try:
            response = requests.get(url, timeout=10)
            results[name] = {
                'status': response.status_code,
                'success': response.status_code == 200,
                'error': None
            }
        except Exception as e:
            results[name] = {
                'status': 'Error',
                'success': False, 
                'error': str(e)
            }
    
    return results

def main():
    print("🧪 Testing Flask App Fixes...")
    print("=" * 50)
    
    server = start_server()
    
    try:
        results = test_endpoints()
        
        print("📊 Test Results:")
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result['success'])
        
        for name, result in results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"  {name}: {status} (Status: {result['status']})")
            if result['error']:
                print(f"    Error: {result['error']}")
        
        print("\n" + "=" * 50)
        print(f"🎯 Summary: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All core Flask app fixes are working!")
        else:
            print("⚠️  Some issues remain, but main fixes are applied")
            
    finally:
        server.terminate()
        server.wait()
        print("🛑 Server stopped")

if __name__ == "__main__":
    main()
