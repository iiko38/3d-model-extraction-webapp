#!/usr/bin/env python3
import sqlite3
from pathlib import Path
import os

def fix_database_paths():
    """Fix the database paths to match the actual downloaded files."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== FIXING DATABASE PATHS ===")
    
    # Get all images with local paths
    cursor.execute("SELECT product_uid, image_url, local_path FROM images WHERE local_path IS NOT NULL")
    images = cursor.fetchall()
    
    print(f"Found {len(images)} images with local paths")
    
    updated = 0
    for product_uid, image_url, local_path in images:
        # Check if the file exists at the current path
        current_path = Path("library") / local_path
        
        if not current_path.exists():
            # Try to find the file in the product directory
            product_dir = Path("library/images") / product_uid.replace(':', '/')
            
            if product_dir.exists():
                # Look for files in the product directory
                for file_path in product_dir.iterdir():
                    if file_path.is_file():
                        # Check if this file matches the image URL (by checking if it's a product image)
                        if any(keyword in file_path.name.lower() for keyword in ['mdl', 'product', 'chair', 'stool', 'table']):
                            # Update the database with the correct path
                            correct_path = str(file_path.relative_to(Path("library"))).replace('\\', '/')
                            
                            cursor.execute(
                                "UPDATE images SET local_path = ? WHERE product_uid = ? AND image_url = ?",
                                (correct_path, product_uid, image_url)
                            )
                            
                            print(f"  Updated: {local_path} -> {correct_path}")
                            updated += 1
                            break
            else:
                print(f"  ✗ Product directory not found: {product_dir}")
        else:
            print(f"  ✓ File exists: {local_path}")
    
    conn.commit()
    conn.close()
    
    print(f"\n=== FIX COMPLETE ===")
    print(f"Updated {updated} image paths")

if __name__ == "__main__":
    fix_database_paths()
