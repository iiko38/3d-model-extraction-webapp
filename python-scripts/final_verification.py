#!/usr/bin/env python3
import sqlite3

def final_verification():
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== FINAL VERIFICATION RESULTS ===\n")
    
    # Core image stats
    print("Core image stats:")
    cursor.execute("SELECT status,COUNT(*) FROM images GROUP BY status")
    status_counts = cursor.fetchall()
    for status, count in status_counts:
        print(f"  {status}: {count}")
    
    cursor.execute("SELECT COUNT(DISTINCT product_uid) FROM images")
    products_with_images = cursor.fetchone()[0]
    print(f"Products with images: {products_with_images}")
    
    cursor.execute("SELECT product_uid,COUNT(*) c FROM images GROUP BY product_uid ORDER BY c DESC LIMIT 10")
    top_products = cursor.fetchall()
    print("\nTop products by image count:")
    for uid, count in top_products:
        print(f"  {uid}: {count}")
    
    # Coverage (which products still have nothing)
    print("\nCoverage - Products with no images:")
    cursor.execute("""
    SELECT p.product_uid,p.name
    FROM products p
    LEFT JOIN (SELECT DISTINCT product_uid FROM images) i USING(product_uid)
    WHERE i.product_uid IS NULL
    ORDER BY p.name LIMIT 30
    """)
    products_without_images = cursor.fetchall()
    for uid, name in products_without_images:
        print(f"  {uid}: {name}")
    
    # Quality sniff (lowest scoring pending to spot junk)
    print("\nQuality sniff - Lowest scoring pending:")
    cursor.execute("""
    SELECT product_uid,variant,score,image_url
    FROM images
    WHERE status='pending'
    ORDER BY score ASC LIMIT 20
    """)
    low_scoring = cursor.fetchall()
    for uid, variant, score, url in low_scoring:
        print(f"  {uid} ({variant}): score={score}, url={url[:50]}...")
    
    # Domain concentration (sanity)
    print("\nDomain concentration:")
    cursor.execute("""
    SELECT
      substr(image_url,1, instr(substr(image_url,9),'/')+8) AS domain,
      COUNT(*) c
    FROM images
    GROUP BY domain
    ORDER BY c DESC LIMIT 15
    """)
    domains = cursor.fetchall()
    for domain, count in domains:
        print(f"  {domain}: {count}")
    
    conn.close()

if __name__ == "__main__":
    final_verification()
