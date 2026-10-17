"""Install the module through Foundry's own package installer from the public manifest URL.
Run with the world shut down (a service restart does that). Needs ~/.config/wfvtt-smoke sourced."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import sync_playwright
from _setup_admin import setup_page
MANIFEST = os.environ.get("SF2E_MANIFEST", "https://github.com/antipop001/sf2ehud/releases/latest/download/module.json")
with sync_playwright() as pw:
    b, pg = setup_page(pw)
    r = pg.evaluate("""async (manifest) => {
        const before = game.modules?.get?.('enhancedcombathud-sf2e')?.version ?? null;
        let result, error = null;
        try { result = await game.installPackage({type: 'module', id: 'enhancedcombathud-sf2e', manifest}); }
        catch (e) { error = String(e); }
        await new Promise(r => setTimeout(r, 2000));
        const pkgs = await game.getPackages?.({type: 'module'}).catch(() => null);
        const mine = pkgs ? [...(pkgs.values?.() ?? pkgs)].find(p => p.id === 'enhancedcombathud-sf2e') : null;
        return {before, error, result: result ? {id: result.id, version: result.version, title: result.title, manifest: result.manifest, download: result.download} : result,
                installedNow: mine ? {version: mine.version, availability: mine.availability, unavailable: mine.unavailable} : null,
                notifications: [...document.querySelectorAll('#notifications li, .notification')].map(n => n.textContent.trim()).slice(-5)};
    }""", MANIFEST)
    print(json.dumps(r, indent=1))
    b.close()
