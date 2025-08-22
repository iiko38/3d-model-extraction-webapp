#!/usr/bin/env python3
"""
Check which hashes are reused across products
"""

import sqlite3
import sys

def main():
    DB = sys.argv[1] if len(sys.argv) > 1 else "library/index.sqlite"
    
    con = sqlite3.connect(DB)
    cur = con.cursor()
    
    print("=== REUSED HASHES ANALYSIS ===")
    
    # Find hashes used by multiple products
    cur.execute("""
        SELECT sha256, COUNT(DISTINCT product_uid) AS products_using 
        FROM files 
        GROUP BY sha256 
        HAVING products_using > 1 
        ORDER BY products_using DESC, sha256 
        LIMIT 20;
    """)
    
    reused_hashes = cur.fetchall()
    
    if reused_hashes:
        print(f"Found {len(reused_hashes)} hashes used by multiple products:")
        for sha256, count in reused_hashes:
            print(f"  {sha256[:16]}... used by {count} products")
        
        # Show details for the most reused hash
        if reused_hashes:
            most_reused_hash = reused_hashes[0][0]
            print(f"\nDetails for most reused hash ({most_reused_hash[:16]}...):")
            cur.execute("""
                SELECT p.brand, p.name, f.stored_path
                FROM files f
                JOIN products p ON f.product_uid = p.product_uid
                WHERE f.sha256 = ?
                ORDER BY p.brand, p.name
            """, (most_reused_hash,))
            
            for brand, name, path in cur.fetchall():
                print(f"  {brand}: {name} - {path}")
    else:
        print("No hashes are reused across products")
    
    # Total stats
    cur.execute("SELECT COUNT(DISTINCT sha256) FROM files")
    unique_hashes = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM files")
    total_files = cur.fetchone()[0]
    
    print(f"\n=== SUMMARY ===")
    print(f"Total files: {total_files}")
    print(f"Unique hashes: {unique_hashes}")
    print(f"Reused hashes: {len(reused_hashes)}")
    print(f"Reuse rate: {len(reused_hashes) / unique_hashes * 100:.1f}% of hashes are reused")
    
    con.close()

if __name__ == "__main__":
    main()


