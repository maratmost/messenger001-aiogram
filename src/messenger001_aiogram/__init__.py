"""messenger001-aiogram — aiogram-compatible SDK for Messenger001 Bot API.

Minimal migration:

    # Before:
    from aiogram import Bot, Dispatcher, F
    from aiogram.filters import Command, CommandStart
    from aiogram.types import Message, CallbackQuery
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    # After:
    from messenger001_aiogram import Bot, Dispatcher, F
    from messenger001_aiogram.filters import Command, CommandStart
    from messenger001_aiogram.types import Message, CallbackQuery
    from messenger001_aiogram.keyboards import InlineKeyboardBuilder
"""
from .bot import Bot
from .client import DefaultBotProperties
from .dispatcher import Dispatcher, Router
from .enums import ChatAction, ParseMode
from .filters import Command, CommandStart, F, StateFilter
from .fsm import FSMContext, MemoryStorage, RedisStorage, State, StatesGroup
from .keyboards import (
    InlineKeyboardBuilder,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from .middleware import BaseMiddleware
from .types import BotCommand, CallbackQuery, Chat, FSInputFile, Message, TelegramObject, Update, User
from .webhook import build_webhook_app, start_webhook

try:
    from importlib.metadata import PackageNotFoundError, version

    __version__ = version("messenger001-aiogram")
except (ImportError, PackageNotFoundError):  # pragma: no cover
    # Editable install / тест без установки — единственный источник истины это pyproject.toml.
    __version__ = "0.0.0+unknown"

__all__ = [
    "Bot",
    "Dispatcher",
    "Router",
    "F",
    "Command",
    "CommandStart",
    "StateFilter",
    "Message",
    "CallbackQuery",
    "Chat",
    "User",
    "Update",
    "BotCommand",
    "FSInputFile",
    "TelegramObject",
    "InlineKeyboardMarkup",
    "InlineKeyboardButton",
    "InlineKeyboardBuilder",
    "KeyboardButton",
    "ReplyKeyboardMarkup",
    "ReplyKeyboardRemove",
    "State",
    "StatesGroup",
    "MemoryStorage",
    "RedisStorage",
    "FSMContext",
    "BaseMiddleware",
    "DefaultBotProperties",
    "ParseMode",
    "ChatAction",
    "build_webhook_app",
    "start_webhook",
]
