#!/usr/bin/env python3
import sqlite3
import os
import re

def match_images_to_3d_files():
    """Match images to 3D files based on filename patterns and update database."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== MATCHING IMAGES TO 3D FILES ===")
    
    # Get all 3D files
    cursor.execute("""
        SELECT product_uid, stored_path, file_type, ext
        FROM files 
        WHERE file_type IN ('revit', 'sketchup', 'autocad_3d', 'autocad_2d', 'autocad')
        ORDER BY product_uid, stored_path
    """)
    
    files = cursor.fetchall()
    print(f"Found {len(files)} 3D files to match")
    
    # Get all images with local paths
    cursor.execute("""
        SELECT product_uid, local_path, image_url, provider, rationale
        FROM images 
        WHERE local_path IS NOT NULL
        ORDER BY product_uid, local_path
    """)
    
    images = cursor.fetchall()
    print(f"Found {len(images)} images to match")
    
    matches = []
    
    for file_product_uid, file_path, file_type, file_ext in files:
        # Extract filename from file path
        file_filename = os.path.basename(file_path)
        file_name_without_ext = os.path.splitext(file_filename)[0]
        
        # Look for matching images
        for img_product_uid, img_path, img_url, provider, rationale in images:
            if file_product_uid != img_product_uid:
                continue
                
            if not img_path:
                continue
                
            # Extract filename from image path
            img_filename = os.path.basename(img_path)
            img_name_without_ext = os.path.splitext(img_filename)[0]
            
            # Remove rendition suffixes
            img_name_clean = re.sub(r'\.rendition\.\d+\.\d+', '', img_name_without_ext)
            
            # Check for exact matches
            if img_name_clean.lower() == file_name_without_ext.lower():
                matches.append({
                    'product_uid': file_product_uid,
                    'file_path': file_path,
                    'file_filename': file_filename,
                    'file_type': file_type,
                    'image_path': img_path,
                    'image_filename': img_filename,
                    'match_type': 'exact'
                })
                break
            
            # Check for model image matches (with _mdl_c suffix)
            elif img_name_clean.lower() == f"{file_name_without_ext.lower()}_mdl_c":
                matches.append({
                    'product_uid': file_product_uid,
                    'file_path': file_path,
                    'file_filename': file_filename,
                    'file_type': file_type,
                    'image_path': img_path,
                    'image_filename': img_filename,
                    'match_type': 'model_image'
                })
                break
    
    # Report results
    print(f"\n=== MATCHING RESULTS ===")
    print(f"Found {len(matches)} matches!")
    
    # Group by match type
    exact_matches = [m for m in matches if m['match_type'] == 'exact']
    model_matches = [m for m in matches if m['match_type'] == 'model_image']
    
    print(f"Exact matches: {len(exact_matches)}")
    print(f"Model image matches: {len(model_matches)}")
    
    if matches:
        print(f"\n=== SAMPLE MATCHES ===")
        for match in matches[:10]:
            print(f"Product: {match['product_uid']}")
            print(f"  3D File: {match['file_filename']} ({match['file_type']})")
            print(f"  Image: {match['image_filename']} ({match['match_type']})")
            print()
    
    # Update database with matches
    print(f"\n=== UPDATING DATABASE ===")
    
    # Add a new column to track file-image relationships
    try:
        cursor.execute("ALTER TABLE files ADD COLUMN matched_image_path TEXT")
        print("✓ Added matched_image_path column to files table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ matched_image_path column already exists")
        else:
            print(f"✗ Error adding column: {e}")
    
    # Update files with matched images
    updated_count = 0
    for match in matches:
        try:
            cursor.execute("""
                UPDATE files 
                SET matched_image_path = ?
                WHERE product_uid = ? AND stored_path = ?
            """, (match['image_path'], match['product_uid'], match['file_path']))
            
            if cursor.rowcount > 0:
                updated_count += 1
                
        except Exception as e:
            print(f"✗ Error updating file {match['file_filename']}: {e}")
    
    conn.commit()
    print(f"✓ Updated {updated_count} files with matched images")
    
    # Show summary by product
    print(f"\n=== MATCHES BY PRODUCT ===")
    product_matches = {}
    for match in matches:
        product = match['product_uid']
        if product not in product_matches:
            product_matches[product] = []
        product_matches[product].append(match)
    
    for product, product_match_list in list(product_matches.items())[:10]:
        print(f"{product}: {len(product_match_list)} matches")
    
    conn.close()

if __name__ == "__main__":
    match_images_to_3d_files()
