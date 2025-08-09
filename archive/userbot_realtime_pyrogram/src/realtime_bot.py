import os
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone

from pyrogram import Client, filters
from pyrogram.types import Message
import httpx
from httpx import RequestError

# Optional schemas
try:
    from schemas import PostBase  # type: ignore
except Exception:
    PostBase = None  # fallback


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("userbot_realtime")

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
PHONE = os.getenv("PHONE", "")
BOT_ID = int(os.getenv("BOT_ID", "4"))
BACKEND = os.getenv("BACKEND_API_URL", "http://backend:8000")

BATCH_MAX = int(os.getenv("REALTIME_BATCH_MAX", "5"))
DEBOUNCE_MS = int(os.getenv("REALTIME_DEBOUNCE_MS", "1000"))

SESSION_DIR = os.path.join(os.getcwd(), "session")
os.makedirs(SESSION_DIR, exist_ok=True)


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


async def get_active_channels() -> List[str]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Пытаемся по заданному BOT_ID
            url = f"{BACKEND}/api/public-bots/{BOT_ID}/channels"
            r = await client.get(url)
            if r.status_code == 404:
                # Фоллбек: берём первого активного бота
                logger.warning(f"Bot {BOT_ID} not found (404). Falling back to first active bot")
                rbots = await client.get(
                    f"{BACKEND}/api/public-bots",
                    params={"status_filter": "active"},
                )
                rbots.raise_for_status()
                bots = rbots.json()
                if not bots:
                    raise RuntimeError("No active public bots available")
                fallback_id = int(bots[0]["id"])
                url = f"{BACKEND}/api/public-bots/{fallback_id}/channels"
                logger.info(f"Using BOT_ID={fallback_id} for realtime listener")
                rr = await client.get(url)
                rr.raise_for_status()
                data = rr.json()
            else:
                r.raise_for_status()
                data = r.json()

            # Пробуем собрать идентификаторы каналов (предпочитаем username с @)
            ident: List[str] = []
            for ch in data:
                username = ch.get("username")
                if username:
                    if not username.startswith("@"):
                        username = f"@{username}"
                    ident.append(username)
                elif ch.get("channel_telegram_id") is not None:
                    # В Pyrogram можно подписаться и по numeric id; используем как строку
                    ident.append(str(ch["channel_telegram_id"]))

            if not ident:
                # Фоллбек: используем глобальный список активных каналов, как делал старый userbot
                logger.warning(
                    "Public-bot channels empty; falling back to /api/channels?active_only=true"
                )
                gr = await client.get(
                    f"{BACKEND}/api/channels", params={"active_only": "true"}
                )
                gr.raise_for_status()
                gl = gr.json()
                for ch in gl:
                    if not ch.get("is_active"):
                        continue
                    username = ch.get("username")
                    if username:
                        if not username.startswith("@"):
                            username = f"@{username}"
                        ident.append(username)
                    elif ch.get("telegram_id") is not None:
                        ident.append(str(ch["telegram_id"]))

            logger.info(f"Loaded {len(ident)} channels for realtime listen")
            return ident
    except RequestError as e:
        logger.warning(f"Backend not reachable yet: {e}")
        return []
    except Exception as e:
        logger.exception(f"Failed to load channels: {e}")
        return []


def to_post_dict(msg: Message) -> Dict[str, Any]:
    channel_id = int(msg.chat.id)
    post_id = int(msg.id)
    text = msg.text or msg.caption or ""
    views = msg.views or 0
    post_date = datetime.fromtimestamp(msg.date, tz=timezone.utc)

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
        "collection_stats": {"source": "pyrogram_realtime", "count": len(items)},
        "posts": items,
        "channels_metadata": {},
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{BACKEND}/api/posts/batch", json=batch)
        r.raise_for_status()
        logger.info(f"Batch sent: {len(items)} posts → {r.status_code}")

        # Пинаем AI обработку
        try:
            await client.post(f"{BACKEND}/api/ai/trigger-processing")
        except Exception as e:
            logger.warning(f"trigger-processing failed (non-blocking): {e}")


async def main():
    channels = await get_active_channels()
    while not channels:
        logger.warning("No channels to listen; retry in 30s...")
        await asyncio.sleep(30)
        channels = await get_active_channels()

    # Используем ту же директорию сессий, что и Telethon контейнер, чтобы избежать интерактивного ввода
    app = Client(
        name="realtime",
        api_id=API_ID,
        api_hash=API_HASH,
        workdir=SESSION_DIR,
        phone_number=PHONE if PHONE else None,
        in_memory=False,
        no_updates=False,
    )
    batcher = MicroBatcher(send_batch, BATCH_MAX, DEBOUNCE_MS)

    @app.on_message(filters.chat(channels))
    async def handler(client: Client, msg: Message):
        try:
            payload = to_post_dict(msg)
            batcher.add(payload)
        except Exception as e:
            logger.exception(f"Failed to process message: {e}")

    async with app:
        logger.info("Realtime listener started (Pyrogram)")
        while True:
            await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())


