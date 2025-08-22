#!/usr/bin/env python3
import sqlite3
import os
import re
from pathlib import Path

def analyze_image_filename_matching():
    """Analyze image filenames and match them to 3D files."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== IMAGE FILENAME ANALYSIS ===")
    
    # Get all images with local paths
    cursor.execute("""
        SELECT product_uid, local_path, image_url, provider, rationale
        FROM images 
        WHERE local_path IS NOT NULL
        ORDER BY product_uid, local_path
    """)
    
    images = cursor.fetchall()
    print(f"Found {len(images)} images with local paths")
    
    # Get all 3D files
    cursor.execute("""
        SELECT product_uid, stored_path, file_type, ext
        FROM files 
        WHERE file_type IN ('revit', 'sketchup', 'autocad_3d', 'autocad_2d', 'autocad')
        ORDER BY product_uid, stored_path
    """)
    
    files = cursor.fetchall()
    print(f"Found {len(files)} 3D files")
    
    # Analyze matching patterns
    matches = []
    potential_matches = []
    
    for img_product_uid, img_path, img_url, provider, rationale in images:
        if not img_path:
            continue
            
        # Extract filename from image path
        img_filename = os.path.basename(img_path)
        img_name_without_ext = os.path.splitext(img_filename)[0]
        
        # Look for matching 3D files
        for file_product_uid, file_path, file_type, file_ext in files:
            if img_product_uid != file_product_uid:
                continue
                
            # Extract filename from file path
            file_filename = os.path.basename(file_path)
            file_name_without_ext = os.path.splitext(file_filename)[0]
            
            # Check for exact matches
            if img_name_without_ext.lower() == file_name_without_ext.lower():
                matches.append({
                    'product_uid': img_product_uid,
                    'image_path': img_path,
                    'image_filename': img_filename,
                    'file_path': file_path,
                    'file_filename': file_filename,
                    'file_type': file_type,
                    'match_type': 'exact'
                })
            
            # Check for partial matches
            elif (img_name_without_ext.lower() in file_name_without_ext.lower() or 
                  file_name_without_ext.lower() in img_name_without_ext.lower()):
                potential_matches.append({
                    'product_uid': img_product_uid,
                    'image_path': img_path,
                    'image_filename': img_filename,
                    'file_path': file_path,
                    'file_filename': file_filename,
                    'file_type': file_type,
                    'match_type': 'partial'
                })
    
    # Report results
    print(f"\n=== MATCHING RESULTS ===")
    print(f"Exact matches: {len(matches)}")
    print(f"Potential matches: {len(potential_matches)}")
    
    if matches:
        print(f"\n=== EXACT MATCHES ===")
        for match in matches[:10]:  # Show first 10
            print(f"Product: {match['product_uid']}")
            print(f"  Image: {match['image_filename']}")
            print(f"  File:  {match['file_filename']} ({match['file_type']})")
            print()
    
    if potential_matches:
        print(f"\n=== POTENTIAL MATCHES (first 10) ===")
        for match in potential_matches[:10]:
            print(f"Product: {match['product_uid']}")
            print(f"  Image: {match['image_filename']}")
            print(f"  File:  {match['file_filename']} ({match['file_type']})")
            print()
    
    # Analyze filename patterns
    print(f"\n=== FILENAME PATTERN ANALYSIS ===")
    
    # Get unique image filenames
    image_filenames = set()
    for _, img_path, _, _, _ in images:
        if img_path:
            filename = os.path.basename(img_path)
            image_filenames.add(filename)
    
    # Common patterns in image filenames
    patterns = {
        'mdl_': 'model',
        'prd_': 'product', 
        'th_': 'thumbnail',
        'hm_': 'herman miller',
        'hmi_': 'herman miller international',
        'rendition': 'rendition',
        'chair': 'chair',
        'stool': 'stool',
        'table': 'table'
    }
    
    for pattern, description in patterns.items():
        count = sum(1 for filename in image_filenames if pattern.lower() in filename.lower())
        if count > 0:
            print(f"  {pattern}: {count} files ({description})")
    
    # Check for specific product patterns
    print(f"\n=== PRODUCT-SPECIFIC PATTERNS ===")
    
    # Group by product
    product_images = {}
    for img_product_uid, img_path, _, _, _ in images:
        if img_path:
            if img_product_uid not in product_images:
                product_images[img_product_uid] = []
            product_images[img_product_uid].append(os.path.basename(img_path))
    
    # Show patterns for products with multiple images
    for product_uid, filenames in list(product_images.items())[:5]:
        if len(filenames) > 1:
            print(f"\n{product_uid}:")
            for filename in filenames:
                print(f"  {filename}")
    
    conn.close()

if __name__ == "__main__":
    analyze_image_filename_matching()
