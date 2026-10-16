import sys, json
sys.path.insert(0, __import__("os").path.dirname(__file__))
from _foundry import *
with sync_playwright() as pw:
    b = pw.chromium.launch(); pg = b.new_page()
    pg.goto(f"{URL}/join", wait_until="networkidle", timeout=60000)
    pg.wait_for_selector('select[name="userId"] option[value]:not([value=""])', state="attached", timeout=60000)
    print("seats:", pg.eval_on_selector_all('select[name="userId"] option', "os => os.map(o => [o.textContent.trim(), o.disabled])"))
    b.close()
    b, pg, errors = join(pw)
    info = pg.evaluate("""() => ({
      user: game.user.name, isGM: game.user.isGM, system: game.system.id + ' ' + game.system.version,
      actors: game.actors.map(a => [a.name, a.type, a.id]),
      scenes: game.scenes.map(s => [s.name, s.active, s.tokens.size]),
      modules: [...game.modules].filter(m => m.id.startsWith('enhancedcombathud')).map(m => [m.id, m.active, m.version]),
      moduleConfig: game.settings.get('core','moduleConfiguration'),
      packs: game.packs.filter(p => p.metadata.packageName === 'sf2e' && ['Actor'].includes(p.documentName)).map(p => p.collection),
      argon: !!ui.ARGON, gamepf2e: !!game.pf2e, actionsCount: game.pf2e?.actions?.size,
    })""")
    print(json.dumps(info, indent=1))
    print("errors:", errors[:20])
    b.close()
