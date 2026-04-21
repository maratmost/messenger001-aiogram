"""Inline keyboards — aiogram-compatible shapes, M001 wire format."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class InlineKeyboardButton:
    text: str
    callback_data: Optional[str] = None
    url: Optional[str] = None

    def to_m001(self) -> dict[str, Any]:
        out: dict[str, Any] = {"text": self.text}
        if self.callback_data is not None:
            out["callback_data"] = self.callback_data
        if self.url is not None:
            out["url"] = self.url
        return out


@dataclass
class InlineKeyboardMarkup:
    inline_keyboard: list[list[InlineKeyboardButton]] = field(default_factory=list)

    def to_m001(self) -> dict[str, Any]:
        return {
            "inline_keyboard": [
                [btn.to_m001() for btn in row] for row in self.inline_keyboard
            ]
        }


class InlineKeyboardBuilder:
    """Minimal aiogram-compatible InlineKeyboardBuilder."""

    def __init__(self) -> None:
        self._rows: list[list[InlineKeyboardButton]] = [[]]

    def button(
        self,
        text: str,
        callback_data: Optional[str] = None,
        url: Optional[str] = None,
    ) -> "InlineKeyboardBuilder":
        self._rows[-1].append(
            InlineKeyboardButton(text=text, callback_data=callback_data, url=url)
        )
        return self

    def row(self, *buttons: InlineKeyboardButton) -> "InlineKeyboardBuilder":
        if buttons:
            self._rows.append(list(buttons))
        else:
            self._rows.append([])
        return self

    def adjust(self, *sizes: int) -> "InlineKeyboardBuilder":
        flat = [b for row in self._rows for b in row]
        self._rows = []
        idx = 0
        for size in sizes:
            if idx >= len(flat):
                break
            self._rows.append(flat[idx : idx + size])
            idx += size
        if idx < len(flat):
            self._rows.append(flat[idx:])
        if not self._rows:
            self._rows = [[]]
        return self

    def as_markup(self) -> InlineKeyboardMarkup:
        rows = [r for r in self._rows if r]
        return InlineKeyboardMarkup(inline_keyboard=rows)
