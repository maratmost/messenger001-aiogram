"""Dual-transport: filters реэкспорт. См. ``messenger001_aiogram.dual``."""
from __future__ import annotations

from . import TRANSPORT

if TRANSPORT == "m001":
    from messenger001_aiogram.filters import (  # noqa: F401
        Command,
        CommandStart,
        F,
        StateFilter,
    )
else:
    from aiogram import F  # noqa: F401
    from aiogram.filters import Command, CommandStart, StateFilter  # noqa: F401

__all__ = ["Command", "CommandStart", "F", "StateFilter"]
