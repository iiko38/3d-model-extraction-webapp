#!/usr/bin/env python3
"""
Product Image Enrichment Script
Scrapes product images using existing product data from the database.
"""

import sqlite3
import requests
import bs4
import pathlib
import time
import random
import json
import argparse
import logging
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DB_PATH = "library/index.sqlite"
LIBRARY_ROOT = pathlib.Path("library")
SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
DEFAULT_SLEEP_MIN = 0.5
DEFAULT_SLEEP_MAX = 0.8

def get_db_connection():
    """Get database connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
                logger.info(f"Found product: {data['product']} with {len(source_pages)} source pages")
        
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Error reading {product_dir}: {e}")
            continue
    
    return products

def fetch_html(url: str, sleep_min: float = 0.5, sleep_max: float = 0.8) -> Tuple[int, str]:
    """Fetch HTML content with polite delays."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'OKII-Image-Enricher/0.1 (contact: you@example.com)'
    })
    
    # Polite delay
    time.sleep(random.uniform(sleep_min, sleep_max))
    
    try:
        response = session.get(url, timeout=30)
        return response.status_code, response.text
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return 0, ""

def extract_product_images(soup: bs4.BeautifulSoup, base_url: str) -> List[Dict]:
    """Extract product images from a product page."""
    images = []
    
    # Common image selectors for product pages
    image_selectors = [
        '.product-image img',
        '.product-gallery img',
        '.product-photo img',
        '.product-thumbnail img',
        '.hero-image img',
        '.main-image img',
        '.product-main-image img',
        '[class*="product"][class*="image"] img',
        '[class*="hero"] img',
        '[class*="main"] img',
        'img[src*="product"]',
        'img[alt*="product"]'
    ]
    
    for selector in image_selectors:
        for img in soup.select(selector):
            src = img.get('src')
            if not src:
                continue
            
            # Make URL absolute
            absolute_url = urljoin(base_url, src)
            
            # Check if it's a supported image format
            parsed_url = urlparse(absolute_url)
            if pathlib.Path(parsed_url.path).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                images.append({
                    'url': absolute_url,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', ''),
                    'width': img.get('width'),
                    'height': img.get('height'),
                    'class': img.get('class', [])
                })
    
    # Also look for images in structured data (JSON-LD)
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                # Look for image URLs in structured data
                if 'image' in data:
                    if isinstance(data['image'], list):
                        for img_url in data['image']:
                            if isinstance(img_url, str) and any(ext in img_url.lower() for ext in SUPPORTED_IMAGE_EXTENSIONS):
                                images.append({
                                    'url': urljoin(base_url, img_url),
                                    'alt': 'Product image from structured data',
                                    'title': '',
                                    'width': None,
                                    'height': None,
                                    'class': ['structured-data']
                                })
                    elif isinstance(data['image'], str):
                        if any(ext in data['image'].lower() for ext in SUPPORTED_IMAGE_EXTENSIONS):
                            images.append({
                                'url': urljoin(base_url, data['image']),
                                'alt': 'Product image from structured data',
                                'title': '',
                                'width': None,
                                'height': None,
                                'class': ['structured-data']
                            })
        except (json.JSONDecodeError, TypeError):
            continue
    
    return images

def download_image(image_url: str, save_path: pathlib.Path, sleep_min: float = 0.5, sleep_max: float = 0.8) -> bool:
    """Download an image file."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'OKII-Image-Enricher/0.1 (contact: you@example.com)'
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

def enrich_product_images(product: Dict, download_images: bool = False, sleep_min: float = 0.5, sleep_max: float = 0.8) -> Dict:
    """Enrich a single product with images from its source pages."""
    logger.info(f"Enriching images for: {product['product_name']}")
    
    all_images = []
    
    for source_page in product['source_pages']:
        logger.info(f"  Checking source page: {source_page}")
        
        status_code, html = fetch_html(source_page, sleep_min, sleep_max)
        if status_code != 200:
            logger.warning(f"  Failed to fetch {source_page}: {status_code}")
            continue
        
        soup = bs4.BeautifulSoup(html, 'html.parser')
        images = extract_product_images(soup, source_page)
        
        logger.info(f"  Found {len(images)} images on {source_page}")
        all_images.extend(images)
    
    # Remove duplicates based on URL
    unique_images = []
    seen_urls = set()
    for img in all_images:
        if img['url'] not in seen_urls:
            unique_images.append(img)
            seen_urls.add(img['url'])
    
    logger.info(f"Total unique images found: {len(unique_images)}")
    
    # Download images if requested
    if download_images and unique_images:
        images_dir = product['product_dir'] / 'images'
        for i, img in enumerate(unique_images[:5]):  # Limit to 5 images per product
            try:
                # Extract file extension from URL
                parsed_url = urlparse(img['url'])
                ext = pathlib.Path(parsed_url.path).suffix.lower()
                if not ext or ext not in SUPPORTED_IMAGE_EXTENSIONS:
                    ext = '.jpg'  # Default extension
                
                # Create filename
                filename = f"product_image_{i+1}{ext}"
                save_path = images_dir / filename
                
                if download_image(img['url'], save_path, sleep_min, sleep_max):
                    # Update image data with local path
                    img['local_path'] = str(save_path.relative_to(LIBRARY_ROOT))
            
            except Exception as e:
                logger.error(f"Error processing image {img['url']}: {e}")
    
    # Update product.json
    product_json_path = product['product_dir'] / 'product.json'
    update_product_json_with_images(product_json_path, unique_images)
    
    return {
        'product_uid': product['product_uid'],
        'product_name': product['product_name'],
        'images_found': len(unique_images),
        'images_downloaded': len([img for img in unique_images if 'local_path' in img])
    }

def main():
    parser = argparse.ArgumentParser(description='Enrich product data with images')
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
    
    logger.info("Starting product image enrichment...")
    
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
            result = enrich_product_images(
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
        
        logger.info(f"\nEnrichment completed!")
        logger.info(f"Products processed: {len(results)}")
        logger.info(f"Total images found: {total_images_found}")
        if args.download:
            logger.info(f"Total images downloaded: {total_images_downloaded}")
    
    logger.info("Done!")

if __name__ == "__main__":
    main()


