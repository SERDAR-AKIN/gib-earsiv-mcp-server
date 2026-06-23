import httpx
import json
import uuid
from typing import Any, Dict
from .config import settings, GibEnvironment
from .exceptions import AuthenticationError, GibApiError, SessionExpiredError

class GibClient:
    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client
        self.base_url = settings.base_url

    async def login(self) -> str:
        url = f"{self.base_url}/assos-login"
        
        if settings.GIB_ENV == GibEnvironment.PRODUCTION:
            if not settings.GIB_USERNAME or not settings.GIB_PASSWORD:
                raise AuthenticationError("GIB_USERNAME and GIB_PASSWORD required for production")
            
            data = {
                "assoscmd": "anologin",
                "rtype": "json",
                "userid": settings.GIB_USERNAME,
                "sifre": settings.GIB_PASSWORD,
                "sifre2": settings.GIB_PASSWORD,
                "parola": "1",
            }
        else:
            if settings.GIB_USERNAME and settings.GIB_PASSWORD:
                data = {
                    "assoscmd": "login",
                    "rtype": "json",
                    "userid": settings.GIB_USERNAME,
                    "sifre": settings.GIB_PASSWORD,
                    "sifre2": settings.GIB_PASSWORD,
                    "parola": "1",
                }
            else:
                test_creds = await self._get_test_credentials()
                data = {
                    "assoscmd": "login",
                    "rtype": "json",
                    "userid": test_creds["userid"],
                    "sifre": test_creds["sifre"],
                    "sifre2": test_creds["sifre"],
                    "parola": "1",
                }

        try:
            response = await self.http_client.post(url, data=data)
            response.raise_for_status()
            
            resp_json = response.json()
            token = resp_json.get("token", "")
            if not token:
                error_msg = resp_json.get("error", "unknown")
                messages = resp_json.get("messages", [])
                raise AuthenticationError(
                    f"Login failed (error={error_msg}): {messages}"
                )
            
            return token
        except httpx.HTTPError as e:
            raise GibApiError(f"HTTP Error during login: {str(e)}")

    async def _get_test_credentials(self) -> dict:
        url = f"{self.base_url}/esign"
        data = {"assoscmd": "kullaniciOner"}
        
        try:
            response = await self.http_client.post(url, data=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise GibApiError(f"HTTP Error getting test credentials: {str(e)}")

    async def dispatch(self, cmd: str, token: str, jp_dict: Dict[str, Any] = None, page_name: str = "RG_KULLANICI") -> dict:
        url = f"{self.base_url}/dispatch"
        
        if jp_dict is None:
            jp_dict = {}
            
        payload = {
            "cmd": cmd,
            "callid": str(uuid.uuid1()),
            "pageName": page_name,
            "token": token,
            "jp": json.dumps(jp_dict, ensure_ascii=True)
        }
        
        try:
            response = await self.http_client.post(url, data=payload)
            response.raise_for_status()
            
            content_type = response.headers.get("content-type", "")
            
            if "text/html" in content_type.lower():
                if "Oturum Süreniz Dolmuştur" in response.text or "Giriş sayfasına" in response.text:
                    raise SessionExpiredError("GIB Session expired")
                raise GibApiError("GIB returned HTML instead of JSON.", response_text=response.text[:200])
                
            try:
                result = response.json()
            except json.JSONDecodeError:
                raise GibApiError("Failed to parse JSON response from GIB", response_text=response.text[:200])

            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict) and item.get("type") == "4":
                        raise SessionExpiredError("GIB Session expired")
                raise GibApiError(f"GIB API Error: {result}", response_text=response.text)
            if isinstance(result, dict):
                if result.get("type") == "4":
                    raise SessionExpiredError("GIB Session expired")
                if result.get("error"):
                    raise GibApiError(f"GIB API Error: {result.get('messages', result.get('error'))}", response_text=response.text)
                
            return result
            
        except httpx.HTTPError as e:
            raise GibApiError(f"HTTP Error during dispatch: {str(e)}")

    async def download(self, token: str, ettn: str, belge_tip: str = "FATURA", onay_durumu: str = "Onaylandı") -> bytes:
        url = f"{self.base_url}/download"
        params = {
            "token": token,
            "ettn": ettn,
            "belgeTip": belge_tip,
            "onayDurumu": onay_durumu,
            "cmd": "EARSIV_PORTAL_BELGE_INDIR"
        }
        try:
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            
            if "text/html" in response.headers.get("content-type", "").lower():
                if "Oturum Süreniz Dolmuştur" in response.text:
                    raise SessionExpiredError("GIB Session expired")
                    
            return response.content
        except httpx.HTTPError as e:
            raise GibApiError(f"HTTP Error during download: {str(e)}")
