# Custom Search App

A minimal FastAPI app to search data loaded from Excel into SQLite.

## Setup

1. Create and activate a virtual environment
   - Windows (Git Bash):
     - `python -m venv .venv && source .venv/Scripts/activate`
2. Install dependencies
   - `pip install -r requirements.txt`
3. Prepare the database (reads Excel files in `data/` and creates `data/custom_search.db`)
   - `python setup_database.py`

## Run

- Development server:
  - `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Open: `http://localhost:8000`

## Key Pages

- `/pdp-plp` – Category PDP/PLP search
- `/attributes` – Attributes search
- `/ptypes-dump` – Product types search
- `/concat-rule` – Concat rule search
- `/category-tree` – Category tree search
- `/rejections` – Rejection reasons search
- `/color-code` – Color code search
- `/rms-manufacturer-brand` – RMS Manufacturer/Brand search
- `/magazine` – Magazine search (brand_name, l2_category, ptype)

## Admin

- Upload/replace Excel files via the admin UI: `/admin`
- After uploads, data is written to SQLite and used by the app.

## Health & Cache

- Health check: `/health`
- Cache stats: `/cache/stats`
- Clear cache: `POST /cache/clear`


