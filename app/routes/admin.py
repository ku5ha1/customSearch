from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import pandas as pd
import os
import sqlite3
from datetime import datetime
import asyncio
import requests
import io

from app.config import config

router = APIRouter()
current_dir = Path(__file__).parent.parent
templates = Jinja2Templates(directory=current_dir / "templates")

# Database file path
DB_FILE = current_dir.parent / "data" / "custom_search.db"

# Excel file configurations
EXCEL_FILES = {
    "attributes": {
        "filename": "attributes.xlsx",
        "required_columns": ["AttributeID", "AttributeName", "Source", "2"],
        "description": "Attributes data"
    },
    "category_pdp_plp": {
        "filename": "category_pdp_plp.xlsx",
        "required_columns": ["L0_category", "L1_category", "L1_category_id", "L2_category", "L2_category_id"],
        "description": "Category PDP/PLP data"
    },
    "concat_rule": {
        "filename": "concat_rule.xlsx",
        "required_columns": ["Category Name", "L1", "L2", "Concat Rule"],
        "description": "Concat rule data"
    },
    "category_tree": {
        "filename": "category_tree.xlsx",
        "required_columns": ["l0_category_id", "l0_category", "l1_category_id", "l1_category", "l2_category_id", "l2_category"],
        "description": "Category tree data"
    },
    "rejection_reasons": {
        "filename": "rejection_reasons.xlsx",
        "required_columns": ["Reason", "Justification"],
        "description": "Rejection reasons data"
    },
    "ptypes_dump": {
        "filename": "ptypes_dump.xlsx",
        "required_columns": ["ptype_id", "ptype_name"],
        "description": "Product types data"
    },
    "color_code": {
        "filename": "colour_code.xlsx",
        "required_columns": ["Color Name", "Hex Code"],
        "description": "Color code data"
    },
    "rms_manufacturer_brand": {
        "filename": "rms_manufacturer_brand.xlsx",
        "required_columns": ["MfgID", "MfgName", "BrandID", "BrandName"],
        "description": "RMS Manufacturer Brand data"
    }
}

def validate_excel_file(file_content: bytes, required_columns: list) -> bool:
    """Validate Excel file structure"""
    try:
        # Read Excel file
        df = pd.read_excel(io.BytesIO(file_content), header=0)
        
        # Convert column names to strings for comparison
        df_columns = [str(col) for col in df.columns]
        required_columns_str = [str(col) for col in required_columns]
        
        print(f"Debug: Found columns: {df_columns}")
        print(f"Debug: Required columns: {required_columns_str}")
        
        # Check if required columns exist
        missing_columns = []
        for col in required_columns_str:
            if col not in df_columns:
                missing_columns.append(col)
        
        if missing_columns:
            return False, f"Missing required columns: {missing_columns}. Found columns: {df_columns}"
        
        # Check if file has data
        if len(df) == 0:
            return False, "Excel file is empty"
        
        return True, f"Valid file with {len(df)} rows"
    except Exception as e:
        return False, f"Error reading Excel file: {str(e)}"

async def update_sqlite_table(file_type: str, file_content: bytes):
    """Update SQLite table with new Excel data (REPLACE existing)"""
    
    # Map file types to table names
    table_mapping = {
        "attributes": "attributes",
        "category_pdp_plp": "category_pdp_plp", 
        "concat_rule": "concat_rule",
        "category_tree": "category_tree",
        "rejection_reasons": "rejection_reasons",
        "ptypes_dump": "ptypes_dump",
        "color_code": "color_codes",
        "rms_manufacturer_brand": "rms_manufacturer_brands"
    }
    
    table_name = table_mapping.get(file_type)
    if not table_name:
        raise ValueError(f"Unknown file type: {file_type}")
    
    # Read Excel data
    df = pd.read_excel(io.BytesIO(file_content))
    
    # Connect to SQLite database
    with sqlite3.connect(DB_FILE) as conn:
        # DELETE existing data (same as current "replace" behavior)
        conn.execute(f"DELETE FROM {table_name}")
        
        # INSERT new data
        df.to_sql(table_name, conn, if_exists='append', index=False)
        
        # Commit changes
        conn.commit()
        
        print(f"✓ Updated {table_name} table with {len(df)} rows")

async def download_from_vercel_blob(filename: str, local_path: str):
    """Download file from Vercel Blob Storage to local directory"""
    try:
        import vercel_blob
        blobs = vercel_blob.list()
        download_url = None
        for blob in blobs['blobs']:
            if blob['pathname'] == filename:
                download_url = blob.get('downloadUrl') or blob.get('url')
                break
        if download_url:
            response = requests.get(download_url)
            response.raise_for_status()
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(response.content)
            return True
        else:
            print(f"Failed to find {filename} in Vercel Blob.")
            return False
    except Exception as e:
        print(f"Failed to download {filename}: {str(e)}")
        return False

async def download_all_files_from_blob():
    """Download all Excel files from Vercel Blob Storage to local directory"""
    data_dir = current_dir.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    success_count = 0
    total_count = len(EXCEL_FILES)
    
    for file_type, config in EXCEL_FILES.items():
        filename = config["filename"]
        local_path = data_dir / filename
        
        try:
            success = await download_from_vercel_blob(filename, str(local_path))
            if success:
                success_count += 1
                print(f"✓ Downloaded {filename}")
            else:
                print(f"⚠ Failed to download {filename}")
        except Exception as e:
            print(f"⚠ Error downloading {filename}: {str(e)}")
    
    print(f"Downloaded {success_count}/{total_count} files from Vercel Blob")
    return success_count

async def get_file_content_from_blob(filename: str) -> bytes:
    """Get file content directly from Vercel Blob Storage"""
    try:
        import vercel_blob
        blobs = vercel_blob.list()
        download_url = None
        for blob in blobs['blobs']:
            if blob['pathname'] == filename:
                download_url = blob.get('downloadUrl') or blob.get('url')
                break
        if download_url:
            response = requests.get(download_url)
            response.raise_for_status()
            return response.content
        else:
            print(f"Failed to find {filename} in Vercel Blob.")
            return None
    except Exception as e:
        print(f"Failed to get {filename} from blob: {str(e)}")
        return None

@router.get("/admin", response_class=HTMLResponse)
async def admin_home(request: Request):
    """Admin dashboard page"""
    return templates.TemplateResponse("admin.html", {"request": request, "files": EXCEL_FILES})

@router.post("/admin/upload/{file_type}")
async def upload_excel_file(
    file_type: str,
    file: UploadFile = File(...),
    admin_password: str = Form(...)
):
    """Upload Excel file and update SQLite database"""
    
    # Admin authentication
    if admin_password != config.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    
    if file_type not in EXCEL_FILES:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Validate file type
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Only .xlsx files are allowed")
    
    # Read file content
    file_content = await file.read()
    
    # Validate Excel structure
    config_excel = EXCEL_FILES[file_type]
    is_valid, message = validate_excel_file(file_content, config_excel["required_columns"])
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    try:
        # Update SQLite database (REPLACE existing data)
        await update_sqlite_table(file_type, file_content)
        
        # Clear cache (import here to avoid circular import)
        from app.main import search_cache
        search_cache.clear()
        # Invalidate in-memory data cache for the relevant route
        if file_type == "attributes":
            import app.routes.attributes as mod
            mod.DATA_CACHE = None
            mod.DATA_CACHE_TIMESTAMP = 0
        elif file_type == "category_pdp_plp":
            import app.routes.pdp_plp as mod
            mod.DATA_CACHE = None
            mod.DATA_CACHE_TIMESTAMP = 0
        elif file_type == "concat_rule":
            import app.routes.concat_rule as mod
            mod.DATA_CACHE = None
            mod.DATA_CACHE_TIMESTAMP = 0
        elif file_type == "category_tree":
            import app.routes.category_tree as mod
            mod.DATA_CACHE = None
            mod.DATA_CACHE_TIMESTAMP = 0
        elif file_type == "rejection_reasons":
            import app.routes.rejections as mod
            mod.DATA_CACHE = None
            mod.DATA_CACHE_TIMESTAMP = 0
        elif file_type == "ptypes_dump":
            import app.routes.ptypes_dump as mod
            mod.DATA_CACHE = None
            mod.DATA_CACHE_TIMESTAMP = 0
        return JSONResponse({
            "success": True,
            "message": f"{config_excel['description']} updated successfully in database",
            "filename": config_excel["filename"],
            "rows_processed": len(pd.read_excel(io.BytesIO(file_content))),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database update failed: {str(e)}")

@router.get("/admin/status")
async def get_upload_status():
    """Get status of database tables"""
    try:
        status = {}
        
        if DB_FILE.exists():
            with sqlite3.connect(DB_FILE) as conn:
                # Get list of tables
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = [row[0] for row in cursor.fetchall()]
                
                for file_type, config in EXCEL_FILES.items():
                    table_name = file_type.replace('_', '')  # Simple mapping
                    if file_type == "category_pdp_plp":
                        table_name = "category_pdp_plp"
                    elif file_type == "concat_rule":
                        table_name = "concat_rule"
                    elif file_type == "category_tree":
                        table_name = "category_tree"
                    elif file_type == "rejection_reasons":
                        table_name = "rejection_reasons"
                    elif file_type == "ptypes_dump":
                        table_name = "ptypes_dump"
                    elif file_type == "attributes":
                        table_name = "attributes"
                    
                    # Check if table exists and has data
                    table_exists = table_name in existing_tables
                    row_count = 0
                    if table_exists:
                        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                        row_count = cursor.fetchone()[0]
                    
                    status[file_type] = {
                        "filename": config["filename"],
                        "uploaded": table_exists and row_count > 0,
                        "description": config["description"],
                        "row_count": row_count
                    }
        else:
            # Database doesn't exist yet
            for file_type, config in EXCEL_FILES.items():
                status[file_type] = {
                    "filename": config["filename"],
                    "uploaded": False,
                    "description": config["description"],
                    "row_count": 0
                }
        
        return JSONResponse(status)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.post("/admin/clear-cache")
async def clear_cache_endpoint(admin_password: str = Form(...)):
    """Clear search cache"""
    if admin_password != config.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    
    from app.main import search_cache
    search_cache.clear()
    
    return JSONResponse({
        "success": True,
        "message": "Cache cleared successfully",
        "timestamp": datetime.now().isoformat()
    }) 
