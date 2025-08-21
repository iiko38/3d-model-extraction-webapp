import sqlite3
import pandas as pd
from pathlib import Path

def examine_database_structure():
    """Comprehensive examination of the database structure."""
    db_path = "library/index.sqlite"
    
    if not Path(db_path).exists():
        print(f"❌ Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 COMPREHENSIVE DATABASE STRUCTURE EXAMINATION")
    print("=" * 80)
    
    # 1. Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\n📋 DATABASE TABLES ({len(tables)} total):")
    print("-" * 40)
    for table in tables:
        print(f"  • {table}")
    
    # 2. Examine each table in detail
    for table_name in tables:
        print(f"\n{'='*60}")
        print(f"📊 TABLE: {table_name}")
        print(f"{'='*60}")
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print(f"\n📋 COLUMNS ({len(columns)} total):")
        print("-" * 30)
        print(f"{'ID':<3} {'Name':<25} {'Type':<15} {'NOT NULL':<8} {'Default':<10} {'PK':<2}")
        print("-" * 70)
        
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, primary_key = col
            not_null_str = "YES" if not_null else "NO"
            pk_str = "PK" if primary_key else ""
            default_str = str(default_val) if default_val else ""
            print(f"{col_id:<3} {col_name:<25} {col_type:<15} {not_null_str:<8} {default_str:<10} {pk_str:<2}")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        print(f"\n📊 ROW COUNT: {row_count:,}")
        
        # Get sample data
        if row_count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            sample_rows = cursor.fetchall()
            
            print(f"\n📝 SAMPLE DATA (first 3 rows):")
            print("-" * 30)
            
            # Get column names for headers
            column_names = [col[1] for col in columns]
            
            # Print headers
            header_str = " | ".join([f"{name:<20}" for name in column_names[:5]])  # Limit to first 5 columns
            print(header_str)
            print("-" * len(header_str))
            
            # Print sample data
            for row in sample_rows:
                # Truncate long values and limit to first 5 columns
                row_str = " | ".join([f"{str(val)[:18]:<20}" for val in row[:5]])
                print(row_str)
            
            if len(column_names) > 5:
                print(f"... and {len(column_names) - 5} more columns")
        
        # Get unique values for key columns (if reasonable)
        print(f"\n🔍 COLUMN ANALYSIS:")
        print("-" * 20)
        
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            
            # Skip analysis for very large tables or binary data
            if row_count > 10000:
                print(f"  {col_name}: {col_type} (skipping analysis - large table)")
                continue
            
            try:
                # Get unique values count
                cursor.execute(f"SELECT COUNT(DISTINCT {col_name}) FROM {table_name}")
                unique_count = cursor.fetchone()[0]
                
                # Get null count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL")
                null_count = cursor.fetchone()[0]
                
                print(f"  {col_name}: {col_type}")
                print(f"    - Unique values: {unique_count:,}")
                print(f"    - Null values: {null_count:,}")
                
                # Show sample unique values for reasonable counts
                if unique_count <= 20 and unique_count > 0:
                    cursor.execute(f"SELECT DISTINCT {col_name} FROM {table_name} WHERE {col_name} IS NOT NULL LIMIT 10")
                    unique_values = [str(row[0]) for row in cursor.fetchall()]
                    print(f"    - Sample values: {', '.join(unique_values)}")
                
                print()
                
            except sqlite3.OperationalError as e:
                print(f"  {col_name}: {col_type} (error analyzing: {e})")
    
    # 3. Foreign key relationships
    print(f"\n{'='*60}")
    print("🔗 FOREIGN KEY RELATIONSHIPS")
    print(f"{'='*60}")
    
    cursor.execute("PRAGMA foreign_key_list")
    foreign_keys = cursor.fetchall()
    
    if foreign_keys:
        print(f"\n📋 FOREIGN KEY CONSTRAINTS ({len(foreign_keys)} total):")
        print("-" * 50)
        for fk in foreign_keys:
            print(f"  • {fk[2]} -> {fk[3]}.{fk[4]}")
    else:
        print("\n📋 No explicit foreign key constraints found")
    
    # 4. Indexes
    print(f"\n{'='*60}")
    print("📇 INDEXES")
    print(f"{'='*60}")
    
    for table_name in tables:
        cursor.execute(f"PRAGMA index_list({table_name})")
        indexes = cursor.fetchall()
        
        if indexes:
            print(f"\n📋 {table_name} indexes:")
            for idx in indexes:
                idx_name = idx[1]
                unique = "UNIQUE" if idx[2] else "NON-UNIQUE"
                print(f"  • {idx_name} ({unique})")
                
                # Get index columns
                cursor.execute(f"PRAGMA index_info({idx_name})")
                idx_columns = cursor.fetchall()
                column_names = [col[2] for col in idx_columns]
                print(f"    Columns: {', '.join(column_names)}")
        else:
            print(f"\n📋 {table_name}: No indexes")
    
    # 5. Database statistics
    print(f"\n{'='*60}")
    print("📊 DATABASE STATISTICS")
    print(f"{'='*60}")
    
    total_rows = 0
    total_size = 0
    
    for table_name in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        total_rows += row_count
        
        # Estimate table size (rough calculation)
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        estimated_row_size = sum([
            8 if col[2] in ('INTEGER', 'REAL') else 50  # Rough estimate
            for col in columns
        ])
        table_size = row_count * estimated_row_size
        total_size += table_size
        
        print(f"  {table_name}: {row_count:,} rows (~{table_size:,} bytes)")
    
    print(f"\n📊 TOTAL: {total_rows:,} rows across all tables")
    print(f"📊 ESTIMATED SIZE: ~{total_size:,} bytes (~{total_size/1024/1024:.1f} MB)")
    
    # 6. Data quality checks
    print(f"\n{'='*60}")
    print("🔍 DATA QUALITY CHECKS")
    print(f"{'='*60}")
    
    # Check for orphaned records
    if 'products' in tables and 'files' in tables:
        cursor.execute("""
            SELECT COUNT(*) FROM files f 
            LEFT JOIN products p ON f.product_uid = p.product_uid 
            WHERE p.product_uid IS NULL
        """)
        orphaned_files = cursor.fetchone()[0]
        print(f"📋 Orphaned files (no matching product): {orphaned_files:,}")
    
    if 'products' in tables and 'images' in tables:
        cursor.execute("""
            SELECT COUNT(*) FROM images i 
            LEFT JOIN products p ON i.product_uid = p.product_uid 
            WHERE p.product_uid IS NULL
        """)
        orphaned_images = cursor.fetchone()[0]
        print(f"📋 Orphaned images (no matching product): {orphaned_images:,}")
    
    # Check for missing URLs
    if 'files' in tables:
        cursor.execute("SELECT COUNT(*) FROM files WHERE thumbnail_url IS NULL OR thumbnail_url = ''")
        missing_thumbnails = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM files WHERE product_url IS NULL OR product_url = ''")
        missing_product_urls = cursor.fetchone()[0]
        print(f"📋 Files missing thumbnail URLs: {missing_thumbnails:,}")
        print(f"📋 Files missing product URLs: {missing_product_urls:,}")
    
    conn.close()
    
    print(f"\n✅ Database examination complete!")
    print(f"📁 Database file: {db_path}")

if __name__ == "__main__":
    examine_database_structure()
