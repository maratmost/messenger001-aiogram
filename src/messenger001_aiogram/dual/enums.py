"""Dual-transport: enums (ChatAction, ParseMode) реэкспорт.
См. ``messenger001_aiogram.dual``.
"""
from __future__ import annotations

from . import TRANSPORT

if TRANSPORT == "m001":
    from messenger001_aiogram.enums import ChatAction, ParseMode  # noqa: F401
else:
    from aiogram.enums import ChatAction, ParseMode  # noqa: F401

__all__ = ["ChatAction", "ParseMode"]
