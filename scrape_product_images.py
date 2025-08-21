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

def get_product_page_url(product_uid):
    """Convert product UID to Herman Miller product page URL."""
    # Extract brand and product name
    if ':' in product_uid:
        brand, product_name = product_uid.split(':', 1)
    else:
        brand = 'herman_miller'
        product_name = product_uid
    
    # Convert product name to URL format
    # e.g., "zeph_stool" -> "zeph-stool"
    url_name = product_name.replace('_', '-')
    
    # Build the URL based on the product type
    if 'zeph' in url_name:
        if 'stool' in url_name:
            return f"https://www.hermanmiller.com/en_gb/resources/3d-models-and-planning-tools/product-models/individual/zeph-stool/"
        else:
            return f"https://www.hermanmiller.com/en_gb/resources/3d-models-and-planning-tools/product-models/individual/zeph-chair-with-arms/"
    elif 'aeron' in url_name:
        return f"https://www.hermanmiller.com/en_gb/resources/3d-models-and-planning-tools/product-models/individual/aeron-chair/"
    elif 'cosm' in url_name:
        return f"https://www.hermanmiller.com/en_gb/resources/3d-models-and-planning-tools/product-models/individual/cosm-chair/"
    elif 'sayl' in url_name:
        return f"https://www.hermanmiller.com/en_gb/resources/3d-models-and-planning-tools/product-models/individual/sayl-chair/"
    elif 'caper' in url_name:
        return f"https://www.hermanmiller.com/en_gb/resources/3d-models-and-planning-tools/product-models/individual/caper-stacking-chair/"
    else:
        # Generic fallback
        return f"https://www.hermanmiller.com/en_gb/resources/3d-models-and-planning-tools/product-models/individual/{url_name}/"

def extract_images_from_page(url, product_uid):
    """Extract product images from a Herman Miller product page."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"  Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        images = []
        
        # Method 1: Try the specific selector you provided
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
        
        # Method 2: Look for all product images in the images container
        image_containers = soup.select(".itemDetails-images-container img, .product-images img, .model-images img")
        
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
        
        # Method 3: Look for any images that might be product-related
        all_images = soup.find_all('img')
        for img in all_images:
            src = img.get('src')
            if src and any(keyword in src.lower() for keyword in ['product', 'model', 'chair', 'stool', 'furniture']):
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(url, src)
                
                # Skip if already added
                if not any(img['url'] == src for img in images):
                    images.append({
                        'url': src,
                        'alt': img.get('alt', ''),
                        'type': 'related_image'
                    })
        
        print(f"  Found {len(images)} images")
        return images
        
    except Exception as e:
        print(f"  ✗ Error fetching {url}: {e}")
        return []

def download_and_store_images(images, product_uid):
    """Download images and store them locally."""
    if not images:
        return []
    
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
                'herman_miller_product_page',
                10.0,  # High score for direct product page images
                f"Scraped from product page: {img['type']}",
                'pending',
                img['local_path']
            ))
        except Exception as e:
            print(f"    ✗ Error updating database: {e}")
    
    conn.commit()
    conn.close()

def scrape_all_product_images():
    """Scrape product images for all products in the database."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    # Get all products
    cursor.execute("SELECT product_uid, name FROM products WHERE brand = 'herman_miller' ORDER BY name")
    products = cursor.fetchall()
    conn.close()
    
    print("=== SCRAPING PRODUCT IMAGES ===")
    print(f"Found {len(products)} Herman Miller products to process")
    
    total_downloaded = 0
    
    for i, (product_uid, name) in enumerate(products, 1):
        print(f"\n[{i}/{len(products)}] Processing: {product_uid} ({name})")
        
        # Get product page URL
        page_url = get_product_page_url(product_uid)
        print(f"  Page URL: {page_url}")
        
        # Extract images from page
        images = extract_images_from_page(page_url, product_uid)
        
        if images:
            # Download and store images
            downloaded = download_and_store_images(images, product_uid)
            
            if downloaded:
                # Update database
                update_database_with_images(product_uid, downloaded)
                total_downloaded += len(downloaded)
                print(f"  ✓ Added {len(downloaded)} images to database")
            else:
                print(f"  ✗ No images downloaded")
        else:
            print(f"  ✗ No images found on page")
        
        # Delay between products
        time.sleep(2)
    
    print(f"\n=== SCRAPING COMPLETE ===")
    print(f"Total images downloaded: {total_downloaded}")

if __name__ == "__main__":
    scrape_all_product_images()
