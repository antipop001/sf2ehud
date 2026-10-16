"""Spell panels on a caster: categories, uses, tooltips, and casting through the HUD's own click actions.
Usage: SF2E_SMOKE_ACTOR="Zemir (Level 10)" probe_spells.py"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from _foundry import *
WANT = os.environ.get('SF2E_SMOKE_ACTOR', '')
NOISE = ("hardware acceleration", "GL Driver Message", "GPU stall", "V1 Application framework")
with sync_playwright() as pw:
    b, pg, errors = join(pw)
    pg.wait_for_timeout(2000); errors.clear()
    r = pg.evaluate("""async (want) => {
        const T = (p, ms=8000) => Promise.race([Promise.resolve(p), new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), ms))]);
        const actor = game.actors.find(a => a.type === 'character' && (!want || a.name === want));
        canvas.tokens.placeables.find(t => t.actor?.id === actor.id).control({releaseOthers: true});
        ui.ARGON.toggle(true); for (let i = 0; i < 60 && !(ui.ARGON._actor?.id === actor.id && ui.ARGON.components.drawer && ui.ARGON.components.weaponSets); i++) await new Promise(r => setTimeout(r, 250)); await new Promise(r => setTimeout(r, 1000));
        const out = {actor: actor.name, level: actor.level, panels: {}};
        const spellButtons = [];
        const collect = (o, panelName, seen = new Set()) => {
            if (!o || typeof o !== 'object' || seen.has(o)) return; seen.add(o);
            if (o.constructor?.name === 'PF2EButtonPanelButton' && o.type === 'spell') { spellButtons.push([panelName, o]); return; }
            for (const k of ['_buttons', 'buttons', 'button1', 'button2']) { const v = o[k]; if (Array.isArray(v)) v.forEach(x => collect(x, panelName, seen)); else if (v) collect(v, panelName, seen); }
        };
        for (const p of ui.ARGON.components.main) { try { const bs = await T(p._getButtons()); (bs ?? []).forEach(x => collect(x, p.constructor.name)); } catch (e) { out.panels[p.constructor.name] = 'getButtons ERR ' + e; } }
        out.spellButtonPanels = spellButtons.map(([n]) => n);
        let firstCantrip = null, firstRank1 = null;
        for (const [panelName, btn] of spellButtons) {
            try {
                const cats = await T(btn.sortedSpells());
                out.panels[panelName] = cats.map(c => {
                    let uses; try { uses = typeof c.uses === 'function' ? c.uses() : c.uses; } catch (e) { uses = 'ERR ' + e; }
                    const names = (c.buttons ?? []).map(b => b.item?.name);
                    for (const sb of c.buttons ?? []) {
                        if (!firstCantrip && sb.item?.isCantrip && sb._clickAction) firstCantrip = sb;
                        if (!firstRank1 && sb.item && !sb.item.isCantrip && !sb.item.isFocusSpell && sb.item.rank === 1 && sb._clickAction) firstRank1 = sb;
                    }
                    return {label: c.label, uses, n: names.length, spells: names.slice(0, 8)};
                });
                out.visible = out.visible ?? {}; out.visible[panelName] = btn.isvalid ?? btn.visible;
            } catch (e) { out.panels[panelName] = 'ERR ' + e; }
        }
        // tooltip for one spell of each kind
        out.tooltips = {};
        for (const sb of [firstCantrip, firstRank1].filter(Boolean)) {
            try { const t = await T(sb.getTooltipData()); out.tooltips[sb.item.name] = {title: t?.title?.replace(/<[^>]+>/g, '').trim(), subtitle: t?.subtitle, details: (t?.details ?? []).map(d => `${d.label}: ${String(d.value).replace(/<[^>]+>/g, '')}`)}; }
            catch (e) { out.tooltips[sb.item?.name] = 'ERR ' + e; }
        }
        // cast through the HUD's click action; count chat messages and slot use
        const slots = () => Object.fromEntries(actor.itemTypes.spellcastingEntry.filter(e => e.system.prepared.value === 'spontaneous').flatMap(e => Object.entries(e.system.slots).filter(([, s]) => s.max).map(([k, s]) => [k, s.value])));
        out.casts = {};
        for (const sb of [firstCantrip, firstRank1].filter(Boolean)) {
            const before = game.messages.size, s0 = slots();
            try {
                const run = sb._clickAction();
                // ranked spontaneous spells open the module's "cast at rank" picker (a V1 Dialog); take its default
                await new Promise(r => setTimeout(r, 1200));
                let picker = null;
                const dlg = [...document.querySelectorAll('.app.dialog, .application.dialog')].find(d => d.querySelector('select#inputresult'));
                if (dlg) { picker = [...dlg.querySelectorAll('select#inputresult option')].map(o => o.textContent); dlg.querySelector('button[data-button="accept"]')?.click(); }
                await T(run); await new Promise(r => setTimeout(r, 1500));
                out.casts[sb.item.name] = {picker, messages: game.messages.size - before, slotsBefore: s0, slotsAfter: slots()};
            }
            catch (e) { out.casts[sb.item.name] = 'ERR ' + e; }
        }
        out.focus = actor.system.resources.focus;
        return out;
    }""", WANT)
    print(json.dumps(r, indent=1)[:7000])
    print("errors:", json.dumps([e[:400] for e in errors if not any(n in e for n in NOISE)], indent=1))
    b.close()
