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

def add_product_url_column():
    """Add product_url column to products table if it doesn't exist."""
    db_path = "library/index.sqlite"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Adding product_url column to products table...")
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(products)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'product_url' in columns:
            print("  ✅ product_url column already exists")
        else:
            cursor.execute("ALTER TABLE products ADD COLUMN product_url TEXT")
            conn.commit()
            print("  ✅ Successfully added product_url column")
        
        # Show updated schema
        cursor.execute("PRAGMA table_info(products)")
        columns = cursor.fetchall()
        print(f"  📋 Updated products table columns: {[col[1] for col in columns]}")
        
    except Exception as e:
        print(f"  ❌ Error adding column: {e}")
        conn.rollback()
    
    conn.close()

def get_variant_for_product(product_uid):
    """Get the most common variant for a product from the files table."""
    db_path = "library/index.sqlite"
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT variant, COUNT(*) as count
    FROM files 
    WHERE product_uid = ? AND variant IS NOT NULL AND variant != ''
    GROUP BY variant
    ORDER BY count DESC
    LIMIT 1
    """
    
    cursor = conn.cursor()
    cursor.execute(query, (product_uid,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

def populate_url_columns():
    """Populate thumbnail_url and product_url columns for all products."""
    db_path = "library/index.sqlite"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🚀 Populating URL columns for all products...")
    
    # Get all products
    cursor.execute("SELECT product_uid, name FROM products")
    products = cursor.fetchall()
    
    updated_count = 0
    skipped_count = 0
    
    for product_uid, name in products:
        print(f"\n📦 Processing: {name} ({product_uid})")
        
        # Get variant for this product
        variant = get_variant_for_product(product_uid)
        
        if variant:
            # Generate URLs
            product_url = build_product_url(variant)
            thumbnail_url = build_thumbnail_url(variant)
            
            # Update database
            cursor.execute("""
                UPDATE products 
                SET product_url = ?, thumbnail_url = ?
                WHERE product_uid = ?
            """, (product_url, thumbnail_url, product_uid))
            
            print(f"  ✅ Variant: {variant}")
            print(f"  🔗 Product URL: {product_url}")
            print(f"  🖼️  Thumbnail URL: {thumbnail_url}")
            updated_count += 1
        else:
            print(f"  ⚠️  No variant found for product")
            skipped_count += 1
    
    # Commit all changes
    conn.commit()
    conn.close()
    
    print(f"\n🎉 URL Population Complete!")
    print(f"  ✅ Updated: {updated_count} products")
    print(f"  ⚠️  Skipped: {skipped_count} products (no variant)")
    print(f"  📊 Total: {len(products)} products")

def verify_population():
    """Verify that URLs were populated correctly."""
    db_path = "library/index.sqlite"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 Verifying URL population...")
    
    # Count products with URLs
    cursor.execute("SELECT COUNT(*) FROM products WHERE thumbnail_url IS NOT NULL AND thumbnail_url != ''")
    thumbnail_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products WHERE product_url IS NOT NULL AND product_url != ''")
    product_url_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products")
    total_count = cursor.fetchone()[0]
    
    print(f"  📊 Total products: {total_count}")
    print(f"  🖼️  Products with thumbnail_url: {thumbnail_count}")
    print(f"  🔗 Products with product_url: {product_url_count}")
    
    # Show sample entries
    cursor.execute("""
        SELECT product_uid, name, product_url, thumbnail_url 
        FROM products 
        WHERE thumbnail_url IS NOT NULL AND thumbnail_url != ''
        LIMIT 3
    """)
    
    samples = cursor.fetchall()
    if samples:
        print(f"\n📝 Sample populated entries:")
        for product_uid, name, product_url, thumbnail_url in samples:
            print(f"  {product_uid}: {name}")
            print(f"    Product URL: {product_url}")
            print(f"    Thumbnail URL: {thumbnail_url}")
            print()
    
    conn.close()

def main():
    """Main function to run the complete URL population process."""
    print("🎯 Starting URL Population Process")
    print("=" * 60)
    
    # Step 1: Add product_url column
    add_product_url_column()
    
    # Step 2: Populate both URL columns
    populate_url_columns()
    
    # Step 3: Verify the population
    verify_population()
    
    print("\n✅ URL Population Process Complete!")

if __name__ == "__main__":
    main()
