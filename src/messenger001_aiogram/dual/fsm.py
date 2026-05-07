"""Dual-transport: FSM реэкспорт. См. ``messenger001_aiogram.dual``."""
from __future__ import annotations

from . import TRANSPORT

if TRANSPORT == "m001":
    from messenger001_aiogram.fsm import (  # noqa: F401
        FSMContext,
        MemoryStorage,
        RedisStorage,
        State,
        StatesGroup,
    )
else:
    from aiogram.fsm.context import FSMContext  # noqa: F401
    from aiogram.fsm.state import State, StatesGroup  # noqa: F401
    from aiogram.fsm.storage.memory import MemoryStorage  # noqa: F401

    try:
        from aiogram.fsm.storage.redis import RedisStorage  # noqa: F401
    except ImportError:  # pragma: no cover
        # aiogram + redis нужен extra; на TG-режиме без redis Redis не доступен.
        # Используй MemoryStorage если RedisStorage не доступен.
        RedisStorage = None  # type: ignore[assignment, misc]

__all__ = ["FSMContext", "MemoryStorage", "RedisStorage", "State", "StatesGroup"]
