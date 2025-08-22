import sqlite3
import pandas as pd
from pathlib import Path

def update_exports_with_thumbnail():
    """Update CSV exports to include the new thumbnail_url column."""
    
    # Database path
    db_path = "library/index.sqlite"
    
    # Create exports directory
    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    print("Updating exports with thumbnail_url column...")
    
    # Update products table export
    try:
        products_df = pd.read_sql_query("SELECT * FROM products", conn)
        products_path = exports_dir / "products.csv"
        products_df.to_csv(products_path, index=False)
        print(f"  -> Updated products.csv with thumbnail_url column")
        
    except Exception as e:
        print(f"  -> Error updating products export: {e}")
    
    # Update comprehensive products export
    try:
        comprehensive_sql = """
        SELECT 
            p.product_uid,
            p.brand,
            p.name,
            p.slug,
            p.category,
            p.product_card_image_path,
            p.thumbnail_url,
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
        print(f"  -> Updated comprehensive_products.csv with thumbnail_url column")
        
    except Exception as e:
        print(f"  -> Error updating comprehensive export: {e}")
    
    # Update files with products export
    try:
        files_sql = """
        SELECT 
            f.product_uid,
            f.sha256,
            f.variant,
            f.file_type,
            f.ext,
            f.stored_path,
            f.size_bytes,
            f.source_url,
            f.source_page,
            f.matched_image_path,
            p.brand,
            p.name as product_name,
            p.slug,
            p.category,
            p.product_card_image_path,
            p.thumbnail_url
        FROM files f
        JOIN products p ON f.product_uid = p.product_uid
        ORDER BY p.brand, p.name, f.file_type
        """
        
        files_df = pd.read_sql_query(files_sql, conn)
        files_path = exports_dir / "files_with_products.csv"
        files_df.to_csv(files_path, index=False)
        print(f"  -> Updated files_with_products.csv with thumbnail_url column")
        
    except Exception as e:
        print(f"  -> Error updating files export: {e}")
    
    # Update images with products export
    try:
        images_sql = """
        SELECT 
            i.product_uid,
            i.variant,
            i.image_url,
            i.provider,
            i.score,
            i.rationale,
            i.status,
            i.width,
            i.height,
            i.content_hash,
            i.local_path,
            i.created_at,
            i.updated_at,
            i.is_primary,
            i.image_score,
            p.brand,
            p.name as product_name,
            p.slug,
            p.category,
            p.product_card_image_path,
            p.thumbnail_url
        FROM images i
        JOIN products p ON i.product_uid = p.product_uid
        ORDER BY p.brand, p.name, i.is_primary DESC, i.score DESC
        """
        
        images_df = pd.read_sql_query(images_sql, conn)
        images_path = exports_dir / "images_with_products.csv"
        images_df.to_csv(images_path, index=False)
        print(f"  -> Updated images_with_products.csv with thumbnail_url column")
        
    except Exception as e:
        print(f"  -> Error updating images export: {e}")
    
    conn.close()
    
    print(f"\n✅ All exports updated with thumbnail_url column!")
    print(f"Updated files in 'exports' directory:")

if __name__ == "__main__":
    update_exports_with_thumbnail()
