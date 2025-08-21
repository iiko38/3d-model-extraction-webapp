# 3D Model Library Web App

A FastAPI-based web application for browsing and managing a 3D model library stored in SQLite.

## Features

- Browse products with search and filtering
- View product details with file variants
- Download files securely
- View library statistics
- HTMX-powered dynamic updates
- JSON API endpoints

## Setup

1. Install dependencies:
```bash
pip install fastapi uvicorn jinja2 pydantic
```

2. Configure settings in `app/settings.py`:
   - `DB_PATH`: Path to SQLite database (default: `library/index.sqlite`)
   - `LIB_ROOT`: Path to library root directory (default: `./library`)

3. Run the application:
```bash
uvicorn app.main:app --reload
```

4. Open your browser to `http://127.0.0.1:8000`

## Usage

- **Products List**: Browse and search products with filters
- **Product Details**: View files grouped by variant and type
- **File Downloads**: Secure downloads with path validation
- **Statistics**: View library coverage and metrics

## JSON API

The app also provides JSON API endpoints:

- `GET /api/products` - List products with filtering
- `GET /api/products/{product_uid}` - Get product details
- `GET /api/stats` - Get library statistics

## Security

- File downloads are sandboxed to `LIB_ROOT`
- Path validation prevents directory traversal
- No authentication (local use only)

## Platform Support

- Works on Windows, macOS, and Linux
- No build step required
- Uses CDN for Tailwind CSS and HTMX

## File Structure

```
app/
├── __init__.py
├── main.py           # FastAPI app + routes
├── db.py             # SQLite connection helpers
├── settings.py       # paths, config
├── viewmodels.py     # Pydantic response models
├── templates/        # Jinja2 templates
└── static/          # Static files
```

## Configuration

Edit `app/settings.py` to customize:
- Database path
- Library root directory
- App title and version
