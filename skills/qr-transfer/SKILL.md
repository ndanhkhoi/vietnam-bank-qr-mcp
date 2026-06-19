---
name: qr-transfer
description: "Create Vietnamese bank transfer QR codes and payment card PNGs. Use whenever the user asks for VietQR, NAPAS QR, bank transfer QR, payment QR, account-number payment cards, or QR for invoices/orders. Not for WiFi, URL, vCard, or non-bank QR codes."
version: 15.3.0
author: vietnam-bank-qr-mcp contributors
license: MIT
metadata:
  hermes:
    tags: [qr, napas, bank-transfer, payment, playwright, qr-code-styling]
    category: productivity
    related_skills: [clean-code-principles]
---

# QR Transfer Generator

Generate Vietnamese bank transfer QR codes using NAPAS QR IBFTTA (EMVCo). The output is a retina PNG payment card with a styled QR code, bank logo, and transfer details.

## Default Accounts

Use these only when the user asks for a QR but does not provide recipient account details.

| Bank | BIN | Code | Account number | Account holder |
|---|---|---|---|---|
| TPBank | `970423` | `TPB` | `0123456789` | `NGUYEN VAN A` |
| CAKE by VPBank | `546034` | `CAKE` | `0123456789` | `NGUYEN VAN A` |

## Scope And Safety

- Handle only Vietnamese bank transfer QR/card generation using this repo's local data and renderer.
- Do not use this skill for WiFi, URL, vCard, or other non-bank QR codes.
- Do not invent account numbers, holder names, bank BINs, or payment amounts. If missing and no default is documented here, ask.
- Do not refresh VietQR bank data/logos unless the user asks; it performs network writes to `banks.json` and `assets/bank_logos/`.
- Do not expose private account details except when needed to satisfy the user's QR/card request.

## Workflow

1. Resolve the bank: use `search_banks(query)[0]` when the user gives a bank name or short code.
2. Generate QR data: call `generate_qr_data(bank_code=bank.bin, ...)`. The QR payload must use the 6-digit BIN, not `bank.code`.
3. Render the card: call `render_card(data_dict, output_path=...)`. The renderer data must use `data_dict["bank_code"] = bank.code` so the logo resolves.
4. Return the generated PNG path, or attach it as media when the host supports media outputs.

## Inputs

| Parameter | Required | Notes |
|---|---:|---|
| `bank_code` | Yes | Accept a 6-digit BIN such as `970423`, or resolve a name/code such as `TPBank` via `search_banks()` first. |
| `account_no` | Yes | Recipient account number. |
| `account_holder` | No | Account holder name. Sanitized for QR/card use. |
| `amount` | No | VND amount. Omit for user-entered amount. |
| `payment_content` | No | Transfer description. Sanitize before QR generation; only `[a-zA-Z0-9 ]` remains. |
| `order_id` | No | Bill/order reference. |

## MCP Tools

Server entrypoint: `mcp-server/server.py`.

| Tool | Use |
|---|---|
| `generate_payment_card(bank_code, account_no, account_holder?, amount?, order_id?, payment_content?)` | Generate QR data plus PNG card. `bank_code` is the 6-digit BIN. |
| `get_qr_data(bank_code, account_no, amount?, order_id?, payment_content?)` | Generate QR data string only, without an image. `bank_code` is the 6-digit BIN. |
| `search_bank(query)` | Search banks by name, short code, short name, or BIN. Returns JSON. |
| `get_bank_list()` | List supported banks. |
| `update_bank_list_tool()` | Refresh banks and logos from VietQR; network mutation. |

MCP tool names are not the same as Python module function names. For direct Python scripts, use the module API below.

## Python API

Use from `mcp-server/`.

```python
from banks import search_banks
from qr_generator import generate_qr_data, sanitize_content
from renderer import render_card

bank = search_banks("TPBank")[0]

qr_data = generate_qr_data(
    bank_code=bank.bin,  # 6-digit BIN; do not use bank.code here.
    account_no="0123456789",
    amount=10000000,
    payment_content=sanitize_content("DONATE DEMO"),
)

data = {
    "qr_data": qr_data,
    "bank_code": bank.code,  # short code for logo lookup.
    "bank_name": bank.name,
    "account_name": "NGUYEN VAN A",
    "account_no": "0123456789",
    "payment_content": "DONATE DEMO",
    "amount": "10.000.000 VND",  # preformatted string for the card.
}

path = render_card(data, output_path="/tmp/qr_card.png")
```

Discover callable signatures instead of guessing:

```bash
cd mcp-server && python3 - <<'PY'
import inspect
from banks import search_banks
from qr_generator import generate_qr_data
from renderer import render_card
print(inspect.signature(search_banks))
print(inspect.signature(generate_qr_data))
print(inspect.signature(render_card))
PY
```

## API Pitfalls

- `generate_qr_data(bank_code=...)` is misnamed: pass `bank.bin`, not `bank.code`.
- `render_card(data)` returns a PNG path, not base64.
- `qr_generator.generate_payment_card()` returns base64 and wraps `render_card()`.
- `search_banks()` is plural and returns a list; MCP `search_bank()` is singular and returns JSON.
- Card `amount` is a preformatted string such as `"10.000.000 VND"`, not a number.

## Rendering Pipeline

```text
transfer data
-> generate raw EMVCo QR string with CRC16
-> inject raw qr_data into the HTML template
-> template loads qr-code-styling.js
-> browser renders styled QR canvas
-> Playwright subprocess screenshots body at 2x scale
-> PNG path or base64 is returned
```

Rendering constraints:

- Keep Playwright in a subprocess; sync Playwright inside async MCP can deadlock.
- Chromium binary resolves from `CHROMIUM_PATH` env var; falls back to Playwright's bundled Chromium when unset. Set `CHROMIUM_PATH=/path/to/chrome` only when the bundled binary is unavailable.
- Use `page.add_init_script()` before `page.goto()` to inject `window.__CARD_DATA__`.
- Use `page.goto("file://...")`, not `set_content()`, so relative fonts, logos, and `node_modules` assets load.
- Screenshot `body`, not `.card` or `.mac-window`, to preserve the 16px padding and shadow.
- Wait for `document.fonts.ready`, images, and `#qr-canvas canvas` before taking the screenshot.
- Keep `.info-row[hidden], .amount-row[hidden] { display: none !important; }`; flex rows override browser hidden defaults.

## QR Spec Constraints

- NAPAS QR uses root tag `38`, not tag `26`.
- Tag `38` nests AID `A000000727`, payment network fields `00 = BIN` and `01 = account number`, and service `QRIBFTTA`.
- Country tag `58` must be `VN`; currency tag `53` is `704`.
- Payment purpose/content belongs under additional data tag `62`, subtag `08`.
- CRC is CRC16-CCITT with polynomial `0x1021`, initial `0xFFFF`.
- Amount tag `54` only emits when `amount > 0`. `0`, negatives, and `None` all omit the tag.
- See `references/qr-algorithm.md` for TLV details and the spec CRC example.

## Card Design Notes

- The current template is `mcp-server/templates/payment-card.html`.
- The current visual style is a macOS window card with local Be Vietnam Pro fonts and browser-side `qr-code-styling`.
- Treat `references/template-design.md` and `references/qr-styling.md` as explanatory references, but verify numeric styling values against the live HTML template before changing code.
- Keep real bank logos via `<img>` and QR center image; do not fake logos with CSS/text.
- Keep account number navy and amount green so amount remains the only strong visual anchor.
- Do not uppercase transfer content for display.

## Response Format

```text
Bank: [bank name]
Account: [account_no]
Amount: [amount] VND
Content: [payment_content]
PNG: [path or media attachment]
```

## Verification

- Confirm the QR payload uses a 6-digit BIN.
- Confirm QR data starts with `00020101021238`.
- Confirm tag `38` contains nested AID, BIN/account, and service fields.
- Confirm tag `62` uses subtag `08` for payment content.
- Confirm tag `58 02 VN` is present.
- Confirm generated QR data ends with `6304` plus a 4-character CRC.
- Confirm the PNG renders a styled QR canvas with the bank logo.
- Confirm the rendered card uses the full bank name, not only `short_name`.
- Confirm optional rows are hidden when empty.
