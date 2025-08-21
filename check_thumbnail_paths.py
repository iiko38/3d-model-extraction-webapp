#!/usr/bin/env python3
import sqlite3

def check_thumbnail_paths():
    """Check if thumbnail paths were updated in the database."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    # Count files with matched_image_path
    cursor.execute('SELECT COUNT(*) FROM files WHERE matched_image_path IS NOT NULL AND matched_image_path != ""')
    with_paths = cursor.fetchone()[0]
    
    # Count files with checked URLs
    cursor.execute('SELECT COUNT(*) FROM files WHERE urls_checked = 1')
    checked = cursor.fetchone()[0]
    
    # Count files with both checked URLs and matched_image_path
    cursor.execute('SELECT COUNT(*) FROM files WHERE urls_checked = 1 AND matched_image_path IS NOT NULL AND matched_image_path != ""')
    both = cursor.fetchone()[0]
    
    print(f"📊 Thumbnail Path Analysis:")
    print(f"  Files with checked URLs: {checked}")
    print(f"  Files with matched_image_path: {with_paths}")
    print(f"  Files with both: {both}")
    
    # Show some sample files with matched_image_path
    cursor.execute("""
        SELECT sha256, variant, matched_image_path, thumbnail_url 
        FROM files 
        WHERE matched_image_path IS NOT NULL AND matched_image_path != ""
        LIMIT 5
    """)
    
    samples = cursor.fetchall()
    if samples:
        print(f"\n📝 Sample files with matched_image_path:")
        for sha256, variant, matched_path, thumbnail_url in samples:
            print(f"  {sha256[:8]}... - {variant}")
            print(f"    Local path: {matched_path}")
            print(f"    Original URL: {thumbnail_url}")
            print()
    
    conn.close()

if __name__ == "__main__":
    check_thumbnail_paths()
