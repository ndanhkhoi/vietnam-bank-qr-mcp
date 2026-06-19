#!/usr/bin/env python3
"""MCP Server — Napas QR code generation for bank transfers."""
from __future__ import annotations

import json
import logging

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from banks import Bank, get_bank_by_bin, load_banks, search_banks, update_bank_list
from qr_generator import generate_qr_data, render_payment_card, sanitize_content

logger = logging.getLogger("napas-qr")
mcp = FastMCP("napas-qr")


# ── Helpers ──────────────────────────────────────────────

def _require_bank(bank_bin: str) -> Bank:
    """Resolve bank by BIN or raise ToolError (sets isError: true)."""
    bank = get_bank_by_bin(bank_bin)
    if bank is None:
        raise ToolError(f"Bank not found: {bank_bin}")
    return bank


def _bank_summary(bank: Bank) -> dict:
    return {"bin": bank.bin, "code": bank.code, "short_name": bank.short_name, "name": bank.name}


# ── QR Tools ─────────────────────────────────────────────

@mcp.tool()
def generate_payment_card(
    bank_bin: str,
    account_no: str,
    account_name: str = "",
    amount: float | None = None,
    order_id: str | None = None,
    payment_content: str | None = None,
) -> str:
    """Generate payment card PNG via HTML + Playwright.

    Professional card design with QR, bank logo, transfer info.
    Rendered via Playwright at 900x1200 viewport, 2x retina.
    Returns JSON with a `png_path` field pointing to the rendered file.

    Args:
        bank_bin: Bank BIN (6 digits, e.g. 970423)
        account_no: Recipient account number
        account_name: Account holder name
        amount: VND amount (omit for 'Tuỳ chọn')
        order_id: Tracking ID
        payment_content: Description
    """
    bank = _require_bank(bank_bin)

    content = sanitize_content(payment_content)
    name = sanitize_content(account_name) or ""
    qr_data = generate_qr_data(bank_bin, account_no, amount, order_id, content)
    png_path = render_payment_card(
        qr_data=qr_data,
        bank_name=bank.name,
        bank_code=bank.code,
        account_no=account_no,
        account_name=name,
        amount=amount,
        payment_content=content,
    )

    return json.dumps({
        "bank": bank.short_name,
        "bank_bin": bank.bin,
        "account_no": account_no,
        "account_name": name or "",
        "amount": amount or "user-entered",
        "payment_content": content or "",
        "qr_data": qr_data,
        "png_path": png_path,
    }, ensure_ascii=False)


@mcp.tool()
def get_qr_data(
    bank_bin: str,
    account_no: str,
    amount: float | None = None,
    order_id: str | None = None,
    payment_content: str | None = None,
) -> str:
    """Generate QR data string only (no image). For custom rendering.

    Args:
        bank_bin: Bank BIN (6 digits, e.g. 970423)
        account_no: Recipient account number
        amount: VND amount
        order_id: Tracking ID
        payment_content: Description
    """
    bank = _require_bank(bank_bin)

    content = sanitize_content(payment_content)
    qr_data = generate_qr_data(bank_bin, account_no, amount, order_id, content)
    return json.dumps({
        "bank": bank.short_name,
        "bank_bin": bank.bin,
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
    try:
        banks = update_bank_list()
    except Exception as e:
        logger.exception("update_bank_list failed")
        raise ToolError(f"Failed to refresh bank list: {e}")
    return json.dumps({
        "message": f"Updated {len(banks)} banks",
        "banks": [_bank_summary(b) for b in banks],
    }, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="stdio")
