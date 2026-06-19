# QR Code Styling Config

**Library:** `qr-code-styling` (npm) — browser-side QR rendering với custom dots, gradients, logos.
**File:** `templates/payment-card.html` — loaded via `<script src="../node_modules/qr-code-styling/lib/qr-code-styling.js">`

## Current Config (v15 — macOS window variant)

```javascript
const qrCode = new QRCodeStyling({
  width: 388,
  height: 388,
  type: 'canvas',
  data: params.qr_data,  // raw EMVCo string from Python
  margin: 10,

  // Dots — round, 3-stop navy gradient
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

  // Background — white
  backgroundOptions: { color: '#ffffff' },

  // Corner markers — green gradient, rounded
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

  // Bank logo center — clean, no background dots
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

## Scannability

Styled QR (rounded dots, logo center) vẫn scannable nếu:
- `imageSize` ≤ 0.25 (logo không quá lớn)
- Contrast đủ (navy on white = OK)
- Error correction level đủ (qr-code-styling default = M, đủ cho logo 22%)
- `hideBackgroundDots: true` — logo cleaner, không cản quét

Nếu QR không quét được → giảm `imageSize` xuống 0.15 hoặc bỏ logo center.
