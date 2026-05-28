import json
import asyncio
from config import base_dir
from playwright.async_api import async_playwright

PROFILE_DIR = "files/vk_profiles/user_1"
COOKIES_PATH = f"{base_dir}/{PROFILE_DIR}/cookies.json"
STORAGE_PATH = f"{base_dir}/{PROFILE_DIR}/storage.json"


async def run():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)

        # Загружаем cookies
        with open(COOKIES_PATH, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        # Загружаем localStorage/sessionStorage
        with open(STORAGE_PATH, "r", encoding="utf-8") as f:
            storage = json.load(f)

        # Создаём контекст с загруженными данными
        context = await browser.new_context(
            storage_state=storage,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.6167.85 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 720},
            locale="ru-RU",
        )

        # Устанавливаем cookies вручную (Playwright требует отдельного вызова)
        await context.add_cookies(cookies)

        page = await context.new_page()

        # Открываем VK
        await page.goto("https://vk.com/feed")

        print("Профиль загружен. Если всё ок — вы должны быть авторизованы.")

        await page.wait_for_timeout(60000)  # держим окно 60 сек


if __name__ == "__main__":
    asyncio.run(run())
