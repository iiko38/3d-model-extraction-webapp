#!/usr/bin/env python3
import requests
import time
import random
from urllib.parse import quote_plus

def test_simple_search():
    print("=== TESTING SIMPLE SEARCH APPROACH ===")
    
    # Test with the simple product names
    test_products = [
        "zeph stool",
        "aeron chairs", 
        "cosm chairs",
        "caper stacking chair"
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
        
        # Build API URL (simple approach)
        encoded_product = quote_plus(product_name)
        api_url = f"{API_BASE_URL}?core=europe/en_gb&fp={encoded_product}&c=9"
        
        print(f"  API URL: {api_url}")
        
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
                    print(f"  Sample URLs:")
                    for i, item in enumerate(items[:3]):
                        print(f"    {i+1}. {item.get('imageLink', 'No URL')}")
            else:
                print(f"  Error: {response.text[:100]}")
                
        except Exception as e:
            print(f"  Exception: {e}")

if __name__ == "__main__":
    test_simple_search()
