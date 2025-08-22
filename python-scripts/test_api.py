#!/usr/bin/env python3
import requests
import json

def test_api():
    """Test the Herman Miller image API."""
    
    # Test with the exact query from your network console
    test_queries = [
        "Zeph Chair",
        "zeph stool", 
        "Aeron Chair",
        "Eames Chair"
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'OKII-Image-Enricher/0.1 (contact: you@example.com)',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Referer': 'https://www.hermanmiller.com/',
        'Origin': 'https://www.hermanmiller.com'
    })
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing query: '{query}'")
        print(f"{'='*60}")
        
        # Build API URL
        from urllib.parse import quote_plus
        encoded_query = quote_plus(query)
        api_url = f"https://www.hermanmiller.com/services/search/images?core=europe/en_gb&fp={encoded_query}&c=9"
        
        print(f"API URL: {api_url}")
        
        try:
            response = session.get(api_url, timeout=30)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                print(f"Images found: {len(items)}")
                
                if items:
                    print("Sample images:")
                    for i, item in enumerate(items[:3]):  # Show first 3
                        print(f"  {i+1}. {item.get('title', 'No title')}")
                        print(f"     ID: {item.get('id', 'No ID')}")
                        print(f"     Alt: {item.get('imageAlt', 'No alt')}")
                        
                        # Show renditions
                        renditions = item.get('renditions', [])
                        if renditions:
                            print(f"     Renditions: {len(renditions)}")
                            for rendition in renditions[:2]:  # Show first 2 renditions
                                print(f"       - {rendition.get('dimension', 'No dim')} ({rendition.get('size', 'No size')})")
                else:
                    print("No images found")
            else:
                print(f"Error: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
