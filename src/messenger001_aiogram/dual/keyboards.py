"""Dual-transport: keyboards реэкспорт. См. ``messenger001_aiogram.dual``."""
from __future__ import annotations

from . import TRANSPORT

if TRANSPORT == "m001":
    from messenger001_aiogram.keyboards import (  # noqa: F401
        InlineKeyboardBuilder,
        InlineKeyboardButton,
        InlineKeyboardMarkup,
        KeyboardButton,
        ReplyKeyboardMarkup,
        ReplyKeyboardRemove,
    )
else:
    from aiogram.types import (  # noqa: F401
        InlineKeyboardButton,
        InlineKeyboardMarkup,
        KeyboardButton,
        ReplyKeyboardMarkup,
        ReplyKeyboardRemove,
    )
    from aiogram.utils.keyboard import InlineKeyboardBuilder  # noqa: F401

__all__ = [
    "InlineKeyboardBuilder",
    "InlineKeyboardButton",
    "InlineKeyboardMarkup",
    "KeyboardButton",
    "ReplyKeyboardMarkup",
    "ReplyKeyboardRemove",
]
