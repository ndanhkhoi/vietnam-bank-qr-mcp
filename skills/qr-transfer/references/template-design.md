# Payment Card Template Design Spec

Source of truth: `mcp-server/templates/payment-card.html`.

This reference explains the current design, but numeric values can drift. Verify against the live template before editing renderer or CSS.

## Design Summary

The card uses a macOS-style window shell: title bar, three traffic-light dots, centered title, and a content area containing the QR code, bank logo/name, transfer rows, warning, and footer.

The title text in the actual UI is Vietnamese: `Chuyen khoan - Napas QR` conceptually maps to the displayed localized title in the template.

## Key Layout Values

- Window radius: `12px`.
- Body padding: `16px`; this is required because the renderer screenshots `body` and needs room for the shadow/radius.
- Content padding: `32px 40px 24px`.
- QR frame: `420px` square, white, `1px` border, `20px` radius, `16px` padding.
- QR canvas: `388px` square with `10px` QR margin.
- Bank logo: max `220px` wide and `66px` high.

## Typography

Local Be Vietnam Pro fonts are used from `mcp-server/assets/fonts/`. Keep weights to available files: `400`, `500`, `600`, and `700`.

| Element | Size | Weight | Color |
|---|---:|---:|---|
| Window title | `13px` | `600` | `#3c3c3c` |
| Card title | `28px` | `600` | `#0a1e3f` |
| Subtitle | `15px` | `400` | `#9ba8bd` |
| Info label | `15px` | `500` | `#6b7d99` |
| Info value | `19px` | `600` | `#142b4f` |
| Account number | `21px` | `700` | `#142b4f` |
| Transfer content | `19px` | `600` | `#475569` |
| Amount | `26px` | `700` | `#15803d` |
| Warning text | `13px` | `400` | `#15803d` |
| Footer | `13px` | `400` | `#a1adbd` |

## Info Rows

The info table uses labels on the left and values on the right. The localized UI labels in the template are Vietnamese, for example account holder, account number, content, and amount.

Each `.info-row` owns its bottom border:

```css
.info-row {
  display: flex;
  border-bottom: 1px solid var(--line-soft);
}
```

Do not use `.info-row:last-child { border-bottom: none }` or adjacent sibling borders. Optional middle rows can be hidden, and those selector patterns leave orphan borders.

## Optional Rows

| Row | Required | Hidden when |
|---|---:|---|
| Account holder | No | `account_name` is empty. |
| Account number | Yes | Never. |
| Transfer content | No | `payment_content` is empty. |
| Amount | No | `amount` is empty. |

Flex display overrides the browser's default `[hidden]` behavior, so keep this rule:

```css
.info-row[hidden], .amount-row[hidden] { display: none !important; }
```

## Visual Hierarchy

- Keep amount as the strongest visual anchor: green, larger, bold.
- Keep account number navy so it does not compete with amount.
- Keep transfer content in slate and preserve user casing.
- Use real bank logo images; do not replace logos with text or CSS approximations.

## Warning Block

The warning block uses a green success-style treatment:

- Padding: `10px 16px`.
- Border radius: `12px`.
- Background: `#f0fdf4`.
- Border: `#bbf7d0`.
- Icon: `24px` green circle with checkmark.
- Text: `13px`, green.
