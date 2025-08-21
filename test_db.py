import sqlite3

conn = sqlite3.connect('library/index.sqlite')
cursor = conn.cursor()

# Check matched_image_path
cursor.execute("SELECT COUNT(*) FROM files WHERE matched_image_path IS NOT NULL AND matched_image_path != ''")
count = cursor.fetchone()[0]
print(f"Files with matched_image_path: {count}")

# Check a sample
cursor.execute("SELECT sha256, matched_image_path FROM files WHERE matched_image_path IS NOT NULL AND matched_image_path != '' LIMIT 3")
samples = cursor.fetchall()
for sha256, path in samples:
    print(f"{sha256[:8]}... -> {path}")

conn.close()
