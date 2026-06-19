# Payment Card Template Design Spec

**File:** `templates/payment-card.html`
**Last refined:** 2026-06-19 (v15 — macOS window variant)

## Design

macOS window chrome (title bar + 3 traffic lights + window title) wrapping card content. Bên trong: table layout, QR premium subtle bằng qr-code-styling (JS library).

## Key Decisions

- **macOS window**: title bar `#e8e9ed`, 3 dots close/min/max, title centered "Chuyển khoản — Napas QR"
- **Window radius**: 12px, shadow deep `0 30px 70px rgba(0,0,0,0.18)`
- **Body padding**: 16px (để shadow + radius visible khi screenshot body element)
- **Content padding**: `32px 40px 24px`
- **Background**: gradient `linear-gradient(160deg, #dfe4ec → #c7d0dd)`

## QR — Premium Subtle (qr-code-styling)

Render QR bằng JS library `qr-code-styling` (không dùng Python qrcode nữa cho card). QR data string truyền qua `window.__CARD_DATA__.qr_data`.

```
width: 388px, margin: 10px
dots: round, navy gradient (#1a3a6b → #142b4f → #0a1e3f)
cornersSquare: extra-rounded, green gradient (#16a34a → #15803d)
cornersDot: dot, green #15803d
image: bank logo, hideBackgroundDots: true, imageSize: 0.22
```

QR frame: 420x420px white, border 1px `#e8edf5`, radius 20px, padding 16px.

## Typography (Be Vietnam Pro local .woff2)

| Element | Size | Weight | Color |
|---|---|---|---|
| Window title | 13px | 600 | #3c3c3c |
| Card title | 28px | 600 | navy #0a1e3f |
| Subtitle | 15px | 400 | muted-2 #9ba8bd |
| Info label | 15px | 500 | muted #6b7d99 |
| Info value | 19px | 600 | navy-value #142b4f |
| Account no | 21px | 700 | navy-value |
| Transfer content | 19px | 600 | slate #475569 |
| Amount | 26px | 700 | green #15803d |
| Warning text | 13px | 400 | green |
| Footer | 13px | 400 | muted-3 #a1adbd |

## Bank Branding (logo + name — below QR)

```
.bank-logo    max-width: 220px, max-height: 66px, margin: 0 auto, object-fit: contain
.bank-name    font-size: 19px, weight: 600, color: var(--muted), margin-top: 7px
              padding-bottom: 12px, border-bottom: 1px solid var(--line-soft)
```

Logo + name nằm giữa QR và info table. Bank name có border-bottom tạo separation với info section. Size logo đủ lớn để nhận diện ngân hàng nhanh.

## Info Layout (table — label left, value right)

```
Chủ tài khoản:    NGUYEN VAN A     (19px/600 navy)
Số tài khoản:       0123456789           (21px/700 navy)
Nội dung:     Chuyen khoan mua hang 123   (19px/600 slate)
Số tiền:              500.000 VNĐ          (26px/700 green)
```

Dividers: `1px solid #edf1f6`. Amount là strongest anchor duy nhất.

### Border-bottom pattern (mỗi row đều có)

```css
.info-row {
  display: flex;
  ...
  border-bottom: 1px solid var(--line-soft);
}
/* KHÔNG dùng :last-child { border-bottom: none } */
/* KHÔNG dùng adjacent sibling .info-row + .info-row { border-top } */
```

**Lý do:** Optional rows ẩn via `display: none !important`. Với border-bottom per-row, row ẩn tự mất border → không orphan line. Với `:last-child` hoặc sibling selector, row cuối/đầu vẫn để lại ghost line khi row giữa ẩn.

### Optional rows — ẩn khi rỗng

| Row | Required | Hidden when |
|---|---|---|
| Chủ tài khoản | ❌ | `account_holder` empty |
| Số tài khoản | ✅ | Never |
| Nội dung | ❌ | `payment_content` empty |
| Số tiền | ❌ | `amount` None |

Template JS:
```js
if (accountName) { /* fill */ } else { document.getElementById('account-name-row').hidden = true; }
```

**CSS quirk:** `.info-row` dùng `display: flex` → override `[hidden]`. Phải thêm:
```css
.info-row[hidden], .amount-row[hidden] { display: none !important; }
```

## Warning

```
padding: 10px 16px, border-radius: 12px
bg: #f0fdf4, border: #bbf7d0
icon: 24px SVG green circle + checkmark
text: 13px green #15803d
```

## Font: Be Vietnam Pro

Local `.woff2` — KHÔNG Google Fonts CDN. 4 weights: 400/500/600/700.
