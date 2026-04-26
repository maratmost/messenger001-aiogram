"""aiohttp webhook receiver + optional HMAC verification."""
from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any, Optional

from aiohttp import web

from .bot import Bot
from .dispatcher import Dispatcher

log = logging.getLogger(__name__)


def webhook_secret_from_token(token: str) -> str:
    """Derive the HMAC secret that M001 uses to sign webhooks.

    The backend stores only `sha256(plain_token)` and uses that value as
    the HMAC-SHA256 key when signing outgoing webhooks. Bots that want to
    verify signatures must derive the same value from their plain token.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_webhook_signature(secret: str, body: bytes, signature: Optional[str]) -> bool:
    """M001 signs payload with HMAC-SHA256 using bot token as secret (hex digest).

    Matches backend/app/Services/WebhookService.php::send().
    Accepts both raw hex and `sha256=hex` formats.
    """
    if not signature:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    candidate = signature.split("=", 1)[1] if "=" in signature else signature
    return hmac.compare_digest(expected, candidate)


# Backwards-compatible alias (was the only export prior to v0.2).
_verify_signature = verify_webhook_signature


def build_webhook_app(
    dispatcher: Dispatcher,
    bot: Bot,
    path: str = "/webhook",
    secret: Optional[str] = None,
) -> web.Application:
    async def handle(request: web.Request) -> web.Response:
        body = await request.read()
        if secret:
            # M001 uses `X-Signature`. Also accept common alternatives.
            signature = (
                request.headers.get("X-Signature")
                or request.headers.get("X-M001-Signature")
                or request.headers.get("X-Hub-Signature-256")
            )
            if not verify_webhook_signature(secret, body, signature):
                log.warning("Webhook signature verification failed")
                return web.Response(status=401, text="invalid signature")
        try:
            payload = await request.json()
        except Exception:
            return web.Response(status=400, text="invalid json")
        log.info("[WEBHOOK] payload=%s", payload)
        handled = await dispatcher.feed_webhook_update(bot, payload)
        log.info("[WEBHOOK] handled=%s", handled)
        return web.json_response({"ok": True})

    app = web.Application()
    app.router.add_post(path, handle)
    app["bot"] = bot
    app["dispatcher"] = dispatcher
    return app


async def start_webhook(
    dispatcher: Dispatcher,
    bot: Bot,
    host: str = "0.0.0.0",
    port: int = 8080,
    path: str = "/webhook",
    secret: Optional[str] = None,
    verify_signature: bool = True,
) -> None:
    """Convenience runner: blocks until cancelled.

    If `verify_signature=True` (default) and `secret` is None, the secret is
    auto-derived from the bot's plain token as M001 does server-side.
    """
    import asyncio

    if verify_signature and secret is None:
        secret = webhook_secret_from_token(bot.token)
    app = build_webhook_app(dispatcher, bot, path=path, secret=secret)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    log.info("Webhook listening on http://%s:%s%s", host, port, path)
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
        await bot.close()
