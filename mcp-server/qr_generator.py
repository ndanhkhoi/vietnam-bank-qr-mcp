"""QR code generation for Napas bank transfers — EMVCo spec compliant.

Spec: EMVCo QR + Napas QR IBFTTA (AID A000000727).
"""
from __future__ import annotations

import re
import unicodedata


# Napas constants
NAPAS_AID = "A000000727"
NAPAS_SERVICE = "QRIBFTTA"
NAPAS_CURRENCY = "704"
MERCHANT_CATEGORY = "5812"
COUNTRY_CODE = "VN"


# ── CRC16-CCITT ──────────────────────────────────────────

def calculate_crc16(data: str) -> str:
    """CRC16-CCITT with polynomial 0x1021, initial 0xFFFF.

    Port of Java CRCUtils.getCRC16CCITT(data, 0x1021, 0xFFFF, false).
    Bit-by-bit processing (MSB first), matching the Java implementation exactly.
    """
    crc = 0xFFFF
    for byte in data.encode("ascii"):
        for i in range(8):
            bit = ((byte >> (7 - i)) & 1) == 1
            c15 = ((crc >> 15) & 1) == 1
            crc <<= 1
            if c15 ^ bit:
                crc ^= 0x1021
    crc &= 0xFFFF
    return f"{crc:04X}"


# ── EMVCo TLV builder ────────────────────────────────────

def _tlv(tag: str, value: str) -> str:
    """Build a single EMVCo TLV: tag + 2-digit length + value."""
    return f"{tag}{len(value):02d}{value}"


def _build_tlv_map(data: dict[str, str]) -> str:
    """Build TLV string from dict, sorted by tag (EMVCo requirement)."""
    return "".join(_tlv(tag, data[tag]) for tag in sorted(data))


# ── QR data generation ───────────────────────────────────

def generate_qr_data(
    bank_code: str,
    account_no: str,
    amount: float | None = None,
    order_id: str | None = None,
    payment_content: str | None = None,
) -> str:
    """Generate Napas QR data string (EMVCo format).

    EMVCo TLV structure:
      00 = Payload format indicator ("01")
      01 = Initiation method ("12" = Dynamic QR)
      38 = Merchant Account Information (Napas)
         00 = AID (A000000727)
         01 = Payment Network Specific (nested)
            00 = bankCode (BIN)
            01 = accountNo
         02 = Service (QRIBFTTA)
      52 = Merchant Category Code (5812)
      53 = Currency (704 VND)
      54 = Amount (optional)
      58 = Country Code (VN)
      62 = Additional Data Field
         08 = Purpose (payment content)
         01 = Bill Number (order_id, optional)
      63 = CRC
    """
    # Root level (sorted by tag automatically via _build_tlv_map)
    root: dict[str, str] = {
        "00": "01",      # Payload format indicator
        "01": "12",      # Dynamic QR
    }

    # ID 38: Merchant Account Information (Napas)
    payment_network = _build_tlv_map({
        "00": bank_code,
        "01": account_no,
    })
    merchant_account = _build_tlv_map({
        "00": NAPAS_AID,
        "01": payment_network,
        "02": NAPAS_SERVICE,
    })
    root["38"] = merchant_account

    # ID 52: Merchant Category Code
    root["52"] = MERCHANT_CATEGORY

    # ID 53: Currency
    root["53"] = NAPAS_CURRENCY

    # ID 54: Transaction Amount (optional)
    if amount is not None and amount > 0:
        amt = f"{amount:.0f}"
        root["54"] = amt

    # ID 58: Country Code
    root["58"] = COUNTRY_CODE

    # ID 62: Additional Data Field
    additional: dict[str, str] = {}
    if payment_content:
        additional["08"] = payment_content
    if order_id:
        additional["01"] = order_id
    if additional:
        root["62"] = _build_tlv_map(additional)

    # Build payload + CRC
    payload = _build_tlv_map(root)
    payload += "6304"  # CRC tag + length placeholder
    crc = calculate_crc16(payload)
    return payload + crc


# ── Sanitize ─────────────────────────────────────────────

def sanitize_content(text: str | None) -> str | None:
    """Normalize to ASCII: remove Vietnamese diacritics, keep alphanumeric + spaces only.

    Pipeline:
      1. Replace Đ/đ manually (Unicode NFD cannot decompose these — they are
         standalone letters, not base + combining mark).
      2. NFD decomposition: "ê" → "e" + combining circumflex, "ơ" → "o" + horn.
      3. Strip combining marks (category Mn).
      4. Final guard: keep [a-zA-Z0-9 ] only.
    """
    if text is None:
        return None
    # Step 1: Đ/đ là chữ cái riêng biệt, NFD không phân tích được → replace tay
    text = text.replace("Đ", "D").replace("đ", "d")
    # Step 2: NFD decomposition
    decomposed = unicodedata.normalize("NFD", text)
    # Step 3: Mn = Mark, Nonspacing (combining diacritics)
    no_marks = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    # Step 4: keep [a-zA-Z0-9 ] only
    return re.sub(r"[^a-zA-Z0-9 ]", "", no_marks).strip()


# ── Payment card ─────────────────────────────────────────

def generate_payment_card(
    qr_data: str,
    bank_name: str,
    bank_bin: str,
    bank_code: str,
    account_no: str,
    account_holder: str = "",
    amount: float | None = None,
    payment_content: str | None = None,
) -> str:
    """Generate payment card PNG via HTML + Playwright. Returns base64."""

    if amount:
        amount_str = f"{amount:,.0f} VNĐ".replace(",", ".")
    else:
        amount_str = ""

    card_data = {
        "qr_data": qr_data,
        "bank_code": bank_code,
        "bank_name": bank_name,
        "account_name": account_holder,
        "account_no": account_no,
        "payment_content": payment_content or "",
        "amount": amount_str,
    }

    from renderer import image_to_base64, render_card

    png_path = render_card(card_data)
    return image_to_base64(png_path)
