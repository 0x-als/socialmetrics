from database import init_database
from utils.logger import logger_config
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

route = APIRouter()


@route.get("/api/settings/proxies/list")
async def api_settings_proxies_list(request: Request):
    logger = logger_config(name="api_settings_proxies_list", log_file="proxies.log")

    try:
        proxies = await init_database.proxies_repo.get_proxies()

        if proxies is False:
            return JSONResponse({
                "status": False,
                "message": "Ошибка получения прокси"
            })

        result = []
        for proxy in proxies:
            result.append({
                "id": proxy.id,
                "login": proxy.login,
                "host": proxy.host,
                "port": proxy.port,
                "status": proxy.status,
                "created_at": proxy.created_at.isoformat() if proxy.created_at else None,
            })

        return JSONResponse({
            "status": True,
            "proxies": result
        })

    except Exception as ex:
        logger.exception(ex)
        return JSONResponse({
            "status": False,
            "message": str(ex)
        })


@route.post("/api/settings/proxies/create")
async def api_settings_proxies_create(request: Request):
    logger = logger_config(name="api_settings_proxies_create", log_file="proxies.log")
    try:
        content_type = request.headers.get("content-type", "")

        if "multipart/form-data" in content_type:
            form = await request.form()
            file = form.get("file")
            if not file:
                return JSONResponse({"status": False, "message": "Файл не найден"}, status_code=400)

            content = await file.read()
            text = content.decode("utf-8-sig")

            lines = [line.strip() for line in text.splitlines() if line.strip()]
            header = lines[0].replace(",", ";").split(";")

            if len(header) < 4:
                return JSONResponse({"status": False, "message": "Неверный формат файла"}, status_code=400)

            proxies_list = []
            for row in lines[1:]:
                parts = row.replace(",", ";").split(";")
                if len(parts) < 4:
                    continue
                proxies_list.append({
                    "login": parts[0] or None,
                    "password": parts[1] or None,
                    "host": parts[2],
                    "port": parts[3]
                })

        else:
            data = await request.json()
            proxies_list = data.get("proxies")
            if not proxies_list:
                proxies_list = [data]

        if not proxies_list:
            return JSONResponse({"status": False, "message": "Нет данных"}, status_code=400)

        created_count = await init_database.proxies_repo.create_proxies(proxies_list)

        return JSONResponse({
            "status": True,
            "added": created_count,
            "message": f"Успешно добавлено {created_count} прокси"
        })

    except Exception as ex:
        logger.exception(ex)
        return JSONResponse({"status": False, "message": "Внутренняя ошибка сервера"}, status_code=500)


@route.delete("/api/settings/proxies/delete")
async def api_settings_proxies_delete(request: Request):
    logger = logger_config(name="api_settings_proxies_delete", log_file="proxies.log")

    try:
        data = await request.json()
        proxy_id = data["id"]

        if not proxy_id:
            return JSONResponse({
                "status": False,
                "message": "ID прокси не передан"
            }, status_code=400)

        deleted = await init_database.proxies_repo.delete_proxy(proxy_id)

        if deleted:
            return JSONResponse({
                "status": True,
                "message": "Прокси успешно удалён"
            })
        else:
            return JSONResponse({
                "status": False,
                "message": "Прокси не найден или уже удалён"
            })

    except Exception as ex:
        logger.exception(ex)
        return JSONResponse({
            "status": False,
            "message": "Внутренняя ошибка сервера"
        }, status_code=500)
