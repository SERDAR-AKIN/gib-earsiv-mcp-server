from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import List

class TaslaklariGetirInput(BaseModel):
    baslangic_tarihi: str = Field(
        default_factory=lambda: (datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y"),
        description="Başlangıç tarihi (GG/AA/YYYY formatında). Örn: 01/01/2025"
    )
    bitis_tarihi: str = Field(
        default_factory=lambda: datetime.now().strftime("%d/%m/%Y"),
        description="Bitiş tarihi (GG/AA/YYYY formatında). Örn: 31/01/2025"
    )

class BelgeIndirInput(BaseModel):
    ettn: str = Field(description="Faturanın ETN (UUID) değeri")
    belge_tip: str = Field(default="FATURA", description="Belge tipi (FATURA, SMM, MÜSTAHSİL)")
    onay_durumu: str = Field(default="Onaylandı", description="Onay durumu (Onaylandı, Onaylanmadı)")

class FaturaGosterInput(BaseModel):
    fatura_uuid: str = Field(description="Görüntülenecek faturanın ETN (UUID) değeri")
    onay_durumu: str = Field(default="Onaylandı", description="Faturanın onay durumu (Onaylandı/Onaylanmadı)")

class FaturaSilInput(BaseModel):
    fatura_uuid: str = Field(description="Silinecek faturanın ETN (UUID) değeri")
    belge_numarasi: str = Field(default="", description="Fatura belge numarası")
    fatura_tarihi: str = Field(default="", description="Fatura tarihi (GG/AA/YYYY)")
    toplam_tutar: str = Field(default="", description="Toplam tutar")
    onay_durumu: str = Field(default="Onaylanmadı", description="Fatura onay durumu (Onaylandı/Onaylanmadı)")
    belge_turu: str = Field(default="FATURA", description="Belge türü (FATURA)")
    alici_vkn_tckn: str = Field(default="", description="Alıcı VKN/TCKN")
    alici_unvan_ad_soyad: str = Field(default="", description="Alıcı unvan/ad soyad")
    aciklama: str = Field(default="", description="Silme nedeni")

class FaturaPdfIndirInput(BaseModel):
    fatura_uuid: str = Field(description="Faturanın ETN (UUID) değeri")
    onay_durumu: str = Field(default="Onaylandı", description="Faturanın onay durumu (Onaylandı/Onaylanmadı)")

class SicilSorgulaInput(BaseModel):
    vkn_tckn: str = Field(description="Mükellefin VKN (10 haneli) veya TCKN (11 haneli) numarası")

class SmsSorgulaInput(BaseModel):
    pass

class SmsGonderInput(BaseModel):
    telefon: str = Field(description="SMS gönderilecek onaylı telefon numarası (örn: 0534XXXXXXX)")

class SmsOnaylaInput(BaseModel):
    oid: str = Field(description="SmsGonder adımından dönen oid (Operation ID) değeri")
    sms_kodu: str = Field(description="Telefona gelen 6 haneli doğrulama kodu")
    fatura_uuid: str = Field(description="İmzalanacak faturanın ETN (UUID) değeri")
    belge_numarasi: str = Field(default="", description="Fatura belge numarası (varsa)")
    onay_durumu: str = Field(default="Onaylanmadı", description="Faturanın onay durumu")

class FaturaKalemi(BaseModel):
    malHizmet: str = Field(description="Mal/Hizmet açıklaması")
    miktar: float = Field(description="Miktar")
    birimFiyat: float = Field(description="Birim Fiyat")
    fiyat: float = Field(description="Tutar (Miktar * BirimFiyat)")
    kdvOrani: int = Field(description="KDV Oranı (Örn: 20)")
    kdvTutari: float = Field(description="KDV Tutarı")
    malHizmetTutari: float = Field(description="Vergiler Dahil Toplam Tutar")
    iskontoOrani: float = Field(default=0)
    iskontoTutari: float = Field(default=0)
    iskontoNedeni: str = Field(default="")
    
class FaturaOlusturInput(BaseModel):
    belgeNumarasi: str = Field(default="")
    faturaTarihi: str = Field(description="Fatura Tarihi (GG/AA/YYYY) Örn: 10/06/2026")
    saat: str = Field(description="Fatura Saati (SS:DD:DD) Örn: 14:30:00")
    paraBirimi: str = Field(default="TRY")
    vknTckn: str = Field(description="Alıcı VKN/TCKN (11 haneli TC veya 10 haneli VKN)")
    aliciUnvan: str = Field(default="", description="Firma ise unvan")
    aliciAdi: str = Field(default="", description="Şahıs ise adı")
    aliciSoyadi: str = Field(default="", description="Şahıs ise soyadı")
    binaAd: str = Field(default="")
    binaNo: str = Field(default="")
    kapiNo: str = Field(default="")
    kasabaKoy: str = Field(default="")
    vergiDairesi: str = Field(default="")
    ulke: str = Field(default="Türkiye")
    bulvarcaddesokak: str = Field(default="")
    mahalleSemtIlce: str = Field(default="")
    sehir: str = Field(default="")
    postaKodu: str = Field(default="")
    tel: str = Field(default="")
    fax: str = Field(default="")
    eposta: str = Field(default="")
    notlar: str = Field(default="")
    
    matrah: float = Field(description="Vergisiz toplam tutar")
    malhizmetToplamTutari: float = Field(description="KDV hariç mal/hizmet toplam tutarı")
    toplamIskonto: float = Field(default=0)
    hesaplananKdv: float = Field(description="Toplam KDV tutarı")
    vergilerDahilToplamTutar: float = Field(description="Vergiler dahil genel toplam")
    odenecekTutar: float = Field(description="Ödenecek toplam tutar")
    
    malHizmetListe: List[FaturaKalemi] = Field(description="Fatura kalemleri listesi")
