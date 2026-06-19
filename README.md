# Vietnam Bank QR MCP

Tạo QR chuyển khoản ngân hàng Việt Nam theo chuẩn **NAPAS QR IBFTTA / EMVCo** và render thành PNG payment card bằng Playwright.

Repo này có hai cách dùng:

- Chạy như **MCP server** qua stdio để agent/client gọi tool.
- Dùng trực tiếp như **Python module** trong [`mcp-server/`](mcp-server/).

## Features

- Sinh QR payload chuẩn NAPAS/EMVCo, gồm TLV tag `38`, currency `704`, country `VN`, CRC16-CCITT.
- Render PNG card bằng HTML template, local font Be Vietnam Pro, bank logo, QR styled bằng `qr-code-styling`.
- Tìm ngân hàng từ [`banks.json`](mcp-server/banks.json) theo BIN, code, short name hoặc tên đầy đủ.
- Có skill agent ở [`skills/qr-transfer/`](skills/qr-transfer/) để hướng dẫn workflow và tránh các lỗi thường gặp.

## Project Structure

```text
vietnam-bank-qr-mcp/
├── mcp-server/
│   ├── server.py                    # MCP stdio server: FastMCP("napas-qr")
│   ├── qr_generator.py              # EMVCo/NAPAS TLV payload + CRC16
│   ├── renderer.py                  # Playwright subprocess renderer
│   ├── banks.py                     # Đọc/tìm/refresh bank data và logo
│   ├── banks.json                   # Dữ liệu ngân hàng local
│   ├── package.json                 # Dependency Node: qr-code-styling
│   ├── templates/payment-card.html  # UI card + render QR trong browser
│   └── assets/                      # Logo ngân hàng và font local
└── skills/qr-transfer/              # Tài liệu skill cho agent
```

## Requirements

- Python 3.11+
- Node.js 18.18+ cho `qr-code-styling`
- Python packages: `mcp`, `playwright`
- Playwright Chromium (cài qua `playwright install chromium`) hoặc Chromium binary tương thích

Nếu binary bundled của Playwright không khả dụng (ví dụ sandbox/CI), đặt env var trỏ tới Chromium thật:

```bash
export CHROMIUM_PATH=/path/to/chrome
```

Khi không set, [`renderer.py`](mcp-server/renderer.py) sẽ fallback về Chromium bundled của Playwright.

## Installation

Chạy từ thư mục [`mcp-server/`](mcp-server/):

```bash
cd mcp-server
pip3 install mcp playwright
playwright install chromium
npm install
```

`npm install` chỉ dùng để cài `qr-code-styling` cho HTML template [`mcp-server/templates/payment-card.html`](mcp-server/templates/payment-card.html):

```text
mcp-server/node_modules/qr-code-styling/lib/qr-code-styling.js
```

## MCP Server

```bash
cd mcp-server
python3 server.py
```

Server dùng stdio transport. Ví dụ cấu hình MCP client:

```json
{
  "mcpServers": {
    "napas-qr": {
      "command": "python3",
      "args": ["/absolute/path/to/vietnam-bank-qr-mcp/mcp-server/server.py"]
    }
  }
}
```

## MCP Tools

[`server.py`](mcp-server/server.py) expose 5 tool:

| Tool | Mục đích |
|---|---|
| `generate_payment_card(bank_bin, account_no, account_name?, amount?, order_id?, payment_content?)` | Sinh QR payload và render PNG card. Trả JSON string với field `png_path` (đường dẫn tuyệt đối tới file PNG). `bank_bin` là BIN 6 số. |
| `get_qr_data(bank_bin, account_no, amount?, order_id?, payment_content?)` | Chỉ sinh QR payload EMVCo, không render ảnh. Trả JSON string. `bank_bin` là BIN 6 số. |
| `search_bank(query)` | Tìm ngân hàng theo tên, short name, code hoặc BIN. Trả JSON string. |
| `get_bank_list()` | Liệt kê toàn bộ ngân hàng trong [`banks.json`](mcp-server/banks.json). Trả JSON string. |
| `update_bank_list_tool()` | Refresh danh sách ngân hàng từ VietQR API và tải logo. Có network write. |

`generate_payment_card` trả `png_path` thay vì `Image` content block để tránh truncation khi serialize qua transport. Agent/client đọc file PNG khi cần hiển thị.

Bank not found hoặc lỗi API sẽ raise `ToolError` → MCP client nhận `isError: true` (không trả JSON error string).

## Python API

Ví dụ này chạy từ [`mcp-server/`](mcp-server/):

```python
from banks import search_banks
from qr_generator import generate_qr_data, render_payment_card, sanitize_content
from renderer import render_card

bank = search_banks("TPBank")[0]

# Quan trọng: QR payload dùng bank.bin, không dùng bank.code.
qr_data = generate_qr_data(
    bank_bin=bank.bin,
    account_no="0123456789",
    amount=1000000,
    payment_content=sanitize_content("TEST TRANSFER"),
)

# Cách 1: render_payment_card() — trả absolute path tới PNG.
png_path = render_payment_card(
    qr_data=qr_data,
    bank_name=bank.name,
    bank_code=bank.code,           # short code cho logo.
    account_no="0123456789",
    account_name="NGUYEN VAN A",
    amount=1000000,                # numeric VND; renderer tự format.
    payment_content="TEST TRANSFER",
    bank_short_name=bank.short_name,
    bank_full_name=bank.name,
)
print(png_path)

# Cách 2: render_card() thủ công nếu cần kiểm soát card_data và output path.
card_data = {
    "qr_data": qr_data,
    "bank_code": bank.code,         # Renderer dùng code ngắn để tìm logo.
    "bank_name": bank.short_name,   # tên ngắn cho header.
    "bank_full_name": bank.name,    # tên đầy đủ cho subtitle.
    "bank_short_name": bank.short_name,
    "account_name": "NGUYEN VAN A",
    "account_no": "0123456789",
    "payment_content": "TEST TRANSFER",
    "amount": 1000000,              # numeric VND; 0/None sẽ ẩn amount box.
}
path = render_card(card_data, output_path="./qr_card.png")
print(path)
```

Nếu muốn PNG bytes thay vì path, dùng `generate_payment_card()` (wrap `render_payment_card()` + đọc file).

Nếu cần kiểm tra signature thật thay vì đoán:

```bash
cd mcp-server
python3 - <<'PY'
import inspect
from banks import search_banks
from qr_generator import generate_qr_data
from renderer import render_card
print(inspect.signature(search_banks))
print(inspect.signature(generate_qr_data))
print(inspect.signature(render_card))
PY
```

## Rendering Pipeline

```text
Bank/account/amount/content
-> generate_qr_data(): tạo payload EMVCo/NAPAS raw + CRC16
-> renderer.py ghi card_data ra JSON config file (không string interpolation)
-> subprocess (sys.executable) khởi Playwright, đọc config, inject window.__CARD_DATA__
-> payment-card.html load font local và qr-code-styling.js
-> browser render styled QR canvas
-> Playwright chụp screenshot body ở scale 2x
-> trả về PNG path; generate_payment_card() đọc thành bytes
```

Playwright được chạy trong subprocess có chủ ý (dùng `sys.executable` để kế thừa Python interpreter đang chạy). Không đưa sync Playwright trực tiếp vào async MCP handler vì có thể deadlock. Subprocess nhận input qua JSON config file thay vì string interpolation để tránh bug escape.

## Common Pitfalls

### `bank_bin` (BIN) vs `bank_code` (short code)

`generate_qr_data()` và MCP tool nhận `bank_bin` — BIN 6 số như `970423`. Renderer cần `bank_code` (short code như `TPB`) trong `card_data` để đọc logo từ [`assets/bank_logos/{code}.png`](mcp-server/assets/bank_logos/).

```python
# QR payload — dùng BIN
qr_data = generate_qr_data(bank_bin=bank.bin, ...)

# Card data — dùng short code cho logo
card_data = {"bank_code": bank.code, ...}
```

### MCP tool names differ from Python functions

- MCP: `search_bank()` trả JSON.
- Python module: `search_banks()` trả list `Bank`.
- MCP: `get_qr_data()`.
- Python module: `generate_qr_data()`.

### Template needs `file://`, not `set_content()`

[`payment-card.html`](mcp-server/templates/payment-card.html) load relative assets:

- [`../assets/fonts/...`](mcp-server/assets/fonts/)
- `../node_modules/qr-code-styling/...`
- bank logos injected từ renderer

Vì vậy renderer phải dùng `page.goto("file://...")` để relative paths hoạt động.

### Screenshot target is `body`

Renderer screenshot `body`, không phải `.card` hay `.mac-window`, để giữ padding 16px và shadow/radius của card.

### Amount `0` hoặc âm không phát tag `54`

`generate_qr_data(amount=0)`, số âm, và `None` đều omit tag `54` trong QR payload. Đây là behavior cố ý — chỉ `amount > 0` mới tạo amount field. Không "fix" bằng truthiness check.

### Optional rows need explicit `[hidden]` CSS

Template dùng flex row. Nếu sửa CSS, giữ rule này:

```css
.info-row[hidden], .amount-row[hidden] { display: none !important; }
```

Nếu bỏ rule này, row rỗng có thể vẫn hiện dù JS đã set `hidden = true`.

## QR Spec Constraints

- Root merchant account tag là `38`, không phải `26`.
- Tag `38` chứa AID `A000000727`, payment network field `00 = BIN`, `01 = account number`, service `QRIBFTTA`.
- Currency tag `53` là `704`.
- Country tag `58` là `VN`.
- Payment content nằm ở additional data tag `62`, subtag `08`.
- CRC dùng CRC16-CCITT, polynomial `0x1021`, initial `0xFFFF`.

Chi tiết thuật toán nằm ở [`skills/qr-transfer/references/qr-algorithm.md`](skills/qr-transfer/references/qr-algorithm.md).

## Smoke Checks

### QR payload

```bash
cd mcp-server
python3 - <<'PY'
from qr_generator import generate_qr_data, sanitize_content

qr = generate_qr_data(
    "970423",
    "0123456789",
    100000,
    payment_content=sanitize_content("TEST"),
)

print(qr)
print("starts_ok", qr.startswith("00020101021238"))
print("crc_tag", qr[-8:-4])
print("crc", qr[-4:])
PY
```

Kỳ vọng:

- `starts_ok True`
- `crc_tag 6304`
- CRC cuối là 4 ký tự hex

### Render PNG

```bash
cd mcp-server
python3 - <<'PY'
from banks import search_banks
from qr_generator import generate_qr_data, sanitize_content
from renderer import render_card

bank = search_banks("TPBank")[0]
qr_data = generate_qr_data(bank.bin, "0123456789", 100000, payment_content=sanitize_content("TEST"))
path = render_card({
    "qr_data": qr_data,
    "bank_code": bank.code,
    "bank_name": bank.name,
    "account_name": "NGUYEN VAN A",
    "account_no": "0123456789",
    "payment_content": "TEST",
    "amount": "100.000 VND",
}, output_path="./qr_card.png")
print(path)
PY
```

Nếu lệnh render fail trên máy mới, kiểm tra:

1. Đã chạy `playwright install chromium` chưa.
2. Nếu dùng Chromium ngoài Playwright, đã set `CHROMIUM_PATH` chưa.

## Bank Data And Logos

[`banks.py`](mcp-server/banks.py) đọc dữ liệu từ [`mcp-server/banks.json`](mcp-server/banks.json) và logo từ [`mcp-server/assets/bank_logos/`](mcp-server/assets/bank_logos/).

Chỉ refresh khi thật sự cần:

```python
from banks import update_bank_list
update_bank_list()
```

Lệnh này gọi `https://api.vietqr.io/v2/banks` và tải logo từ VietQR, nên sẽ thay đổi file local.

## Agent Skill

Skill dành cho agent nằm ở:

```text
skills/qr-transfer/
```

Đọc [`skills/qr-transfer/SKILL.md`](skills/qr-transfer/SKILL.md) để biết workflow agent-facing, các pitfall đã gặp, và các reference về QR algorithm/rendering/design.

## License

MIT.

## Credits

- Bank data và logos: VietQR (`api.vietqr.io`)
- QR styling: `qr-code-styling`
- Font: Be Vietnam Pro
- QR spec: NAPAS QR IBFTTA / EMVCo
