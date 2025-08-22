#!/usr/bin/env python3
"""
Hybrid Product Image Enrichment Script
Combines precise metadata matching with fallback to general terms for API compatibility.
"""

import json
import pathlib
import requests
import time
import random
import argparse
import logging
import re
from urllib.parse import quote_plus, urlparse
from typing import Dict, List, Optional, Set

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
LIBRARY_ROOT = pathlib.Path("library")
API_BASE_URL = "https://www.hermanmiller.com/services/search/images"
DEFAULT_SLEEP_MIN = 1.0
DEFAULT_SLEEP_MAX = 2.0

def extract_search_strategy(product_data: Dict) -> Dict[str, List[str]]:
    """Extract search strategy with precise and fallback terms."""
    strategy = {
        'precise': [],      # Exact product identifiers
        'general': [],      # General product names for API
        'fallback': []      # Brand + product combinations
    }
    
    # Base product info
    brand = product_data.get('brand', '')
    product_name = product_data.get('product', '')
    
    # Extract variants from files
    variants = set()
    for file_info in product_data.get('files', []):
        variant = file_info.get('variant', '')
        if variant:
            variants.add(variant)
    
    # Extract from stored_path patterns
    path_identifiers = set()
    for file_info in product_data.get('files', []):
        stored_path = file_info.get('stored_path', '')
        if stored_path:
            # Extract product identifiers from path
            path_parts = stored_path.split('/')
            for part in path_parts:
                # Look for product-specific identifiers
                if any(keyword in part.lower() for keyword in ['aeron', 'zeph', 'cosm', 'eames', 'caper']):
                    # Clean up the identifier
                    clean_id = re.sub(r'[_-]', ' ', part).strip()
                    if clean_id and len(clean_id) > 2:
                        path_identifiers.add(clean_id)
    
    # Extract from source pages (if available)
    source_identifiers = set()
    for source_page in product_data.get('source_pages', []):
        if source_page:
            # Extract product name from URL
            parsed_url = urlparse(source_page)
            path_parts = parsed_url.path.split('/')
            for part in path_parts:
                if part and part != 'individual' and part != 'product-models':
                    # Clean up the identifier
                    clean_id = re.sub(r'[_-]', ' ', part).strip()
                    if clean_id and len(clean_id) > 2:
                        source_identifiers.add(clean_id)
    
    # Build PRECISE search terms (exact matches)
    if brand and product_name:
        strategy['precise'].append(product_name)
        
        # Try brand + product combinations
        strategy['precise'].append(f"{brand} {product_name}")
        strategy['precise'].append(f"{brand.title()} {product_name.title()}")
    
    # Add variant-specific identifiers
    for variant in variants:
        if variant:
            # Clean up variant name
            clean_variant = re.sub(r'[_-]', ' ', variant).strip()
            if clean_variant:
                strategy['precise'].append(clean_variant)
                # Try with brand
                if brand:
                    strategy['precise'].append(f"{brand} {clean_variant}")
    
    # Add path-based identifiers
    strategy['precise'].extend(path_identifiers)
    
    # Add source-based identifiers
    strategy['precise'].extend(source_identifiers)
    
    # Build GENERAL search terms (API-compatible)
    if product_name:
        # Extract main product name (before "chairs", "stools", etc.)
        main_product = re.sub(r'\s+(chairs?|stools?|tables?|desks?)$', '', product_name, flags=re.IGNORECASE)
        if main_product != product_name:
            strategy['general'].append(main_product)
            strategy['general'].append(f"{main_product} Chair")
            strategy['general'].append(f"{main_product} Stool")
    
    # Common product mappings for API compatibility
    product_mappings = {
        'aeron chairs': 'Aeron Chair',
        'aeron chair': 'Aeron Chair',
        'zeph stool': 'Zeph Chair',
        'zeph chairs': 'Zeph Chair',
        'cosm chairs': 'Cosm Chair',
        'cosm chair': 'Cosm Chair',
        'eames aluminum group chairs': 'Eames Chair',
        'eames chair': 'Eames Chair',
        'caper stacking chair': 'Caper Chair',
        'caper chair': 'Caper Chair'
    }
    
    # Add mapped general terms
    for original, mapped in product_mappings.items():
        if original.lower() in product_name.lower():
            strategy['general'].append(mapped)
    
    # Build FALLBACK terms (brand + general product)
    if brand and product_name:
        # Try brand + main product
        main_product = re.sub(r'\s+(chairs?|stools?|tables?|desks?)$', '', product_name, flags=re.IGNORECASE)
        strategy['fallback'].append(f"{brand.title()} {main_product}")
        strategy['fallback'].append(f"{brand.title()} {main_product} Chair")
        strategy['fallback'].append(f"{brand.title()} {main_product} Stool")
    
    # Remove duplicates while preserving order
    for category in strategy:
        seen = set()
        unique_terms = []
        for term in strategy[category]:
            if term.lower() not in seen:
                seen.add(term.lower())
                unique_terms.append(term)
        strategy[category] = unique_terms
    
    return strategy

def search_product_images_hybrid(search_strategy: Dict[str, List[str]], sleep_min: float = 1.0, sleep_max: float = 2.0) -> List[Dict]:
    """Search for product images using hybrid strategy."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'OKII-Image-Enricher/0.1 (contact: you@example.com)',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Referer': 'https://www.hermanmiller.com/',
        'Origin': 'https://www.hermanmiller.com'
    })
    
    logger.info(f"Searching with hybrid strategy:")
    logger.info(f"  Precise terms: {search_strategy['precise']}")
    logger.info(f"  General terms: {search_strategy['general']}")
    logger.info(f"  Fallback terms: {search_strategy['fallback']}")
    
    best_result = []
    best_term = None
    best_score = 0
    best_category = None
    
    # Search in order: precise -> general -> fallback
    search_order = [('precise', 3), ('general', 2), ('fallback', 1)]
    
    for category, category_weight in search_order:
        terms = search_strategy[category]
        logger.info(f"  Trying {category} terms (weight: {category_weight})...")
        
        for search_term in terms:
            # Build API URL
            encoded_term = quote_plus(search_term)
            api_url = f"{API_BASE_URL}?core=europe/en_gb&fp={encoded_term}&c=9"
            
            logger.info(f"    Trying term: '{search_term}'")
            
            try:
                # Polite delay
                time.sleep(random.uniform(sleep_min, sleep_max))
                
                response = session.get(api_url, timeout=30)
                if response.status_code != 200:
                    logger.warning(f"      API request failed: {response.status_code}")
                    continue
                
                data = response.json()
                items = data.get('items', [])
                
                logger.info(f"      Found {len(items)} images")
                
                if items:
                    # Score the results based on relevance and category
                    score = len(items) * category_weight
                    
                    # Bonus for exact matches in titles
                    for item in items:
                        title = item.get('title', '').lower()
                        alt = item.get('imageAlt', '').lower()
                        search_lower = search_term.lower()
                        
                        # Check for exact matches
                        if search_lower in title or search_lower in alt:
                            score += 2 * category_weight
                        
                        # Check for variant-specific matches
                        if any(variant.lower() in title for variant in search_strategy['precise']):
                            score += 1 * category_weight
                    
                    logger.info(f"      Relevance score: {score}")
                    
                    if score > best_score:
                        best_result = items
                        best_term = search_term
                        best_score = score
                        best_category = category
                        logger.info(f"      ✅ New best result with score {score}!")
                    
                    # If we found a very high score, we can stop
                    if score >= 15:
                        logger.info(f"      🎯 Found excellent match, stopping search")
                        break
                        
            except Exception as e:
                logger.error(f"      Error searching for '{search_term}': {e}")
                continue
        
        # If we found a good result in this category, we can stop
        if best_result and best_score >= 10:
            break
    
    if best_result:
        logger.info(f"🎉 Best match: '{best_term}' ({best_category}) with score {best_score} and {len(best_result)} images")
        
        # Process images
        processed_images = []
        for item in best_result:
            image_data = {
                'id': item.get('id'),
                'title': item.get('title'),
                'alt': item.get('imageAlt'),
                'original_url': f"https://www.hermanmiller.com{item.get('imageLink')}",
                'search_term': best_term,
                'search_category': best_category,
                'relevance_score': best_score,
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
        logger.warning(f"❌ No images found for any search term")
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
                    'product_dir': product_dir.parent,
                    'product_data': data  # Include full data for precise matching
                })
        
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Error reading {product_dir}: {e}")
            continue
    
    return products

def enrich_product_images_hybrid(product: Dict, download_images: bool = False, sleep_min: float = 1.0, sleep_max: float = 2.0) -> Dict:
    """Enrich a single product with images using hybrid strategy."""
    logger.info(f"Enriching images for: {product['product_name']}")
    
    # Extract search strategy
    search_strategy = extract_search_strategy(product['product_data'])
    
    if not any(search_strategy.values()):
        logger.warning(f"No search terms extracted for {product['product_name']}")
        return {
            'product_uid': product['product_uid'],
            'product_name': product['product_name'],
            'images_found': 0,
            'images_downloaded': 0
        }
    
    # Search for images using hybrid strategy
    images = search_product_images_hybrid(search_strategy, sleep_min, sleep_max)
    
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
    parser = argparse.ArgumentParser(description='Hybrid product image enrichment using rich metadata')
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
    
    logger.info("Starting hybrid product image enrichment using rich metadata...")
    
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
            search_strategy = extract_search_strategy(product['product_data'])
            logger.info(f"[DRY RUN] Would enrich: {product['product_name']}")
            logger.info(f"  Precise terms: {search_strategy['precise']}")
            logger.info(f"  General terms: {search_strategy['general']}")
            logger.info(f"  Fallback terms: {search_strategy['fallback']}")
            continue
        
        try:
            result = enrich_product_images_hybrid(
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
        
        logger.info(f"\n🎉 Hybrid enrichment completed!")
        logger.info(f"Products processed: {len(results)}")
        logger.info(f"Total images found: {total_images_found}")
        if args.download:
            logger.info(f"Total images downloaded: {total_images_downloaded}")
    
    logger.info("Done!")

if __name__ == "__main__":
    main()
