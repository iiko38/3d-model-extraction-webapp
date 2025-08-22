#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def test_zeph_chair_scraping():
    """Test scraping images from the Zeph Chair product page."""
    
    url = "https://www.hermanmiller.com/en_gb/resources/3d-models-and-planning-tools/product-models/individual/zeph-chair-with-arms/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"Testing URL: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("=== TESTING SELECTORS ===")
        
        # Test the specific selector you provided
        main_image = soup.select_one("#content > div > div > div > div > div > div.modelDetails.section.col-xs-12.first.odd.default-style > div > div > div > div > div.itemDetails-description-container.col-sm-6.col-lg-7 > div.itemDetails-images-container > div.itemDetails-images-selected-container > picture.itemDetails-image-selected.active > img")
        
        if main_image:
            print("✓ Found main image with your selector!")
            print(f"  Src: {main_image.get('src')}")
            print(f"  Alt: {main_image.get('alt')}")
        else:
            print("✗ Main image selector not found")
        
        # Test other selectors
        print("\n=== TESTING OTHER SELECTORS ===")
        
        selectors_to_test = [
            ".itemDetails-images-container img",
            ".product-images img", 
            ".model-images img",
            "img[src*='product']",
            "img[src*='chair']",
            "img[src*='zeph']"
        ]
        
        for selector in selectors_to_test:
            images = soup.select(selector)
            print(f"{selector}: {len(images)} images found")
            for i, img in enumerate(images[:3]):  # Show first 3
                src = img.get('src', '')
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(url, src)
                print(f"  {i+1}. {src[:80]}...")
        
        # Show all images on the page
        print("\n=== ALL IMAGES ON PAGE ===")
        all_images = soup.find_all('img')
        print(f"Total images found: {len(all_images)}")
        
        for i, img in enumerate(all_images[:10]):  # Show first 10
            src = img.get('src', '')
            alt = img.get('alt', '')
            if src:
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(url, src)
                print(f"{i+1}. {src[:60]}... | Alt: {alt[:30]}...")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_zeph_chair_scraping()
