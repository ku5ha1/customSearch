from fastapi import APIRouter, Request, Form, Response, Depends
from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import pandas as pd
import re
import math
import hashlib
from datetime import datetime
import io
import requests
from fastapi.security import HTTPBasic

from app.config import config

router = APIRouter()
current_dir = Path(__file__).parent.parent
DATA_FILE = current_dir.parent / "data" / "category_tree.xlsx"
templates = Jinja2Templates(directory=current_dir / "templates")

# Check if Vercel Blob is configured
BLOB_ENABLED = config.validate_blob_config()
if BLOB_ENABLED:
    print("⚠ Vercel Blob not configured - Category Tree will use local files only")

SEARCH_COLUMNS = [
    "l0_category_id", "l0_category", "l1_category_id", "l1_category", "l2_category_id", "l2_category"
]

# Data file cache (in-memory)
DATA_CACHE = None
DATA_CACHE_TIMESTAMP = 0
DATA_CACHE_TTL = 600  # seconds (10 minutes)

# Helper to clean NaN for JSON
def clean_data_for_json(data):
    if isinstance(data, dict):
        return {k: clean_data_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_data_for_json(v) for v in data]
    elif isinstance(data, float) and math.isnan(data):
        return None
    return data

# Helper to generate cache key
def generate_cache_key(query: str) -> str:
    return hashlib.md5(f"category_tree_search_{query.lower().strip()}".encode()).hexdigest()

# Load data from Vercel Blob or local file
async def load_data():
    global DATA_CACHE, DATA_CACHE_TIMESTAMP
    now = datetime.now().timestamp()
    # Check if data is cached and not expired
    if DATA_CACHE is not None and (now - DATA_CACHE_TIMESTAMP) < DATA_CACHE_TTL:
        return DATA_CACHE
    try:
        if BLOB_ENABLED:
            try:
                import vercel_blob
                blobs = vercel_blob.list()
                download_url = None
                for blob in blobs['blobs']:
                    if blob['pathname'] == 'category_tree.xlsx':
                        download_url = blob.get('downloadUrl') or blob.get('url')
                        break
                if download_url:
                    response = requests.get(download_url)
                    response.raise_for_status()
                    df = pd.read_excel(io.BytesIO(response.content), header=0)
                    df = df.where(pd.notnull(df), None)
                    data = df.to_dict(orient="records")
                    print(f"[Category Tree] Data loaded from Vercel Blob at {datetime.now()}")
                    # Cache the data
                    DATA_CACHE = data
                    DATA_CACHE_TIMESTAMP = now
                    return data
                else:
                    print(f"[Category Tree] File not found in Vercel Blob.")
            except Exception as e:
                print(f"[Category Tree] Failed to load from Vercel Blob: {e}")
        if DATA_FILE.exists():
            df = pd.read_excel(DATA_FILE, header=0)
            df = df.where(pd.notnull(df), None)
            data = df.to_dict(orient="records")
            print(f"[Category Tree] Data loaded from local file at {datetime.now()}")
            # Cache the data
            DATA_CACHE = data
            DATA_CACHE_TIMESTAMP = now
            return data
        else:
            print(f"[Category Tree] Warning: Data file not found at {DATA_FILE}")
            return []
    except Exception as e:
        print(f"[Category Tree] Warning: Failed to load data: {e}")
        return []

# Routes
@router.get("/category-tree", response_class=HTMLResponse)
async def category_tree_home(request: Request):
    return templates.TemplateResponse("category_tree.html", {"request": request})

@router.post("/category-tree/search")
async def category_tree_search(request: Request, response: Response, query: str = Form(...)):
    print(f"[Category Tree] Search query: '{query}' @ {datetime.now()}")

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    query = query.strip()
    if not query:
        return JSONResponse({"error": "Query cannot be empty"}, status_code=400)

    # Load data (from Blob or local file)
    data = await load_data()

    # Check cache first
    from app.main import search_cache
    cache_key = generate_cache_key(query)
    cached_result = search_cache.get(cache_key)
    
    if cached_result:
        print(f"[Category Tree] Cache hit for query '{query}'")
        return JSONResponse(cached_result)

    # Perform search if not in cache
    query_words = query.lower().split()
    results = []

    for row in data:
        row_text = ' '.join(str(row[col]).lower() for col in SEARCH_COLUMNS if col in row and row[col] is not None)
        if all(word in row_text for word in query_words):
            matches = {col: row[col] for col in SEARCH_COLUMNS if col in row and row[col] is not None and any(word in str(row[col]).lower() for word in query_words)}
            results.append({
                "row_data": clean_data_for_json(row),
                "matched_columns": matches
            })

    result_data = {
        "query": query,
        "results": results,
        "total_matches": len(results),
        "timestamp": datetime.now().isoformat(),
        "cached": False
    }

    # Cache the result
    search_cache.set(cache_key, result_data)
    print(f"[Category Tree] Found {len(results)} matches for query '{query}' (cached)")

    return JSONResponse(result_data)
