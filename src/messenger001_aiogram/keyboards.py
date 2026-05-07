"""Keyboards — aiogram-compatible shapes, M001 wire format.

Both inline (``InlineKeyboardMarkup`` — buttons under the message, callback_query
on tap) and reply (``ReplyKeyboardMarkup`` — bottom-panel buttons that send their
text as a regular user message) keyboards are first-class since v0.1.0a5.

``Bot.send_message`` and friends accept a single ``reply_markup`` parameter
(matching aiogram) and dispatch internally:

  * ``InlineKeyboardMarkup`` → wire field ``reply_markup``
  * ``ReplyKeyboardMarkup``  → wire field ``reply_keyboard``

Backend forbids both fields in one call. ``ReplyKeyboardRemove`` is currently
a stub (``to_m001()`` returns ``None``) — backend support is planned.
"""
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


# --------------------------------------------------------------------------
# Reply keyboards — bottom-panel buttons (Telegram-style "reply keyboard")
# --------------------------------------------------------------------------


@dataclass
class KeyboardButton:
    """Кнопка reply-клавиатуры. Текст обязателен; флаги request_contact /
    request_location декодируются клиентом (если поддерживает; iOS пока игнорит).
    """

    text: str
    request_contact: bool = False
    request_location: bool = False

    def to_m001(self) -> dict[str, Any]:
        out: dict[str, Any] = {"text": self.text}
        if self.request_contact:
            out["request_contact"] = True
        if self.request_location:
            out["request_location"] = True
        return out


@dataclass
class ReplyKeyboardMarkup:
    """Reply-клавиатура: ряды кнопок над input bar. Tap по кнопке = юзер
    отправил её text в чат как обычное сообщение. См. wire-формат в
    docs/webhook-spec.md (поле ``reply_keyboard``).
    """

    keyboard: list[list[KeyboardButton]] = field(default_factory=list)
    resize_keyboard: bool = False
    one_time_keyboard: bool = False
    selective: bool = False
    input_field_placeholder: Optional[str] = None

    def to_m001(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "keyboard": [[btn.to_m001() for btn in row] for row in self.keyboard],
            "resize_keyboard": self.resize_keyboard,
            "one_time_keyboard": self.one_time_keyboard,
            "selective": self.selective,
        }
        if self.input_field_placeholder is not None:
            out["input_field_placeholder"] = self.input_field_placeholder
        return out


@dataclass
class ReplyKeyboardRemove:
    """Сигнал клиенту "снять reply-клавиатуру". Backend пока не поддерживает —
    ``to_m001()`` возвращает None, ``Bot.send_message`` опустит поле. Для снятия
    клавиатуры используй ``edit_message_text(..., reply_keyboard=None)`` с
    explicit None — это поддерживается.
    """

    remove_keyboard: bool = True
    selective: bool = False

    def to_m001(self) -> Optional[dict[str, Any]]:
        return None
