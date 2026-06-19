---
name: qr-transfer
description: "Use when creating bank transfer QR codes — generate Napas/EMVCo compliant QR with payment card PNG. Input: bank code/BIN, account number, amount, description."
version: 15.2.0
author: vietnam-bank-qr-mcp contributors
license: MIT
metadata:
  hermes:
    tags: [qr, napas, bank-transfer, payment, playwright, qr-code-styling]
    category: productivity
    related_skills: [clean-code-principles]
---

# QR Transfer Generator

Tạo QR code chuyển khoản ngân hàng theo chuẩn NAPAS QR IBFTTA (EMVCo). Output: PNG card retina với **styled QR** (rounded dots, gradient, bank logo center) + thông tin transfer + bank logo.

## Anh Khôi's Bank Accounts

Dùng khi user yêu cầu QR mà không cung cấp STK/tên:

### TPBank (mặc định)

| Field | Value |
|---|---|
| Bank | TPBank (BIN `970423`, code `TPB`) |
| Số tài khoản | `0123456789` |
| Tên chủ TK | `NGUYEN VAN A` |

### CAKE by VPBank

| Field | Value |
|---|---|
| Bank | CAKE by VPBank (BIN `546034`, code `CAKE`) |
| Số tài khoản | `0123456789` |
| Tên chủ TK | `NGUYEN VAN A` |

## When to Use

- User yêu cầu tạo QR chuyển khoản
- Gửi QR cho khách thanh toán
- Tạo QR cho đơn hàng/hóa đơn

**Không dùng khi:** QR cho WiFi, URL, vCard, QR không phải ngân hàng.

## Workflow

1. **Tìm bank** (nếu user nhập tên) → `search_banks(query)[0]` — trả về `Bank(name, code, bin)`
2. **Generate QR data** → `generate_qr_data(bank_code=bank.bin, ...)` — **BẮT BUỘC dùng `.bin` (6 số), KHÔNG dùng `.code` (string như "TPB")**. QR không hợp lệ nếu truyền `.code`.
3. **Render card** → `render_card(data_dict, output_path=...)` — `data_dict['bank_code']` dùng `.code` (để tìm logo)
4. **Gửi ảnh** → `MEDIA:/tmp/qr_card.png`

## Input

### Required

| Param | Mô tả | Ví dụ |
|-------|-------|-------|
| `bank_code` | BIN 6 số hoặc tên bank | `970423`, `TPBank` |
| `account_no` | Số tài khoản | `0123456789` |

### Optional

| Param | Default | Mô tả |
|-------|---------|-------|
| `account_holder` | `""` | Tên chủ TK |
| `amount` | `None` | Số tiền VND (omit → "Tuỳ chọn") |
| `payment_content` | `None` | Nội dung CK (auto-sanitize: chỉ `a-zA-Z0-9 `) |
| `order_id` | `None` | Mã đơn hàng |

## MCP Tools

**Server:** `~/projects/napas-qr-mcp-python/server.py`

| Tool / Function | Dùng khi |
|------|----------|
| `generate_qr_data(bank_code, account_no, amount?, order_id?, payment_content?)` | Gen QR data string (EMVCo TLV + CRC16). **`bank_code` = BIN 6 số, KHÔNG phải `bank.code`** |
| `generate_payment_card(qr_data, bank_name, bank_bin, bank_code, account_no, ...)` | Card PNG — wraps `render_card` |
| `render_card(data_dict, output_path?)` | Renderer trực tiếp — trả path PNG. `data_dict` gồm: `qr_data, bank_code, bank_name, account_name, account_no, payment_content, amount` |
| `sanitize_content(text)` | Normalize ASCII: bỏ dấu VN, chỉ giữ `a-zA-Z0-9 ` |
| `search_banks(query)` → `list[Bank]` | Tìm bank theo tên/code/BIN. Trả list, lấy `[0]` |
| `load_banks()` → `list[Bank]` | Load 65 banks |
| `get_bank_by_bin(bin)` → `Bank | None` | Lookup theo BIN |
| `update_bank_list()` → `list[Bank]` | Refresh banks + download logos |

**Bank object:** `Bank(name, code, bin)` — `name` đầy đủ, `code` string ngắn (`TPB`, `CAKE`), `bin` 6 số (`970423`)

## Python API (dùng trực tiếp không qua MCP)

**Quan trọng:** Module-level API khác MCP tools. Dùng khi script Python trực tiếp:

```python
from banks import search_banks          # ← số nhiều (KHÔNG phải search_bank)
from qr_generator import generate_qr_data, sanitize_content
from renderer import render_card

bank = search_banks('TPBank')[0]
# bank.code (string code), bank.bin (6 số), bank.name, bank.short_name

qr_data = generate_qr_data(
    bank_code=bank.code,            # ← param tên "bank_code" (KHÔNG phải "bin_code")
    account_no='0123456789',
    amount=10000000,
    payment_content=sanitize_content('DONATE DEMO'),
)

data = {
    'qr_data': qr_data,
    'bank_code': bank.code,
    'bank_name': bank.name,
    'account_name': 'NGUYEN VAN A',
    'account_no': '0123456789',
    'payment_content': 'DONATE DEMO',
    'amount': '10.000.000 VNĐ',     # ← string đã format, KHÔNG phải số
}
path = render_card(data, output_path='/tmp/qr_card.png')
```

**Param pitfall:**
- `generate_qr_data`: param là `bank_code` (không phải `bin_code`)
- `generate_payment_card` (qr_generator.py): nhận `qr_data` + `bank_name` + `bank_bin` + `bank_code` (4 trường riêng biệt, không gộp)
- `render_card` (renderer.py): nhận dict `data` + `output_path`, trả về **path** (không trả base64)
- `search_banks`: số nhiều, trả list (dùng `[0]`)
- `amount` trong dict `data` phải là **string đã format** (vd `'10.000.000 VNĐ'`), không phải số

**Signature discovery (tránh mò):** Module-level Python API khác MCP tool API. Trước khi gọi, đọc signature thực tế:
```bash
cd ~/projects/napas-qr-mcp-python && grep -n "^def \|^class " banks.py qr_generator.py renderer.py
```
Tên MCP tool (server.py @mcp.tool decorator) ≠ tên module function. Ví dụ MCP `search_bank` (singular) vs module `search_banks` (plural).

## Pipeline

```
data → generate QR data string (EMVCo TLV + CRC16)
     → pass raw qr_data to template (NOT pre-rendered PNG)
     → HTML template loads qr-code-styling.js
     → JS renders styled QR canvas (rounded dots, gradient, logo center)
     → Playwright render (subprocess, 900x1200, 2x retina)
     → screenshot `body` element → base64 PNG
```

**Architecture (v15):** QR rendering by browser-side `qr-code-styling` JS. Python chỉ gen QR data string (EMVCo TLV + CRC). Renderer pass raw `qr_data` → template JS self-render styled canvas. Không còn Python `qrcode` dependency cho card.

**Screenshot target:** Chụp `body`, KHÔNG chụp `.card`. Body padding 16px → card nổi trên background, radius + shadow visible.

**LƯU Ý:** Playwright sync API KHÔNG chạy trong async MCP. BẮT BUỘC subprocess.

## QR Algorithm

Spec NAPAS QR v1.5.2 — tag **38** (không 26), nested payment network (38→01→00+01), tag 08 cho purpose, country code 58 bắt buộc.

Chi tiết + verification: `references/qr-algorithm.md`

## Card Design

**macOS window chrome** + table layout bên trong. QR premium subtle (qr-code-styling). Be Vietnam Pro local .woff2.

Chi tiết + references:
- Design specs: `references/template-design.md`
- QR styling config: `references/qr-styling.md`
- Template hiện tại: `templates/payment-card.html` (macOS window variant)

## Renderer Architecture (v15)

**Data flow:** Renderer passes `window.__CARD_DATA__` via `page.add_init_script()` BEFORE `page.goto()`. Template's own `<script>` reads `window.__CARD_DATA__` and self-renders.

```
renderer.py                          template HTML
─────────                           ─────────────
add_init_script(                    <script src="qr-code-styling.js">
  window.__CARD_DATA__ = {          <script>
    qr_data: "...",      ──┐          const params = window.__CARD_DATA__;
    bank_logo_base64,      │          // bank logo, info inject
    bank_name,             │          // styled QR render
    account_name,          │          new QRCodeStyling({...}).append(...)
    ...                    │        </script>
  };                       ──┘
)
```

**Key benefits:**
- Renderer không cần biết element IDs (template tự xử lý)
- Dễ swap template (plain card ↔ macOS window ↔ custom)
- 1 inject point, không lặp logic inject cho mỗi template variant

## Response Format

```
🏦 [Tên ngân hàng]
💰 STK: [account_no]
💵 Số tiền: [amount] VNĐ
📝 Nội dung: [payment_content]

[Ảnh PNG → MEDIA:]
```

## File Structure

```
~/projects/napas-qr-mcp-python/
├── server.py              # MCP server (5 tools)
├── qr_generator.py        # QR data generation (CRC16 + TLV)
├── banks.py               # Bank data + search + logo download
├── renderer.py            # Playwright subprocess renderer
├── banks.json             # 65 banks
├── package.json           # npm deps (qr-code-styling)
├── node_modules/          # qr-code-styling
├── templates/
│   └── payment-card.html  # macOS window template (current)
└── assets/
    ├── bank_logos/        # 63 logo PNGs
    └── fonts/             # Be Vietnam Pro .woff2 (4 weights)
```

## Common Pitfalls

1. **`bank_code` param lừa người** → `generate_qr_data(bank_code=...)` tên param là `bank_code` nhưng thực chất cần **BIN 6 số** (`bank.bin` = `970423`), KHÔNG PHẢI `bank.code` (string như `"TPB"`). Truyền `.code` → QR data có tag `00` = `TPB` (3 ký tự) → app ngân hàng không parse → **QR không hợp lệ**. Symptom: QR render thành công nhưng scan fail. **Luôn dùng `bank.bin` cho QR data, `bank.code` chỉ cho renderer tìm logo.** Lỗi thực tế gặp session 2026-06-19
2. **Bank code sai format** → phải `search_banks(query)` trước nếu user nhập tên. `search_banks` trả list, lấy `[0]`
3. **Playwright trong async MCP** → BẮT BUỘC subprocess. Sync API sẽ deadlock
4. **Font local không load với `set_content`** → dùng `page.goto("file://" + template_path)`
5. **Screenshot trước khi font/canvas load** → wait `document.fonts.ready` + `wait_for_function("canvas exists")` + `wait_for_timeout(300)`
6. **Weight lẻ (650/680/720/760)** → chỉ dùng 400/500/600/700
7. **Bank logo fake CSS/text** → PHẢI dùng `<img>` thật hoặc canvas image
8. **Account number blue cạnh tranh amount** → navy (#142b4f), chỉ amount green nổi
9. **Transfer content uppercase** → KHÔNG. Hiển thị nguyên dạng
10. **Screenshot `.card` cắt padding/shadow** → Screenshot `body` (có padding). Card `width: 100%`
11. **Body padding quá sâu** → 16px là sweet spot. 40px quá sâu, 8px quá ít
12. **Card width fix + body padding = lệch** → Card `width: 100%` để tự fill
13. **Element ID mismatch sau redesign** → Giải pháp v15: `add_init_script` + `window.__CARD_DATA__`, template tự đọc → renderer không cần biết IDs
14. **Bank name** → dùng `bank.name` (đầy đủ), KHÔNG `bank.short_name`
15. **Subprocess timeout leak** → `except TimeoutExpired: pkill`, `finally: unlink`
16. **Card-in-card anti-pattern** → macOS window variant: content nằm trực tiếp trên `.mac-content`, KHÔNG wrap thêm `.card` div bên trong
17. **QR canvas render async** → `qrCode.append()` không đồng bộ. Must `wait_for_function("document.querySelector('#qr-canvas canvas') !== null")` trước screenshot
18. **qr-code-styling script load** → `<script src="../node_modules/qr-code-styling/lib/qr-code-styling.js">` — PHẢI dùng relative path từ template, load trước render script
19. **add_init_script timing** → inject `window.__CARD_DATA__` TRƯỚC `page.goto()`. Nếu inject sau goto → template script đã chạy, `window.__CARD_DATA__` undefined → QR render fail
20. **HTML `[hidden]` không hoạt động với flexbox** → `.info-row { display: flex }` override browser default `[hidden] { display: none }`. Phải thêm CSS: `.info-row[hidden] { display: none !important; }`. Symptom: row vẫn visible dù JS set `element.hidden = true`
21. **Optional info rows phải ẩn khi rỗng** → `account_holder` và `payment_content` là optional. Template JS check giá trị rỗng → set `row.hidden = true`. Chỉ `account_no` + `amount` (nếu có) luôn hiển thị
22. **Info row border glitch khi ẩn row** → KHÔNG dùng `.info-row + .info-row { border-top }` hoặc `.info-row:last-child { border-bottom: none }`. Khi row giữa bị ẩn (`display: none !important`), sibling selector nhảy position → orphan/ghost line xuất hiện. **Giải pháp:** mỗi `.info-row` tự có `border-bottom`, không except last-child. Row ẩn → tự mất border
23. **Library docs drift** → Khi tham chiếu giá trị từ `references/*.md` (vd QR width/height/margin), verify với code thực tế trong `templates/payment-card.html` trước. Ref docs dễ lag sau khi sửa template. Session 2026-06-19: qr-styling.md ghi `width: 316, margin: 8` nhưng template thực tế `388, 10`

## Verification

- [ ] BIN code đúng 6 số
- [ ] QR data bắt đầu `00020101021238` (payload + dynamic + tag 38)
- [ ] Tag 38 chứa nested: `00` (AID) + `01` (00:BIN + 01:account) + `02` (service)
- [ ] Tag 62 dùng `08` cho purpose
- [ ] Tag `58 02 VN` có mặt
- [ ] CRC16 match spec example (section 6.3.3 → `2E2E`)
- [ ] QR canvas rendered (rounded dots, gradient, logo center)
- [ ] PNG retina 2x, QR quét được bởi app banking
- [ ] Be Vietnam Pro font loaded
- [ ] `page.goto("file://...")` + `add_init_script` trước goto
- [ ] document.fonts.ready + QR canvas wait trước screenshot
- [ ] Payment content chỉ chứa `a-zA-Z0-9 ` + khoảng trắng
- [ ] Bank logo hiển thị (img + QR center)
- [ ] Bank name đầy đủ (`bank.name`)
- [ ] Transfer content nguyên dạng (không uppercase)
- [ ] Amount là green anchor duy nhất (account number navy)
- [ ] Screenshot `body` element — margin + radius + shadow visible
- [ ] Body padding 16px
- [ ] Card `width: 100%`
- [ ] macOS variant: không card-in-card
- [ ] Optional rows (account_holder, payment_content) ẩn khi rỗng — `.info-row[hidden] { display: none !important; }`
- [ ] Info rows dùng `border-bottom` per-row (không sibling/last-child selector) — tránh orphan line khi ẩn row
