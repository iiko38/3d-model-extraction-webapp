#!/usr/bin/env python3
import sqlite3

def fix_image_product_mapping():
    """Fix the product UID mapping between images and products tables."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== FIXING IMAGE-PRODUCT MAPPING ===")
    
    # Check current state
    cursor.execute("SELECT DISTINCT product_uid FROM images")
    image_products = [row[0] for row in cursor.fetchall()]
    print(f"Products in images table: {image_products}")
    
    # Create mapping from hyphenated to underscore UIDs
    mapping = {
        'herman_miller:aeron-chairs': 'herman_miller:aeron_chairs',
        'herman_miller:zeph-chair': 'herman_miller:zeph_chair', 
        'herman_miller:zeph-stool': 'herman_miller:zeph_stool'
    }
    
    # Update images table
    for old_uid, new_uid in mapping.items():
        cursor.execute("UPDATE images SET product_uid = ? WHERE product_uid = ?", (new_uid, old_uid))
        updated = cursor.rowcount
        print(f"Updated {updated} images from {old_uid} to {new_uid}")
    
    conn.commit()
    
    # Verify the fix
    cursor.execute("SELECT DISTINCT product_uid FROM images")
    new_image_products = [row[0] for row in cursor.fetchall()]
    print(f"Products in images table after fix: {new_image_products}")
    
    # Check if products exist
    for product_uid in new_image_products:
        cursor.execute("SELECT COUNT(*) FROM products WHERE product_uid = ?", (product_uid,))
        count = cursor.fetchone()[0]
        print(f"Product {product_uid}: {'EXISTS' if count > 0 else 'MISSING'} in products table")
    
    conn.close()
    print("=== FIX COMPLETE ===")

if __name__ == "__main__":
    fix_image_product_mapping()
