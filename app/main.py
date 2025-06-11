from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pandas as pd
from pathlib import Path
import re
import math
from datetime import datetime

app = FastAPI()

# Configuration
current_dir = Path(__file__).parent
DATA_FILE = current_dir.parent / "data" / "sheet_6.xlsx"
SEARCH_COLUMNS = [
    "L0_category", "L1_category", "L1_category_id", 
    "L2_category", "L2_category_id",
    "PDP1", "PDP2", "PDP3", "PDP4", "PDP5", "PDP6", 
    "PDP7", "PDP8", "PDP9", "PDP10", "PDP11",
    "PLP1", "PLP2", "PLP3", "PLP4"
]

# Custom JSON encoder to handle NaN values
def clean_data_for_json(data):
    if isinstance(data, dict):
        return {k: clean_data_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_data_for_json(v) for v in data]
    elif isinstance(data, float) and math.isnan(data):
        return None
    return data

# Load data
try:
    df = pd.read_excel(DATA_FILE, header=0)
    # Convert NaN values to None before converting to dict
    df = df.where(pd.notnull(df), None)
    data = df.to_dict(orient="records")
    print(f"Data loaded successfully at {datetime.now()}")
except Exception as e:
    raise RuntimeError(f"Failed to load data: {str(e)}")

# Setup templates and static files
templates = Jinja2Templates(directory=current_dir / "templates")
app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "placeholder": "Category_PDP_PLP"
    })

@app.post("/search")
async def search(request: Request, response: Response, query: str = Form(...)):
    print(f"Search request received for: '{query}' at {datetime.now()}")
    
    # Disable caching
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
                cell_value = str(row[col])
                if pattern.search(cell_value):
                    matches[col] = cell_value
        
        if matches:
            results.append({
                "row_data": clean_data_for_json(row),
                "matched_columns": matches
            })

    print(f"Found {len(results)} matches for '{query}'")
    return JSONResponse({
        "query": query,
        "results": results,
        "total_matches": len(results),
        "timestamp": datetime.now().isoformat()
    })