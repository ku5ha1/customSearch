from fastapi import APIRouter, Request, Form, Response, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import pandas as pd
import math
import hashlib
from datetime import datetime
import sqlite3
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

from app.config import config

router = APIRouter()
current_dir = Path(__file__).parent.parent
DB_FILE = current_dir.parent / "data" / "custom_search.db"
templates = Jinja2Templates(directory=current_dir / "templates")

SEARCH_COLUMNS = ["MfgID", "MfgName", "BrandID", "BrandName"]

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

def generate_cache_key(query: str) -> str:
    return hashlib.md5(f"rms_manufacturer_brand_search_{query.lower().strip()}".encode()).hexdigest()

async def load_data():
    global DATA_CACHE, DATA_CACHE_TIMESTAMP
    now = datetime.now().timestamp()
    if DATA_CACHE is not None and (now - DATA_CACHE_TIMESTAMP) < DATA_CACHE_TTL:
        return DATA_CACHE
    try:
        if DB_FILE.exists():
            with sqlite3.connect(DB_FILE) as conn:
                query = "SELECT * FROM rms_manufacturer_brands"
                df = pd.read_sql_query(query, conn)
                df = df.where(pd.notnull(df), None)
                data = df.to_dict(orient="records")
                DATA_CACHE = data
                DATA_CACHE_TIMESTAMP = now
                return data
        else:
            print(f"[RMS Manufacturer Brand] Warning: Database file not found at {DB_FILE}")
            return []
    except Exception as e:
        print(f"[RMS Manufacturer Brand] Warning: Failed to load data: {e}")
        return []

@router.get("/rms-manufacturer-brand", response_class=HTMLResponse)
async def rms_manufacturer_brand_home(request: Request):
    return templates.TemplateResponse("rms_manufacturer_brand.html", {"request": request})

@router.post("/rms-manufacturer-brand/search")
async def rms_manufacturer_brand_search(request: Request, response: Response, query: str = Form(...)):
    print(f"[RMS Manufacturer Brand] Search query: '{query}' @ {datetime.now()}")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    query = query.strip()
    if not query:
        return JSONResponse({"error": "Query cannot be empty"}, status_code=400)
    data = await load_data()
    from app.main import search_cache
    cache_key = generate_cache_key(query)
    cached_result = search_cache.get(cache_key)
    if cached_result:
        print(f"[RMS Manufacturer Brand] Cache hit for query '{query}'")
        return JSONResponse(cached_result)
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
    search_cache.set(cache_key, result_data)
    print(f"[RMS Manufacturer Brand] Found {len(results)} matches for query '{query}' (cached)")
    return JSONResponse(result_data)

@router.get("/rms-manufacturer-brand/db-status")
async def db_status(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != "admin" or credentials.password != config.ADMIN_PASSWORD:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"cache_timestamp": DATA_CACHE_TIMESTAMP, "db_file_exists": DB_FILE.exists()} 