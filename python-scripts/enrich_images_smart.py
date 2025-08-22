#!/usr/bin/env python3
"""
Smart Product Image Enrichment Script
Uses intelligent product name matching to find images via Herman Miller's API.
"""

import json
import pathlib
import requests
import time
import random
import argparse
import logging
import re
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

def generate_search_variations(product_name: str) -> List[str]:
    """Generate different search variations for a product name."""
    variations = []
    
    # Original name
    variations.append(product_name)
    
    # Common transformations
    name_lower = product_name.lower()
    name_upper = product_name.upper()
    name_title = product_name.title()
    
    # Add variations
    variations.extend([name_lower, name_upper, name_title])
    
    # Split and try different combinations
    words = product_name.split()
    if len(words) > 1:
        # Try first word only
        variations.append(words[0])
        variations.append(words[0].title())
        
        # Try last word only
        variations.append(words[-1])
        variations.append(words[-1].title())
        
        # Try combinations
        if len(words) >= 2:
            variations.append(f"{words[0]} {words[1]}")
            variations.append(f"{words[0].title()} {words[1].title()}")
    
    # Common product name mappings
    name_mappings = {
        'aeron chairs': 'Aeron Chair',
        'aeron chair': 'Aeron Chair',
        'zeph stool': 'Zeph Chair',
        'zeph chair': 'Zeph Chair',
        'cosm chairs': 'Cosm Chair',
        'cosm chair': 'Cosm Chair',
        'eames aluminum group chairs': 'Eames Chair',
        'eames chair': 'Eames Chair',
        'caper stacking chair': 'Caper Chair',
        'caper chair': 'Caper Chair'
    }
    
    # Add mapped variations
    for original, mapped in name_mappings.items():
        if original.lower() in product_name.lower():
            variations.append(mapped)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_variations = []
    for var in variations:
        if var.lower() not in seen:
            seen.add(var.lower())
            unique_variations.append(var)
    
    return unique_variations

def search_product_images_smart(product_name: str, sleep_min: float = 1.0, sleep_max: float = 2.0) -> List[Dict]:
    """Search for product images using multiple name variations."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'OKII-Image-Enricher/0.1 (contact: you@example.com)',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Referer': 'https://www.hermanmiller.com/',
        'Origin': 'https://www.hermanmiller.com'
    })
    
    # Generate search variations
    variations = generate_search_variations(product_name)
    logger.info(f"Generated {len(variations)} search variations for '{product_name}': {variations}")
    
    best_result = []
    best_variation = None
    
    for variation in variations:
        # Build API URL
        encoded_variation = quote_plus(variation)
        api_url = f"{API_BASE_URL}?core=europe/en_gb&fp={encoded_variation}&c=9"
        
        logger.info(f"  Trying variation: '{variation}'")
        
        try:
            # Polite delay
            time.sleep(random.uniform(sleep_min, sleep_max))
            
            response = session.get(api_url, timeout=30)
            if response.status_code != 200:
                logger.warning(f"    API request failed: {response.status_code}")
                continue
            
            data = response.json()
            items = data.get('items', [])
            
            logger.info(f"    Found {len(items)} images")
            
            if len(items) > len(best_result):
                best_result = items
                best_variation = variation
                logger.info(f"    ✅ New best result with {len(items)} images!")
            
            # If we found a good number of images, we can stop
            if len(items) >= 5:
                logger.info(f"    🎯 Found excellent result, stopping search")
                break
                
        except Exception as e:
            logger.error(f"    Error searching for '{variation}': {e}")
            continue
    
    if best_result:
        logger.info(f"🎉 Best result: '{best_variation}' with {len(best_result)} images")
        
        # Process images
        processed_images = []
        for item in best_result:
            image_data = {
                'id': item.get('id'),
                'title': item.get('title'),
                'alt': item.get('imageAlt'),
                'original_url': f"https://www.hermanmiller.com{item.get('imageLink')}",
                'search_variation': best_variation,
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
    else:
        logger.warning(f"❌ No images found for any variation of '{product_name}'")
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

def enrich_product_images_smart(product: Dict, download_images: bool = False, sleep_min: float = 1.0, sleep_max: float = 2.0) -> Dict:
    """Enrich a single product with images using smart search."""
    logger.info(f"Enriching images for: {product['product_name']}")
    
    # Search for images using smart variations
    images = search_product_images_smart(product['product_name'], sleep_min, sleep_max)
    
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
    parser = argparse.ArgumentParser(description='Smart product image enrichment using Herman Miller API')
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
    
    logger.info("Starting smart product image enrichment using Herman Miller API...")
    
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
            result = enrich_product_images_smart(
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
        
        logger.info(f"\n🎉 Smart enrichment completed!")
        logger.info(f"Products processed: {len(results)}")
        logger.info(f"Total images found: {total_images_found}")
        if args.download:
            logger.info(f"Total images downloaded: {total_images_downloaded}")
    
    logger.info("Done!")

if __name__ == "__main__":
    main()
