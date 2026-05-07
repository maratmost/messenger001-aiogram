# Migration Guide — с aiogram на messenger001-aiogram

Гайд для разработчиков, у которых уже есть рабочий Telegram-бот на aiogram 3.x и которые хотят перенести его в Messenger001.

Главный посыл: в большинстве случаев меняется только блок импортов и способ запуска (webhook вместо polling). Handlers, фильтры, FSM, middleware, inline-клавиатуры — всё это работает без изменений.

## TL;DR

```diff
- from aiogram import Bot, Dispatcher, F
- from aiogram.filters import Command, CommandStart
- from aiogram.types import Message, CallbackQuery
- from aiogram.utils.keyboard import InlineKeyboardBuilder
- from aiogram.fsm.context import FSMContext
- from aiogram.fsm.state import State, StatesGroup
- from aiogram.fsm.storage.memory import MemoryStorage

+ from messenger001_aiogram import Bot, Dispatcher, F, InlineKeyboardBuilder
+ from messenger001_aiogram.filters import Command, CommandStart
+ from messenger001_aiogram.types import Message, CallbackQuery
+ from messenger001_aiogram.fsm import FSMContext, State, StatesGroup, MemoryStorage
```

```diff
- await dp.start_polling(bot)
+ from messenger001_aiogram import start_webhook
+ await start_webhook(dp, bot, port=8080)
```

Всё остальное — handlers, фильтры, `await msg.answer(...)`, `InlineKeyboardBuilder`, FSM-states — переносится без изменений.

## Что меняется

### 1. Импорты

| aiogram | messenger001-aiogram |
|---------|----------------------|
| `from aiogram import Bot, Dispatcher, F, Router` | `from messenger001_aiogram import Bot, Dispatcher, F, Router` |
| `from aiogram.filters import Command, CommandStart, StateFilter` | `from messenger001_aiogram.filters import Command, CommandStart, StateFilter` |
| `from aiogram.types import Message, CallbackQuery, BotCommand, FSInputFile` | `from messenger001_aiogram.types import Message, CallbackQuery, BotCommand, FSInputFile` |
| `from aiogram.utils.keyboard import InlineKeyboardBuilder` | `from messenger001_aiogram import InlineKeyboardBuilder` |
| `from aiogram.fsm.context import FSMContext` | `from messenger001_aiogram.fsm import FSMContext` |
| `from aiogram.fsm.state import State, StatesGroup` | `from messenger001_aiogram.fsm import State, StatesGroup` |
| `from aiogram.fsm.storage.memory import MemoryStorage` | `from messenger001_aiogram.fsm import MemoryStorage` |
| `from aiogram.fsm.storage.redis import RedisStorage` | `from messenger001_aiogram.fsm import RedisStorage` |
| `from aiogram.client.default import DefaultBotProperties` | `from messenger001_aiogram import DefaultBotProperties` |
| `from aiogram.enums import ParseMode, ChatAction` | `from messenger001_aiogram import ParseMode, ChatAction` |
| `from aiogram import BaseMiddleware` | `from messenger001_aiogram import BaseMiddleware` |

Совет: если в проекте много мест — сделайте sed-замену по корню `aiogram` → `messenger001_aiogram` и потом подправьте подмодули вручную (их немного).

### 2. Транспорт: polling → webhook

Messenger001 — webhook-only. `dp.start_polling(bot)` не работает (вызовет `RuntimeError`). Используйте:

```python
from messenger001_aiogram import start_webhook

async def main():
    async with Bot(token=TOKEN) as bot:
        await start_webhook(dp, bot, host="0.0.0.0", port=8080, path="/webhook")
```

Это поднимет aiohttp-сервер и заблокирует функцию до отмены. Если вам нужен свой aiohttp-app (например, для health-check или нескольких роутов) — используйте `build_webhook_app(...)` и поднимите runner вручную.

После запуска зарегистрируйте webhook-URL у `@botfather` в Messenger001 (`/mybots` → ваш бот → «Webhook URL»). См. [getting-started.md](getting-started.md).

### 3. Регистрация бота

В Telegram это `@BotFather` в самом TG. В Messenger001 — `@botfather` **внутри приложения Messenger001**. Команды те же: `/newbot`, `/mybots`, `/setdescription` и т. д.

## Что НЕ меняется

- **Handlers**: `@dp.message(...)`, `@dp.callback_query(...)`, `Router.include_router(...)`.
- **Фильтры**: `Command("foo")`, `CommandStart(deep_link=True)`, `StateFilter(...)`, F-magic (`F.data == "x"`, `F.text.startswith("/")`).
- **Inline-клавиатуры**: `InlineKeyboardBuilder().button(...).adjust(...).as_markup()`, `InlineKeyboardMarkup`, `InlineKeyboardButton(text=..., callback_data=..., url=...)`.
- **FSM**: `State`, `StatesGroup`, `FSMContext`, `MemoryStorage`, `RedisStorage`. Сигнатуры `state.set_state(...)`, `state.update_data(**kw)`, `state.get_data()`, `state.clear()` — идентичны aiogram.
- **Bot-методы**: `bot.send_message`, `send_photo`, `send_document`, `send_video`, `send_audio`, `edit_message_text`, `edit_message_reply_markup`, `answer_callback_query`, `send_chat_action`, `get_me`, `set_my_commands`, `get_my_commands`, `delete_my_commands`.
- **Message-методы**: `msg.answer(...)`, `msg.reply(...)`, `msg.edit_text(...)`, `msg.edit_reply_markup(...)`, `msg.answer_photo(...)`, `msg.answer_document(...)`.
- **CallbackQuery-методы**: `call.answer(...)`, `call.message.edit_text(...)`.
- **Middleware**: подкласс `BaseMiddleware` с `async __call__(handler, event, data)`. Регистрация: `router.message.middleware(mw)`, `dp.update.middleware(mw)`.
- **DefaultBotProperties**: `Bot(token=..., default=DefaultBotProperties(parse_mode=ParseMode.HTML))`.

## Что НЕ поддерживается в Messenger001

| Возможность | Статус | Что делать |
|-------------|--------|------------|
| `dp.start_polling(...)` | Не поддерживается (M001 webhook-only) | Используйте `start_webhook(...)` |
| Reply-клавиатура (`ReplyKeyboardMarkup`, `KeyboardButton`) | Платформа не рендерит | Классы есть как стабы (импорты не сломаются), но клиент их не покажет. Используйте inline-клавиатуру. |
| Forwarding сообщений | Не поддерживается | Удалите вызовы `bot.forward_message`, `msg.forward(...)` или замените логику. |
| Polls / Stickers | Не поддерживается | На стороне M001 этих сущностей нет. Замените опросы inline-клавиатурой, стикеры — фото/видео. |
| Voice / Animation / VideoNote | Не поддерживается | Используйте `send_audio` / `send_video` / `send_document`. |
| Long-polling, `getUpdates` | Не поддерживается | Webhook only. |
| Inline-mode (`@bot query`) | Не поддерживается | На стороне M001 inline-режима нет. |
| `parse_mode=HTML/Markdown` | Best-effort | Передаётся в API, но рендеринг зависит от клиента M001. Не закладывайтесь на полный паритет с TG. |

## Пример «было / стало»: handlers без изменений

**Было (aiogram):**

```python
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

dp = Dispatcher()

@dp.message(CommandStart())
async def start(msg: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="Ping", callback_data="ping")
    await msg.answer("Hi!", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "ping")
async def ping(call: CallbackQuery):
    await call.answer("pong")

async def main():
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)
```

**Стало (messenger001-aiogram):**

```python
from messenger001_aiogram import Bot, Dispatcher, F, InlineKeyboardBuilder, start_webhook
from messenger001_aiogram.filters import CommandStart
from messenger001_aiogram.types import Message, CallbackQuery

dp = Dispatcher()

@dp.message(CommandStart())
async def start(msg: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="Ping", callback_data="ping")
    await msg.answer("Hi!", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "ping")
async def ping(call: CallbackQuery):
    await call.answer("pong")

async def main():
    async with Bot(token=TOKEN) as bot:
        await start_webhook(dp, bot, port=8080)
```

Тело хендлеров — посимвольно одинаковое.

## Чек-лист миграции

1. Замените импорты по таблице выше.
2. Замените `dp.start_polling(bot)` на `start_webhook(dp, bot, port=...)`.
3. Уберите/замените код, использующий неподдерживаемые фичи (reply-клавиатуры, polls, forwarding).
4. Создайте бота в Messenger001 через `@botfather` → получите токен.
5. Задеплойте бота на публичный HTTPS-хост.
6. Зарегистрируйте webhook-URL у `@botfather`.
7. Проверьте: `/start`, основные команды, inline-кнопки.

Если что-то не работает — сначала смотрите [api-reference.md](api-reference.md): возможно, метод не поддерживается. Затем [webhook-spec.md](webhook-spec.md), если подозреваете проблему на уровне протокола.
