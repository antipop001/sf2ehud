"""Import an iconic and raise it to a target level, then put its token on the active scene.
Usage: setup_leveled.py "<iconic name>" <level>    e.g. setup_leveled.py "Zemir (Level 7)" 10
Prints the world actor's name; pass it to the other scripts via SF2E_SMOKE_ACTOR.
Leveling grants class features through the system's own level-up path; spell slots, equipment and
feat choices stay as the source iconic had them (those are player choices / rules data, not HUD logic)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from _foundry import *
SRC, LEVEL = sys.argv[1], int(sys.argv[2])
with sync_playwright() as pw:
    b, pg, errors = join(pw)
    r = pg.evaluate("""async ([src, level]) => {
        const target = src.replace(/\\(Level \\d+\\)/, `(Level ${level})`);
        let actor = game.actors.getName(target);
        const pack = game.packs.get('sf2e.iconics');
        if (!actor) {
            const entry = (await pack.getIndex()).find(e => e.name === src);
            if (!entry) return {error: 'not found: ' + src};
            actor = await game.actors.importFromCompendium(pack, entry._id, {name: target});
        }
        const snap = a => ({level: a.level, hp: a.hitPoints?.max, items: a.items.size,
            classFeatures: a.itemTypes.feat.filter(f => f.category === 'classfeature').map(f => f.name),
            ranks: Object.fromEntries(Object.entries(a.skills).map(([k, s]) => [k, s.rank])),
            spellEntries: a.itemTypes.spellcastingEntry.map(e => [e.name, Object.entries(e.system.slots ?? {}).filter(([, s]) => s.max).map(([k, s]) => k.replace('slot', 'r') + ':' + s.max).join(' ')]),
            focus: a.system.resources?.focus});
        const before = snap(actor);
        if (actor.level !== level) {
            await actor.update({'system.details.level.value': level});
            await new Promise(r => setTimeout(r, 3000));
        }
        const after = snap(actor);
        const scene = game.scenes.active;
        let tok = scene.tokens.find(t => t.actorId === actor.id);
        if (!tok) { const td = await actor.getTokenDocument({x: scene.dimensions.sceneX + 1000, y: scene.dimensions.sceneY + 400}); [tok] = await scene.createEmbeddedDocuments('Token', [td.toObject()]); }
        return {name: actor.name, before, after,
                addedFeatures: after.classFeatures.filter(f => !before.classFeatures.includes(f))};
    }""", [SRC, LEVEL])
    print(json.dumps(r, indent=1))
    b.close()
