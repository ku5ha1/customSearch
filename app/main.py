from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from pathlib import Path
import time
from collections import OrderedDict
from typing import Dict, Any, Optional

from routes import pdp_plp, attributes, concat_rule, category_tree, rejections, ptypes_dump

# Simple in-memory cache with TTL
class SimpleCache:
    def __init__(self, max_size: int = 100, ttl: int = 300):  # 5 minutes TTL
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl:
                # Move to end (LRU)
                self.cache.move_to_end(key)
                return self.cache[key]
            else:
                # Expired, remove
                del self.cache[key]
                del self.timestamps[key]
        return None
    
    def set(self, key: str, value: Any):
        if key in self.cache:
            # Update existing
            self.cache.move_to_end(key)
        else:
            # Add new
            if len(self.cache) >= self.max_size:
                # Remove oldest
                oldest = next(iter(self.cache))
                del self.cache[oldest]
                del self.timestamps[oldest]
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def clear(self):
        self.cache.clear()
        self.timestamps.clear()
    
    def get_stats(self):
        current_time = time.time()
        active_entries = sum(1 for ts in self.timestamps.values() if current_time - ts < self.ttl)
        return {
            "total_entries": len(self.cache),
            "active_entries": active_entries,
            "max_size": self.max_size,
            "ttl_seconds": self.ttl
        }

# Global cache instance
search_cache = SimpleCache(max_size=200, ttl=600)  # 10 minutes TTL, 200 entries

app = FastAPI()
router = APIRouter()

current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")
templates = Jinja2Templates(directory=current_dir / "templates")

@router.get("/")
async def homepage():
    return RedirectResponse(url="/pdp-plp")

@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics for monitoring"""
    return JSONResponse(search_cache.get_stats())

@router.post("/cache/clear")
async def clear_cache():
    """Clear all cached search results"""
    search_cache.clear()
    return JSONResponse({"message": "Cache cleared successfully", "timestamp": time.time()})

app.include_router(router)
app.include_router(pdp_plp.router)     
app.include_router(attributes.router)  
app.include_router(concat_rule.router)
app.include_router(category_tree.router)
app.include_router(rejections.router)
app.include_router(ptypes_dump.router)
