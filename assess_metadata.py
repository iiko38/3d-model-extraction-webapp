#!/usr/bin/env python3
"""
Metadata Assessment Script
Deep analysis of current product metadata and page structures.
"""

import sqlite3
import json
import pathlib
import requests
import bs4
import time
import random
from collections import defaultdict, Counter
from urllib.parse import urlparse
from typing import Dict, List, Set, Tuple

# Constants
DB_PATH = "library/index.sqlite"
LIBRARY_ROOT = pathlib.Path("library")

def get_db_connection():
    """Get database connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def analyze_database_structure():
    """Analyze the SQLite database structure and content."""
    print("=" * 60)
    print("DATABASE ANALYSIS")
    print("=" * 60)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables found: {[t[0] for t in tables]}")
    
    # Analyze products table
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    print(f"\nProducts: {product_count}")
    
    cursor.execute("SELECT brand, COUNT(*) FROM products GROUP BY brand ORDER BY COUNT(*) DESC")
    brands = cursor.fetchall()
    print("Brands breakdown:")
    for brand, count in brands:
        print(f"  {brand}: {count}")
    
    # Analyze files table
    cursor.execute("SELECT COUNT(*) FROM files")
    file_count = cursor.fetchone()[0]
    print(f"\nFiles: {file_count}")
    
    cursor.execute("SELECT file_type, COUNT(*) FROM files GROUP BY file_type ORDER BY COUNT(*) DESC")
    file_types = cursor.fetchall()
    print("File types breakdown:")
    for file_type, count in file_types:
        print(f"  {file_type}: {count}")
    
    # Check for source pages in files
    cursor.execute("SELECT COUNT(*) FROM files WHERE source_page IS NOT NULL AND source_page != ''")
    files_with_source = cursor.fetchone()[0]
    print(f"\nFiles with source pages: {files_with_source}")
    
    cursor.execute("SELECT DISTINCT source_page FROM files WHERE source_page IS NOT NULL AND source_page != '' LIMIT 10")
    sample_sources = cursor.fetchall()
    print("Sample source pages:")
    for (source,) in sample_sources:
        print(f"  {source}")
    
    conn.close()

def analyze_product_json_files():
    """Analyze the product.json files structure."""
    print("\n" + "=" * 60)
    print("PRODUCT.JSON ANALYSIS")
    print("=" * 60)
    
    product_files = list(LIBRARY_ROOT.rglob("product.json"))
    print(f"Found {len(product_files)} product.json files")
    
    if not product_files:
        print("No product.json files found!")
        return
    
    # Analyze structure of first few files
    sample_files = product_files[:5]
    structure_analysis = defaultdict(set)
    source_pages_count = 0
    products_with_source_pages = []
    
    for product_file in product_files:
        try:
            with open(product_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Track structure
            for key in data.keys():
                structure_analysis[key].add(type(data[key]).__name__)
            
            # Check for source pages
            source_pages = data.get('source_pages', [])
            if source_pages:
                source_pages_count += 1
                products_with_source_pages.append({
                    'file': product_file,
                    'brand': data.get('brand', 'unknown'),
                    'product': data.get('product', 'unknown'),
                    'source_pages': source_pages
                })
        
        except Exception as e:
            print(f"Error reading {product_file}: {e}")
    
    print(f"\nProducts with source pages: {source_pages_count}")
    print(f"Products without source pages: {len(product_files) - source_pages_count}")
    
    print("\nProduct.json structure analysis:")
    for key, types in structure_analysis.items():
        print(f"  {key}: {', '.join(types)}")
    
    # Show sample products with source pages
    if products_with_source_pages:
        print(f"\nSample products with source pages:")
        for product in products_with_source_pages[:5]:
            print(f"  {product['brand']}:{product['product']}")
            for page in product['source_pages'][:2]:  # Show first 2 pages
                print(f"    - {page}")
            if len(product['source_pages']) > 2:
                print(f"    ... and {len(product['source_pages']) - 2} more")
    
    return products_with_source_pages

def analyze_page_structure(url: str, product_name: str = "Unknown") -> Dict:
    """Analyze the structure of a product page."""
    print(f"\nAnalyzing page structure for: {product_name}")
    print(f"URL: {url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'OKII-Metadata-Assessor/0.1 (contact: you@example.com)'
    })
    
    try:
        # Polite delay
        time.sleep(random.uniform(0.5, 1.0))
        
        response = session.get(url, timeout=30)
        if response.status_code != 200:
            print(f"  Failed to fetch: {response.status_code}")
            return {}
        
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        
        analysis = {
            'title': soup.title.string if soup.title else None,
            'meta_description': soup.find('meta', attrs={'name': 'description'})['content'] if soup.find('meta', attrs={'name': 'description'}) else None,
            'image_selectors_found': [],
            'structured_data': [],
            'total_images': len(soup.find_all('img')),
            'image_sources': Counter(),
            'page_size_kb': len(response.content) / 1024
        }
        
        # Analyze images
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src:
                # Categorize image sources
                if 'product' in src.lower():
                    analysis['image_sources']['product'] += 1
                elif 'hero' in src.lower():
                    analysis['image_sources']['hero'] += 1
                elif 'gallery' in src.lower():
                    analysis['image_sources']['gallery'] += 1
                elif 'thumbnail' in src.lower():
                    analysis['image_sources']['thumbnail'] += 1
                else:
                    analysis['image_sources']['other'] += 1
                
                # Check for common selectors
                parent_classes = ' '.join(img.parent.get('class', [])) if img.parent else ''
                img_classes = ' '.join(img.get('class', []))
                
                if 'product' in parent_classes or 'product' in img_classes:
                    analysis['image_selectors_found'].append('product-related')
                if 'gallery' in parent_classes or 'gallery' in img_classes:
                    analysis['image_selectors_found'].append('gallery')
                if 'hero' in parent_classes or 'hero' in img_classes:
                    analysis['image_selectors_found'].append('hero')
        
        # Analyze structured data
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    analysis['structured_data'].append({
                        'type': data.get('@type', 'unknown'),
                        'has_image': 'image' in data,
                        'image_count': len(data.get('image', [])) if isinstance(data.get('image'), list) else (1 if data.get('image') else 0)
                    })
            except:
                continue
        
        print(f"  Page size: {analysis['page_size_kb']:.1f} KB")
        print(f"  Total images: {analysis['total_images']}")
        print(f"  Image sources: {dict(analysis['image_sources'])}")
        print(f"  Selectors found: {list(set(analysis['image_selectors_found']))}")
        print(f"  Structured data: {len(analysis['structured_data'])} items")
        
        return analysis
        
    except Exception as e:
        print(f"  Error analyzing page: {e}")
        return {}

def test_image_extraction_on_sample():
    """Test our image extraction logic on a few sample pages."""
    print("\n" + "=" * 60)
    print("IMAGE EXTRACTION TEST")
    print("=" * 60)
    
    # Get a few products with source pages
    products_with_sources = analyze_product_json_files()
    
    if not products_with_sources:
        print("No products with source pages found for testing!")
        return
    
    # Test on first 3 products
    test_products = products_with_sources[:3]
    
    for product in test_products:
        print(f"\nTesting: {product['brand']}:{product['product']}")
        
        # Test first source page
        if product['source_pages']:
            test_url = product['source_pages'][0]
            page_analysis = analyze_page_structure(test_url, product['product'])
            
            if page_analysis:
                # Test our extraction logic
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'OKII-Metadata-Assessor/0.1 (contact: you@example.com)'
                })
                
                time.sleep(random.uniform(0.5, 1.0))
                response = session.get(test_url, timeout=30)
                soup = bs4.BeautifulSoup(response.text, 'html.parser')
                
                # Test our selectors
                test_selectors = [
                    '.product-image img',
                    '.product-gallery img',
                    '.product-photo img',
                    '.product-thumbnail img',
                    '.hero-image img',
                    '.main-image img',
                    '[class*="product"][class*="image"] img',
                    'img[src*="product"]'
                ]
                
                print("  Testing selectors:")
                for selector in test_selectors:
                    matches = soup.select(selector)
                    if matches:
                        print(f"    {selector}: {len(matches)} matches")
                        # Show first match details
                        first_match = matches[0]
                        src = first_match.get('src', '')
                        alt = first_match.get('alt', '')
                        print(f"      First match: {src[:100]}... (alt: {alt[:50]})")

def analyze_url_patterns():
    """Analyze patterns in source URLs."""
    print("\n" + "=" * 60)
    print("URL PATTERN ANALYSIS")
    print("=" * 60)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT source_page FROM files WHERE source_page IS NOT NULL AND source_page != ''")
    source_pages = cursor.fetchall()
    
    if not source_pages:
        print("No source pages found in database!")
        conn.close()
        return
    
    domains = Counter()
    path_patterns = Counter()
    
    for (url,) in source_pages:
        try:
            parsed = urlparse(url)
            domains[parsed.netloc] += 1
            
            # Analyze path patterns
            path_parts = [p for p in parsed.path.split('/') if p]
            if path_parts:
                # Look for common patterns
                if len(path_parts) >= 2:
                    pattern = f"{path_parts[0]}/.../{path_parts[-1]}"
                    path_patterns[pattern] += 1
                else:
                    path_patterns[parsed.path] += 1
        
        except Exception as e:
            print(f"Error parsing URL {url}: {e}")
    
    print("Top domains:")
    for domain, count in domains.most_common(10):
        print(f"  {domain}: {count}")
    
    print("\nCommon path patterns:")
    for pattern, count in path_patterns.most_common(10):
        print(f"  {pattern}: {count}")
    
    conn.close()

def main():
    """Run comprehensive metadata assessment."""
    print("PRODUCT METADATA & PAGE STRUCTURE ASSESSMENT")
    print("=" * 60)
    
    # 1. Database analysis
    analyze_database_structure()
    
    # 2. Product.json analysis
    products_with_sources = analyze_product_json_files()
    
    # 3. URL pattern analysis
    analyze_url_patterns()
    
    # 4. Page structure analysis (if we have source pages)
    if products_with_sources:
        test_image_extraction_on_sample()
    
    print("\n" + "=" * 60)
    print("ASSESSMENT COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
