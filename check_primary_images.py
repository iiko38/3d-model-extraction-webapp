#!/usr/bin/env python3
import sqlite3

def check_primary_images():
    """Check if primary images were selected correctly."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== PRIMARY IMAGE CHECK ===")
    
    # Check products with primary images
    cursor.execute("""
        SELECT p.product_uid, p.name, p.product_card_image_path, i.image_score
        FROM products p
        LEFT JOIN images i ON p.product_uid = i.product_uid AND i.is_primary = 1
        WHERE p.product_card_image_path IS NOT NULL
        ORDER BY p.name
        LIMIT 10
    """)
    
    results = cursor.fetchall()
    
    print(f"Products with primary images: {len(results)}")
    for uid, name, path, score in results:
        print(f"  {uid}: {name}")
        print(f"    Path: {path}")
        print(f"    Score: {score}")
        print()
    
    # Check total primary images
    cursor.execute("SELECT COUNT(*) FROM images WHERE is_primary = 1")
    primary_count = cursor.fetchone()[0]
    print(f"Total primary images: {primary_count}")
    
    conn.close()

if __name__ == "__main__":
    check_primary_images()
