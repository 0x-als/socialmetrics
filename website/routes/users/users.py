from fastapi import APIRouter, Form, Request
from fastapi.openapi.utils import validation_error_response_definition
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse

from database import init_database
from utils.logger import logger_config
from website.core import templates
from utils import security

route = APIRouter()


@route.get("/api/users/list")
async def api_users_list(request: Request):
    logger = logger_config(name="api_users_list", log_file="Users.log")

    try:

        users = await init_database.users_repo.get_all_users()

        return JSONResponse({
            "status": True,
            "users": [
                {
                    "id": u.id,
                    "login": u.login,
                    "email": u.email
                } for u in users
            ]
        })

    except Exception as ex:
        logger.exception(ex)
        return JSONResponse({"status": False, "message": "Ошибка сервера"}, status_code=500)