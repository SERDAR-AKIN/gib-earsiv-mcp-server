import uuid
from typing import Any, Dict

class MockGibClient:
    def __init__(self, *args, **kwargs):
        pass

    async def login(self) -> str:
        return f"mock_token_{uuid.uuid4().hex}"

    async def dispatch(self, cmd: str, token: str, jp_dict: Dict[str, Any] = None, page_name: str = "RG_KULLANICI") -> dict:
        if cmd == "EARSIV_PORTAL_KULLANICI_BILGILERI_GETIR":
            return {"data": {"vknTckn": "11111111111", "unvan": "MOCK USER INC", "ad": "MOCK", "soyad": "USER"}}
        elif cmd == "EARSIV_PORTAL_TASLAKLARI_GETIR":
            return {"data": [
                {"belgeNumarasi": "GIB2025000000001", "belgeTarihi": "07-04-2025", "odenecekTutar": 1500.50, "onayDurumu": "Onaylandı", "ettn": "mock-ettn-001", "aliciUnvanAdSoyad": "ALICI A.Ş."},
                {"belgeNumarasi": "GIB2025000000002", "belgeTarihi": "08-04-2025", "odenecekTutar": 2500.00, "onayDurumu": "Onaylanmadı", "ettn": "mock-ettn-002", "aliciUnvanAdSoyad": "IMZA BEKLEYEN LTD"},
                {"belgeNumarasi": "GIB2025000000003", "belgeTarihi": "09-04-2025", "odenecekTutar": 800.00, "onayDurumu": "Onaylanmadı", "ettn": "mock-ettn-003", "aliciUnvanAdSoyad": "BEKLEYEN FİRMA"},
            ]}
        elif cmd == "getUserMenu":
            return {"data": [{"isim": "Fatura Oluştur", "link": "#"}]}
        elif cmd == "EARSIV_PORTAL_FATURA_OLUSTUR":
            return {"data": "Fatura başarıyla oluşturuldu.", "mock_uuid": str(uuid.uuid4())}
        elif cmd == "EARSIV_PORTAL_FATURA_GOSTER":
            return {"data": "<html><body><h1>MOCK FATURA HTML</h1></body></html>"}
        elif cmd == "EARSIV_PORTAL_TELEFONNO_SORGULA":
            return {"data": {"telefon": "555****99"}}
        elif cmd == "EARSIV_PORTAL_SMSSIFRE_GONDER":
            return {"data": {"oid": "mock_sms_oid_12345"}}
        elif cmd == "0lhozfib5410mp":
            return {"data": "Fatura başarıyla imzalandı."}
        elif cmd == "EARSIV_PORTAL_FATURA_SIL":
            return {"data": "Fatura başarıyla silindi/iptal edildi."}
        elif cmd == "SICIL_VEYA_MERNISTEN_BILGILERI_GETIR":
            return {"data": {"vknTckn": jp_dict.get("vknTcknn", "1234567890"), "unvan": "SORGULANAN FIRMA LTD ŞTİ", "vergiDairesi": "MOCK VD"}}
        elif cmd == "EARSIV_PORTAL_ADIMA_KESILEN_BELGELERI_GETIR":
            return {"data": [{"belgeNumarasi": "GIB2025000000002", "saticiVknTckn": "99999999999", "saticiUnvanAdSoyad": "MOCK SATICI LTD", "belgeTarihi": "30-10-2025", "belgeTuru": "FATURA", "onayDurumu": "Onaylandı", "ettn": "mock-ettn-uuid", "toplamTutar": 250.0}]}
            
        return {"status": "success", "mocked": True, "cmd": cmd, "jp": jp_dict}

    async def download(self, token: str, ettn: str, belge_tip: str = "FATURA", onay_durumu: str = "Onaylandı") -> bytes:
        return b"MOCK_ZIP_CONTENT_BYTES"
