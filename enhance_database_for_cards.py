#!/usr/bin/env python3
import sqlite3
from pathlib import Path

def enhance_database_for_cards():
    """Enhance database schema for product cards."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== ENHANCING DATABASE FOR PRODUCT CARDS ===")
    
    # 1. Add is_primary column to images table
    try:
        cursor.execute("ALTER TABLE images ADD COLUMN is_primary BOOLEAN DEFAULT 0")
        print("✓ Added is_primary column to images table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ is_primary column already exists")
        else:
            print(f"✗ Error adding is_primary column: {e}")
    
    # 2. Add product_card_image_path to products table
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN product_card_image_path TEXT")
        print("✓ Added product_card_image_path column to products table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ product_card_image_path column already exists")
        else:
            print(f"✗ Error adding product_card_image_path column: {e}")
    
    # 3. Add image_score column to images table for better selection
    try:
        cursor.execute("ALTER TABLE images ADD COLUMN image_score REAL DEFAULT 0.0")
        print("✓ Added image_score column to images table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ image_score column already exists")
        else:
            print(f"✗ Error adding image_score column: {e}")
    
    conn.commit()
    conn.close()
    
    print("✓ Database enhancement complete")

if __name__ == "__main__":
    enhance_database_for_cards()
