#!/usr/bin/env python3
import sqlite3

def check_images_schema():
    """Check the actual schema of the images table."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== IMAGES TABLE SCHEMA ===")
    
    # Get table info
    cursor.execute("PRAGMA table_info(images)")
    columns = cursor.fetchall()
    
    for col in columns:
        print(f"  {col[1]} ({col[2]}) - Default: {col[4]}")
    
    # Get sample data
    print("\n=== SAMPLE IMAGE DATA ===")
    cursor.execute("SELECT * FROM images LIMIT 1")
    sample = cursor.fetchone()
    
    if sample:
        print("Sample row:")
        for i, col in enumerate(columns):
            print(f"  {col[1]}: {sample[i]}")
    
    conn.close()

if __name__ == "__main__":
    check_images_schema()
