import asyncio
import pytest
from fastmcp import Client
from gib_earsiv_mcp.server import mcp

@pytest.mark.asyncio
async def test_fatura_olustur():
    async with Client(mcp) as client:
        payload = {
            "faturaTarihi": "10/06/2026",
            "saat": "14:30:00",
            "vknTckn": "11111111111",
            "matrah": 100.0,
            "malhizmetToplamTutari": 100.0,
            "hesaplananKdv": 20.0,
            "vergilerDahilToplamTutar": 120.0,
            "odenecekTutar": 120.0,
            "malHizmetListe": [
                {
                    "malHizmet": "Danışmanlık",
                    "miktar": 1,
                    "birimFiyat": 100.0,
                    "fiyat": 100.0,
                    "kdvOrani": 20,
                    "kdvTutari": 20.0,
                    "malHizmetTutari": 120.0
                }
            ]
        }
        result = await client.call_tool("gib_earsiv_fatura_olustur", {"params": payload})
        assert result.is_error is False
        assert "başarıyla" in str(result.data)

@pytest.mark.asyncio
async def test_fatura_goster():
    async with Client(mcp) as client:
        result = await client.call_tool("gib_earsiv_fatura_goster", {"params": {"fatura_uuid": "mock-uuid"}})
        assert result.is_error is False
        assert "MOCK FATURA HTML" in str(result.data)

@pytest.mark.asyncio
async def test_sms_akis():
    async with Client(mcp) as client:
        r1 = await client.call_tool("gib_earsiv_sms_sorgula", {"params": {"vkn_tckn": "11111111111"}})
        assert "telefon" in str(r1.data)
        
        r2 = await client.call_tool("gib_earsiv_sms_gonder", {"params": {"vkn_tckn": "11111111111", "telefon": "5551234567"}})
        assert "oid" in str(r2.data)
        
        r3 = await client.call_tool("gib_earsiv_sms_onayla", {"params": {"oid": "mockoid", "sms_kodu": "123456", "fatura_uuid": "mockuuid"}})
        assert "imzalandı" in str(r3.data)
