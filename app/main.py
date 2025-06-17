from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pathlib import Path

from routes import pdp_plp, attributes, concat_rule, category_tree, rejections, ptypes_dump

app = FastAPI()
router = APIRouter()

current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")
templates = Jinja2Templates(directory=current_dir / "templates")

@router.get("/")
async def homepage():
    return RedirectResponse(url="/pdp-plp")

app.include_router(router)
app.include_router(pdp_plp.router)     
app.include_router(attributes.router)  
app.include_router(concat_rule.router)
app.include_router(category_tree.router)
app.include_router(rejections.router)
app.include_router(ptypes_dump.router)
