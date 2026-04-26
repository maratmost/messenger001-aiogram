"""Bot — HTTP client to Messenger001 Bot API, aiogram-compatible method names."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

import aiohttp

from .exceptions import APIError
from .keyboards import InlineKeyboardMarkup
from .types import BotCommand, FSInputFile, Message, User

if TYPE_CHECKING:
    from .client import DefaultBotProperties

log = logging.getLogger(__name__)

DEFAULT_API_BASE = "https://messenger001.ru/api/v1"


class Bot:
    """aiogram-compatible Bot backed by Messenger001 Bot API.

    Example:
        bot = Bot(token="...")
        await bot.send_message(chat_id=123, text="hello")
    """

    def __init__(
        self,
        token: str,
        api_base: str = DEFAULT_API_BASE,
        session: Optional[aiohttp.ClientSession] = None,
        request_timeout: float = 30.0,
        default: Optional["DefaultBotProperties"] = None,
    ) -> None:
        if not token:
            raise ValueError("token is required")
        self.token = token
        self.api_base = api_base.rstrip("/")
        self._session = session
        self._own_session = session is None
        self._timeout = aiohttp.ClientTimeout(total=request_timeout)
        self._default = default
        self.parse_mode: Optional[str] = (
            default.parse_mode_value if default is not None else None
        )

    @property
    def _url_prefix(self) -> str:
        return f"{self.api_base}/bot/{self.token}"

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
            self._own_session = True
        return self._session

    async def close(self) -> None:
        if self._own_session and self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> "Bot":
        await self._ensure_session()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    # ---------- low-level ----------

    async def _post_json(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._url_prefix}/{method}"
        session = await self._ensure_session()
        async with session.post(url, json=payload) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400 or not data.get("ok", True):
                raise APIError(resp.status, data)
            return data

    async def _post_form(
        self, method: str, fields: dict[str, Any], file_field: str, file: Any
    ) -> dict[str, Any]:
        url = f"{self._url_prefix}/{method}"
        session = await self._ensure_session()
        form = aiohttp.FormData()
        for k, v in fields.items():
            if v is None:
                continue
            if isinstance(v, (dict, list)):
                import json

                form.add_field(k, json.dumps(v), content_type="application/json")
            else:
                form.add_field(k, str(v))
        # file can be FSInputFile, path, Path, bytes, or file-like
        if isinstance(file, FSInputFile):
            p = file.resolve_path()
            form.add_field(file_field, p.read_bytes(), filename=file.filename or p.name)
        elif isinstance(file, (str, Path)):
            p = Path(file)
            form.add_field(file_field, p.read_bytes(), filename=p.name)
        elif isinstance(file, bytes):
            form.add_field(file_field, file, filename=f"{file_field}.bin")
        else:
            form.add_field(file_field, file)
        async with session.post(url, data=form) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400 or not data.get("ok", True):
                raise APIError(resp.status, data)
            return data

    # ---------- aiogram-compatible methods ----------

    async def get_me(self) -> User:
        session = await self._ensure_session()
        async with session.get(f"{self._url_prefix}/getMe") as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400 or not data.get("ok", True):
                raise APIError(resp.status, data)
            result = data.get("result") or {}
            return User(
                id=int(result.get("botId", 0)),
                is_bot=True,
                first_name=result.get("name", ""),
                username=result.get("username"),
            )

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        reply_to_message_id: Optional[int] = None,
        parse_mode: Optional[str] = None,
        **_: Any,
    ) -> Message:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if reply_markup is not None:
            wire = reply_markup.to_m001()
            if wire is not None:
                payload["reply_markup"] = wire
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        effective_parse_mode = parse_mode if parse_mode is not None else self.parse_mode
        if effective_parse_mode is not None:
            payload["parse_mode"] = effective_parse_mode
        data = await self._post_json("sendMessage", payload)
        return self._stub_message(chat_id, data)

    async def edit_message_text(
        self,
        text: str,
        chat_id: Optional[int] = None,
        message_id: Optional[int] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **_: Any,
    ) -> Message:
        if chat_id is None or message_id is None:
            raise ValueError("edit_message_text requires chat_id and message_id")
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        }
        if reply_markup is not None:
            wire = reply_markup.to_m001()
            if wire is not None:
                payload["reply_markup"] = wire
        data = await self._post_json("editMessageText", payload)
        return self._stub_message(chat_id, data)

    async def edit_message_reply_markup(
        self,
        chat_id: int,
        message_id: int,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **_: Any,
    ) -> Message:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
        }
        if reply_markup is not None:
            wire = reply_markup.to_m001()
            payload["reply_markup"] = wire  # may be None to clear
        else:
            payload["reply_markup"] = None
        data = await self._post_json("editMessageReplyMarkup", payload)
        return self._stub_message(chat_id, data)

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False,
        **_: Any,
    ) -> bool:
        payload: dict[str, Any] = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert,
        }
        if text is not None:
            payload["text"] = text
        data = await self._post_json("answerCallbackQuery", payload)
        return bool(data.get("ok"))

    async def set_my_commands(
        self, commands: list[Union[BotCommand, dict[str, str]]], **_: Any
    ) -> list[BotCommand]:
        """Register the bot's command list so clients can show a menu / autocomplete."""
        payload_commands: list[dict[str, str]] = []
        for c in commands:
            if isinstance(c, BotCommand):
                payload_commands.append(c.to_dict())
            elif isinstance(c, dict):
                payload_commands.append(
                    {"command": str(c["command"]), "description": str(c["description"])}
                )
            else:
                raise TypeError("commands must be BotCommand or dict")
        data = await self._post_json("setMyCommands", {"commands": payload_commands})
        return [BotCommand.from_dict(x) for x in (data.get("result") or [])]

    async def delete_my_commands(self, **_: Any) -> bool:
        data = await self._post_json("deleteMyCommands", {})
        return bool(data.get("ok"))

    async def get_my_commands(self, **_: Any) -> list[BotCommand]:
        session = await self._ensure_session()
        async with session.get(f"{self._url_prefix}/getMyCommands") as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400 or not data.get("ok", True):
                raise APIError(resp.status, data)
            return [BotCommand.from_dict(x) for x in (data.get("result") or [])]

    async def send_chat_action(self, chat_id: int, action: str = "typing", **_: Any) -> bool:
        data = await self._post_json("sendTyping", {"chat_id": chat_id})
        return bool(data.get("ok"))

    async def send_photo(
        self,
        chat_id: int,
        photo: Any,
        caption: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **_: Any,
    ) -> Message:
        fields: dict[str, Any] = {"chat_id": chat_id}
        if caption is not None:
            fields["caption"] = caption
        if reply_markup is not None:
            wire = reply_markup.to_m001()
            if wire is not None:
                fields["reply_markup"] = wire
        data = await self._post_form("sendPhoto", fields, "photo", photo)
        return self._stub_message(chat_id, data)

    async def send_document(
        self,
        chat_id: int,
        document: Any,
        caption: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **_: Any,
    ) -> Message:
        return await self._send_media("sendDocument", chat_id, document, caption, reply_markup)

    async def send_video(
        self,
        chat_id: int,
        video: Any,
        caption: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **_: Any,
    ) -> Message:
        return await self._send_media("sendVideo", chat_id, video, caption, reply_markup)

    async def send_audio(
        self,
        chat_id: int,
        audio: Any,
        caption: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **_: Any,
    ) -> Message:
        return await self._send_media("sendAudio", chat_id, audio, caption, reply_markup)

    async def _send_media(
        self,
        method: str,
        chat_id: int,
        file: Any,
        caption: Optional[str],
        reply_markup: Optional[InlineKeyboardMarkup],
    ) -> Message:
        fields: dict[str, Any] = {"chat_id": chat_id}
        if caption is not None:
            fields["caption"] = caption
        if reply_markup is not None:
            wire = reply_markup.to_m001()
            if wire is not None:
                fields["reply_markup"] = wire
        data = await self._post_form(method, fields, "file", file)
        return self._stub_message(chat_id, data)

    # ---------- helpers ----------

    def _stub_message(self, chat_id: int, api_response: dict[str, Any]) -> Message:
        """Build a minimal Message stub from API response (M001 returns only message_id)."""
        import time

        from .types import Chat

        return Message(
            message_id=int(api_response.get("message_id", 0)),
            date=int(time.time()),
            chat=Chat(id=chat_id),
            _bot=self,
        )
