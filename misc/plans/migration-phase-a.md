# Phase A: JavaScript modernization (legacy PHP contract)

## Goal

Improve the client codebase (TypeScript, no Dojo in game code, clearer module structure) **without changing the PHP ↔ JS contract**. The game must keep working on the current BGA Studio setup: `Table`, `states.inc.php`, `taumalteredtest.action.php`, and existing notification/action names.

**References:** current repo layout; [bga-dojoless](../../../bga-dojoless/) `misc/other/customMixin` pattern for optional bridge; **not** the modern `export class Game` path (that is Phase B).

---

## What must not change (frozen contract)

These are the boundaries between layers. Phase A must preserve them byte-for-byte in behavior, not necessarily in implementation.

| Contract | Legacy value (keep) | Do not switch to (Phase B) |
|----------|---------------------|----------------------------|
| JS entry | AMD `define` → `declare('bgagame.taumalteredtest', …)` | `export class Game` in `modules/js/Game.js` only |
| Base class | `ebg.core.gamegui` via `customgame.game` | `this.bga` / `GameFramework` JS API |
| Player actions | `this.ajaxcall('/taumalteredtest/taumalteredtest/actXxx.html', …)` | `this.bga.actions.performAction('action_xxx', …)` |
| Action names | `actConfirmTurn`, `actFirstDayManaSelection`, … in `taumalteredtest.action.php` | `action_*` on PHP `GameState` classes |
| Notifications | Type strings in `_notifications` + `notif_<type>` handlers | `setupPromiseNotifications()` only (can emulate timing manually) |
| Notification wiring | `dojo.subscribe` in `setupNotifications()` | Auto-registration without equivalent sync/duration behavior |
| State UI hooks | `onEnteringState` → `onEnteringState<Name>` on game object | `bga.states.register('Name', …)` |
| State names | Names in `states.inc.php` (`discard`, `nightCleanup`, …) | Renamed states unless PHP updated in Phase B |
| Initial data | `setup(gamedatas)` shape from `getAllDatas()` | New keys without PHP |
| Game slug / URLs | `taumalteredtest` paths in ajax and theme | Renamed game folder without coordinated deploy |

### `gamedatas` fields (read-only from JS perspective)

Document and treat as API (add `src/types/gamedatas.d.ts` or JSDoc):

- `prefs`, `players`, `cards`, `meeples`, `undo`, `beginner`
- `firstPlayer`, `passedPlayers`, `storm`, `day`, `phase`, `tieBreaker`
- `movements`, `biomes`, `blockedExpeditions`, `powersBlockedExpeditions`, `defenders`, `reserveSlots`, `landmarkSlots`

### Notification inventory

Maintain parity with `taumalteredtest.js` constructor `_notifications` (~50 entries) and every `notif_*` in:

- `taumalteredtest.js`
- `modules/js/Cards.js`, `Players.js`, `Meeples.js`
- Any handler in `modules/js/Core/game.js`

Before refactors, generate a checklist (name, duration, optional filter) and verify after each milestone.

---

## Out of scope for Phase A

- Migrating `taumalteredtest.game.php` to `GameFramework\Table`
- Replacing `states.inc.php` with `modules/php/States/*`
- Renaming `act*` actions or notification types
- Switching entry file to BGA “modern” `modules/js/Game.js` as sole loader (unless Studio documents dual support for your project)
- Removing `ebg/counter` or `dijit` until replacements are wired and tested
- PHP unit test migration (optional later)

---

## Target end state (Phase A)

```
taumalteredtest/
├── package.json
├── tsconfig.json
├── rollup.config.mjs          # or esbuild — outputs AMD-compatible bundle
├── bga-legacy.d.ts              # $, _, gameui, ebg, dojo (minimal), g_gamethemeurl
├── src/
│   ├── entry.ts                 # define([...], () => declare(...))
│   ├── dom.ts                   # replace dojo.place, style, query, connect
│   ├── mixins/ or modules/
│   │   ├── CoreGame.ts          # from Core/game.js
│   │   ├── Modal.ts
│   │   ├── Cards.ts
│   │   ├── Players.ts
│   │   ├── Meeples.ts
│   │   ├── StarterDecks.ts
│   │   └── MainGame.ts          # from taumalteredtest.js body
│   └── types/
│       └── gamedatas.d.ts
├── modules/js/                  # built output OR gradual hand-migrated .js
└── taumalteredtest.js           # final AMD entry (built or thin re-export)
```

Runtime behavior: identical to today on Studio/production for a full game (setup, several states, notifications, undo if used).

---

## Prerequisites

1. **SFTP / deploy** — `npm run watch:ts` (or build) uploads to Studio; confirm which file BGA loads (`taumalteredtest.js` vs `modules/js/*`).
2. **Node.js** — LTS, `npm i` in repo root.
3. **Baseline** — note current game version on Studio; one scripted “smoke path” (new game → deck select → one turn → one card play → refresh F5).
4. **Branch** — `migration/phase-a` off main.

---

## Milestone 0: Tooling (no behavior change)

**Duration:** ~1–2 days  
**Risk:** Low

1. Add `package.json`, `tsconfig.json`, `rollup.config.mjs` (mirror bga-dojoless; output **AMD** or IIFE that assigns to existing `define` pattern).
2. Add `bga-legacy.d.ts` — declare `$`, `_`, `g_gamethemeurl`, `ebg`, `gameui`, minimal `dojo` only if still referenced in glue.
3. Configure build to emit to a **staging file** first (e.g. `taumalteredtest.built.js`) and load only on `?dev=1` or after manual rename — avoid breaking Studio until verified.
4. Add scripts: `build:ts`, `watch:ts`, optional `typecheck`.
5. Document in this folder: `misc/plans/README.md` one paragraph pointing to Phase A/B.

**Done when:** `npm run build:ts` succeeds; game still runs from **unchanged** `taumalteredtest.js`.

---

## Milestone 1: DOM helper layer

**Duration:** ~2–3 days  
**Risk:** Low–medium

Create `src/dom.ts` and use it in all new/edited code:

| Dojo | Replacement |
|------|-------------|
| `dojo.place(node, ref, pos)` | `place(el, parent, position)` using `insertAdjacentHTML` / `appendChild` / `replaceWith` |
| `dojo.query(sel)` | `document.querySelectorAll` |
| `dojo.style` | `el.style` / `setStyle(el, props)` |
| `dojo.addClass` / `removeClass` / `toggleClass` | `classList` |
| `dojo.connect` / `disconnect` | `on(el, event, fn)` returning `{ remove() }`; track in `_connections[]` |
| `dojo.empty` | `el.replaceChildren()` or `innerHTML = ''` |
| `dojo.destroy` | `el.remove()` |
| `dojo.clone` | `el.cloneNode(true)` |
| `dojo.attr` | `setAttribute` / `dataset` |
| `dojo.string.substitute` | template literal or small `${key}` replacer |
| `dojo.position` / `marginBox` | `getBoundingClientRect()` (+ scroll if needed) |
| `dojo.xhrGet` | `fetch` (keep CSRF/query params as `ajaxcall` does) |

**Do not** replace `this.ajaxcall` — keep framework method.

**Pilot order:**

1. `modules/js/StarterDecks.js` (tiny)
2. `modules/js/Meeples.js` (`dojo.place` only)
3. `modules/js/Players.js`
4. `modules/js/Core/modal.js` (FX last in modal — see Milestone 3)

**Done when:** pilot files use `dom.ts`; smoke path passes.

---

## Milestone 2: TypeScript + module split (still legacy declare)

**Duration:** ~1–2 weeks  
**Risk:** Medium

### Option A — Incremental (recommended)

Keep shipping concatenated/legacy files; convert one file at a time to TS, compile to same path under `modules/js/`.

### Option B — Single bundle

`src/entry.ts` imports all modules; Rollup outputs one AMD module list matching current `define([...])` dependencies.

### Mixin strategy (pick one)

1. **Keep `declare` mixins** — TS types the mixin object; least churn.
2. **`customMixin` bridge** (bga-dojoless `misc/other/dojoless-orig.js`) — ES classes copied onto `gamegui` instance; `dest.super` for overrides; still one `declare('bgagame.taumalteredtest', [ebg.core.gamegui], { constructor() { customMixin(this, composed); } })`.

### File migration order

| Order | Source | Notes |
|------|--------|--------|
| 1 | `StarterDecks.js` | Autogenerated block — keep Python extractor compatible |
| 2 | `Meeples.js` | Small |
| 3 | `Players.js` | MutationObservers already modern |
| 4 | `Core/modal.js` | Depends on FX milestone |
| 5 | `Core/game.js` | Notifications, tooltips, slide animations |
| 6 | `Cards.js` | Largest; split internal helpers first |
| 7 | `taumalteredtest.js` | Main + `_notifications` list |

**Done when:** all app JS typechecks; Studio runs from built artifacts; no `dojo.*` in `src/` except optional glue in `entry.ts`.

---

## Milestone 3: Replace Dojo FX and Dijit

**Duration:** ~3–5 days  
**Risk:** Medium (visual regressions)

1. **`Core/modal.js`** — Replace `dojo.fadeIn/Out`, `dojo.animateProperty`, `dojo.fx.combine` with CSS transitions or Web Animations API; drop `dojox/fx/ext-dojo/complex` dependency.
2. **`Core/game.js` — `slideToObject` / `slideToObjectAndDestroy`** — `transform` + `requestAnimationFrame` or CSS; preserve phantom-node behavior used by cards/meeples.
3. **Tooltips** — Replace `dijit.Tooltip` with existing **Tippy** vendor lib (already in `game.js` deps); port help-mode behavior (`_helpMode`, instant show).
4. **Leave `ebg/counter`** until Phase B unless you verify counter API without dijit.

**Done when:** no `dijit` / `dojo/fx` / `dojox` in `define()` dependency array; animations acceptable on desktop + mobile.

---

## Milestone 4: Notifications hardening (still legacy wiring)

**Duration:** ~2–3 days  
**Risk:** Medium (timing bugs)

Do **not** switch to `setupPromiseNotifications()` unless you replicate:

- Per-type durations from `_notifications`
- `notifqueue.setSynchronous` / `setSynchronousDuration` / `dojo.publish('notifEnd')` behavior
- Filter predicates (e.g. `drawCards` only for current player)
- Title bar / `gameaction_status` updates in wrapper (`Core/game.js` `setupNotifications`)

Tasks:

1. Export `_notifications` to a typed `notifications.config.ts` for documentation.
2. Add dev-only logger: log notif type, duration, handler return value.
3. Optionally wrap handlers to return `Promise` while still calling legacy `setSynchronousDuration` — preparatory for Phase B, not required.

**Done when:** full game night/day cycle with no stuck “waiting for notification” or double-speed skips.

---

## Milestone 5: Tests and CI (optional but valuable)

**Duration:** ~3–5 days  
**Risk:** Low

Copy pattern from bga-dojoless `src/tests/`:

- `setup.ts` stubs `$`, `_`, `gameui`, `ebg`, `define`
- Unit tests for `dom.ts`, `formatString`, card container helpers, starter deck meta
- No PHP changes

**Done when:** `npm test` runs locally; critical pure functions covered.

---

## Verification checklist (every milestone)

- [ ] New game loads; `setup(gamedatas)` renders boards
- [ ] F5 refresh restores state
- [ ] At least one `act*` from UI succeeds (network 200, state advances)
- [ ] Notifications: card draw, move, tap, phase change (pick 5 from inventory)
- [ ] Spectator / replay / archive if you support them (`isReadOnly()` paths)
- [ ] Mobile layout (viewport, hands, modals)
- [ ] Undo path if enabled
- [ ] No console errors from missing `dojo` / `dijit`

---

## Rollback

- Keep `taumalteredtest.js` backup tag per milestone.
- Build artifact optional: ship unbundled `modules/js/*.js` until stable.
- One milestone per PR for bisect.

---

## Success criteria (Phase A complete)

1. **Zero** `dojo.place` / `connect` / `query` / FX in application source (`src/`).
2. TypeScript build is the source of truth for UI JS.
3. **No PHP file changes** required for deploy.
4. All legacy contract items in the table above unchanged.
5. Smoke path + one full 2-player game on Studio without regression reports.

---

## Estimated effort

| Milestone | Calendar (part-time) |
|-----------|----------------------|
| 0 Tooling | 1–2 days |
| 1 DOM helpers | 2–3 days |
| 2 TS + modules | 1–2 weeks |
| 3 FX / tooltips | 3–5 days |
| 4 Notifications | 2–3 days |
| 5 Tests | 3–5 days |
| **Total** | **~4–6 weeks** part-time |

---

## After Phase A

Phase B migrates PHP to `GameFramework\Table` and swaps the JS contract to `export class Game` + `this.bga`. See `misc/plans/migration-phase-b.md`.

Phase A deliverables that **ease Phase B**:

- Typed `gamedatas` and notification names
- Pure DOM/animation utilities reusable in modern `Game`
- Modules already split (`Cards`, `Players`, …) map to composition or state classes
