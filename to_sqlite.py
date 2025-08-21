#!/usr/bin/env python3
"""
Load manifest into SQLite database
"""

import csv
import json
import sqlite3
import sys
from pathlib import Path


def main():
    DB = sys.argv[1] if len(sys.argv) > 1 else "library/index.sqlite"
    MANIFEST = sys.argv[2] if len(sys.argv) > 2 else "manifest.jsonl"

    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.executescript("""
    DROP TABLE IF EXISTS files;
    DROP TABLE IF EXISTS products;
    
    CREATE TABLE IF NOT EXISTS products (
      product_uid TEXT PRIMARY KEY,
      brand       TEXT NOT NULL,
      name        TEXT NOT NULL,
      slug        TEXT NOT NULL,
      category    TEXT
    );

    -- Composite PK: a given file (hash) can appear under multiple products.
    CREATE TABLE IF NOT EXISTS files (
      product_uid  TEXT NOT NULL REFERENCES products(product_uid),
      sha256       TEXT NOT NULL,
      variant      TEXT,
      file_type    TEXT NOT NULL,
      ext          TEXT NOT NULL,
      stored_path  TEXT NOT NULL,
      size_bytes   INTEGER,
      source_url   TEXT,
      source_page  TEXT,
      PRIMARY KEY (product_uid, sha256)
    );

    CREATE INDEX IF NOT EXISTS files_product_idx ON files(product_uid);
    CREATE INDEX IF NOT EXISTS files_type_idx    ON files(file_type);
    CREATE INDEX IF NOT EXISTS files_sha_idx ON files(sha256);  -- non-unique index to spot global dupes
    """)

    def upsert_product(brand, name, slug, category):
        uid = f"{brand}:{slug}"
        cur.execute(
            "INSERT INTO products(product_uid, brand, name, slug, category) VALUES (?,?,?,?,?) "
            "ON CONFLICT(product_uid) DO UPDATE SET brand=excluded.brand, name=excluded.name, slug=excluded.slug, category=COALESCE(excluded.category, products.category)",
            (uid, brand, name, slug, category)
        )
        return uid

    def upsert_file(product_uid, r):
        cur.execute(
            "INSERT INTO files(product_uid, sha256, variant, file_type, ext, stored_path, size_bytes, source_url, source_page) "
            "VALUES (?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(product_uid, sha256) DO UPDATE SET "
            "  variant=COALESCE(excluded.variant, files.variant), "
            "  file_type=excluded.file_type, "
            "  ext=excluded.ext, "
            "  stored_path=excluded.stored_path, "
            "  size_bytes=excluded.size_bytes, "
            "  source_url=COALESCE(excluded.source_url, files.source_url), "
            "  source_page=COALESCE(excluded.source_page, files.source_page)",
            (product_uid, r['sha256'], r.get('variant'), r['file_type'], r['ext'], r['stored_path'], int(r.get('size_bytes') or 0), r.get('source_url'), r.get('source_page'))
        )

    p = Path(MANIFEST)
    if p.suffix == ".jsonl":
        for line in p.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            uid = upsert_product(r["brand"], r["product"], r["product_slug"], r.get("category"))
            upsert_file(uid, r)
    else:
        with p.open("r", encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                uid = upsert_product(r["brand"], r["product"], r["product_slug"], r.get("category"))
                upsert_file(uid, r)

    con.commit()
    print("Loaded into", DB)


if __name__ == "__main__":
    main()
