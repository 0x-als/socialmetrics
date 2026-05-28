import json
import os
import base64
from config import base_dir
from playwright.async_api import async_playwright
from utils.logger import logger_config


class AuthorizationVkontakte:
    def __init__(self):
        self._playwright = None
        self.log_file = "AuthorizationVkontakte.log"

    async def _create_browser(self):
        logger = logger_config(name="_create_browser", log_file=self.log_file)
        try:
            if self._playwright is None:
                self._playwright = await async_playwright().start()
            browser = await self._playwright.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ]
            )
            return browser
        except Exception as ex:
            logger.exception(ex)
            return None

    async def _new_context(self):
        logger = logger_config(name="_new_context", log_file=self.log_file)
        try:
            browser = await self._create_browser()
            if not browser:
                return None, None, None
            context = await browser.new_context(
                user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/121.0.6167.85 Safari/537.36"),
                viewport={"width": 1280, "height": 720},
                locale="en-US",
                java_script_enabled=True,
            )
            page = await context.new_page()
            return browser, context, page
        except Exception as ex:
            logger.exception(ex)
            return None, None, None

    async def _click_continue_if_exists(self, page):
        try:
            btn = await page.query_selector('text="Продолжить"')
            if btn:
                await btn.click()
                await page.wait_for_timeout(500)
        except:
            pass

    async def _get_quick_response_code(self):
        logger = logger_config(name="_get_quick_response_code", log_file=self.log_file)
        try:
            browser, context, page = await self._new_context()
            if not browser or not context or not page:
                return None, None, None, None
            await page.goto("https://vk.com")
            await self._click_continue_if_exists(page)
            await page.wait_for_selector('text="Sign in to VK"', timeout=20000)
            qr_bytes = await page.screenshot(type="png")
            qr_base64 = base64.b64encode(qr_bytes).decode()
            return f"data:image/png;base64,{qr_base64}", page, context, browser
        except Exception as ex:
            logger.exception(ex)
            return None, None, None, None

    async def _wait_for_login(self, page, context, browser, folder_name: str):
        logger = logger_config(name="_wait_for_login", log_file=self.log_file)
        try:
            logger.info("Ожидание завершения авторизации через QR-код...")
            await self._click_continue_if_exists(page)
            await page.wait_for_selector('text="Профиль"', timeout=240000)
            await self._click_continue_if_exists(page)
            await page.wait_for_function("""
                () => {
                    const profileLink = document.querySelector('a[href*="/id"]') || 
                                       document.querySelector('text="Профиль"');
                    return profileLink !== null;
                }
            """, timeout=30000)
            logger.info("Авторизация успешно завершена (найден пункт 'Профиль')")
            profile_path = await self.save_profile(context, folder_name)
            return profile_path
        except Exception as ex:
            logger.exception("Ошибка или таймаут при ожидании авторизации")
            try:
                await page.screenshot(path=f"vk_login_error_{folder_name}.png")
                logger.info(f"Скриншот ошибки сохранён: vk_login_error_{folder_name}.png")
            except:
                pass
            return None
        finally:
            try:
                if page and not page.is_closed():
                    await page.close()
            except:
                pass
            try:
                if context:
                    await context.close()
            except:
                pass
            try:
                if browser:
                    await browser.close()
            except:
                pass

    async def save_profile(self, context, folder_name: str):
        logger = logger_config(name="save_profile", log_file=self.log_file)
        try:
            profile_dir = os.path.join(base_dir, "files", "vk_profiles", folder_name)
            os.makedirs(profile_dir, exist_ok=True)
            cookies = await context.cookies()
            with open(os.path.join(profile_dir, "cookies.json"), "w", encoding="UTF-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=4)
            storage = await context.storage_state()
            with open(os.path.join(profile_dir, "storage.json"), "w", encoding="UTF-8") as f:
                json.dump(storage, f, ensure_ascii=False, indent=4)
            return folder_name
        except Exception as ex:
            logger.exception(ex)
            return None