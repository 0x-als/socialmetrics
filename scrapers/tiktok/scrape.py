import os
import json
import asyncio
import jmespath

from config import base_dir
from datetime import timezone, datetime, UTC
from parsel import Selector
from database import init_database
from utils.logger import logger_config
from cloakbrowser import launch_persistent_context_async


class ScraperTikTokURL:
    def __init__(self):
        self.log_file = "ScraperTikTokURL.log"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        self.extra_headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "application/json, text/plain, */*",
        }
        self.base_profile_path = f"{base_dir}/files/profiles/tiktok_profiles/profile"
        self.profile_dirs = [
            f"{self.base_profile_path}_1",
            f"{self.base_profile_path}_2",
            f"{self.base_profile_path}_3"
        ]
        self.urls = []
        self.time_sleep = 1
        self.batch_size = 200
        self.results = []

    async def _load_urls(self):
        logger = logger_config(name="_load_urls", log_file=self.log_file)
        try:
            urls = await init_database.social_networks_repo.get_social_networks_by_type("tiktok")
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

    async def _create_browser(self, profile_dir):
        logger = logger_config(name="_create_browser", log_file=self.log_file)
        try:
            os.makedirs(profile_dir, exist_ok=True)
            context = await launch_persistent_context_async(
                user_data_dir=profile_dir,
                headless=True,
                humanize=True,
                human_preset="careful",
                geoip=True,
                user_agent=self.user_agent,
                locale="en-US",
                viewport={"width": 1200, "height": 800},
                extra_http_headers=self.extra_headers,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--fingerprint-noise=false"
                ]
            )
            if context.pages:
                page = context.pages[0]
            else:
                page = await context.new_page()
            logger.info(f"Browser started with profile: {profile_dir}")
            return context, page
        except Exception as ex:
            logger.exception(ex)
            return None, None

    def _parse_followers_text(self, text):
        if not text:
            return None
        text = text.strip().upper().replace(",", "").replace(" ", "")
        try:
            if "M" in text:
                return int(float(text.replace("M", "")) * 1000000)
            elif "K" in text:
                return int(float(text.replace("K", "")) * 1000)
            else:
                return int(text)
        except:
            return None

    async def _get_followers(self, page):
        try:
            followers_text = await page.evaluate(r"""
                () => {
                    const selectors = [
                        'span[data-e2e="followers-count"]',
                        'strong[data-e2e="followers-count"]',
                        '[data-e2e="followers-count"]',
                        'div[class*="FollowerCount"]',
                        'span[class*="FollowerCount"]'
                    ];
                    for (let sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el && el.textContent) return el.textContent.trim();
                    }
                    const allTexts = Array.from(document.querySelectorAll('span, strong, div'))
                        .map(el => el.textContent.trim())
                        .filter(t => /[\d.,]+[KkMm]?\s*(followers|follower)/i.test(t));
                    return allTexts.length > 0 ? allTexts[0] : null;
                }
            """)
            return self._parse_followers_text(followers_text)
        except:
            return None

    async def _fetch_webprofile(self, page, network_id: int, url: str):
        logger = logger_config(name="_fetch_webprofile", log_file=self.log_file)
        try:
            logger.info(f"Opening profile: {url}")
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)

            followers = await self._get_followers(page)
            logger.info(f"Followers found: {followers}")

            logger.info("Starting accelerated scroll and video links collection...")

            video_urls = set()
            previous_height = 0
            previous_count = 0
            no_change_count = 0
            max_no_change = 5

            while no_change_count < max_no_change:
                current_height = await page.evaluate("document.body.scrollHeight")

                video_links = await page.evaluate("""
                    () => {
                        return Array.from(document.querySelectorAll('a[href*="tiktok.com/@"][href*="/video/"]'))
                            .map(a => a.href)
                            .filter(href => href.includes('/video/'));
                    }
                """)

                new_links = [link for link in video_links if link not in video_urls]
                video_urls.update(new_links)

                current_count = len(video_urls)

                logger.info(f"Scrolled | Height: {current_height:,} px | Videos: {current_count} | New: {len(new_links)}")

                if current_height == previous_height and current_count == previous_count:
                    no_change_count += 1
                    logger.info(f"No new content ({no_change_count}/{max_no_change})")
                else:
                    no_change_count = 0

                previous_height = current_height
                previous_count = current_count

                if no_change_count >= max_no_change:
                    logger.info("Reached end of profile")
                    break

                await page.evaluate("window.scrollBy(0, window.innerHeight * 1.8)")
                await page.wait_for_timeout(1600)

            profile_data = {
                "id": network_id,
                "url": url,
                "followers": followers,
                "urls": list(video_urls)
            }

            self.results.append([profile_data])

            logger.info(f"Profile processed: {url}")
            logger.info(f"Collected {len(video_urls)} unique video URLs")

            # Сохраняем сразу после обработки одного профиля
            await init_database.tiktok_repo.save_network_items([[profile_data]])
            logger.info(f"Data for {url} saved to database")

            return True

        except Exception as ex:
            logger.exception(f"Error fetching profile {url}")
            return False

    async def _process_single(self, url_object, profile_dir):
        logger = logger_config(name="_process_single", log_file=self.log_file)
        url = url_object.url if hasattr(url_object, "url") else str(url_object)
        network_id = getattr(url_object, "id", None)

        logger.info(f"Processing: {url} (id: {network_id}) using profile: {profile_dir}")

        context = None
        page = None
        try:
            context, page = await self._create_browser(profile_dir)
            if not page:
                return
            await self._fetch_webprofile(page, network_id, url)
        except Exception as ex:
            logger.exception(f"Error processing {url}")
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
            if not self.urls:
                logger.warning("No active URLs to process. Exiting.")
                return

            logger.info(f"Starting parallel processing of {len(self.urls)} TikTok profiles (max 3 concurrent)")

            semaphore = asyncio.Semaphore(3)

            async def sem_task(idx, url_object):
                async with semaphore:
                    profile_dir = self.profile_dirs[idx % 3]
                    await self._process_single(url_object, profile_dir)

            tasks = [sem_task(i, url_object) for i, url_object in enumerate(self.urls)]
            await asyncio.gather(*tasks, return_exceptions=True)

            logger.info(f"Processing completed. Total profiles: {len(self.urls)}")

        except Exception as ex:
            logger.exception("Critical error in run method")


class ScraperTikTokMetadata:
    def __init__(self):
        self.log_file = "ScraperTikTokMetadata.log"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        self.extra_headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "application/json, text/plain, */*",
        }
        self.base_profile_path = f"{base_dir}/files/profiles/tiktok_profiles/profile"
        self.profile_dirs = [
            f"{self.base_profile_path}_1",
            f"{self.base_profile_path}_2",
            f"{self.base_profile_path}_3"
        ]
        self.urls = []
        self.results = []
        self.time_sleep = 3
        self.batch_size = 200

    async def _load_urls(self):
        logger = logger_config(name="_load_urls", log_file=self.log_file)
        try:
            urls = await init_database.network_item_repo.get_network_items_by_type("tiktok")
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

    async def _create_browser(self, profile_dir):
        logger = logger_config(name="_create_browser", log_file=self.log_file)
        try:
            os.makedirs(profile_dir, exist_ok=True)
            context = await launch_persistent_context_async(
                user_data_dir=profile_dir,
                headless=True,
                humanize=True,
                human_preset="careful",
                geoip=True,
                user_agent=self.user_agent,
                locale="en-US",
                viewport={"width": 1200, "height": 800},
                extra_http_headers=self.extra_headers,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--fingerprint-noise=false"
                ]
            )
            if context.pages:
                page = context.pages[0]
            else:
                page = await context.new_page()
            return context, page
        except Exception as ex:
            logger.exception(ex)
            return None, None

    def _extract_metadata(self, html):
        selector = Selector(html)
        raw = selector.xpath("//script[@id='__UNIVERSAL_DATA_FOR_REHYDRATION__']/text()").get()
        if not raw:
            return {}

        try:
            data = json.loads(raw)
            post = data.get("__DEFAULT_SCOPE__", {}) \
                .get("webapp.video-detail", {}) \
                .get("itemInfo", {}) \
                .get("itemStruct", {})
            return jmespath.search(
                "{id:id, desc:desc, createTime:createTime, stats:stats}",
                post
            ) or {}
        except:
            return {}

    async def _fetch_metadata(self, page, network_item_id: int, url: str):
        logger = logger_config(name="_fetch_metadata", log_file=self.log_file)
        try:
            logger.info(f"Fetching metadata: {url}")

            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await page.wait_for_timeout(4000)

            html = await page.content()
            data = self._extract_metadata(html)

            stats = data.get("stats", {})

            create_time = data.get("createTime")
            if create_time:
                try:
                    published_at = datetime.fromtimestamp(int(create_time), UTC)
                except:
                    published_at = None

            metadata = {
                "likes": int(stats.get("diggCount", 0)),
                "video_views_count": 0,
                "video_play_count": int(stats.get("playCount", 0)),
                "comments_count": int(stats.get("commentCount", 0)),
                "shares": int(stats.get("shareCount", 0)),
                "saves": int(stats.get("collectCount", 0)),
                "published_at": (
                    published_at.strftime("%Y-%m-%d %H:%M:%S")
                    if published_at else None
                ),
                "caption": data.get("desc", None),
            }

            result = {
                "network_item_id": network_item_id,
                "url": url,
                "metadata": metadata
            }

            self.results.append(result)
            logger.info(f"Metadata collected for: {url}")
            return result

        except Exception as ex:
            logger.exception(f"Error fetching metadata {url}")
            result = {
                "network_item_id": network_item_id,
                "url": url,
                "metadata": {
                    "likes": None, "video_views_count": None, "video_play_count": None,
                    "comments_count": None, "shares": None, "saves": None,
                    "published_at": None, "caption": None
                }
            }
            self.results.append(result)
            return result

    async def _process_single(self, item, profile_dir):
        logger = logger_config(name="_process_single", log_file=self.log_file)
        url = item.url
        network_item_id = item.id

        context = None
        page = None
        try:
            await asyncio.sleep(0.7)
            context, page = await self._create_browser(profile_dir)
            if not page:
                return
            await self._fetch_metadata(page, network_item_id, url)
        except Exception as ex:
            logger.exception(f"Error processing metadata for {url}")
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
            if not self.urls:
                logger.warning("No active URLs to process. Exiting.")
                return

            logger.info(f"Starting metadata collection for {len(self.urls)} videos (max 3 concurrent)")

            semaphore = asyncio.Semaphore(3)

            async def sem_task(idx, item):
                async with semaphore:
                    profile_dir = self.profile_dirs[idx % 3]
                    await self._process_single(item, profile_dir)

            tasks = [sem_task(i, item) for i, item in enumerate(self.urls)]
            await asyncio.gather(*tasks, return_exceptions=True)

            if self.results:
                logger.info(f"Saving metadata for {len(self.results)} items...")
                await init_database.item_metadata_repo.save_metadata(self.results)
                await init_database.network_item_repo.update_published_at(self.results)
                logger.info("Metadata successfully saved to database")
            else:
                logger.warning("No metadata collected")

            logger.info("Metadata scraping completed")

        except Exception as ex:
            logger.exception("Critical error in run method")