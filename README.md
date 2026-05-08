# messenger001-aiogram

**aiogram-совместимый SDK для [Messenger001](https://messenger001.ru) Bot API.**
Перенеси свой Telegram-бот на aiogram в Messenger001 **заменой одного импорта** —
или запусти **один codebase в двух мессенджерах одновременно**.

> Beta. API стабилизируется. Используй для пилотов и экспериментов.

## Установка

```bash
# Только M001:
pip install messenger001-aiogram

# Dual-transport (TG + M001 в одной кодовой базе):
pip install messenger001-aiogram[telegram]
```

## Сценарий 1 — миграция TG-бота в Messenger001

```diff
- from aiogram import Bot, Dispatcher, F
- from aiogram.filters import Command, CommandStart
- from aiogram.types import Message, CallbackQuery
- from aiogram.utils.keyboard import InlineKeyboardBuilder
+ from messenger001_aiogram import Bot, Dispatcher, F, InlineKeyboardBuilder
+ from messenger001_aiogram.filters import Command, CommandStart
+ from messenger001_aiogram.types import Message, CallbackQuery
```

Handlers, фильтры, клавиатуры (inline + reply), FSM — без изменений.

## Сценарий 2 — один codebase для TG и M001

```python
# Импортируй из dual-submodule везде:
from messenger001_aiogram.dual import Bot, Dispatcher, F, Router
from messenger001_aiogram.dual.filters import Command, CommandStart
from messenger001_aiogram.dual.types import Message, CallbackQuery
from messenger001_aiogram.dual.keyboards import InlineKeyboardBuilder, ReplyKeyboardMarkup
from messenger001_aiogram.dual.fsm import State, StatesGroup, FSMContext, MemoryStorage

# Handlers пишутся ОДИН раз — работают в обоих транспортах:
@dp.message(Command("start"))
async def start(msg: Message):
    await msg.answer("Привет!")
```

Транспорт выбирается переменной окружения `TRANSPORT`:

| `TRANSPORT` | Что используется под капотом | Token env |
|---|---|---|
| `telegram` (default) | aiogram (long-polling или webhook) | `TELEGRAM_TOKEN` |
| `m001` | messenger001-aiogram (webhook) | `M001_TOKEN` |

**Один docker-image, два деплоя:** запусти две инстанции с разными `TRANSPORT` и токенами — handler-код общий.

## Пример

```python
import asyncio, os
from messenger001_aiogram import Bot, Dispatcher, F, InlineKeyboardBuilder, Message, start_webhook
from messenger001_aiogram.filters import CommandStart

dp = Dispatcher()

@dp.message(CommandStart())
async def start(msg: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="Ping", callback_data="ping")
    await msg.answer("Привет!", reply_markup=kb.as_markup())

async def main():
    async with Bot(token=os.environ["M001_TOKEN"]) as bot:
        await start_webhook(dp, bot, port=8080)

asyncio.run(main())
```

См. [examples/echo_bot.py](examples/echo_bot.py) для полного примера.

## Меню команд

Зарегистрируй команды бота — в чате с ботом появится кнопка меню слева от поля ввода, `/команды` в тексте станут кликабельными, а ввод `/` покажет автокомплит.

```python
from messenger001_aiogram import BotCommand

async with Bot(token=TOKEN) as bot:
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать работу"),
        BotCommand(command="help",  description="Помощь"),
    ])
```

## Что поддерживается (v0.1)

| aiogram | messenger001-aiogram |
|---------|----------------------|
| `Bot(token)` | ✅ |
| `bot.send_message / send_photo / send_document / send_video / send_audio` | ✅ |
| `bot.edit_message_text / edit_message_reply_markup` | ✅ |
| `bot.answer_callback_query / send_chat_action / get_me` | ✅ |
| `bot.set_my_commands / get_my_commands / delete_my_commands` | ✅ |
| `Dispatcher`, `Router`, `include_router` | ✅ |
| `@dp.message(...)`, `@dp.callback_query(...)` | ✅ |
| `Command`, `CommandStart(deep_link=True)` | ✅ |
| `F.data == "..."`, `F.text.startswith(...)` | ✅ (подмножество) |
| `InlineKeyboardBuilder`, `InlineKeyboardMarkup` | ✅ |
| `State`, `StatesGroup`, `FSMContext`, `MemoryStorage` | ✅ |
| Webhook receiver (aiohttp) + HMAC-verify | ✅ |
| Reply-клавиатура (`ReplyKeyboardMarkup`) | ✅ Telegram-style панель над input bar |
| `parse_mode="HTML"` (`<b>`, `<i>`, `<a href>`, `<code>`, и т.д.) | ✅ парсится на backend в `MessageEntity[]` (как Telegram MTProto) |
| `bot.start_polling(...)` | ❌ (M001 — webhook-only) |
| Forwarding, polls, stickers | ❌ (нет на платформе) |

## Подключение

1. **Создай бота.** Открой в Messenger001 чат с **@botfather** → `/newbot` → получи токен. Сохрани его в env-переменную `M001_TOKEN`.

2. **Напиши код бота.** Используй пример выше или скопируй [examples/echo_bot.py](examples/echo_bot.py).

3. **Запусти бота на сервере с публичным HTTPS** (VPS, Railway, Render, Fly.io). Скрипт должен слушать `POST /webhook` на публично доступном URL. Для production используй systemd / supervisor / docker, чтобы процесс автоматически рестартился.

   ```bash
   python your_bot.py
   ```

4. **Зарегистрируй webhook у @botfather.** В том же чате: `/mybots` → выбери бота → «Webhook URL» → укажи `https://your-host/webhook`.

5. **Готово.** Пиши боту в Messenger001 — он отвечает.

## Документация

См. также:

- [docs/getting-started.md](docs/getting-started.md) — пошаговый «hello world» от установки до первого ответа.
- [docs/migration-from-aiogram.md](docs/migration-from-aiogram.md) — гид по переезду существующего TG-бота.
- [docs/api-reference.md](docs/api-reference.md) — таблица соответствия aiogram API ↔ messenger001-aiogram API.
- [docs/webhook-spec.md](docs/webhook-spec.md) — техническое описание webhook protocol и Bot API endpoints.

## Лицензия

MIT © Marat Khusainov
