# 📄 GİB e-Arşiv MCP Server

> 🇹🇷 *Türkiye Gelir İdaresi Başkanlığı (GİB) e-Arşiv Portalı için FastMCP tabanlı MCP sunucusu*
> 🇬🇧 *FastMCP-based MCP server for the Turkish Revenue Administration (GİB) e-Arşiv Portal*

Bu proje, Gelir İdaresi Başkanlığı (GİB) e-Arşiv Portalına entegre olarak çalışan ve yapay zeka asistanları (Claude, vb.) için [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) araçları sağlayan bir Python sunucusudur.

*This project is a Python server that integrates with the Turkish Revenue Administration (GİB) e-Arşiv Portal and provides [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) tools for AI assistants (Claude, etc.).*

Sunucu sayesinde; GİB portalı üzerinden otomatik fatura taslakları oluşturabilir, faturaları iptal edebilir, SMS ile imzalama süreçlerini yönetebilir ve PDF olarak faturayı indirebilirsiniz.

*With this server, you can: create e-invoice drafts, cancel invoices, manage SMS-based signing workflows, and download invoices as PDF — all through the GİB portal.*

---

## 🚀 Tools / Araçlar

*All tools are available via MCP. Each tool name follows the `gib_earsiv_` prefix convention.*

| Tool | Description (EN) | Açıklama (TR) |
|------|-------------------|---------------|
| `gib_earsiv_ping` | Authentication check (token validation) | Kimlik doğrulama testi (token kontrolü) |
| `gib_earsiv_kullanici_bilgileri_getir` | Get taxpayer (seller) profile info | Mükellef (Satıcı) profil bilgilerini getirir |
| `gib_earsiv_menu_getir` | List portal menus | Portal menülerini listeler |
| `gib_earsiv_taslaklari_getir` | List draft invoices by date range | Belirtilen tarih aralığındaki taslak faturaları listeler |
| `gib_earsiv_imza_bekleyenler` | List invoices pending SMS signature | SMS ile imzalanmayı bekleyen onaylanmamış faturaları listeler |
| `gib_earsiv_adima_kesilen_belgeler` | List invoices issued to me (VKN/TCKN) | Adıma kesilen e-Arşiv faturalarını listeler |
| `gib_earsiv_fatura_olustur` | Create a new e-invoice draft (auto ETTN) | Yeni e-Arşiv fatura taslağı oluşturur (otomatik ETTN) |
| `gib_earsiv_fatura_sil` | Delete/cancel a draft invoice | Taslak faturayı iptal eder/siler |
| `gib_earsiv_fatura_goster` | View invoice as HTML preview | Faturanın HTML önizlemesini getirir |
| `gib_earsiv_fatura_pdf_indir` | Download invoice as Base64-encoded PDF | Faturayı PDF olarak Base64 formatında indirir |
| `gib_earsiv_belge_indir` | Download original GİB ZIP file | Faturayı orijinal GİB formatında ZIP olarak indirir |
| `gib_earsiv_sicil_sorgula` | Look up taxpayer info by VKN/TCKN | VKN/TCKN ile alıcı şirket/şahıs bilgilerini sorgular |
| `gib_earsiv_sms_sorgula` | Query registered GSM number | Sistemde kayıtlı GSM numarasını sorgular |
| `gib_earsiv_sms_gonder` | Send OTP SMS for invoice signing | İmzalama için onay kodu (OTP SMS) gönderir |
| `gib_earsiv_sms_onayla` | Confirm OTP and sign the invoice | 6 haneli kod ile faturayı imzalar (resmileştirir) |

---

## 🛠️ Installation / Kurulum

*This project uses [uv](https://github.com/astral-sh/uv) for package management and `weasyprint` for PDF generation.*

### 1. Install dependencies / Bağımlılıkları kurun

```bash
uv sync
```

### 2. Configure credentials / Kimlik bilgilerini yapılandırın

*Copy `.env.example` to `.env` and fill in your GİB credentials:*

```env
GIB_ENV=production
GIB_USERNAME=your_tax_id_or_username
GIB_PASSWORD=your_password
```

### Environment Modes / Ortam Modları

| Mode | Description (EN) | Açıklama (TR) |
|------|-------------------|---------------|
| `mock` | No real GİB connection — returns predefined responses (for dev/testing) | Gerçek GİB bağlantısı yapmaz, önceden tanımlı yanıtlar döner (geliştirme/test) |
| `test` | GİB test environment (`earsivportaltest.efatura.gov.tr`) | GİB test ortamı |
| `production` | Live GİB environment (`earsivportal.efatura.gov.tr`) — **real credentials required** | Canlı GİB ortamı — **gerçek kimlik bilgileri gerekli** |

### 3. Start the server / Sunucuyu başlatın

```bash
uv run gib-mcp
```

> ⚠️ `main.py` is a stub — the real entry point is the `gib-mcp` CLI command.
> ⚠️ `main.py` sadece stub'tır — gerçek giriş noktası `gib-mcp` CLI komutudur.

---

## 🧪 Testing / Testler

```bash
uv run pytest                    # Run all tests (auto GIB_ENV=mock)
uv run pytest -k "imza"          # Run signature-related tests
uv run pytest -k "fatura"        # Run invoice-related tests
uv run pytest -v                 # Verbose output
```

---

## 📦 Build / Derleme

```bash
uv build                         # Build wheel (hatchling)
```

---

## 🔄 Example Flow: Invoice Creation & Signing / Fatura Oluşturma ve İmzalama

1. **Create Draft:** Call `gib_earsiv_fatura_olustur`. (*Leave `faturaUuid` empty — GİB auto-assigns ETTN.*)
2. **Query Phone:** Call `gib_earsiv_sms_sorgula` to get the registered phone number.
3. **Send SMS:** Call `gib_earsiv_sms_gonder`. Returns an `OID` (Operation ID).
4. **Confirm & Sign:** Call `gib_earsiv_sms_onayla` with the 6-digit OTP, OID, and invoice ETTN. Status changes to "Onaylandı" (Approved).

---

## 💡 Developer Notes / Geliştirici Notları

*Known GİB Portal quirks and workarounds — must-read before modifying code:*

### Encoding / Karakter Bozulmaları
> GİB breaks on UTF-8 Turkish characters. Always use `json.dumps(..., ensure_ascii=True)` in HTTP payloads. GİB correctly handles `\uXXXX` escape sequences.

### SMS NullPointerException
> **Always** call `EARSIV_PORTAL_TELEFONNO_SORGULA` before `EARSIV_PORTAL_SMSSIFRE_GONDER`. Otherwise GİB throws a Java `NullPointerException`. This step is already integrated into `gib_earsiv_sms_gonder`.

### ETTN Error
> When creating invoices, pass `faturaUuid` as an empty string `""`. GİB rejects valid UUIDs with "Ettn sınırına uymuyor".

### Invoice Deletion
> Use `belgeNumarasi` (NOT `belgeNo`) as the key in the delete list. `pageName` must be `RG_TASLAKLAR`. Include full order details for cancellation.

---

## 📁 Project Structure / Proje Yapısı

```
arsiv-fatura/
├── pyproject.toml              # Project config (hatchling + uv)
├── src/gib_earsiv_mcp/
│   ├── server.py               # FastMCP server + middleware (rate-limit, retry, error handling)
│   ├── tools.py                # All 15 MCP tool definitions
│   ├── core/                   # Business logic layer
│   │   ├── client.py           # GİB HTTP client (login, dispatch, download)
│   │   ├── mock_client.py      # Mock client for offline testing
│   │   ├── session.py          # Session & token management
│   │   ├── config.py           # Environment settings (pydantic-settings)
│   │   └── exceptions.py       # Custom exception hierarchy
│   └── models/                 # Data models
│       └── input.py            # Pydantic input models for all tools
└── tests/                      # Tests (pytest + pytest-asyncio)
    ├── conftest.py             # Sets GIB_ENV=mock for all tests
    └── test_phase*.py          # Phase-based test files
```

---

## 🔗 Developer Documentation / Geliştirici Dokümantasyonu

*For detailed code map, anti-patterns, conventions, and development guide, see:*

→ **[`AGENTS.md`](AGENTS.md)** ←
