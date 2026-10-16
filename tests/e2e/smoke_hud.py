"""Smoke test: enable the module, put an SF2e iconic on the canvas, bind Argon to it, exercise
the HUD panels, and report every page error. Usage: smoke_hud.py [iconic-name-substring]"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from _foundry import *

OUT = os.environ.get("SF2E_SMOKE_OUT", "/tmp")
WANT = sys.argv[1] if len(sys.argv) > 1 else ""
MOD = "enhancedcombathud-sf2e"
NOISE = ("hardware acceleration", "GL Driver Message", "GPU stall")

def shot(name):
    """Playwright's screenshot waits on a frame the busy WebGL canvas never yields; CDP capture does not."""
    import base64
    try:
        cdp = pg.context.new_cdp_session(pg)
        data = cdp.send("Page.captureScreenshot", {"format": "png"})["data"]
        path = f"{OUT}/{name}.png"; open(path, "wb").write(base64.b64decode(data)); print("screenshot", path)
    except Exception as e: print("screenshot failed", name, str(e)[:160])

def real(errs): return [e for e in errs if not any(n in e for n in NOISE)]

with sync_playwright() as pw:
    b, pg, errors = join(pw)
    enabled = pg.evaluate(f"""async () => {{
        const cfg = game.settings.get('core','moduleConfiguration');
        if (cfg['{MOD}']) return true;
        await game.settings.set('core','moduleConfiguration', {{...cfg, '{MOD}': true}});
        return false; }}""")
    if not enabled:
        print("module enabled; rejoining"); b.close()
        b, pg, errors = join(pw)
    pg.wait_for_timeout(3000)
    load_errors = real(errors)
    print('load errors:', json.dumps(load_errors, indent=1))
    print('module active:', pg.evaluate("() => game.modules.get('enhancedcombathud-sf2e')?.active"))

    setup = pg.evaluate("""async (want) => {
        const pack = game.packs.get('sf2e.iconics');
        const idx = await pack.getIndex({fields: ['type', 'system.details.level.value']});
        let cand = idx.filter(e => e.type === 'character');
        if (want) cand = cand.filter(e => e.name.toLowerCase().includes(want.toLowerCase()));
        cand.sort((a, b) => (a.system?.details?.level?.value ?? 99) - (b.system?.details?.level?.value ?? 99));
        const pick = cand[0];
        if (!pick) return {error: 'no iconic matched', names: idx.map(e => e.name)};
        let actor = game.actors.find(a => a.getFlag('core', 'sourceId') === pick.uuid || a._stats?.compendiumSource === pick.uuid);
        if (!actor) actor = await game.actors.importFromCompendium(pack, pick._id);
        const scene = game.scenes.active;
        let tok = scene.tokens.find(t => t.actorId === actor.id);
        if (!tok) {
            const td = await actor.getTokenDocument({x: scene.dimensions.sceneX + 400, y: scene.dimensions.sceneY + 400});
            [tok] = await scene.createEmbeddedDocuments('Token', [td.toObject()]);
        }
        return {actor: actor.name, level: actor.level, cls: actor.class?.name, id: actor.id, token: tok.id,
                items: actor.items.size, strikes: actor.system.actions?.length,
                all: idx.filter(e => e.type === 'character').map(e => e.name)};
    }""", WANT)
    print("setup:", json.dumps({k: v for k, v in setup.items() if k != 'all'}))
    if "error" in setup: print(setup); b.close(); sys.exit(1)

    pg.wait_for_timeout(1500)
    errors.clear()
    bound = pg.evaluate("""async (tokenId) => {
        const token = canvas.tokens.get(tokenId);
        token.control({releaseOthers: true});
        ui.ARGON.toggle(true);
        await new Promise(r => setTimeout(r, 4000));
        const hud = ui.ARGON;
        return {enabled: hud?.enabled, actor: hud?._actor?.name,
                components: Object.keys(hud?.components ?? {}),
                mainPanels: (hud?.components?.main ?? []).map(p => p.constructor.name),
                buttons: (hud?.itemButtons ?? []).length,
                rendered: !!document.querySelector('#enhancedcombathud')};
    }""", setup["token"])
    print("bind:", json.dumps(bound))
    shot("sf2e_hud_main")

    # open the drawer (skills/saves) and every button panel to force their render paths
    exercised = pg.evaluate("""async () => {
        const out = {};
        const hud = ui.ARGON;
        try { const d = hud.components.drawer; if (d) { await d.render?.(); d.element?.querySelector?.('.ech-drawer-header, .drawer-header')?.click?.(); out.drawerCategories = (await d.categories)?.length ?? d.categories?.length; } } catch (e) { out.drawerError = String(e); }
        out.panels = [];
        for (const btn of (hud.itemButtons ?? [])) { try { await btn.render(); } catch (e) { out.panels.push(String(e)); } }
        for (const p of (hud.components.main ?? [])) {
            for (const b of (p.buttons ?? [])) {
                if (b.panel) { try { await b.panel.render?.(); out.panels.push(b.label ?? b.constructor.name); } catch (e) { out.panels.push('ERR ' + (b.label ?? b.constructor.name) + ': ' + e); } }
            }
        }
        return out;
    }""")
    print("exercise:", json.dumps(exercised)[:1500])
    pg.mouse.move(800, 900); pg.wait_for_timeout(800)
    for sel in [".ech-drawer, .drawer", "[data-tooltip]"]:
        pass
    shot("sf2e_hud_after")

    print("hud errors:", json.dumps(real(errors), indent=1))
    b.close()
