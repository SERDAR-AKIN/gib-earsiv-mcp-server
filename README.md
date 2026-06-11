# 📄 GİB e-Arşiv MCP Sunucusu

Bu proje, Gelir İdaresi Başkanlığı (GİB) e-Arşiv Portalına entegre olarak çalışan ve yapay zeka asistanları (Claude, vb.) için [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) araçları sağlayan bir Python sunucusudur.

Sunucu sayesinde; GİB portalı üzerinden otomatik fatura taslakları oluşturabilir, faturaları iptal edebilir, SMS ile imzalama süreçlerini yönetebilir ve PDF olarak faturayı indirebilirsiniz.

## 🚀 Özellikler ve Araçlar (Tools)

Aşağıdaki araçlar MCP üzerinden kullanılabilir durumdadır:

*   **`gib_earsiv_fatura_olustur`**: Yeni bir e-Arşiv fatura taslağı oluşturur. GİB tarafından otomatik ETTN atanır.
*   **`gib_earsiv_fatura_sil`**: Taslak durumundaki (henüz imzalanmamış) faturayı iptal eder/siler.
*   **`gib_earsiv_taslaklari_getir`**: Belirtilen tarih aralığındaki taslak faturaları listeler.
*   **`gib_earsiv_imza_bekleyenler`**: SMS ile imzalanmayı bekleyen onaylanmamış faturaları listeler.
*   **`gib_earsiv_sms_sorgula`**: Mükellefin sistemde kayıtlı GSM numarasını sorgular.
*   **`gib_earsiv_sms_gonder`**: Kayıtlı GSM numarasına fatura imzalama için onay kodu (OTP SMS) gönderir.
*   **`gib_earsiv_sms_onayla`**: Telefona gelen 6 haneli kod ile taslak halindeki faturayı imzalar (resmileştirir).
*   **`gib_earsiv_fatura_goster`**: Faturanın HTML önizlemesini getirir.
*   **`gib_earsiv_fatura_pdf_indir`**: Faturayı PDF formatına dönüştürüp Base64 formatında indirir.
*   **`gib_earsiv_belge_indir`**: Faturayı orijinal GİB formatında ZIP olarak indirir.
*   **`gib_earsiv_kullanici_bilgileri_getir`**: Mükellef (Satıcı) profil bilgilerini getirir.
*   **`gib_earsiv_sicil_sorgula`**: VKN/TCKN üzerinden alıcı şirket/şahıs bilgilerini sorgular.
*   **`gib_earsiv_adima_kesilen_belgeler`**: Mükellefin (kendi) adına kesilen e-Arşiv faturaları listeler.

## 🛠️ Kurulum ve Çalıştırma

Proje paket yönetimi için [uv](https://github.com/astral-sh/uv) kullanmaktadır. PDF üretimi için `weasyprint` kütüphanesinden faydalanılır.

1. Bağımlılıkları kurun:
```bash
uv sync
```

2. `.env` dosyasını oluşturup GİB kimlik bilgilerinizi girin:
```env
GIB_ENV=production
GIB_USERNAME=vergi_no_veya_kullanici_kodu
GIB_PASSWORD=sifre
```

3. MCP Sunucusunu başlatın (Claude Desktop veya diğer istemciler config dosyanızdan otomatik başlatacaktır):
```bash
uv run python main.py
```

## 🔄 Örnek Akış: Fatura Oluşturma ve İmzalama

Sistemin uçtan uca çalışması için izlenmesi gereken doğru akış:

1. **Taslak Oluşturma:** `gib_earsiv_fatura_olustur` aracı çağrılır. (Not: `faturaUuid` boş bırakılmalı, GİB otomatik ETTN üretecektir).
2. **Kayıtlı Telefonu Sorgulama:** `gib_earsiv_sms_sorgula` ile sistemdeki cep telefonu numarası çekilir.
3. **SMS Gönderimi:** `gib_earsiv_sms_gonder` çağrılır. Sistem telefona kod iletir ve bir `OID` (Operation ID) döner.
4. **SMS Onayı (İmzalama):** Kullanıcıdan alınan 6 haneli kod, OID ve Fatura ETTN'si ile `gib_earsiv_sms_onayla` çağrılır. İşlem başarılı ise fatura "Onaylandı" statüsüne geçer.

## 💡 Geliştirici Notları ve Çözülen GİB Sorunları

GİB e-Arşiv portalının kendine has bazı arka plan davranışları projede çözülmüştür. Kodu geliştireceklerin dikkatine:

*   **Karakter Bozulmaları (Encoding):** GİB sistemine JSON verisi gönderilirken Türkçe karakterlerin bozulup `GÃ¼ltepe` gibi görünmesini önlemek için, HTTP payload'larında `json.dumps(..., ensure_ascii=True)` kullanılmalıdır. GİB, ASCII-safe `\uXXXX` kaçış dizilerini doğru işlemektedir.
*   **SMS Gönderme (NullPointerException) Hatası:** `EARSIV_PORTAL_SMSSIFRE_GONDER` komutunu çalıştırmadan hemen önce aynı session içinde MUTLAKA `EARSIV_PORTAL_TELEFONNO_SORGULA` komutu çalıştırılmalıdır. Aksi halde GİB sunucuları Java NullPointerException döndürür. Bu adım `gib_earsiv_sms_gonder` aracının içine entegre edilmiştir.
*   **ETTN Hatası:** Yeni fatura oluşturulurken `faturaUuid` alanına geçerli bir UUID dahi yazılsa GİB "Ettn sınırına uymuyor" hatası verebilmektedir. Çözüm, bu alanı boş string (`""`) olarak göndermektir.
*   **Fatura Silme:** `EARSIV_PORTAL_FATURA_SIL` işleminde silinecekler listesindeki anahtar `belgeNo` değil, **`belgeNumarasi`** olmalıdır ve `pageName` olarak `RG_TASLAKLAR` kullanılmalıdır. Ayrıca iptal işlemi için siparişin detaylı verisi sunulmalıdır.
