import pytest
from fastmcp import Client
from gib_earsiv_mcp.server import mcp

@pytest.mark.asyncio
async def test_imza_bekleyenler_filtreleme():
    async with Client(mcp) as client:
        result = await client.call_tool("gib_earsiv_imza_bekleyenler", {})
        assert result.is_error is False
        content = str(result.data)
        assert "IMZA BEKLEYEN LTD" in content
        assert "BEKLEYEN FİRMA" in content
        assert "onayDurumu" in content
