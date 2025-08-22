import sqlite3
import pandas as pd
from pathlib import Path

def regenerate_exports_with_files_urls():
    """Regenerate all CSV exports to include the URL columns in the files table."""
    
    db_path = "library/index.sqlite"
    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    
    print("🔄 Regenerating CSV Exports with Files URL Columns")
    print("=" * 60)
    
    # 1. Basic tables with URL columns
    print("\n📋 Exporting basic tables...")
    
    # Products table (keeping existing URL columns)
    products_sql = """
    SELECT product_uid, brand, name, slug, category, 
           product_card_image_path, thumbnail_url, product_url
    FROM products
    ORDER BY brand, name
    """
    
    df_products = pd.read_sql_query(products_sql, conn)
    df_products.to_csv(exports_dir / "products_with_urls.csv", index=False)
    print(f"  ✅ products_with_urls.csv ({len(df_products)} rows)")
    
    # Files table with URL columns
    files_sql = """
    SELECT product_uid, sha256, variant, file_type, ext, 
           stored_path, size_bytes, source_url, source_page, matched_image_path,
           thumbnail_url, product_url
    FROM files
    ORDER BY product_uid, file_type
    """
    
    df_files = pd.read_sql_query(files_sql, conn)
    df_files.to_csv(exports_dir / "files_with_urls.csv", index=False)
    print(f"  ✅ files_with_urls.csv ({len(df_files)} rows)")
    
    # Images table
    images_sql = """
    SELECT product_uid, variant, image_url, provider, score, rationale, 
           status, width, height, content_hash, local_path, 
           created_at, updated_at, is_primary, image_score
    FROM images
    ORDER BY product_uid, score DESC
    """
    
    df_images = pd.read_sql_query(images_sql, conn)
    df_images.to_csv(exports_dir / "images.csv", index=False)
    print(f"  ✅ images.csv ({len(df_images)} rows)")
    
    # 2. Comprehensive joined exports
    print("\n📊 Exporting comprehensive joined views...")
    
    # Comprehensive products with URLs
    comprehensive_sql = """
    SELECT
        p.product_uid, p.brand, p.name, p.slug, p.category,
        p.product_card_image_path, p.thumbnail_url, p.product_url,
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
    
    df_comprehensive = pd.read_sql_query(comprehensive_sql, conn)
    df_comprehensive.to_csv(exports_dir / "comprehensive_products_with_urls.csv", index=False)
    print(f"  ✅ comprehensive_products_with_urls.csv ({len(df_comprehensive)} rows)")
    
    # Files with product info and URLs (MAIN EXPORT)
    files_with_products_sql = """
    SELECT
        f.product_uid, f.sha256, f.variant, f.file_type, f.ext,
        f.stored_path, f.size_bytes, f.source_url, f.source_page, f.matched_image_path,
        f.thumbnail_url, f.product_url,
        p.brand, p.name, p.slug, p.category, p.product_card_image_path
    FROM files f
    LEFT JOIN products p ON f.product_uid = p.product_uid
    ORDER BY p.brand, p.name, f.file_type
    """
    
    df_files_with_products = pd.read_sql_query(files_with_products_sql, conn)
    df_files_with_products.to_csv(exports_dir / "files_with_products_and_urls.csv", index=False)
    print(f"  ✅ files_with_products_and_urls.csv ({len(df_files_with_products)} rows)")
    
    # Images with product info and URLs
    images_with_products_sql = """
    SELECT
        i.product_uid, i.variant, i.image_url, i.provider, i.score, i.rationale,
        i.status, i.width, i.height, i.content_hash, i.local_path,
        i.created_at, i.updated_at, i.is_primary, i.image_score,
        p.brand, p.name, p.slug, p.category, p.thumbnail_url, p.product_url
    FROM images i
    LEFT JOIN products p ON i.product_uid = p.product_uid
    ORDER BY p.brand, p.name, i.score DESC
    """
    
    df_images_with_products = pd.read_sql_query(images_with_products_sql, conn)
    df_images_with_products.to_csv(exports_dir / "images_with_products_and_urls.csv", index=False)
    print(f"  ✅ images_with_products_and_urls.csv ({len(df_images_with_products)} rows)")
    
    # 3. Summary statistics
    print("\n📈 Exporting summary statistics...")
    
    # Summary statistics with files URL counts
    summary_sql = """
    SELECT
        'Total Products' as metric, COUNT(*) as value
        FROM products
    UNION ALL
    SELECT
        'Products with Thumbnail URLs' as metric, COUNT(*) as value
        FROM products WHERE thumbnail_url IS NOT NULL AND thumbnail_url != ''
    UNION ALL
    SELECT
        'Products with Product URLs' as metric, COUNT(*) as value
        FROM products WHERE product_url IS NOT NULL AND product_url != ''
    UNION ALL
    SELECT
        'Total Files' as metric, COUNT(*) as value
        FROM files
    UNION ALL
    SELECT
        'Files with Thumbnail URLs' as metric, COUNT(*) as value
        FROM files WHERE thumbnail_url IS NOT NULL AND thumbnail_url != ''
    UNION ALL
    SELECT
        'Files with Product URLs' as metric, COUNT(*) as value
        FROM files WHERE product_url IS NOT NULL AND product_url != ''
    UNION ALL
    SELECT
        'Total Images' as metric, COUNT(*) as value
        FROM images
    UNION ALL
    SELECT
        'Unique Variants' as metric, COUNT(DISTINCT variant) as value
        FROM files WHERE variant IS NOT NULL AND variant != ''
    """
    
    df_summary = pd.read_sql_query(summary_sql, conn)
    df_summary.to_csv(exports_dir / "summary_statistics_with_files_urls.csv", index=False)
    print(f"  ✅ summary_statistics_with_files_urls.csv ({len(df_summary)} rows)")
    
    # Brand summary with files URL counts
    brand_summary_sql = """
    SELECT
        p.brand,
        COUNT(DISTINCT p.product_uid) as total_products,
        SUM(CASE WHEN p.thumbnail_url IS NOT NULL AND p.thumbnail_url != '' THEN 1 ELSE 0 END) as products_with_thumbnails,
        SUM(CASE WHEN p.product_url IS NOT NULL AND p.product_url != '' THEN 1 ELSE 0 END) as products_with_urls,
        COUNT(f.sha256) as total_files,
        SUM(CASE WHEN f.thumbnail_url IS NOT NULL AND f.thumbnail_url != '' THEN 1 ELSE 0 END) as files_with_thumbnails,
        SUM(CASE WHEN f.product_url IS NOT NULL AND f.product_url != '' THEN 1 ELSE 0 END) as files_with_urls
    FROM products p
    LEFT JOIN files f ON p.product_uid = f.product_uid
    GROUP BY p.brand
    ORDER BY total_products DESC
    """
    
    df_brand_summary = pd.read_sql_query(brand_summary_sql, conn)
    df_brand_summary.to_csv(exports_dir / "brand_summary_with_files_urls.csv", index=False)
    print(f"  ✅ brand_summary_with_files_urls.csv ({len(df_brand_summary)} rows)")
    
    # File type summary with URL counts
    file_type_summary_sql = """
    SELECT
        file_type,
        COUNT(*) as total_files,
        COUNT(DISTINCT product_uid) as unique_products,
        SUM(CASE WHEN thumbnail_url IS NOT NULL AND thumbnail_url != '' THEN 1 ELSE 0 END) as files_with_thumbnails,
        SUM(CASE WHEN product_url IS NOT NULL AND product_url != '' THEN 1 ELSE 0 END) as files_with_urls
    FROM files
    GROUP BY file_type
    ORDER BY total_files DESC
    """
    
    df_file_type_summary = pd.read_sql_query(file_type_summary_sql, conn)
    df_file_type_summary.to_csv(exports_dir / "file_type_summary_with_urls.csv", index=False)
    print(f"  ✅ file_type_summary_with_urls.csv ({len(df_file_type_summary)} rows)")
    
    conn.close()
    
    print(f"\n🎉 All exports regenerated successfully!")
    print(f"📁 Files saved to: {exports_dir}")
    
    # Show summary
    print(f"\n📊 Export Summary:")
    print(f"  📋 Basic tables: 3 files")
    print(f"  📊 Comprehensive views: 3 files")
    print(f"  📈 Summary statistics: 3 files")
    print(f"  📁 Total: 9 CSV files")
    
    # Show key file info
    print(f"\n🔑 Key Files:")
    print(f"  📄 files_with_products_and_urls.csv - MAIN EXPORT with all file data and URLs")
    print(f"  📄 files_with_urls.csv - Just files with their URLs")
    print(f"  📄 comprehensive_products_with_urls.csv - Product summary with file counts")

if __name__ == "__main__":
    regenerate_exports_with_files_urls()
