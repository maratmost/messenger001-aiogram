"""Dual-transport: types реэкспорт. См. ``messenger001_aiogram.dual``."""
from __future__ import annotations

from . import TRANSPORT

if TRANSPORT == "m001":
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
        Message,
        TelegramObject,
        Update,
        User,
    )

__all__ = [
    "BotCommand",
    "CallbackQuery",
    "Chat",
    "FSInputFile",
    "Message",
    "TelegramObject",
    "Update",
    "User",
]
