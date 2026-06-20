# PROJECT KNOWLEDGE BASE

**Generated:** 2026-06-20
**Commit:** 9805eb6
**Branch:** master

## OVERVIEW
GİB e-Arşiv MCP Server — FastMCP server exposing Turkish Revenue Administration (GİB) e-Arşiv Portal as MCP tools. Invoices, SMS signing, PDF download. Python 3.14, httpx, Pydantic, weasyprint.

## STRUCTURE
```
arsiv-fatura/
├── main.py                          # STUB — delete this. Real entry: gib-mcp CLI
├── pyproject.toml                   # hatchling build, uv deps, entry: gib-mcp
├── .env.example                     # Env template (GIB_USERNAME, GIB_PASSWORD, GIB_ENV)
├── src/gib_earsiv_mcp/
│   ├── server.py                    # FastMCP app + middleware (error, rate-limit, retry)
│   ├── tools.py                     # ALL 14 MCP tools (434 lines — split when >20 tools)
│   ├── core/
│   │   ├── client.py                # GibClient: login(), dispatch(), download()
│   │   ├── mock_client.py           # MockGibClient for GIB_ENV=mock testing
│   │   ├── session.py               # AppState dataclass + app_lifespan (token store)
│   │   ├── config.py                # Settings (pydantic-settings, .env, GIB_ENV enum)
│   │   └── exceptions.py            # GibMcpError → AuthError, ApiError, SessionExpired
│   └── models/
│       ├── input.py                 # Pydantic models for all tool inputs
│       └── api.py                   # EMPTY — intended for response models
└── tests/
    ├── conftest.py                  # Sets GIB_ENV=mock at module level (fragile)
    ├── test_phase2.py               # User info, menu, draft listing
    ├── test_phase3.py               # Invoice create, display, SMS flow
    ├── test_phase4.py               # Delete, taxpayer lookup, incoming invoices
    └── test_imza_bekleyen.py        # Pending-signature filter logic
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add new MCP tool | `tools.py` → define function + `@mcp.tool()` | Then add Pydantic model to `models/input.py` |
| Change GİB API call | `core/client.py` → `dispatch()` | payload = cmd + jp_dict (JSON, ensure_ascii=True) |
| Environment switch | `core/config.py` → `GibEnvironment` | mock \| test \| production |
| Session/token logic | `core/session.py` → `AppState.get_valid_token()` | In-memory dict, no TTL |
| Mock responses for tests | `core/mock_client.py` | Add elif block for new cmd |
| Middleware tuning | `server.py` lines 14-31 | Rate limit: 10 req/s, Retry: 3x, backoff 2x |
| PDF generation | `tools.py` line 409 | `weasyprint.HTML(string=html).write_pdf()` |

## CODE MAP
| Symbol | Type | File | Role |
|--------|------|------|------|
| `mcp` | FastMCP | `server.py:9` | MCP server instance, all tools registered on it |
| `GibClient` | class | `core/client.py:8` | Real GİB HTTP dispatcher |
| `MockGibClient` | class | `core/mock_client.py:4` | Offline test client |
| `AppState` | dataclass | `core/session.py:10` | Per-server-lifespan state: http_client, token_store |
| `app_lifespan` | async ctx mgr | `core/session.py:27` | FastMCP lifespan factory |
| `Settings` | pydantic | `core/config.py:11` | Reads .env: GIB_ENV, GIB_USERNAME, GIB_PASSWORD |
| `GibEnvironment` | enum | `core/config.py:6` | mock, test, production |
| `FaturaOlusturInput` | pydantic | `models/input.py:67` | Largest input model (30+ fields) |
| `_build_invoice_jp()` | function | `tools.py:139` | Converts FaturaOlusturInput → GIB jp_dict |
| `GibMcpError` | exception | `core/exceptions.py:1` | Base exception |
| `SessionExpiredError` | exception | `core/exceptions.py:13` | Triggers token clear + re-login |

## CONVENTIONS
- **Tool naming**: `gib_earsiv_{isim}` — snake_case, Turkish names (e.g. `gib_earsiv_fatura_olustur`)
- **MCP annotations**: Every tool gets `readOnlyHint` + `destructiveHint` annotations
- **Token per client_id**: `AppState.token_store` is `dict[client_id, token]` — no TTL, cleared on `SessionExpiredError`
- **Environment pattern**: `GIB_ENV` enum selects mock/test/production — `conftest.py` forces `mock` for all tests
- **GİB encoding**: `json.dumps(jp_dict, ensure_ascii=True)` — Turkish chars as `\uXXXX` escapes (GİB breaks on UTF-8)
- **Config**: `GIB_ENV` env var or `.env` file → `Settings` via pydantic-settings
- **Test style**: `FastMCP Client(mcp)` in-memory, `@pytest.mark.asyncio`, mock client responses
- **Module init**: All `__init__.py` are empty — no public API exports defined

## ANTI-PATTERNS (THIS PROJECT)
- **NEVER** call `EARSIV_PORTAL_SMSSIFRE_GONDER` without first calling `EARSIV_PORTAL_TELEFONNO_SORGULA` (GİB NullPointerException)
- **NEVER** pass a valid UUID to `faturaUuid` — must be empty string `""` (GİB "Ettn sınırına uymuyor" error)
- **NEVER** use `belgeNo` as key when deleting — must be `belgeNumarasi`
- **MUST** use `page_name="RG_TASLAKLAR"` for delete operations
- **DO NOT** send UTF-8 Turkish characters to GİB — always `ensure_ascii=True`
- **DO NOT** add tools without adding corresponding mock responses in `mock_client.py`

## UNIQUE STYLES
- **Late import pattern**: `server.py` creates `mcp`, then `from . import tools` at bottom. `tools.py` imports `from .server import mcp`. Order-dependent — `mcp` must exist before `tools.py` is imported.
- **Inline weasyprint import**: `from weasyprint import HTML` inside `gib_earsiv_fatura_pdf_indir()` — not top-level (hides missing dep until runtime)
- **Phase-numbered tests**: `test_phase2.py`, `test_phase3.py`, `test_phase4.py` — chronological naming, not feature-named
- **Empty stub files**: `main.py` (dead code), `models/api.py` (empty), `tests/test_client.py` (empty) — cleanup candidates
- **Module-level env mutation**: `tests/conftest.py` sets `os.environ["GIB_ENV"] = "mock"` at import time, not via fixture

## COMMANDS
```bash
uv sync                          # Install all deps (prod + dev)
uv run gib-mcp                   # Start MCP server (proper entry)
uv run python main.py            # ⚠️ STUB — just prints "Hello"
uv run pytest                    # Run all tests (auto-sets mock env)
uv run pytest -k "imza"          # Run specific test by keyword
uv build                         # Build wheel (hatchling)
```

## NOTES
- **`main.py` is dead code** — real entry is `gib_earsiv_mcp.server:mcp.run` via `gib-mcp` console script
- **No CI/CD, no linter, no type checker** — project is young, add `.github/workflows/ci.yml` + `[tool.ruff]`
- **.env committed?** `.env` is in `.gitignore` but verify it's not tracked (`git ls-files .env`) — contains live credentials
- **weasyprint needs system libs**: Pango, Cairo, GDK-Pixbuf, libffi — Dockerfile highly recommended
- **Python 3.14 only** — `requires-python = ">=3.14"` may limit deployment targets
- **`fatura_GIB2026000000011.pdf`** is a sample invoice PDF committed to repo — potential binary bloat and data leak
