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
    naughtone_tokens = {'leeway', 'knot', 'riley'}
    return 'NTO' if first_token in naughtone_tokens else 'HMI'

def should_pluralize(head_noun):
    """Determine if family should be pluralized."""
    pluralize_types = {'chair', 'sofa', 'stool', 'bench'}
    return head_noun in pluralize_types

def title_case_slug(slug):
    """Convert snake_case slug to Title_Case for filename."""
    return '_'.join(word.capitalize() for word in slug.split('_'))

def build_thumbnail_url(variant_slug):
    """Build thumbnail URL from variant slug using the transformation rules."""
    
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
    
    # Build family directory
    family_tokens = tokens[:head_noun_index + 1]
    family = '_'.join(family_tokens)
    
    # Pluralize if needed
    head_noun = tokens[head_noun_index]
    if should_pluralize(head_noun):
        family = family + 's'
    
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

def test_with_real_data():
    """Test URL transformation with real variant data from database."""
    
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
    LIMIT 10
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print("Testing with Real Database Variants:")
    print("=" * 80)
    
    for i, row in df.iterrows():
        variant = row['variant']
        file_count = row['file_count']
        url = build_thumbnail_url(variant)
        
        print(f"{i+1:2d}. Variant: {variant}")
        print(f"    Files: {file_count}")
        print(f"    URL:   {url}")
        print()

if __name__ == "__main__":
    test_with_real_data()
