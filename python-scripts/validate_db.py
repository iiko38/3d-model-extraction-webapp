#!/usr/bin/env python3
"""
Validate SQLite database integrity
"""

import sqlite3
import sys


def main():
    DB = sys.argv[1] if len(sys.argv) > 1 else "library/index.sqlite"
    
    con = sqlite3.connect(DB)
    cur = con.cursor()
    
    print("=== DATABASE VALIDATION ===")
    
    # Files count
    cur.execute("SELECT COUNT(*) FROM files;")
    files_count = cur.fetchone()[0]
    print(f"Files count: {files_count}")
    
    # Products count
    cur.execute("SELECT COUNT(*) FROM products;")
    products_count = cur.fetchone()[0]
    print(f"Products count: {products_count}")
    
    # Invalid file_type count
    cur.execute("""
        SELECT COUNT(*) FROM files 
        WHERE file_type NOT IN ('revit','sketchup','autocad_3d','autocad_2d','autocad','sif');
    """)
    invalid_file_type_count = cur.fetchone()[0]
    print(f"Invalid file_type count: {invalid_file_type_count}")
    
    # Orphan rows (files without matching product)
    cur.execute("""
        SELECT COUNT(*) FROM files f
        LEFT JOIN products p ON f.product_uid = p.product_uid
        WHERE p.product_uid IS NULL;
    """)
    orphan_count = cur.fetchone()[0]
    print(f"Orphan rows: {orphan_count}")
    
    # Breakdown by file_type
    print("\nBreakdown by file_type:")
    cur.execute("""
        SELECT file_type, COUNT(*) 
        FROM files 
        GROUP BY file_type 
        ORDER BY COUNT(*) DESC;
    """)
    file_types = cur.fetchall()
    for file_type, count in file_types:
        print(f"  {file_type}: {count}")
    
    # Breakdown by brand
    print("\nBreakdown by brand:")
    cur.execute("""
        SELECT p.brand, COUNT(*) 
        FROM files f
        JOIN products p ON f.product_uid = p.product_uid
        GROUP BY p.brand 
        ORDER BY COUNT(*) DESC;
    """)
    brands = cur.fetchall()
    for brand, count in brands:
        print(f"  {brand}: {count}")
    
    # Sample products
    print("\nSample products:")
    cur.execute("""
        SELECT p.brand, p.name, p.slug, COUNT(f.sha256) as file_count
        FROM products p
        LEFT JOIN files f ON p.product_uid = f.product_uid
        GROUP BY p.product_uid
        ORDER BY file_count DESC
        LIMIT 5;
    """)
    sample_products = cur.fetchall()
    for brand, name, slug, file_count in sample_products:
        print(f"  {brand}: {name} ({slug}) - {file_count} files")
    
    con.close()
    
    # Summary assessment
    print("\n=== VALIDATION SUMMARY ===")
    if invalid_file_type_count == 0:
        print("✅ All file types are valid")
    else:
        print(f"❌ {invalid_file_type_count} files have invalid file types")
    
    if orphan_count == 0:
        print("✅ No orphan files")
    else:
        print(f"❌ {orphan_count} orphan files found")
    
    if products_count > 30:
        print(f"✅ Good product count: {products_count}")
    else:
        print(f"❌ Low product count: {products_count}")
    
    if files_count > 500:
        print(f"✅ Good file count: {files_count}")
    else:
        print(f"❌ Low file count: {files_count}")


if __name__ == "__main__":
    main()
