#!/usr/bin/env python3
"""
Deep Page Analysis Script
Analyze actual page structures and test image extraction strategies.
"""

import json
import pathlib
import requests
import bs4
import time
import random
from urllib.parse import urlparse
from typing import Dict, List

def get_products_with_source_pages():
    """Get products that actually have source pages."""
    library_root = pathlib.Path("library")
    products_with_sources = []
    
    for product_file in library_root.rglob("product.json"):
        try:
            with open(product_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            source_pages = data.get('source_pages', [])
            if source_pages:
                products_with_sources.append({
                    'file': product_file,
                    'brand': data.get('brand', 'unknown'),
                    'product': data.get('product', 'unknown'),
                    'source_pages': source_pages
                })
        except Exception as e:
            continue
    
    return products_with_sources

def analyze_page_type(url: str) -> str:
    """Determine if this is a listing page or individual product page."""
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    if 'individual' in path:
        return 'individual_product'
    elif 'product-models' in path and '?' in url:
        return 'category_listing'
    else:
        return 'other'

def test_image_extraction_on_page(url: str, product_name: str) -> Dict:
    """Test various image extraction strategies on a single page."""
    print(f"\n{'='*80}")
    print(f"ANALYZING: {product_name}")
    print(f"URL: {url}")
    print(f"Type: {analyze_page_type(url)}")
    print(f"{'='*80}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'OKII-Deep-Analysis/0.1 (contact: you@example.com)'
    })
    
    try:
        # Polite delay
        time.sleep(random.uniform(1.0, 2.0))
        
        response = session.get(url, timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to fetch: {response.status_code}")
            return {}
        
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        
        # Basic page info
        title = soup.title.string if soup.title else "No title"
        print(f"📄 Title: {title[:100]}...")
        print(f"📊 Page size: {len(response.content) / 1024:.1f} KB")
        
        # Count all images
        all_images = soup.find_all('img')
        print(f"🖼️  Total images: {len(all_images)}")
        
        # Test our extraction strategies
        strategies = {
            'product_images': 'img[src*="product"]',
            'hero_images': 'img[src*="hero"]',
            'gallery_images': 'img[src*="gallery"]',
            'main_images': 'img[src*="main"]',
            'thumbnail_images': 'img[src*="thumb"]',
            'large_images': 'img[width][height]',
            'alt_contains_product': 'img[alt*="product"]',
            'title_contains_product': 'img[title*="product"]'
        }
        
        results = {}
        for strategy_name, selector in strategies.items():
            matches = soup.select(selector)
            if matches:
                results[strategy_name] = len(matches)
                print(f"✅ {strategy_name}: {len(matches)} matches")
                
                # Show first match details
                first_match = matches[0]
                src = first_match.get('src', '')
                alt = first_match.get('alt', '')
                width = first_match.get('width', '')
                height = first_match.get('height', '')
                
                print(f"   First: {src[:80]}...")
                print(f"   Alt: {alt[:50]}...")
                if width and height:
                    print(f"   Size: {width}x{height}")
            else:
                print(f"❌ {strategy_name}: 0 matches")
        
        # Test structured data
        structured_data_count = 0
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'image' in data:
                    structured_data_count += 1
            except:
                continue
        
        if structured_data_count > 0:
            print(f"✅ Structured data with images: {structured_data_count} items")
        else:
            print(f"❌ No structured data with images found")
        
        # Analyze image sources
        image_sources = {}
        for img in all_images:
            src = img.get('src', '')
            if src:
                domain = urlparse(src).netloc
                if domain:
                    image_sources[domain] = image_sources.get(domain, 0) + 1
        
        if image_sources:
            print(f"🌐 Image sources:")
            for domain, count in sorted(image_sources.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   {domain}: {count}")
        
        return {
            'url': url,
            'page_type': analyze_page_type(url),
            'total_images': len(all_images),
            'strategies': results,
            'structured_data': structured_data_count,
            'image_sources': image_sources
        }
        
    except Exception as e:
        print(f"❌ Error analyzing page: {e}")
        return {}

def main():
    """Run deep page analysis."""
    print("DEEP PAGE STRUCTURE ANALYSIS")
    print("=" * 80)
    
    # Get products with source pages
    products = get_products_with_source_pages()
    print(f"Found {len(products)} products with source pages")
    
    # Analyze a few representative products
    test_products = []
    
    # Find different types of pages
    for product in products:
        for page in product['source_pages']:
            page_type = analyze_page_type(page)
            if page_type == 'individual_product' and len(test_products) < 3:
                test_products.append((product, page))
            elif page_type == 'category_listing' and len(test_products) < 5:
                test_products.append((product, page))
    
    print(f"\nTesting {len(test_products)} representative pages...")
    
    results = []
    for product, page in test_products:
        result = test_image_extraction_on_page(page, f"{product['brand']}:{product['product']}")
        if result:
            results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print("ANALYSIS SUMMARY")
    print(f"{'='*80}")
    
    if results:
        total_images = sum(r['total_images'] for r in results)
        avg_images = total_images / len(results)
        
        print(f"📊 Pages analyzed: {len(results)}")
        print(f"🖼️  Total images found: {total_images}")
        print(f"📈 Average images per page: {avg_images:.1f}")
        
        # Most successful strategies
        strategy_counts = {}
        for result in results:
            for strategy, count in result['strategies'].items():
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + count
        
        if strategy_counts:
            print(f"\n🎯 Most successful strategies:")
            for strategy, count in sorted(strategy_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   {strategy}: {count} total matches")
    
    print(f"\n{'='*80}")
    print("RECOMMENDATIONS")
    print(f"{'='*80}")
    
    if results:
        print("✅ Based on analysis, recommend:")
        print("   1. Use img[src*='product'] as primary selector")
        print("   2. Fall back to img[alt*='product'] for additional images")
        print("   3. Check for structured data (JSON-LD) images")
        print("   4. Filter by image size to avoid thumbnails")
        print("   5. Focus on individual product pages over listing pages")
    else:
        print("❌ No successful page analysis - may need to adjust approach")

if __name__ == "__main__":
    main()
