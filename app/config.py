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
            print("⚠ Warning: BLOB_READ_WRITE_TOKEN not set. Vercel Blob features will be disabled.")
            return False
        return True

# Global config instance
config = Config() 