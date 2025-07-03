from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import pandas as pd
import os
from datetime import datetime
import asyncio
import requests
import io

from app.config import config

router = APIRouter()
current_dir = Path(__file__).parent.parent
templates = Jinja2Templates(directory=current_dir / "templates")

# Check if Vercel Blob is configured
BLOB_ENABLED = config.validate_blob_config()

if BLOB_ENABLED:
    from vercel_blob import put, list, delete
else:
    print("⚠ Vercel Blob not configured - admin features will be limited")

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

async def upload_to_vercel_blob(file_content: bytes, filename: str) -> str:
    """Upload file to Vercel Blob Storage"""
    try:
        blob = put(filename, file_content, {"access": "public", "allowOverwrite": True})
        return blob["url"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to cloud storage: {str(e)}")

async def download_from_vercel_blob(filename: str, local_path: str):
    """Download file from Vercel Blob Storage to local directory"""
    try:
        import vercel_blob
        blobs = vercel_blob.list()
        download_url = None
        for blob in blobs['blobs']:
            if blob['pathname'] == filename:
                download_url = blob['downloadUrl']
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
                download_url = blob['downloadUrl']
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
    """Upload Excel file to cloud storage"""
    
    # Admin authentication
    if admin_password != config.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    
    if not BLOB_ENABLED:
        raise HTTPException(status_code=503, detail="Vercel Blob not configured. Please set BLOB_READ_WRITE_TOKEN environment variable.")
    
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
        # Upload to Vercel Blob
        filename = config_excel["filename"]
        blob_url = await upload_to_vercel_blob(file_content, filename)
        
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
            "message": f"{config_excel['description']} updated successfully",
            "filename": filename,
            "rows_processed": len(pd.read_excel(io.BytesIO(file_content))),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/admin/status")
async def get_upload_status():
    """Get status of uploaded files"""
    if not BLOB_ENABLED:
        return JSONResponse({
            "error": "Vercel Blob not configured",
            "files": {file_type: {"filename": config["filename"], "uploaded": False, "description": config["description"]} 
                     for file_type, config in EXCEL_FILES.items()}
        })
    
    try:
        blobs = await list()
        uploaded_files = [blob.pathname for blob in blobs.blobs]
        
        status = {}
        for file_type, config in EXCEL_FILES.items():
            filename = config["filename"]
            status[file_type] = {
                "filename": filename,
                "uploaded": filename in uploaded_files,
                "description": config["description"]
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