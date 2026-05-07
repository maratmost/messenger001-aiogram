# Webhook & Bot API Spec — Messenger001

Этот документ описывает протокол webhook и Bot API без привязки к Python/aiogram-shim. Используйте его, если пишете клиент на другом языке (Go, Node, Rust) или хотите интегрировать M001 в существующий стек.

База API: `https://messenger001.ru/api/v1`. Все запросы — HTTPS, JSON в теле (либо `multipart/form-data` при загрузке файлов).

## Общая модель

- Бот в M001 — это виртуальный пользователь с `is_bot=true`. Создаётся через служебного бота `@botfather` внутри приложения Messenger001.
- Транспорт **только webhook**: long-polling (`getUpdates`) не поддерживается.
- При наступлении события (новое сообщение пользователю-боту, нажатие inline-кнопки) сервер M001 шлёт `POST` на зарегистрированный URL бота.
- Ответы / отправка сообщений — через Bot API endpoint'ы вида `POST /bot/{token}/<method>`, где `{token}` — секретный токен бота.

## Регистрация webhook

Webhook-URL задаётся через `@botfather` в Messenger001 (`/mybots` → выбрать бота → «Webhook URL»). URL должен быть публичным HTTPS и принимать `POST` с JSON.

## Incoming webhook payload

Сервер M001 шлёт `POST <ваш-URL>` со следующими заголовками и телом.

### Заголовки

| Заголовок | Описание |
|-----------|----------|
| `Content-Type` | `application/json; charset=utf-8` |
| `X-Signature` | HMAC-SHA256 подпись тела (см. ниже). Также допустимы `X-M001-Signature`, `X-Hub-Signature-256` (форма `sha256=hex`). |

### Тело: Update

```json
{
  "update_id": 12345,
  "message": { ... },           // либо
  "callback_query": { ... }     // либо
}
```

Ровно одно из полей `message` / `callback_query` присутствует в каждом апдейте. Других типов апдейтов в M001 нет.

### Message

```json
{
  "message_id": 987,
  "date": 1715000000,
  "chat_id": 42,
  "chat": { "id": 42, "type": "private" },
  "from": {
    "id": 7,
    "is_bot": false,
    "first_name": "Marat",
    "last_name": "K",
    "username": "marat"
  },
  "text": "/start",
  "caption": null,
  "reply_to_message": { ... }   // optional, тот же формат Message
}
```

Заметки:

- `chat_id` приходит **плоско** (для совместимости с историческим форматом M001) и/или вложенным как `chat.id`. Парсер должен принимать оба варианта.
- `from` (вложенный объект) — в API ответа M001 называется именно `from`. Поля `name`/`first_name`, `surname`/`last_name`, `nick`/`username` — синонимы (M001 раньше использовал свои имена; сейчас приходят оба).
- `reply_to_message` — опционально, если сообщение является ответом на другое.

### CallbackQuery

```json
{
  "update_id": 12346,
  "callback_query": {
    "id": "cb_abcdef",
    "from": { "id": 7, "first_name": "Marat", "username": "marat" },
    "chat_id": 42,
    "message_id": 987,
    "data": "ping"
  }
}
```

Заметки:

- В отличие от TG, M001 шлёт `chat_id` и `message_id` **на верхнем уровне callback_query**, а не вложенным `message: { message_id, chat: {...} }`. Клиент должен либо собрать stub-Message вручную, либо учитывать оба формата.
- `data` — строка, та же, что вы клали в `callback_data` inline-кнопки.

## HMAC-подпись webhook

Сервер M001 подписывает каждый POST к webhook-URL, чтобы получатель мог отличить настоящий запрос платформы от подделки.

### Алгоритм

1. **Секрет**: `secret = sha256(plain_token)` в hex (lowercase). Это значение, которое бэкенд M001 хранит у себя, и оно же используется как HMAC-ключ.
2. **Подпись**: `signature = hmac_sha256(key=secret, message=raw_request_body).hexdigest()`
3. Подпись передаётся в заголовке `X-Signature`. Также допустимы:
   - `X-M001-Signature` — то же значение,
   - `X-Hub-Signature-256` — в формате `sha256=<hex>` (совместимость с GitHub-style клиентами).

### Псевдокод верификации

```python
import hashlib, hmac

def webhook_secret_from_token(plain_token: str) -> str:
    return hashlib.sha256(plain_token.encode()).hexdigest()

def verify(plain_token: str, body: bytes, header_value: str) -> bool:
    secret = webhook_secret_from_token(plain_token)
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    candidate = header_value.split("=", 1)[1] if "=" in header_value else header_value
    return hmac.compare_digest(expected, candidate)
```

Эталонная реализация: `src/messenger001_aiogram/webhook.py` → `webhook_secret_from_token` / `verify_webhook_signature`. Серверная сторона: `app/Services/WebhookService.php::send()` в репозитории бэкенда.

### Что делать при невалидной подписи

Возвращайте HTTP 401 и не обрабатывайте payload. SDK по умолчанию делает это (`web.Response(status=401, text="invalid signature")`).

### Ответ на webhook

- Статус `2xx` означает «принято». Платформа не повторяет доставку при `2xx`.
- Тело ответа M001 не парсит, но из соображений совместимости рекомендуем `200 {"ok": true}`.
- Если вернуть `5xx`, поведение re-delivery зависит от настроек `BotMessageListener` / `SendWebhookJob` на бэкенде (по умолчанию — retry 3 раза с backoff 5/15/45 секунд; после 10 подряд провалов webhook автоматически отключается).

## Bot API endpoints

База: `POST https://messenger001.ru/api/v1/bot/{token}/<method>`. Токен — секрет, не светите его в клиентском коде.

### sendMessage

```http
POST /bot/{token}/sendMessage
Content-Type: application/json

{
  "chat_id": 42,
  "text": "Hello",
  "reply_markup": { "inline_keyboard": [[{"text": "Ping", "callback_data": "ping"}]] },
  "reply_to_message_id": 987,
  "parse_mode": "HTML"
}
```

Ответ:

```json
{ "ok": true, "message_id": 1010 }
```

### editMessageText

```json
{
  "chat_id": 42,
  "message_id": 1010,
  "text": "updated",
  "reply_markup": { "inline_keyboard": [[ ... ]] }
}
```

### editMessageReplyMarkup

```json
{
  "chat_id": 42,
  "message_id": 1010,
  "reply_markup": null            // null — убрать кнопки
}
```

### sendPhoto / sendDocument / sendVideo / sendAudio

Только `multipart/form-data`. Поля:

- `chat_id` — integer.
- `photo` (для sendPhoto) или `file` (для sendDocument / sendVideo / sendAudio) — бинарный файл.
- `caption` — опционально, строка.
- `reply_markup` — опционально, JSON-строка с inline-клавиатурой.

Ответ — тот же `{ "ok": true, "message_id": ... }`.

### answerCallbackQuery

```json
{
  "callback_query_id": "cb_abcdef",
  "text": "pong",
  "show_alert": false
}
```

Ответ: `{ "ok": true }`.

### sendTyping

```json
{ "chat_id": 42 }
```

Это упрощённый аналог Telegram `sendChatAction` — только typing-индикатор.

### getMe

```http
GET /bot/{token}/getMe
```

Ответ:

```json
{
  "ok": true,
  "result": {
    "botId": 7,
    "name": "Echo Bot",
    "username": "echo_bot"
  }
}
```

### setMyCommands / getMyCommands / deleteMyCommands

```json
POST /bot/{token}/setMyCommands
{
  "commands": [
    { "command": "start", "description": "Начать работу" },
    { "command": "help", "description": "Помощь" }
  ]
}
```

```http
GET /bot/{token}/getMyCommands
```

Ответ:

```json
{
  "ok": true,
  "result": [
    { "command": "start", "description": "Начать работу" },
    { "command": "help", "description": "Помощь" }
  ]
}
```

```http
POST /bot/{token}/deleteMyCommands
```

## Формат `reply_markup`

Только inline-клавиатура. Структура:

```json
{
  "inline_keyboard": [
    [
      { "text": "Ping", "callback_data": "ping" },
      { "text": "Сайт", "url": "https://example.com" }
    ],
    [
      { "text": "Закрыть", "callback_data": "close" }
    ]
  ]
}
```

Поля кнопки:

| Поле | Тип | Заметка |
|------|-----|---------|
| `text` | string, обязательно | Видимый текст. |
| `callback_data` | string | До ~64 символов. При нажатии шлётся в `callback_query.data`. |
| `url` | string | URL-кнопка. Открывает ссылку в системном браузере. Не комбинируется с `callback_data`. |

`ReplyKeyboardMarkup` (обычная, не-inline клавиатура), `web_app`, `login_url`, `switch_inline_query`, `pay`, `copy_text` и подобные TG-расширения **не поддерживаются**: платформа их не рендерит.

## Формат ошибок

```json
HTTP/1.1 400 Bad Request
{
  "ok": false,
  "description": "chat_id is required"
}
```

или

```json
HTTP/1.1 401 Unauthorized
{
  "ok": false,
  "description": "invalid bot token"
}
```

Клиент должен трактовать `status >= 400` либо `"ok": false` как ошибку. SDK выбрасывает `APIError(status, payload)`.

## Rate limits

Бэкенд применяет лимиты по тарифу разработчика:

| Тариф | Запросов/мин |
|-------|--------------|
| free | 30 |
| pro | 120 |
| business | 600 |

При превышении возвращается `429 Too Many Requests`. Реализуйте экспоненциальный бэкофф на стороне клиента.

## Полная карта endpoint'ов

| Method | URL | Назначение |
|--------|-----|------------|
| `POST` | `/bot/{token}/sendMessage` | Отправить текстовое сообщение. |
| `POST` | `/bot/{token}/editMessageText` | Изменить текст ранее отправленного сообщения. |
| `POST` | `/bot/{token}/editMessageReplyMarkup` | Изменить только inline-клавиатуру. |
| `POST` | `/bot/{token}/sendPhoto` | Отправить изображение (multipart). |
| `POST` | `/bot/{token}/sendDocument` | Отправить файл (multipart). |
| `POST` | `/bot/{token}/sendVideo` | Отправить видео (multipart). |
| `POST` | `/bot/{token}/sendAudio` | Отправить аудио (multipart). |
| `POST` | `/bot/{token}/sendTyping` | Показать typing-индикатор. |
| `POST` | `/bot/{token}/answerCallbackQuery` | Ответить на нажатие inline-кнопки. |
| `GET` | `/bot/{token}/getMe` | Информация о боте. |
| `POST` | `/bot/{token}/setMyCommands` | Зарегистрировать список команд. |
| `GET` | `/bot/{token}/getMyCommands` | Получить список команд. |
| `POST` | `/bot/{token}/deleteMyCommands` | Сбросить список команд. |

## Минимальная реализация receiver'а без SDK (Python, aiohttp)

```python
import hashlib, hmac, json
from aiohttp import web

TOKEN = "..."           # ваш bot-token
SECRET = hashlib.sha256(TOKEN.encode()).hexdigest()

async def handle(request: web.Request) -> web.Response:
    body = await request.read()
    sig = request.headers.get("X-Signature", "")
    expected = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    candidate = sig.split("=", 1)[1] if "=" in sig else sig
    if not hmac.compare_digest(expected, candidate):
        return web.Response(status=401, text="invalid signature")

    payload = json.loads(body)
    print("Update:", payload)
    # ... обработка ...
    return web.json_response({"ok": True})

app = web.Application()
app.router.add_post("/webhook", handle)
web.run_app(app, host="0.0.0.0", port=8080)
```

Этот receiver полностью эквивалентен тому, что делает `messenger001_aiogram.webhook.start_webhook` в части верификации и приёма апдейтов; вы добавляете только свой роутинг хендлеров.
