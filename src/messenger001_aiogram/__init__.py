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
from .dispatcher import Dispatcher, Router
from .filters import Command, CommandStart, F
from .fsm import FSMContext, MemoryStorage, State, StatesGroup
from .keyboards import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup
from .types import CallbackQuery, Chat, Message, Update, User
from .webhook import build_webhook_app, start_webhook

__version__ = "0.1.0"

__all__ = [
    "Bot",
    "Dispatcher",
    "Router",
    "F",
    "Command",
    "CommandStart",
    "Message",
    "CallbackQuery",
    "Chat",
    "User",
    "Update",
    "InlineKeyboardMarkup",
    "InlineKeyboardButton",
    "InlineKeyboardBuilder",
    "State",
    "StatesGroup",
    "MemoryStorage",
    "FSMContext",
    "build_webhook_app",
    "start_webhook",
]
