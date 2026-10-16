"""Deeper HUD probe on the bound actor: weapon sets, strikes, drawer skills, and live rolls."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from _foundry import *
NOISE = ("hardware acceleration", "GL Driver Message", "GPU stall")
with sync_playwright() as pw:
    b, pg, errors = join(pw)
    pg.wait_for_timeout(2000); errors.clear()
    r = pg.evaluate("""async () => {
        const actor = game.actors.find(a => a.type === 'character');
        const token = canvas.tokens.placeables.find(t => t.actor?.id === actor.id);
        token.control({releaseOthers: true}); ui.ARGON.toggle(true);
        await new Promise(r => setTimeout(r, 4000));
        const hud = ui.ARGON, out = {};
        out.strikes = actor.system.actions.map(s => [s.label, s.item?.type, s.item?.system?.traits?.value, s.ready]);
        out.weapons = actor.itemTypes.weapon.map(w => [w.name, w.id, w.isEquipped, w.system.equipped?.carryType, w.system.equipped?.handsHeld, w.system.traits.value]);
        const ws = hud.components.weaponSets;
        try { out.setData = await Promise.race([ws.getSetData(), new Promise(r => setTimeout(() => r('timeout'), 5000))]); } catch (e) { out.setDataErr = String(e); }
        out.weaponSetFlag = actor.getFlag('enhancedcombathud', 'weaponSets') ?? actor.flags['enhancedcombathud-sf2e'];
        const drawer = hud.components.drawer;
        try { const cats = await Promise.race([drawer.categories, new Promise(r => setTimeout(() => r([]), 5000))]); out.drawer = cats.map(c => [c.categoryName ?? c.title ?? '?', (c.buttons ?? []).length]); } catch (e) { out.drawerErr = String(e); }
        out.skills = Object.keys(actor.skills);
        out.mainButtons = (hud.components.main ?? []).map(p => [p.constructor.name, (p.buttons ?? []).map(b => b.label ?? b.item?.name ?? b.constructor.name)]);
        // live rolls through the same entry points the HUD buttons call
        const rolls = {};
        const roll = async (k, fn) => { try { const m = await Promise.race([fn(), new Promise((_, rej) => setTimeout(() => rej(new Error('timeout 8s (dialog?)')), 8000))]); rolls[k] = m ? 'ok' : 'no-message'; } catch (e) { rolls[k] = 'ERR ' + e; } document.querySelectorAll('dialog, .application.dialog').forEach(d => d.querySelector('[data-action=close], .header-control.close')?.click()); };
        await roll('skill:computers', () => actor.skills.computers?.check.roll({skipDialog: true}));
        await roll('skill:piloting', () => actor.skills.piloting?.check.roll({skipDialog: true}));
        await roll('save:fortitude', () => actor.saves.fortitude.check.roll({skipDialog: true}));
        await roll('perception', () => actor.perception.check.roll({skipDialog: true}));
        const s0 = actor.system.actions[0];
        if (s0) await roll('strike:' + s0.label, () => s0.variants[0].roll({skipDialog: true}));
        await roll('action:step', () => game.pf2e.actions.get('step').toActionVariant({actors: actor}).toMessage());
        await roll('action:take-cover-msg', () => game.pf2e.actions.get('take-cover').toActionVariant({actors: actor}).toMessage());
        out.rolls = rolls;
        out.sf2eOnlyActions = ['access-infosphere','hack','operate-device','navigate','plot-course','stunt','drive','take-control','run-over','stop','area-fire','auto-fire'].map(s => [s, !!game.pf2e.actions.get(s)]);
        return out;
    }""")
    print(json.dumps(r, indent=1)[:6000])
    print("errors:", json.dumps([e for e in errors if not any(n in e for n in NOISE)], indent=1))
    b.close()
