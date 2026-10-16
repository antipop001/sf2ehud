import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from _foundry import *
with sync_playwright() as pw:
    b, pg, errors = join(pw)
    r = pg.evaluate("""async () => {
        const out = {};
        for (const id of ['sf2e.iconics', 'sf2e.paizo-pregens']) {
            const idx = await game.packs.get(id).getIndex({fields: ['type', 'system.details.level.value']});
            out[id] = idx.filter(e => e.type === 'character').map(e => [e.system?.details?.level?.value, e.name]).sort((a, b) => a[0] - b[0]);
        }
        return out; }""")
    for k, v in r.items():
        print(k, len(v)); print("  levels:", sorted({x[0] for x in v})); print("  L7:", [n for l, n in v if l == 7])
    b.close()
