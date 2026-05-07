"""Dual-transport shim: один кодеbase для Telegram (через aiogram) и
Messenger001 (через messenger001-aiogram).

Использование (вместо `from messenger001_aiogram import ...`):

    from messenger001_aiogram.dual import Bot, Dispatcher, F, Router

Транспорт выбирается переменной окружения ``TRANSPORT``:

* ``TRANSPORT=telegram`` (default) → реэкспорт из ``aiogram``.
* ``TRANSPORT=m001``               → реэкспорт из ``messenger001_aiogram``.

Поскольку наш SDK API-совместим с aiogram, handler-код один и тот же —
deployment-инстанции отличаются только переменной окружения и токеном.

Submodule также имеет ``messenger001_aiogram.dual.filters`` /
``messenger001_aiogram.dual.types`` / ``messenger001_aiogram.dual.fsm`` /
``messenger001_aiogram.dual.keyboards`` /
``messenger001_aiogram.dual.client`` / ``messenger001_aiogram.dual.enums``
с тем же switch-механизмом.

Зависимость от ``aiogram`` — soft: пакет нужен только при ``TRANSPORT=telegram``.
``pip install messenger001-aiogram[telegram]`` поставит aiogram автоматически
(см. extras в pyproject.toml).
"""
from __future__ import annotations

import os
from typing import Literal

TransportName = Literal["telegram", "m001"]

_RAW = os.environ.get("TRANSPORT", "telegram").strip().lower()
if _RAW not in ("telegram", "m001"):
    raise RuntimeError(
        f"Unknown TRANSPORT={_RAW!r}. Set TRANSPORT=telegram or TRANSPORT=m001."
    )
TRANSPORT: TransportName = _RAW  # type: ignore[assignment]

if TRANSPORT == "m001":
    from messenger001_aiogram import (  # noqa: F401
        BaseMiddleware,
        Bot,
        Dispatcher,
        F,
        Router,
    )
else:
    try:
        from aiogram import (  # noqa: F401
            BaseMiddleware,
            Bot,
            Dispatcher,
            F,
            Router,
        )
    except ImportError as e:  # pragma: no cover
        raise RuntimeError(
            "TRANSPORT=telegram requires aiogram to be installed. "
            "Either set TRANSPORT=m001 or `pip install aiogram` "
            "(or `pip install messenger001-aiogram[telegram]`)."
        ) from e

__all__ = ["BaseMiddleware", "Bot", "Dispatcher", "F", "Router", "TRANSPORT"]
