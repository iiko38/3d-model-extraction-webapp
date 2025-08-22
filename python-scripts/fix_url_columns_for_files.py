import sqlite3
import pandas as pd

def get_furniture_types():
    """Return set of furniture type keywords for head noun detection."""
    return {
        'chair', 'sofa', 'table', 'stool', 'bench', 'desk', 
        'screen', 'pod', 'storage', 'cabinet', 'shelf'
    }

def get_brand_code(first_token):
    """Determine brand code based on first token."""
    # Based on actual Herman Miller CDN structure
    if first_token == 'leeway':
        return 'GGR'  # Geiger
    elif first_token in {'knot', 'riley'}:
        return 'NTO'  # NaughtOne
    else:
        return 'HMI'  # Herman Miller

def should_pluralize(head_noun):
    """Determine if family should be pluralized."""
    # Based on actual CDN structure, most families ARE pluralized
    pluralize_types = {'chair', 'sofa', 'stool', 'bench', 'table'}
    return head_noun in pluralize_types

def title_case_slug(slug):
    """Convert snake_case slug to Title_Case for filename with special handling."""
    words = slug.split('_')
    title_words = []
    
    for word in words:
        # Special case: keep "to" lowercase in compound words
        if word.lower() == 'to':
            title_words.append(word.lower())
        else:
            title_words.append(word.capitalize())
    
    return '_'.join(title_words)

def build_family_directory(tokens):
    """Build family directory with improved logic."""
    furniture_types = get_furniture_types()
    
    # Special case mappings for known families
    special_families = {
        'eames_molded_plastic_armchair': 'eames_molded_plastic_chairs',
        'motia_sit_to_stand_table': 'motia_sit_to_stand_tables',
        'aeron_chair': 'aeron_chairs',
        'leeway_stool': 'leeway_stools'
    }
    
    # Check if we have a known special case
    for i in range(len(tokens)):
        for j in range(i+1, len(tokens)+1):
            test_family = '_'.join(tokens[i:j])
            if test_family in special_families:
                return special_families[test_family]
    
    # Look for furniture type in tokens
    head_noun_index = -1
    for i, token in enumerate(tokens):
        if token in furniture_types:
            head_noun_index = i
            break
    
    # If no furniture type found, look for compound patterns
    if head_noun_index == -1:
        # Check for compound patterns like "sit_to_stand_tables"
        for i in range(len(tokens) - 2):
            if (tokens[i] == 'sit' and tokens[i+1] == 'to' and 
                tokens[i+2] in ['stand', 'sit']):
                head_noun_index = i + 2
                break
    
    # Fallback to second token if still not found
    if head_noun_index == -1:
        head_noun_index = min(1, len(tokens) - 1)
    
    # Build family directory
    family_tokens = tokens[:head_noun_index + 1]
    family = '_'.join(family_tokens)
    
    # Pluralize if needed
    head_noun = tokens[head_noun_index]
    if should_pluralize(head_noun):
        family = family + 's'
    
    return family

def build_product_url(variant_slug):
    """Build product page URL from variant slug."""
    # Convert underscores to dashes for product URL
    product_slug = variant_slug.replace('_', '-')
    return f"https://www.hermanmiller.com/en_gb/resources/3d-models-and-planning-tools/product-models/individual/{product_slug}/"

def build_thumbnail_url(variant_slug):
    """Build thumbnail URL from variant slug using the actual CDN structure."""
    
    # Normalize slug (lowercase, underscores only)
    slug = variant_slug.lower().replace('-', '_')
    tokens = slug.split('_')
    
    if not tokens:
        return None
    
    # 1. First letter directory
    first_letter = tokens[0][0]
    
    # 2. Build family directory with improved logic
    family = build_family_directory(tokens)
    
    # 3. Variant directory (entire slug)
    variant_dir = slug
    
    # 4. Brand code
    brand = get_brand_code(tokens[0])
    
    # 5. Title case filename with special handling
    title_case = title_case_slug(slug)
    
    # 6. Assemble URL
    base_url = "https://www.hermanmiller.com/content/dam/hmicom/app_assets/product_models"
    filename = f"{brand}_{title_case}_mdl_c.jpg.rendition.900.675.jpg"
    
    url = f"{base_url}/{first_letter}/{family}/{variant_dir}/{filename}"
    
    return url

def add_url_columns_to_files():
    """Add thumbnail_url and product_url columns to files table."""
    db_path = "library/index.sqlite"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Adding URL columns to files table...")
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(files)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'thumbnail_url' in columns:
            print("  ✅ thumbnail_url column already exists")
        else:
            cursor.execute("ALTER TABLE files ADD COLUMN thumbnail_url TEXT")
            print("  ✅ Successfully added thumbnail_url column")
        
        if 'product_url' in columns:
            print("  ✅ product_url column already exists")
        else:
            cursor.execute("ALTER TABLE files ADD COLUMN product_url TEXT")
            print("  ✅ Successfully added product_url column")
        
        # Show updated schema
        cursor.execute("PRAGMA table_info(files)")
        columns = cursor.fetchall()
        print(f"  📋 Updated files table columns: {[col[1] for col in columns]}")
        
    except Exception as e:
        print(f"  ❌ Error adding columns: {e}")
        conn.rollback()
    
    conn.close()

def populate_url_columns_for_files():
    """Populate thumbnail_url and product_url columns for all files based on their variants."""
    db_path = "library/index.sqlite"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🚀 Populating URL columns for all files...")
    
    # Get all files with variants
    cursor.execute("""
        SELECT sha256, variant, product_uid, file_type 
        FROM files 
        WHERE variant IS NOT NULL AND variant != ''
        ORDER BY product_uid, variant
    """)
    
    files = cursor.fetchall()
    
    updated_count = 0
    skipped_count = 0
    
    print(f"📊 Processing {len(files)} files with variants...")
    
    for sha256, variant, product_uid, file_type in files:
        # Generate URLs based on the file's variant
        product_url = build_product_url(variant)
        thumbnail_url = build_thumbnail_url(variant)
        
        # Update database
        cursor.execute("""
            UPDATE files 
            SET product_url = ?, thumbnail_url = ?
            WHERE sha256 = ?
        """, (product_url, thumbnail_url, sha256))
        
        updated_count += 1
        
        # Show progress every 50 files
        if updated_count % 50 == 0:
            print(f"  ✅ Updated {updated_count} files...")
    
    # Commit all changes
    conn.commit()
    conn.close()
    
    print(f"\n🎉 URL Population Complete!")
    print(f"  ✅ Updated: {updated_count} files")
    print(f"  ⚠️  Skipped: {skipped_count} files (no variant)")
    print(f"  📊 Total: {len(files)} files with variants")

def verify_files_population():
    """Verify that URLs were populated correctly in files table."""
    db_path = "library/index.sqlite"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 Verifying files URL population...")
    
    # Count files with URLs
    cursor.execute("SELECT COUNT(*) FROM files WHERE thumbnail_url IS NOT NULL AND thumbnail_url != ''")
    thumbnail_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM files WHERE product_url IS NOT NULL AND product_url != ''")
    product_url_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM files")
    total_files = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM files WHERE variant IS NOT NULL AND variant != ''")
    files_with_variants = cursor.fetchone()[0]
    
    print(f"  📊 Total files: {total_files}")
    print(f"  📋 Files with variants: {files_with_variants}")
    print(f"  🖼️  Files with thumbnail_url: {thumbnail_count}")
    print(f"  🔗 Files with product_url: {product_url_count}")
    
    # Show sample entries
    cursor.execute("""
        SELECT sha256, variant, product_uid, file_type, product_url, thumbnail_url 
        FROM files 
        WHERE thumbnail_url IS NOT NULL AND thumbnail_url != ''
        LIMIT 3
    """)
    
    samples = cursor.fetchall()
    if samples:
        print(f"\n📝 Sample populated file entries:")
        for sha256, variant, product_uid, file_type, product_url, thumbnail_url in samples:
            print(f"  {sha256[:8]}...: {variant}")
            print(f"    Product: {product_uid} | Type: {file_type}")
            print(f"    Product URL: {product_url}")
            print(f"    Thumbnail URL: {thumbnail_url}")
            print()
    
    conn.close()

def main():
    """Main function to run the complete files URL population process."""
    print("🎯 Starting Files URL Population Process")
    print("=" * 60)
    
    # Step 1: Add URL columns to files table
    add_url_columns_to_files()
    
    # Step 2: Populate both URL columns for all files
    populate_url_columns_for_files()
    
    # Step 3: Verify the population
    verify_files_population()
    
    print("\n✅ Files URL Population Process Complete!")

if __name__ == "__main__":
    main()
