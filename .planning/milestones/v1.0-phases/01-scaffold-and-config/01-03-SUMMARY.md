---
phase: 01-scaffold-and-config
plan: "03"
subsystem: infra
tags: [python, json, questionary, click, config, tdd]

# Dependency graph
requires:
  - phase: 01-scaffold-and-config
    plan: "01"
    provides: "Installable package with xfail test stubs and makenote.__init__/constants"
  - phase: 01-scaffold-and-config
    plan: "02"
    provides: "cli.py click group with first-run detection and config subcommand"
provides:
  - src/makenote/config.py — CONFIG_PATH, config_exists, load_config, save_config, run_config_flow
  - Config persistence at ~/.config/makenote/config.json with auto-created parent dirs
  - Interactive menu-loop config editor supporting set repo, default subject, add/remove subjects, Ctrl-C clean exit
affects: [02-github, 02-note-command, 03-packaging]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Module-level import (import makenote.config as _cfg) in cli.py for pytest monkeypatch compatibility"
    - "run_config_flow menu-loop: questionary.select with Separator(), None-check for Ctrl-C → sys.exit(0)"
    - "save_config with mkdir(parents=True, exist_ok=True) before open() — atomic write with dir creation"

key-files:
  created:
    - src/makenote/config.py
  modified:
    - src/makenote/cli.py

key-decisions:
  - "cli.py changed from direct function imports to module import (_cfg) so pytest monkeypatching of config_exists and run_config_flow works correctly"
  - "run_config_flow checks every .ask() return for None immediately — None signals Ctrl-C, calls sys.exit(0) to avoid traceback"
  - "CONFIG_PATH defined in config.py (canonical source); constants.py retains it for import convenience"

patterns-established:
  - "Monkeypatch-safe imports: use module import (as _cfg) rather than direct function import when test isolation via monkeypatching is required"
  - "Ctrl-C handling: every questionary .ask() call must check for None and call sys.exit(0)"

requirements-completed: [CONF-02, CONF-03, CONF-04, CONF-05, CONF-06]

# Metrics
duration: 5min
completed: 2026-03-09
---

# Phase 1 Plan 03: Config Read/Write and Interactive Flow Summary

**JSON config layer (config_exists, load_config, save_config) plus questionary menu-loop run_config_flow() persisting to ~/.config/makenote/config.json — all 11 Phase 1 tests green**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-09T01:59:46Z
- **Completed:** 2026-03-09T02:04:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- config.py implements CONFIG_PATH, config_exists(), load_config(), save_config() with auto-mkdir
- run_config_flow() implements a menu-loop editor using questionary.select with clean Ctrl-C handling
- All 11 Phase 1 tests xpassed (previously all 11 were xfail)
- mn --version outputs "mn 0.1.0" and mn --help lists the config subcommand

## Task Commits

Each task was committed atomically:

1. **Task 1: Config read/write layer — CONFIG_PATH, config_exists, load_config, save_config** - `e06ad1b` (feat)
2. **Task 2: run_config_flow() and cli.py monkeypatch fix** - `8912546` (feat)

**Plan metadata:** (docs commit to follow)

_Note: TDD tasks — RED phase pre-confirmed (11 xfail stubs from Plan 01), GREEN phase implemented with all 11 xpassed._

## Files Created/Modified
- `src/makenote/config.py` - CONFIG_PATH, config_exists, load_config, save_config, run_config_flow
- `src/makenote/cli.py` - Changed from direct function imports to module import (_cfg) for monkeypatch compatibility

## Decisions Made
- Changed `cli.py` from `from makenote.config import config_exists, run_config_flow` to `import makenote.config as _cfg` — direct imports bind names in cli.py's namespace and bypass pytest monkeypatching of the module-level attributes
- Every `questionary.ask()` return is checked for None immediately and calls `sys.exit(0)` — this satisfies the "Ctrl-C at any prompt exits cleanly without a Python traceback" requirement

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Changed cli.py to use module import instead of direct function imports**
- **Found during:** Task 2 (run_config_flow implementation — test verification)
- **Issue:** tests/test_cli.py monkeypatches `makenote.config.run_config_flow` and `makenote.config.CONFIG_PATH`, but cli.py used `from makenote.config import config_exists, run_config_flow` which binds local names at import time. Monkeypatching the module attribute does not affect the already-bound local name in cli.py, so `test_first_run_triggers_config` and `test_config_cmd_no_double_trigger` remained xfail even after config.py was implemented.
- **Fix:** Changed cli.py to `import makenote.config as _cfg` and call `_cfg.config_exists()` and `_cfg.run_config_flow()` so monkeypatching flows through correctly.
- **Files modified:** src/makenote/cli.py
- **Verification:** `pytest tests/ -v` shows all 11 xpassed after fix
- **Committed in:** 8912546 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug: direct import bypassed monkeypatch in test contracts)
**Impact on plan:** Necessary fix for test contracts to pass. No scope change — the observable behavior of mn is identical.

## Issues Encountered
None beyond the auto-fixed monkeypatch issue above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All Phase 1 requirements (CONF-01 through CONF-06, UX-01, CORE-05) are now implemented and tested
- Phase 2 can import `config_exists`, `load_config`, `save_config` directly from `makenote.config`
- mn --version and mn --help verified working end-to-end

## Self-Check: PASSED

- src/makenote/config.py: FOUND
- src/makenote/cli.py: FOUND (modified)
- Commit e06ad1b: FOUND
- Commit 8912546: FOUND
- pytest tests/ -v: 11 xpassed, 0 failures, exit 0

---
*Phase: 01-scaffold-and-config*
*Completed: 2026-03-09*
