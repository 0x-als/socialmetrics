import os
import json
import base64
import aiohttp

from config import base_dir
from playwright.async_api import async_playwright

from database import init_database
from utils import security
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


class GetTokenVkontakte:

    """
    Before parsing starts, it will go through all the sessions and update the tokens.
    """

    def __init__(self):
        self.log_file = "GetTokenVkontakte.log"
        self.sessions = None

    async def get_token(self, id, client_id, api_key, path):
        logger = logger_config(name="get_token", log_file=self.log_file)

        try:

            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(
                    headless=False,
                )
                with open(f"{base_dir}/files/vk_profiles/{path}/cookies.json", "r", encoding="UTF-8") as f:
                    cookies = json.load(f)

                with open(f"{base_dir}/files/vk_profiles/{path}/storage.json", "r", encoding="UTF-8") as f:
                    storage = json.load(f)

                context = await browser.new_context(storage_state=storage)
                await context.add_cookies(cookies)

                page = await context.new_page()

                await page.goto("https://vk.com", wait_until="domcontentloaded")
                await page.wait_for_timeout(5000)

                try:
                    await page.locator("text=Профиль").wait_for(timeout=25000)
                    logger.info(f"VK profile: {id} - logged in")
                except Exception as ex:
                    logger.warning(f"VK profile: {id} - not logged in\n{ex}")

                oauth_rul = (
                    f"https://oauth.vk.com/authorize?"
                    f"client_id={client_id}&"
                    f"display=page&"
                    f"redirect_uri=https://oauth.vk.com/blank.html&"
                    f"scope=video,wall,groups&"
                    f"response_type=token&"
                    f"v=5.199"
                )

                logger.info(f"Redirecting to: {oauth_rul[:120]}")

                await page.goto(oauth_rul)
                logger.info("Waiting button: Разрешить")

                try:
                    warning = page.locator("text=Пожалуйста, не копируйте данные из адресной строки для сторонних сайтов. Таким образом Вы можете потерять доступ к Вашему аккаунту.")

                    if await warning.count() > 0:
                        logger.info("Detected warning - not clicked button: 'Разрешить'")
                    else:
                        await page.locator("button:has-text('Разрешить')").wait_for(timeout=25000)
                        await page.locator("button:has-text('Разрешить')").click()
                        logger.info(f"Button 'Разрешить' clicked")

                except Exception as ex:
                    logger.exception(ex)

                try:

                    await page.wait_for_url("https://oauth.vk.com/blank.html*", timeout=90000)
                    logger.info("Redirecting to: 'https://oauth.vk.com/blank.html' completed")

                except Exception as ex:
                    logger.exception(ex)

                try:

                    hash_value = await page.evaluate("window.location.hash")
                    logger.debug(f"GET hash: {hash_value[:80]}{'...' if len(hash_value) > 80 else ''}")

                    if "access_token" in hash_value:
                        logger.info("Found access token in URL")
                        parts = hash_value.lstrip("#").split("&")
                        token_dict = dict(p.split("=") for p in parts if "=" in p)
                        token = token_dict.get("access_token")
                        if token:
                            token_hash = await security.encrypt(token)
                            if token_hash:
                                await page.goto("https://vk.com/feed")
                                await page.locator("text=Профиль").wait_for(timeout=25000)
                                logger.info(f"VK profile: {id} - logged in")

                                if await init_database.vkontakte_repo.update_token_hash(id, token_hash):
                                    logger.info("Saved access token")
                                else:
                                    logger.error("Failed to get access token")
                            else:
                                logger.error(f"Failed request for access token")

                    if "code=" in hash_value:
                        logger.info("found code in URL -> request token")
                        code = hash_value.replace("#code", "").split("&")[0]

                        token_url = (
                            f"https://oauth.vk.com/access_token?"
                            f"client_id={client_id}"
                            f"client_secret={api_key}&"
                            f"redirect_uri=https://oauth.vk.com/blank.html&"
                            f"code={code}"
                        )

                        async with aiohttp.ClientSession() as http:
                            async with http.get(token_url, ssl=False) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    token = data["access_token"]

                                    if token:
                                        token_hash = await security.encrypt(token)
                                        if token_hash:
                                            logger.info("Found access token in URL")
                                            await page.goto("https://vk.com/feed")
                                            await page.locator("text=Профиль").wait_for(timeout=25000)
                                            logger.info(f"VK profile: {id} - logged in")

                                            if await init_database.vkontakte_repo.update_token_hash(id, token_hash):
                                                logger.info("Saved access token")
                                    else:
                                        logger.error("Failed to get access token")
                                else:
                                    logger.error(f"Failed request for access token: {response.status}")

                except Exception as ex:
                    logger.exception(ex)

        except Exception as ex:
            logger.exception(ex)
        finally:
            await browser.close()

    async def run(self):
        logger = logger_config(name="run", log_file=self.log_file)

        try:

            self.sessions = await init_database.vkontakte_repo.get_sessions()

            for session in self.sessions:
                id = session.id
                client_id = await security.decrypt(session.client_id)
                api_key = await security.decrypt(session.api_key)
                path = session.path

                await self.get_token(id, client_id, api_key, path)

        except Exception as ex:
            logger.exception(ex)