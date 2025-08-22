#!/usr/bin/env python3
import sqlite3

def check_thumbnail_data():
    """Check thumbnail URL data and urls_checked status."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    # Count files with checked URLs
    cursor.execute('SELECT COUNT(*) FROM files WHERE urls_checked = 1')
    checked = cursor.fetchone()[0]
    
    # Count files with thumbnail URLs
    cursor.execute('SELECT COUNT(*) FROM files WHERE thumbnail_url IS NOT NULL AND thumbnail_url != ""')
    thumbnails = cursor.fetchone()[0]
    
    # Count files with both checked URLs and thumbnail URLs
    cursor.execute('SELECT COUNT(*) FROM files WHERE urls_checked = 1 AND thumbnail_url IS NOT NULL AND thumbnail_url != ""')
    both = cursor.fetchone()[0]
    
    # Total files
    cursor.execute('SELECT COUNT(*) FROM files')
    total = cursor.fetchone()[0]
    
    print(f"📊 Thumbnail URL Analysis:")
    print(f"  Total files: {total}")
    print(f"  Files with checked URLs: {checked}")
    print(f"  Files with thumbnail URLs: {thumbnails}")
    print(f"  Files with both checked URLs and thumbnail URLs: {both}")
    
    # Show some sample files with checked URLs and thumbnail URLs
    cursor.execute("""
        SELECT sha256, variant, thumbnail_url, urls_checked 
        FROM files 
        WHERE urls_checked = 1 AND thumbnail_url IS NOT NULL AND thumbnail_url != ""
        LIMIT 5
    """)
    
    samples = cursor.fetchall()
    if samples:
        print(f"\n📝 Sample files with checked URLs and thumbnail URLs:")
        for sha256, variant, thumbnail_url, urls_checked in samples:
            print(f"  {sha256[:8]}... - {variant}")
            print(f"    Thumbnail: {thumbnail_url}")
            print(f"    Checked: {urls_checked}")
            print()
    
    conn.close()

if __name__ == "__main__":
    check_thumbnail_data()
