import hmac
import hashlib

from utils import security
from fastapi import Request
from database import init_database
from utils.logger import logger_config
from fastapi.responses import RedirectResponse
from datetime import datetime, timezone, timedelta


async def middleware(request: Request, call_next):
    logger = logger_config(name="access_page", log_file="middleware.log")

    try:
        path = request.url.path

        # Пути, доступные без авторизации
        public_paths = ["/", "/api/login/authorization"]

        # Статика всегда доступна
        if path.startswith("/static"):
            return await call_next(request)

        # Публичные пути
        if path in public_paths:
            return await call_next(request)

        # Получаем токен
        token = request.cookies.get("token")
        if not token:
            return RedirectResponse("/")

        # Проверяем подпись токена
        try:
            raw, signature = token.split(".")
        except ValueError:
            return RedirectResponse("/")

        expected = hmac.new(
            key=security.key,
            msg=raw.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected):
            return RedirectResponse("/")

        # Ищем сессию в БД
        session = await init_database.session_repo.get_session_by_token(token)
        if not session:
            return RedirectResponse("/")

        now = datetime.now(timezone.utc)

        # Проверяем срок действия
        if session.expires_at < now:
            return RedirectResponse("/")

        # Сколько осталось времени
        time_left = session.expires_at - now

        # Если осталось меньше 30 минут — продлеваем
        if time_left < timedelta(minutes=30):
            new_expires_at = now + timedelta(hours=12)
            await init_database.session_repo.update_session(session.id, new_expires_at)

            # ВАЖНО: загружаем пользователя
            request.state.user = await init_database.users_repo.get_user_by_id(session._user_id)

            # Продлеваем cookie
            response = await call_next(request)
            response.set_cookie(
                key="token",
                value=token,
                httponly=True,
                max_age=60 * 60 * 24 * 12,
                samesite="lax"
            )
            return response

        # Если продлевать не нужно — просто загружаем пользователя
        request.state.user = await init_database.users_repo.get_user_by_id(session._user_id)

        return await call_next(request)

    except Exception as ex:
        logger.exception(ex)
        return RedirectResponse("/")
