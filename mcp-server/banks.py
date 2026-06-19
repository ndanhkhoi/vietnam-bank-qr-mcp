"""Bank data management for Napas QR codes."""
from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from functools import lru_cache

BANKS_FILE = os.path.join(os.path.dirname(__file__), "banks.json")
LOGO_CACHE = os.path.join(os.path.dirname(__file__), "assets", "bank_logos")
VIETQR_API = "https://api.vietqr.io/v2/banks"


@dataclass(frozen=True, slots=True)
class Bank:
    bin: str
    code: str
    name: str
    short_name: str


def _parse_banks(banks_raw: list[dict]) -> tuple[Bank, ...]:
    """Parse raw bank dicts into Bank dataclasses, filtering invalid entries."""
    return tuple(
        Bank(
            bin=str(b.get("bin", "")),
            code=b.get("code", ""),
            name=b.get("name", ""),
            short_name=b.get("short_name", ""),
        )
        for b in banks_raw
        if b.get("bin") and b.get("code")
    )


@lru_cache(maxsize=1)
def _load_banks_cached() -> tuple[Bank, ...]:
    """Load banks from JSON, cached in memory after first call."""
    if not os.path.exists(BANKS_FILE):
        return ()
    with open(BANKS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    banks_raw = data.get("data", data) if isinstance(data, dict) else data
    return _parse_banks(banks_raw)


def load_banks() -> list[Bank]:
    """Return list of all supported banks."""
    return list(_load_banks_cached())


def get_bank_by_bin(bin_code: str) -> Bank | None:
    for bank in _load_banks_cached():
        if bank.bin == bin_code:
            return bank
    return None


def search_banks(query: str) -> list[Bank]:
    q = query.lower()
    return [
        b for b in _load_banks_cached()
        if q in b.code.lower()
        or q in b.name.lower()
        or q in b.short_name.lower()
        or q in b.bin
    ]


def _download_bank_logo(code: str) -> bool:
    """Download bank logo from VietQR API, save to cache."""
    os.makedirs(LOGO_CACHE, exist_ok=True)
    cache_path = os.path.join(LOGO_CACHE, f"{code}.png")
    if os.path.exists(cache_path):
        return True
    url = f"https://api.vietqr.io/img/{code}.png"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            with open(cache_path, "wb") as f:
                f.write(resp.read())
        return True
    except Exception:
        return False


def update_bank_list() -> list[Bank]:
    """Fetch bank list from VietQR API, save to JSON + download all logos."""
    req = urllib.request.Request(VIETQR_API, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())

    banks_raw = data.get("data", [])
    with open(BANKS_FILE, "w", encoding="utf-8") as f:
        json.dump({"data": banks_raw}, f, ensure_ascii=False, indent=2)

    _load_banks_cached.cache_clear()
    banks = _parse_banks(banks_raw)

    for bank in banks:
        _download_bank_logo(bank.code)

    return list(banks)
