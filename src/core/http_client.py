from typing import Any

from httpx import AsyncClient

from .exceptions import SessionNotInitializedException


class HTTPClientManager:
    def __init__(self):
        self.client: AsyncClient | None = None

    def start(self, **client_kwargs: Any) -> None:
        """Initialize the client."""
        if self.client is None:
            self.client = AsyncClient(**client_kwargs)

    async def stop(self) -> None:
        if self.client:
            await self.client.aclose()
            self.client = None

    async def client(self) -> AsyncClient:
        if self.client is None:
            raise SessionNotInitializedException(session_name="HTTPX_Client")
        return self.client


http_client_manager = HTTPClientManager()
