"""Shared Playwright helpers for the foundrySB smoke world (sf2e-smoketest)."""
import os, sys, json
from playwright.sync_api import sync_playwright

URL = os.environ.get("SF2E_SMOKE_URL", "http://192.168.11.36:30000")
GM_USER = os.environ.get("SF2E_SMOKE_GM", "Gamemaster")
GM_PASS = os.environ.get("SF2E_SMOKE_GM_PASSWORD", "")


def join(pw, user=GM_USER, password=GM_PASS, viewport=(1600, 1000)):
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = b.new_page(viewport={"width": viewport[0], "height": viewport[1]})
    errors = []
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type in ("error", "warning") else None)
    pg.goto(f"{URL}/join", wait_until="networkidle", timeout=60000)
    pg.wait_for_selector('select[name="userId"] option[value]:not([value=""])', state="attached", timeout=60000)
    opts = pg.eval_on_selector_all('select[name="userId"] option', "os => os.map(o => [o.value, o.textContent.trim(), o.disabled])")
    match = [o for o in opts if o[1] == user and o[0]]
    if not match:
        print("join seats:", opts, file=sys.stderr); b.close(); sys.exit(f"user {user!r} not found")
    if match[0][2]:
        b.close(); sys.exit(f"user {user!r} seat is occupied; log out of the browser tab first")
    pg.select_option('select[name="userId"]', match[0][0])
    if password: pg.fill('input[name="password"]', password)
    pg.click('button[name="join"]')
    pg.wait_for_url("**/game", timeout=60000)
    pg.wait_for_function("() => window.game?.ready === true", timeout=120000)
    return b, pg, errors
