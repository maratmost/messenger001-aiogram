# API Reference — messenger001-aiogram

Полная карта соответствия aiogram 3.x ↔ messenger001-aiogram. Всё, что отмечено как поддерживаемое, имеет ту же сигнатуру и поведение, что и в aiogram (в пределах возможностей платформы Messenger001).

Условные обозначения: «да» — поддерживается, «нет» — не реализовано платформой M001, «стаб» — класс/функция импортируется, но не имеет эффекта (для совместимости импортов при миграции).

## Bot

```python
from messenger001_aiogram import Bot, DefaultBotProperties, ParseMode

bot = Bot(
    token="...",
    api_base="https://messenger001.ru/api/v1",   # default
    request_timeout=30.0,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
```

Bot реализует async-context-manager: `async with Bot(token=...) as bot: ...` корректно закрывает HTTP-сессию.

### Методы Bot

| Метод | Поддержка | Сигнатура (упрощённая) |
|-------|-----------|------------------------|
| `get_me()` | да | `() -> User` |
| `send_message(chat_id, text, reply_markup=None, reply_to_message_id=None, parse_mode=None)` | да | `-> Message` |
| `send_photo(chat_id, photo, caption=None, reply_markup=None)` | да | `-> Message`. `photo` — путь, `Path`, `bytes`, или `FSInputFile`. |
| `send_document(chat_id, document, caption=None, reply_markup=None)` | да | `-> Message` |
| `send_video(chat_id, video, caption=None, reply_markup=None)` | да | `-> Message` |
| `send_audio(chat_id, audio, caption=None, reply_markup=None)` | да | `-> Message` |
| `edit_message_text(text, chat_id, message_id, reply_markup=None)` | да | `-> Message`. `chat_id` и `message_id` обязательны. |
| `edit_message_reply_markup(chat_id, message_id, reply_markup=None)` | да | `-> Message`. Передайте `reply_markup=None`, чтобы убрать кнопки. |
| `answer_callback_query(callback_query_id, text=None, show_alert=False)` | да | `-> bool` |
| `send_chat_action(chat_id, action="typing")` | частично | `-> bool`. На уровне M001 поддерживается только `typing`. |
| `set_my_commands(commands)` | да | `commands: list[BotCommand \| dict] -> list[BotCommand]` |
| `get_my_commands()` | да | `-> list[BotCommand]` |
| `delete_my_commands()` | да | `-> bool` |
| `forward_message`, `copy_message` | нет | Платформа не поддерживает форвардинг. |
| `send_voice`, `send_animation`, `send_video_note`, `send_sticker`, `send_poll`, `send_dice`, `send_contact`, `send_location` | нет | На стороне M001 этих сущностей нет. |
| `start_polling(...)` (через Dispatcher) | нет | `RuntimeError`. M001 — webhook-only. |

Все Bot-методы принимают `**kwargs`, неизвестные параметры тихо игнорируются — это упрощает миграцию кода, который передаёт TG-специфичные опции (`disable_web_page_preview`, `protect_content` и т. п.).

### Возвращаемое `Message`

API M001 в ответе на `sendMessage` возвращает только `message_id`. SDK строит «стаб» Message с заполненными `message_id`, `chat.id`, `date`. Поля `text`, `from_user` остаются пустыми — их можно получить только в incoming-апдейтах из webhook.

## Dispatcher / Router

```python
from messenger001_aiogram import Dispatcher, Router

dp = Dispatcher()                      # MemoryStorage по умолчанию
router = Router(name="my_router")
dp.include_router(router)
```

### Регистрация хендлеров

| aiogram | messenger001-aiogram | Поддержка |
|---------|----------------------|-----------|
| `@dp.message(...)` | `@dp.message(...)` | да |
| `@dp.callback_query(...)` | `@dp.callback_query(...)` | да |
| `@dp.message.register(handler, ...)` | `dp.message.register(handler, ...)` | да |
| `dp.include_router(r)` | `dp.include_router(r)` | да |
| `@dp.edited_message`, `@dp.channel_post`, `@dp.inline_query`, `@dp.chosen_inline_result`, `@dp.poll` и т. д. | — | нет (этих апдейтов нет в M001) |

### Запуск

```python
from messenger001_aiogram import start_webhook, build_webhook_app

# Простейший вариант — блокирующий runner.
await start_webhook(
    dp, bot,
    host="0.0.0.0",
    port=8080,
    path="/webhook",
    secret=None,           # auto-derive из bot.token
    verify_signature=True, # default
)

# Вариант для интеграции в свой aiohttp-app.
app = build_webhook_app(dp, bot, path="/webhook", secret=None)
# дальше — стандартный aiohttp.web.AppRunner.
```

`start_polling(...)` сознательно поднимает `RuntimeError`, чтобы случай «забыл переключиться на webhook» падал явно.

## Filters

### Command / CommandStart

```python
from messenger001_aiogram.filters import Command, CommandStart

@dp.message(Command("help"))
async def h(msg): ...

@dp.message(Command("ban", "kick", prefix="/", ignore_case=True))
async def h(msg, command): ...   # command: CommandObject(command, args)

@dp.message(CommandStart())                  # /start без аргументов или с любыми
@dp.message(CommandStart(deep_link=True))    # только когда есть payload (/start ABC123)
```

`CommandObject` имеет поля `.command: str`, `.args: Optional[str]` — те же, что в aiogram (поле `.regexp_match` не реализовано).

### StateFilter

```python
from messenger001_aiogram.filters import StateFilter
from messenger001_aiogram.fsm import State, StatesGroup

class Onboarding(StatesGroup):
    waiting_email = State()

@dp.message(StateFilter(Onboarding.waiting_email))
async def step1(msg, state): ...

@dp.message(StateFilter(None))    # только когда состояние не установлено
@dp.message(StateFilter("*"))     # любое непустое состояние
```

Также допустимо `@dp.message(Onboarding.waiting_email)` — экземпляр `State` сам распознаётся как фильтр.

### F-magic

| Шаблон | Поддержка |
|--------|-----------|
| `F.data == "x"`, `F.text == "x"` | да |
| `F.data != "x"` | да |
| `F.text.startswith("/")` | да |
| `F.text.regexp(r"^\d+$")` | да |
| `F.data.in_({"a", "b"})` | да |
| `F.text.lower() == "ok"`, `F.text.casefold().in_({"a","b"})` | да (цепочка `.attr().method()`) |
| `F.text` (truthiness как фильтр) | да |
| `~F.text` (отрицание truthiness) | да |
| `(F.data == "a") & (F.text.startswith("/"))` | да (`__and__`, `__or__`) |
| `F.from_user.id == 123` | да (через chained attr) |

Не поддерживаются менее распространённые TG-only поля magic-фильтров (например, `F.poll`, `F.sticker`).

## Types

| Тип | Поддержка | Заметки |
|-----|-----------|---------|
| `Message` | да | Поля: `message_id`, `date`, `chat`, `from_user`, `text`, `caption`, `reply_to_message`. Метод `.bot` возвращает связанный `Bot`. |
| `CallbackQuery` | да | Поля: `id`, `from_user`, `data`, `message`. M001 шлёт `chat_id`+`message_id` плоско, SDK собирает stub-Message. |
| `User` | да | `id`, `is_bot`, `first_name`, `last_name`, `username`, `language_code`, property `full_name`. |
| `Chat` | да | `id`, `type` (`"private"` по умолчанию), `title`, `username`. M001 = только private-чаты бота. |
| `Update` | да | `update_id`, `message`, `callback_query`. Прочих апдейт-типов нет. |
| `BotCommand` | да | `command`, `description`. `to_dict()`, `from_dict(...)`. |
| `FSInputFile` | да | `path: str \| Path`, `filename: Optional[str]`. Используется в `send_photo` и т. д. |
| `TelegramObject` | стаб (= `Any`) | Только для type-hints в middleware/handler-сигнатурах. |
| `Sticker`, `Poll`, `Voice`, `Animation`, `VideoNote`, `Contact`, `Location`, `Venue`, `Dice` | нет | Платформа их не отправляет. |

### Хелперы Message

```python
await msg.answer(text, reply_markup=...)
await msg.reply(text, reply_markup=...)         # с reply_to_message_id
await msg.edit_text(text, reply_markup=...)
await msg.edit_reply_markup(reply_markup=...)
await msg.answer_photo(photo, caption=...)
await msg.answer_document(document, caption=...)
```

### Хелперы CallbackQuery

```python
await call.answer(text=None, show_alert=False)
await call.message.edit_text(text, reply_markup=...)   # call.message — stub Message
```

## Keyboards

```python
from messenger001_aiogram import (
    InlineKeyboardBuilder,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

kb = InlineKeyboardBuilder()
kb.button(text="A", callback_data="a")
kb.button(text="B", url="https://example.com")
kb.adjust(2)                        # разложить по 2 в ряд
markup = kb.as_markup()             # InlineKeyboardMarkup
```

`InlineKeyboardButton` поддерживает только `text`, `callback_data`, `url`. TG-специфичные поля (`web_app`, `login_url`, `switch_inline_query`, `pay`, `callback_game`, `copy_text`) не реализованы.

`ReplyKeyboardMarkup`, `KeyboardButton`, `ReplyKeyboardRemove` импортируются как стабы (миграция не сломается), но клиент M001 их **не рендерит**: `to_m001()` возвращает `None`, и SDK не передаёт поле в API.

## FSM

```python
from messenger001_aiogram.fsm import (
    State, StatesGroup,
    FSMContext,
    MemoryStorage, RedisStorage,
)

class Survey(StatesGroup):
    name = State()
    age = State()

dp = Dispatcher(storage=MemoryStorage())          # default
dp = Dispatcher(storage=RedisStorage(redis_client, key_prefix="bot:fsm", ttl=86400))

@dp.message(Command("survey"))
async def begin(msg, state: FSMContext):
    await state.set_state(Survey.name)
    await msg.answer("Как зовут?")

@dp.message(StateFilter(Survey.name))
async def step1(msg, state: FSMContext):
    await state.update_data(name=msg.text)
    await state.set_state(Survey.age)
    await msg.answer("Сколько лет?")

@dp.message(StateFilter(Survey.age))
async def step2(msg, state: FSMContext):
    data = await state.get_data()
    data["age"] = msg.text
    await state.clear()
    await msg.answer(f"Готово: {data}")
```

Методы `FSMContext`: `set_state`, `get_state`, `set_data`, `update_data(**kw)`, `get_data`, `clear`. Сигнатуры идентичны aiogram.

`RedisStorage` принимает любой `redis.asyncio.Redis`-совместимый клиент.

## Middleware

```python
from messenger001_aiogram import BaseMiddleware

class LogMW(BaseMiddleware):
    async def __call__(self, handler, event, data):
        print("incoming:", type(event).__name__)
        return await handler(event, data)

dp.message.middleware(LogMW())          # inner — после фильтров
dp.message.outer_middleware(LogMW())    # outer — до фильтров
dp.update.middleware(LogMW())           # outer на уровне Dispatcher (любой апдейт)
```

`data` — словарь с ключами `bot`, `state` (`FSMContext`), `dispatcher`. Хендлеры получают значения по имени параметра (`async def h(msg, state, bot): ...`).

## Enums

```python
from messenger001_aiogram import ParseMode, ChatAction

ParseMode.HTML, ParseMode.MARKDOWN, ParseMode.MARKDOWN_V2
ChatAction.TYPING, ChatAction.UPLOAD_PHOTO, ...   # значения совпадают с aiogram
```

Идентичность значений с aiogram — для совместимости импортов; на стороне M001 honoured только подмножество (`parse_mode` — best-effort, из `ChatAction` — `typing`).

## Exceptions

```python
from messenger001_aiogram.exceptions import APIError, M001Error, WebhookError
```

`APIError(status, payload)` бросается при HTTP-ошибке от Bot API (status >= 400 либо `"ok": false`). Используйте `try/except APIError` в местах, где важно отличать ошибку платформы от ошибки логики.

## Webhook utilities

```python
from messenger001_aiogram.webhook import (
    start_webhook,
    build_webhook_app,
    webhook_secret_from_token,
    verify_webhook_signature,
)

# Ручная верификация подписи (например, в кастомном aiohttp-handler):
secret = webhook_secret_from_token(bot.token)
ok = verify_webhook_signature(secret, raw_body_bytes, request.headers.get("X-Signature"))
```

Подробности протокола — в [webhook-spec.md](webhook-spec.md).
