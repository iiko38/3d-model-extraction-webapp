#!/usr/bin/env python3
"""
Update thumbnail paths in database based on downloaded files
"""

import sqlite3
import os
from pathlib import Path

def update_thumbnail_paths():
    """Update the database with thumbnail paths based on downloaded files."""
    db_path = "library/index.sqlite"
    thumbnails_dir = Path("static/thumbnails/original")
    
    if not thumbnails_dir.exists():
        print("❌ Thumbnails directory not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all downloaded thumbnail files
    thumbnail_files = list(thumbnails_dir.glob("*.jpg"))
    print(f"📁 Found {len(thumbnail_files)} thumbnail files")
    
    updated_count = 0
    
    for file_path in thumbnail_files:
        # Extract SHA256 from filename (format: sha256_hash.ext)
        filename = file_path.stem
        sha256 = filename.split('_')[0]
        
        # Create the relative path for the database (use forward slashes for web)
        relative_path = str(file_path.relative_to("static")).replace("\\", "/")
        
        # Update the database
        cursor.execute("""
            UPDATE files 
            SET matched_image_path = ?
            WHERE sha256 = ?
        """, (relative_path, sha256))
        
        if cursor.rowcount > 0:
            updated_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"✅ Updated {updated_count} files with thumbnail paths")
    
    # Verify the update
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM files WHERE matched_image_path IS NOT NULL AND matched_image_path != ''")
    count = cursor.fetchone()[0]
    conn.close()
    
    print(f"📊 Total files with matched_image_path: {count}")

if __name__ == "__main__":
    update_thumbnail_paths()
