import asyncio
import pytest
from fastmcp import Client
from gib_earsiv_mcp.server import mcp

@pytest.mark.asyncio
async def test_fatura_sil():
    async with Client(mcp) as client:
        result = await client.call_tool("gib_earsiv_fatura_sil", {"params": {"fatura_uuid": "test-uuid"}})
        assert result.is_error is False
        assert "başarıyla" in str(result.data).lower()

@pytest.mark.asyncio
async def test_sicil_sorgula():
    async with Client(mcp) as client:
        result = await client.call_tool("gib_earsiv_sicil_sorgula", {"params": {"vkn_tckn": "1234567890"}})
        assert result.is_error is False
        assert "SORGULANAN" in str(result.data)

@pytest.mark.asyncio
async def test_adima_kesilen():
    async with Client(mcp) as client:
        result = await client.call_tool("gib_earsiv_adima_kesilen_belgeler", {})
        assert result.is_error is False
        assert "GIB2025000000002" in str(result.data)
