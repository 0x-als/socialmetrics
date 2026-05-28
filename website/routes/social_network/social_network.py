from fastapi import APIRouter, Form, Request
from fastapi.openapi.utils import validation_error_response_definition
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse

from database import init_database
from utils.logger import logger_config
from website.core import templates
from utils import security

route = APIRouter()


@route.get("/social_network")
async def dashboard_page(request: Request):
    return templates.TemplateResponse(request=request, name="social_network.html")


@route.post("/api/social_networks/list")
async def get_social_networks(request: Request):
    logger = logger_config(name="social_networks_list", log_file="social_networks.log")

    try:
        token = request.cookies.get("token")
        session = await init_database.session_repo.get_session_by_token(token)
        user_id = session._user_id

        networks = await init_database.social_networks_repo.get_social_networks(user_id=user_id)

        return JSONResponse({
            "status": True,
            "networks": [
                {
                    "id": n.id,
                    "username": n.username,
                    "url": n.url,
                    "type": n.type,
                    "status": n.status,
                    "created_at": n.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(n, 'created_at') and n.created_at else None
                } for n in networks
            ]
        })

    except Exception as ex:
        logger.exception(ex)
        return JSONResponse({"status": False, "message": "Ошибка сервера"}, status_code=500)


@route.post("/api/social_networks/create")
async def api_social_networks_create(request: Request):
    logger = logger_config(name="social_networks_create", log_file="social_networks.log")

    try:

        data = await request.json()
        session = await init_database.session_repo.get_session_by_token(request.cookies.get("token"))
        user_id = session._user_id
        data["user_id"] = user_id

        if await init_database.social_networks_repo.create_social_network(data):
            return {"status": True, "message": "Социальная сеть успешно добавлена"}
        else:
            return {"status": False, "message": "Социальная не была добавлена"}

    except Exception as ex:
        logger.exception(ex)


@route.delete("/api/social_networks/delete")
async def api_social_networks_delete(request: Request):
    logger = logger_config(name="social_networks_delete", log_file="social_networks.log")
    try:

        data = await request.json()
        social_network_id = data["id"]
        if social_network_id:
            if await init_database.social_networks_repo.delete_social_network(social_network_id):
                return JSONResponse({
                    "status": True,
                    "message": "Соц. сеть успешно удалена!"
                })
            else:
                return JSONResponse({
                    "status": False,
                    "message": "Не удалось удалить соц. сеть!"
                })

        else:
            return JSONResponse({
                "status": False,
                "message": "ID не передан"
            }, status_code=400)

    except Exception as ex:
        logger.exception(ex)
        return JSONResponse({
            "status": False,
            "message": "Ошибка сервера"
        }, status_code=500)
