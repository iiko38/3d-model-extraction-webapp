#!/usr/bin/env python3
import sqlite3

def check_images():
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== IMAGE CHECK ===")
    
    # Check total images
    cursor.execute("SELECT COUNT(*) FROM images")
    total = cursor.fetchone()[0]
    print(f"Total images: {total}")
    
    # Check by status
    cursor.execute("SELECT status, COUNT(*) FROM images GROUP BY status")
    print("\nBy status:")
    for status, count in cursor.fetchall():
        print(f"  {status}: {count}")
    
    # Check sample images for zeph-stool
    cursor.execute("SELECT image_url, score FROM images WHERE product_uid = 'herman_miller:zeph-stool' LIMIT 3")
    print("\nSample images for zeph-stool:")
    for url, score in cursor.fetchall():
        print(f"  Score {score}: {url[:60]}...")
    
    conn.close()

if __name__ == "__main__":
    check_images()
