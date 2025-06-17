from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import pandas as pd
import re
import math
from datetime import datetime

router = APIRouter()
current_dir = Path(__file__).parent.parent
DATA_FILE = current_dir.parent / "data" / "category_tree.xlsx"
templates = Jinja2Templates(directory=current_dir / "templates")

SEARCH_COLUMNS = [
    "l0_category_id", "l0_category", "l1_category_id", "l1_category", "l2_category_id", "l2_category"
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

# Load Excel on module load
try:
    df = pd.read_excel(DATA_FILE, header=0)
    df = df.where(pd.notnull(df), None)
    data = df.to_dict(orient="records")
    print(f"[Category Tree] Data loaded successfully at {datetime.now()}")
except Exception as e:
    raise RuntimeError(f"Failed to load category tree data: {e}")

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

    print(f"[Category Tree] Found {len(results)} matches for query '{query}'")
    return JSONResponse({
        "query": query,
        "results": results,
        "total_matches": len(results),
        "timestamp": datetime.now().isoformat()
    })
