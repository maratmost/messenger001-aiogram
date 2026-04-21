class M001Error(Exception):
    """Base exception for messenger001-aiogram."""


class APIError(M001Error):
    def __init__(self, status: int, payload: dict | str):
        self.status = status
        self.payload = payload
        super().__init__(f"M001 API error {status}: {payload}")


class WebhookError(M001Error):
    pass
