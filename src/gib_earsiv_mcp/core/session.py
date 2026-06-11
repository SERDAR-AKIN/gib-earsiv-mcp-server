import httpx
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from fastmcp import FastMCP
from .config import settings, GibEnvironment
from .client import GibClient
from .mock_client import MockGibClient

@dataclass
class AppState:
    http_client: httpx.AsyncClient | None = None
    gib_client: GibClient | MockGibClient | None = None
    token_store: dict[str, str] = field(default_factory=dict)

    async def get_valid_token(self, client_id: str) -> str:
        token = self.token_store.get(client_id)
        if not token:
            token = await self.gib_client.login()
            self.token_store[client_id] = token
        return token

    def clear_token(self, client_id: str):
        if client_id in self.token_store:
            del self.token_store[client_id]

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppState]:
    state = AppState()
    
    if settings.GIB_ENV == GibEnvironment.MOCK:
        state.gib_client = MockGibClient()
        yield state
    else:
        client = httpx.AsyncClient(timeout=30.0)
        state.http_client = client
        state.gib_client = GibClient(http_client=client)
        try:
            yield state
        finally:
            await client.aclose()
