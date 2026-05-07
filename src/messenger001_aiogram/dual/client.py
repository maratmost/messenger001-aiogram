"""Dual-transport: client (DefaultBotProperties) реэкспорт.
См. ``messenger001_aiogram.dual``.
"""
from __future__ import annotations

from . import TRANSPORT

if TRANSPORT == "m001":
    from messenger001_aiogram.client import DefaultBotProperties  # noqa: F401
else:
    from aiogram.client.default import DefaultBotProperties  # noqa: F401

__all__ = ["DefaultBotProperties"]
