import os
from typing import Optional

class Config:
    """Application configuration"""
    
    # Vercel Blob Storage configuration
    BLOB_READ_WRITE_TOKEN: Optional[str] = os.getenv("BLOB_READ_WRITE_TOKEN")
    
    # Admin configuration
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")  # Change this in production
    
    # App configuration
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    @classmethod
    def validate_blob_config(cls) -> bool:
        """Validate that Vercel Blob is properly configured"""
        if not cls.BLOB_READ_WRITE_TOKEN:
            print(f"⚠ Warning: BLOB_READ_WRITE_TOKEN not set. Vercel Blob features will be disabled. (Current value: {cls.BLOB_READ_WRITE_TOKEN})")
            return False
        print(f"✓ BLOB_READ_WRITE_TOKEN is set. Length: {len(cls.BLOB_READ_WRITE_TOKEN)}")
        return True

    @classmethod
    def debug_print(cls):
        print(f"BLOB_READ_WRITE_TOKEN: {cls.BLOB_READ_WRITE_TOKEN}")
        print(f"ADMIN_PASSWORD: {cls.ADMIN_PASSWORD}")
        print(f"DEBUG: {cls.DEBUG}")

    @classmethod
    def reload_env(cls):
        cls.BLOB_READ_WRITE_TOKEN = os.getenv("BLOB_READ_WRITE_TOKEN")
        cls.ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
        cls.DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Global config instance
config = Config() 