#!/usr/bin/env python3
"""
Simple Product Image Enrichment Script
Uses a simple mapping approach based on what we know works with the API.
"""

import json
import pathlib
import requests
import time
import random
import argparse
import logging
import sqlite3
from urllib.parse import quote_plus
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
LIBRARY_ROOT = pathlib.Path("library")
API_BASE_URL = "https://www.hermanmiller.com/services/search/images"
DEFAULT_SLEEP_MIN = 1.0
DEFAULT_SLEEP_MAX = 2.0

# Simple mapping of product names to API-compatible search terms
PRODUCT_MAPPING = {
    'zeph stool': 'Zeph Chair',
    'zeph chair': 'Zeph Chair',
    'aeron chairs': 'Aeron Chair',
    'aeron chair': 'Aeron Chair',
    'cosm chairs': 'Cosm Chair',
    'cosm chair': 'Cosm Chair',
    'caper stacking chair': 'Caper Chair',
    'caper chair': 'Caper Chair',
    'eames aluminum group chairs': 'Eames Chair',
    'eames chair': 'Eames Chair',
    'sayl chairs': 'Sayl Chair',
    'sayl chair': 'Sayl Chair',
    'mirra 2 chairs': 'Mirra Chair',
    'mirra chair': 'Mirra Chair',
    'verus chairs': 'Verus Chair',
    'verus chair': 'Verus Chair'
}

def get_products_with_source_pages() -> List[Dict]:
    """Get products that have source pages in their product.json files."""
    products = []
    
    for product_dir in LIBRARY_ROOT.rglob("product.json"):
        try:
            with open(product_dir, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if we have source pages
            source_pages = data.get('source_pages', [])
            if source_pages:
                products.append({
                    'product_uid': f"{data['brand']}:{data['product_slug']}",
                    'brand': data['brand'],
                    'product_name': data['product'],
                    'product_slug': data['product_slug'],
                    'source_pages': source_pages,
                    'product_dir': product_dir.parent,
                    'product_data': data
                })
        
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Error reading {product_dir}: {e}")
            continue
    
    return products

def search_product_images_simple(product_name: str, sleep_min: float = 1.0, sleep_max: float = 2.0) -> List[Dict]:
    """Search for product images using simple mapping approach."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'OKII-Image-Enricher/0.1 (contact: you@example.com)',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Referer': 'https://www.hermanmiller.com/',
        'Origin': 'https://www.hermanmiller.com'
    })
    
    # Get the mapped search term
    search_term = PRODUCT_MAPPING.get(product_name.lower(), product_name)
    
    # Build API URL
    encoded_term = quote_plus(search_term)
    api_url = f"{API_BASE_URL}?core=europe/en_gb&fp={encoded_term}&c=9"
    
    logger.info(f"Searching for '{product_name}' using term '{search_term}'")
    
    try:
        # Polite delay
        time.sleep(random.uniform(sleep_min, sleep_max))
        
        response = session.get(api_url, timeout=30)
        if response.status_code != 200:
            logger.warning(f"API request failed: {response.status_code}")
            return []
        
        data = response.json()
        items = data.get('items', [])
        
        logger.info(f"Found {len(items)} images for '{search_term}'")
        
        # Process images
        processed_images = []
        for item in items:
            image_data = {
                'id': item.get('id'),
                'title': item.get('title'),
                'alt': item.get('imageAlt'),
                'original_url': f"https://www.hermanmiller.com{item.get('imageLink')}",
                'search_term': search_term,
                'renditions': []
            }
            
            # Add renditions (different sizes)
            for rendition in item.get('renditions', []):
                rendition_data = {
                    'url': f"https://www.hermanmiller.com{rendition.get('imageLink')}",
                    'dimension': rendition.get('dimension'),
                    'size': rendition.get('size'),
                    'type': 'L' if '_L.' in rendition.get('imageLink', '') else 
                           'P' if '_P.' in rendition.get('imageLink', '') else 
                           'G' if '_G.' in rendition.get('imageLink', '') else 'unknown'
                }
                image_data['renditions'].append(rendition_data)
            
            processed_images.append(image_data)
        
        return processed_images
        
    except Exception as e:
        logger.error(f"Error searching images for {product_name}: {e}")
        return []

def insert_images_to_db(images: List[Dict], product_uid: str, variant: str = '') -> None:
    """Insert images into the database."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    for img in images:
        try:
            cursor.execute("""
                INSERT INTO images(product_uid, variant, image_url, provider, score, rationale, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, strftime('%s','now'), strftime('%s','now'))
                ON CONFLICT(product_uid, variant, image_url) DO UPDATE SET
                    score=excluded.score,
                    updated_at=excluded.updated_at
            """, (
                product_uid,
                variant,
                img['original_url'],
                'herman_miller_api',
                10.0,  # High score for API results
                f"Found via API search term: {img['search_term']}",
                'pending'
            ))
        except Exception as e:
            logger.error(f"Error inserting image {img.get('id', 'unknown')}: {e}")
    
    conn.commit()
    conn.close()

def enrich_product_images_simple(product: Dict, sleep_min: float = 1.0, sleep_max: float = 2.0) -> Dict:
    """Enrich a single product with images using simple approach."""
    logger.info(f"Enriching images for: {product['product_name']}")
    
    # Search for images using simple mapping
    images = search_product_images_simple(product['product_name'], sleep_min, sleep_max)
    
    if not images:
        logger.warning(f"No images found for {product['product_name']}")
        return {
            'product_uid': product['product_uid'],
            'product_name': product['product_name'],
            'images_found': 0,
            'images_downloaded': 0
        }
    
    # Insert images into database
    insert_images_to_db(images, product['product_uid'])
    
    # Update product.json with image metadata
    product_json_path = product['product_dir'] / 'product.json'
    try:
        with open(product_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Add images to the product data
        data['images'] = images
        
        # Write updated data
        with open(product_json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Updated {product_json_path} with {len(images)} images")
    except Exception as e:
        logger.error(f"Error updating {product_json_path}: {e}")
    
    return {
        'product_uid': product['product_uid'],
        'product_name': product['product_name'],
        'images_found': len(images),
        'images_downloaded': 0
    }

def main():
    parser = argparse.ArgumentParser(description='Simple product image enrichment')
    parser.add_argument('--product', type=str, help='Process specific product (brand:slug)')
    parser.add_argument('--all', action='store_true', help='Process all products')
    parser.add_argument('--sleep-min', type=float, default=DEFAULT_SLEEP_MIN)
    parser.add_argument('--sleep-max', type=float, default=DEFAULT_SLEEP_MAX)
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    
    args = parser.parse_args()
    
    logger.info("=== STARTING SIMPLE ENRICHMENT ===")
    
    # Get products with source pages
    products = get_products_with_source_pages()
    
    if not products:
        logger.warning("No products with source pages found!")
        return
    
    logger.info(f"Found {len(products)} products with source pages")
    
    # Filter by specific product if requested
    if args.product:
        products = [p for p in products if p['product_uid'] == args.product]
        if not products:
            logger.error(f"Product {args.product} not found!")
            return
        logger.info(f"Processing specific product: {args.product}")
    
    # Process products
    results = []
    for i, product in enumerate(products, 1):
        logger.info(f"[{i}/{len(products)}] Enriching: {product['product_name']}")
        
        if args.dry_run:
            search_term = PRODUCT_MAPPING.get(product['product_name'].lower(), product['product_name'])
            logger.info(f"  Would search with term: '{search_term}'")
            continue
        
        try:
            result = enrich_product_images_simple(
                product,
                sleep_min=args.sleep_min,
                sleep_max=args.sleep_max
            )
            results.append(result)
            
            if result['images_found'] > 0:
                logger.info(f"  ✅ Found {result['images_found']} images")
            else:
                logger.warning(f"  ❌ No images found")
                
        except Exception as e:
            logger.error(f"Error enriching {product['product_name']}: {e}")
            continue
    
    # Summary
    if results:
        total_images_found = sum(r['images_found'] for r in results)
        
        logger.info(f"\n🎉 Simple enrichment completed!")
        logger.info(f"Products processed: {len(results)}")
        logger.info(f"Total images found: {total_images_found}")
    
    logger.info("Done!")

if __name__ == "__main__":
    main()
