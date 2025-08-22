#!/usr/bin/env python3
import sqlite3
import os

def update_product_cards_with_matched_images():
    """Update product cards to show matched images for 3D files."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== UPDATING PRODUCT CARDS WITH MATCHED IMAGES ===")
    
    # Get products with matched images
    cursor.execute("""
        SELECT DISTINCT p.product_uid, p.name, p.brand,
               COUNT(f.matched_image_path) as matched_files,
               COUNT(f.sha256) as total_files
        FROM products p
        LEFT JOIN files f ON p.product_uid = f.product_uid
        WHERE f.matched_image_path IS NOT NULL
        GROUP BY p.product_uid
        ORDER BY matched_files DESC
    """)
    
    products_with_matches = cursor.fetchall()
    
    print(f"Found {len(products_with_matches)} products with matched images")
    
    for product_uid, name, brand, matched_files, total_files in products_with_matches:
        print(f"\n{product_uid}: {name}")
        print(f"  Matched files: {matched_files}/{total_files}")
        
        # Get the matched files for this product
        cursor.execute("""
            SELECT stored_path, file_type, matched_image_path
            FROM files
            WHERE product_uid = ? AND matched_image_path IS NOT NULL
            ORDER BY file_type, stored_path
        """, (product_uid,))
        
        matched_files_list = cursor.fetchall()
        
        for file_path, file_type, image_path in matched_files_list:
            file_name = os.path.basename(file_path)
            image_name = os.path.basename(image_path)
            print(f"    {file_name} ({file_type}) -> {image_name}")
    
    # Update product card image paths to use matched images
    print(f"\n=== UPDATING PRODUCT CARD IMAGES ===")
    
    updated_count = 0
    
    for product_uid, name, brand, matched_files, total_files in products_with_matches:
        # Get the best matched image for this product (prefer model images)
        cursor.execute("""
            SELECT f.matched_image_path, f.file_type
            FROM files f
            WHERE f.product_uid = ? AND f.matched_image_path IS NOT NULL
            ORDER BY 
                CASE 
                    WHEN f.matched_image_path LIKE '%_mdl_c%' THEN 1
                    ELSE 2
                END,
                f.file_type,
                f.stored_path
            LIMIT 1
        """, (product_uid,))
        
        result = cursor.fetchone()
        
        if result:
            best_image_path, file_type = result
            print(f"  {product_uid}: Using {os.path.basename(best_image_path)} (from {file_type})")
            
            # Update the product card image
            cursor.execute("""
                UPDATE products 
                SET product_card_image_path = ?
                WHERE product_uid = ?
            """, (best_image_path, product_uid))
            
            updated_count += 1
    
    conn.commit()
    print(f"✓ Updated {updated_count} product cards with matched images")
    
    # Show final results
    print(f"\n=== FINAL PRODUCT CARD IMAGES ===")
    
    cursor.execute("""
        SELECT product_uid, name, product_card_image_path
        FROM products
        WHERE product_card_image_path IS NOT NULL
        ORDER BY name
        LIMIT 10
    """)
    
    final_results = cursor.fetchall()
    
    for product_uid, name, image_path in final_results:
        if image_path:
            image_name = os.path.basename(image_path)
            print(f"  {product_uid}: {name}")
            print(f"    Card image: {image_name}")
            print()
    
    conn.close()

if __name__ == "__main__":
    update_product_cards_with_matched_images()
