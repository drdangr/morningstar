import asyncio
import logging
import os
from typing import Dict, Any, List

import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeDefault
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000")


async def fetch_active_bots() -> List[Dict[str, Any]]:
    url = f"{BACKEND_API_URL}/api/public-bots"
    params = {"status_filter": "active"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data if isinstance(data, list) else []
                logger.error(f"Failed to fetch bots: {resp.status}")
    except Exception as e:
        logger.error(f"fetch_active_bots error: {e}")
    return []


def register_handlers(app: Application, bot_id: int):
    backend_url = BACKEND_API_URL

    async def create_or_update_user(user):
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "telegram_id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "language_code": user.language_code or "ru",
                    "is_active": True,
                }
                await session.post(f"{backend_url}/api/users", json=payload, timeout=5)
        except Exception:
            pass

    async def get_categories():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{backend_url}/api/public-bots/{bot_id}/categories", timeout=10) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            logger.error(f"get_categories error: {e}")
        return []

    async def get_user_subscriptions(telegram_id: int):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{backend_url}/api/public-bots/{bot_id}/users/{telegram_id}/subscriptions",
                    timeout=10,
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    if resp.status == 404:
                        return []
        except Exception as e:
            logger.error(f"get_user_subscriptions error: {e}")
        return []

    async def update_user_subscriptions(telegram_id: int, category_ids: List[int]):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{backend_url}/api/public-bots/{bot_id}/users/{telegram_id}/subscriptions",
                    json={"category_ids": category_ids},
                    timeout=10,
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            logger.error(f"update_user_subscriptions error: {e}")
        return None

    async def get_bot_channels():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{backend_url}/api/public-bots/{bot_id}/channels", timeout=10) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            logger.error(f"get_bot_channels error: {e}")
        return []

    async def get_user_channel_subscriptions(telegram_id: int):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{backend_url}/api/public-bots/{bot_id}/users/{telegram_id}/channel-subscriptions",
                    timeout=10,
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("subscribed_channels", []) if isinstance(data, dict) else []
                    if resp.status == 404:
                        return []
        except Exception as e:
            logger.error(f"get_user_channel_subscriptions error: {e}")
        return []

    async def update_user_channel_subscriptions(telegram_id: int, channel_ids: List[int]):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{backend_url}/api/public-bots/{bot_id}/users/{telegram_id}/channel-subscriptions",
                    json={"channel_ids": channel_ids},
                    timeout=10,
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            logger.error(f"update_user_channel_subscriptions error: {e}")
        return None

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        await create_or_update_user(user)
        await update.message.reply_text(
            "Привет! Я мультитенантный бот. Используйте /help и /digest."
        )

    async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📋 Команды:\n\n"
            "/start — начать\n"
            "/help — помощь\n"
            "/categories — список категорий\n"
            "/subscribe — управление подписками\n"
            "/channels — управление каналами\n"
            "/digest — персональный дайджест"
        )

    async def categories_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        cats = await get_categories()
        if not cats:
            await update.message.reply_text("❌ Не удалось загрузить категории")
            return
        text_lines = ["📚 Доступные категории:\n"]
        for c in cats:
            name = c.get("name") or c.get("category_name") or "Без названия"
            emoji = c.get("emoji", "📝")
            text_lines.append(f"{emoji} {name}")
        await update.message.reply_text("\n".join(text_lines))

    async def subscribe_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        await create_or_update_user(user)
        cats, subs = await asyncio.gather(get_categories(), get_user_subscriptions(user.id))
        if not cats:
            await update.message.reply_text("❌ Не удалось загрузить категории")
            return
        subscribed_ids = {s.get("id") for s in (subs or [])}
        keyboard = []
        for c in cats:
            cid = c.get("id")
            name = c.get("name") or c.get("category_name") or "Без названия"
            emoji = c.get("emoji", "📝")
            mark = "✅" if cid in subscribed_ids else "❌"
            keyboard.append([InlineKeyboardButton(f"{mark} {emoji} {name}", callback_data=f"toggle_category_{cid}")])
        keyboard.append([InlineKeyboardButton("💾 Сохранить", callback_data="save_subscriptions")])
        await update.message.reply_text(
            "🎯 Управление подписками: нажимайте для переключения, затем 'Сохранить'",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    async def channels_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chans, subs = await asyncio.gather(get_bot_channels(), get_user_channel_subscriptions(user.id))
        if not chans:
            await update.message.reply_text("❌ Не удалось загрузить каналы")
            return
        subscribed_ids = {c.get("id") for c in (subs or [])}
        keyboard = []
        for ch in chans:
            ch_id = ch.get("id")
            title = ch.get("title") or ch.get("channel_name") or f"Канал {ch_id}"
            mark = "✅" if ch_id in subscribed_ids else "❌"
            keyboard.append([InlineKeyboardButton(f"{mark} {title}", callback_data=f"toggle_channel_{ch_id}")])
        keyboard.append([InlineKeyboardButton("💾 Сохранить каналы", callback_data="save_channel_subscriptions")])
        await update.message.reply_text("📺 Управление подписками на каналы", reply_markup=InlineKeyboardMarkup(keyboard))

    async def cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        data = query.data
        user = query.from_user
        await query.answer()

        # Категории
        if data.startswith("toggle_category_"):
            cid = int(data.split("_")[-1])
            if "selected_categories" not in context.user_data:
                subs = await get_user_subscriptions(user.id)
                context.user_data["selected_categories"] = {s.get("id") for s in (subs or [])}
            sel = context.user_data["selected_categories"]
            if cid in sel:
                sel.remove(cid)
            else:
                sel.add(cid)
            cats = await get_categories()
            keyboard = []
            for c in cats:
                c_id = c.get("id")
                name = c.get("name") or c.get("category_name") or "Без названия"
                emoji = c.get("emoji", "📝")
                mark = "✅" if c_id in sel else "❌"
                keyboard.append([InlineKeyboardButton(f"{mark} {emoji} {name}", callback_data=f"toggle_category_{c_id}")])
            keyboard.append([InlineKeyboardButton("💾 Сохранить", callback_data="save_subscriptions")])
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
            return

        if data == "save_subscriptions":
            # Если пользователь ничего не переключал в этой сессии,
            # сохраняем ТЕКУЩИЕ подписки (не очищаем до нуля)
            if "selected_categories" in context.user_data:
                sel_set = context.user_data.get("selected_categories", set())
            else:
                current = await get_user_subscriptions(user.id)
                sel_set = {c.get("id") for c in (current or [])}

            sel = list(sel_set)
            res = await update_user_subscriptions(user.id, sel)
            if res is not None:
                await query.edit_message_text("✅ Подписки сохранены!")
            else:
                await query.edit_message_text("❌ Ошибка сохранения подписок")
            context.user_data.pop("selected_categories", None)
            return

        # Каналы
        if data.startswith("toggle_channel_"):
            ch_id = int(data.split("_")[-1])
            if "selected_channels" not in context.user_data:
                subs = await get_user_channel_subscriptions(user.id)
                context.user_data["selected_channels"] = {c.get("id") for c in (subs or [])}
            sel = context.user_data["selected_channels"]
            if ch_id in sel:
                sel.remove(ch_id)
            else:
                sel.add(ch_id)
            chans = await get_bot_channels()
            keyboard = []
            for ch in chans:
                c_id = ch.get("id")
                title = ch.get("title") or ch.get("channel_name") or f"Канал {c_id}"
                mark = "✅" if c_id in sel else "❌"
                keyboard.append([InlineKeyboardButton(f"{mark} {title}", callback_data=f"toggle_channel_{c_id}")])
            keyboard.append([InlineKeyboardButton("💾 Сохранить каналы", callback_data="save_channel_subscriptions")])
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
            return

        if data == "save_channel_subscriptions":
            sel = list(context.user_data.get("selected_channels", set()))
            res = await update_user_channel_subscriptions(user.id, sel)
            if res is not None:
                await query.edit_message_text("✅ Подписки на каналы сохранены!")
            else:
                await query.edit_message_text("❌ Ошибка сохранения подписок на каналы")
            context.user_data.pop("selected_channels", None)

    async def digest(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        msg = await update.message.reply_text("🔄 Генерирую ваш персональный дайджест...")
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{backend_url}/api/public-bots/{bot_id}/users/{user.id}/digest"
                logger.info(f"/digest request: bot_id={bot_id}, user_id={user.id}, url={url}")
                async with session.get(url, params={"limit": 15}, timeout=20) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        text = data.get("text") or "❌ Пустой дайджест"
                        await msg.edit_text(text, parse_mode="HTML")
                        return
        except Exception as e:
            logger.error(f"/digest error: {e}")
        await msg.edit_text("❌ Не удалось сформировать дайджест. Попробуйте позже.")

    # Регистрация команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("categories", categories_cmd))
    app.add_handler(CommandHandler("subscribe", subscribe_cmd))
    app.add_handler(CommandHandler("channels", channels_cmd))
    app.add_handler(CommandHandler("digest", digest))
    app.add_handler(CallbackQueryHandler(cb_handler))


async def main():
    bots = await fetch_active_bots()
    logger.info(f"Active bots: {len(bots)}")
    if not bots:
        logger.warning("No active bots found. Exiting idle loop.")

    apps = []
    for bot in bots:
        token = bot.get("bot_token")
        bot_id = bot.get("id")
        if not token or not bot_id:
            logger.warning(f"Skip bot without token/id: {bot}")
            continue
        app = Application.builder().token(token).build()
        register_handlers(app, bot_id)
        apps.append(app)
        logger.info(f"Prepared PTB application for bot_id={bot_id}")

    if apps:
        # Initialize and start all apps, then start polling for each
        for app in apps:
            await app.initialize()
        for app in apps:
            await app.start()
        # Set commands (menu) for each bot
        bot_commands = [
            BotCommand("start", "Начало работы"),
            BotCommand("help", "Справка"),
            BotCommand("categories", "Список категорий"),
            BotCommand("subscribe", "Подписки на категории"),
            BotCommand("channels", "Подписки на каналы"),
            BotCommand("digest", "Персональный дайджест"),
        ]
        for app in apps:
            try:
                # очистим старые меню, затем установим новое для гарантированного обновления
                try:
                    await app.bot.delete_my_commands()
                except Exception:
                    pass
                await app.bot.set_my_commands(bot_commands, scope=BotCommandScopeDefault())
                # продублируем для русской локали, если клиент её использует
                try:
                    await app.bot.set_my_commands(bot_commands, scope=BotCommandScopeDefault(), language_code="ru")
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"set_my_commands failed: {e}")
        for app in apps:
            # start polling concurrently for each app
            await app.updater.start_polling(drop_pending_updates=True)
        logger.info(f"Started {len(apps)} PTB applications (polling)")

        # Keep running
        stop_event = asyncio.Event()
        await stop_event.wait()
    else:
        # Idle loop if no bots yet; poll periodically and try again
        while True:
            await asyncio.sleep(30)
            bots = await fetch_active_bots()
            if bots:
                logger.info("Bots appeared. Restart container to attach.")


if __name__ == "__main__":
    asyncio.run(main())


