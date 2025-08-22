#!/usr/bin/env python3
import sqlite3
import os
import re

def comprehensive_file_matching():
    """Comprehensive matching of images to 3D files with multiple strategies."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()

    print("=== COMPREHENSIVE FILE-IMAGE MATCHING ===")

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
    matched_files = set()  # Track which files have been matched

    for file_product_uid, file_path, file_type, file_ext in files:
        # Skip if already matched
        if (file_product_uid, file_path) in matched_files:
            continue

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

            # Strategy 1: Exact match
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
                matched_files.add((file_product_uid, file_path))
                break

            # Strategy 2: Model image with _mdl_c suffix
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
                matched_files.add((file_product_uid, file_path))
                break

            # Strategy 3: Remove _3D suffix from file and match
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
                    matched_files.add((file_product_uid, file_path))
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
                    matched_files.add((file_product_uid, file_path))
                    break

            # Strategy 4: Check if image contains the file name (partial match)
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
                    matched_files.add((file_product_uid, file_path))
                    break

            # Strategy 5: Remove common suffixes and try again
            else:
                # Remove common suffixes from file name
                file_name_clean = re.sub(r'_(3d|2d|skp|rfa|rvt|dwg)$', '', file_name_without_ext.lower())
                if img_name_clean.lower() == file_name_clean:
                    matches.append({
                        'product_uid': file_product_uid,
                        'file_path': file_path,
                        'file_filename': file_filename,
                        'file_type': file_type,
                        'image_path': img_path,
                        'image_filename': img_filename,
                        'match_type': 'cleaned_suffix'
                    })
                    matched_files.add((file_product_uid, file_path))
                    break
                elif img_name_clean.lower() == f"{file_name_clean}_mdl_c":
                    matches.append({
                        'product_uid': file_product_uid,
                        'file_path': file_path,
                        'file_filename': file_filename,
                        'file_type': file_type,
                        'image_path': img_path,
                        'image_filename': img_filename,
                        'match_type': 'cleaned_suffix_model'
                    })
                    matched_files.add((file_product_uid, file_path))
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

    # Now let's try to match remaining files by finding the best image for each product
    print(f"\n=== MATCHING REMAINING FILES BY PRODUCT ===")
    
    # Get products that have images but not all files matched
    cursor.execute("""
        SELECT DISTINCT p.product_uid, p.name
        FROM products p
        JOIN files f ON p.product_uid = f.product_uid
        JOIN images i ON p.product_uid = i.product_uid
        WHERE f.matched_image_path IS NULL
        AND i.local_path IS NOT NULL
        ORDER BY p.product_uid
    """)
    
    products_with_unmatched_files = cursor.fetchall()
    print(f"Found {len(products_with_unmatched_files)} products with unmatched files")

    additional_matches = 0
    
    for product_uid, product_name in products_with_unmatched_files:
        # Get the best image for this product
        cursor.execute("""
            SELECT local_path, provider, rationale
            FROM images
            WHERE product_uid = ? AND local_path IS NOT NULL
            ORDER BY 
                CASE
                    WHEN provider = 'herman_miller_comprehensive' THEN 1
                    WHEN provider = 'herman_miller_api' THEN 2
                    ELSE 3
                END,
                CASE
                    WHEN local_path LIKE '%_mdl_c%' THEN 1
                    ELSE 2
                END,
                local_path
            LIMIT 1
        """, (product_uid,))
        
        best_image = cursor.fetchone()
        if best_image:
            image_path, provider, rationale = best_image
            
            # Get all unmatched files for this product
            cursor.execute("""
                SELECT stored_path, file_type
                FROM files
                WHERE product_uid = ? AND matched_image_path IS NULL
                AND file_type IN ('revit', 'sketchup', 'autocad_3d', 'autocad_2d', 'autocad')
            """, (product_uid,))
            
            unmatched_files = cursor.fetchall()
            
            for file_path, file_type in unmatched_files:
                try:
                    cursor.execute("""
                        UPDATE files
                        SET matched_image_path = ?
                        WHERE product_uid = ? AND stored_path = ?
                    """, (image_path, product_uid, file_path))
                    
                    if cursor.rowcount > 0:
                        additional_matches += 1
                        print(f"  {product_uid}: {os.path.basename(file_path)} -> {os.path.basename(image_path)}")
                        
                except Exception as e:
                    print(f"✗ Error updating file {file_path}: {e}")

    conn.commit()
    print(f"✓ Added {additional_matches} additional matches by product")

    # Final summary
    cursor.execute("SELECT COUNT(*) FROM files WHERE matched_image_path IS NOT NULL")
    total_matched = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM files")
    total_files = cursor.fetchone()[0]
    
    print(f"\n=== FINAL SUMMARY ===")
    print(f"Total files: {total_files}")
    print(f"Files with matched images: {total_matched}")
    print(f"Match rate: {(total_matched/total_files)*100:.1f}%")

    conn.close()

if __name__ == "__main__":
    comprehensive_file_matching()
