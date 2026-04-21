"""Minimal echo bot + inline keyboard + edit demo.

Run:
    export M001_TOKEN=<test_bot_token>
    export M001_API_BASE=https://messenger001.ru/api/v1   # optional
    python examples/echo_bot.py

Then register webhook URL (http://<your-host>:8080/webhook) for the bot
via BotFather in Messenger001.
"""
from __future__ import annotations

import asyncio
import logging
import os

from messenger001_aiogram import (
    Bot,
    CallbackQuery,
    Dispatcher,
    F,
    InlineKeyboardBuilder,
    Message,
    start_webhook,
)
from messenger001_aiogram.filters import Command, CommandStart

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ["M001_TOKEN"]
API_BASE = os.environ.get("M001_API_BASE", "https://messenger001.ru/api/v1")
WEBHOOK_SECRET = os.environ.get("M001_WEBHOOK_SECRET")

dp = Dispatcher()


@dp.message(CommandStart())
async def on_start(msg: Message) -> None:
    kb = InlineKeyboardBuilder()
    kb.button(text="Ping", callback_data="ping")
    kb.button(text="Меню", callback_data="menu")
    kb.adjust(2)
    await msg.answer(
        "Привет! Я тестовый бот на messenger001-aiogram.",
        reply_markup=kb.as_markup(),
    )


@dp.message(Command("help"))
async def on_help(msg: Message) -> None:
    await msg.answer("Команды: /start, /help. Жми кнопки под сообщением.")


@dp.message()
async def on_any(msg: Message) -> None:
    if msg.text:
        await msg.answer(f"Ты сказал: {msg.text}")


@dp.callback_query(F.data == "ping")
async def on_ping(call: CallbackQuery) -> None:
    await call.answer("pong")
    if call.message:
        await call.message.edit_text("pong 🏓 (нажми ещё раз на «Меню»)")


@dp.callback_query(F.data == "menu")
async def on_menu(call: CallbackQuery) -> None:
    await call.answer()
    kb = InlineKeyboardBuilder()
    kb.button(text="Ping", callback_data="ping")
    kb.button(text="Закрыть", callback_data="close")
    kb.adjust(2)
    if call.message:
        await call.message.edit_text("Меню:", reply_markup=kb.as_markup())


@dp.callback_query(F.data == "close")
async def on_close(call: CallbackQuery) -> None:
    await call.answer("Закрыто")
    if call.message:
        await call.message.edit_text("— закрыто —")


async def main() -> None:
    async with Bot(token=TOKEN, api_base=API_BASE) as bot:
        me = await bot.get_me()
        logging.info("Bot: %s (@%s)", me.first_name, me.username)
        await start_webhook(dp, bot, host="0.0.0.0", port=8080, secret=WEBHOOK_SECRET)


if __name__ == "__main__":
    asyncio.run(main())
