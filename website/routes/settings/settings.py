from datetime import datetime
from database import init_database
from website.core import templates
from utils.logger import logger_config
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from scrapers import authorizationvkontatke

route = APIRouter()


@route.get("/settings")
async def settings_page(request: Request):
    return templates.TemplateResponse(request=request, name="settings.html")
