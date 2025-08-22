#!/usr/bin/env python3
"""
Create SQLite views and enforce file_type hygiene
"""

import sqlite3
import sys

def main():
    DB = sys.argv[1] if len(sys.argv) > 1 else "library/index.sqlite"
    
    con = sqlite3.connect(DB)
    cur = con.cursor()
    
    print("=== ENFORCING FILE_TYPE HYGIENE ===")
    
    # Check for files with unusual file_type values
    cur.execute("""
        SELECT stored_path, file_type
        FROM files
        WHERE file_type NOT IN ('revit','sketchup','autocad_2d','autocad_3d','autocad','sif');
    """)
    
    unusual_files = cur.fetchall()
    if unusual_files:
        print(f"Found {len(unusual_files)} files with unusual file_type values:")
        for stored_path, file_type in unusual_files[:10]:
            print(f"  {file_type}: {stored_path}")
        if len(unusual_files) > 10:
            print(f"  ... and {len(unusual_files) - 10} more")
    else:
        print("All files have valid file_type values ✓")
    
    print("\n=== CREATING SHOPPING VIEWS ===")
    
    # Create product coverage view
    cur.execute("""
        CREATE VIEW IF NOT EXISTS v_product_coverage AS
        SELECT
          p.product_uid, p.brand, p.name, p.slug, p.category,
          MAX(CASE WHEN f.file_type='revit'      THEN 1 ELSE 0 END) AS has_revit,
          MAX(CASE WHEN f.file_type='sketchup'   THEN 1 ELSE 0 END) AS has_skp,
          MAX(CASE WHEN f.file_type='autocad_3d' THEN 1 ELSE 0 END) AS has_dwg3d,
          COUNT(*) AS file_count
        FROM products p
        LEFT JOIN files f ON f.product_uid = p.product_uid
        GROUP BY 1,2,3,4,5;
    """)
    print("Created v_product_coverage view ✓")
    
    # Create heavy files view
    cur.execute("""
        CREATE VIEW IF NOT EXISTS v_heavy_files AS
        SELECT brand, name, file_type, stored_path, ROUND(size_bytes/1024.0/1024.0,1) AS size_mb
        FROM products p JOIN files f ON p.product_uid=f.product_uid
        ORDER BY size_bytes DESC LIMIT 100;
    """)
    print("Created v_heavy_files view ✓")
    
    # Test the views
    print("\n=== TESTING VIEWS ===")
    
    cur.execute("SELECT COUNT(*) FROM v_product_coverage;")
    coverage_count = cur.fetchone()[0]
    print(f"Products in coverage view: {coverage_count}")
    
    cur.execute("SELECT COUNT(*) FROM v_heavy_files;")
    heavy_count = cur.fetchone()[0]
    print(f"Files in heavy files view: {heavy_count}")
    
    # Show sample data
    print("\nSample product coverage:")
    cur.execute("SELECT brand, name, has_revit, has_skp, has_dwg3d, file_count FROM v_product_coverage ORDER BY has_revit DESC, has_skp DESC LIMIT 5;")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} (R:{row[2]} S:{row[3]} D:{row[4]} F:{row[5]})")
    
    print("\nSample heavy files:")
    cur.execute("SELECT brand, name, file_type, size_mb FROM v_heavy_files LIMIT 5;")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} ({row[2]}) - {row[3]}MB")
    
    con.commit()
    con.close()
    
    print("\n=== COMPLETE ===")
    print("Run these queries to explore the data:")
    print("sqlite3 library/index.sqlite \"SELECT * FROM v_product_coverage ORDER BY has_revit DESC, has_skp DESC LIMIT 20;\"")
    print("sqlite3 library/index.sqlite \"SELECT * FROM v_heavy_files LIMIT 10;\"")

if __name__ == "__main__":
    main()
