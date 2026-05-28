from fastapi import APIRouter, Form, Request
from fastapi.openapi.utils import validation_error_response_definition
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse

from database import init_database
from utils.logger import logger_config
from website.core import templates
from utils import security

route = APIRouter()


@route.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@route.post("/api/login/authorization")
async def api_login_authorization(request: Request):
    logger = logger_config(name="api_login_authorization", log_file="login.log")

    try:

        data = await request.json()
        login = data["login"]
        password = data["password"]
        user = await init_database.users_repo.get_user_login(login)

        if user:
            verify_password = await security.verify(password, user.password_hash)

            if verify_password:
                token = security.generate_session_token(user.id)

                if token["status"]:
                    if await init_database.session_repo.create_session(user.id, token):
                        response = JSONResponse(
                            {
                                "status": True,
                            }
                        )
                        response.set_cookie(
                            key="token",
                            value=token["token"],
                            httponly=True,
                            max_age=60 * 60 * 24 * 12,
                            samesite="lax"
                        )
                        return response
            else:
                return JSONResponse({
                    "status": False,
                    "message": "Incorrect login or password"
                })
        else:
            return JSONResponse({
                "status": False,
                "message": "Incorrect login or password"
            })

    except Exception as ex:
        logger.exception(ex)
