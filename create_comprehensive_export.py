import sqlite3
import pandas as pd
from pathlib import Path

def create_comprehensive_export():
    """Create comprehensive CSV exports based on actual database schema."""
    
    # Database path
    db_path = "library/index.sqlite"
    
    # Create exports directory
    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    print("Creating comprehensive exports...")
    
    # Create products with file counts
    try:
        comprehensive_sql = """
        SELECT 
            p.product_uid,
            p.brand,
            p.name,
            p.slug,
            p.category,
            p.created_at,
            p.updated_at,
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
    
    # Create files with product info
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
            p.created_at as product_created,
            f.created_at as file_created
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
    
    # Create images with product info
    try:
        images_sql = """
        SELECT 
            i.product_uid,
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
            p.category
        FROM images i
        JOIN products p ON i.product_uid = p.product_uid
        ORDER BY p.brand, p.name, i.is_primary DESC, i.score DESC
        """
        
        images_df = pd.read_sql_query(images_sql, conn)
        images_path = exports_dir / "images_with_products.csv"
        images_df.to_csv(images_path, index=False)
        print(f"  -> Exported images with product info to {images_path}")
        
    except Exception as e:
        print(f"  -> Error creating images export: {e}")
    
    # Create summary statistics
    try:
        summary_sql = """
        SELECT 
            'Total Products' as metric,
            COUNT(DISTINCT p.product_uid) as value
        FROM products p
        UNION ALL
        SELECT 
            'Total Files' as metric,
            COUNT(*) as value
        FROM files
        UNION ALL
        SELECT 
            'Total Images' as metric,
            COUNT(*) as value
        FROM images
        UNION ALL
        SELECT 
            'Products with Files' as metric,
            COUNT(DISTINCT product_uid) as value
        FROM files
        UNION ALL
        SELECT 
            'Products with Images' as metric,
            COUNT(DISTINCT product_uid) as value
        FROM images
        UNION ALL
        SELECT 
            'Revit Files' as metric,
            COUNT(*) as value
        FROM files WHERE file_type = 'revit'
        UNION ALL
        SELECT 
            'SketchUp Files' as metric,
            COUNT(*) as value
        FROM files WHERE file_type = 'sketchup'
        UNION ALL
        SELECT 
            'AutoCAD 3D Files' as metric,
            COUNT(*) as value
        FROM files WHERE file_type = 'autocad_3d'
        UNION ALL
        SELECT 
            'Primary Images' as metric,
            COUNT(*) as value
        FROM images WHERE is_primary = 1
        """
        
        summary_df = pd.read_sql_query(summary_sql, conn)
        summary_path = exports_dir / "summary_statistics.csv"
        summary_df.to_csv(summary_path, index=False)
        print(f"  -> Exported summary statistics to {summary_path}")
        
    except Exception as e:
        print(f"  -> Error creating summary: {e}")
    
    conn.close()
    
    print(f"\n✅ Comprehensive export complete!")
    print(f"Files available in 'exports' directory:")
    print(f"  - products.csv (raw products table)")
    print(f"  - files.csv (raw files table)")
    print(f"  - images.csv (raw images table)")
    print(f"  - comprehensive_products.csv (products with file counts)")
    print(f"  - files_with_products.csv (files with product details)")
    print(f"  - images_with_products.csv (images with product details)")
    print(f"  - summary_statistics.csv (overall statistics)")

if __name__ == "__main__":
    create_comprehensive_export()
