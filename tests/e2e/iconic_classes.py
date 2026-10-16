import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from _foundry import *
with sync_playwright() as pw:
    b, pg, errors = join(pw)
    print(json.dumps(pg.evaluate("""async () => {
        const pack = game.packs.get('sf2e.iconics');
        const idx = await pack.getIndex({fields: ['type', 'system.details.level.value']});
        const out = [];
        for (const e of idx.filter(e => e.type === 'character' && e.system?.details?.level?.value === 7)) {
            const d = await pack.getDocument(e._id);
            out.push([d.name, d.class?.name, d.itemTypes.spellcastingEntry.map(s => s.name), d.itemTypes.spell.length, d.itemTypes.weapon.map(w => w.name)]);
        }
        return out; }"""), indent=1))
    b.close()
