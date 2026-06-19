"""HTML to PNG renderer using Playwright (subprocess)."""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import tempfile


_TEMPLATE = os.path.join(os.path.dirname(__file__), "templates", "payment-card.html")
_LOGO_CACHE = os.path.join(os.path.dirname(__file__), "assets", "bank_logos")


def _get_chromium_path() -> str | None:
    """Resolve Chromium path from env at call time."""
    return os.environ.get("CHROMIUM_PATH") or None


def _get_bank_logo_b64(bank_code: str) -> str:
    """Get cached bank logo as raw base64 string (no data URL prefix)."""
    cache_path = os.path.join(_LOGO_CACHE, f"{bank_code}.png")
    if not os.path.exists(cache_path):
        return ""
    with open(cache_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def render_card(data: dict, output_path: str | None = None) -> str:
    """Render payment card HTML to PNG via Playwright subprocess.

    Returns: Absolute path to rendered PNG.
    """
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".png", prefix="qr_card_")
        os.close(fd)

    # Get bank logo
    bank_code = data.get("bank_code", "")
    logo_b64 = _get_bank_logo_b64(bank_code)

    # Amount
    amount = data.get("amount", "")

    # Build inject JS — set window.__CARD_DATA__ for template script
    inject_js = (
        "window.__CARD_DATA__ = {"
        + f"qr_data: {json.dumps(data.get('qr_data', ''))},"
        + f"bank_logo_base64: {json.dumps(logo_b64)},"
        + f"bank_name: {json.dumps(data.get('bank_name', ''))},"
        + f"account_name: {json.dumps(data.get('account_name', ''))},"
        + f"account_no: {json.dumps(data.get('account_no', ''))},"
        + f"payment_content: {json.dumps(data.get('payment_content', ''))},"
        + f"amount: {json.dumps(amount)},"
        + "};"
    )

    # Build Playwright script — use file:// to load template with relative font paths
    template_url = "file://" + _TEMPLATE
    chromium_path = _get_chromium_path()

    config = {
        "template_url": template_url,
        "output_path": output_path,
        "chromium_path": chromium_path,
        "inject_js": inject_js,
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir="/tmp") as cf:
        json.dump(config, cf)
        config_path = cf.name

    script_content = """import json, sys
from playwright.sync_api import sync_playwright

with open(sys.argv[1]) as f:
    cfg = json.load(f)

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        **({"executable_path": cfg["chromium_path"]} if cfg["chromium_path"] else {}),
        args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
    )
    page = browser.new_page(
        viewport={"width": 900, "height": 1200},
        device_scale_factor=2,
    )
    page.add_init_script(cfg["inject_js"])
    page.goto(cfg["template_url"], wait_until="networkidle")
    page.wait_for_timeout(500)

    page.evaluate("async () => { await document.fonts.ready; }")

    page.evaluate('''() => {
        const imgs = document.querySelectorAll('img');
        return Promise.all(Array.from(imgs).map(img => {
            if (img.complete) return Promise.resolve();
            return new Promise((resolve) => {
                img.onload = resolve;
                img.onerror = resolve;
            });
        }));
    }''')

    page.wait_for_timeout(500)
    page.wait_for_function("() => document.querySelector('#qr-canvas canvas') !== null", timeout=5000)
    page.wait_for_timeout(300)

    page.locator("body").screenshot(path=cfg["output_path"], type="png")
    browser.close()
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir="/tmp") as f:
        f.write(script_content)
        script_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, script_path, config_path],
            capture_output=True,
            text=True,
            timeout=45,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Renderer failed: {result.stderr}")
        return os.path.abspath(output_path)
    except subprocess.TimeoutExpired:
        raise RuntimeError("Renderer timed out after 45s")
    finally:
        for p in (script_path, config_path):
            try:
                os.unlink(p)
            except OSError:
                pass


def image_to_base64(path: str) -> str:
    """Read PNG file and return base64 string."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def read_image_bytes(path: str) -> bytes:
    """Read PNG file and return raw bytes."""
    with open(path, "rb") as f:
        return f.read()
