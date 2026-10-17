"""Admin session on /setup (world must not be running). Needs WF_SMOKE_ADMIN_PASSWORD (~/.config/wfvtt-smoke)."""
import os
URL = os.environ.get("SF2E_SMOKE_URL", "http://192.168.11.36:30000")
PW = os.environ.get("WF_SMOKE_ADMIN_PASSWORD", "")

def setup_page(pw):
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 1600, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    pg.goto(f"{URL}/auth", wait_until="networkidle", timeout=60000)
    pg.wait_for_selector("input[name=adminPassword]", timeout=30000)
    pg.fill("input[name=adminPassword]", PW)
    pg.keyboard.press("Enter")
    pg.wait_for_url("**/setup", timeout=60000)
    pg.wait_for_timeout(2500)
    pg.evaluate("""() => { try { for (const t of (game?.tours?.values?.() ?? [])) if (t.status === 'in-progress') t.exit(); } catch (e) {}
        document.querySelectorAll('.tour-overlay, .tour.active').forEach(el => el.remove()); }""")
    return b, pg
