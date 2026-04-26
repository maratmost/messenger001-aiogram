"""aiogram-compatible filters: Command, CommandStart, StateFilter, F-magic."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Optional, Union

from .fsm import FSMContext, State
from .types import CallbackQuery, Message


class BaseFilter:
    async def __call__(self, event: Any) -> Union[bool, dict[str, Any]]:
        raise NotImplementedError


class StateFilter(BaseFilter):
    """Filter by current FSM state.

    Usage::

        from messenger001_aiogram.filters import StateFilter
        @router.message(StateFilter("OnboardingFlow:waiting_email"))
        async def handler(...): ...

        @router.message(StateFilter(OnboardingFlow.waiting_email))
        async def handler(...): ...

        @router.message(StateFilter(None))  # only when no state is set
        async def handler(...): ...

        @router.message(StateFilter("*"))  # any state
        async def handler(...): ...
    """

    def __init__(self, *states: Any):
        self._states: tuple[Any, ...] = states

    def _matches(self, current: Optional[str]) -> bool:
        for s in self._states:
            if s == "*":
                if current is not None:
                    return True
            elif s is None:
                if current is None:
                    return True
            elif isinstance(s, State):
                if current == s.state:
                    return True
            else:
                if current == str(s):
                    return True
        return False

    async def __call__(  # type: ignore[override]
        self, event: Any, data: Optional[dict[str, Any]] = None
    ) -> bool:
        ctx: Optional[FSMContext] = (data or {}).get("state") if data else None
        if ctx is None:
            return False
        current = await ctx.get_state()
        return self._matches(current)


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
    """F-magic with attribute access AND method invocation.

    Supports::
        F.text == "ok"
        F.text.lower() == "ok"
        F.text.casefold().in_({"a", "b"})
        F.data.startswith("buy_")
    """

    def __init__(self, ops: tuple[tuple[Any, ...], ...] = ()):
        # each op is ("attr", name) or ("call", args, kwargs)
        self._ops = ops

    def __getattr__(self, name: str) -> "_MagicAttribute":
        # protect dunder lookups (pickle, copy, etc.) from being captured
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        return _MagicAttribute(self._ops + (("attr", name),))

    def __call__(self, *args: Any, **kwargs: Any) -> "_MagicAttribute":
        return _MagicAttribute(self._ops + (("call", args, kwargs),))

    def _resolve(self, event: Any) -> Any:
        v: Any = event
        for op in self._ops:
            if v is None:
                return None
            kind = op[0]
            if kind == "attr":
                v = getattr(v, op[1], None)
            elif kind == "call":
                if not callable(v):
                    return None
                try:
                    v = v(*op[1], **op[2])
                except Exception:
                    return None
        return v

    def __eq__(self, other: Any) -> "_MagicFilter":  # type: ignore[override]
        return _MagicFilter(lambda e: self._resolve(e) == other)

    def __ne__(self, other: Any) -> "_MagicFilter":  # type: ignore[override]
        return _MagicFilter(lambda e: self._resolve(e) != other)

    def __invert__(self) -> "_MagicFilter":
        # Bare `~F.text` — true when value is falsy.
        return _MagicFilter(lambda e: not self._resolve(e))

    def __bool__(self) -> bool:
        # Defensive: prevent accidental `bool(F.text)` short-circuiting in user code.
        raise TypeError("Magic filter cannot be used in boolean context")

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

    # Bare-attribute filter mode: `@router.message(F.text)` means "F.text is truthy".
    async def _as_filter(self, event: Any) -> bool:
        return bool(self._resolve(event))


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

    def __invert__(self) -> "_MagicFilter":
        return _MagicFilter(lambda e: not self.predicate(e))


# Public magic root — `F.data == "..."`, `F.text.startswith("...")`, etc.
F = _MagicAttribute()
