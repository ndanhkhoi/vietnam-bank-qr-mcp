# Repository Instructions

## Project Shape

- This repo is a Python MCP server, not an Astro/Node app. The implementation lives in `mcp-server/`; root has no package scripts.
- `mcp-server/server.py` is the stdio MCP entrypoint using `FastMCP("napas-qr")`.
- `qr_generator.py` builds NAPAS/EMVCo TLV payloads and CRC16; `renderer.py` renders the PNG card via a Playwright subprocess; `banks.py` loads/searches `banks.json` and refreshes VietQR data/logos.
- `skills/qr-transfer/SKILL.md` contains detailed user-facing workflow and historical pitfalls; verify any numeric styling claims against `mcp-server/templates/payment-card.html` because reference docs may drift.

## Setup And Commands

- Work from `mcp-server/` for runtime commands.
- Python deps are not pinned in a requirements file: install `mcp` and `playwright`, then run `playwright install chromium`.
- Node is only needed for `qr-code-styling`; install with `npm install` in `mcp-server/` to create `node_modules/qr-code-styling/lib/qr-code-styling.js` for the HTML template.
- Start the MCP server with `python3 server.py` from `mcp-server/`; it uses stdio transport.
- There is no configured lint/test runner or CI. Use focused Python smoke checks for changed behavior.

## Runtime Gotchas

- `generate_qr_data(bank_bin=...)` expects the bank BIN (`bank.bin`, 6 digits such as `970423`).
- Renderer card data uses `bank_code` (the short code such as `TPB`) so logos resolve from `assets/bank_logos/{code}.png`.
- MCP tool names differ from module function names: server exposes `search_bank`, `get_qr_data`, `generate_payment_card`, `get_bank_list`, `update_bank_list_tool`; module API has `search_banks`, `generate_qr_data`, and `render_card`.
- `sanitize_content()` strips Vietnamese diacritics and keeps only `[a-zA-Z0-9 ]`; sanitize payment content before QR generation.
- `renderer.py` resolves the Chromium binary from the `CHROMIUM_PATH` env var (read at call time) and falls back to Playwright's bundled Chromium when unset. Set `CHROMIUM_PATH=/path/to/chrome` if the bundled binary is unavailable.
- Playwright rendering is intentionally done in a subprocess (spawned via `sys.executable` so it inherits the same Python interpreter) because sync Playwright inside async MCP can deadlock.
- The subprocess receives its inputs via a JSON config file (not string interpolation), so values flow safely through `json.load`.
- The HTML template loads local fonts and `../node_modules/qr-code-styling/...`; keep `page.goto(file://...)`, not `set_content()`, or relative assets/fonts break.
- `generate_qr_data(amount=...)` emits tag `54` only when `amount > 0`. `0`, negatives, and `None` all omit the tag. Do not "fix" this with a truthiness check.

## Rendering Constraints

- `renderer.py` injects `window.__CARD_DATA__` with `page.add_init_script()` before `page.goto()`; injecting after navigation races the template script.
- The screenshot target is `body`, not `.card` or `.mac-window`, to preserve the 16px padding and shadow.
- The template waits for local fonts, images, and `#qr-canvas canvas`; keep these waits when editing rendering.
- Optional rows are hidden in template JS; keep `.info-row[hidden], .amount-row[hidden] { display: none !important; }` because flex display overrides browser hidden behavior.
- Avoid sibling/last-child border tricks on `.info-row`; hidden middle rows can leave orphan lines. Each row currently owns its bottom border.

## MCP Tool Contract

- `generate_payment_card` returns `list[str | Image]` — a JSON summary string plus an `Image` content block (raw PNG bytes). Declared with `structured_output=False` because pydantic cannot schema `Image`.
- `get_qr_data`, `search_bank`, `get_bank_list`, `update_bank_list_tool` return JSON-serialized strings.
- Bank not found raises `ToolError` via `_require_bank()` → MCP sets `isError: true` in the response. Do not return error JSON strings.
- `update_bank_list_tool` catches exceptions from the VietQR API and re-raises as `ToolError` so network failures don't crash the MCP session.

## QR Spec Constraints

- NAPAS QR uses root tag `38`, not tag `26`.
- Tag `38` nests AID `A000000727`, payment network fields `00` = BIN and `01` = account number, and service `QRIBFTTA`.
- Country tag `58` must be `VN`; currency tag `53` is `704`; purpose/content belongs under additional data tag `62` subtag `08`.
- `generate_qr_data(amount=...)` emits tag `54` only when `amount > 0`. `0`, negatives, and `None` all omit the tag. Do not "fix" this with a truthiness check.
- CRC is CRC16-CCITT with polynomial `0x1021`, initial `0xFFFF`, implemented in `calculate_crc16()`.

## Verification Shortcuts

- Inspect callable signatures with `python3 - <<'PY'` snippets or by reading the small modules; do not rely on stale examples in prose.
- QR data smoke check from `mcp-server/`: generate with a known BIN via `generate_qr_data("970423", "0123456789", 100000, payment_content=sanitize_content("TEST"))` and verify it starts with `00020101021238` and ends with tag `6304` plus a 4-char CRC.
- Renderer smoke check from `mcp-server/`: search a bank, generate QR with `bank.bin`, render card data with `bank.code`, and confirm a PNG path is produced.
- Refreshing banks with `update_bank_list()` hits `https://api.vietqr.io/v2/banks` and downloads logos; avoid running it unless network mutation is intended.
