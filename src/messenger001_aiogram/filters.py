"""aiogram-compatible filters: Command, CommandStart, F-magic."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Optional, Union

from .types import CallbackQuery, Message


class BaseFilter:
    async def __call__(self, event: Any) -> Union[bool, dict[str, Any]]:
        raise NotImplementedError


@dataclass
class Command(BaseFilter):
    commands: tuple[str, ...]
    prefix: str = "/"
    ignore_case: bool = True

    def __init__(self, *commands: str, prefix: str = "/", ignore_case: bool = True):
        self.commands = tuple(c.lstrip("/") for c in commands)
        self.prefix = prefix
        self.ignore_case = ignore_case

    async def __call__(self, event: Any) -> Union[bool, dict[str, Any]]:
        if not isinstance(event, Message) or not event.text:
            return False
        text = event.text.strip()
        if not text.startswith(self.prefix):
            return False
        head, _, args = text[len(self.prefix) :].partition(" ")
        head = head.split("@", 1)[0]  # strip bot mention if any
        candidates = [c.lower() for c in self.commands] if self.ignore_case else list(self.commands)
        head_cmp = head.lower() if self.ignore_case else head
        if head_cmp in candidates:
            return {"command": CommandObject(command=head, args=args or None)}
        return False


@dataclass
class CommandObject:
    command: str
    args: Optional[str] = None


class CommandStart(Command):
    def __init__(self, deep_link: bool = False, **kwargs: Any):
        super().__init__("start", **kwargs)
        self.deep_link = deep_link

    async def __call__(self, event: Any) -> Union[bool, dict[str, Any]]:
        result = await super().__call__(event)
        if not result:
            return False
        if self.deep_link:
            cmd: CommandObject = result["command"]  # type: ignore[assignment]
            if not cmd.args:
                return False
        return result


class _MagicAttribute:
    """Minimal F.attr == value / in / .contains style filter."""

    def __init__(self, attrs: tuple[str, ...] = ()):
        self._attrs = attrs

    def __getattr__(self, name: str) -> "_MagicAttribute":
        return _MagicAttribute(self._attrs + (name,))

    def _resolve(self, event: Any) -> Any:
        v = event
        for a in self._attrs:
            if v is None:
                return None
            v = getattr(v, a, None)
        return v

    def __eq__(self, other: Any) -> "_MagicFilter":  # type: ignore[override]
        return _MagicFilter(lambda e: self._resolve(e) == other)

    def __ne__(self, other: Any) -> "_MagicFilter":  # type: ignore[override]
        return _MagicFilter(lambda e: self._resolve(e) != other)

    def in_(self, values: Any) -> "_MagicFilter":
        return _MagicFilter(lambda e: self._resolve(e) in values)

    def startswith(self, prefix: str) -> "_MagicFilter":
        return _MagicFilter(
            lambda e: isinstance(self._resolve(e), str) and self._resolve(e).startswith(prefix)
        )

    def regexp(self, pattern: str) -> "_MagicFilter":
        rx = re.compile(pattern)
        return _MagicFilter(
            lambda e: isinstance(self._resolve(e), str) and bool(rx.search(self._resolve(e)))
        )


@dataclass
class _MagicFilter(BaseFilter):
    predicate: Callable[[Any], bool]

    async def __call__(self, event: Any) -> bool:
        try:
            return bool(self.predicate(event))
        except Exception:
            return False

    def __and__(self, other: "_MagicFilter") -> "_MagicFilter":
        return _MagicFilter(lambda e: self.predicate(e) and other.predicate(e))

    def __or__(self, other: "_MagicFilter") -> "_MagicFilter":
        return _MagicFilter(lambda e: self.predicate(e) or other.predicate(e))


# Public magic root — `F.data == "..."`, `F.text.startswith("...")`, etc.
F = _MagicAttribute()
