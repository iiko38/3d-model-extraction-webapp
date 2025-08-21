# 3D Model Library Web App

A lightweight FastAPI web application for browsing and managing your 3D model library.

## Features

- **Product Browsing**: List and search products with filters by brand, category, and text search
- **Product Details**: View product information and files grouped by variants
- **File Downloads**: Secure file downloads with path validation
- **Statistics**: Library overview with file type breakdowns and largest files
- **HTMX Integration**: Dynamic search and filtering without page reloads
- **Responsive Design**: Works on desktop and mobile with Tailwind CSS

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app**:
   ```bash
   python run_app.py
   ```

3. **Open your browser**:
   Navigate to http://127.0.0.1:8000

## Project Structure

```
app/
├── __init__.py          # Package initialization
├── main.py             # FastAPI app and routes
├── db.py               # Database connection and queries
├── settings.py         # Configuration and paths
├── viewmodels.py       # Pydantic models
├── templates/          # Jinja2 HTML templates
│   ├── base.html
│   ├── products_list.html
│   ├── products_list_partial.html
│   ├── product_detail.html
│   ├── stats.html
│   └── 404.html
└── static/
    └── styles.css      # Custom CSS styles
```

## Database Schema

The app expects a SQLite database (`library/index.sqlite`) with:

- `products` table: product_uid, brand, name, slug, category
- `files` table: product_uid, sha256, variant, file_type, ext, stored_path, size_bytes, source_url

## Security Features

- **Path Validation**: All file downloads are validated to prevent directory traversal
- **Library Root**: Files can only be accessed from within the library directory
- **SHA256 Lookup**: Files are served by hash, not direct path access

## Development

- **Auto-reload**: The app includes hot reloading for development
- **HTMX**: Dynamic updates without full page reloads
- **Tailwind CSS**: Utility-first CSS framework via CDN
- **Responsive**: Mobile-friendly design

## API Endpoints

- `GET /` - Main products listing with search/filters
- `GET /products` - HTMX endpoint for filtered results
- `GET /product/{product_uid}` - Product detail page
- `GET /stats` - Library statistics
- `GET /download/{sha256}` - File download by hash

## Customization

- Modify `app/settings.py` for database paths and app configuration
- Update `app/static/styles.css` for custom styling
- Add new routes in `app/main.py`
- Extend database queries in `app/db.py`
