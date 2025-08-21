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

def test_corrected_transformations():
    """Test the corrected URL transformations with known examples."""
    
    test_cases = [
        "motia_sit_to_stand_table_vista_rectangular",
        "aeron_chair_a_size_height_adjustable_arms", 
        "eames_molded_plastic_armchair_dowel_base_fully_upholstered",
        "leeway_stool_bar_height_polyurethane_seat"
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

if __name__ == "__main__":
    test_corrected_transformations()
