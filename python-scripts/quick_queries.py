import sqlite3
import pandas as pd
from pathlib import Path

def quick_queries():
    """Run common database queries."""
    db_path = "library/index.sqlite"
    
    if not Path(db_path).exists():
        print(f"❌ Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    
    print("🔍 QUICK DATABASE QUERIES")
    print("=" * 50)
    
    queries = {
        "1": {
            "name": "Files by Brand",
            "sql": """
            SELECT p.brand, COUNT(*) as file_count
            FROM files f
            JOIN products p ON f.product_uid = p.product_uid
            GROUP BY p.brand
            ORDER BY file_count DESC
            """
        },
        "2": {
            "name": "Files by Type",
            "sql": """
            SELECT file_type, COUNT(*) as count
            FROM files
            GROUP BY file_type
            ORDER BY count DESC
            """
        },
        "3": {
            "name": "Products with Most Files",
            "sql": """
            SELECT p.name, p.brand, COUNT(f.sha256) as file_count
            FROM products p
            LEFT JOIN files f ON p.product_uid = f.product_uid
            GROUP BY p.product_uid
            ORDER BY file_count DESC
            LIMIT 10
            """
        },
        "4": {
            "name": "Files Missing URLs",
            "sql": """
            SELECT f.variant, f.file_type, p.name, p.brand
            FROM files f
            JOIN products p ON f.product_uid = p.product_uid
            WHERE f.thumbnail_url IS NULL OR f.thumbnail_url = ''
            ORDER BY p.brand, p.name
            """
        },
        "5": {
            "name": "Recent Images",
            "sql": """
            SELECT i.product_uid, i.image_url, i.provider, i.score, i.status
            FROM images i
            ORDER BY i.created_at DESC
            LIMIT 10
            """
        },
        "6": {
            "name": "Database Summary",
            "sql": """
            SELECT 
                'products' as table_name, COUNT(*) as count FROM products
            UNION ALL
            SELECT 'files', COUNT(*) FROM files
            UNION ALL
            SELECT 'images', COUNT(*) FROM images
            """
        }
    }
    
    while True:
        print("\n" + "="*50)
        print("📋 AVAILABLE QUERIES:")
        for key, query in queries.items():
            print(f"  {key}. {query['name']}")
        print("  7. Custom Query")
        print("  8. Exit")
        
        choice = input(f"\n🎯 Select query (1-8): ").strip()
        
        if choice == "8":
            print("👋 Goodbye!")
            break
        elif choice == "7":
            sql = input("🔍 Enter custom SQL: ").strip()
            if not sql.lower().startswith('select'):
                print("❌ Only SELECT queries allowed for safety")
                continue
        elif choice in queries:
            sql = queries[choice]["sql"]
            print(f"\n📊 Running: {queries[choice]['name']}")
        else:
            print("❌ Invalid choice")
            continue
        
        try:
            df = pd.read_sql_query(sql, conn)
            print(f"\n📊 Results ({len(df)} rows):")
            print(df.to_string(index=False, max_rows=20))
            
            if len(df) > 20:
                print(f"\n... showing first 20 of {len(df)} rows")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    conn.close()

if __name__ == "__main__":
    quick_queries()
