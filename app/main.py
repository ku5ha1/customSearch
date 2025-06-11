from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

# Import routers
from routes import pdp_plp  

app = FastAPI()
router = APIRouter()

current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")

templates = Jinja2Templates(directory=current_dir / "templates")

@router.get("/")
async def homepage():
    return RedirectResponse(url="/pdp-plp")

# Include routers
app.include_router(router)          
app.include_router(pdp_plp.router)    
