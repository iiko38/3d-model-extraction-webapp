#!/usr/bin/env python3
"""
HM Product Models Scraper
Single-file scraper for downloading HM product models from their website.
"""

import requests
import bs4
import lxml
import tqdm
import hashlib
import zipfile
import pathlib
import urllib.parse
import time
import random
import re
import json
import argparse
from collections import deque
from typing import Dict, List, Optional, Tuple, Set
import logging
import collections

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SUPPORTED_EXTENSIONS = {'.zip', '.rfa', '.rvt', '.skp', '.dwg', '.obj', '.fbx', '.glb', '.gltf', '.3ds', '.3dm', '.sif'}
DOWNLOAD_PATTERN = r'/content/dam/hmicom/app_assets/product_models/'
DEFAULT_SEEDS = ['https://www.hermanmiller.com/resources/3d-models-and-planning-tools/product-models/']
DEFAULT_OUTPUT_DIR = './library'
SEEN_PAGES_FILE = 'seen_pages.txt'
PRODUCT_JSON_FILE = 'product.json'

def fetch_html(url: str, sleep_min: float = 0.5, sleep_max: float = 0.8) -> Tuple[int, str]:
    """
    Fetch HTML content from URL with retry logic and polite delays.
    
    Args:
        url: The URL to fetch
        sleep_min: Minimum sleep time between requests
        sleep_max: Maximum sleep time between requests
        
    Returns:
        Tuple[int, str]: (status_code, html_content)
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'OKII-3D-Ripper/0.1 (contact: you@example.com)'
    })
    
    # Polite delay with jitter
    time.sleep(random.uniform(sleep_min, sleep_max))
    
    for attempt in range(3):
        try:
            response = session.get(url, timeout=30)
            
            # Return immediately for successful requests
            if response.status_code < 400:
                return response.status_code, response.text
            
            # Retry on 429/5xx with exponential backoff
            if response.status_code in [429] or response.status_code >= 500:
                if attempt < 2:  # Don't sleep on last attempt
                    backoff_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"HTTP {response.status_code}, retrying in {backoff_time:.1f}s...")
                    time.sleep(backoff_time)
                    continue
            
            # Return for other status codes (4xx except 429)
            return response.status_code, response.text
            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < 2:
                backoff_time = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Connection error: {e}, retrying in {backoff_time:.1f}s...")
                time.sleep(backoff_time)
                continue
            else:
                logger.error(f"Failed to fetch {url}: {e}")
                return 0, ""
    
    return 0, ""

def is_hm(url: str) -> bool:
    """
    Check if URL is from Herman Miller domain.
    
    Args:
        url: The URL to check
    
    Returns:
        bool: True if URL is from HM domain
    """
    parsed_url = urllib.parse.urlparse(url)
    return parsed_url.netloc.lower() in ['www.hermanmiller.com', 'hermanmiller.com']

def classify_page(url: str, html: str) -> str:
    """
    Classify page type based on URL path.
    
    Args:
        url: The URL of the page
        html: The HTML content of the page (unused in this implementation)
    
    Returns:
        str: 'listing', 'individual', 'system', or 'unknown'
    """
    parsed_url = urllib.parse.urlparse(url)
    path = parsed_url.path.lower()
    
    # Individual product pages
    if "/product-models/individual/" in path:
        return "individual"
    
    # System pages
    elif "/product-models/system/" in path:
        return "system"
    
    # Listing pages (including /b/ and /pc/ subdirectories)
    elif "/product-models/" in path:
        return "listing"
    
    # Unknown pages
    else:
        return "unknown"

def extract_links(url: str, html: str) -> Dict:
    """
    Extract download links and next pages from HTML content.
    
    Args:
        url: The source URL
        html: The HTML content
    
    Returns:
        dict: Contains download_links, next_pages, product_name, category, variant
    """
    soup = bs4.BeautifulSoup(html, 'lxml')
    base_url = urllib.parse.urljoin(url, '/')
    page_type = classify_page(url, html)
    
    result = {
        'download_links': [],
        'next_pages': [],
        'product_name': None,
        'category': None,
        'variant': None
    }
    
    # Extract product information first
    result['product_name'] = extract_product_name(soup, url)
    result['category'] = extract_category(soup)
    result['variant'] = extract_variant(url)
    
    # Extract download links and next pages based on page type
    if page_type == "listing":
        extract_listing_links(soup, base_url, result, url)  # Pass full URL for AJAX
    elif page_type == "individual":
        extract_individual_links(soup, base_url, result)
    elif page_type == "system":
        extract_system_links(soup, base_url, result)
    else:
        # For unknown pages, use generic extraction
        extract_generic_links(soup, base_url, result)
    
    return result

def extract_product_name(soup: bs4.BeautifulSoup, url: str) -> str:
    """Extract product name from page heading or nearest tile heading."""
    # Try page heading first
    name_selectors = [
        'h1',
        'h1[class*="product"]',
        '.product-name',
        '.product-title',
        '[data-product-name]',
        '.page-title',
        '.title'
    ]
    
    for selector in name_selectors:
        element = soup.select_one(selector)
        if element and element.get_text().strip():
            return element.get_text().strip()
    
    # Try to extract from URL if no heading found
    parsed_url = urllib.parse.urlparse(url)
    path_parts = parsed_url.path.split('/')
    if len(path_parts) > 2:
        # Get the last meaningful part of the path
        for part in reversed(path_parts):
            if part and part not in ['individual', 'system', 'product-models']:
                return part.replace('-', ' ').replace('_', ' ').title()
    
    return None

def extract_category(soup: bs4.BeautifulSoup) -> str:
    """Extract category from breadcrumbs or page content."""
    category_selectors = [
        '.breadcrumb',
        '.category',
        '[class*="breadcrumb"]',
        'nav[aria-label*="breadcrumb"]',
        '.breadcrumbs'
    ]
    
    for selector in category_selectors:
        element = soup.select_one(selector)
        if element:
            return element.get_text().strip()
    
    return None

def extract_variant(url: str) -> str:
    """Extract variant from URL or DAM path."""
    # Check for variant in URL
    if '/variant/' in url:
        return url.split('/variant/')[-1].split('/')[0]
    
    # Check for variant in DAM path
    if DOWNLOAD_PATTERN in url:
        path_parts = url.split(DOWNLOAD_PATTERN)[1].split('/')
        if len(path_parts) > 2:
            # Look for variant-like segments
            for part in path_parts[1:-1]:  # Skip first (product) and last (filename)
                if part and part not in ['zip', 'rfa', 'skp', 'dwg', 'obj', 'fbx', 'glb', 'gltf', '3ds', '3dm', 'sif']:
                    return part
    
    return None

def extract_listing_links(soup: bs4.BeautifulSoup, base_url: str, result: Dict, full_url: str = None) -> None:
    """Extract links from listing pages."""
    # First, try to extract embedded data from the HTML page
    if '/product-models/' in (full_url or base_url) and '?' in (full_url or base_url):
        logger.info(f"Attempting to extract embedded data from HTML")
        embedded_links = extract_embedded_links(soup, full_url or base_url)
        if embedded_links:
            result['download_links'].extend(embedded_links)
            logger.info(f"Added {len(embedded_links)} embedded links to result")
        else:
            logger.info("No embedded links found")
    
    # Fallback: try AJAX extraction if no embedded data found
    if not result['download_links'] and '/product-models/' in (full_url or base_url) and '?' in (full_url or base_url):
        logger.info(f"Attempting AJAX extraction for: {full_url or base_url}")
        ajax_links = extract_ajax_links(full_url or base_url)
        if ajax_links:
            result['download_links'].extend(ajax_links)
            logger.info(f"Added {len(ajax_links)} AJAX links to result")
        else:
            logger.info("No AJAX links found")
    
    # Then extract regular HTML links
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        absolute_url = urllib.parse.urljoin(base_url, href)
        anchor_text = link.get_text().strip()
        
        # Check for download links
        if DOWNLOAD_PATTERN in absolute_url:
            file_ext = pathlib.Path(urllib.parse.urlparse(absolute_url).path).suffix.lower()
            if file_ext in SUPPORTED_EXTENSIONS:
                result['download_links'].append({
                    'url': absolute_url,
                    'text': anchor_text,
                    'filename': pathlib.Path(urllib.parse.urlparse(absolute_url).path).name
                })
        
        # Check for product detail links
        if ('/product-models/individual/' in absolute_url or 
            '/product-models/system/' in absolute_url):
            if absolute_url not in result['next_pages']:
                result['next_pages'].append(absolute_url)

def extract_individual_links(soup: bs4.BeautifulSoup, base_url: str, result: Dict) -> None:
    """Extract links from individual product pages."""
    # Look for download links in "Downloads" and "Related product configurations" areas
    # But be generic and use the DAM path rule across the whole DOM
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        absolute_url = urllib.parse.urljoin(base_url, href)
        anchor_text = link.get_text().strip()
        
        # Check for download links using DAM path rule
        if DOWNLOAD_PATTERN in absolute_url:
            file_ext = pathlib.Path(urllib.parse.urlparse(absolute_url).path).suffix.lower()
            if file_ext in SUPPORTED_EXTENSIONS:
                result['download_links'].append({
                    'url': absolute_url,
                    'text': anchor_text,
                    'filename': pathlib.Path(urllib.parse.urlparse(absolute_url).path).name
                })
        
        # Check for next pages (product links, etc.)
        if is_hm(absolute_url) and absolute_url not in result['next_pages']:
            result['next_pages'].append(absolute_url)

def extract_system_links(soup: bs4.BeautifulSoup, base_url: str, result: Dict) -> None:
    """Extract links from system pages."""
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        absolute_url = urllib.parse.urljoin(base_url, href)
        anchor_text = link.get_text().strip()
        
        # Check for "Download All Revit Family Components" link (ZIP)
        if (DOWNLOAD_PATTERN in absolute_url and 
            absolute_url.lower().endswith('.zip') and
            'revit' in anchor_text.lower() and 'family' in anchor_text.lower()):
            result['download_links'].append({
                'url': absolute_url,
                'text': anchor_text,
                'filename': pathlib.Path(urllib.parse.urlparse(absolute_url).path).name
            })
        
        # Check for "Planning Idea" block links
        elif DOWNLOAD_PATTERN in absolute_url:
            file_ext = pathlib.Path(urllib.parse.urlparse(absolute_url).path).suffix.lower()
            if file_ext in SUPPORTED_EXTENSIONS:
                result['download_links'].append({
                    'url': absolute_url,
                    'text': anchor_text,
                    'filename': pathlib.Path(urllib.parse.urlparse(absolute_url).path).name
                })
        
        # Check for family group links
        elif DOWNLOAD_PATTERN in absolute_url:
            file_ext = pathlib.Path(urllib.parse.urlparse(absolute_url).path).suffix.lower()
            if file_ext in SUPPORTED_EXTENSIONS:
                result['download_links'].append({
                    'url': absolute_url,
                    'text': anchor_text,
                    'filename': pathlib.Path(urllib.parse.urlparse(absolute_url).path).name
                })
        
        # Check for next pages
        if is_hm(absolute_url) and absolute_url not in result['next_pages']:
            result['next_pages'].append(absolute_url)

def extract_generic_links(soup: bs4.BeautifulSoup, base_url: str, result: Dict) -> None:
    """Extract links from unknown page types."""
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        absolute_url = urllib.parse.urljoin(base_url, href)
        anchor_text = link.get_text().strip()
        
        # Check for download links
        if DOWNLOAD_PATTERN in absolute_url:
            file_ext = pathlib.Path(urllib.parse.urlparse(absolute_url).path).suffix.lower()
            if file_ext in SUPPORTED_EXTENSIONS:
                result['download_links'].append({
                    'url': absolute_url,
                    'text': anchor_text,
                    'filename': pathlib.Path(urllib.parse.urlparse(absolute_url).path).name
                })
        
        # Check for next pages
        if is_hm(absolute_url) and absolute_url not in result['next_pages']:
            result['next_pages'].append(absolute_url)

def infer_brand_from_fname(fname: str) -> str:
    """
    Infer brand name from filename using prefix mapping.
    
    Args:
        fname: The filename
    
    Returns:
        str: Inferred brand name
    """
    # Prefix mapping for HM brands
    prefix_mapping = {
        'HMI_': 'herman_miller',
        'GGR_': 'geiger', 
        'NTO_': 'naughtone'
    }
    
    for prefix, brand in prefix_mapping.items():
        if fname.startswith(prefix):
            return brand
    
    # Default to herman_miller if no prefix matches
    return 'herman_miller'

def slugify(name: str) -> str:
    """
    Convert a string to a URL-friendly slug.
    
    Args:
        name: The string to slugify
    
    Returns:
        str: URL-friendly slug
    """
    if not name:
        return 'unknown'
    
    # Convert to lowercase, ascii-safe, replace non-alnum with hyphens, squeeze repeats
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')
    
    return slug or 'unknown'

def infer_file_type_from_text(text: str) -> str:
    """
    Infer file type from anchor text or fallback to extension.
    
    Args:
        text: The anchor text or filename
    
    Returns:
        str: Normalized file type
    """
    text_lower = text.lower()
    
    # Text-based mapping
    if 'revit' in text_lower:
        return 'revit'
    elif 'sketchup' in text_lower:
        return 'sketchup'
    elif 'autocad 2d' in text_lower:
        return 'autocad_2d'
    elif 'autocad 3d' in text_lower:
        return 'autocad_3d'
    elif 'sif' in text_lower:
        return 'sif'
    
    # Fallback by extension
    if text_lower.endswith('.dwg'):
        return 'autocad'
    elif text_lower.endswith('.skp'):
        return 'sketchup'
    elif text_lower.endswith(('.rfa', '.rvt', '.zip')):
        return 'revit'
    
    # Default fallback
    return 'unknown'

def download_and_index(link: Dict, out_root: str, context: Dict, dry_run: bool = False, sleep_min: float = 0.5, sleep_max: float = 0.8) -> List[Dict]:
    """
    Download a file and create index records.
    
    Args:
        link: Download link dictionary with {url, text, filename}
        out_root: Output root directory
        context: Context information with {brand, product_name, product_slug, variant?}
        dry_run: If True, only simulate the download without writing files
        sleep_min: Minimum sleep time between requests
        sleep_max: Maximum sleep time between requests
    
    Returns:
        List[Dict]: List of records for main file and any extracted inner files
    """
    url = link['url']
    filename = link['filename']
    text = link.get('text', '')
    
    # Get context values
    brand = context.get('brand', infer_brand_from_fname(filename))
    product_name = context.get('product_name', 'unknown')
    product_slug = context.get('product_slug', slugify(product_name))
    variant = context.get('variant')
    
    # Determine file type and extension
    file_type = infer_file_type_from_text(text or filename)
    extension = pathlib.Path(filename).suffix.lower()
    
    # Build destination directory
    variant_path = f"/{variant}" if variant else ""
    dest_dir = pathlib.Path(out_root) / brand / product_slug / variant_path.lstrip('/') / file_type
    
    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = dest_dir / filename
    temp_path = dest_dir / f"{filename}.tmp"
    
    # Check if file exists and compute hash if it does
    existing_hash = None
    if file_path.exists() and not dry_run:
        logger.info(f"File exists, computing hash: {file_path}")
        existing_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                existing_hash.update(chunk)
        existing_hash = existing_hash.hexdigest()
    
    # Download file to temp location
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'OKII-3D-Ripper/0.1 (contact: you@example.com)'
        })
        
        # Polite delay with jitter
        time.sleep(random.uniform(sleep_min, sleep_max))
        
        response = session.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Calculate file size for progress bar
        total_size = int(response.headers.get('content-length', 0))
        
        if dry_run:
            logger.info(f"[DRY RUN] Would download: {filename} ({total_size} bytes) to {file_path}")
            # Create mock record for dry run
            mock_record = {
                'source_url': url,
                'stored_path': str(file_path.relative_to(pathlib.Path(out_root))),
                'file_type': file_type,
                'ext': extension,
                'sha256': 'dry_run_mock_hash',
                'size_bytes': total_size
            }
            return [mock_record]
        
        # Stream download to temp file
        with open(temp_path, 'wb') as f:
            with tqdm.tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        # Compute hash of downloaded file
        sha256_hash = hashlib.sha256()
        with open(temp_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        new_hash = sha256_hash.hexdigest()
        
        # Check if file is the same (skip if hash matches)
        if existing_hash and existing_hash == new_hash:
            logger.info(f"File unchanged, skipping download: {file_path}")
            temp_path.unlink()  # Remove temp file
            
            # Create main file record
            main_record = {
                'source_url': url,
                'stored_path': str(file_path.relative_to(pathlib.Path(out_root))),
                'file_type': file_type,
                'ext': extension,
                'sha256': existing_hash,
                'size_bytes': file_path.stat().st_size,
                'link_text': text  # Store the raw anchor text
            }
            
            records = [main_record]
            
            # Handle ZIP extraction even for existing files
            if extension == '.zip':
                extracted_records = extract_zip_contents(file_path, url, dest_dir, dry_run)
                records.extend(extracted_records)
            
            return records
        else:
            logger.info(f"File changed or new, proceeding with download")
        
        # Move temp file to final location (atomic-ish)
        temp_path.replace(file_path)
        size_bytes = file_path.stat().st_size
        
        logger.info(f"Downloaded: {file_path}")
        
        # Create main file record
        main_record = {
            'source_url': url,
            'stored_path': str(file_path.relative_to(pathlib.Path(out_root))),
            'file_type': file_type,
            'ext': extension,
            'sha256': new_hash,
            'size_bytes': size_bytes,
            'link_text': text  # Store the raw anchor text
        }
        
        records = [main_record]
        
        # Handle ZIP extraction
        if extension == '.zip':
            extracted_records = extract_zip_contents(file_path, url, dest_dir, dry_run)
            records.extend(extracted_records)
        
        return records
        
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        # Clean up temp file if it exists
        if temp_path.exists():
            temp_path.unlink()
        return []

def extract_zip_contents(zip_path: pathlib.Path, zip_url: str, dest_dir: pathlib.Path, dry_run: bool = False) -> List[Dict]:
    """
    Extract allowed 3D file extensions from ZIP to extracted/ subfolder.
    
    Args:
        zip_path: Path to the ZIP file
        zip_url: Original URL of the ZIP file
        dest_dir: Destination directory for extraction
        dry_run: If True, only simulate extraction without writing files
    
    Returns:
        List[Dict]: Records for extracted files
    """
    extracted_dir = dest_dir / 'extracted'
    
    if not dry_run:
        extracted_dir.mkdir(exist_ok=True)
    
    records = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.filelist:
                # Check if file has allowed 3D extension
                file_ext = pathlib.Path(file_info.filename).suffix.lower()
                if file_ext in SUPPORTED_EXTENSIONS:
                    if dry_run:
                        logger.info(f"[DRY RUN] Would extract: {file_info.filename} from {zip_path.name}")
                        # Create mock record for dry run
                        mock_record = {
                            'source_url': f"{zip_url}#zip",
                            'stored_path': str(extracted_dir / file_info.filename),
                            'file_type': infer_file_type_from_text(file_info.filename),
                            'ext': file_ext,
                            'sha256': 'dry_run_mock_hash',
                            'size_bytes': file_info.file_size
                        }
                        records.append(mock_record)
                    else:
                        # Extract file
                        zip_ref.extract(file_info, extracted_dir)
                        extracted_path = extracted_dir / file_info.filename
                        
                        # Compute hash and size
                        sha256_hash = hashlib.sha256()
                        with open(extracted_path, 'rb') as f:
                            for chunk in iter(lambda: f.read(4096), b""):
                                sha256_hash.update(chunk)
                        
                        # Create record for extracted file
                        record = {
                            'source_url': f"{zip_url}#zip",
                            'stored_path': str(extracted_path.relative_to(pathlib.Path(dest_dir).parent.parent.parent.parent)),
                            'file_type': infer_file_type_from_text(file_info.filename),
                            'ext': file_ext,
                            'sha256': sha256_hash.hexdigest(),
                            'size_bytes': extracted_path.stat().st_size,
                            'link_text': f"Extracted from {pathlib.Path(zip_url).name}"  # Store extraction info
                        }
                        records.append(record)
                        
                        logger.info(f"Extracted: {extracted_path}")
    
    except Exception as e:
        logger.error(f"Failed to extract ZIP {zip_path}: {e}")
    
    return records

def update_product_json(meta_path: str, records: List[Dict], source_page: str = None) -> None:
    """
    Update or create product.json with download records.
    
    Args:
        meta_path: Path to product.json file
        records: List of download records
        source_page: URL of the page currently being processed
    """
    meta_path = pathlib.Path(meta_path)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing data if it exists
    existing_data = {}
    if meta_path.exists():
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            existing_data = {}
    
    # Initialize structure if needed
    if 'files' not in existing_data:
        existing_data['files'] = []
    if 'source_pages' not in existing_data:
        existing_data['source_pages'] = []
    
    # Add source page to source_pages if provided
    if source_page and source_page not in existing_data['source_pages']:
        existing_data['source_pages'].append(source_page)
    
    # Create set of existing file identifiers (source_url + sha256)
    existing_file_ids = set()
    for file_record in existing_data['files']:
        file_id = (file_record.get('source_url'), file_record.get('sha256'))
        existing_file_ids.add(file_id)
    
    # Add new records, avoiding duplicates by source_url and sha256
    for record in records:
        file_id = (record.get('source_url'), record.get('sha256'))
        if file_id not in existing_file_ids:
            # Ensure all required fields are present
            wave6_record = {
                'source_url': record.get('source_url'),
                'stored_path': record.get('stored_path'),
                'file_type': record.get('file_type'),
                'ext': record.get('ext'),
                'sha256': record.get('sha256'),
                'size_bytes': record.get('size_bytes'),
                'link_text': record.get('link_text', '')  # Include link text
            }
            existing_data['files'].append(wave6_record)
            existing_file_ids.add(file_id)
    
    # Update metadata from first record if available
    if records:
        first_record = records[0]
        # Extract brand and product info from stored_path
        stored_path = pathlib.Path(first_record.get('stored_path', ''))
        path_parts = stored_path.parts if stored_path.parts else []
        
        # Brand is typically the first part after library
        brand = 'unknown'
        if len(path_parts) > 1:
            brand = path_parts[1] if path_parts[0] == 'library' else path_parts[0]
        
        # Product slug is typically the second part after library
        product_slug = 'unknown'
        if len(path_parts) > 2:
            product_slug = path_parts[2] if path_parts[0] == 'library' else path_parts[1]
        
        existing_data.update({
            'brand': brand,
            'product': product_slug.replace('-', ' ').replace('_', ' ').title(),
            'product_slug': product_slug,
            'updated_at': int(time.time())
        })
    
    # Write updated data
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)

def load_seen(out_root: str) -> Set[str]:
    """Load already seen pages from file."""
    seen_file = pathlib.Path(out_root) / SEEN_PAGES_FILE
    seen_pages = set()
    if seen_file.exists():
        with open(seen_file, 'r', encoding='utf-8') as f:
            seen_pages = set(line.strip() for line in f if line.strip())
    return seen_pages

def save_seen(out_root: str, url: str) -> None:
    """Save a single URL to seen pages file."""
    seen_file = pathlib.Path(out_root) / SEEN_PAGES_FILE
    seen_file.parent.mkdir(parents=True, exist_ok=True)
    with open(seen_file, 'a', encoding='utf-8') as f:
        f.write(f"{url}\n")

def allowed_file_type(anchor_text: str, ext: str, allow: set[str], exclude_2d: bool) -> bool:
    """
    Check if a file type is allowed based on anchor text and extension.
    
    Args:
        anchor_text: The anchor text from the link
        ext: File extension
        allow: Set of allowed file types
        exclude_2d: Whether to exclude AutoCAD 2D files
    
    Returns:
        bool: True if file type is allowed
    """
    t = (anchor_text or "").lower()
    
    def map_type(t, ext):
        if "revit" in t: return "revit"
        if "sketchup" in t: return "sketchup"
        if "autocad" in t and "3d" in t: return "autocad_3d"
        if "autocad" in t and "2d" in t: return "autocad_2d"
        if "sif" in t: return "sif"
        # fallback by ext
        if ext == ".dwg": return "autocad"
        if ext in [".rfa",".rvt",".zip"]: return "revit"
        if ext == ".skp": return "sketchup"
        return "other"
    
    ft = map_type(t, ext.lower())
    if exclude_2d and ft == "autocad_2d": 
        return False
    return ft in allow

def derive_product_variant_from_dam(url: str) -> tuple[str, str]:
    """
    Derive product slug and variant from DAM URL path.
    
    Args:
        url: The download URL
    
    Returns:
        tuple: (product_slug, variant_slug)
    """
    parsed_url = urllib.parse.urlparse(url)
    path_parts = parsed_url.path.split('/')
    
    # Find the DAM pattern
    dam_index = -1
    for i, part in enumerate(path_parts):
        if 'product_models' in part:
            dam_index = i
            break
    
    if dam_index == -1:
        return "unknown", None
    
    # Extract parts after product_models
    dam_parts = path_parts[dam_index + 1:]
    
    if len(dam_parts) >= 2:
        # First part is the product category (e.g., 'z', 'v', 's')
        product_category = dam_parts[0]
        
        # Second part is the product name (e.g., 'zeph_chair', 'verus_chairs')
        if len(dam_parts) > 1:
            product_name = dam_parts[1]
            # Convert to a more readable format
            product_slug = product_name.replace('_', '-')
        else:
            product_slug = product_category
        
        # Check if there's a variant (third part between product and filename)
        if len(dam_parts) > 2:
            variant_slug = dam_parts[2]
        else:
            variant_slug = None
        
        return product_slug, variant_slug
    
    return "unknown", None

def extract_ajax_links(base_url: str) -> List[Dict]:
    """Extract download links from AJAX-loaded content."""
    try:
        # Parse the URL to extract query parameters
        parsed = urllib.parse.urlparse(base_url)
        query_params = urllib.parse.parse_qs(parsed.query)
        
        # Build the facets for the AJAX request
        facets = []
        
        # Extract category filters (pc= parameters)
        if 'pc' in query_params:
            facets.append({
                'queryFieldId': 'category',
                'values': query_params['pc']
            })
        
        # Add other facets as needed
        facets.extend([
            {
                'queryFieldId': 'portfolio',
                'values': ['herman-miller-x-hay-collection', 'oe1-workspace-collection', 'thrive-ergonomic-portfolio']
            },
            {
                'queryFieldId': 'brand',
                'values': ['geiger', 'herman-miller', 'naughtone']
            },
            {
                'queryFieldId': 'file-type',
                'values': ['autocad-2d', 'autocad-3d', 'revit', 'revit-component', 'sketchup']
            }
        ])
        
        # Make the AJAX request
        ajax_url = 'https://www.hermanmiller.com/services/planning-ideas/models/search'
        headers = {
            'User-Agent': 'OKII-3D-Ripper/0.1 (contact: you@example.com)',
            'Accept': '*/*',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': base_url,
            'Origin': 'https://www.hermanmiller.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        
        # Build multipart form data (as seen in the network trace)
        from io import BytesIO
        import uuid
        
        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex[:8].upper()}"
        headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'
        
        # Create multipart form data
        form_data = BytesIO()
        
        # Add facets
        form_data.write(f'--{boundary}\r\n'.encode())
        form_data.write(b'Content-Disposition: form-data; name="facets"\r\n\r\n')
        form_data.write(json.dumps(facets).encode())
        form_data.write(b'\r\n')
        
        # Add totalCount
        form_data.write(f'--{boundary}\r\n'.encode())
        form_data.write(b'Content-Disposition: form-data; name="totalCount"\r\n\r\n')
        form_data.write(b'1087')
        form_data.write(b'\r\n')
        
        # End boundary
        form_data.write(f'--{boundary}--\r\n'.encode())
        
        # Debug: print the form data
        logger.info(f"Form data: {form_data.getvalue().decode('utf-8', errors='ignore')}")
        
        # Make the request
        session = requests.Session()
        response = session.post(ajax_url, data=form_data.getvalue(), headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            download_links = []
            
            logger.info(f"AJAX response: {len(data.get('results', []))} products, totalCount: {data.get('totalCount', 'unknown')}")
            
            # Extract download links from all results
            for product in data.get('results', []):
                for download in product.get('downloads', []):
                    download_url = urllib.parse.urljoin('https://www.hermanmiller.com', download['url'])
                    download_links.append({
                        'url': download_url,
                        'text': f"{download['name']}({format_size(download['size'])})",
                        'filename': pathlib.Path(urllib.parse.urlparse(download_url).path).name
                    })
            
            logger.info(f"AJAX extracted {len(download_links)} download links from {len(data.get('results', []))} products")
            return download_links
        else:
            logger.warning(f"AJAX request failed with status {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        logger.warning(f"Failed to extract AJAX links: {e}")
    
    return []

def extract_embedded_links(soup: bs4.BeautifulSoup, base_url: str) -> List[Dict]:
    """Extract download links from embedded data in HTML."""
    try:
        # Look for script tags that might contain product data
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                script_content = script.string
                
                # Look for JSON-like data structures
                # Common patterns: window.__INITIAL_STATE__, window.products, etc.
                patterns = [
                    r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                    r'window\.products\s*=\s*(\[.*?\]);',
                    r'var\s+products\s*=\s*(\[.*?\]);',
                    r'const\s+products\s*=\s*(\[.*?\]);',
                    r'"products"\s*:\s*(\[.*?\])',
                    r'"results"\s*:\s*(\[.*?\])',
                    r'"downloads"\s*:\s*(\[.*?\])'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, script_content, re.DOTALL)
                    for match in matches:
                        try:
                            data = json.loads(match)
                            if isinstance(data, list):
                                return extract_from_product_list(data, base_url)
                            elif isinstance(data, dict):
                                if 'products' in data:
                                    return extract_from_product_list(data['products'], base_url)
                                elif 'results' in data:
                                    return extract_from_product_list(data['results'], base_url)
                        except json.JSONDecodeError:
                            continue
        
        # Look for data attributes on elements
        elements_with_data = soup.find_all(attrs={'data-products': True})
        for element in elements_with_data:
            try:
                data = json.loads(element['data-products'])
                return extract_from_product_list(data, base_url)
            except (json.JSONDecodeError, KeyError):
                continue
        
        # Look for any elements with download links that might be hidden
        download_elements = soup.find_all('a', href=True)
        download_links = []
        
        for element in download_elements:
            href = element.get('href')
            if DOWNLOAD_PATTERN in href:
                abs_url = urllib.parse.urljoin(base_url, href)
                ext = pathlib.Path(urllib.parse.urlparse(abs_url).path).suffix.lower()
                if ext in SUPPORTED_EXTENSIONS:
                    download_links.append({
                        'url': abs_url,
                        'text': element.get_text(strip=True) or f"Download {ext.upper()}",
                        'filename': pathlib.Path(urllib.parse.urlparse(abs_url).path).name
                    })
        
        if download_links:
            logger.info(f"Found {len(download_links)} download links in embedded HTML")
            return download_links
            
    except Exception as e:
        logger.warning(f"Failed to extract embedded links: {e}")
    
    return []

def extract_from_product_list(products: List[Dict], base_url: str) -> List[Dict]:
    """Extract download links from a list of product objects."""
    download_links = []
    
    for product in products:
        if isinstance(product, dict):
            # Handle different product data structures
            downloads = product.get('downloads', [])
            if not downloads and 'files' in product:
                downloads = product['files']
            
            for download in downloads:
                if isinstance(download, dict):
                    url = download.get('url', '')
                    if url:
                        abs_url = urllib.parse.urljoin(base_url, url)
                        if DOWNLOAD_PATTERN in abs_url:
                            ext = pathlib.Path(urllib.parse.urlparse(abs_url).path).suffix.lower()
                            if ext in SUPPORTED_EXTENSIONS:
                                download_links.append({
                                    'url': abs_url,
                                    'text': download.get('name', '') or download.get('title', '') or f"Download {ext.upper()}",
                                    'filename': pathlib.Path(urllib.parse.urlparse(abs_url).path).name
                                })
    
    return download_links

def format_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def main():
    parser = argparse.ArgumentParser(description='Herman Miller 3D Model Ripper')
    parser.add_argument('--seeds', nargs='+', default=DEFAULT_SEEDS,
                       help='Starting URLs to crawl')
    parser.add_argument('--out', default=DEFAULT_OUTPUT_DIR,
                       help='Output directory')
    parser.add_argument('--max-pages', type=int, default=400,
                       help='Maximum pages to crawl')
    parser.add_argument('--max-downloads', type=int, default=0,
                       help='Maximum downloads per run (0 = unlimited)')
    parser.add_argument('--sleep-min', type=float, default=0.5,
                       help='Minimum sleep between requests')
    parser.add_argument('--sleep-max', type=float, default=0.8,
                       help='Maximum sleep between requests')
    parser.add_argument('--dry-run', action='store_true',
                       help='Parse and print planned downloads without writing files')
    parser.add_argument('--single-listing', type=str,
                       help='Process exactly this single page (overrides seeds/queue)')
    parser.add_argument('--multi-page-crawl', action='store_true',
                       help='Use multi-page crawl mode to capture all results (recommended for filtered listings)')
    parser.add_argument('--types', type=str, default='revit,sketchup,autocad_3d',
                       help='Comma-separated list of file types to include')
    parser.add_argument('--exclude-2d', action='store_true',
                       help='Exclude AutoCAD 2D files')
    
    args = parser.parse_args()
    
    # Parse allowed types
    allow_types = set(args.types.lower().split(','))
    logger.info(f"Allowed types: {', '.join(allow_types)}")
    if args.exclude_2d:
        logger.info("Excluding AutoCAD 2D files")
    
    output_dir = pathlib.Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Multi-page crawl mode (recommended for filtered listings)
    if args.multi_page_crawl:
        logger.info("Multi-page crawl mode enabled - will capture all results")
        crawl_queue = collections.deque(args.seeds)
        seen_pages = load_seen(output_dir)
        
        page_count = 0
        download_count = 0
        
        while crawl_queue and page_count < args.max_pages:
            url = crawl_queue.popleft()
            
            if url in seen_pages:
                continue
                
            logger.info(f"Processing page {page_count + 1}/{args.max_pages}: {url}")
            
            try:
                status_code, html = fetch_html(url)
                if status_code != 200:
                    logger.warning(f"Failed to fetch {url}: {status_code}")
                    continue
                    
                page_type = classify_page(url, html)
                logger.info(f"Page type: {page_type}")
                
                data = extract_links(url, html)
                
                # Process download links
                for link in data.get('download_links', []):
                    if args.max_downloads > 0 and download_count >= args.max_downloads:
                        break
                        
                    ext = pathlib.Path(urllib.parse.urlparse(link["url"]).path).suffix.lower()
                    if not allowed_file_type(link.get("text", ""), ext, allow_types, args.exclude_2d):
                        continue
                        
                    # Clean filename
                    fname = pathlib.Path(urllib.parse.urlparse(link["url"]).path).name
                    fname = re.sub(r"[^\w\-.]+", "_", fname)
                    link["filename"] = fname
                    
                    # Derive context from DAM path
                    product_slug, variant_slug = derive_product_variant_from_dam(link["url"])
                    brand = infer_brand_from_fname(link["filename"]) or "herman_miller"
                    context = {
                        "brand": brand,
                        "product_name": product_slug.replace("-", " "),
                        "product_slug": product_slug,
                        "variant": variant_slug
                    }
                    
                    if not args.dry_run:
                        records = download_and_index(link, str(output_dir), context, args.dry_run, args.sleep_min, args.sleep_max)
                        if records:
                            meta_path = output_dir / brand / product_slug / PRODUCT_JSON_FILE
                            update_product_json(meta_path, records, url)
                            download_count += 1
                    else:
                        print(f"[PLAN] {brand}/{product_slug}/{variant_slug or '-'} :: {link['text']} :: {link['filename']}")
                        download_count += 1
                
                # Enqueue next pages (only for HM domain and not already seen)
                for next_url in data.get('next_pages', []):
                    if is_hm(next_url) and next_url not in seen_pages and next_url not in crawl_queue:
                        crawl_queue.append(next_url)
                
                save_seen(output_dir, url)
                page_count += 1
                
                # Polite delay
                time.sleep(random.uniform(args.sleep_min, args.sleep_max))
                
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                continue
        
        logger.info(f"Multi-page crawl completed: {page_count} pages, {download_count} downloads")
        return
    
    # Single-page mode
    if args.single_listing:
        logger.info(f"Single-page mode: {args.single_listing}")
        logger.info(f"Allowed types: {', '.join(allow_types)}")
        if args.exclude_2d:
            logger.info("Excluding AutoCAD 2D files")
        
        try:
            status_code, html = fetch_html(args.single_listing)
            if status_code != 200:
                logger.error(f"Failed to fetch {args.single_listing}: {status_code}")
                return
                
            data = extract_links(args.single_listing, html)
            
            total_planned = 0
            total_downloaded = 0
            by_file_type = collections.defaultdict(int)
            
            # Process download links (do NOT enqueue next_pages)
            for link in data.get('download_links', []):
                if args.max_downloads > 0 and total_downloaded >= args.max_downloads:
                    break
                    
                ext = pathlib.Path(urllib.parse.urlparse(link["url"]).path).suffix.lower()
                if not allowed_file_type(link.get("text", ""), ext, allow_types, args.exclude_2d):
                    continue
                    
                # Clean filename
                fname = pathlib.Path(urllib.parse.urlparse(link["url"]).path).name
                fname = re.sub(r"[^\w\-.]+", "_", fname)
                link["filename"] = fname
                
                # Derive context from DAM path
                product_slug, variant_slug = derive_product_variant_from_dam(link["url"])
                brand = infer_brand_from_fname(link["filename"]) or "herman_miller"
                context = {
                    "brand": brand,
                    "product_name": product_slug.replace("-", " "),
                    "product_slug": product_slug,
                    "variant": variant_slug
                }
                
                # Determine file type for counting
                file_type = infer_file_type_from_text(link.get("text", ""))
                by_file_type[file_type] += 1
                total_planned += 1
                
                if not args.dry_run:
                    records = download_and_index(link, str(output_dir), context, args.dry_run, args.sleep_min, args.sleep_max)
                    if records:
                        meta_path = output_dir / brand / product_slug / PRODUCT_JSON_FILE
                        update_product_json(meta_path, records, args.single_listing)
                        total_downloaded += 1
                else:
                    print(f"[PLAN] {brand}/{product_slug}/{variant_slug or '-'} :: {link['text']} :: {link['filename']}")
            
            logger.info("=== SUMMARY ===")
            logger.info(f"Total planned: {total_planned}")
            logger.info(f"Total downloaded: {total_downloaded}")
            logger.info(f"By file type: {dict(by_file_type)}")
            
        except Exception as e:
            logger.error(f"Error processing single listing: {e}")
        return
    
    # Original multi-page crawl mode (fallback)
    logger.info("Starting multi-page crawl...")
    crawl_queue = collections.deque(args.seeds)
    seen_pages = load_seen(output_dir)
    
    page_count = 0
    download_count = 0
    
    while crawl_queue and page_count < args.max_pages:
        url = crawl_queue.popleft()
        
        if url in seen_pages:
            continue
            
        logger.info(f"Processing page {page_count + 1}/{args.max_pages}: {url}")
        
        try:
            status_code, html = fetch_html(url)
            if status_code != 200:
                logger.warning(f"Failed to fetch {url}: {status_code}")
                continue
                
            page_type = classify_page(url, html)
            logger.info(f"Page type: {page_type}")
            
            data = extract_links(url, html)
            
            # Process download links
            for link in data.get('download_links', []):
                if args.max_downloads > 0 and download_count >= args.max_downloads:
                    break
                    
                ext = pathlib.Path(urllib.parse.urlparse(link["url"]).path).suffix.lower()
                if not allowed_file_type(link.get("text", ""), ext, allow_types, args.exclude_2d):
                    continue
                    
                # Clean filename
                fname = pathlib.Path(urllib.parse.urlparse(link["url"]).path).name
                fname = re.sub(r"[^\w\-.]+", "_", fname)
                link["filename"] = fname
                
                # Derive context from DAM path
                product_slug, variant_slug = derive_product_variant_from_dam(link["url"])
                brand = infer_brand_from_fname(link["filename"]) or "herman_miller"
                context = {
                    "brand": brand,
                    "product_name": product_slug.replace("-", " "),
                    "product_slug": product_slug,
                    "variant": variant_slug
                }
                
                if not args.dry_run:
                    records = download_and_index(link, str(output_dir), context, args.dry_run, args.sleep_min, args.sleep_max)
                    if records:
                        meta_path = output_dir / brand / product_slug / PRODUCT_JSON_FILE
                        update_product_json(meta_path, records, url)
                        download_count += 1
                else:
                    print(f"[PLAN] {brand}/{product_slug}/{variant_slug or '-'} :: {link['text']} :: {link['filename']}")
                    download_count += 1
            
            # Enqueue next pages (only for HM domain and not already seen)
            for next_url in data.get('next_pages', []):
                if is_hm(next_url) and next_url not in seen_pages and next_url not in crawl_queue:
                    crawl_queue.append(next_url)
            
            save_seen(output_dir, url)
            page_count += 1
            
            # Polite delay
            time.sleep(random.uniform(args.sleep_min, args.sleep_max))
            
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            continue
    
    logger.info(f"Crawl completed: {page_count} pages, {download_count} downloads")

if __name__ == '__main__':
    main()
