#!/usr/bin/env python3
import sqlite3
import re
from pathlib import Path

def calculate_image_score(image_data, product_name):
    """Calculate a relevance score for an image (0-10 scale)."""
    score = 0.0
    
    # Base score from provider
    if image_data['provider'] == 'herman_miller_product_page':
        score += 3.0
    elif image_data['provider'] == 'herman_miller_comprehensive':
        score += 2.0
    else:
        score += 1.0
    
    # Score based on rationale (extract type information)
    rationale = (image_data.get('rationale', '') or '').lower()
    if 'main_product_image' in rationale:
        score += 3.0
    elif 'product_image' in rationale:
        score += 2.0
    elif 'search_match' in rationale:
        score += 1.5
    elif 'model_image' in rationale:
        score += 1.0
    elif 'comprehensive search' in rationale:
        score += 1.5
    else:
        score += 0.5
    
    # Score based on alt text relevance (extract from rationale or URL)
    product_words = product_name.lower().replace('_', ' ').split()
    
    # Check URL for product relevance
    url = image_data.get('image_url', '').lower()
    for word in product_words:
        if len(word) > 2 and word in url:
            score += 0.5
    
    # Score based on filename relevance
    filename = image_data.get('local_path', '')
    if filename:
        filename_lower = filename.lower()
        for word in product_words:
            if len(word) > 2 and word in filename_lower:
                score += 0.5
    
    # Score based on image dimensions (larger = better)
    width = image_data.get('width', 0)
    height = image_data.get('height', 0)
    if width and height:
        area = width * height
        if area > 1000000:  # > 1MP
            score += 1.0
        elif area > 500000:  # > 500KP
            score += 0.5
    
    # Bonus for having local path (downloaded successfully)
    if image_data.get('local_path'):
        score += 0.5
    
    # Cap at 10.0
    return min(score, 10.0)

def select_primary_images():
    """Select the best primary image for each product."""
    conn = sqlite3.connect('library/index.sqlite')
    cursor = conn.cursor()
    
    print("=== SELECTING PRIMARY IMAGES ===")
    
    # Get all products with images
    cursor.execute("""
        SELECT DISTINCT p.product_uid, p.name, p.brand
        FROM products p
        JOIN images i ON p.product_uid = i.product_uid
        WHERE i.status = 'pending'
        ORDER BY p.name
    """)
    products = cursor.fetchall()
    
    print(f"Found {len(products)} products with images")
    
    updated_count = 0
    
    for product_uid, product_name, brand in products:
        print(f"\nProcessing: {product_uid} ({product_name})")
        
        # Get all images for this product
        cursor.execute("""
            SELECT image_url, provider, rationale, local_path, width, height, score
            FROM images
            WHERE product_uid = ? AND status = 'pending'
            ORDER BY score DESC, created_at DESC
        """, (product_uid,))
        
        images = cursor.fetchall()
        
        if not images:
            continue
        
        # Calculate scores for each image
        scored_images = []
        for img in images:
            image_data = {
                'image_url': img[0],
                'provider': img[1],
                'rationale': img[2],
                'local_path': img[3],
                'width': img[4],
                'height': img[5],
                'score': img[6]
            }
            
            calculated_score = calculate_image_score(image_data, product_name)
            scored_images.append((calculated_score, image_data))
        
        # Sort by calculated score (highest first)
        scored_images.sort(key=lambda x: x[0], reverse=True)
        
        # Select the best image
        best_score, best_image = scored_images[0]
        
        print(f"  Best image score: {best_score:.1f}")
        print(f"  Selected: {best_image['local_path'] or best_image['image_url'][:50]}...")
        
        # Update the database
        try:
            # Mark this image as primary
            cursor.execute("""
                UPDATE images 
                SET is_primary = 1, image_score = ?
                WHERE product_uid = ? AND image_url = ?
            """, (best_score, product_uid, best_image['image_url']))
            
            # Update product with primary image path
            primary_path = best_image.get('local_path') or best_image['image_url']
            cursor.execute("""
                UPDATE products 
                SET product_card_image_path = ?
                WHERE product_uid = ?
            """, (primary_path, product_uid))
            
            updated_count += 1
            
        except Exception as e:
            print(f"  ✗ Error updating database: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n=== PRIMARY IMAGE SELECTION COMPLETE ===")
    print(f"Updated {updated_count} products with primary images")

if __name__ == "__main__":
    select_primary_images()
