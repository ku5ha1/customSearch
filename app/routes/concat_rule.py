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
DATA_FILE = current_dir.parent / "data" / "concat_rule.xlsx"
templates = Jinja2Templates(directory=current_dir / "templates")

# Check if Vercel Blob is configured
BLOB_ENABLED = config.validate_blob_config()
if BLOB_ENABLED:
    print("⚠ Vercel Blob not configured - Concat Rule will use local files only")

SEARCH_COLUMNS = [
    "Category Name", "L1", "L2", "Concat Rule"
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
    return hashlib.md5(f"concat_rule_search_{query.lower().strip()}".encode()).hexdigest()

# Load data from Vercel Blob or local file
async def load_data():
    global DATA_CACHE, DATA_CACHE_TIMESTAMP, LAST_BLOB_READ
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
                    if blob['pathname'] == 'concat_rule.xlsx':
                        download_url = blob['downloadUrl']
                        break
                if download_url:
                    print(f"[Concat Rule] BLOB READ at {datetime.now()}")
                    LAST_BLOB_READ = datetime.now().isoformat()
                    response = requests.get(download_url)
                    response.raise_for_status()
                    df = pd.read_excel(io.BytesIO(response.content), header=0)
                    df = df.where(pd.notnull(df), None)
                    data = df.to_dict(orient="records")
                    print(f"[Concat Rule] Data loaded from Vercel Blob at {datetime.now()}")
                    # Cache the data
                    DATA_CACHE = data
                    DATA_CACHE_TIMESTAMP = now
                    return data
                else:
                    print(f"[Concat Rule] File not found in Vercel Blob.")
            except Exception as e:
                print(f"[Concat Rule] Failed to load from Vercel Blob: {e}")
        if DATA_FILE.exists():
            df = pd.read_excel(DATA_FILE, header=0)
            df = df.where(pd.notnull(df), None)
            data = df.to_dict(orient="records")
            print(f"[Concat Rule] Data loaded from local file at {datetime.now()}")
            # Cache the data
            DATA_CACHE = data
            DATA_CACHE_TIMESTAMP = now
            return data
        else:
            print(f"[Concat Rule] Warning: Data file not found at {DATA_FILE}")
            return []
    except Exception as e:
        print(f"[Concat Rule] Warning: Failed to load data: {e}")
        return []

# Routes
@router.get("/concat-rule", response_class=HTMLResponse)
async def concat_rule_home(request: Request):
    return templates.TemplateResponse("concat_rule.html", {"request": request})

@router.post("/concat-rule/search")
async def concat_rule_search(request: Request, response: Response, query: str = Form(...)):
    print(f"[Concat Rule] Search query: '{query}' @ {datetime.now()}")

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
        print(f"[Concat Rule] Cache hit for query '{query}'")
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
    print(f"[Concat Rule] Found {len(results)} matches for query '{query}' (cached)")

    return JSONResponse(result_data)

# Monitoring endpoint
security = HTTPBasic()
@router.get("/concat-rule/blob-status")
async def blob_status(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != "admin" or credentials.password != config.ADMIN_PASSWORD:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"last_blob_read": LAST_BLOB_READ, "cache_timestamp": DATA_CACHE_TIMESTAMP}
