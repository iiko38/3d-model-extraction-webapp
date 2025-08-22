#!/usr/bin/env python3
import sqlite3

def check_products():
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== PRODUCT CHECK ===")
    
    # Check products with images
    cursor.execute("SELECT DISTINCT product_uid FROM images LIMIT 10")
    print("Products with images:")
    for (product_uid,) in cursor.fetchall():
        print(f"  {product_uid}")
    
    # Check if these products exist in products table
    cursor.execute("SELECT product_uid, name FROM products WHERE product_uid IN (SELECT DISTINCT product_uid FROM images) LIMIT 5")
    print("\nProducts that exist in products table:")
    for product_uid, name in cursor.fetchall():
        print(f"  {product_uid}: {name}")
    
    # Check what products are actually in the products table
    cursor.execute("SELECT product_uid, name FROM products WHERE name LIKE '%zeph%' OR name LIKE '%aeron%' LIMIT 10")
    print("\nZeph/Aeron products in products table:")
    for product_uid, name in cursor.fetchall():
        print(f"  {product_uid}: {name}")
    
    # Check total products
    cursor.execute("SELECT COUNT(*) FROM products")
    total = cursor.fetchone()[0]
    print(f"\nTotal products in database: {total}")
    
    conn.close()

if __name__ == "__main__":
    check_products()
