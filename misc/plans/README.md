# Migration plans (BGA UI / framework)

Plans for moving **taumalteredtest** from the legacy Dojo + `declare` + `Table` stack to the modern BGA GameFramework pattern (as in [bga-dojoless](https://github.com/laskav/bga-dojoless)).

| Document | Scope |
|----------|--------|
| [migration-phase-a.md](./migration-phase-a.md) | **JS only** — TypeScript, remove Dojo, keep legacy PHP contract (`act*`, `states.inc.php`, `_notifications`, `ajaxcall`) |
| [migration-phase-b.md](./migration-phase-b.md) | **PHP + JS** — `GameFramework\Table`, PHP state classes, `export class Game`, `this.bga` |

Phase B depends on Phase A (or equivalent module cleanup). Do not adopt the modern JS contract before PHP is ready.
