import sqlite3
import pandas as pd
from pathlib import Path

def get_table_schema(conn, table_name):
    """Get the actual schema of a table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return [col[1] for col in columns]

def create_final_export():
    """Create final CSV exports based on actual database schema."""
    
    # Database path
    db_path = "library/index.sqlite"
    
    # Create exports directory
    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    print("Creating final comprehensive exports...")
    
    # Get actual schemas
    products_columns = get_table_schema(conn, 'products')
    files_columns = get_table_schema(conn, 'files')
    images_columns = get_table_schema(conn, 'images')
    
    print(f"Products columns: {products_columns}")
    print(f"Files columns: {files_columns}")
    print(f"Images columns: {images_columns}")
    
    # Create products with file counts using only existing columns
    try:
        # Build dynamic SQL based on actual columns
        product_cols = []
        for col in products_columns:
            if col in ['product_uid', 'brand', 'name', 'slug', 'category']:
                product_cols.append(f"p.{col}")
        
        comprehensive_sql = f"""
        SELECT 
            {', '.join(product_cols)},
            COUNT(f.product_uid) as total_files,
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
        print(f"  -> Exported comprehensive products view to {comprehensive_path}")
        
    except Exception as e:
        print(f"  -> Error creating comprehensive export: {e}")
    
    # Create files with product info using only existing columns
    try:
        # Build dynamic SQL for files
        file_cols = []
        for col in files_columns:
            if col in ['product_uid', 'sha256', 'variant', 'file_type', 'ext', 'stored_path', 'size_bytes', 'source_url', 'source_page', 'matched_image_path']:
                file_cols.append(f"f.{col}")
        
        product_cols_for_files = []
        for col in products_columns:
            if col in ['brand', 'name', 'slug', 'category']:
                product_cols_for_files.append(f"p.{col} as product_{col}")
        
        files_sql = f"""
        SELECT 
            {', '.join(file_cols)},
            {', '.join(product_cols_for_files)}
        FROM files f
        JOIN products p ON f.product_uid = p.product_uid
        ORDER BY p.brand, p.name, f.file_type
        """
        
        files_df = pd.read_sql_query(files_sql, conn)
        files_path = exports_dir / "files_with_products.csv"
        files_df.to_csv(files_path, index=False)
        print(f"  -> Exported files with product info to {files_path}")
        
    except Exception as e:
        print(f"  -> Error creating files export: {e}")
    
    # Create brand summary
    try:
        brand_summary_sql = """
        SELECT 
            p.brand,
            COUNT(DISTINCT p.product_uid) as product_count,
            COUNT(f.product_uid) as total_files,
            SUM(CASE WHEN f.file_type = 'revit' THEN 1 ELSE 0 END) as revit_files,
            SUM(CASE WHEN f.file_type = 'sketchup' THEN 1 ELSE 0 END) as sketchup_files,
            SUM(CASE WHEN f.file_type = 'autocad_3d' THEN 1 ELSE 0 END) as autocad_3d_files,
            COUNT(DISTINCT i.product_uid) as products_with_images,
            COUNT(i.product_uid) as total_images
        FROM products p
        LEFT JOIN files f ON p.product_uid = f.product_uid
        LEFT JOIN images i ON p.product_uid = i.product_uid
        GROUP BY p.brand
        ORDER BY product_count DESC
        """
        
        brand_df = pd.read_sql_query(brand_summary_sql, conn)
        brand_path = exports_dir / "brand_summary.csv"
        brand_df.to_csv(brand_path, index=False)
        print(f"  -> Exported brand summary to {brand_path}")
        
    except Exception as e:
        print(f"  -> Error creating brand summary: {e}")
    
    # Create file type summary
    try:
        file_type_summary_sql = """
        SELECT 
            file_type,
            COUNT(*) as count,
            COUNT(DISTINCT product_uid) as unique_products,
            ROUND(AVG(size_bytes) / 1024 / 1024, 2) as avg_size_mb
        FROM files
        GROUP BY file_type
        ORDER BY count DESC
        """
        
        file_type_df = pd.read_sql_query(file_type_summary_sql, conn)
        file_type_path = exports_dir / "file_type_summary.csv"
        file_type_df.to_csv(file_type_path, index=False)
        print(f"  -> Exported file type summary to {file_type_path}")
        
    except Exception as e:
        print(f"  -> Error creating file type summary: {e}")
    
    conn.close()
    
    print(f"\n✅ Final export complete!")
    print(f"All CSV files available in 'exports' directory for download:")

if __name__ == "__main__":
    create_final_export()
