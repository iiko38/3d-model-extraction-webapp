#!/usr/bin/env python3
import requests
import time
import random
from urllib.parse import quote_plus

def test_general_names():
    print("=== TESTING GENERAL PRODUCT NAMES ===")
    
    # Test with the general product names that the API expects
    test_products = [
        "Zeph Chair",      # We know this works
        "Aeron Chair",     # Should work
        "Cosm Chair",      # Should work
        "Caper Chair",     # Should work
        "Eames Chair",     # Should work
        "Sayl Chair"       # Should work
    ]
    
    API_BASE_URL = "https://www.hermanmiller.com/services/search/images"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'OKII-Image-Enricher/0.1 (contact: you@example.com)',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Referer': 'https://www.hermanmiller.com/',
        'Origin': 'https://www.hermanmiller.com'
    })
    
    for product_name in test_products:
        print(f"\nTesting: '{product_name}'")
        
        # Build API URL
        encoded_product = quote_plus(product_name)
        api_url = f"{API_BASE_URL}?core=europe/en_gb&fp={encoded_product}&c=9"
        
        try:
            # Polite delay
            time.sleep(random.uniform(1.0, 2.0))
            
            response = session.get(api_url, timeout=30)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                print(f"  Found {len(items)} images")
                
                if items:
                    print(f"  First image: {items[0].get('title', 'No title')}")
                else:
                    print(f"  No images found")
            else:
                print(f"  Error: {response.text[:100]}")
                
        except Exception as e:
            print(f"  Exception: {e}")

if __name__ == "__main__":
    test_general_names()
