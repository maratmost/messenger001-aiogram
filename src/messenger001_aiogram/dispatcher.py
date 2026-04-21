"""Dispatcher + Router — aiogram 3.x compatible subset."""
from __future__ import annotations

import asyncio
import inspect
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional, Union

from .bot import Bot
from .filters import BaseFilter, _MagicFilter
from .fsm import FSMContext, MemoryStorage
from .types import CallbackQuery, Message, Update

log = logging.getLogger(__name__)

Handler = Callable[..., Awaitable[Any]]
FilterLike = Union[BaseFilter, _MagicFilter, Callable[[Any], Awaitable[bool]]]


@dataclass
class _HandlerEntry:
    callback: Handler
    filters: tuple[FilterLike, ...] = ()


class _Observer:
    def __init__(self, event_type: str):
        self._event_type = event_type
        self._handlers: list[_HandlerEntry] = []

    def register(self, callback: Handler, *filters: FilterLike) -> None:
        self._handlers.append(_HandlerEntry(callback=callback, filters=tuple(filters)))

    def __call__(self, *filters: FilterLike) -> Callable[[Handler], Handler]:
        def decorator(handler: Handler) -> Handler:
            self.register(handler, *filters)
            return handler

        return decorator

    async def trigger(self, event: Any, context: dict[str, Any]) -> bool:
        for entry in self._handlers:
            extra: dict[str, Any] = {}
            matched = True
            for f in entry.filters:
                result = await _apply_filter(f, event)
                if result is False or result is None:
                    matched = False
                    break
                if isinstance(result, dict):
                    extra.update(result)
            if not matched:
                continue
            await _invoke(entry.callback, event, {**context, **extra})
            return True
        return False


async def _apply_filter(f: FilterLike, event: Any) -> Any:
    if hasattr(f, "__call__"):
        res = f(event)
        if inspect.isawaitable(res):
            return await res
        return res
    return False


async def _invoke(callback: Handler, event: Any, context: dict[str, Any]) -> None:
    sig = inspect.signature(callback)
    kwargs: dict[str, Any] = {}
    for name, param in sig.parameters.items():
        if name in ("self", "cls"):
            continue
        if name == list(sig.parameters)[0]:
            # first positional is the event
            continue
        if name in context:
            kwargs[name] = context[name]
        elif param.default is inspect.Parameter.empty:
            # Unfilled required kwarg — pass None; handler author sees it.
            kwargs[name] = None
    await callback(event, **kwargs)


class Router:
    def __init__(self, name: Optional[str] = None):
        self.name = name or "router"
        self.message = _Observer("message")
        self.callback_query = _Observer("callback_query")
        self._sub_routers: list["Router"] = []

    def include_router(self, router: "Router") -> None:
        self._sub_routers.append(router)

    async def _dispatch(self, update: Update, context: dict[str, Any]) -> bool:
        if update.message is not None:
            if await self.message.trigger(update.message, context):
                return True
        if update.callback_query is not None:
            if await self.callback_query.trigger(update.callback_query, context):
                return True
        for sub in self._sub_routers:
            if await sub._dispatch(update, context):
                return True
        return False


class Dispatcher(Router):
    def __init__(self, storage: Optional[MemoryStorage] = None, **_: Any):
        super().__init__(name="dispatcher")
        self.storage = storage or MemoryStorage()

    def _context_for(self, update: Update, bot: Bot) -> dict[str, Any]:
        chat_id: Optional[int] = None
        user_id: Optional[int] = None
        if update.message is not None:
            chat_id = update.message.chat.id
            user_id = update.message.from_user.id if update.message.from_user else chat_id
        elif update.callback_query is not None and update.callback_query.message is not None:
            chat_id = update.callback_query.message.chat.id
            user_id = update.callback_query.from_user.id
        state: Optional[FSMContext] = None
        if chat_id is not None and user_id is not None:
            state = FSMContext(self.storage, chat_id=chat_id, user_id=user_id)
        return {"bot": bot, "state": state, "dispatcher": self}

    async def feed_update(self, bot: Bot, update: Union[Update, dict[str, Any]]) -> bool:
        if isinstance(update, dict):
            update = Update.from_m001(update, bot)
        context = self._context_for(update, bot)
        try:
            return await self._dispatch(update, context)
        except Exception:
            log.exception("Handler failed for update_id=%s", update.update_id)
            return False

    async def feed_webhook_update(
        self, bot: Bot, update_data: dict[str, Any]
    ) -> bool:
        return await self.feed_update(bot, update_data)

    # aiogram parity: start_polling is a no-op (M001 is webhook-only)
    async def start_polling(self, *_: Any, **__: Any) -> None:
        raise RuntimeError(
            "Messenger001 is webhook-only. Use `start_webhook(...)` from "
            "messenger001_aiogram.webhook instead of start_polling."
        )
