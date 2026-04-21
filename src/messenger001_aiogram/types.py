"""aiogram-compatible data types mapped to Messenger001 Bot API."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .bot import Bot
    from .keyboards import InlineKeyboardMarkup


@dataclass
class User:
    id: int
    is_bot: bool = False
    first_name: str = ""
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() if self.last_name else self.first_name

    @classmethod
    def from_m001(cls, data: dict[str, Any]) -> "User":
        return cls(
            id=int(data.get("id", 0)),
            is_bot=bool(data.get("is_bot", False)),
            first_name=data.get("first_name") or data.get("name") or "",
            last_name=data.get("last_name"),
            username=data.get("username") or data.get("nick"),
            language_code=data.get("language_code"),
        )


@dataclass
class Chat:
    id: int
    type: str = "private"
    title: Optional[str] = None
    username: Optional[str] = None

    @classmethod
    def from_m001(cls, data: dict[str, Any]) -> "Chat":
        return cls(
            id=int(data.get("id", 0)),
            type=data.get("type", "private"),
            title=data.get("title"),
            username=data.get("username"),
        )


@dataclass
class Message:
    message_id: int
    date: int
    chat: Chat
    from_user: Optional[User] = None
    text: Optional[str] = None
    caption: Optional[str] = None
    reply_to_message: Optional["Message"] = None
    _bot: Optional["Bot"] = field(default=None, repr=False)

    @property
    def bot(self) -> "Bot":
        if self._bot is None:
            raise RuntimeError("Message is not bound to a Bot instance")
        return self._bot

    @classmethod
    def from_m001(cls, data: dict[str, Any], bot: "Bot") -> "Message":
        reply = None
        if data.get("reply_to_message"):
            reply = cls.from_m001(data["reply_to_message"], bot)
        return cls(
            message_id=int(data.get("message_id", 0)),
            date=int(data.get("date", 0)),
            chat=Chat.from_m001(data.get("chat") or {}),
            from_user=User.from_m001(data["from"]) if data.get("from") else None,
            text=data.get("text"),
            caption=data.get("caption"),
            reply_to_message=reply,
            _bot=bot,
        )

    async def answer(
        self,
        text: str,
        reply_markup: Optional["InlineKeyboardMarkup"] = None,
        **kwargs: Any,
    ) -> "Message":
        return await self.bot.send_message(
            chat_id=self.chat.id, text=text, reply_markup=reply_markup, **kwargs
        )

    async def reply(
        self,
        text: str,
        reply_markup: Optional["InlineKeyboardMarkup"] = None,
        **kwargs: Any,
    ) -> "Message":
        return await self.bot.send_message(
            chat_id=self.chat.id,
            text=text,
            reply_markup=reply_markup,
            reply_to_message_id=self.message_id,
            **kwargs,
        )

    async def edit_text(
        self,
        text: str,
        reply_markup: Optional["InlineKeyboardMarkup"] = None,
        **kwargs: Any,
    ) -> "Message":
        return await self.bot.edit_message_text(
            chat_id=self.chat.id,
            message_id=self.message_id,
            text=text,
            reply_markup=reply_markup,
            **kwargs,
        )

    async def edit_reply_markup(
        self,
        reply_markup: Optional["InlineKeyboardMarkup"] = None,
        **kwargs: Any,
    ) -> "Message":
        return await self.bot.edit_message_reply_markup(
            chat_id=self.chat.id,
            message_id=self.message_id,
            reply_markup=reply_markup,
            **kwargs,
        )

    async def answer_photo(self, photo: Any, caption: Optional[str] = None, **kwargs: Any) -> "Message":
        return await self.bot.send_photo(chat_id=self.chat.id, photo=photo, caption=caption, **kwargs)

    async def answer_document(self, document: Any, caption: Optional[str] = None, **kwargs: Any) -> "Message":
        return await self.bot.send_document(chat_id=self.chat.id, document=document, caption=caption, **kwargs)


@dataclass
class CallbackQuery:
    id: str
    from_user: User
    data: Optional[str] = None
    message: Optional[Message] = None
    _bot: Optional["Bot"] = field(default=None, repr=False)

    @property
    def bot(self) -> "Bot":
        if self._bot is None:
            raise RuntimeError("CallbackQuery is not bound to a Bot instance")
        return self._bot

    @classmethod
    def from_m001(cls, data: dict[str, Any], bot: "Bot") -> "CallbackQuery":
        msg = Message.from_m001(data["message"], bot) if data.get("message") else None
        return cls(
            id=str(data.get("id", "")),
            from_user=User.from_m001(data["from"]) if data.get("from") else User(id=0),
            data=data.get("data"),
            message=msg,
            _bot=bot,
        )

    async def answer(self, text: Optional[str] = None, show_alert: bool = False, **kwargs: Any) -> bool:
        return await self.bot.answer_callback_query(
            callback_query_id=self.id, text=text, show_alert=show_alert, **kwargs
        )


@dataclass
class Update:
    update_id: int
    message: Optional[Message] = None
    callback_query: Optional[CallbackQuery] = None

    @classmethod
    def from_m001(cls, data: dict[str, Any], bot: "Bot") -> "Update":
        return cls(
            update_id=int(data.get("update_id", 0)),
            message=Message.from_m001(data["message"], bot) if data.get("message") else None,
            callback_query=CallbackQuery.from_m001(data["callback_query"], bot)
            if data.get("callback_query")
            else None,
        )
