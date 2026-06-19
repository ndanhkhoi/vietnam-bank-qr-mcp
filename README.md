# QR Transfer Generator

Tạo QR code chuyển khoản ngân hàng Việt Nam theo chuẩn **NAPAS QR IBFTTA (EMVCo)**. Output: PNG card retina với styled QR (rounded dots, gradient, bank logo center) + thông tin transfer + bank logo.

- 🇻🇳 65 ngân hàng Việt Nam — data + logos từ [VietQR API](https://vietqr.net/) ([`api.vietqr.io`](https://api.vietqr.io/v2/banks))
- 🎨 Card premium macOS window style, font Be Vietnam Pro
- ⚡ MCP server (Model Context Protocol) — tích hợp vào Claude Desktop, Hermes, hoặc bất kỳ MCP client
- 🔌 Hoặc dùng Python API trực tiếp

## Cấu trúc

```
vietnam-bank-qr-mcp/
├── mcp-server/              # Python MCP server + renderer
│   ├── server.py            # MCP server (5 tools)
│   ├── qr_generator.py      # QR data generation (EMVCo TLV + CRC16)
│   ├── banks.py             # Bank data + search + logo download
│   ├── renderer.py          # Playwright subprocess renderer
│   ├── banks.json           # 65 ngân hàng VN
│   ├── package.json         # npm deps (qr-code-styling)
│   ├── templates/
│   │   └── payment-card.html
│   └── assets/
│       ├── bank_logos/      # 63 logo PNG
│       └── fonts/           # Be Vietnam Pro .woff2/.ttf
└── skill/                   # Hermes Agent skill
    ├── SKILL.md             # Documentation + workflow + pitfalls
    └── references/
        ├── qr-algorithm.md
        ├── qr-styling.md
        └── template-design.md
```

## Requirements

- **Python ≥ 3.11**
- **Node.js ≥ 18** (cho `qr-code-styling`)
- **Playwright Chromium** (`pip install playwright && playwright install chromium`)
- **Chromium binary** tại `~/chromium/chrome-linux/chrome` — chỉnh path trong `renderer.py` (`_CHROMIUM_PATH`) nếu khác

## Cài đặt

```bash
cd mcp-server/

# Python deps
pip install mcp playwright
playwright install chromium

# Nếu chưa có Chromium system, dùng Playwright Chromium và sửa _CHROMIUM_PATH trong renderer.py
# thành: os.path.expanduser("~/.cache/ms-playwright/chromium-.../chrome-linux/chrome")

# Node deps (qr-code-styling)
npm install
```

## Sử dụng

### 1. Python API (đơn giản nhất)

```python
import sys; sys.path.insert(0, '.')
from banks import search_banks
from qr_generator import generate_qr_data, sanitize_content
from renderer import render_card

bank = search_banks('TPBank')[0]
# bank.code (string), bank.bin (6 số), bank.name

qr_data = generate_qr_data(
    bank_code=bank.code,          # param "bank_code" nhưng thực ra truyền .code hay .bin đều OK
    account_no='0123456789',
    amount=1000000,
    payment_content=sanitize_content('TEST TRANSFER'),
)

data = {
    'qr_data':        qr_data,
    'bank_code':      bank.code,
    'bank_name':      bank.name,
    'account_name':   'NGUYEN VAN A',
    'account_no':     '0123456789',
    'payment_content':'TEST TRANSFER',
    'amount':         '1.000.000 VNĐ',   # string đã format
}
path = render_card(data, output_path='./qr_card.png')
print(f"Card: {path}")
```

### 2. MCP Server

Chạy MCP server (stdio transport):

```bash
cd mcp-server/
python server.py
```

Tích hợp với MCP client. Ví dụ Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "napas-qr": {
      "command": "python3",
      "args": ["/absolute/path/to/mcp-server/server.py"]
    }
  }
}
```

5 MCP tools:

| Tool | Mô tả |
|------|-------|
| `generate_qr_data(bank_code, account_no, amount?, order_id?, payment_content?)` | QR data string EMVCo TLV + CRC16 |
| `generate_payment_card(...)` | Card PNG — wrapper render_card |
| `render_card(data_dict, output_path?)` | Renderer trực tiếp |
| `sanitize_content(text)` | Normalize ASCII, bỏ dấu VN |
| `search_banks(query)` → `list[Bank]` | Tìm bank theo tên/code/BIN |

### 3. Hermes Agent Skill

Copy folder `skill/` vào `~/.hermes/skills/productivity/vietnam-bank-qr-mcp/` (hoặc category khác). Đọc `skill/SKILL.md` để biết workflow, pitfalls, verification.

## QR Algorithm

Chuẩn NAPAS QR v1.5.2 — tag **38** (không 26), nested payment network (38→01→00+01), tag 08 cho purpose, country code 58 bắt buộc. Chi tiết: `skill/references/qr-algorithm.md`.

## Pitfalls quan trọng

1. **`bank_code` param lừa người** — `generate_qr_data(bank_code=...)` tên param là `bank_code` nhưng cần **BIN 6 số** (`bank.bin` = `970423`), KHÔNG PHẢI `bank.code` (string như `"TPB"`). Truyền `.code` → QR không hợp lệ. **Dùng `bank.bin` cho QR data, `bank.code` chỉ cho renderer tìm logo.**
2. **Playwright trong async MCP** → BẮT BUỘC subprocess. Sync API deadlock.
3. **Screenshot `body` element**, không phải `.card` — body có padding 16px.
4. **Font local** → dùng `page.goto("file://...")`, không dùng `set_content`.

Đầy đủ pitfalls: `skill/SKILL.md` section "Common Pitfalls" (23 items).

## License

MIT. Tự do sử dụng, chỉnh sửa, phân phối.

## Credits

- Bank data + logos: [VietQR](https://vietqr.net/) via [`api.vietqr.io`](https://api.vietqr.io/v2/banks) (MIT)
- QR lib: [qr-code-styling](https://github.com/kozakdenys/qr-code-styling) (MIT)
- Font: [Be Vietnam Pro](https://github.com/be-vietnam/be-vietnam-pro) (OFL-1.1)
- EMVCo QR spec: NAPAS QR IBFTTA v1.5.2
