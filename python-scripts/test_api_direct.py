#!/usr/bin/env python3
import requests
import json

def test_api():
    print("=== TESTING HERMAN MILLER API ===")
    
    # Test with the known working query from the user's network console
    test_queries = [
        "Zeph Chair",  # Known to work
        "Aeron Chair", # Should work
        "Caper Chair", # Should work
        "leeway stool" # Geiger product - might not work
    ]
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        
        url = f"https://www.hermanmiller.com/services/search/images?core=europe/en_gb&fp={query}&c=9"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Referer': 'https://www.hermanmiller.com/',
            'Origin': 'https://www.hermanmiller.com'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                print(f"  Found {len(items)} images")
                
                if items:
                    print(f"  First image: {items[0].get('title', 'No title')}")
            else:
                print(f"  Error: {response.text[:100]}")
                
        except Exception as e:
            print(f"  Exception: {e}")

if __name__ == "__main__":
    test_api()
