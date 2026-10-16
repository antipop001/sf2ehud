"""Screenshot the HUD for the first PC with the skills drawer open and a skill expanded (icon review)."""
import sys, os, json, base64
sys.path.insert(0, os.path.dirname(__file__))
from _foundry import *
OUT = os.environ.get("SF2E_SMOKE_OUT", "/tmp")
SKILL = sys.argv[1] if len(sys.argv) > 1 else "athletics"
def shot(pg, name):
    data = pg.context.new_cdp_session(pg).send("Page.captureScreenshot", {"format": "png"})["data"]
    p = f"{OUT}/{name}.png"; open(p, "wb").write(base64.b64decode(data)); print("screenshot", p)
with sync_playwright() as pw:
    b, pg, errors = join(pw)
    pg.wait_for_timeout(2000)
    pg.evaluate("""async () => {
        document.querySelectorAll('#notifications li, .notification').forEach(n => n.remove());
        const actor = game.actors.find(a => a.type === 'character');
        canvas.tokens.placeables.find(t => t.actor?.id === actor.id).control({releaseOthers: true});
        ui.ARGON.toggle(true); await new Promise(r => setTimeout(r, 4000));
    }""")
    shot(pg, "icons_main")
    pg.locator(".ability-menu, .ech-drawer-header, .drawer-header, .portrait-hud .ability-title").first.click(timeout=5000) if pg.locator(".ability-menu, .ech-drawer-header, .drawer-header").count() else None
    pg.evaluate("() => { const h = [...document.querySelectorAll('#enhancedcombathud *')].find(e => /SAVES, CORE SKILLS/i.test(e.textContent) && e.children.length === 0); h?.click(); }")
    pg.wait_for_timeout(1500)
    pg.evaluate(f"() => document.querySelector('.{SKILL}-skill')?.click()")
    pg.wait_for_timeout(1500)
    shot(pg, f"icons_drawer_{SKILL}")
    b.close()
