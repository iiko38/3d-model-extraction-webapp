import re

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

def test_transformations():
    """Test the URL transformation with various examples."""
    
    test_cases = [
        "aeron_chair_a_size_height_adjustable_arms",
        "leeway_stool_bar_height_upholstered_seat",
        "cosm_chair_mid_back_leaf_arms",
        "eames_lounge_chair_classic",
        "riley_table_round_wood_top",
        "knot_side_table_small",
        "everywhere_table_rectangular",
        "mirra_2_chair_fully_adjustable_arms",
        "sayl_chair_suspension_mid_back_fully_adjustable_arms",
        "zeph_chair_with_arms"
    ]
    
    print("Testing Thumbnail URL Transformations:")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        url = build_thumbnail_url(test_case)
        print(f"{i:2d}. Input:  {test_case}")
        print(f"    Output: {url}")
        print()

if __name__ == "__main__":
    test_transformations()
