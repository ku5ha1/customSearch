from fastapi import APIRouter, Request, Form, Response, Depends
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
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config import config

router = APIRouter()
current_dir = Path(__file__).parent.parent
DATA_FILE = current_dir.parent / "data" / "rejection_reasons.xlsx"
templates = Jinja2Templates(directory=current_dir / "templates")

# Check if Vercel Blob is configured
BLOB_ENABLED = config.validate_blob_config()
if BLOB_ENABLED:
    print("⚠ Vercel Blob not configured - Rejections will use local files only")

SEARCH_COLUMNS = [
    "Reason", "Justification"
]

# Data file cache (in-memory)
DATA_CACHE = None
DATA_CACHE_TIMESTAMP = 0
DATA_CACHE_TTL = 600  # seconds (10 minutes)
LAST_BLOB_READ = None

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
    return hashlib.md5(f"rejections_search_{query.lower().strip()}".encode()).hexdigest()

# Load data from Vercel Blob or local file
async def load_data():
    global DATA_CACHE, DATA_CACHE_TIMESTAMP, LAST_BLOB_READ
    now = datetime.now().timestamp()
    # Check if data is cached and not expired
    if DATA_CACHE is not None and (now - DATA_CACHE_TIMESTAMP) < DATA_CACHE_TTL:
        return DATA_CACHE
    try:
        print(f"[Rejections] BLOB_ENABLED: {BLOB_ENABLED}")
        if BLOB_ENABLED:
            try:
                import vercel_blob
                blobs = vercel_blob.list()
                print(f"[Rejections] Blobs found: {[b['pathname'] for b in blobs['blobs']]}")
                download_url = None
                for blob in blobs['blobs']:
                    if blob['pathname'] == 'rejection_reasons.xlsx':
                        download_url = blob['downloadUrl']
                        break
                if download_url:
                    print(f"[Rejections] BLOB READ at {datetime.now()}")
                    LAST_BLOB_READ = datetime.now().isoformat()
                    response = requests.get(download_url)
                    response.raise_for_status()
                    df = pd.read_excel(io.BytesIO(response.content), header=0)
                    df = df.where(pd.notnull(df), None)
                    data = df.to_dict(orient="records")
                    print(f"[Rejections] Data loaded from Vercel Blob at {datetime.now()}")
                    # Cache the data
                    DATA_CACHE = data
                    DATA_CACHE_TIMESTAMP = now
                    return data
                else:
                    print(f"[Rejections] File not found in Vercel Blob. Filenames available: {[b['pathname'] for b in blobs['blobs']]}")
            except Exception as e:
                print(f"[Rejections] Failed to load from Vercel Blob: {e}")
        if DATA_FILE.exists():
            df = pd.read_excel(DATA_FILE, header=0)
            df = df.where(pd.notnull(df), None)
            data = df.to_dict(orient="records")
            print(f"[Rejections] Data loaded from local file at {datetime.now()}")
            # Cache the data
            DATA_CACHE = data
            DATA_CACHE_TIMESTAMP = now
            return data
        else:
            print(f"[Rejections] Warning: Data file not found at {DATA_FILE}")
            return []
    except Exception as e:
        print(f"[Rejections] Warning: Failed to load data: {e}")
        return []

# Routes
@router.get("/rejections", response_class=HTMLResponse)
async def rejections_home(request: Request):
    return templates.TemplateResponse("rejections.html", {"request": request})

@router.post("/rejections/search")
async def rejections_search(request: Request, response: Response, query: str = Form(...)):
    print(f"[Rejections] Search query: '{query}' @ {datetime.now()}")

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
        print(f"[Rejections] Cache hit for query '{query}'")
        return JSONResponse(cached_result)

    # Perform search if not in cache
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    results = []

    for row in data:
        matches = {}
        for col in SEARCH_COLUMNS:
            if col in row and row[col] is not None:
                if pattern.search(str(row[col])):
                    matches[col] = row[col]
        if matches:
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
    print(f"[Rejections] Found {len(results)} matches for query '{query}' (cached)")

    return JSONResponse(result_data)

# Monitoring endpoint
@router.get("/rejections/blob-status")
async def blob_status(credentials: HTTPBasicCredentials = Depends(HTTPBasic())):
    if credentials.username != "admin" or credentials.password != config.ADMIN_PASSWORD:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"last_blob_read": LAST_BLOB_READ, "cache_timestamp": DATA_CACHE_TIMESTAMP}
