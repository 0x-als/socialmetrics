import os
import json
import asyncio
from datetime import timezone, datetime, UTC

from config import base_dir
from database import init_database
from utils import security
from utils.logger import logger_config
import httpx


class ScraperYoutubeURL:
    def __init__(self):
        self.log_file = "ScraperYoutubeURL.log"
        self.urls = []
        self.metadata_delay = 3
        self.sessions = []
        self.results = []

    async def _load_urls(self):
        logger = logger_config(name="_load_urls", log_file=self.log_file)

        try:
            urls = await init_database.social_networks_repo.get_social_networks_by_type("youtube")
            if not urls:
                logger.warning("No youtube accounts found")
                self.urls = []
                return

            urls_active = [u for u in urls if u.status]
            logger.info(f"Loaded {len(urls_active)} youtube accounts")
            self.urls = urls_active
            return self.urls

        except Exception as ex:
            logger.exception(ex)

    async def _load_sessions(self):
        logger = logger_config(name="_load_sessions", log_file=self.log_file)

        try:
            sessions = await init_database.scrape_accounts_repo.get_scrape_account_by_type("youtube")
            if not sessions:
                logger.warning("No youtube sessions found")
                self.sessions = []
                return

            for session in sessions:
                api_key = await security.decrypt(session.api_key)
                if api_key:
                    self.sessions.append({
                        "api_key": api_key
                    })

            logger.info(f"Loaded {len(self.sessions)} sessions")

        except Exception as ex:
            logger.exception(ex)

    async def _get_channel_id(self, channel_url: str, api_key: str):
        logger = logger_config(name="_get_channel_id", log_file=self.log_file)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Если это handle (@username)
                if "@" in channel_url:
                    handle = channel_url.split("@")[-1].strip("/")
                    params = {
                        "part": "id",
                        "forHandle": handle,
                        "key": api_key
                    }
                    response = await client.get("https://www.googleapis.com/youtube/v3/channels", params=params)
                else:
                    # Если обычная ссылка
                    params = {
                        "part": "id",
                        "key": api_key
                    }
                    response = await client.get("https://www.googleapis.com/youtube/v3/channels", params=params)

                data = response.json()
                if data.get("items"):
                    return data["items"][0]["id"]
                logger.warning(f"Failed to get channel ID for {channel_url}")
                return None
        except Exception as ex:
            logger.exception(ex)
            return None

    async def _fetch_videos(self, channel_id: str, api_key: str, video_type: str = "videos"):
        logger = logger_config(name="_fetch_videos", log_file=self.log_file)
        videos = []

        try:
            # Сначала получаем playlistId uploads
            async with httpx.AsyncClient(timeout=15.0) as client:
                params = {
                    "part": "contentDetails",
                    "id": channel_id,
                    "key": api_key
                }
                response = await client.get("https://www.googleapis.com/youtube/v3/channels", params=params)
                data = response.json()

                if not data.get("items"):
                    return []

                uploads_playlist_id = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

                # Теперь получаем видео из плейлиста
                next_page_token = None
                while True:
                    params = {
                        "part": "snippet,contentDetails",
                        "playlistId": uploads_playlist_id,
                        "maxResults": 50,
                        "key": api_key
                    }
                    if next_page_token:
                        params["pageToken"] = next_page_token

                    response = await client.get("https://www.googleapis.com/youtube/v3/playlistItems", params=params)
                    data = response.json()

                    for item in data.get("items", []):
                        video_id = item["contentDetails"]["videoId"]
                        title = item["snippet"]["title"]
                        published_at = item["snippet"]["publishedAt"]

                        # Фильтрация Shorts
                        if video_type == "shorts" and not title.lower().startswith("#shorts") and not self._is_short(item):
                            continue
                        if video_type == "videos" and self._is_short(item):
                            continue

                        videos.append({
                            "url": f"https://www.youtube.com/watch?v={video_id}",
                            "title": title,
                            "published_at": published_at,
                            "video_id": video_id,
                            "channel_id": channel_id
                        })

                    next_page_token = data.get("nextPageToken")
                    if not next_page_token:
                        break

                    await asyncio.sleep(0.5)

            return videos

        except Exception as ex:
            logger.exception(ex)
            return []

    def _is_short(self, item):
        # Простая эвристика: Shorts обычно имеют duration < 60 сек, но в playlistItems duration не всегда есть
        # Поэтому проверяем по заголовку или другим признакам
        title = item.get("snippet", {}).get("title", "").lower()
        return "#short" in title or "shorts" in item.get("snippet", {}).get("thumbnails", {}).get("default", {}).get("url", "")

    async def run(self):
        logger = logger_config(name="run", log_file=self.log_file)

        try:
            await self._load_urls()
            await self._load_sessions()

            if not self.urls:
                logger.warning("Нет YouTube каналов для обработки")
                return

            if not self.sessions:
                logger.warning("Нет API ключей для YouTube")
                return

            logger.info(f"Starting video collection for {len(self.urls)} channels with {len(self.sessions)} sessions")

            for url_object in self.urls:
                channel_url = url_object.url
                logger.info(f"Processing channel: {channel_url}")

                api_key = self.sessions[0].get("api_key")  # Используем первый ключ
                if not api_key:
                    continue

                channel_id = await self._get_channel_id(channel_url, api_key)
                if not channel_id:
                    logger.warning(f"Could not get channel ID for {channel_url}")
                    continue

                logger.info(f"Got channel ID: {channel_id}")

                # Собираем обычные видео
                logger.info(f"Fetching regular videos for {channel_url}")
                regular_videos = await self._fetch_videos(channel_id, api_key, video_type="videos")

                # Собираем Shorts
                logger.info(f"Fetching Shorts for {channel_url}")
                shorts = await self._fetch_videos(channel_id, api_key, video_type="shorts")

                # Сохраняем результаты
                all_items = regular_videos + shorts
                for item in all_items:
                    self.results.append({
                        "network_item_id": url_object.id,  # Привязываем к родительскому каналу
                        "url": item["url"],
                        "title": item["title"],
                        "published_at": item["published_at"],
                        "video_type": "short" if "short" in item["url"].lower() or "#short" in item.get("title", "").lower() else "video"
                    })

                logger.info(f"Collected {len(regular_videos)} videos and {len(shorts)} shorts for {channel_url}")

                await asyncio.sleep(self.metadata_delay)

            if self.results:
                logger.info(f"Total collected {len(self.results)} YouTube items. Ready for saving.")
                print(json.dumps(self.results, indent=2, ensure_ascii=False))
                # await init_database...save(...) — добавьте вызов сохранения по необходимости

        except Exception as ex:
            logger.exception(ex)

async def main():
    scraper = ScraperYoutubeURL()
    await scraper.run()

asyncio.run(main())