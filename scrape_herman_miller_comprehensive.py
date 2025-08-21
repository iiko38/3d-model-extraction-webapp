#!/usr/bin/env python3
import os
import requests
import sqlite3
from pathlib import Path
from urllib.parse import urljoin, urlparse
import time
import hashlib
from bs4 import BeautifulSoup
import re

def get_product_search_urls(product_uid):
    """Get multiple search URLs for a product to find images."""
    if ':' in product_uid:
        brand, product_name = product_uid.split(':', 1)
    else:
        brand = 'herman_miller'
        product_name = product_uid
    
    # Convert product name to search terms
    search_terms = []
    
    # Extract key product words
    words = product_name.replace('_', ' ').split()
    
    # Add original product name
    search_terms.append(product_name.replace('_', ' '))
    
    # Add key product words
    for word in words:
        if len(word) > 2:  # Skip short words
            search_terms.append(word)
    
    # Add specific product variations
    if 'aeron' in product_name:
        search_terms.extend(['aeron chair', 'aeron'])
    elif 'zeph' in product_name:
        search_terms.extend(['zeph chair', 'zeph stool', 'zeph'])
    elif 'cosm' in product_name:
        search_terms.extend(['cosm chair', 'cosm'])
    elif 'sayl' in product_name:
        search_terms.extend(['sayl chair', 'sayl'])
    elif 'caper' in product_name:
        search_terms.extend(['caper chair', 'caper stacking chair', 'caper'])
    elif 'mirra' in product_name:
        search_terms.extend(['mirra chair', 'mirra'])
    elif 'verus' in product_name:
        search_terms.extend(['verus chair', 'verus'])
    
    # Remove duplicates and empty strings
    search_terms = list(set([term.strip() for term in search_terms if term.strip()]))
    
    # Build search URLs
    urls = []
    
    # 1. Direct product page URLs (if they exist)
    if 'zeph' in product_name:
        if 'stool' in product_name:
            urls.append("https://www.hermanmiller.com/en_gb/resources/3d-models-and-planning-tools/product-models/individual/zeph-stool/")
        else:
            urls.append("https://www.hermanmiller.com/en_gb/resources/3d-models-and-planning-tools/product-models/individual/zeph-chair-with-arms/")
    elif 'aeron' in product_name:
        urls.append("https://www.hermanmiller.com/en_gb/resources/3d-models-and-planning-tools/product-models/individual/aeron-chair/")
    elif 'cosm' in product_name:
        urls.append("https://www.hermanmiller.com/en_gb/resources/3d-models-and-planning-tools/product-models/individual/cosm-chair/")
    elif 'sayl' in product_name:
        urls.append("https://www.hermanmiller.com/en_gb/resources/3d-models-and-planning-tools/product-models/individual/sayl-chair/")
    elif 'caper' in product_name:
        urls.append("https://www.hermanmiller.com/en_gb/resources/3d-models-and-planning-tools/product-models/individual/caper-stacking-chair/")
    
    # 2. Main product category pages
    urls.extend([
        "https://www.hermanmiller.com/en_gb/products/seating/office-chairs/",
        "https://www.hermanmiller.com/en_gb/products/seating/side-chairs/",
        "https://www.hermanmiller.com/en_gb/products/seating/stools/",
        "https://www.hermanmiller.com/en_gb/products/tables/",
        "https://www.hermanmiller.com/en_gb/products/desks-and-workspaces/",
        "https://www.hermanmiller.com/en_gb/resources/3d-models-and-planning-tools/product-models/"
    ])
    
    # 3. Search results pages for each term
    for term in search_terms[:3]:  # Limit to first 3 terms
        encoded_term = requests.utils.quote(term)
        urls.append(f"https://www.hermanmiller.com/en_gb/search/?q={encoded_term}")
    
    return urls, search_terms

def extract_images_from_page(url, product_uid, search_terms):
    """Extract product images from a Herman Miller page."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"  Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        images = []
        
        # Method 1: Product page specific selectors (highest priority)
        main_image = soup.select_one("#content > div > div > div > div > div > div.modelDetails.section.col-xs-12.first.odd.default-style > div > div > div > div > div.itemDetails-description-container.col-sm-6.col-lg-7 > div.itemDetails-images-container > div.itemDetails-images-selected-container > picture.itemDetails-image-selected.active > img")
        
        if main_image and main_image.get('src'):
            src = main_image.get('src')
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = urljoin(url, src)
            
            images.append({
                'url': src,
                'alt': main_image.get('alt', ''),
                'type': 'main_product_image'
            })
        
        # Method 2: Product images container (high priority)
        image_containers = soup.select(".itemDetails-images-container img, .product-images img, .model-images img, .product-image img")
        
        for img in image_containers:
            src = img.get('src')
            if src:
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(url, src)
                
                # Skip if already added
                if not any(img['url'] == src for img in images):
                    images.append({
                        'url': src,
                        'alt': img.get('alt', ''),
                        'type': 'product_image'
                    })
        
        # Method 3: Search for images that match product terms (medium priority)
        all_images = soup.find_all('img')
        for img in all_images:
            src = img.get('src', '')
            alt = img.get('alt', '').lower()
            
            # Check if image matches any search terms
            matches_product = False
            for term in search_terms:
                if term.lower() in alt or term.lower() in src.lower():
                    matches_product = True
                    break
            
            if matches_product and src:
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(url, src)
                
                # Skip if already added
                if not any(img['url'] == src for img in images):
                    images.append({
                        'url': src,
                        'alt': img.get('alt', ''),
                        'type': 'search_match'
                    })
        
        # Method 4: Look for product model images (lower priority)
        for img in all_images:
            src = img.get('src', '')
            if src and any(keyword in src.lower() for keyword in ['product_models', 'mdl_', 'chair', 'stool', 'table']):
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(url, src)
                
                # Skip if already added
                if not any(img['url'] == src for img in images):
                    images.append({
                        'url': src,
                        'alt': img.get('alt', ''),
                        'type': 'model_image'
                    })
        
        # Limit to 15 images per page to avoid overwhelming
        if len(images) > 15:
            print(f"  Limiting page results from {len(images)} to 15 images")
            images = images[:15]
        
        print(f"  Found {len(images)} images")
        return images
        
    except Exception as e:
        print(f"  ✗ Error fetching {url}: {e}")
        return []

def download_and_store_images(images, product_uid):
    """Download images and store them locally."""
    if not images:
        return []
    
    # Limit to maximum 10 images per product
    if len(images) > 10:
        print(f"    Limiting from {len(images)} to 10 images")
        images = images[:10]
    
    # Create images directory
    images_dir = Path("library/images")
    images_dir.mkdir(exist_ok=True)
    
    # Create product directory
    product_dir = images_dir / product_uid.replace(':', '/')
    product_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded_images = []
    
    for i, img_info in enumerate(images):
        try:
            img_url = img_info['url']
            
            # Generate filename
            parsed_url = urlparse(img_url)
            filename = os.path.basename(parsed_url.path)
            if not filename or '.' not in filename:
                # Generate filename from URL hash
                url_hash = hashlib.md5(img_url.encode()).hexdigest()[:8]
                filename = f"product_image_{url_hash}.jpg"
            
            local_path = product_dir / filename
            
            # Skip if already downloaded
            if local_path.exists():
                print(f"    ✓ Already exists: {local_path}")
                downloaded_images.append({
                    'url': img_url,
                    'local_path': str(local_path.relative_to(Path("library"))).replace('\\', '/'),
                    'alt': img_info.get('alt', ''),
                    'type': img_info.get('type', 'product_image')
                })
                continue
            
            # Download image
            print(f"    Downloading: {img_url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(img_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Save image
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            print(f"    ✓ Downloaded: {local_path} ({len(response.content)} bytes)")
            
            downloaded_images.append({
                'url': img_url,
                'local_path': str(local_path.relative_to(Path("library"))).replace('\\', '/'),
                'alt': img_info.get('alt', ''),
                'type': img_info.get('type', 'product_image')
            })
            
            # Small delay
            time.sleep(0.5)
            
        except Exception as e:
            print(f"    ✗ Failed to download {img_url}: {e}")
    
    return downloaded_images

def update_database_with_images(product_uid, downloaded_images):
    """Update the database with the new images."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    for img in downloaded_images:
        try:
            cursor.execute("""
                INSERT INTO images(product_uid, variant, image_url, provider, score, rationale, status, local_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, strftime('%s','now'), strftime('%s','now'))
                ON CONFLICT(product_uid, variant, image_url) DO UPDATE SET
                    local_path=excluded.local_path,
                    updated_at=excluded.updated_at
            """, (
                product_uid,
                '',  # variant
                img['url'],
                'herman_miller_comprehensive',
                8.0,  # Good score for comprehensive search
                f"Found via comprehensive search: {img['type']}",
                'pending',
                img['local_path']
            ))
        except Exception as e:
            print(f"    ✗ Error updating database: {e}")
    
    conn.commit()
    conn.close()

def scrape_comprehensive_product_images():
    """Scrape product images using comprehensive search across multiple pages."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    # Get all products
    cursor.execute("SELECT product_uid, name FROM products WHERE brand = 'herman_miller' ORDER BY name")
    products = cursor.fetchall()
    conn.close()
    
    print("=== COMPREHENSIVE PRODUCT IMAGE SCRAPING ===")
    print(f"Found {len(products)} Herman Miller products to process")
    
    total_downloaded = 0
    
    for i, (product_uid, name) in enumerate(products, 1):
        print(f"\n[{i}/{len(products)}] Processing: {product_uid} ({name})")
        
        # Get search URLs and terms
        urls, search_terms = get_product_search_urls(product_uid)
        print(f"  Search terms: {search_terms}")
        print(f"  URLs to search: {len(urls)}")
        
        all_images = []
        
        # Search each URL
        for j, url in enumerate(urls):
            print(f"  [{j+1}/{len(urls)}] Searching: {url}")
            images = extract_images_from_page(url, product_uid, search_terms)
            
            # Add unique images
            for img in images:
                if not any(existing['url'] == img['url'] for existing in all_images):
                    all_images.append(img)
        
        if all_images:
            # Limit total unique images to 15 before downloading
            if len(all_images) > 15:
                print(f"  Limiting total unique images from {len(all_images)} to 15")
                all_images = all_images[:15]
            
            print(f"  Total unique images found: {len(all_images)}")
            
            # Download and store images
            downloaded = download_and_store_images(all_images, product_uid)
            
            if downloaded:
                # Update database
                update_database_with_images(product_uid, downloaded)
                total_downloaded += len(downloaded)
                print(f"  ✓ Added {len(downloaded)} images to database")
            else:
                print(f"  ✗ No images downloaded")
        else:
            print(f"  ✗ No images found")
        
        # Delay between products
        time.sleep(3)
    
    print(f"\n=== COMPREHENSIVE SCRAPING COMPLETE ===")
    print(f"Total images downloaded: {total_downloaded}")

if __name__ == "__main__":
    scrape_comprehensive_product_images()
