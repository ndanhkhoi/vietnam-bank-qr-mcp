# Payment Card Template Design Spec

Source of truth: `mcp-server/templates/payment-card.html`.

This reference explains the current design, but numeric values can drift. Verify against the live template before editing renderer or CSS.

## Design Summary

The card is a single flat white rounded card (`480px` wide) centered on a cream `#ECE5D2` body. There is no OS window chrome. The card contains: a header row (bank logo + bank short name + full name subtitle + a green "NAPAS QR" badge), a centered title, a centered QR frame with the bank logo overlaid in the middle, an info table with dashed dividers, an optional amount box with a warm gradient background, a warning block, and a footer line.

## Key Layout Values

- Body width: `560px`; background `#ECE5D2`; padding `16px`. The renderer screenshots `body` at 2x, so this padding preserves the card shadow and radius.
- Card width: `480px`, centered via `margin: 0 auto`; radius `20px`.
- Card top padding: `20px 24px 16px`.
- Title padding: `18px 24px 12px`.
- QR frame: `248px` square, white, `1px` border, `14px` radius, `14px` padding.
- QR canvas (qr-code-styling): `220px` square with `6px` QR margin.
- Header bank logo box: `56px` square, `12px` radius.
- Info padding: `2px 24px 4px`.
- Amount box margin/padding: `12px 24px 0` outer, `14px 18px` inner, `12px` radius.
- Warning margin/padding: `14px 24px 0` outer, `10px 12px` inner, `8px` radius.
- Footer padding: `12px 24px`, top border.

## Typography

Local fonts from `mcp-server/assets/fonts/`:

- `Be Vietnam Pro` — UI text. Weights: `400`, `500`, `600`, `700` (separate woff2 files).
- `Fraunces` — display (titles, amount). Variable font (`Fraunces-Variable.woff2`) for weights `100–900`, plus `Fraunces-Italic.woff2` for italic brand mark only.
- `JetBrains Mono` — account number, NAPAS badge, footer timestamp. Variable font (`JetBrainsMono-Variable.woff2`) for weights `100–800`.

| Element | Family | Size | Weight | Color |
|---|---|---:|---:|---|
| Bank short name | Be Vietnam Pro | `15px` | `600` | ink `#15120D` |
| Bank full name (subtitle) | Be Vietnam Pro | `11px` | `400` | stone `#75716A` |
| Card title | Fraunces | `22px` | `500` | ink |
| Subtitle | Be Vietnam Pro | `12px` | `400` | stone |
| Info label | Be Vietnam Pro | `10px` | `600` | stone (uppercase, `0.7px` tracking) |
| Info value | Be Vietnam Pro | `14px` | `500` | ink |
| Account number (mono) | JetBrains Mono | `15px` | `600` | ink |
| Amount value | Fraunces | `28px` | `600` | accent `#0F4D34` |
| NAPAS badge | JetBrains Mono | `9.5px` | `700` | accent on `#E8F0EB` |
| Warning text | Be Vietnam Pro | `11px` | `400` | warn-ink `#6B4A12` |
| Footer | JetBrains Mono | `10px` | `400` | stone-2 `#9A958C` |

## Palette (CSS variables)

- `--bg #ECE5D2`, `--card-bg #FFFFFF`
- `--ink #15120D`, `--ink-2 #3A352D`
- `--stone #75716A`, `--stone-2 #9A958C`
- `--line #E5DFCD`, `--line-2 #F0EBDD`
- `--accent #0F4D34` (green), `--accent-soft #E8F0EB`
- `--gold #B8842B`
- `--warn-bg #FBF3DF`, `--warn-line #E5C97A`, `--warn-ink #6B4A12`

## Info Rows

The info table uses labels on the left and values on the right. UI labels are Vietnamese (`Chủ TK`, `Số TK`, `Ngân hàng`, `Nội dung`). Dividers are dashed:

```css
.info-row {
  display: flex;
  border-bottom: 1px dashed var(--line);
}
.info-row:last-child { border-bottom: none; }
```

Optional rows are hidden via the `[hidden]` attribute. Flex display overrides the browser's default hidden behavior, so keep:

```css
.info-row[hidden], .amount-row[hidden], .card-amount[hidden], .card-warn[hidden] { display: none !important; }
```

## Optional Rows

| Row | Required | Hidden when |
|---|---:|---|
| Account holder (`Chủ TK`) | No | `account_name` is empty. |
| Account number (`Số TK`) | Yes | Never. |
| Bank (`Ngân hàng`) | Yes | Never (always shows bank short name). |
| Transfer content (`Nội dung`) | No | `payment_content` is empty. |
| Amount box | No | `amount` is `0`, `None`, or empty. |

## Amount Box

The amount block is a separate rounded box below the info table with a warm cream gradient background and a faint green radial glow in the corner. A subtle `VND` watermark sits in the bottom-right. The value is rendered as `Fraunces` accent green with a `đ` superscript. The renderer formats the numeric VND with `.` thousands separators.

When `amount` is `0`, `None`, or empty, the entire `.card-amount` block is hidden.

## Header Bank Logo

- Real bank logos load from `assets/bank_logos/{code}.png` as base64-injected `<img>` (white padding inside the colored box).
- When no logo file exists, the box gets a `placeholder` class: dark gradient background with the bank's short-name initials (max 3 chars) in Fraunces.

## QR Center Logo

The QR is rendered by `qr-code-styling` (loaded from `node_modules/qr-code-styling/lib/qr-code-styling.js`) with:
- Dots: solid ink `#0E0E0C`, `dots` type.
- Corner squares: `extra-rounded`, accent green.
- Corner dots: `dot`, accent green.
- Center image: bank logo at `imageSize: 0.22` when available.

## Visual Hierarchy

- Amount is the strongest visual anchor: accent green, Fraunces serif, large.
- Account number is the secondary anchor: JetBrains Mono, ink, slightly smaller.
- Keep transfer content in ink, preserve user casing, do not uppercase.

## Warning Block

- Padding: `10px 12px`.
- Border radius: `8px`.
- Background: `#FBF3DF` (warm), border `#E5C97A`.
- Icon: `14px` triangular warning SVG in warn-ink.
- Text: `11px`, warn-ink `#6B4A12`, bold keywords.
