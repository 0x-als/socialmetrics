from datetime import datetime
from database import init_database
from utils.logger import logger_config
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from scrapers import AuthorizationTelegram, authorizationvkontatke

route = APIRouter()


@route.get("/api/list/scrape_accounts")
async def api_list_scrape_accounts(request: Request):
    logger = logger_config(name="api_list_scrape_accounts", log_file="settings.log")

    try:

        scrape_accounts = await init_database.scrape_accounts_repo.get_scrape_accounts()
        return [{
            "id": a.id,
            "path": a.path,
            "type": a.type,
            "status": a.status
        } for a in scrape_accounts]

    except Exception as ex:
        logger.error(ex)
        return []


@route.post("/api/settings/scrape_account")
async def api_settings_scrape_account(request: Request):
    logger = logger_config(name="api_settings_scrape_account", log_file="settings.log")

    try:
        data = await request.json()
        platform = data.get("platform")
        fields = data.get("fields", {})
        if platform == "youtube":
            api_key = fields.get("api_key")

            created = await init_database.youtube_repo.create_session(api_key)
            return JSONResponse(
                {"status": True, "message": "YouTube аккаунт добавлен"}
                if created else
                {"status": False, "message": "Ошибка добавления YouTube"}
            )

        if platform == "telegram":
            phone = fields.get("phone")
            api_id = fields.get("api_id")
            api_hash = fields.get("api_hash")

            service = AuthorizationTelegram(phone, api_id, api_hash)
            request.app.state.tg_service = service

            await service.start()

            return JSONResponse({
                "status": "code_required",
                "message": "Введите код подтверждения"
            })

        if platform == "vk":
            client_id = fields.get("client_id")
            api_key = fields.get("api_key")

            quick_response, page, context, browser = await authorizationvkontatke._get_quick_response_code()

            if not quick_response:
                return JSONResponse({"status": False, "message": "QR not found"}, status_code=500)

            # сохраняем состояние VK‑авторизации
            request.app.state.vk_page = page
            request.app.state.vk_context = context
            request.app.state.vk_browser = browser
            request.app.state.vk_done = False

            request.app.state.vk_client_id = client_id
            request.app.state.vk_api_key = api_key

            return JSONResponse({
                "status": "quick_response",
                "quick_response": quick_response
            })

        return JSONResponse({"status": False, "message": "Unknown platform"}, status_code=400)

    except Exception as ex:
        logger.exception(ex)
        return JSONResponse({"status": False, "message": str(ex)}, status_code=500)


@route.post("/api/settings/scrape_account/vk/wait_login")
async def api_settings_scrape_account_wait_login(request: Request):
    logger = logger_config(name="api_settings_scrape_account_wait_login", log_file="settings.log")
    try:
        page = getattr(request.app.state, "vk_page", None)
        context = getattr(request.app.state, "vk_context", None)
        browser = getattr(request.app.state, "vk_browser", None)
        if not page or not context or not browser:
            return JSONResponse({"status": False, "message": "No active VK session"}, status_code=400)

        body = await request.json()
        client_id = body["client_id"]
        api_key = body["api_key"]

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        folder_name = f"user_{request.state.user.id}_{timestamp}"

        profile_path = await authorizationvkontatke._wait_for_login(page, context, browser, folder_name)

        request.app.state.vk_page = None
        request.app.state.vk_context = None
        request.app.state.vk_browser = None

        if not profile_path:
            return JSONResponse({"status": False, "message": "Login failed"}, status_code=500)

        created = await init_database.vkontakte_repo.create_session(
            client_id=client_id,
            api_key=api_key,
            profile_path=profile_path
        )

        if not created:
            return JSONResponse({"status": False, "message": "DB save failed"}, status_code=500)

        return JSONResponse({"status": True, "profile_path": profile_path})

    except Exception as ex:
        logger.exception(ex)
        return JSONResponse({"status": False, "message": str(ex)}, status_code=500)


@route.post("/api/settings/scrape_account/telegram/confirm")
async def api_settings_scrape_account_telegram_confirm(request: Request):
    data = await request.json()
    code = data["code"]

    service = request.app.state.tg_service
    result = await service.confirm_code(code)

    if result["status"] is True:

        if await init_database.telegram_repo.create_session(phone=service.phone, api_id=service.api_id, api_hash=service.api_hash):
            return JSONResponse({"status": True, "message": "Telegram успешно добавлен!"})
        else:
            return JSONResponse({"status": False, "message": "Не удалось сохранить telegram"}, status_code=400)

    if result["status"] == "password_required":
        return JSONResponse({"status": "password_required", "message": "Введите пароль от 2FA"})

    return JSONResponse({"status": False, "message": result.get("message")}, status_code=400)


@route.post("/api/settings/scrape_account/telegram/password")
async def api_settings_scrape_account_telegram_password(request: Request):
    data = await request.json()
    password = data["password"]

    service = request.app.state.tg_service

    try:
        await service.sign_in(password=password)
        await service.disconnect()

        if await init_database.telegram_repo.create_session(phone=service.phone, api_id=service.api_id, api_hash=service.api_hash):
            return JSONResponse({"status": True, "message": "Telegram успешно добавлен!"})
        else:
            return JSONResponse({"statu": False, "message": "Не удалось сохранить telegram"}, status_code=400)
    except Exception as ex:
        return JSONResponse({"status": False, "message": str(ex)})


@route.delete("/api/settings/scrape_account/delete")
async def api_settings_scrape_account_delete(request: Request):
    logger = logger_config(name="api_settings_scrape_account", log_file="settings.log")

    try:

        data = await request.json()
        scrape_account_id = data["id"]

        if scrape_account_id and await init_database.scrape_accounts_repo.delete_scrape_account(scrape_account_id):
            return JSONResponse({
                "status": True,
                "message": "Scrape-аккаунт успешно удален"
            }, status_code=200)

        else:
            return JSONResponse({
                "status": False,
                "message": "Не удалось удалить scrape-account"
            }, status_code=400)

    except Exception as ex:
        logger.exception(ex)
        return JSONResponse({
            "status": False,
            "message": "Ошибка сервера"
        }, status_code=500)
