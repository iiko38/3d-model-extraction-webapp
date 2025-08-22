#!/usr/bin/env python3
import sqlite3
import time

def test_upsert():
    print("=== TESTING UPSERT BEHAVIOR ===")
    
    conn = sqlite3.connect('library/index.images-test.sqlite')
    cursor = conn.cursor()
    
    # Insert an approved image with score 10
    print("1. Inserting approved image with score 10...")
    cursor.execute("""
    INSERT INTO images(product_uid, variant, image_url, provider, score, rationale, status, created_at, updated_at)
    VALUES ('herman_miller:aeron_chairs', '', 'https://example.com/a.jpg', 'test', 10.0, 'seed', 'approved', strftime('%s','now'), strftime('%s','now'))
    ON CONFLICT(product_uid, variant, image_url) DO UPDATE SET
      score=excluded.score,
      status='approved',
      updated_at=excluded.updated_at;
    """)
    
    # Attempt to upsert same URL with a lower score (should NOT downgrade)
    print("2. Attempting to upsert same URL with score 5...")
    cursor.execute("""
    INSERT INTO images(product_uid, variant, image_url, provider, score, rationale, status, created_at, updated_at)
    VALUES ('herman_miller:aeron_chairs', '', 'https://example.com/a.jpg', 'test', 5.0, 'lower', 'pending', strftime('%s','now'), strftime('%s','now'))
    ON CONFLICT(product_uid, variant, image_url) DO UPDATE SET
      score=CASE WHEN excluded.score > images.score THEN excluded.score ELSE images.score END,
      status=CASE WHEN images.status='approved' THEN 'approved' ELSE images.status END,
      updated_at=excluded.updated_at;
    """)
    
    # Check the result
    print("3. Checking final status and score...")
    cursor.execute("""
    SELECT status, score FROM images 
    WHERE product_uid='herman_miller:aeron_chairs' AND variant='' AND image_url='https://example.com/a.jpg';
    """)
    
    result = cursor.fetchone()
    if result:
        status, score = result
        print(f"Final status: {status}")
        print(f"Final score: {score}")
        
        if status == 'approved' and score == 10.0:
            print("✅ UPSERT TEST PASSED - No downgrade occurred")
        else:
            print("❌ UPSERT TEST FAILED - Downgrade occurred")
    else:
        print("❌ No record found")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    test_upsert()
