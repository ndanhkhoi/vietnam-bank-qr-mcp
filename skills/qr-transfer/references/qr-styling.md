# QR Code Styling Config

`qr-code-styling` is loaded in the browser from `mcp-server/templates/payment-card.html`:

```html
<script src="../node_modules/qr-code-styling/lib/qr-code-styling.js"></script>
```

The template renders from the raw EMVCo QR string in `window.__CARD_DATA__.qr_data`; Python does not pre-render the QR image for the card.

## Current Config

Verify these values against `mcp-server/templates/payment-card.html` before changing them.

```javascript
const qrCode = new QRCodeStyling({
  width: 220,
  height: 220,
  type: 'canvas',
  data: params.qr_data,
  margin: 6,

  dotsOptions: {
    type: 'dots',
    color: '#0E0E0C',
  },

  backgroundOptions: { color: '#ffffff' },

  cornersSquareOptions: {
    type: 'extra-rounded',
    color: '#0F4D34',
  },
  cornersDotOptions: {
    type: 'dot',
    color: '#0F4D34',
  },

  image: params.bank_logo_base64 ? 'data:image/png;base64,' + params.bank_logo_base64 : '',
  imageOptions: {
    crossOrigin: 'anonymous',
    margin: 4,
    imageSize: 0.22,
    hideBackgroundDots: true,
  },
});
qrCode.append(document.getElementById('qr-canvas'));
```

## Scannability Rules

- Keep `imageSize` at or below `0.25`; the current logo size is `0.22`.
- Keep ink-on-white contrast for QR dots (solid `#0E0E0C`).
- Keep `hideBackgroundDots: true` so the centered logo does not interfere with modules.
- If scanning becomes unreliable, reduce `imageSize` to `0.15` or remove the centered logo.
