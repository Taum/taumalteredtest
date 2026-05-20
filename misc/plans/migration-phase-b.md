# Phase B: Full modern BGA stack (PHP + JavaScript contract)

## Goal

Align **taumalteredtest** with the Board Game Arena **GameFramework** pattern used in bga-dojoless and the modern Studio template: PHP `Game` extends `\Bga\GameFramework\Table`, states as PHP classes, JS `export class Game` with `this.bga`, and ESM build to `modules/js/Game.js`.

**Prerequisite:** Phase A complete (or far enough that UI logic lives in maintainable TS modules without Dojo). Phase B is a **coordinated** PHP + JS migration; doing JS-only modern APIs before PHP is ready will break production.

**References:**

- `C:\Users\taumx\Documents\GitHub\bga-dojoless` (target architecture)
- `C:\Users\taumx\Documents\GitHub\backup-altered-preprod-bga-start` (minimal modern skeleton)
- Phase A plan: `misc/plans/migration-phase-a.md`

---

## Contract change summary

| Area | After Phase A (legacy) | After Phase B (modern) |
|------|------------------------|-------------------------|
| PHP base | `class taumalteredtest extends Table` | `class Game extends \Bga\GameFramework\Table` |
| States | `states.inc.php` + `st*` in traits/actions | `modules/php/States/*.php` extends `GameState` |
| Actions | `taumalteredtest.action.php` → `actFoo()` | `#[PossibleAction] function action_foo()` on state/game |
| JS entry | `taumalteredtest.js` AMD + `declare` | `modules/js/Game.js` ESM `export class Game` |
| JS ↔ state | `onEnteringStateDiscard` on game object | `bga.states.register('Discard', discardState)` |
| JS → server | `ajaxcall(…/actConfirmTurn.html)` | `bga.actions.performAction('action_confirmTurn', args)` |
| Notifications | `_notifications` + `dojo.subscribe` | `bga.notifications.setupPromiseNotifications()` |
| UI chrome | `addPrimaryActionButton`, custom bars | `bga.statusBar`, `bga.gameArea`, `bga.dialogs` |
| Config | `gameinfos.inc.php`, `stats.inc.php` | `gameinfos.jsonc`, `stats.jsonc` (where Studio expects) |
| Counters | `ebg.counter` on gamegui | `counterFactory` / `ebg.counter` via framework |

Notification **type strings** can often stay the same (`playCard`, `refreshUI`, …) if PHP `$this->notify->all('playCard', …)` matches existing `notif_playCard` — but registration and timing logic change.

---

## Out of scope / defer

- Rewriting game rules or engine semantics (port behavior, don’t redesign)
- Changing database schema unless Framework requires `DBPREFIX_` audit
- Renaming game slug `taumalteredtest` on BGA (high coordination cost)
- Altered-specific card PHP classes (stay as-is; only wiring changes)

---

## Target end state (Phase B)

```
taumalteredtest/
├── package.json
├── tsconfig.json
├── rollup.config.mjs              # input: src/Game.ts → modules/js/Game.js (ESM)
├── bga-framework.d.ts             # copy/adapt from bga-dojoless
├── gameinfos.jsonc / stats.jsonc  # migrated from .inc.php where required
├── modules/
│   ├── js/Game.js                 # built; platform entry
│   └── php/
│       ├── Game.php               # GameFramework\Table
│       ├── States/                # one class per major state / group
│       └── ...                    # existing ALT\ logic called from Game
├── src/
│   ├── Game.ts
│   ├── states/                    # PlayerTurn-style TS state classes
│   ├── Cards.ts / Players.ts / …  # from Phase A modules
│   └── tests/
└── states.inc.php                 # REMOVED or reduced to stub (per Studio docs)
```

Studio must load **modern** JS entry (`modules/js/Game.js`). Confirm with current Studio docs for your project type before deleting `taumalteredtest.js`.

---

## Prerequisites

1. **Phase A** — TS modules, no Dojo in app code, notification inventory documented.
2. **Studio access** — GameFramework-enabled project (same as bga-dojoless template).
3. **Inventory spreadsheets:**
   - All states in `states.inc.php` (id, name, type, possibleaction, transitions)
   - All `act*` in `taumalteredtest.action.php`
   - All `notifyAllPlayers` / `notifyPlayer` types in `modules/php/Core/Notifications.php` and call sites
   - All `onEnteringState*` / `onLeavingState*` in JS
4. **Test plan** — automated PHP tests (bga-dojoless style) + manual smoke paths per phase.
5. **Feature branch** — `migration/phase-b`; consider Studio “dev” game copy.

---

## Phase B sub-phases

### B0 — Framework shell (PHP + empty modern JS)

**Duration:** ~3–5 days  
**Risk:** High (game won’t run until B1+)

1. Add `bga-framework.d.ts`, `package.json`, Rollup → `modules/js/Game.js`.
2. Create `modules/php/Game.php` extending `\Bga\GameFramework\Table` in namespace `Bga\Games\taumalteredtest` (or Studio-assigned namespace).
3. Minimal `src/Game.ts`: `export class Game { constructor(bga) { … } setup() {} }`.
4. Wire `getAllDatas(int $currentPlayerId)` to delegate to existing `localGetAllDatas()` logic (adapter on old `Table` or move methods incrementally).
5. Keep **legacy** `taumalteredtest.game.php` as thin wrapper OR parallel until cutover — follow Studio migration guide for your version.
6. Migrate `gameinfos` / `stats` to jsonc if required by template.

**Done when:** empty game loads on Studio with modern JS entry; no rules yet.

---

### B1 — State machine migration (PHP)

**Duration:** ~2–4 weeks  
**Risk:** Highest

`states.inc.php` is large (~600+ lines). Do **not** big-bang in one commit.

#### Strategy: strangle by state group

1. List states by **feature area** (setup, deck selection, day/turn, engine, end game).
2. For each group, create `modules/php/States/<Name>.php`:
   - `id`, `type` (`StateType::ACTIVE_PLAYER`, `GAME`, `MULTIPLE_ACTIVE_PLAYER`, …)
   - `description` / `descriptionMyTurn` (clienttranslate)
   - `transitions` matching old machine
   - `getArgs()` — port from PHP `arg*` / engine args
   - `#[PossibleAction]` methods — port from `act*` + `st*` where applicable
3. Register states in Framework (per bga-dojoless / `_ide_helper.php` patterns).
4. Remove migrated entries from `states.inc.php` only when Framework owns them.

#### Mapping table (template — fill during B1)

| states.inc.php `name` | PHP class | JS state class `register()` | Notes |
|----------------------|-----------|----------------------------|--------|
| `gameSetup` | `GameSetup` | optional | manager state |
| `selectPrecoDeck` | `SelectPrecoDeck` | `SelectPrecoDeckState` | inactive UI list in JS |
| `playerTurn` | … | … | |
| `discard` | … | … | maps from `onEnteringStateDiscard` |
| … | … | … | |

#### Engine / custom turn order

`taumalteredtest.game.php` has `initCustomTurnOrder`, engine traits — map to Framework equivalents or keep internal until sub-states are stable. Document any behavior that **does not** map 1:1 to `GameState` transitions.

#### Action rename map (template)

| Legacy `act*` | Modern `action_*` | State class |
|---------------|-------------------|-------------|
| `actConfirmTurn` | `action_confirmTurn` | … |
| `actFirstDayManaSelection` | `action_firstDayManaSelection` | … |
| … | … | … |

Update **every** JS `ajaxcall` when B3 completes (or use temporary PHP aliases that accept both names during bridge).

**Done when:** all states run on PHP classes; `states.inc.php` deleted or stub; game playable on Studio with **legacy JS** still calling `act*` via bridge — optional intermediate.

---

### B2 — Action layer cutover (PHP)

**Duration:** ~1 week (overlaps B1)  
**Risk:** High

1. Deprecate `taumalteredtest.action.php` methods as logic moves to `GameState` / `Game`.
2. Implement `#[PossibleAction]` with same validation as old `act*` (reuse `ALT\` managers).
3. Ensure `possibleaction` lists in states match registered action names.
4. Add PHP unit tests (`modules/php/Tests/`) for critical actions (pass, play card, deck confirm).

**Done when:** no required `action.php` endpoints for normal play; `performAction` works from minimal modern JS test buttons.

---

### B3 — JavaScript contract migration

**Duration:** ~2–3 weeks  
**Risk:** Medium–high

Depends on Phase A module split.

1. **`src/Game.ts`**
   - `constructor(bga: Bga)` — store `this.bga`, compose modules (`Cards`, `Players`, …).
   - `setup(gamedatas)` — port from current `setup`.
   - `get player_id()` → `gameui.player_id` (bga-dojoless pattern).
   - `bgaFormatText` — port notification arg decoration from `Core/game.js` if used.

2. **State classes** (`src/states/`)
   - One TS class per registered PHP state name.
   - Move `onEnteringStateXxx` / `onLeavingStateXxx` bodies from mixins into state classes.
   - `this.bga.statusBar.addActionButton` replaces `addPrimaryActionButton` where appropriate.
   - `this.bga.actions.performAction('action_*', args)` replaces `ajaxcall`.

3. **Notifications**
   - Remove `_notifications` array and `dojo.subscribe` setup.
   - `this.bga.notifications.setupPromiseNotifications({ … })`.
   - Convert `notif_*` to async where animations need promises; respect `bgaAnimationsActive()` / replay mode.
   - Re-test durations (old ms return values → promise + `minDuration` config).

4. **UI**
   - Replace `customgame.modal` with `bga.dialogs` or framework `PopinDialog` where possible.
   - `bga.gameArea.getElement()` for main layout injection.
   - `bga.playerPanels` for panel counters.

5. **Delete** legacy entry:
   - `taumalteredtest.js` AMD `define`
   - `dojo/_base/declare` mixins
   - `modules/js/Core/game.js` legacy `customgame.game` if fully superseded

6. **Vendor libs** — load via `importEsmLib` / npm where Studio recommends (tippy, nouislider).

**Done when:** Studio loads only `modules/js/Game.js`; full smoke path passes.

---

### B4 — Notifications & engine polish

**Duration:** ~1 week  
**Risk:** Medium

1. Cross-check every PHP `notify->all` type has `notif_*` on `Game`.
2. Fix race conditions (notification order vs state change).
3. Port log CSS classes / undo UI to modern hooks.
4. Performance: batch DOM updates in `refreshUI` / `refreshCard`.

---

### B5 — Config, stats, preferences, deploy

**Duration:** ~3–5 days  
**Risk:** Low–medium

1. `gamepreferences.jsonc` — map from `gamepreferences.json`.
2. `stats.jsonc` — map from `stats.inc.php`.
3. Update SFTP/deploy paths if entry file name changes.
4. Update `misc/python-tools/rename-game-slug.py` if slug ever changes (optional).
5. Documentation for contributors: build, watch, test commands.

---

## PHP namespace / code reuse

Keep heavy logic in existing `ALT\` modules where possible:

```php
// Target pattern
namespace Bga\Games\taumalteredtest\States;

use Bga\Games\taumalteredtest\Game;
use ALT\Managers\Cards; // via Game adapter

class Discard extends GameState {
    public function __construct(protected Game $game) { … }

    #[PossibleAction]
    public function action_confirmDiscard(int $active_player_id, array $card_ids): string {
        // delegate to ALT\Actions\Discard or engine
        return 'next';
    }
}
```

Add a thin `Game` wrapper that exposes `ALT\Core\Game::get()` if needed during transition.

---

## JavaScript mapping from Phase A modules

| Phase A module | Phase B home |
|----------------|--------------|
| `src/modules/Cards.ts` | Methods on `Game` + `CardNotifs` helpers, or `CardsUI` class used by `Game` |
| `src/modules/Players.ts` | `PlayersUI` + setup in `Game.setup` |
| `src/modules/Meeples.ts` | `MeeplesUI` + `notif_*` on `Game` delegating |
| `src/dom.ts` | Keep; no `bga` dependency |
| `src/states/*.ts` | State-specific UI only |
| `MainGame.ts` content | Split into `Game` + state classes |

---

## Verification checklist (Phase B)

### PHP

- [ ] All states reachable; no orphan transitions
- [ ] Zombie modes for active-player states
- [ ] `getAllDatas` parity with pre-migration (field-by-field diff tool)
- [ ] PHPUnit green for core actions
- [ ] Multiplayer / simultaneous states (`MULTIPLE_ACTIVE_PLAYER`)

### JavaScript

- [ ] `export class Game` loads; no AMD errors
- [ ] Every `performAction` name exists as `#[PossibleAction]`
- [ ] Every notification type handled
- [ ] F5, replay, archive, spectator
- [ ] Preferences apply correctly
- [ ] Mobile + desktop layouts

### Integration

- [ ] Full game: setup → deck → several days → combat → end
- [ ] Undo (if supported)
- [ ] Tiebreaker mode
- [ ] Beginner mode / tutorials if applicable

---

## Rollback strategy

1. Maintain `migration/phase-a` tag until B3 verified.
2. Studio: keep duplicate “legacy” game project on BGA if available.
3. During B1–B2, optional **dual action** period: PHP accepts both `actFoo` and `action_foo` (thin wrappers) — remove after JS cutover.
4. Do not delete `states.inc.php` from git until production sign-off.

---

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| State machine parity bugs | State-by-state migration; log transitions in dev |
| Notification timing regressions | Table of old durations → `setupPromiseNotifications` params |
| Engine complexity (`ALT\Core\Engine`) | Keep engine PHP intact; only change state entry/exit wiring first |
| Studio template drift | Pin docs date; diff against bga-dojoless quarterly |
| Long feature freeze | Migrate by vertical slice (e.g. “setup only” game playable) |

---

## Success criteria (Phase B complete)

1. No `states.inc.php` machine (or documented exception).
2. No `taumalteredtest.action.php` for gameplay (archive/reference only).
3. JS is `src/Game.ts` → `modules/js/Game.js` with `this.bga` API only.
4. PHP is `GameFramework\Table` + `States/*`.
5. Production Studio game runs full Altered rules without legacy contract shims.
6. Contributor docs: `npm run build`, `npm test`, PHP `composer test` if added.

---

## Estimated effort

| Sub-phase | Calendar (part-time) |
|-----------|----------------------|
| B0 Shell | 3–5 days |
| B1 States (PHP) | 2–4 weeks |
| B2 Actions | 1 week (overlap) |
| B3 JS contract | 2–3 weeks |
| B4 Polish | 1 week |
| B5 Config/deploy | 3–5 days |
| **Total** | **~8–12 weeks** after Phase A |

---

## Suggested order of execution

```
Phase A complete
    → B0 (shell)
    → B1 slice: setup + deck selection states only → B3 partial JS for those states
    → B1 slice: main turn / engine states
    → B1 end game + B2 action cleanup
    → B3 full JS cutover
    → B4–B5
```

Vertical slices deliver a playable game earlier than “all PHP then all JS.”

---

## Related files in this repo (audit before B1)

| File | Role in migration |
|------|-------------------|
| `states.inc.php` | Source of truth until B1 |
| `taumalteredtest.game.php` | Port to `modules/php/Game.php` |
| `taumalteredtest.action.php` | Action inventory → `#[PossibleAction]` |
| `modules/php/Core/Notifications.php` | Notify API → `$this->notify->` |
| `modules/php/States/*Trait.php` | `st*` methods → state classes |
| `taumalteredtest.js` | Replace with `src/Game.ts` |
| `modules/js/Core/game.js` | Notifications, tooltips → `Game` / `bga` |
| `misc/python-tools/extract-starter-decks.py` | Keep generating `StarterDecks` TS block |

---

## After Phase B

- Optional: stricter TypeScript (`strict: true`), shared types generated from PHP
- Optional: E2E on Studio staging
- Remove `bga-legacy.d.ts` and any `customMixin` bridge code from Phase A experiments
