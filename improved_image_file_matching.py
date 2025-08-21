#!/usr/bin/env python3
import sqlite3
import os
import re

def improved_image_file_matching():
    """Improved matching of images to 3D files with more pattern variations."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== IMPROVED IMAGE-FILE MATCHING ===")
    
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
            
            # Pattern 1: Exact match
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
            
            # Pattern 2: Model image with _mdl_c suffix
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
            
            # Pattern 3: Remove _3D suffix from file and match
            elif file_name_without_ext.lower().endswith('_3d'):
                file_name_no_3d = file_name_without_ext.lower()[:-3]
                if img_name_clean.lower() == file_name_no_3d:
                    matches.append({
                        'product_uid': file_product_uid,
                        'file_path': file_path,
                        'file_filename': file_filename,
                        'file_type': file_type,
                        'image_path': img_path,
                        'image_filename': img_filename,
                        'match_type': 'no_3d_suffix'
                    })
                    break
                elif img_name_clean.lower() == f"{file_name_no_3d}_mdl_c":
                    matches.append({
                        'product_uid': file_product_uid,
                        'file_path': file_path,
                        'file_filename': file_filename,
                        'file_type': file_type,
                        'image_path': img_path,
                        'image_filename': img_filename,
                        'match_type': 'no_3d_suffix_model'
                    })
                    break
            
            # Pattern 4: Check if image contains the file name (partial match)
            elif file_name_without_ext.lower() in img_name_clean.lower():
                # Make sure it's not just a common word
                if len(file_name_without_ext) > 5:  # Avoid short common words
                    matches.append({
                        'product_uid': file_product_uid,
                        'file_path': file_path,
                        'file_filename': file_filename,
                        'file_type': file_type,
                        'image_path': img_path,
                        'image_filename': img_filename,
                        'match_type': 'partial_contained'
                    })
                    break
    
    # Report results
    print(f"\n=== MATCHING RESULTS ===")
    print(f"Found {len(matches)} matches!")
    
    # Group by match type
    match_types = {}
    for match in matches:
        match_type = match['match_type']
        if match_type not in match_types:
            match_types[match_type] = []
        match_types[match_type].append(match)
    
    for match_type, match_list in match_types.items():
        print(f"{match_type}: {len(match_list)} matches")
    
    if matches:
        print(f"\n=== SAMPLE MATCHES ===")
        for match in matches[:15]:
            print(f"Product: {match['product_uid']}")
            print(f"  3D File: {match['file_filename']} ({match['file_type']})")
            print(f"  Image: {match['image_filename']} ({match['match_type']})")
            print()
    
    # Update database with matches
    print(f"\n=== UPDATING DATABASE ===")
    
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
    
    for product, product_match_list in list(product_matches.items())[:15]:
        print(f"{product}: {len(product_match_list)} matches")
    
    conn.close()

if __name__ == "__main__":
    improved_image_file_matching()
