# QR Algorithm Spec (NAPAS QR IBFTTA)

**Spec:** NAPAS QR Format v1.5.2 — `https://vietqr.net/portal-service/download/documents/QR_Format_T&C_v1.5.2_EN_102022.pdf`

## TLV Structure (EMVCo format)

```
00 02 01                          Payload Format Indicator (mandatory, "01")
01 02 12                          Point of Initiation Method ("12" = Dynamic QR)
38 NN                             Merchant Account Information (Napas)
  00 10 A000000727                GUID/AID (mandatory)
  01 NN                           Payment Network Specific (nested, mandatory)
    00 06 970423                  Acquirer ID / BIN
    01 NN 0123456789             Consumer ID / Account No
  02 08 QRIBFTTA                  Service Code (Inter-Bank Fund Transfer to Account)
52 04 5812                        Merchant Category Code (Eating Places)
53 03 704                         Transaction Currency (VND)
54 NN 500000                      Transaction Amount (optional)
58 02 VN                          Country Code (mandatory)
62 NN                             Additional Data Field (conditional)
  01 NN ORD123                    Bill Number (order_id, optional)
  08 NN Chuyen khoan              Purpose of Transaction (payment_content)
63 04 XXXX                        CRC16-CCITT
```

## Tag Allocation

| Tag | Name | Presence |
|---|---|---|
| 00 | Payload Format Indicator | M |
| 01 | Point of Initiation Method | M |
| 38 | Merchant Account Information (Napas) | M |
| 52 | Merchant Category Code | M |
| 53 | Transaction Currency | M |
| 54 | Transaction Amount | C (if amount) |
| 58 | Country Code | M |
| 62 | Additional Data Field | C |
| 63 | CRC | M |

**Note:** Tag 26-51 used for Payment Intermediaries. Tag **38** specifically for NAPAS system (spec line 930).

## Additional Data Field (ID 62) Sub-tags

| Sub-tag | Name | Max Length |
|---|---|---|
| 01 | Bill Number | 25 |
| 02 | Mobile Number | 25 |
| 03 | Store Label | 25 |
| 04 | Loyalty Number | 25 |
| 05 | Reference Label | 25 |
| 06 | Customer Label | 25 |
| 07 | Terminal Label | 25 |
| 08 | Purpose of Transaction | 25 |
| 09 | Additional Consumer Data Request | 03 |

## CRC16-CCITT

- Polynomial: `0x1021`
- Initial: `0xFFFF`
- Processing: MSB first, bit-by-bit
- No reflection, no final XOR
- Port of Java `CRCUtils.getCRC16CCITT(data, 0x1021, 0xFFFF, false)`

### Verification (spec section 6.3.3)

```
Payload: 00020101021238570010A00000072701270006970403011300110123456780208QRIBFTTA530370454061800005802VN62340107NPS68690819thanh toan don hang6304
Expected CRC: 2E2E
```

If match → algorithm correct.
