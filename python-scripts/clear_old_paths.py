#!/usr/bin/env python3
import sqlite3

def clear_old_paths():
    """Clear old local paths from the database."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== CLEARING OLD PATHS ===")
    
    # Clear old API image paths
    cursor.execute("UPDATE images SET local_path = NULL WHERE provider = 'herman_miller_api'")
    cleared = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"Cleared {cleared} old API image paths")

if __name__ == "__main__":
    clear_old_paths()
