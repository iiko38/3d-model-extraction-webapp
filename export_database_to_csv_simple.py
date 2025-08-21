import sqlite3
import pandas as pd
from pathlib import Path

def export_database_to_csv():
    """Export all tables from the SQLite database to CSV files."""
    
    # Database path
    db_path = "library/index.sqlite"
    
    # Create exports directory
    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    # Get list of all tables
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"Found {len(tables)} tables in database:")
    
    exported_files = []
    
    for table in tables:
        table_name = table[0]
        print(f"Exporting table: {table_name}")
        
        # Read table into pandas DataFrame
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        
        # Export to CSV
        csv_path = exports_dir / f"{table_name}.csv"
        df.to_csv(csv_path, index=False)
        
        print(f"  -> Exported {len(df)} rows to {csv_path}")
        exported_files.append(str(csv_path))
        
        # Show table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"  -> Columns: {[col[1] for col in columns]}")
    
    # Create a simple comprehensive export
    print("\nCreating comprehensive export...")
    
    try:
        # Get products with file counts - using only columns that exist
        comprehensive_sql = """
        SELECT 
            p.product_uid,
            p.brand,
            p.name,
            p.slug,
            p.category,
            p.url,
            p.created_at,
            p.updated_at,
            COUNT(f.file_id) as total_files,
            SUM(CASE WHEN f.file_type = 'revit' THEN 1 ELSE 0 END) as revit_files,
            SUM(CASE WHEN f.file_type = 'sketchup' THEN 1 ELSE 0 END) as sketchup_files,
            SUM(CASE WHEN f.file_type = 'autocad_3d' THEN 1 ELSE 0 END) as autocad_3d_files,
            SUM(CASE WHEN f.file_type = 'autocad_2d' THEN 1 ELSE 0 END) as autocad_2d_files,
            SUM(CASE WHEN f.file_type = 'obj' THEN 1 ELSE 0 END) as obj_files,
            SUM(CASE WHEN f.file_type = 'fbx' THEN 1 ELSE 0 END) as fbx_files,
            SUM(CASE WHEN f.file_type = '3ds' THEN 1 ELSE 0 END) as three_ds_files,
            SUM(CASE WHEN f.file_type = 'dwg' THEN 1 ELSE 0 END) as dwg_files,
            SUM(CASE WHEN f.file_type = 'dxf' THEN 1 ELSE 0 END) as dxf_files,
            SUM(CASE WHEN f.file_type = 'stl' THEN 1 ELSE 0 END) as stl_files,
            SUM(CASE WHEN f.file_type = 'other' THEN 1 ELSE 0 END) as other_files
        FROM products p
        LEFT JOIN files f ON p.product_uid = f.product_uid
        GROUP BY p.product_uid
        ORDER BY p.brand, p.name
        """
        
        comprehensive_df = pd.read_sql_query(comprehensive_sql, conn)
        comprehensive_path = exports_dir / "comprehensive_products.csv"
        comprehensive_df.to_csv(comprehensive_path, index=False)
        exported_files.append(str(comprehensive_path))
        print(f"  -> Exported comprehensive view to {comprehensive_path}")
        
    except Exception as e:
        print(f"  -> Error creating comprehensive export: {e}")
    
    # Create files with product info
    try:
        files_sql = """
        SELECT 
            f.file_id,
            f.product_uid,
            p.brand,
            p.name as product_name,
            f.file_type,
            f.file_name,
            f.file_path,
            f.file_size,
            f.download_url,
            f.created_at
        FROM files f
        JOIN products p ON f.product_uid = p.product_uid
        ORDER BY p.brand, p.name, f.file_type
        """
        
        files_df = pd.read_sql_query(files_sql, conn)
        files_path = exports_dir / "files_with_products.csv"
        files_df.to_csv(files_path, index=False)
        exported_files.append(str(files_path))
        print(f"  -> Exported files with product info to {files_path}")
        
    except Exception as e:
        print(f"  -> Error creating files export: {e}")
    
    # Create images export if images table exists
    try:
        images_sql = """
        SELECT 
            i.image_id,
            i.product_uid,
            p.brand,
            p.name as product_name,
            i.image_url,
            i.local_path,
            i.image_type,
            i.file_size,
            i.width,
            i.height,
            i.created_at
        FROM images i
        JOIN products p ON i.product_uid = p.product_uid
        ORDER BY p.brand, p.name, i.image_type
        """
        
        images_df = pd.read_sql_query(images_sql, conn)
        images_path = exports_dir / "images_with_products.csv"
        images_df.to_csv(images_path, index=False)
        exported_files.append(str(images_path))
        print(f"  -> Exported images with product info to {images_path}")
    except Exception as e:
        print(f"  -> Error creating images export: {e}")
    
    conn.close()
    
    print(f"\n✅ Export complete! {len(exported_files)} files created in 'exports' directory:")
    for file_path in exported_files:
        print(f"  - {file_path}")
    
    return exported_files

if __name__ == "__main__":
    export_database_to_csv()
