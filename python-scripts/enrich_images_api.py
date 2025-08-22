#!/usr/bin/env python3
"""
Product Image Enrichment Script - API Version
Uses Herman Miller's image search API for high-quality product images.
"""

import json
import pathlib
import requests
import time
import random
import argparse
import logging
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
                    'product_dir': product_dir.parent
                })
        
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Error reading {product_dir}: {e}")
            continue
    
    return products

def search_product_images(product_name: str, sleep_min: float = 1.0, sleep_max: float = 2.0) -> List[Dict]:
    """Search for product images using Herman Miller's API."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'OKII-Image-Enricher/0.1 (contact: you@example.com)',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Referer': 'https://www.hermanmiller.com/',
        'Origin': 'https://www.hermanmiller.com'
    })
    
    # Build API URL
    encoded_product = quote_plus(product_name)
    api_url = f"{API_BASE_URL}?core=europe/en_gb&fp={encoded_product}&c=9"
    
    logger.info(f"Searching API for: {product_name}")
    logger.info(f"API URL: {api_url}")
    
    try:
        # Polite delay
        time.sleep(random.uniform(sleep_min, sleep_max))
        
        response = session.get(api_url, timeout=30)
        if response.status_code != 200:
            logger.warning(f"API request failed: {response.status_code}")
            return []
        
        data = response.json()
        items = data.get('items', [])
        
        logger.info(f"Found {len(items)} images for {product_name}")
        
        # Process images
        processed_images = []
        for item in items:
            image_data = {
                'id': item.get('id'),
                'title': item.get('title'),
                'alt': item.get('imageAlt'),
                'original_url': f"https://www.hermanmiller.com{item.get('imageLink')}",
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

def download_image(image_url: str, save_path: pathlib.Path, sleep_min: float = 1.0, sleep_max: float = 2.0) -> bool:
    """Download an image file."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'OKII-Image-Enricher/0.1 (contact: you@example.com)',
        'Referer': 'https://www.hermanmiller.com/'
    })
    
    # Polite delay
    time.sleep(random.uniform(sleep_min, sleep_max))
    
    try:
        response = session.get(image_url, timeout=30, stream=True)
        if response.status_code == 200:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Downloaded: {save_path}")
            return True
        else:
            logger.warning(f"Failed to download {image_url}: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error downloading {image_url}: {e}")
        return False

def update_product_json_with_images(product_json_path: pathlib.Path, images: List[Dict]) -> None:
    """Update product.json with image information."""
    try:
        with open(product_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        logger.error(f"Could not read {product_json_path}")
        return
    
    # Add images to the product data
    data['images'] = images
    
    # Write updated data
    with open(product_json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Updated {product_json_path} with {len(images)} images")

def enrich_product_images_api(product: Dict, download_images: bool = False, sleep_min: float = 1.0, sleep_max: float = 2.0) -> Dict:
    """Enrich a single product with images from the API."""
    logger.info(f"Enriching images for: {product['product_name']}")
    
    # Search for images using the API
    images = search_product_images(product['product_name'], sleep_min, sleep_max)
    
    if not images:
        logger.warning(f"No images found for {product['product_name']}")
        return {
            'product_uid': product['product_uid'],
            'product_name': product['product_name'],
            'images_found': 0,
            'images_downloaded': 0
        }
    
    # Download images if requested
    if download_images:
        images_dir = product['product_dir'] / 'images'
        downloaded_count = 0
        
        for i, img in enumerate(images[:5]):  # Limit to 5 images per product
            try:
                # Choose the best rendition (prefer Portrait size)
                best_rendition = None
                for rendition in img['renditions']:
                    if rendition['type'] == 'P':  # Portrait
                        best_rendition = rendition
                        break
                
                if not best_rendition:
                    # Fall back to first available rendition
                    best_rendition = img['renditions'][0] if img['renditions'] else None
                
                if best_rendition:
                    # Extract file extension from URL
                    url_parts = best_rendition['url'].split('.')
                    ext = f".{url_parts[-1]}" if len(url_parts) > 1 else '.jpg'
                    
                    # Create filename
                    filename = f"product_image_{i+1}_{img['id']}{ext}"
                    save_path = images_dir / filename
                    
                    if download_image(best_rendition['url'], save_path, sleep_min, sleep_max):
                        # Update image data with local path
                        img['local_path'] = str(save_path.relative_to(LIBRARY_ROOT))
                        downloaded_count += 1
            
            except Exception as e:
                logger.error(f"Error processing image {img.get('id', 'unknown')}: {e}")
    
    # Update product.json
    product_json_path = product['product_dir'] / 'product.json'
    update_product_json_with_images(product_json_path, images)
    
    return {
        'product_uid': product['product_uid'],
        'product_name': product['product_name'],
        'images_found': len(images),
        'images_downloaded': downloaded_count if download_images else 0
    }

def main():
    parser = argparse.ArgumentParser(description='Enrich product data with images using Herman Miller API')
    parser.add_argument('--download', action='store_true',
                       help='Download images to local storage')
    parser.add_argument('--sleep-min', type=float, default=DEFAULT_SLEEP_MIN,
                       help='Minimum sleep between requests')
    parser.add_argument('--sleep-max', type=float, default=DEFAULT_SLEEP_MAX,
                       help='Maximum sleep between requests')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--product', type=str,
                       help='Process only a specific product (brand:slug format)')
    
    args = parser.parse_args()
    
    logger.info("Starting product image enrichment using Herman Miller API...")
    
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
    for product in products:
        if args.dry_run:
            logger.info(f"[DRY RUN] Would enrich: {product['product_name']}")
            continue
        
        try:
            result = enrich_product_images_api(
                product, 
                download_images=args.download,
                sleep_min=args.sleep_min,
                sleep_max=args.sleep_max
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Error enriching {product['product_name']}: {e}")
            continue
    
    # Summary
    if results:
        total_images_found = sum(r['images_found'] for r in results)
        total_images_downloaded = sum(r['images_downloaded'] for r in results)
        
        logger.info(f"\n🎉 Enrichment completed!")
        logger.info(f"Products processed: {len(results)}")
        logger.info(f"Total images found: {total_images_found}")
        if args.download:
            logger.info(f"Total images downloaded: {total_images_downloaded}")
    
    logger.info("Done!")

if __name__ == "__main__":
    main()
