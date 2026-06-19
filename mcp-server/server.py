#!/usr/bin/env python3
"""MCP Server — Napas QR code generation for bank transfers."""
from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from banks import Bank, get_bank_by_bin, load_banks, search_banks, update_bank_list
from qr_generator import generate_payment_card as _gen_card, generate_qr_data, sanitize_content

mcp = FastMCP("napas-qr")


# ── Helpers ──────────────────────────────────────────────

def _error_response(bin_code: str) -> str:
    return json.dumps({"error": f"Bank not found: {bin_code}"})


def _bank_summary(bank: Bank) -> dict:
    return {"bin": bank.bin, "code": bank.code, "short_name": bank.short_name, "name": bank.name}


# ── QR Tools ─────────────────────────────────────────────

@mcp.tool()
def generate_payment_card(
    bank_code: str,
    account_no: str,
    account_holder: str = "",
    amount: float | None = None,
    order_id: str | None = None,
    payment_content: str | None = None,
) -> str:
    """Generate payment card PNG via HTML + Playwright.

    Professional card design with QR, bank logo, transfer info.
    Rendered via Playwright at 900x1200 viewport, 2x retina.

    Args:
        bank_code: Bank BIN
        account_no: Recipient account number
        account_holder: Account holder name
        amount: VND amount (omit for 'Tuỳ chọn')
        order_id: Tracking ID
        payment_content: Description
    """
    bank = get_bank_by_bin(bank_code)
    if bank is None:
        return _error_response(bank_code)

    content = sanitize_content(payment_content)
    holder = sanitize_content(account_holder) or ""
    qr_data = generate_qr_data(bank_code, account_no, amount, order_id, content)
    image_base64 = _gen_card(
        qr_data=qr_data,
        bank_name=bank.name,
        bank_bin=bank.bin,
        bank_code=bank.code,
        account_no=account_no,
        account_holder=holder,
        amount=amount,
        payment_content=content,
    )

    return json.dumps({
        "bank": bank.short_name,
        "bank_code": bank.bin,
        "account_no": account_no,
        "amount": amount or "user-entered",
        "payment_content": content or "",
        "qr_data": qr_data,
        "image_base64": f"data:image/png;base64,{image_base64}",
    }, ensure_ascii=False)


@mcp.tool()
def get_qr_data(
    bank_code: str,
    account_no: str,
    amount: float | None = None,
    order_id: str | None = None,
    payment_content: str | None = None,
) -> str:
    """Generate QR data string only (no image). For custom rendering.

    Args:
        bank_code: Bank BIN
        account_no: Recipient account number
        amount: VND amount
        order_id: Tracking ID
        payment_content: Description
    """
    bank = get_bank_by_bin(bank_code)
    if bank is None:
        return _error_response(bank_code)

    content = sanitize_content(payment_content)
    qr_data = generate_qr_data(bank_code, account_no, amount, order_id, content)
    return json.dumps({
        "bank": bank.short_name,
        "bank_code": bank.bin,
        "account_no": account_no,
        "amount": amount or "user-entered",
        "payment_content": content or "",
        "qr_data": qr_data,
    }, ensure_ascii=False)


# ── Bank Tools ───────────────────────────────────────────

@mcp.tool()
def get_bank_list() -> str:
    """List all supported banks."""
    return json.dumps([_bank_summary(b) for b in load_banks()], ensure_ascii=False)


@mcp.tool()
def search_bank(query: str) -> str:
    """Search bank by name, code, or BIN.

    Args:
        query: Search string
    """
    return json.dumps([_bank_summary(b) for b in search_banks(query)], ensure_ascii=False)


@mcp.tool()
def update_bank_list_tool() -> str:
    """Refresh bank list from VietQR API. Also downloads all bank logos to cache."""
    banks = update_bank_list()
    return json.dumps({
        "message": f"Updated {len(banks)} banks",
        "banks": [_bank_summary(b) for b in banks],
    }, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="stdio")
