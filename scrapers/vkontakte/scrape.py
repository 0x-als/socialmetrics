import os
import json
import httpx
import asyncio

from datetime import datetime, UTC
from config import base_dir
from database import init_database
from utils import security
from utils.logger import logger_config
from cloakbrowser import launch_context_async


class ScraperVkontakteURL:
    def __init__(self):
        self.log_file = "ScraperVkontakteURL.log"
        self.base_path = f"{base_dir}/files/profiles/vk_profiles"
        self.urls = []
        self.sessions = []
        self.results = []

    def _normalize_clip_url(self, url: str):
        if "clip-" in url:
            part = url.split("clip-")[-1]
            part = part.split("&")[0]
            return f"https://vk.com/clip-{part}"
        if "z=clip-" in url:
            part = url.split("z=clip-")[-1]
            part = part.split("&")[0]
            return f"https://vk.com/clip-{part}"
        return None

    async def _load_urls(self):
        logger = logger_config(name="_load_urls", log_file=self.log_file)
        try:
            urls = await init_database.social_networks_repo.get_social_networks_by_type("vk")
            if not urls:
                logger.warning("No vkontakte accounts found")
                self.urls = []
                return
            urls_active = [u for u in urls if u.status]
            logger.info(f"Active urls loaded: {len(urls_active)}")
            self.urls = urls_active
            return self.urls
        except Exception as ex:
            logger.exception(ex)

    async def _load_sessions(self):
        logger = logger_config(name="_load_sessions", log_file=self.log_file)
        try:
            sessions = await init_database.scrape_accounts_repo.get_scrape_account_by_type("vk")
            if not sessions:
                logger.warning("No vkontakte sessions found")
                self.sessions = []
                return
            self.sessions = sessions
            logger.info(f"Loaded {len(self.sessions)} sessions")
        except Exception as ex:
            logger.exception(ex)

    async def _create_browser(self, session_path: str):
        logger = logger_config(name="_create_browser", log_file=self.log_file)
        try:
            cookies_path = os.path.join(session_path, "cookies.json")
            storage_path = os.path.join(session_path, "storage.json")

            storage = None
            if os.path.exists(storage_path):
                with open(storage_path, "r", encoding="utf-8") as f:
                    storage = json.load(f)

            context = await launch_context_async(
                storage_state=storage,
                headless=True,
                humanize=True,
                human_preset="careful",
                locale="ru-RU",
                viewport={"width": 1280, "height": 800},
            )

            if os.path.exists(cookies_path):
                with open(cookies_path, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                await context.add_cookies(cookies)

            if context.pages:
                page = context.pages[0]
            else:
                page = await context.new_page()

            return context, page
        except Exception as ex:
            logger.exception(ex)
            return None, None

    async def _fetch_clips(self, page, original_url: str, network_id: int):
        logger = logger_config(name="_fetch_clips", log_file=self.log_file)
        try:
            clean_url = original_url.split("?")[0].rstrip("/")
            username = clean_url.split("/")[-1]
            clips_url = f"https://vk.com/clips/{username}"

            logger.info(f"Opening clips page: {clips_url}")
            await page.goto(clips_url, timeout=60000, wait_until="domcontentloaded")
            await page.wait_for_timeout(4000)

            clip_urls = set()
            previous_height = 0
            no_change_count = 0
            max_no_change = 5

            while no_change_count < max_no_change:
                current_height = await page.evaluate("document.body.scrollHeight")

                links = await page.evaluate("""
                    () => {
                        const selectors = [
                            'a[href*="/clip-"]',
                            'a[href*="/video-"]',
                            'a[href*="z=clip-"]',
                            'div[class*="VideoCard"] a',
                            'a[href*="/clips/"]'
                        ];
                        let result = [];
                        for (let sel of selectors) {
                            result = result.concat(Array.from(document.querySelectorAll(sel)));
                        }
                        return [...new Set(result.map(a => a.href))];
                    }
                """)

                normalized = []
                for link in links:
                    n = self._normalize_clip_url(link)
                    if n:
                        normalized.append(n)

                new_links = [link for link in normalized if link not in clip_urls]
                clip_urls.update(new_links)

                current_count = len(clip_urls)

                logger.info(f"Scrolled | Height: {current_height:,} | Total clips: {current_count} | New: {len(new_links)}")

                if current_height == previous_height and len(new_links) == 0:
                    no_change_count += 1
                else:
                    no_change_count = 0

                previous_height = current_height

                if no_change_count >= max_no_change:
                    logger.info("Reached end of clips page")
                    break

                await page.evaluate("window.scrollBy(0, window.innerHeight * 2.2)")
                await page.wait_for_timeout(1200)

            profile_data = {
                "id": network_id,
                "url": original_url,
                "followers": None,
                "urls": list(clip_urls)
            }

            self.results.append([profile_data])
            logger.info(f"Collected {len(clip_urls)} clip URLs from {original_url}")

            return True

        except Exception as ex:
            logger.exception(f"Error fetching clips {original_url}")
            return False

    async def _process_single(self, url_object, session):
        logger = logger_config(name="_process_single", log_file=self.log_file)
        original_url = url_object.url.strip()
        network_id = url_object.id

        session_path = os.path.join(self.base_path, session.path)

        context = None
        page = None
        try:
            context, page = await self._create_browser(session_path)
            if not page:
                return
            await self._fetch_clips(page, original_url, network_id)
        except Exception as ex:
            logger.exception(f"Error processing {original_url}")
        finally:
            if context:
                try:
                    await context.close()
                except:
                    pass

    async def run(self):
        logger = logger_config(name="run", log_file=self.log_file)
        try:
            await self._load_urls()
            await self._load_sessions()

            if not self.urls or not self.sessions:
                logger.warning("No data to process")
                return

            logger.info(f"Starting VK clips scraping with {len(self.sessions)} sessions")

            for idx, url_object in enumerate(self.urls):
                session = self.sessions[idx % len(self.sessions)]
                await self._process_single(url_object, session)

            if self.results:
                logger.info("Saving parsed items to database...")
                await init_database.vkontakte_repo.save_network_items(self.results)
                logger.info("Saving completed")
            else:
                logger.warning("No data collected")

            logger.info(f"Processing completed. Total profiles: {len(self.urls)}")

        except Exception as ex:
            logger.exception(ex)


class ScraperVkontakteMetadata:
    def __init__(self):
        self.log_file = "ScraperVkontakteMetadata.log"
        self.urls = []
        self.base_path = f"{base_dir}/files/vk_profiles"
        self.results = []
        self.sessions = []
        self.metadata_delay = 3
        self.batch_size = 200

    def _extract_ids(self, url):
        logger = logger_config(name="_extract_ids", log_file=self.log_file)

        try:
            part = url.split("clip", 1)[1]
            owner_id, video_id = part.split("_", 1)
            return owner_id, video_id

        except Exception as ex:
            logger.exception(ex)
            return None, None

    async def _load_urls(self):
        logger = logger_config(name="_load_urls", log_file=self.log_file)

        try:

            self.urls = await init_database.network_item_repo.get_network_items_by_type("vk")
            if not self.urls:
                logger.warning("No work urls found!")
                self.urls = []
                return []

            urls_active = [u for u in self.urls if u.status]
            logger.info(f"Found {len(urls_active)} active urls")
            self.urls = urls_active
            return self.urls

        except Exception as ex:
            logger.exception(ex)

    async def _load_sessions(self):
        logger = logger_config(name="_load_sessions", log_file=self.log_file)

        try:

            sessions = await init_database.scrape_accounts_repo.get_scrape_account_by_type("vk")
            if sessions:
                for session in sessions:
                    client_id = await security.decrypt(session.client_id)
                    api_key = await security.decrypt(session.api_key)
                    token = await security.decrypt(session.token_hash)
                    self.sessions.append({
                        "api_key": api_key,
                        "token": token
                    })

                logger.info(f"Loaded {len(self.sessions)} sessions")

            else:
                logger.warning("No sessions found")
                self.sessions = []
                return []

        except Exception as ex:
            logger.exception(ex)

    def _normalize_metadata(self, raw_metadata):
        if not isinstance(raw_metadata, dict):
            return {"success": False, "error": "Invalid metadata format"}

        normalized = {
            "likes": raw_metadata.get("likes") or 0,
            "video_views_count": raw_metadata.get("views_picture") or 0,
            "video_play_count": raw_metadata.get("views_video") or 0,
            "comments_count": raw_metadata.get("comment_count") or 0,
            "shares": raw_metadata.get("shares") or 0,
            "saves": raw_metadata.get("saves") or 0,
            "published_at": raw_metadata.get("published_at"),
            "caption": raw_metadata.get("caption"),
            "followers": None
        }
        return normalized

    async def _fetch_metadata(self, token: str, owner_id: int, video_id: int):
        logger = logger_config(name="_fetch_metadata", log_file=self.log_file)

        try:
            params = {
                "videos": f"{owner_id}_{video_id}",
                "access_token": token,
                "v": "5.199"
            }

            async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
                try:
                    response = await client.get("https://api.vk.com/method/video.get", params=params)
                    data = response.json()

                    if "error" in data or not data.get("response", {}).get("items"):
                        return {}

                    video = data["response"]["items"][0]
                    if video:
                        ts = video.get("date")
                        published_at = None
                        if ts:
                            try:
                                published_at = datetime.fromtimestamp(int(ts), UTC)
                                published_at = published_at.strftime("%Y-%m-%d %H:%M:%S")
                            except:
                                published_at = None

                        return {
                            "likes": video.get("likes", {}).get("count"),
                            "views_picture": None,
                            "views_video": video.get("views"),
                            "comment_count": video.get("comments"),
                            "shares": video.get("reposts", {}).get("count"),
                            "saves": None,
                            "published_at": published_at,
                            "caption": video.get("description")
                        }

                except Exception as ex:
                    logger.exception(ex)
                    return None

        except Exception as ex:
            logger.exception(ex)
            return None

    async def _process_batch(self, batch, sessions):
        results = []
        logger = logger_config(name="_process_batch", log_file=self.log_file)

        for url_object in batch:
            url = url_object.url
            logger.info(f"Processing URL: {url}")

            owner_id_str, video_id_str = self._extract_ids(url)

            if not owner_id_str or not video_id_str:
                logger.info(f"Failed to extract IDs for URL: {url}")
                continue

            try:
                owner_id = int(owner_id_str)
                video_id = int(video_id_str)
            except:
                logger.info(f"Failed to convert IDs for URL: {url}")
                continue

            success = False
            for session in sessions:
                token = session.get("token")
                if not token:
                    continue

                metadata = await self._fetch_metadata(token, owner_id, video_id)
                if metadata:
                    normalized = self._normalize_metadata(metadata)
                    results.append({
                        "network_item_id": url_object.id,
                        "url": url,
                        "metadata": normalized
                    })
                    logger.info(f"Successfully fetched metadata for URL: {url}")
                    success = True
                    break

            if not success:
                logger.info(f"Failed to fetch metadata for URL: {url}")

            await asyncio.sleep(self.metadata_delay)

        return results

    async def run(self):
        logger = logger_config(name="run", log_file=self.log_file)

        try:
            await self._load_urls()
            await self._load_sessions()

            logger.info(f"Starting processing of {len(self.urls)} URLs with {len(self.sessions)} sessions")

            if not self.urls:
                logger.warning("Нет URL для обработки")
                return

            data_metadata = []

            if len(self.sessions) > 1:
                chunk_size = max(1, len(self.urls) // len(self.sessions))
                for i in range(0, len(self.urls), chunk_size):
                    batch = self.urls[i:i + chunk_size]
                    batch_sessions = self.sessions[i % len(self.sessions):] + self.sessions[:i % len(self.sessions)]
                    logger.info(f"Processing batch of {len(batch)} URLs")
                    batch_results = await self._process_batch(batch, batch_sessions[:1])
                    data_metadata.extend(batch_results)
            else:
                logger.info(f"Processing all {len(self.urls)} URLs with single session")
                batch_results = await self._process_batch(self.urls, self.sessions)
                data_metadata.extend(batch_results)

            if data_metadata:
                logger.info(f"Successfully processed {len(data_metadata)} items. Saving to database.")
                print(data_metadata)
                await init_database.item_metadata_repo.save_metadata(data_metadata)
                await init_database.network_item_repo.update_published_at(data_metadata)
            else:
                logger.info("No metadata was collected.")

        except Exception as ex:
            logger.exception(ex)
