# Getting Started — первый бот на messenger001-aiogram

Этот гайд проведёт от пустой папки до бота, отвечающего в Messenger001 на команду `/start`. Ожидаемое время — 10–15 минут.

## Что нужно

1. Python 3.10+ (`python3 --version`).
2. Установленное приложение **Messenger001** ([messenger001.ru](https://messenger001.ru)) и зарегистрированный аккаунт в нём.
3. Сервер с публичным HTTPS-адресом (VPS, Railway, Render, Fly.io, ngrok для локальной отладки). Нужен потому, что Messenger001 — webhook-only: платформа сама шлёт `POST` на ваш URL, polling-режима нет.

## 1. Создание бота через @botfather

@botfather — это служебный бот **внутри Messenger001** (не телеграмный). Он живёт прямо в приложении.

1. Откройте Messenger001 → найдите чат с **@botfather**.
2. Отправьте `/newbot` и следуйте подсказкам: имя бота → username (заканчивается на `bot`).
3. Сохраните токен из ответа. Это секрет — не публикуйте его в репозитории.

```bash
export M001_TOKEN="xxxxx:yyyyyyyyyyyyyy"
```

## 2. Установка SDK

```bash
pip install messenger001-aiogram
```

Зависимости: `aiohttp>=3.9`, `pydantic>=2.5`. Поддержка Python 3.10–3.12.

## 3. Минимальный бот

Создайте файл `bot.py`:

```python
import asyncio
import os

from messenger001_aiogram import (
    Bot,
    Dispatcher,
    F,
    InlineKeyboardBuilder,
    Message,
    CallbackQuery,
    start_webhook,
)
from messenger001_aiogram.filters import Command, CommandStart

dp = Dispatcher()


@dp.message(CommandStart())
async def on_start(msg: Message) -> None:
    kb = InlineKeyboardBuilder()
    kb.button(text="Ping", callback_data="ping")
    await msg.answer("Привет!", reply_markup=kb.as_markup())


@dp.message(Command("help"))
async def on_help(msg: Message) -> None:
    await msg.answer("Команды: /start, /help.")


@dp.message()
async def on_any(msg: Message) -> None:
    if msg.text:
        await msg.answer(f"Эхо: {msg.text}")


@dp.callback_query(F.data == "ping")
async def on_ping(call: CallbackQuery) -> None:
    await call.answer("pong")
    if call.message:
        await call.message.edit_text("pong")


async def main() -> None:
    async with Bot(token=os.environ["M001_TOKEN"]) as bot:
        await start_webhook(dp, bot, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    asyncio.run(main())
```

Полный референсный пример с inline-меню и `set_my_commands` — `examples/echo_bot.py`.

## 4. Запуск локально (через ngrok)

```bash
python bot.py
# В соседнем терминале:
ngrok http 8080
```

ngrok вернёт публичный HTTPS-URL вида `https://abc123.ngrok-free.app`. Webhook-эндпоинт бота — `https://abc123.ngrok-free.app/webhook`.

## 5. Регистрация webhook у @botfather

Снова откройте чат с **@botfather** в Messenger001:

1. `/mybots` → выберите вашего бота.
2. В появившемся меню: «Webhook URL» → пришлите ваш URL целиком, с путём `/webhook`.

Бот сразу начнёт получать апдейты. Проверьте: напишите ему `/start` в Messenger001 — должен прийти ответ с inline-кнопкой.

## 6. Деплой на сервер

Скрипт должен слушать `POST /webhook` на публичном HTTPS. Любой PaaS, поддерживающий long-running Python-процесс, подойдёт.

- **Railway / Render / Fly.io**: задеплойте репозиторий, в команде запуска укажите `python bot.py`, в env-переменные положите `M001_TOKEN`. На таких платформах HTTPS уже включён — отдельной TLS-настройки не нужно.
- **Свой VPS**: запускайте через `systemd` / `supervisor` / `docker`, чтобы процесс автоматически рестартился; HTTPS поднимите через nginx + Let's Encrypt или Caddy.

После деплоя обновите webhook-URL в @botfather на адрес продакшена.

## Что дальше

- [migration-from-aiogram.md](migration-from-aiogram.md) — если у вас уже есть TG-бот, и вы хотите перенести его в Messenger001.
- [api-reference.md](api-reference.md) — таблица всех поддерживаемых методов и фильтров.
- [webhook-spec.md](webhook-spec.md) — техдока по протоколу webhook (для тех, кто пишет клиент без SDK).

## Частые проблемы

- **Бот не отвечает.** Убедитесь, что webhook-URL зарегистрирован у @botfather и доступен снаружи (`curl -X POST https://your-host/webhook -d '{}'` должен вернуть `{"ok": true}`).
- **`401 invalid signature`.** Проверка HMAC-подписи включена по умолчанию. Если развёрнут локальный/тестовый бэкенд, который не подписывает запросы, передайте `verify_signature=False` в `start_webhook(...)` — но в продакшене этого делать **нельзя**.
- **`KeyError: 'M001_TOKEN'`.** Не выставлена env-переменная. Экспортируйте её или подгрузите из `.env` (например, через `python-dotenv`).
