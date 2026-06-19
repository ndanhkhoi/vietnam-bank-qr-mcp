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
  width: 388,
  height: 388,
  type: 'canvas',
  data: params.qr_data,
  margin: 10,

  dotsOptions: {
    type: 'dots',
    gradient: {
      type: 'linear',
      rotation: Math.PI / 6,
      colorStops: [
        { offset: 0, color: '#1a3a6b' },
        { offset: 0.5, color: '#142b4f' },
        { offset: 1, color: '#0a1e3f' },
      ],
    },
  },

  backgroundOptions: { color: '#ffffff' },

  cornersSquareOptions: {
    type: 'extra-rounded',
    gradient: {
      type: 'linear',
      rotation: 0,
      colorStops: [
        { offset: 0, color: '#16a34a' },
        { offset: 1, color: '#15803d' },
      ],
    },
  },
  cornersDotOptions: {
    type: 'dot',
    color: '#15803d',
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
- Keep navy-on-white contrast for QR dots.
- Keep `hideBackgroundDots: true` so the centered logo does not interfere with modules.
- If scanning becomes unreliable, reduce `imageSize` to `0.15` or remove the centered logo.
