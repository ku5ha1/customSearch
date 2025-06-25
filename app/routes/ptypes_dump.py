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

from app.config import config

router = APIRouter()
current_dir = Path(__file__).parent.parent
DATA_FILE = current_dir.parent / "data" / "ptypes_dump.xlsx"
templates = Jinja2Templates(directory=current_dir / "templates")

# Check if Vercel Blob is configured
BLOB_ENABLED = config.validate_blob_config()
if BLOB_ENABLED:
    print("⚠ Vercel Blob not configured - Ptypes Dump will use local files only")

SEARCH_COLUMNS = [
    "ptype_id", "ptype_name"
]

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
    return hashlib.md5(f"ptypes_dump_search_{query.lower().strip()}".encode()).hexdigest()

# Load data from Vercel Blob or local file
async def load_data():
    try:
        if BLOB_ENABLED:
            try:
                import vercel_blob
                blobs = vercel_blob.list()
                download_url = None
                for blob in blobs['blobs']:
                    if blob['pathname'] == 'ptypes_dump.xlsx':
                        download_url = blob.get('downloadUrl') or blob.get('url')
                        break
                if download_url:
                    response = requests.get(download_url)
                    response.raise_for_status()
                    df = pd.read_excel(io.BytesIO(response.content), sheet_name='PTypes Dump', header=0)
                    df = df.where(pd.notnull(df), None)
                    data = df.to_dict(orient="records")
                    print(f"[Ptypes Dump] Data loaded from Vercel Blob at {datetime.now()}")
                    return data
                else:
                    print(f"[Ptypes Dump] File not found in Vercel Blob.")
            except Exception as e:
                print(f"[Ptypes Dump] Failed to load from Vercel Blob: {e}")
        if DATA_FILE.exists():
            df = pd.read_excel(DATA_FILE, sheet_name='PTypes Dump', header=0)
            df = df.where(pd.notnull(df), None)
            data = df.to_dict(orient="records")
            print(f"[Ptypes Dump] Data loaded from local file at {datetime.now()}")
            return data
        else:
            print(f"[Ptypes Dump] Warning: Data file not found at {DATA_FILE}")
            return []
    except Exception as e:
        print(f"[Ptypes Dump] Warning: Failed to load data: {e}")
        return []

# Routes
@router.get("/ptypes-dump", response_class=HTMLResponse)
async def ptypes_dump_home(request: Request):
    return templates.TemplateResponse("ptypes_dump.html", {"request": request})

@router.post("/ptypes-dump/search")
async def ptypes_dump_search(request: Request, response: Response, query: str = Form(...)):
    print(f"[Ptypes Dump] Search query: '{query}' @ {datetime.now()}")

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
        print(f"[Ptypes Dump] Cache hit for query '{query}'")
        return JSONResponse(cached_result)

    # Perform search if not in cache
    query_words = query.lower().split()
    results = []

    for row in data:
        matches = {}
        for col in SEARCH_COLUMNS:
            if col in row and row[col] is not None:
                cell_text = str(row[col]).lower()
                if all(word in cell_text for word in query_words):
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
    print(f"[Ptypes Dump] Found {len(results)} matches for query '{query}' (cached)")

    return JSONResponse(result_data)
