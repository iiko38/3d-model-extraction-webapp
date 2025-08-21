#!/usr/bin/env python3
"""
URL Health Checker for 3D Warehouse
HEAD-checks unique URLs and updates url_health status
"""

import sqlite3
import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('url_health.log'),
        logging.StreamHandler()
    ]
)

class URLHealthChecker:
    def __init__(self, db_path="library/index.sqlite", max_workers=10, timeout=10):
        self.db_path = db_path
        self.max_workers = max_workers
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': '3D-Warehouse-URL-Checker/1.0'
        })
        
    def get_unique_urls(self):
        """Get all unique URLs from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT thumbnail_url, product_url 
            FROM files 
            WHERE thumbnail_url IS NOT NULL OR product_url IS NOT NULL
        """)
        
        urls = set()
        for row in cursor.fetchall():
            if row[0]:  # thumbnail_url
                urls.add(row[0])
            if row[1]:  # product_url
                urls.add(row[1])
        
        conn.close()
        return list(urls)
    
    def check_url_health(self, url):
        """Check if a URL is healthy using HEAD request."""
        if not url or not url.strip():
            return url, 'unknown'
        
        try:
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            
            if response.status_code == 200:
                return url, 'healthy'
            elif response.status_code in [301, 302, 307, 308]:
                return url, 'healthy'  # Redirects are considered healthy
            elif response.status_code == 404:
                return url, 'broken'
            elif response.status_code >= 500:
                return url, 'broken'
            else:
                return url, 'unknown'
                
        except requests.exceptions.Timeout:
            return url, 'timeout'
        except requests.exceptions.ConnectionError:
            return url, 'broken'
        except requests.exceptions.RequestException:
            return url, 'broken'
        except Exception as e:
            logging.error(f"Error checking {url}: {e}")
            return url, 'unknown'
    
    def update_url_health(self, url_results):
        """Update the database with URL health results."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updated_count = 0
        for url, health_status in url_results:
            if health_status in ['healthy', 'broken', 'timeout']:
                cursor.execute("""
                    UPDATE files 
                    SET url_health = ? 
                    WHERE thumbnail_url = ? OR product_url = ?
                """, (health_status, url, url))
                updated_count += cursor.rowcount
        
        conn.commit()
        conn.close()
        logging.info(f"Updated {updated_count} file records with URL health status")
    
    def update_files_status(self):
        """Update files.status based on url_health."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Set status to 'archived' for files with broken URLs
        cursor.execute("""
            UPDATE files 
            SET status = 'archived' 
            WHERE url_health = 'broken' AND status = 'active'
        """)
        archived_count = cursor.rowcount
        
        # Set status to 'active' for files with healthy URLs
        cursor.execute("""
            UPDATE files 
            SET status = 'active' 
            WHERE url_health = 'healthy' AND status = 'archived'
        """)
        activated_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logging.info(f"Archived {archived_count} files with broken URLs")
        logging.info(f"Activated {activated_count} files with healthy URLs")
    
    def run_health_check(self):
        """Run the complete URL health check process."""
        logging.info("Starting URL health check...")
        
        # Get unique URLs
        urls = self.get_unique_urls()
        logging.info(f"Found {len(urls)} unique URLs to check")
        
        if not urls:
            logging.info("No URLs to check")
            return
        
        # Check URLs in parallel
        url_results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self.check_url_health, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    url, health_status = future.result()
                    url_results.append((url, health_status))
                    logging.info(f"{url}: {health_status}")
                except Exception as e:
                    logging.error(f"Error checking {url}: {e}")
                    url_results.append((url, 'unknown'))
        
        # Update database
        self.update_url_health(url_results)
        self.update_files_status()
        
        # Print summary
        health_counts = {}
        for _, status in url_results:
            health_counts[status] = health_counts.get(status, 0) + 1
        
        logging.info("URL Health Check Summary:")
        for status, count in health_counts.items():
            logging.info(f"  {status}: {count}")
        
        logging.info("URL health check completed!")

def main():
    """Main function to run URL health check."""
    checker = URLHealthChecker()
    checker.run_health_check()

if __name__ == "__main__":
    main()
