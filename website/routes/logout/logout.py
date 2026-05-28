from database import init_database
from utils.logger import logger_config
from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse

route = APIRouter()


@route.get("/logout")
async def logout(request: Request):
    logger = logger_config(name="logout", log_file="logout.log")

    try:

        token = request.cookies.get("token")
        if token:
            await init_database.session_repo.delete_session_by_token(token)

        response = RedirectResponse(url="/")
        response.delete_cookie("token")

        return response

    except Exception as ex:
        logger.exception(ex)
