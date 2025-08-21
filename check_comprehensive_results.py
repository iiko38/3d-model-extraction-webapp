#!/usr/bin/env python3
import sqlite3

def check_comprehensive_results():
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== COMPREHENSIVE SCRAPING RESULTS ===")
    
    # Check total images from comprehensive scraping
    cursor.execute("SELECT COUNT(*) FROM images WHERE provider = 'herman_miller_comprehensive'")
    total = cursor.fetchone()[0]
    print(f"Total images from comprehensive scraping: {total}")
    
    # Check products with images
    cursor.execute("SELECT product_uid, COUNT(*) as count FROM images WHERE provider = 'herman_miller_comprehensive' GROUP BY product_uid ORDER BY count DESC LIMIT 15")
    results = cursor.fetchall()
    
    print(f"\nTop products with images:")
    for uid, count in results:
        print(f"  {uid}: {count} images")
    
    # Check overall image stats
    cursor.execute("SELECT status, COUNT(*) FROM images GROUP BY status")
    status_results = cursor.fetchall()
    
    print(f"\nOverall image status:")
    for status, count in status_results:
        print(f"  {status}: {count}")
    
    conn.close()

if __name__ == "__main__":
    check_comprehensive_results()
