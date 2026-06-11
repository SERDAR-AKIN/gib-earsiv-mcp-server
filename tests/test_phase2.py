import asyncio
import pytest
from fastmcp import Client
from gib_earsiv_mcp.server import mcp

@pytest.mark.asyncio
async def test_kullanici_bilgileri():
    async with Client(mcp) as client:
        result = await client.call_tool("gib_earsiv_kullanici_bilgileri_getir", {})
        assert result.is_error is False
        # The mock returns this
        assert "MOCK USER INC" in str(result.data)

@pytest.mark.asyncio
async def test_menu_getir():
    async with Client(mcp) as client:
        result = await client.call_tool("gib_earsiv_menu_getir", {})
        assert result.is_error is False
        assert "Fatura Oluştur" in str(result.data)

@pytest.mark.asyncio
async def test_taslaklari_getir():
    async with Client(mcp) as client:
        # Pydantic will use defaults if not provided
        result = await client.call_tool("gib_earsiv_taslaklari_getir", {})
        assert result.is_error is False
        assert "GIB2025000000001" in str(result.data)
