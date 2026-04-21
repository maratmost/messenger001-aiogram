"""Minimal FSM: MemoryStorage + FSMContext + State/StatesGroup, aiogram-compatible."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional


class State:
    def __init__(self, state: Optional[str] = None):
        self._state = state
        self._group: Optional[str] = None
        self._name: Optional[str] = None

    def __set_name__(self, owner: type, name: str) -> None:
        self._group = owner.__name__
        self._name = name

    @property
    def state(self) -> str:
        if self._state:
            return self._state
        return f"{self._group}:{self._name}"

    def __eq__(self, other: Any) -> bool:  # type: ignore[override]
        if isinstance(other, State):
            return self.state == other.state
        if isinstance(other, str):
            return self.state == other
        return False

    def __hash__(self) -> int:
        return hash(self.state)


class StatesGroup:
    """Base class. Define states as class-level `State()`."""

    @classmethod
    def states(cls) -> list[State]:
        return [v for v in cls.__dict__.values() if isinstance(v, State)]


@dataclass
class _Record:
    state: Optional[str] = None
    data: dict[str, Any] = field(default_factory=dict)


class MemoryStorage:
    """In-process FSM storage keyed by (chat_id, user_id). Not safe across restarts."""

    def __init__(self) -> None:
        self._store: dict[tuple[int, int], _Record] = {}
        self._lock = asyncio.Lock()

    async def get(self, chat_id: int, user_id: int) -> _Record:
        async with self._lock:
            return self._store.setdefault((chat_id, user_id), _Record())

    async def set_state(self, chat_id: int, user_id: int, state: Optional[str]) -> None:
        async with self._lock:
            rec = self._store.setdefault((chat_id, user_id), _Record())
            rec.state = state

    async def set_data(self, chat_id: int, user_id: int, data: dict[str, Any]) -> None:
        async with self._lock:
            rec = self._store.setdefault((chat_id, user_id), _Record())
            rec.data = dict(data)

    async def update_data(self, chat_id: int, user_id: int, data: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            rec = self._store.setdefault((chat_id, user_id), _Record())
            rec.data.update(data)
            return dict(rec.data)


class FSMContext:
    def __init__(self, storage: MemoryStorage, chat_id: int, user_id: int) -> None:
        self.storage = storage
        self.chat_id = chat_id
        self.user_id = user_id

    async def set_state(self, state: Optional[object] = None) -> None:
        value: Optional[str]
        if state is None:
            value = None
        elif isinstance(state, State):
            value = state.state
        else:
            value = str(state)
        await self.storage.set_state(self.chat_id, self.user_id, value)

    async def get_state(self) -> Optional[str]:
        rec = await self.storage.get(self.chat_id, self.user_id)
        return rec.state

    async def clear(self) -> None:
        await self.storage.set_state(self.chat_id, self.user_id, None)
        await self.storage.set_data(self.chat_id, self.user_id, {})

    async def update_data(self, **kwargs: Any) -> dict[str, Any]:
        return await self.storage.update_data(self.chat_id, self.user_id, kwargs)

    async def set_data(self, data: dict[str, Any]) -> None:
        await self.storage.set_data(self.chat_id, self.user_id, data)

    async def get_data(self) -> dict[str, Any]:
        rec = await self.storage.get(self.chat_id, self.user_id)
        return dict(rec.data)
