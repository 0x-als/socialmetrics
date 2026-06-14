import os
import json
import asyncio
import platform
import subprocess

from utils import security
from database import init_database
from datetime import datetime, UTC
from utils.logger import logger_config


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

                proxy_list.append({
                    "id": proxy_id,
                    "proxy": f"http://{login}:{password}@{host}:{port}"
                })

            return proxy_list

        except Exception as ex:
            logger.exception(ex)

    async def _find_followers(self, stdout):
        try:
            if isinstance(stdout, str):
                data = json.loads(stdout)
            else:
                data = stdout

            if isinstance(data, dict) and "data" in data:
                user = data["data"].get("user")

                if user:
                    edge = user.get("edge_followed_by")
                    if edge and "count" in edge:
                        return edge["count"]

                    if "followers_count" in user:
                        return user["followers_count"]

            return None

        except Exception:
            return None

    async def _find_shortcode(self, stdout):
        try:
            if isinstance(stdout, str):
                data = json.loads(stdout)
            else:
                data = stdout

            result = []

            def extract(obj):
                if isinstance(obj, dict):
                    if "shortcode" in obj and isinstance(obj["shortcode"], str):
                        result.append(obj["shortcode"])

                    for v in obj.values():
                        extract(v)

                elif isinstance(obj, list):
                    for item in obj:
                        extract(item)

            extract(data)
            return list(dict.fromkeys(result))

        except Exception:
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

            try:
                return json.loads(stdout)
            except:
                return stdout

        except Exception as ex:
            logger.exception(ex)

    async def run(self):
        logger = logger_config(name="run", log_file=self.log_file)

        self.urls = await self._load_urls()
        self.proxies = await self._load_proxies()
        self.proxies = await self._build_proxy(self.proxies)

        storage = []

        try:
            if not self.proxies:
                logger.warning("No work proxies found!")
                self.failed_urls = list(self.urls)

            else:
                for i, url_object in enumerate(self.urls):
                    id = url_object.id
                    url = url_object.url

                    logger.info(f"Processing URL: {url}")

                    success = False

                    for proxy_data in self.proxies:
                        proxy_string = proxy_data["proxy"]

                        logger.info(f"Trying proxy: {proxy_string}")

                        try:
                            result = await self._fetch_webprofile(url=url, proxy_string=proxy_string)

                            if isinstance(result, dict) and result.get("status") == "fail":
                                logger.warning(f"Proxy failed for {url}")
                                continue

                            followers = await self._find_followers(result)
                            shortcodes = await self._find_shortcode(result)

                            logger.info(f"Followers: {followers}")
                            logger.info(f"Shortcodes: {len(shortcodes)}")
                            logger.info(f"Success via proxy: {proxy_string}")

                            storage.append([{
                                "id": id,
                                "url": url,
                                "followers": followers,
                                "shortcodes": shortcodes
                            }])

                            success = True
                            break

                        except Exception as ex:
                            logger.exception(ex)
                            continue

                    if not success:
                        logger.info(f"All proxies failed for {url}, trying main IP")

                        try:
                            result = await self._fetch_webprofile(url=url, proxy_string=None)

                            if isinstance(result, dict) and result.get("status") == "fail":
                                logger.warning(f"Main IP failed for {url}")
                                self.failed_urls.append(url_object)
                                continue

                            followers = await self._find_followers(result)
                            shortcodes = await self._find_shortcode(result)

                            logger.info(f"Followers: {followers}")
                            logger.info(f"Shortcodes: {len(shortcodes)}")
                            logger.info("Success via main IP")

                            storage.append([{
                                "id": id,
                                "url": url,
                                "followers": followers,
                                "shortcodes": shortcodes
                            }])

                        except Exception as ex:
                            logger.exception(ex)
                            self.failed_urls.append(url_object)
                            continue

                    if i != len(self.urls) - 1:
                        logger.info(f"Sleep {self.time_sleep} seconds")
                        await asyncio.sleep(self.time_sleep)
                    else:
                        logger.info("This last object, no pause.")

            if storage:
                logger.info("Saving parsed items to database...")
                await init_database.instagram_repo.save_network_items(storage)
                logger.info("Saving completed")

        except Exception as ex:
            logger.exception(ex)


class ScraperInstagramMetadata:
    def __init__(self):
        self.log_file = "ScraperInstagramMetadata.log"
        self.proxies = []
        self.urls = []
        self.failed_urls = []
        self.time_sleep = 20
        self.batch_size = 200

        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))

        self.path_to_metadata_js = os.path.join(project_root, "scrapers", "instagram", "metadata.js")
        self.metadata_cwd = os.path.dirname(self.path_to_metadata_js)

        logger = logger_config(name="ScraperInstagramMetadata_init", log_file=self.log_file)
        logger.info(f"Metadata.js full path: {self.path_to_metadata_js}")
        logger.info(f"Metadata CWD: {self.metadata_cwd}")

    async def _load_proxies(self):
        logger = logger_config(name="_load_proxies", log_file=self.log_file)

        try:
            proxies = await init_database.proxies_repo.get_proxies_true()

            if not proxies:
                logger.warning("No work proxies found!")
                self.proxies = []
                return []

            proxies_active = [p for p in proxies if p.status]
            logger.info(f"Active proxies loaded: {len(proxies_active)}")

            self.proxies = proxies_active
            return self.proxies

        except Exception as ex:
            logger.exception(ex)
            return []

    async def _build_proxy(self, data_proxy):
        logger = logger_config(name="_build_proxy", log_file=self.log_file)
        proxy_list = []

        try:
            if not data_proxy:
                return []

            for proxy in data_proxy:
                proxy_id = proxy.id
                login = proxy.login
                host = proxy.host
                port = proxy.port
                password = await security.decrypt(proxy.password_hash)

                proxy_list.append({
                    "id": proxy_id,
                    "proxy": f"http://{login}:{password}@{host}:{port}"
                })

            return proxy_list

        except Exception as ex:
            logger.exception(ex)
            return []

    async def _load_urls(self):
        logger = logger_config(name="_load_urls", log_file=self.log_file)

        try:
            urls = await init_database.instagram_repo.get_instagram_items()

            if not urls:
                logger.warning("No work urls found!")
                self.urls = []
                return []

            urls_active = [u for u in urls if u.status]
            logger.info(f"Active urls loaded: {len(urls_active)}")

            self.urls = urls_active
            return self.urls

        except Exception as ex:
            logger.exception(ex)
            return []

    def _normalize_metadata(self, raw_metadata):
        if not isinstance(raw_metadata, dict):
            return {"success": False, "error": "Invalid metadata format"}

        if "error" in raw_metadata:
            return {"success": False, "error": raw_metadata.get("error")}

        data = raw_metadata

        ts = data.get("taken_at_timestamp")

        published_at = None
        if ts:
            try:
                published_at = datetime.fromtimestamp(int(ts), UTC)
            except:
                published_at = None

        normalized = {
            "likes": data.get("likes") or 0,
            "video_views_count": data.get("video_view_count") or 0,
            "video_play_count": data.get("video_play_count") or 0,
            "caption": data.get("caption"),
            "published_at": (
                published_at.strftime("%Y-%m-%d %H:%M:%S")
                if published_at else None
            ),
            "comments_count": data.get("comment_count") or 0,
            "shares": 0,
            "saves": 0
        }

        return normalized

    async def _fetch_metadata(self):
        logger = logger_config(name="_fetch_metadata", log_file=self.log_file)

        results = []

        try:
            if not self.urls:
                logger.warning("No URLs to process")
                return []

            total_urls = len(self.urls)

            for batch_start in range(0, len(self.urls), self.batch_size):
                batch = self.urls[batch_start: batch_start + self.batch_size]
                logger.info(f"Processing batch {batch_start // self.batch_size + 1}")

                for idx, url_obj in enumerate(batch):
                    url = url_obj.url
                    logger.info(f"Processing URL: {url}")

                    success = False
                    data = None

                    for proxy in self.proxies:
                        proxy_string = proxy["proxy"]
                        logger.info(f"Trying proxy: {proxy_string}")

                        try:
                            cmd = ["node", self.path_to_metadata_js, url, proxy_string]

                            process = subprocess.run(
                                cmd,
                                capture_output=True,
                                text=True,
                                encoding="utf-8",
                                errors="replace",
                                cwd=self.metadata_cwd,
                                timeout=30
                            )

                            stdout = process.stdout.strip()
                            stderr = process.stderr.strip()

                            if stderr:
                                logger.error(f"Node STDERR (proxy): {stderr}")

                            try:
                                data = json.loads(stdout)
                            except Exception:
                                data = {"raw": stdout, "error": "JSON parse failed"}

                            logger.info(f"Response via proxy: {proxy_string}")
                            success = True
                            break

                        except Exception as ex:
                            logger.exception(ex)
                            continue

                    if not success:
                        logger.info("Trying main IP")

                        try:
                            cmd = ["node", self.path_to_metadata_js, url]

                            process = subprocess.run(
                                cmd,
                                capture_output=True,
                                text=True,
                                encoding="utf-8",
                                errors="replace",
                                cwd=self.metadata_cwd,
                                timeout=30
                            )

                            stdout = process.stdout.strip()
                            stderr = process.stderr.strip()

                            if stderr:
                                logger.error(f"Node STDERR (main IP): {stderr}")

                            try:
                                data = json.loads(stdout)
                            except Exception:
                                data = {"raw": stdout, "error": "JSON parse failed"}

                            logger.info("Response via main IP")
                            success = True

                        except Exception as ex:
                            logger.exception(ex)
                            self.failed_urls.append(url_obj)
                            continue

                    if success:
                        normalized_data = self._normalize_metadata(data)

                        results.append({
                            "network_item_id": url_obj.id,
                            "url": url,
                            "metadata": normalized_data
                        })

                    await asyncio.sleep(0.1)

                    current_global_index = batch_start + idx
                    if current_global_index < total_urls - 1:
                        logger.info(f"Sleep {self.time_sleep} seconds")
                        await asyncio.sleep(self.time_sleep)

                logger.info(f"Batch complete.")

            return results

        except Exception as ex:
            logger.exception(ex)
            return []

    async def run(self):
        logger = logger_config(name="run", log_file=self.log_file)

        try:
            self.urls = await self._load_urls()
            raw_proxies = await self._load_proxies()
            self.proxies = await self._build_proxy(raw_proxies)

            data_metadata = await self._fetch_metadata()

            print(data_metadata)
            await init_database.item_metadata_repo.save_metadata(data_metadata)
            await init_database.network_item_repo.update_published_at(data_metadata)

        except Exception as ex:
            logger.exception(ex)
