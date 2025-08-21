#!/usr/bin/env python3
import sqlite3
import os
from pathlib import Path

def cleanup_unused_images():
    """Remove images that are not referenced by any files."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()

    print("=== CLEANING UP UNUSED IMAGES ===")

    # Get all images that are referenced by files
    cursor.execute("""
        SELECT DISTINCT matched_image_path
        FROM files
        WHERE matched_image_path IS NOT NULL
    """)
    
    referenced_images = {row[0] for row in cursor.fetchall()}
    print(f"Found {len(referenced_images)} images referenced by files")

    # Get all images in the database
    cursor.execute("""
        SELECT local_path
        FROM images
        WHERE local_path IS NOT NULL
    """)
    
    all_images = {row[0] for row in cursor.fetchall()}
    print(f"Found {len(all_images)} total images in database")

    # Find unused images
    unused_images = all_images - referenced_images
    print(f"Found {len(unused_images)} unused images")

    if unused_images:
        print(f"\n=== UNUSED IMAGES (first 20) ===")
        for img_path in list(unused_images)[:20]:
            print(f"  {img_path}")

        # Ask for confirmation
        response = input(f"\nDelete {len(unused_images)} unused images? (y/N): ")
        
        if response.lower() == 'y':
            # Delete unused images from database
            deleted_count = 0
            for img_path in unused_images:
                try:
                    cursor.execute("""
                        DELETE FROM images
                        WHERE local_path = ?
                    """, (img_path,))
                    
                    if cursor.rowcount > 0:
                        deleted_count += 1
                        
                        # Also delete the physical file
                        full_path = Path("library") / img_path
                        if full_path.exists():
                            try:
                                full_path.unlink()
                                print(f"  Deleted: {img_path}")
                            except Exception as e:
                                print(f"  Failed to delete file {img_path}: {e}")
                        
                except Exception as e:
                    print(f"  Failed to delete from DB {img_path}: {e}")

            conn.commit()
            print(f"✓ Deleted {deleted_count} unused images from database and filesystem")
        else:
            print("Cleanup cancelled")
    else:
        print("No unused images found!")

    # Final summary
    cursor.execute("SELECT COUNT(*) FROM images WHERE local_path IS NOT NULL")
    remaining_images = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM files WHERE matched_image_path IS NOT NULL")
    matched_files = cursor.fetchone()[0]
    
    print(f"\n=== FINAL SUMMARY ===")
    print(f"Remaining images: {remaining_images}")
    print(f"Files with matched images: {matched_files}")
    print(f"Image efficiency: {(matched_files/remaining_images)*100:.1f}% (files per image)")

    conn.close()

if __name__ == "__main__":
    cleanup_unused_images()
