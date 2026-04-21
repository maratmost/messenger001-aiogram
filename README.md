# messenger001-aiogram

**aiogram-совместимый SDK для [Messenger001](https://messenger001.ru) Bot API.**
Перенеси свой Telegram-бот на aiogram в Messenger001 **заменой одного импорта**.

> ⚠️ Alpha. API стабилизируется. Используй для пилотов и экспериментов.

## Установка

```bash
pip install messenger001-aiogram   # позже, после публикации на PyPI
# Сейчас:
pip install git+https://github.com/maratmost/messenger001-aiogram.git
```

## Миграция существующего TG-бота

```diff
- from aiogram import Bot, Dispatcher, F
- from aiogram.filters import Command, CommandStart
- from aiogram.types import Message, CallbackQuery
- from aiogram.utils.keyboard import InlineKeyboardBuilder
+ from messenger001_aiogram import Bot, Dispatcher, F, InlineKeyboardBuilder
+ from messenger001_aiogram.filters import Command, CommandStart
+ from messenger001_aiogram.types import Message, CallbackQuery
```

Handlers, фильтры, inline-клавиатуры, FSM — остаются без изменений.

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

## Что поддерживается (v0.1)

| aiogram | messenger001-aiogram |
|---------|----------------------|
| `Bot(token)` | ✅ |
| `bot.send_message / send_photo / send_document / send_video / send_audio` | ✅ |
| `bot.edit_message_text / edit_message_reply_markup` | ✅ |
| `bot.answer_callback_query / send_chat_action / get_me` | ✅ |
| `Dispatcher`, `Router`, `include_router` | ✅ |
| `@dp.message(...)`, `@dp.callback_query(...)` | ✅ |
| `Command`, `CommandStart(deep_link=True)` | ✅ |
| `F.data == "..."`, `F.text.startswith(...)` | ✅ (подмножество) |
| `InlineKeyboardBuilder`, `InlineKeyboardMarkup` | ✅ |
| `State`, `StatesGroup`, `FSMContext`, `MemoryStorage` | ✅ |
| Webhook receiver (aiohttp) + HMAC-verify | ✅ |
| `bot.start_polling(...)` | ❌ (M001 — webhook-only) |
| Reply-клавиатура | ❌ (нет на платформе) |
| Forwarding, polls, stickers | ❌ (нет на платформе) |

## Подключение

1. Зарегистрируй бота через **@botfather** в Messenger001 → получи токен.
2. Подними свой код на сервере с публичным HTTPS.
3. В настройках бота (через @botfather или dashboard) укажи webhook URL: `https://your-host/webhook`.
4. Запусти скрипт. Бот отвечает.

## Лицензия

MIT © Marat Mostafin
