"""aiogram-compatible BaseMiddleware.

Subclass and override `__call__(handler, event, data)`. Register via
`router.message.middleware(MyMW())` / `router.callback_query.middleware(MyMW())`,
or use `dispatcher.update.middleware(MyMW())` for an outer (cross-event) chain.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable

Handler = Callable[[Any, dict[str, Any]], Awaitable[Any]]


class BaseMiddleware(ABC):
    """Base class for outer/inner middlewares.

    Implementations call `await handler(event, data)` to continue the chain
    or short-circuit by returning early.
    """

    @abstractmethod
    async def __call__(
        self,
        handler: Handler,
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        raise NotImplementedError
