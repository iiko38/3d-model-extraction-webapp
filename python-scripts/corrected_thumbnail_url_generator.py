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
    # Based on actual CDN structure, most families are NOT pluralized
    return False  # Don't pluralize

def title_case_slug(slug):
    """Convert snake_case slug to Title_Case for filename."""
    return '_'.join(word.capitalize() for word in slug.split('_'))

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
    
    # 2. Find head noun and build family
    furniture_types = get_furniture_types()
    head_noun_index = -1
    
    for i, token in enumerate(tokens):
        if token in furniture_types:
            head_noun_index = i
            break
    
    # Fallback to second token if no furniture type found
    if head_noun_index == -1:
        head_noun_index = min(1, len(tokens) - 1)
    
    # Build family directory (don't pluralize)
    family_tokens = tokens[:head_noun_index + 1]
    family = '_'.join(family_tokens)
    
    # 3. Variant directory (entire slug)
    variant_dir = slug
    
    # 4. Brand code
    brand = get_brand_code(tokens[0])
    
    # 5. Title case filename
    title_case = title_case_slug(slug)
    
    # 6. Assemble URL
    base_url = "https://www.hermanmiller.com/content/dam/hmicom/app_assets/product_models"
    filename = f"{brand}_{title_case}_mdl_c.jpg.rendition.900.675.jpg"
    
    url = f"{base_url}/{first_letter}/{family}/{variant_dir}/{filename}"
    
    return url

def test_corrected_transformations():
    """Test the corrected URL transformations."""
    
    test_cases = [
        "leeway_stool_bar_height_polyurethane_seat",
        "aeron_chair_a_size_height_adjustable_arms",
        "cosm_chair_mid_back_leaf_arms",
        "eames_lounge_chair_classic",
        "knot_side_table_small"
    ]
    
    print("Testing Corrected URL Transformations:")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        product_url = build_product_url(test_case)
        thumbnail_url = build_thumbnail_url(test_case)
        
        print(f"{i:2d}. Variant: {test_case}")
        print(f"    Product URL: {product_url}")
        print(f"    Thumbnail URL: {thumbnail_url}")
        print()

def test_with_real_data():
    """Test with real database variants."""
    
    # Connect to database
    db_path = "library/index.sqlite"
    conn = sqlite3.connect(db_path)
    
    # Get unique variants from files table
    query = """
    SELECT DISTINCT variant, COUNT(*) as file_count
    FROM files 
    WHERE variant IS NOT NULL AND variant != ''
    GROUP BY variant
    ORDER BY file_count DESC
    LIMIT 5
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print("Testing with Real Database Variants:")
    print("=" * 80)
    
    for i, row in df.iterrows():
        variant = row['variant']
        file_count = row['file_count']
        product_url = build_product_url(variant)
        thumbnail_url = build_thumbnail_url(variant)
        
        print(f"{i+1:2d}. Variant: {variant}")
        print(f"    Files: {file_count}")
        print(f"    Product URL: {product_url}")
        print(f"    Thumbnail URL: {thumbnail_url}")
        print()

if __name__ == "__main__":
    test_corrected_transformations()
    print("\n" + "="*80 + "\n")
    test_with_real_data()
