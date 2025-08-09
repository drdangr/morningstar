import os
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone

from telethon import TelegramClient, events
import httpx

try:
    from schemas import PostBase  # type: ignore
except Exception:
    PostBase = None


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("userbot_realtime_telethon")

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BACKEND = os.getenv("BACKEND_API_URL", "http://backend:8000")
BOT_ID = int(os.getenv("BOT_ID", "1"))
BATCH_MAX = int(os.getenv("REALTIME_BATCH_MAX", "5"))
DEBOUNCE_MS = int(os.getenv("REALTIME_DEBOUNCE_MS", "1000"))

SESSION_DIR = os.path.join(os.getcwd(), "session")
os.makedirs(SESSION_DIR, exist_ok=True)
SESSION_PATH = os.path.join(SESSION_DIR, "morningstar")


class MicroBatcher:
    def __init__(self, send_fn, batch_max: int, debounce_ms: int):
        self.send_fn = send_fn
        self.batch_max = batch_max
        self.debounce = debounce_ms / 1000.0
        self.buffer: List[Dict[str, Any]] = []
        self._task: asyncio.Task | None = None

    def add(self, item: Dict[str, Any]):
        self.buffer.append(item)
        if len(self.buffer) >= self.batch_max:
            return asyncio.create_task(self.flush())
        if not self._task or self._task.done():
            self._task = asyncio.create_task(self._delayed_flush())

    async def _delayed_flush(self):
        await asyncio.sleep(self.debounce)
        await self.flush()

    async def flush(self):
        if not self.buffer:
            return
        items = self.buffer
        self.buffer = []
        await self.send_fn(items)


def to_post_dict(message) -> Dict[str, Any]:
    channel_id = int(message.peer_id.channel_id if hasattr(message.peer_id, 'channel_id') else message.chat_id)
    post_id = int(message.id)
    text = message.message or ""
    views = int(getattr(message, 'views', 0) or 0)
    post_date = message.date.replace(tzinfo=timezone.utc)

    payload = {
        "channel_telegram_id": channel_id,
        "telegram_message_id": post_id,
        "title": None,
        "content": text,
        "media_urls": [],
        "views": views,
        "post_date": post_date.isoformat(),
    }

    if PostBase:
        try:
            model = PostBase(**payload)
            payload = model.model_dump(mode="json")
        except Exception as e:
            logger.warning(f"PostBase validation failed, fallback to raw: {e}")

    return payload


async def send_batch(items: List[Dict[str, Any]]):
    batch = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        # В backend: Dict[str, Union[int, List[str]]]; строки недопустимы → кладём теги в List[str]
        "collection_stats": {"count": len(items), "source": ["telethon_realtime"]},
        "posts": items,
        "channels_metadata": {},
    }
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.post(f"{BACKEND}/api/posts/batch", json=batch)
            r.raise_for_status()
            logger.info(f"Batch sent: {len(items)} posts → {r.status_code}")
        except httpx.HTTPStatusError as e:
            body = e.response.text if e.response is not None else str(e)
            logger.error(f"POST /api/posts/batch failed: {e} | body='{body}'")
            return

        try:
            await client.post(f"{BACKEND}/api/ai/trigger-processing")
        except Exception as e:
            logger.warning(f"trigger-processing failed (non-blocking): {e}")


async def get_channels() -> List[int | str]:
    async with httpx.AsyncClient(timeout=15) as client:
        url = f"{BACKEND}/api/public-bots/{BOT_ID}/channels"
        r = await client.get(url)
        channels = []
        if r.status_code == 200:
            for ch in r.json():
                if ch.get("username"):
                    channels.append(ch["username"])  # Telethon поддерживает username
                elif ch.get("channel_telegram_id") is not None:
                    channels.append(int(ch["channel_telegram_id"]))
        if not channels:
            gr = await client.get(f"{BACKEND}/api/channels", params={"active_only": "true"})
            gr.raise_for_status()
            for ch in gr.json():
                if not ch.get("is_active"):
                    continue
                if ch.get("username"):
                    channels.append(ch["username"])
                elif ch.get("telegram_id") is not None:
                    channels.append(int(ch["telegram_id"]))
    logger.info(f"Loaded {len(channels)} channels for realtime listen")
    return channels


async def main():
    channels = await get_channels()
    if not channels:
        logger.warning("No channels to listen; exit")
        return

    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    batcher = MicroBatcher(send_batch, BATCH_MAX, DEBOUNCE_MS)

    @client.on(events.NewMessage(chats=channels))
    async def handler(event):
        try:
            payload = to_post_dict(event.message)
            batcher.add(payload)
        except Exception as e:
            logger.exception(f"Failed to process message: {e}")

    async with client:
        logger.info("Realtime listener started (Telethon)")
        while True:
            await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())


