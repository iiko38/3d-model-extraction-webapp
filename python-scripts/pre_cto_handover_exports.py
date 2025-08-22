#!/usr/bin/env python3
"""
Pre-CTO Handover Export Script
Generates comprehensive CSV exports for the 3D Model Extraction project.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

# Configuration
DB_PATH = "library/index.sqlite"
EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(exist_ok=True)

def get_db_connection():
    """Create database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def export_products():
    """Export products table with file counts."""
    conn = get_db_connection()
    
    sql = """
    SELECT 
        p.product_uid,
        p.brand,
        p.name,
        p.slug,
        p.category,
        COUNT(f.sha256) as total_files,
        SUM(CASE WHEN f.file_type = 'revit' THEN 1 ELSE 0 END) as revit_count,
        SUM(CASE WHEN f.file_type = 'sketchup' THEN 1 ELSE 0 END) as sketchup_count,
        SUM(CASE WHEN f.file_type = 'autocad_3d' THEN 1 ELSE 0 END) as autocad_3d_count,
        SUM(CASE WHEN f.file_type = 'autocad_2d' THEN 1 ELSE 0 END) as autocad_2d_count,
        SUM(CASE WHEN f.file_type = 'autocad' THEN 1 ELSE 0 END) as autocad_count,
        SUM(CASE WHEN f.file_type = 'sif' THEN 1 ELSE 0 END) as sif_count
    FROM products p
    LEFT JOIN files f ON p.product_uid = f.product_uid
    GROUP BY p.product_uid
    ORDER BY p.brand, p.name
    """
    
    df = pd.read_sql_query(sql, conn)
    output_path = EXPORTS_DIR / "pre_cto_handover_products.csv"
    df.to_csv(output_path, index=False)
    print(f"✅ Exported {len(df)} products to {output_path}")
    conn.close()

def export_files_data():
    """Export files table with all metadata."""
    conn = get_db_connection()
    
    sql = """
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
        f.furniture_type,
        f.subtype,
        f.tags_csv,
        f.url_health,
        f.status,
        f.thumbnail_url,
        f.product_url,
        f.matched_image_path,
        f.brand,
        f.name,
        f.slug,
        f.category,
        f.product_card_image_path,
        f.urls_checked,
        p.name as product_name,
        p.brand as product_brand
    FROM files f
    LEFT JOIN products p ON f.product_uid = p.product_uid
    ORDER BY f.brand, f.name, f.file_type
    """
    
    df = pd.read_sql_query(sql, conn)
    output_path = EXPORTS_DIR / "pre_cto_handover_files.csv"
    df.to_csv(output_path, index=False)
    print(f"✅ Exported {len(df)} files to {output_path}")
    conn.close()

def export_images():
    """Export images table."""
    conn = get_db_connection()
    
    sql = """
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
        p.name as product_name,
        p.brand as product_brand
    FROM images i
    LEFT JOIN products p ON i.product_uid = p.product_uid
    ORDER BY i.product_uid, i.score DESC
    """
    
    df = pd.read_sql_query(sql, conn)
    output_path = EXPORTS_DIR / "pre_cto_handover_images.csv"
    df.to_csv(output_path, index=False)
    print(f"✅ Exported {len(df)} images to {output_path}")
    conn.close()

def export_statistics():
    """Export comprehensive statistics."""
    conn = get_db_connection()
    
    # Overall statistics
    stats = {}
    
    # Product counts by brand
    brand_stats = pd.read_sql_query("""
        SELECT brand, COUNT(*) as product_count
        FROM products 
        GROUP BY brand 
        ORDER BY product_count DESC
    """, conn)
    stats['brand_stats'] = brand_stats
    
    # File type distribution
    file_type_stats = pd.read_sql_query("""
        SELECT file_type, COUNT(*) as file_count, 
               SUM(size_bytes) as total_size_bytes
        FROM files 
        GROUP BY file_type 
        ORDER BY file_count DESC
    """, conn)
    stats['file_type_stats'] = file_type_stats
    
    # Image statistics
    image_stats = pd.read_sql_query("""
        SELECT 
            provider,
            status,
            COUNT(*) as image_count,
            AVG(score) as avg_score
        FROM images 
        GROUP BY provider, status
        ORDER BY image_count DESC
    """, conn)
    stats['image_stats'] = image_stats
    
    # Coverage statistics
    coverage_stats = pd.read_sql_query("""
        SELECT 
            p.brand,
            COUNT(p.product_uid) as total_products,
            SUM(CASE WHEN f.sha256 IS NOT NULL THEN 1 ELSE 0 END) as products_with_files,
            SUM(CASE WHEN i.product_uid IS NOT NULL THEN 1 ELSE 0 END) as products_with_images,
            ROUND(SUM(CASE WHEN f.sha256 IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(p.product_uid), 2) as file_coverage_pct,
            ROUND(SUM(CASE WHEN i.product_uid IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(p.product_uid), 2) as image_coverage_pct
        FROM products p
        LEFT JOIN files f ON p.product_uid = f.product_uid
        LEFT JOIN images i ON p.product_uid = i.product_uid
        GROUP BY p.brand
        ORDER BY total_products DESC
    """, conn)
    stats['coverage_stats'] = coverage_stats
    
    # Export each statistics table
    for name, df in stats.items():
        output_path = EXPORTS_DIR / f"pre_cto_handover_{name}.csv"
        df.to_csv(output_path, index=False)
        print(f"✅ Exported {name} to {output_path}")
    
    conn.close()

def export_summary():
    """Export a comprehensive summary report."""
    conn = get_db_connection()
    
    # Get overall counts
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM files")
    file_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM images")
    image_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(size_bytes) FROM files WHERE size_bytes IS NOT NULL")
    total_size = cursor.fetchone()[0] or 0
    
    # Create summary dataframe
    summary_data = {
        'metric': [
            'Total Products',
            'Total Files', 
            'Total Images',
            'Total Size (bytes)',
            'Total Size (MB)',
            'Total Size (GB)',
            'Export Date',
            'Database Path'
        ],
        'value': [
            product_count,
            file_count,
            image_count,
            total_size,
            round(total_size / (1024 * 1024), 2),
            round(total_size / (1024 * 1024 * 1024), 2),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            DB_PATH
        ]
    }
    
    df = pd.DataFrame(summary_data)
    output_path = EXPORTS_DIR / "pre_cto_handover_summary.csv"
    df.to_csv(output_path, index=False)
    print(f"✅ Exported summary to {output_path}")
    
    conn.close()

def main():
    """Run all export functions."""
    print("🚀 Starting Pre-CTO Handover Export Process...")
    print(f"📁 Exporting to: {EXPORTS_DIR}")
    print(f"🗄️  Database: {DB_PATH}")
    print("-" * 50)
    
    try:
        export_products()
        export_files_data()
        export_images()
        export_statistics()
        export_summary()
        
        print("-" * 50)
        print("🎉 All exports completed successfully!")
        print(f"📊 Files created in: {EXPORTS_DIR}")
        
        # List all created files
        created_files = list(EXPORTS_DIR.glob("pre_cto_handover_*.csv"))
        print(f"📋 Total export files: {len(created_files)}")
        for file in created_files:
            print(f"   - {file.name}")
            
    except Exception as e:
        print(f"❌ Export failed: {e}")
        raise

if __name__ == "__main__":
    main()
