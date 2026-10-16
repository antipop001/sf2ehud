"""Weapon sets (PC by flag, NPC by default), item tooltips, and the Treat Wounds fallback label."""
import sys, os, json, base64
sys.path.insert(0, os.path.dirname(__file__))
from _foundry import *
WANT = os.environ.get('SF2E_SMOKE_ACTOR', '')
OUT = os.environ.get("SF2E_SMOKE_OUT", "/tmp")
NOISE = ("hardware acceleration", "GL Driver Message", "GPU stall", "V1 Application framework")
def shot(pg, name):
    data = pg.context.new_cdp_session(pg).send("Page.captureScreenshot", {"format": "png"})["data"]
    p = f"{OUT}/{name}.png"; open(p, "wb").write(base64.b64decode(data)); print("screenshot", p)
with sync_playwright() as pw:
    b, pg, errors = join(pw)
    pg.wait_for_timeout(2000); errors.clear()
    pc = pg.evaluate("""async (want) => {
        const T = (p, ms=6000) => Promise.race([p, new Promise(r => setTimeout(() => r('timeout'), ms))]);
        const actor = game.actors.find(a => a.type === 'character' && (!want || a.name === want));
        const pistol = actor.itemTypes.weapon[0];
        await actor.setFlag('enhancedcombathud', 'weaponSets', {1: {primary: pistol.uuid, secondary: null}});
        const token = canvas.tokens.placeables.find(t => t.actor?.id === actor.id);
        token.control({releaseOthers: true}); ui.ARGON.toggle(true);
        for (let i = 0; i < 60 && !(ui.ARGON._actor?.id === actor.id && ui.ARGON.components.drawer && ui.ARGON.components.weaponSets); i++) await new Promise(r => setTimeout(r, 250)); await new Promise(r => setTimeout(r, 1000));
        const hud = ui.ARGON, out = {};
        const sets = await T(hud.components.weaponSets._getSets());
        out.set1 = sets?.[1] ? [sets[1].primary?.name, sets[1].secondary?.name] : sets;
        const btns = hud.itemButtons ?? [];
        out.buttonItems = btns.map(b => { try { return b.item?.name ?? b.label ?? b.constructor.name; } catch { return '(empty ' + b.constructor.name + ')'; } });
        const tips = {};
        for (const b of btns.filter(b => b.item).slice(0, 25)) {
            try { const t = await T(b.getTooltipData()); tips[b.item.name] = t === 'timeout' ? 'timeout' : {title: t?.title?.replace(/<[^>]+>/g,'').trim(), subtitle: t?.subtitle, props: (t?.properties ?? []).map(p => p.label ?? p), details: (t?.details ?? []).map(d => `${d.label}: ${String(d.value).replace(/<[^>]+>/g,'')}`)}; }
            catch (e) { tips[b.item.name] = 'ERR ' + e; }
        }
        out.tooltips = tips;
        out.treatWoundsLabel = game.i18n.localize('PF2E.Actions.TreatWounds.Label');
        out.treatWoundsInPack = !!(await fromUuid('Compendium.sf2e.actions.Item.1kGNdIIhuglAjIp9'));
        out.medicineRank = actor.skills.medicine.rank;
        return out;
    }""", WANT)
    print("PC:", json.dumps(pc, indent=1)[:5000])
    shot(pg, "sf2e_hud_pc_weaponset")
    npc = pg.evaluate("""async () => {
        const T = (p, ms=6000) => Promise.race([p, new Promise(r => setTimeout(() => r('timeout'), ms))]);
        const pack = game.packs.get('sf2e.alien-core-bestiary');
        const idx = await pack.getIndex({fields: ['system.details.level.value']});
        const pick = idx.find(e => (e.system?.details?.level?.value ?? 9) >= 2 && (e.system?.details?.level?.value ?? 9) <= 4) ?? idx.contents[0];
        let actor = game.actors.find(a => a._stats?.compendiumSource === pick.uuid) ?? await game.actors.importFromCompendium(pack, pick._id);
        const scene = game.scenes.active;
        let tok = scene.tokens.find(t => t.actorId === actor.id);
        if (!tok) { const td = await actor.getTokenDocument({x: scene.dimensions.sceneX + 700, y: scene.dimensions.sceneY + 400}); [tok] = await scene.createEmbeddedDocuments('Token', [td.toObject()]); }
        await new Promise(r => setTimeout(r, 1000));
        canvas.tokens.get(tok.id).control({releaseOthers: true}); ui.ARGON.toggle(true);
        await new Promise(r => setTimeout(r, 4000));
        const hud = ui.ARGON;
        const sets = await T(hud.components.weaponSets._getSets());
        return {npc: actor.name, level: actor.level, bound: hud._actor?.name,
                melee: actor.itemTypes.melee.map(m => m.name),
                sets: Object.fromEntries(Object.entries(sets ?? {}).map(([k, v]) => [k, [v.primary?.name ?? null, v.secondary?.name ?? null]])),
                buttons: (hud.itemButtons ?? []).map(b => { try { return b.item?.name ?? b.label ?? b.constructor.name; } catch { return '(empty ' + b.constructor.name + ')'; } })};
    }""")
    print("NPC:", json.dumps(npc, indent=1)[:3000])
    shot(pg, "sf2e_hud_npc")
    print("errors:", json.dumps([e[:400] for e in errors if not any(n in e for n in NOISE)], indent=1))
    b.close()
