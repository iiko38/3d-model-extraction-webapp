"""
Cloud deployment settings for Vercel + Supabase
"""

import os
from pathlib import Path
from typing import Optional

class CloudSettings:
    # Application settings
    APP_TITLE = "3D Model Library - Cloud Edition"
    APP_VERSION = "2.0.0"
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    # File Storage Configuration
    USE_CLOUD_STORAGE = os.getenv("USE_CLOUD_STORAGE", "true").lower() == "true"
    
    # Local file storage (for 3D files - remains local)
    # In Vercel, this will be a read-only path to uploaded files
    LOCAL_FILE_ROOT = Path(os.getenv("LOCAL_FILE_ROOT", "/var/task/library"))
    
    # Cloud storage settings
    CLOUD_STORAGE_BUCKET = os.getenv("CLOUD_STORAGE_BUCKET", "3d-model-images")
    
    # Security settings
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    
    # Performance settings
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "100000000"))  # 100MB
    
    # Database settings
    DB_CONNECTION_POOL_SIZE = int(os.getenv("DB_CONNECTION_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that all required environment variables are set"""
        required_vars = [
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {missing_vars}")
            return False
        
        print("✅ Cloud configuration validated successfully")
        return True
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get database connection URL for Supabase"""
        if not cls.SUPABASE_URL:
            raise ValueError("SUPABASE_URL not configured")
        
        # Extract database URL from Supabase URL
        # Format: https://project-ref.supabase.co
        # Database URL: postgresql://postgres:[password]@db.project-ref.supabase.co:5432/postgres
        project_ref = cls.SUPABASE_URL.split("//")[1].split(".")[0]
        return f"postgresql://postgres:{cls.SUPABASE_SERVICE_KEY}@db.{project_ref}.supabase.co:5432/postgres"

# Global settings instance
settings = CloudSettings()
