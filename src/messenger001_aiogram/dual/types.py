"""Dual-transport: types реэкспорт. См. ``messenger001_aiogram.dual``.

Для совместимости с aiogram, ``InlineKeyboardButton`` / ``InlineKeyboardMarkup``
/ ``KeyboardButton`` / ``ReplyKeyboardMarkup`` / ``ReplyKeyboardRemove`` тоже
доступны через ``.types`` (aiogram держит их в ``aiogram.types``, многие
проекты импортируют именно так — мы зеркалим поведение).
"""
from __future__ import annotations

from . import TRANSPORT

if TRANSPORT == "m001":
    from messenger001_aiogram.keyboards import (  # noqa: F401
        InlineKeyboardButton,
        InlineKeyboardMarkup,
        KeyboardButton,
        ReplyKeyboardMarkup,
        ReplyKeyboardRemove,
    )
    from messenger001_aiogram.types import (  # noqa: F401
        BotCommand,
        CallbackQuery,
        Chat,
        FSInputFile,
        Message,
        TelegramObject,
        Update,
        User,
    )
else:
    from aiogram.types import (  # noqa: F401
        BotCommand,
        CallbackQuery,
        Chat,
        FSInputFile,
        InlineKeyboardButton,
        InlineKeyboardMarkup,
        KeyboardButton,
        Message,
        ReplyKeyboardMarkup,
        ReplyKeyboardRemove,
        TelegramObject,
        Update,
        User,
    )

__all__ = [
    "BotCommand",
    "CallbackQuery",
    "Chat",
    "FSInputFile",
    "InlineKeyboardButton",
    "InlineKeyboardMarkup",
    "KeyboardButton",
    "Message",
    "ReplyKeyboardMarkup",
    "ReplyKeyboardRemove",
    "TelegramObject",
    "Update",
    "User",
]
