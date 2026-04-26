"""aiogram-compatible Bot client defaults.

Mirrors `aiogram.client.default.DefaultBotProperties`:

    Bot(token=..., default=DefaultBotProperties(parse_mode=ParseMode.HTML))
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from .enums import ParseMode


@dataclass
class DefaultBotProperties:
    parse_mode: Optional[Union[ParseMode, str]] = None
    disable_notification: Optional[bool] = None
    protect_content: Optional[bool] = None

    @property
    def parse_mode_value(self) -> Optional[str]:
        if self.parse_mode is None:
            return None
        if isinstance(self.parse_mode, ParseMode):
            return self.parse_mode.value
        return str(self.parse_mode)
