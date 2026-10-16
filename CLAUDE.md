# CLAUDE.md — sf2ehud (Argon Combat HUD, Starfinder 2e port)

Shared conventions live in `~/CLAUDE.md` (drive layout, `agy`, Ralph loops). This file is only what is specific here.

- **What:** fork of `Saibot393/enhancedcombathud-pf2e` v4.0.2, retargeted to the Foundry `sf2e` system. Module id `enhancedcombathud-sf2e`. Work branch `sf2e`; `origin` = `antipop001/sf2ehud`, `upstream` = Saibot393.
- **Key fact:** the sf2e system is built from the `foundryvtt/pf2e` repo, so `game.pf2e.*` and `PF2E.*` lang keys work unchanged. Anything keyed on the system id (settings namespace, `flags.<id>`, `systems/<id>/` paths, the actions pack) must go through `game.system.id` or the `systemPath()` / `actionUUID()` helpers in `scripts/utils.js`. Never write the literal `"pf2e"` for those.
- **Rules authority:** NotebookLM "SF2E" `758a4ef0-88a2-49a8-bdba-bdad34058dcd` (use `nlm notebook query`; the `notebooklm` CLI hit a CSRF error 2026-10-16) and https://2e.aonsrd.com/.
- **Starfinder 1e HUD (`Saibot393/enhancedcombathud-sfrpg`) is an aesthetics source only** (operator's rule, 2026-10-16): icons, colours, styling. Never take rules, actions, weapon-set behaviour or mechanics from it; SF1e rules differ from SF2e. Its CSS and `WeaponSets.hbs` encode SF1e's single-slot weapon sets, so they count as rules. Credit any borrowed icon in `icons/LICENSE.md`.
- **No build step.** Plain ES modules; the gate is `node --check` on every script plus JSON validation, which `tools/deploy_smoke.sh` runs before deploying.

## Smoke server (foundrySB, CT 211 — shared with rt/wfvtt; details in `~/wfvtt/CLAUDE.md` §3)

- World **`sf2e-smoketest`**, system sf2e 1.6.1, Foundry 14.369, GM seat `Gamemaster` (no password). Argon core `enhancedcombathud` 5.0.1 is installed and enabled.
- Deploy: `tools/deploy_smoke.sh` (syntax gate → rsync → restart). **A restart drops the world to /setup**; relaunch with
  `set -a; . ~/.config/wfvtt-smoke; set +a; WF_SMOKE_WORLD=sf2e-smoketest ~/.venvs/playwright/bin/python ~/wfvtt/tools/launch_smoke_world.py`
- Tests: `PLAYWRIGHT_BROWSERS_PATH=/mnt/project_data/playwright ~/.venvs/playwright/bin/python tests/e2e/<script>.py`
  - `smoke_hud.py [iconic]` enables the module, imports an iconic (default: lowest level), binds Argon, reports page errors, screenshots.
  - `probe_hud_detail.py` strikes/skills drawer/live rolls; `probe_sets_npc.py` weapon sets, tooltips, an NPC bind.
  - `probe_spells.py` spell panels per action cost, slot/focus uses, tooltips, and casts through the HUD's own click actions (consumes slots; restore afterwards).
  - **Target a specific actor** with `SF2E_SMOKE_ACTOR="<exact world actor name>"`; otherwise the probes use the first character.
  - **Higher levels:** compendium iconics stop at level 7. `setup_leveled.py "Zemir (Level 7)" 10` imports a copy, raises it through the system's level-up path (class features, HP) and places its token. Spell slots, skill ranks, feats and gear stay at the source level: those are build choices, not something to invent. `list_iconics.py` / `iconic_classes.py` show what is available.
- **Probe gotcha:** Argon builds panel buttons on demand (`await panel._getButtons()`), not in `_buttons`; a spell button's action is `_clickAction`. Bigger actors take longer to bind, so poll for `ui.ARGON._actor` and `components.drawer` instead of a fixed sleep.
- **Gotchas:** v14 join field is `select[name="userId"]` and its options render after networkidle (wait for them). `page.screenshot` hangs on the WebGL canvas headless; capture via CDP `Page.captureScreenshot` (done in the scripts). Argon only binds on token control if enabled: call `ui.ARGON.toggle(true)`. `skipDialog` does not suppress the strike `CheckModifiersDialog`; race rolls with a timeout.
- Player characters start with **empty weapon sets by design** (upstream only auto-fills NPCs); drag weapons in or set `flags.enhancedcombathud.weaponSets`.
