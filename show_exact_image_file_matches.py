#!/usr/bin/env python3
import sqlite3
import os
import re

def show_exact_image_file_matches():
    """Show exact matches between image filenames and 3D file filenames."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== EXACT IMAGE-FILE MATCHES ===")
    
    # Get all images with local paths
    cursor.execute("""
        SELECT product_uid, local_path, image_url, provider, rationale
        FROM images 
        WHERE local_path IS NOT NULL
        ORDER BY product_uid, local_path
    """)
    
    images = cursor.fetchall()
    
    # Get all 3D files
    cursor.execute("""
        SELECT product_uid, stored_path, file_type, ext
        FROM files 
        WHERE file_type IN ('revit', 'sketchup', 'autocad_3d', 'autocad_2d', 'autocad')
        ORDER BY product_uid, stored_path
    """)
    
    files = cursor.fetchall()
    
    # Find exact matches
    exact_matches = []
    
    for img_product_uid, img_path, img_url, provider, rationale in images:
        if not img_path:
            continue
            
        # Extract filename from image path
        img_filename = os.path.basename(img_path)
        img_name_without_ext = os.path.splitext(img_filename)[0]
        
        # Remove rendition suffixes
        img_name_clean = re.sub(r'\.rendition\.\d+\.\d+', '', img_name_without_ext)
        
        # Look for matching 3D files
        for file_product_uid, file_path, file_type, file_ext in files:
            if img_product_uid != file_product_uid:
                continue
                
            # Extract filename from file path
            file_filename = os.path.basename(file_path)
            file_name_without_ext = os.path.splitext(file_filename)[0]
            
            # Check for exact matches (after cleaning)
            if img_name_clean.lower() == file_name_without_ext.lower():
                exact_matches.append({
                    'product_uid': img_product_uid,
                    'image_path': img_path,
                    'image_filename': img_filename,
                    'image_clean': img_name_clean,
                    'file_path': file_path,
                    'file_filename': file_filename,
                    'file_type': file_type
                })
    
    # Report results
    print(f"Found {len(exact_matches)} exact matches!")
    
    if exact_matches:
        print(f"\n=== EXACT MATCHES ===")
        for match in exact_matches:
            print(f"Product: {match['product_uid']}")
            print(f"  Image: {match['image_filename']}")
            print(f"  Clean: {match['image_clean']}")
            print(f"  File:  {match['file_filename']} ({match['file_type']})")
            print()
    
    # Show some examples of the pattern
    print(f"\n=== FILENAME PATTERN EXAMPLES ===")
    
    # Get some sample 3D files
    cursor.execute("""
        SELECT product_uid, stored_path, file_type
        FROM files 
        WHERE file_type IN ('revit', 'sketchup', 'autocad_3d')
        ORDER BY product_uid, stored_path
        LIMIT 10
    """)
    
    sample_files = cursor.fetchall()
    
    for product_uid, file_path, file_type in sample_files:
        file_filename = os.path.basename(file_path)
        file_name_without_ext = os.path.splitext(file_filename)[0]
        
        print(f"3D File: {file_filename}")
        print(f"  Expected image: {file_name_without_ext}.jpg or {file_name_without_ext}_mdl_c.jpg")
        print()
    
    conn.close()

if __name__ == "__main__":
    show_exact_image_file_matches()
