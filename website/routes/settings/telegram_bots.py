from database import init_database
from telegram_bot.utils import get_telegram_bot_name, get_telegram_bot_username
from utils.logger import logger_config
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

route = APIRouter()


@route.post("/api/settings/telegram_bots/list")
async def api_telegram_bots_list(request: Request):
    logger = logger_config(name="api_telegram_bot_list", log_file="TelegramBots.log")

    try:
        bots = await init_database.telegram_bot_repo.get_telegram_bots()

        if bots is False:
            return JSONResponse({"status": False, "message": "Ошибка получения списка"})

        result = []
        for bot in bots:
            result.append({
                "id": bot.id,
                "bot_name": bot.bot_name,
                "url": bot.url,
                "status": bot.status,
                "created_at": str(bot.created_at),
                "updated_at": str(bot.updated_at)
            })

        return JSONResponse({"status": True, "bots": result})

    except Exception as ex:
        logger.exception(ex)
        return JSONResponse({"status": False, "message": str(ex)})


@route.post("/api/settings/telegram_bots/create")
async def api_telegram_bots_create(request: Request):
    logger = logger_config(name='telegram_bots_create', log_file="TelegramBots.log")
    try:
        data = await request.json()
        token = data["token"]
        bot_username = await get_telegram_bot_username(token)
        bot_name = await get_telegram_bot_name(token)

        if not token:
            return JSONResponse({
                "status": False,
                "message": "Токен не был получен"
            })

        created = await init_database.telegram_bot_repo.create_telegram_bot(token, bot_name, bot_username)

        if created:
            return JSONResponse({
                "status": True,
                "message": "Телеграм бот успешно добавлен",
                "name": bot_name
            })
        else:
            return JSONResponse({
                "status": False,
                "message": "Телеграм бот не был добавлен"
            })

    except Exception as ex:
        logger.error(ex)
        return JSONResponse({
            "status": False,
            "message": f"Техническая ошибка: {ex}"
        })


@route.delete("/api/settings/telegram_bot/delete")
async def api_telegram_bot_delete(request: Request):
    logger = logger_config(name='telegram_bot_delete', log_file="TelegramBots.log")

    try:

        data = await request.json()
        telegram_bot_id = data["id"]
        if telegram_bot_id and await init_database.telegram_bot_repo.delete_telegram_bot(telegram_bot_id):
            return JSONResponse({
                "status": True,
                "message": "Телеграм бот успешно удален"
            }, status_code=200)
        else:
            return JSONResponse({
                "status": False,
                "message": "Не получилось удалить телеграм бота"
            }, status_code=400)

    except Exception as ex:
        logger.exception(ex)
        return JSONResponse({
            "status": False,
            "message": "Ошибка сервера"
        }, status_code=500)
