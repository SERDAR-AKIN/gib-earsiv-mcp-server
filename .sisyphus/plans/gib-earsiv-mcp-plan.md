# GİB e-Arşiv MCP Sunucusu Geliştirme Planı

Bu belge, Gelir İdaresi Başkanlığı (GİB) e-Arşiv portalı için geliştirilecek Python tabanlı MCP (Model Context Protocol) sunucusunun mimarisini ve aşamalarını tanımlar.

## 1. Mimari Kararlar
- **Çerçeve (Framework):** `fastmcp` (PrefectHQ) v3.4+ (En güncel sürüm, lifespan ve middleware desteği)
- **Dil:** Python 3.10+
- **Taşıyıcı (Transport):** Hem `stdio` (yerel kullanım) hem de `streamable-http` (uzak kullanım) desteklenecek.
- **Modlar:** 
  - `production` (earsivportal.efatura.gov.tr - Gerçek TC kimlik/şifre)
  - `test` (earsivportaltest.efatura.gov.tr - `/earsiv-services/esign` üzerinden otomatik test kullanıcısı oluşturma)
  - `mock` (GİB sunucuları 503 verdiğinde geliştirme yapabilmek için statik/dinamik sahte yanıtlar)
- **Loglama:** FastMCP'nin `Context` objesi üzerinden (örn. `await ctx.info()`)
- **Bağımlılık Yönetimi:** `uv`

## 2. Kritik Problemlerin Çözümü

### A. Oturum (Session) Yönetimi
GİB API'sinde `assos-login` başarılı olduğunda bir token döner ve sonraki `dispatch` veya `download` isteklerinde bu token'ın kullanılması gerekir.
- **Çözüm:** FastMCP `lifespan` kullanılarak uygulama ömrü boyunca yaşayacak bir durum (state) yönetimi kurulacak.
- Token, bir `Dict[client_id, token]` yapısında hafızada tutulacak. Her tool çağrısında `ctx.request_context.lifespan_context` üzerinden mevcut token alınacak, yoksa veya süresi dolmuşsa otomatik yeniden giriş yapılacak.

### B. JP Parametresi Formatlaması (En Büyük Risk)
`dispatch` isteklerinde tüm veriler `cmd` ve `jp` isimli form parametreleri ile gönderiliyor. `jp`, JSON formatında ancak dışarıdan çift tırnakla (string olarak) sarılıp escape edilmesi gerekiyor.
- **Çözüm:** Parametre hazırlama mantığı merkezi bir fonksiyona (`GibClient.dispatch()`) alınacak. Pydantic ile validate edilen objeler, tek bir merkezde güvenli şekilde JSON string'e dönüştürülecek.

### C. GİB 503 ve Hata Yönetimi
GİB sunucuları sık sık çöker (503) veya JSON yerine HTML döner.
- **Çözüm:** 
  - **RetryMiddleware:** 502, 503 ve zaman aşımı (TimeoutError) hatalarında `RetryMiddleware` ile (exponential backoff) otomatik 3 tekrar yapılacak.
  - **ErrorHandlingMiddleware:** HTML veya anlamsız yanıtlar temiz MCP `ToolError` mesajlarına dönüştürülecek.

### D. Mock Modu (Sahte Veri Modu)
GİB'in kapalı olduğu zamanlar için HTTP katmanında (örn. `httpx.MockTransport` veya sınıflar arası soyutlama) sahte yanıt döndüren bir `MockGibClient` yazılacak. `GIB_ENV=mock` ise bu client çalışacak.

## 3. MCP Tool Tanımları (14 Komut)

Tüm araçlar, birbirleriyle çakışmamak adına `gib_earsiv_` önekiyle adlandırılacaktır.

1. **`gib_earsiv_fatura_olustur`**: Fatura keser (Taslak olarak). Pydantic modeliyle detaylı veri doğrulama.
2. **`gib_earsiv_taslaklari_getir`**: Taslaklar kutusundaki faturaları listeler. Tarih aralığı destekler.
3. **`gib_earsiv_adima_kesilen_belgeler`**: Vergi no/TC'ye kesilen belgeleri getirir.
4. **`gib_earsiv_fatura_getir`**: Tek bir faturanın detaylarını (JSON) getirir.
5. **`gib_earsiv_fatura_goster`**: Faturayı HTML formatında görüntüler.
6. **`gib_earsiv_fatura_sil`**: Taslak durumundaki bir faturayı iptal eder/siler.
7. **`gib_earsiv_belge_indir`**: Faturayı ZIP formatında indirir.
8. **`gib_earsiv_kullanici_bilgileri_getir`**: Portaldaki profil bilgilerini çeker.
9. **`gib_earsiv_kullanici_bilgileri_kaydet`**: Profil bilgilerini günceller.
10. **`gib_earsiv_sicil_sorgula`**: Vergi Kimlik No (VKN) / TCKN üzerinden mükellef bilgisi sorgular.
11. **`gib_earsiv_telefon_sorgula`**: Sistemde kayıtlı onay telefonunu sorgular (SMS adımı 1).
12. **`gib_earsiv_sms_gonder`**: Fatura onay için SMS kodu gönderir (SMS adımı 2).
13. **`gib_earsiv_sms_onayla`**: Gelen kodu doğrulayıp faturayı imzalar (SMS adımı 3).
14. **`gib_earsiv_menu_getir`**: Kullanıcı menü yetkilerini listeler.

## 4. Proje Dizini Yapısı

```
/mnt/nvme_2tb/Kodlama/arsiv-fatura/
├── pyproject.toml               # Bağımlılıklar (fastmcp, httpx, pydantic)
├── src/
│   ├── gib_earsiv_mcp/
│   │   ├── __init__.py
│   │   ├── server.py            # FastMCP sunucu tanımı ve entrypoint
│   │   ├── tools.py             # 14 adet mcp.tool() tanımı
│   │   ├── core/
│   │   │   ├── client.py        # GIBClient (gerçek istekler)
│   │   │   ├── mock_client.py   # Sahte istekler (Mock mode)
│   │   │   ├── session.py       # Lifespan ve state yönetimi
│   │   │   ├── exceptions.py    # Özel hata sınıfları
│   │   ├── models/
│   │   │   ├── input.py         # Tool girdileri için Pydantic sınıfları
│   │   │   └── api.py           # GİB JSON şemaları (jp formatları)
├── tests/
│   ├── test_client.py
│   ├── test_tools.py
└── .env.example                 # Ortam değişkenleri (GIB_ENV, GIB_USER vs.)
```

## 5. Geliştirme Fazları

### Faz 1: Altyapı ve Mocking (Odak: Mimari)
1. `uv` ile proje kurulumu.
2. `GIB_ENV` (test/prod/mock) yapısının kurulması.
3. FastMCP `lifespan` kullanılarak `SessionManager`'ın yazılması (token tutma).
4. Sadece `login` işleminin gerçeklenmesi (Gerçek ve Mock ortamda).
5. FastMCP Middleware eklenmesi (Rate limiting ve Retry).

### Faz 2: Temel Akış (Odak: Okuma ve Doğrulama)
1. JP string parser ve form request metotlarının yazılması (`dispatch` metodu).
2. Temel okuma toolları: `kullanici_bilgileri_getir`, `taslaklari_getir`, `menu_getir`.
3. Pydantic şemalarının yazılması.

### Faz 3: İleri Akış (Odak: Yazma ve İndirme)
1. Fatura oluşturma şeması (`fatura_olustur`) ve validasyonu.
2. Fatura indirme (`belge_indir`) ve görüntüleme (`fatura_goster`).
3. SMS doğrulama üçlüsünün yazılması (Sorgula -> Gönder -> Onayla).

### Faz 4: Test ve Dağıtım (Odak: Güvenilirlik)
1. FastMCP yerleşik `Client` objesiyle In-Memory testler yazılması.
2. `pyproject.toml` içerisine entrypoint eklenmesi.
3. Hata mesajlarının optimize edilmesi (LLM'e anlamlı hatalar gönderme).