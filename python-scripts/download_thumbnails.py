#!/usr/bin/env python3
"""
Thumbnail Download Script
Downloads thumbnail images for files with checked URLs
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.thumbnail_service import thumbnail_service

def main():
    """Download thumbnails for all files with checked URLs."""
    print("🖼️  Thumbnail Download Service")
    print("=" * 50)
    
    # Check current status
    files_needing_thumbnails = thumbnail_service.get_files_needing_thumbnails()
    
    if not files_needing_thumbnails:
        print("✅ No files need thumbnail downloads (no checked URLs with thumbnail URLs)")
        return
    
    print(f"📊 Found {len(files_needing_thumbnails)} files needing thumbnails")
    
    # Show sample files
    print("\n📝 Sample files to process:")
    for i, file_data in enumerate(files_needing_thumbnails[:5]):
        print(f"  {i+1}. {file_data['sha256'][:8]}... - {file_data['variant']}")
        print(f"     URL: {file_data['thumbnail_url']}")
    
    if len(files_needing_thumbnails) > 5:
        print(f"  ... and {len(files_needing_thumbnails) - 5} more")
    
    # Ask for confirmation
    response = input(f"\n🚀 Start downloading {len(files_needing_thumbnails)} thumbnails? (y/N): ")
    if response.lower() != 'y':
        print("❌ Download cancelled")
        return
    
    # Start download
    print(f"\n🔄 Starting thumbnail download...")
    result = thumbnail_service.download_all_thumbnails()
    
    print(f"\n✅ Download complete!")
    print(f"  📊 Total files: {result['total']}")
    print(f"  ✅ Downloaded: {result['downloaded']}")
    print(f"  ❌ Failed: {result['failed']}")
    
    if result['downloaded'] > 0:
        print(f"\n🎉 Successfully downloaded {result['downloaded']} thumbnails!")
        print(f"📁 Thumbnails stored in: {thumbnail_service.cache_dir}")
    else:
        print(f"\n⚠️  No thumbnails were downloaded. Check the logs for errors.")

if __name__ == "__main__":
    main()
