#!/usr/bin/env python3
"""
Run sanity queries on the SQLite database
"""

import sqlite3
import sys

def main():
    DB = sys.argv[1] if len(sys.argv) > 1 else "library/index.sqlite"
    
    con = sqlite3.connect(DB)
    cur = con.cursor()
    
    print("=== SANITY QUERIES ===")
    
    # Count products
    cur.execute("SELECT COUNT(*) FROM products;")
    product_count = cur.fetchone()[0]
    print(f"Products: {product_count}")
    
    # Count files by file type
    cur.execute("SELECT file_type, COUNT(*) FROM files GROUP BY file_type ORDER BY COUNT(*) DESC;")
    file_types = cur.fetchall()
    print(f"\nFiles by type:")
    for file_type, count in file_types:
        print(f"  {file_type}: {count}")
    
    # Count files by brand (join with products table)
    cur.execute("""
        SELECT p.brand, COUNT(*) 
        FROM files f 
        JOIN products p ON f.product_uid = p.product_uid 
        GROUP BY p.brand 
        ORDER BY COUNT(*) DESC;
    """)
    brands = cur.fetchall()
    print(f"\nFiles by brand:")
    for brand, count in brands:
        print(f"  {brand}: {count}")
    
    # Total file count
    cur.execute("SELECT COUNT(*) FROM files;")
    total_files = cur.fetchone()[0]
    print(f"\nTotal files: {total_files}")
    
    # Sample products
    cur.execute("SELECT brand, name, slug FROM products LIMIT 5;")
    sample_products = cur.fetchall()
    print(f"\nSample products:")
    for brand, name, slug in sample_products:
        print(f"  {brand}: {name} ({slug})")
    
    con.close()

if __name__ == "__main__":
    main()
