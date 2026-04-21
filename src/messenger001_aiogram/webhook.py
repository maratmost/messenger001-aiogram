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


def _verify_signature(secret: str, body: bytes, signature: Optional[str]) -> bool:
    if not signature:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    # Support both raw hex and `sha256=hex` formats.
    candidate = signature.split("=", 1)[1] if "=" in signature else signature
    return hmac.compare_digest(expected, candidate)


def build_webhook_app(
    dispatcher: Dispatcher,
    bot: Bot,
    path: str = "/webhook",
    secret: Optional[str] = None,
) -> web.Application:
    async def handle(request: web.Request) -> web.Response:
        body = await request.read()
        if secret:
            signature = request.headers.get("X-M001-Signature") or request.headers.get(
                "X-Hub-Signature-256"
            )
            if not _verify_signature(secret, body, signature):
                log.warning("Webhook signature verification failed")
                return web.Response(status=401, text="invalid signature")
        try:
            payload = await request.json()
        except Exception:
            return web.Response(status=400, text="invalid json")
        await dispatcher.feed_webhook_update(bot, payload)
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
) -> None:
    """Convenience runner: blocks until cancelled."""
    import asyncio

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
