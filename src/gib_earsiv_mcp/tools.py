from typing import Annotated
from datetime import datetime, timedelta
import base64

from pydantic import Field
from fastmcp import Context

from .server import mcp
from .core.session import AppState
from .core.exceptions import GibApiError, SessionExpiredError
from .models.input import (
    FaturaKalemi,
    FaturaOlusturInput,
)


@mcp.tool()
async def gib_earsiv_ping(ctx: Context) -> str:
    state: AppState = ctx.request_context.lifespan_context
    client_id = ctx.client_id or "default"
    token = await state.get_valid_token(client_id)
    return f"Successfully authenticated. Token prefix: {token[:10]}..."


@mcp.tool(
    name="gib_earsiv_kullanici_bilgileri_getir",
    description="GIB e-Arsiv portalındaki kullanıcı profil bilgilerini getirir.",
    annotations={"readOnlyHint": True, "destructiveHint": False},
)
async def gib_earsiv_kullanici_bilgileri_getir(ctx: Context) -> dict:
    state: AppState = ctx.request_context.lifespan_context
    client_id = ctx.client_id or "default"
    try:
        token = await state.get_valid_token(client_id)
        return await state.gib_client.dispatch(
            "EARSIV_PORTAL_KULLANICI_BILGILERI_GETIR", token
        )
    except SessionExpiredError:
        state.clear_token(client_id)
        raise


@mcp.tool(
    name="gib_earsiv_menu_getir",
    description="GIB portalındaki kullanıcının yetkili olduğu menüleri getirir.",
    annotations={"readOnlyHint": True},
)
async def gib_earsiv_menu_getir(ctx: Context) -> dict:
    state: AppState = ctx.request_context.lifespan_context
    client_id = ctx.client_id or "default"
    try:
        token = await state.get_valid_token(client_id)
        return await state.gib_client.dispatch(
            "getUserMenu",
            token,
            jp_dict={"ANONIM_LOGIN": "1"},
            page_name="MAINTREEMENU",
        )
    except SessionExpiredError:
        state.clear_token(client_id)
        raise


@mcp.tool(
    name="gib_earsiv_taslaklari_getir",
    description="Belirtilen tarih aralığındaki taslak faturaları listeler.",
    annotations={"readOnlyHint": True},
)
async def gib_earsiv_taslaklari_getir(
    ctx: Context,
    baslangic_tarihi: str | None = None,
    bitis_tarihi: str | None = None,
) -> dict:
    state: AppState = ctx.request_context.lifespan_context
    client_id = ctx.client_id or "default"

    if not bitis_tarihi:
        bitis_tarihi = datetime.now().strftime("%d/%m/%Y")
    if not baslangic_tarihi:
        baslangic_tarihi = (datetime.now() - timedelta(days=30)).strftime(
            "%d/%m/%Y"
        )

    jp_dict = {
        "baslangic": baslangic_tarihi,
        "bitis": bitis_tarihi,
        "hangiTip": "5000/30000",
    }
    try:
        token = await state.get_valid_token(client_id)
        return await state.gib_client.dispatch(
            "EARSIV_PORTAL_TASLAKLARI_GETIR",
            token,
            jp_dict=jp_dict,
            page_name="RG_BASITTASLAKLAR",
        )
    except SessionExpiredError:
        state.clear_token(client_id)
        raise


@mcp.tool(
    name="gib_earsiv_imza_bekleyenler",
    description="İmza bekleyen (onaylanmamış) faturaları listeler. SMS ile imzalanmayı bekleyen taslak faturaları döndürür.",
    annotations={"readOnlyHint": True},
)
async def gib_earsiv_imza_bekleyenler(
    ctx: Context,
    baslangic_tarihi: str | None = None,
    bitis_tarihi: str | None = None,
) -> dict:
    state: AppState = ctx.request_context.lifespan_context
    client_id = ctx.client_id or "default"

    if not bitis_tarihi:
        bitis_tarihi = datetime.now().strftime("%d/%m/%Y")
    if not baslangic_tarihi:
        baslangic_tarihi = (datetime.now() - timedelta(days=30)).strftime(
            "%d/%m/%Y"
        )

    jp_dict = {
        "baslangic": baslangic_tarihi,
        "bitis": bitis_tarihi,
        "hangiTip": "5000/30000",
    }
    try:
        token = await state.get_valid_token(client_id)
        result = await state.gib_client.dispatch(
            "EARSIV_PORTAL_TASLAKLARI_GETIR",
            token,
            jp_dict=jp_dict,
            page_name="RG_BASITTASLAKLAR",
        )
        all_invoices = result.get("data", [])
        if isinstance(all_invoices, list):
            pending = [
                inv
                for inv in all_invoices
                if inv.get("onayDurumu") == "Onaylanmadı"
            ]
            return {
                "data": pending,
                "total": len(pending),
                "filtered_from": len(all_invoices),
            }
        return result
    except SessionExpiredError:
        state.clear_token(client_id)
        raise


@mcp.tool(
    name="gib_earsiv_adima_kesilen_belgeler",
    description="Adıma (VKN/TCKN) kesilen e-Arşiv faturaları listeler.",
    annotations={"readOnlyHint": True},
)
async def gib_earsiv_adima_kesilen_belgeler(
    ctx: Context,
    baslangic_tarihi: str | None = None,
    bitis_tarihi: str | None = None,
) -> dict:
    state: AppState = ctx.request_context.lifespan_context
    client_id = ctx.client_id or "default"

    if not bitis_tarihi:
        bitis_tarihi = datetime.now().strftime("%d/%m/%Y")
    if not baslangic_tarihi:
        baslangic_tarihi = (datetime.now() - timedelta(days=30)).strftime(
            "%d/%m/%Y"
        )

    jp_dict = {
        "baslangic": baslangic_tarihi,
        "bitis": bitis_tarihi,
        "hourlySearchInterval": "NONE",
        "table": [],
    }
    try:
        token = await state.get_valid_token(client_id)
        return await state.gib_client.dispatch(
            "EARSIV_PORTAL_ADIMA_KESILEN_BELGELERI_GETIR",
            token,
            jp_dict=jp_dict,
            page_name="RG_ALICI_TASLAKLAR",
        )
    except SessionExpiredError:
        state.clear_token(client_id)
        raise


def _build_invoice_jp(params: FaturaOlusturInput) -> dict:
    mal_hizmet_table = []
    for k in params.malHizmetListe:
        mal_hizmet_table.append(
            {
                "malHizmet": k.malHizmet,
                "miktar": k.miktar,
                "birim": "ADET",
                "birimFiyat": str(k.birimFiyat),
                "fiyat": str(k.fiyat),
                "iskontoOrani": k.iskontoOrani,
                "iskontoTutari": str(k.iskontoTutari),
                "iskontoNedeni": k.iskontoNedeni,
                "malHizmetTutari": str(k.malHizmetTutari),
                "kdvOrani": str(k.kdvOrani),
                "vergiOrani": 0,
                "kdvTutari": str(k.kdvTutari),
                "vergininKdvTutari": "0",
                "ozelMatrahTutari": "0",
            }
        )
    return {
        "faturaUuid": "",
        "belgeNumarasi": params.belgeNumarasi or "",
        "faturaTarihi": params.faturaTarihi,
        "saat": params.saat,
        "paraBirimi": params.paraBirimi or "TRY",
        "dovzTLkur": "0",
        "faturaTipi": "SATIS",
        "hangiTip": "5000/30000",
        "vknTckn": params.vknTckn,
        "aliciUnvan": params.aliciUnvan or "",
        "aliciAdi": params.aliciAdi or "",
        "aliciSoyadi": params.aliciSoyadi or "",
        "binaAdi": params.binaAd or "",
        "binaNo": params.binaNo or "",
        "kapiNo": params.kapiNo or "",
        "kasabaKoy": params.kasabaKoy or "",
        "vergiDairesi": params.vergiDairesi or "",
        "ulke": params.ulke or "Türkiye",
        "bulvarcaddesokak": params.bulvarcaddesokak or "",
        "mahalleSemtIlce": params.mahalleSemtIlce or "",
        "sehir": params.sehir or "",
        "postaKodu": params.postaKodu or "",
        "tel": params.tel or "",
        "fax": params.fax or "",
        "eposta": params.eposta or "",
        "websitesi": "",
        "iadeTable": [],
        "ozelMatrahTutari": "0",
        "ozelMatrahOrani": 0,
        "ozelMatrahVergiTutari": "0",
        "vergiCesidi": " ",
        "malHizmetTable": mal_hizmet_table,
        "tip": "İskonto",
        "matrah": str(params.matrah),
        "malhizmetToplamTutari": str(params.malhizmetToplamTutari),
        "toplamIskonto": str(params.toplamIskonto),
        "hesaplanankdv": str(params.hesaplananKdv),
        "vergilerToplami": str(params.hesaplananKdv),
        "vergilerDahilToplamTutar": str(params.vergilerDahilToplamTutar),
        "odenecekTutar": str(params.odenecekTutar),
        "not": params.notlar or "",
        "siparisNumarasi": "",
        "siparisTarihi": "",
        "irsaliyeNumarasi": "",
        "irsaliyeTarihi": "",
        "fisNo": "",
        "fisTarihi": "",
        "fisSaati": " ",
        "fisTipi": " ",
        "zRaporNo": "",
        "okcSeriNo": "",
    }


@mcp.tool(
    name="gib_earsiv_fatura_olustur",
    description="Yeni bir e-Arşiv fatura oluşturur (Taslak olarak kaydeder). GIB otomatik ETN atar.",
    annotations={"readOnlyHint": False, "destructiveHint": False},
)
async def gib_earsiv_fatura_olustur(
    faturaTarihi: Annotated[
        str, Field(description="Fatura Tarihi (GG/AA/YYYY) Örn: 10/06/2026")
    ],
    saat: Annotated[
        str, Field(description="Fatura Saati (SS:DD:DD) Örn: 14:30:00")
    ],
    vknTckn: Annotated[
        str,
        Field(
            description="Alıcı VKN/TCKN (11 haneli TC veya 10 haneli VKN)"
        ),
    ],
    matrah: Annotated[float, Field(description="Vergisiz toplam tutar")],
    malhizmetToplamTutari: Annotated[
        float, Field(description="KDV hariç mal/hizmet toplam tutarı")
    ],
    hesaplananKdv: Annotated[
        float, Field(description="Toplam KDV tutarı")
    ],
    vergilerDahilToplamTutar: Annotated[
        float, Field(description="Vergiler dahil genel toplam")
    ],
    odenecekTutar: Annotated[
        float, Field(description="Ödenecek toplam tutar")
    ],
    malHizmetListe: Annotated[
        list[dict], Field(description="Fatura kalemleri listesi")
    ],
    belgeNumarasi: Annotated[str, Field(default="")] = "",
    paraBirimi: Annotated[str, Field(default="TRY")] = "TRY",
    aliciUnvan: Annotated[
        str, Field(default="", description="Firma ise unvan")
    ] = "",
    aliciAdi: Annotated[
        str, Field(default="", description="Şahıs ise adı")
    ] = "",
    aliciSoyadi: Annotated[
        str, Field(default="", description="Şahıs ise soyadı")
    ] = "",
    binaAd: Annotated[str, Field(default="")] = "",
    binaNo: Annotated[str, Field(default="")] = "",
    kapiNo: Annotated[str, Field(default="")] = "",
    kasabaKoy: Annotated[str, Field(default="")] = "",
    vergiDairesi: Annotated[str, Field(default="")] = "",
    ulke: Annotated[str, Field(default="Türkiye")] = "Türkiye",
    bulvarcaddesokak: Annotated[str, Field(default="")] = "",
    mahalleSemtIlce: Annotated[str, Field(default="")] = "",
    sehir: Annotated[str, Field(default="")] = "",
    postaKodu: Annotated[str, Field(default="")] = "",
    tel: Annotated[str, Field(default="")] = "",
    fax: Annotated[str, Field(default="")] = "",
    eposta: Annotated[str, Field(default="")] = "",
    notlar: Annotated[str, Field(default="")] = "",
    toplamIskonto: Annotated[float, Field(default=0)] = 0,
    ctx: Context = None,
) -> dict:
    state: AppState = ctx.request_context.lifespan_context
    client_id = ctx.client_id or "default"

    kalem_list = [FaturaKalemi(**k) for k in malHizmetListe]
    params = FaturaOlusturInput(
        faturaTarihi=faturaTarihi,
        saat=saat,
        vknTckn=vknTckn,
        matrah=matrah,
        malhizmetToplamTutari=malhizmetToplamTutari,
        hesaplananKdv=hesaplananKdv,
        vergilerDahilToplamTutar=vergilerDahilToplamTutar,
        odenecekTutar=odenecekTutar,
        malHizmetListe=kalem_list,
        belgeNumarasi=belgeNumarasi,
        paraBirimi=paraBirimi,
        aliciUnvan=aliciUnvan,
        aliciAdi=aliciAdi,
        aliciSoyadi=aliciSoyadi,
        binaAd=binaAd,
        binaNo=binaNo,
        kapiNo=kapiNo,
        kasabaKoy=kasabaKoy,
        vergiDairesi=vergiDairesi,
        ulke=ulke,
        bulvarcaddesokak=bulvarcaddesokak,
        mahalleSemtIlce=mahalleSemtIlce,
        sehir=sehir,
        postaKodu=postaKodu,
        tel=tel,
        fax=fax,
        eposta=eposta,
        notlar=notlar,
        toplamIskonto=toplamIskonto,
    )

    jp_dict = _build_invoice_jp(params)
    try:
        token = await state.get_valid_token(client_id)
        result = await state.gib_client.dispatch(
            "EARSIV_PORTAL_FATURA_OLUSTUR",
            token,
            jp_dict=jp_dict,
            page_name="RG_BASITFATURA",
        )
        data_msg = result.get("data", "")
        if "başarıyla oluşturulmuştur" in data_msg:
            now = datetime.now()
            start = now - timedelta(days=30)
            draft_jp = {
                "baslangic": start.strftime("%d/%m/%Y"),
                "bitis": now.strftime("%d/%m/%Y"),
                "hangiTip": "5000/30000",
            }
            drafts_result = await state.gib_client.dispatch(
                "EARSIV_PORTAL_TASLAKLARI_GETIR",
                token,
                jp_dict=draft_jp,
                page_name="RG_BASITTASLAKLAR",
            )
            drafts = drafts_result.get("data", [])
            target_name = (
                f"{params.aliciAdi} {params.aliciSoyadi}".strip()
                or params.aliciUnvan
            )
            for inv in reversed(drafts):
                if (
                    inv.get("onayDurumu") == "Onaylanmadı"
                    and target_name
                    and target_name in inv.get("aliciUnvanAdSoyad", "")
                ):
                    result["ettn"] = inv.get("ettn")
                    result["belgeNumarasi"] = inv.get("belgeNumarasi", "")
                    break
        return result
    except SessionExpiredError:
        state.clear_token(client_id)
        raise


@mcp.tool(
    name="gib_earsiv_fatura_sil",
    description="Taslak durumundaki bir faturayı iptal eder/siler.",
    annotations={"readOnlyHint": False, "destructiveHint": True},
)
async def gib_earsiv_fatura_sil(
    fatura_uuid: Annotated[
        str, Field(description="Silinecek faturanın ETN (UUID) değeri")
    ],
    belge_numarasi: Annotated[
        str, Field(default="", description="Fatura belge numarası")
    ] = "",
    fatura_tarihi: Annotated[
        str, Field(default="", description="Fatura tarihi (GG/AA/YYYY)")
    ] = "",
    toplam_tutar: Annotated[
        str, Field(default="", description="Toplam tutar")
    ] = "",
    onay_durumu: Annotated[
        str,
        Field(
            default="Onaylanmadı",
            description="Fatura onay durumu (Onaylandı/Onaylanmadı)",
        ),
    ] = "Onaylanmadı",
    belge_turu: Annotated[
        str, Field(default="FATURA", description="Belge türü (FATURA)")
    ] = "FATURA",
    alici_vkn_tckn: Annotated[
        str, Field(default="", description="Alıcı VKN/TCKN")
    ] = "",
    alici_unvan_ad_soyad: Annotated[
        str, Field(default="", description="Alıcı unvan/ad soyad")
    ] = "",
    aciklama: Annotated[
        str, Field(default="", description="Silme nedeni")
    ] = "",
    ctx: Context = None,
) -> dict:
    state: AppState = ctx.request_context.lifespan_context
    client_id = ctx.client_id or "default"

    delete_item = {"ettn": fatura_uuid}
    if belge_numarasi:
        delete_item["belgeNumarasi"] = belge_numarasi
    if fatura_tarihi:
        delete_item["belgeTarihi"] = fatura_tarihi
    if toplam_tutar:
        delete_item["toplamTutar"] = toplam_tutar
    if onay_durumu:
        delete_item["onayDurumu"] = onay_durumu
    if belge_turu:
        delete_item["belgeTuru"] = belge_turu
    if alici_vkn_tckn:
        delete_item["aliciVknTckn"] = alici_vkn_tckn
    if alici_unvan_ad_soyad:
        delete_item["aliciUnvanAdSoyad"] = alici_unvan_ad_soyad

    jp_dict = {"silinecekler": [delete_item]}
    if aciklama:
        jp_dict["aciklama"] = aciklama
    try:
        token = await state.get_valid_token(client_id)
        return await state.gib_client.dispatch(
            "EARSIV_PORTAL_FATURA_SIL",
            token,
            jp_dict=jp_dict,
            page_name="RG_TASLAKLAR",
        )
    except SessionExpiredError:
        state.clear_token(client_id)
        raise


@mcp.tool(
    name="gib_earsiv_belge_indir",
    description="Faturayı ZIP formatında indirir ve base64 olarak döner.",
    annotations={"readOnlyHint": True},
)
async def gib_earsiv_belge_indir(
    ettn: Annotated[
        str, Field(description="Faturanın ETN (UUID) değeri")
    ],
    belge_tip: Annotated[
        str,
        Field(
            default="FATURA",
            description="Belge tipi (FATURA, SMM, MÜSTAHSİL)",
        ),
    ] = "FATURA",
    onay_durumu: Annotated[
        str,
        Field(
            default="Onaylandı",
            description="Onay durumu (Onaylandı, Onaylanmadı)",
        ),
    ] = "Onaylandı",
    ctx: Context = None,
) -> dict:
    state: AppState = ctx.request_context.lifespan_context
    client_id = ctx.client_id or "default"
    try:
        token = await state.get_valid_token(client_id)
        file_bytes = await state.gib_client.download(
            token, ettn=ettn, belge_tip=belge_tip, onay_durumu=onay_durumu
        )
        return {
            "filename": f"{ettn}.zip",
            "content_base64": base64.b64encode(file_bytes).decode("utf-8"),
        }
    except SessionExpiredError:
        state.clear_token(client_id)
        raise


@mcp.tool(
    name="gib_earsiv_fatura_goster",
    description="Faturayı HTML formatında görüntüler.",
    annotations={"readOnlyHint": True},
)
async def gib_earsiv_fatura_goster(
    fatura_uuid: Annotated[
        str,
        Field(description="Görüntülenecek faturanın ETN (UUID) değeri"),
    ],
    onay_durumu: Annotated[
        str,
        Field(
            default="Onaylandı",
            description="Faturanın onay durumu (Onaylandı/Onaylanmadı)",
        ),
    ] = "Onaylandı",
    ctx: Context = None,
) -> str:
    state: AppState = ctx.request_context.lifespan_context
    client_id = ctx.client_id or "default"

    jp_dict = {"ettn": fatura_uuid, "onayDurumu": onay_durumu}
    try:
        token = await state.get_valid_token(client_id)
        result = await state.gib_client.dispatch(
            "EARSIV_PORTAL_FATURA_GOSTER",
            token,
            jp_dict=jp_dict,
            page_name="RG_TASLAKLAR",
        )
        if isinstance(result, dict) and "data" in result:
            return result["data"]
        return str(result)
    except SessionExpiredError:
        state.clear_token(client_id)
        raise


@mcp.tool(
    name="gib_earsiv_sicil_sorgula",
    description="VKN veya TCKN ile mükellef (şahıs/firma) unvan ve vergi dairesi bilgilerini sorgular.",
)
async def gib_earsiv_sicil_sorgula(
    vkn_tckn: Annotated[
        str,
        Field(
            description="Mükellefin VKN (10 haneli) veya TCKN (11 haneli) numarası"
        ),
    ],
    ctx: Context = None,
) -> dict:
    state: AppState = ctx.request_context.lifespan_context
    client_id = ctx.client_id or "default"

    jp_dict = {"vknTcknn": vkn_tckn}
    try:
        token = await state.get_valid_token(client_id)
        return await state.gib_client.dispatch(
            "SICIL_VEYA_MERNISTEN_BILGILERI_GETIR",
            token,
            jp_dict=jp_dict,
            page_name="RG_BASITFATURA",
        )
    except SessionExpiredError:
        state.clear_token(client_id)
        raise


@mcp.tool(
    name="gib_earsiv_sms_sorgula",
    description="Mükellefin sistemde kayıtlı GSM numarasını sorgular.",
)
async def gib_earsiv_sms_sorgula(ctx: Context) -> dict:
    state: AppState = ctx.request_context.lifespan_context
    client_id = ctx.client_id or "default"
    try:
        token = await state.get_valid_token(client_id)
        return await state.gib_client.dispatch(
            "EARSIV_PORTAL_TELEFONNO_SORGULA",
            token,
            jp_dict={},
            page_name="RG_BASITTASLAKLAR",
        )
    except SessionExpiredError:
        state.clear_token(client_id)
        raise


@mcp.tool(
    name="gib_earsiv_sms_gonder",
    description="Kayıtlı GSM numarasına onay kodu (SMS) gönderir.",
)
async def gib_earsiv_sms_gonder(
    telefon: Annotated[
        str,
        Field(
            description="SMS gönderilecek onaylı telefon numarası (örn: 0534XXXXXXX)"
        ),
    ],
    ctx: Context = None,
) -> dict:
    state: AppState = ctx.request_context.lifespan_context
    client_id = ctx.client_id or "default"
    try:
        token = await state.get_valid_token(client_id)
        await state.gib_client.dispatch(
            "EARSIV_PORTAL_TELEFONNO_SORGULA",
            token,
            jp_dict={},
            page_name="RG_BASITTASLAKLAR",
        )
        jp_dict = {"CEPTEL": telefon, "KCEPTEL": False, "TIP": ""}
        return await state.gib_client.dispatch(
            "EARSIV_PORTAL_SMSSIFRE_GONDER",
            token,
            jp_dict=jp_dict,
            page_name="RG_SMSONAY",
        )
    except SessionExpiredError:
        state.clear_token(client_id)
        raise


@mcp.tool(
    name="gib_earsiv_sms_onayla",
    description="Telefona gelen onay kodu ile faturayı imzalar.",
)
async def gib_earsiv_sms_onayla(
    oid: Annotated[
        str,
        Field(
            description="SmsGonder adımından dönen oid (Operation ID) değeri"
        ),
    ],
    sms_kodu: Annotated[
        str,
        Field(description="Telefona gelen 6 haneli doğrulama kodu"),
    ],
    fatura_uuid: Annotated[
        str,
        Field(description="İmzalanacak faturanın ETN (UUID) değeri"),
    ],
    belge_numarasi: Annotated[
        str,
        Field(default="", description="Fatura belge numarası (varsa)"),
    ] = "",
    onay_durumu: Annotated[
        str,
        Field(
            default="Onaylanmadı",
            description="Faturanın onay durumu",
        ),
    ] = "Onaylanmadı",
    ctx: Context = None,
) -> dict:
    state: AppState = ctx.request_context.lifespan_context
    client_id = ctx.client_id or "default"

    jp_dict = {
        "SIFRE": sms_kodu,
        "OID": oid,
        "OPR": 1,
        "DATA": [
            {
                "ettn": fatura_uuid,
                "belgeNumarasi": belge_numarasi or "",
                "onayDurumu": onay_durumu,
            }
        ],
    }
    try:
        token = await state.get_valid_token(client_id)
        return await state.gib_client.dispatch(
            "0lhozfib5410mp",
            token,
            jp_dict=jp_dict,
            page_name="RG_SMSONAY",
        )
    except SessionExpiredError:
        state.clear_token(client_id)
        raise


@mcp.tool(
    name="gib_earsiv_fatura_pdf_indir",
    description="Faturayı PDF formatında indirir (base64 olarak döner).",
    annotations={"readOnlyHint": True},
)
async def gib_earsiv_fatura_pdf_indir(
    fatura_uuid: Annotated[
        str, Field(description="Faturanın ETN (UUID) değeri")
    ],
    onay_durumu: Annotated[
        str,
        Field(
            default="Onaylandı",
            description="Faturanın onay durumu (Onaylandı/Onaylanmadı)",
        ),
    ] = "Onaylandı",
    ctx: Context = None,
) -> dict:
    from weasyprint import HTML

    state: AppState = ctx.request_context.lifespan_context
    client_id = ctx.client_id or "default"

    jp_dict = {"ettn": fatura_uuid, "onayDurumu": onay_durumu}
    try:
        token = await state.get_valid_token(client_id)
        result = await state.gib_client.dispatch(
            "EARSIV_PORTAL_FATURA_GOSTER",
            token,
            jp_dict=jp_dict,
            page_name="RG_TASLAKLAR",
        )
        html = result.get("data", "")
        if not html:
            return {"error": "Fatura HTML içeriği alınamadı"}

        pdf_bytes = HTML(string=html).write_pdf() or b""
        if not pdf_bytes:
            return {"error": "PDF oluşturulamadı"}
        return {
            "filename": f"{fatura_uuid}.pdf",
            "content_base64": base64.b64encode(pdf_bytes).decode("utf-8"),
            "size_bytes": len(pdf_bytes),
        }
    except SessionExpiredError:
        state.clear_token(client_id)
        raise
