from fastapi import APIRouter, Form, Request
from fastapi.openapi.utils import validation_error_response_definition
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse

from database import init_database
from utils.logger import logger_config
from website.core import templates
from utils import security

route = APIRouter()

@route.get("/dashboard")
async def dashboard_page(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")