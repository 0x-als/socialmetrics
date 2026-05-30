import platform
import subprocess
import json
import requests
import asyncio

from utils import security
from utils.logger import logger_config
from database import init_database


class ScraperInstagramURL:
    def __init__(self):
        self.log_file = "ScraperInstagramURL.log"
        self.base_url = "https://i.instagram.com/api/v1/users/web_profile_info/"
        self.proxies = []
        self.urls = []
        self.failed_urls = []

        self.time_sleep = 20

        if platform.system() == "Windows":
            self.curl_base = ["wsl", "curl"]
        else:
            self.curl_base = ["curl"]

    async def _load_proxies(self):
        logger = logger_config(name="_load_proxies", log_file=self.log_file)

        try:

            proxies = await init_database.proxies_repo.get_proxies_true()
            if not proxies:
                logger.warning("No work proxies found!")
                self.proxies = []
                return

            proxies_active = [p for p in proxies if p.status]
            logger.info(f"Active proxies loaded: {len(proxies_active)}")

            self.proxies = proxies_active
            return self.proxies

        except Exception as ex:
            logger.exception(ex)

    async def _load_urls(self):
        logger = logger_config(name="_load_urls", log_file=self.log_file)

        try:

            urls = await init_database.instagram_repo.get_instagram_accounts()
            if not urls:
                logger.warning("No work urls found!")
                self.urls = []
                return

            urls_active = [u for u in urls if u.status]

            logger.info(f"Active urls loaded: {len(urls_active)}")
            self.urls = urls_active
            return self.urls

        except Exception as ex:
            logger.exception(ex)

    async def _build_proxy(self, data_proxy):
        logger = logger_config(name="_build_proxy", log_file=self.log_file)
        proxy_list = []
        try:

            for proxy in data_proxy:
                proxy_id = proxy.id
                login = proxy.login
                host = proxy.host
                port = proxy.port
                password = await security.decrypt(proxy.password_hash)

                proxy_list.append({"id": proxy_id, "proxy": f"http://{login}:{password}@{host}:{port}"})

            return proxy_list

        except Exception as ex:
            logger.exception(ex)

    async def _find_followers(self, stdout):
        logger = logger_config(name="_find_followers", log_file=self.log_file)

        try:
            # Если пришёл JSON-строка — парсим
            if isinstance(stdout, str):
                data = json.loads(stdout)
            elif isinstance(stdout, dict):
                data = stdout
            else:
                logger.warning(f"Unexpected type: {type(stdout)}")
                return None

            # Безопасный спуск по структуре
            if isinstance(data, dict) and "data" in data:
                user = data["data"].get("user")
                if user and isinstance(user, dict):
                    edge = user.get("edge_followed_by")
                    if edge and isinstance(edge, dict) and "count" in edge:
                        return edge["count"]

                    # Дополнительные варианты (на всякий случай)
                    if "followers_count" in user:
                        return user["followers_count"]
                    if "edge_followed_by" in user and isinstance(user["edge_followed_by"], int):
                        return user["edge_followed_by"]

            logger.warning("Followers count not found in response")
            return None

        except json.JSONDecodeError as ex:
            logger.error(f"JSON decode error: {ex}")
        except Exception as ex:
            logger.exception(ex)

        return None

    async def _find_shortcode(self, stdout):
        logger = logger_config(name="_find_shortcode", log_file=self.log_file)

        try:
            if isinstance(stdout, str):
                data = json.loads(stdout)
            elif isinstance(stdout, dict):
                data = stdout
            else:
                logger.warning(f"Unexpected type for shortcode search: {type(stdout)}")
                return []

            result = []

            def extract_shortcodes(obj):
                """Рекурсивная функция для поиска всех shortcode"""
                if isinstance(obj, dict):
                    if "shortcode" in obj and isinstance(obj["shortcode"], str):
                        result.append(obj["shortcode"])

                    for value in obj.values():
                        extract_shortcodes(value)

                elif isinstance(obj, list):
                    for item in obj:
                        extract_shortcodes(item)

            extract_shortcodes(data)

            unique_shortcodes = list(dict.fromkeys(result))

            logger.info(f"Found {len(unique_shortcodes)} shortcodes")
            return unique_shortcodes

        except json.JSONDecodeError as ex:
            logger.error(f"JSON decode error in _find_shortcode: {ex}")
        except Exception as ex:
            logger.exception(ex)

        return []

    async def _fetch_webprofile(self, url: str, proxy_string: str = None):
        logger = logger_config(name="_fetch_metadata", log_file=self.log_file)

        try:
            username = url.split("/")[-2]

            cmd = self.curl_base + [
                "-s",
                f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}",
                "-H", "User-Agent: Instagram 155.0.0.37.107",
                "-H", "X-IG-App-ID: 936619743392459",
                "-H", "Accept-Language: en-US,en;q=0.9",
                "-H", "Accept: */*"
            ]

            if proxy_string:
                cmd.extend(["-x", proxy_string])

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            stdout = process.stdout.strip()
            return stdout

        except Exception as ex:
            logger.exception(ex)

    async def run(self):
        logger = logger_config(name="run", log_file=self.log_file)

        self.urls = await self._load_urls()
        self.proxies = await self._load_proxies()
        self.proxies = await self._build_proxy(self.proxies)

        try:
            if not self.proxies:
                logger.warning("No work proxies found!")
                self.failed_urls = list(self.urls)
            else:
                for i, url_object in enumerate(self.urls):
                    url = url_object.url

                    current_proxy_data = self.proxies[i % len(self.proxies)]
                    proxy_string = current_proxy_data["proxy"]
                    proxy_id = current_proxy_data["id"]

                    try:

                        result = await self._fetch_webprofile(url=url, proxy_string=proxy_string)
                        followers = await self._find_followers(result)
                        shortcode = await self._find_shortcode(result)
                        print(followers, len(shortcode))
                        logger.info(f"Sleep {str(self.time_sleep)} seconds")
                        await asyncio.sleep(self.time_sleep)

                    except Exception as ex:
                        logger.exception(ex)

            if self.failed_urls:
                logger.info(f"Repeat request for main IP machine.")

                url = url_object.url
                result = await self._fetch_webprofile(url=url, proxy_string=None)

        except Exception as ex:
            logger.exception(ex)


async def main():
    scraper_instagram_url = ScraperInstagramURL()
    await scraper_instagram_url.run()


asyncio.run(main())
