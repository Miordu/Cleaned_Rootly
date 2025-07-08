#!/usr/bin/env python3
"""Simple Flask debug script to identify 500 errors."""

import requests
import subprocess
import time
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_endpoint(url, method='GET', data=None, files=None):
    """Test a specific endpoint and log detailed error info."""
    try:
        if method == 'POST':
            response = requests.post(url, data=data, files=files)
        else:
            response = requests.get(url)
        
        logger.info(f"{method} {url}: {response.status_code}")
        
        if response.status_code >= 400:
            logger.error(f"Response content: {response.text[:500]}...")
        
        return response.status_code < 400
    except Exception as e:
        logger.error(f"Error testing {url}: {e}")
        return False

def main():
    # Start Flask server in background
    env = os.environ.copy()
    env['FLASK_APP'] = 'server.py'
    env['FLASK_ENV'] = 'development'
    
    logger.info("Starting Flask server...")
    server_process = subprocess.Popen(
        ['flask', 'run'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(3)
    
    try:
        base_url = "http://127.0.0.1:5000"
        
        # Test basic endpoints
        logger.info("Testing endpoints...")
        
        # Test homepage
        test_endpoint(f"{base_url}/")
        
        # Test register GET (should work)
        test_endpoint(f"{base_url}/register")
        
        # Test register POST (might fail)
        test_data = {
            'username': 'debuguser',
            'email': 'debug@test.com',
            'password': 'testpass123',
            'region_id': '1'
        }
        test_endpoint(f"{base_url}/register", 'POST', data=test_data)
        
        # Test login GET
        test_endpoint(f"{base_url}/login")
        
        # Test browse plants
        test_endpoint(f"{base_url}/browse-plants")
        
    finally:
        server_process.terminate()
        server_process.wait()
        logger.info("Server stopped")

if __name__ == "__main__":
    main()
