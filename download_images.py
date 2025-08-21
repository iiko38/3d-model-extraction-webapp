#!/usr/bin/env python3
import os
import requests
import sqlite3
from pathlib import Path
from urllib.parse import urlparse
import time
import hashlib

def download_images():
    """Download all images from the database and store them locally."""
    
    # Create images directory
    images_dir = Path("library/images")
    images_dir.mkdir(exist_ok=True)
    
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== DOWNLOADING IMAGES ===")
    
    # Get all images
    cursor.execute("SELECT product_uid, image_url, score FROM images WHERE status = 'pending'")
    images = cursor.fetchall()
    
    print(f"Found {len(images)} images to download")
    
    downloaded = 0
    failed = 0
    
    for i, (product_uid, image_url, score) in enumerate(images, 1):
        print(f"\n[{i}/{len(images)}] Processing {product_uid}")
        
        try:
            # Create product directory
            product_dir = images_dir / product_uid.replace(':', '/')
            product_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename from URL
            parsed_url = urlparse(image_url)
            filename = os.path.basename(parsed_url.path)
            if not filename or '.' not in filename:
                # Generate filename from URL hash
                url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
                filename = f"image_{url_hash}.jpg"
            
            local_path = product_dir / filename
            
            # Skip if already downloaded
            if local_path.exists():
                print(f"  ✓ Already exists: {local_path}")
                # Update database anyway
                cursor.execute(
                    "UPDATE images SET local_path = ? WHERE product_uid = ? AND image_url = ?",
                    (str(local_path), product_uid, image_url)
                )
                downloaded += 1
                continue
            
            # Download image
            print(f"  Downloading: {image_url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Save image
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            # Update database with local path
            cursor.execute(
                "UPDATE images SET local_path = ? WHERE product_uid = ? AND image_url = ?",
                (str(local_path), product_uid, image_url)
            )
            
            print(f"  ✓ Downloaded: {local_path} ({len(response.content)} bytes)")
            downloaded += 1
            
            # Commit after each successful download
            conn.commit()
            
            # Small delay to be polite
            time.sleep(0.2)
            
        except Exception as e:
            print(f"  ✗ Failed to download {image_url}: {e}")
            failed += 1
    
    conn.close()
    
    print(f"\n=== DOWNLOAD COMPLETE ===")
    print(f"Downloaded: {downloaded}")
    print(f"Failed: {failed}")
    print(f"Images stored in: {images_dir}")

if __name__ == "__main__":
    download_images()
