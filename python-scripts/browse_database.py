import sqlite3
import pandas as pd
from pathlib import Path

def browse_database():
    """Simple database browser using Python."""
    db_path = "library/index.sqlite"
    
    if not Path(db_path).exists():
        print(f"❌ Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    
    print("🔍 DATABASE BROWSER")
    print("=" * 50)
    print(f"📁 Database: {db_path}")
    
    while True:
        print("\n" + "="*50)
        print("📋 AVAILABLE TABLES:")
        
        # Get tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        for i, table in enumerate(tables, 1):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {i}. {table} ({count:,} rows)")
        
        print(f"  {len(tables)+1}. Custom SQL Query")
        print(f"  {len(tables)+2}. Exit")
        
        try:
            choice = input(f"\n🎯 Select option (1-{len(tables)+2}): ").strip()
            
            if choice == str(len(tables)+2):
                print("👋 Goodbye!")
                break
            elif choice == str(len(tables)+1):
                # Custom SQL query
                sql = input("🔍 Enter SQL query: ").strip()
                if sql.lower().startswith('select'):
                    try:
                        df = pd.read_sql_query(sql, conn)
                        print(f"\n📊 Results ({len(df)} rows):")
                        print(df.to_string(index=False, max_rows=20))
                        
                        if len(df) > 20:
                            print(f"\n... showing first 20 of {len(df)} rows")
                    except Exception as e:
                        print(f"❌ Error: {e}")
                else:
                    print("❌ Only SELECT queries are allowed for safety")
            elif choice.isdigit() and 1 <= int(choice) <= len(tables):
                # Show table data
                table_name = tables[int(choice)-1]
                show_table_data(conn, table_name)
            else:
                print("❌ Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    conn.close()

def show_table_data(conn, table_name):
    """Show data for a specific table."""
    print(f"\n📊 TABLE: {table_name}")
    print("=" * 60)
    
    # Get table info
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    print(f"📋 Columns: {', '.join(column_names)}")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    print(f"📊 Total rows: {row_count:,}")
    
    if row_count == 0:
        print("📝 No data in table")
        return
    
    # Show sample data
    print(f"\n📝 Sample data (first 10 rows):")
    print("-" * 60)
    
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 10", conn)
        print(df.to_string(index=False))
        
        if row_count > 10:
            print(f"\n... showing first 10 of {row_count:,} rows")
            
            # Show more options
            show_more = input("\n🔍 Show more rows? (y/n): ").lower().strip()
            if show_more == 'y':
                try:
                    limit = int(input("📊 How many rows? (max 100): "))
                    limit = min(limit, 100)
                    df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {limit}", conn)
                    print(f"\n📝 Showing {len(df)} rows:")
                    print(df.to_string(index=False))
                except ValueError:
                    print("❌ Invalid number")
                    
    except Exception as e:
        print(f"❌ Error reading table: {e}")

if __name__ == "__main__":
    browse_database()
