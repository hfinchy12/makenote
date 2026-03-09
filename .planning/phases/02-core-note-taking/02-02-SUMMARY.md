---
phase: 02-core-note-taking
plan: "02"
subsystem: cli
tags: [click, questionary, github, cli, tdd]

requires:
  - phase: 02-01
    provides: write_note() and read_notes() in github.py, GhError hierarchy

provides:
  - mn bare invocation with arrow-key subject picker (questionary.select)
  - Add New subject flow that persists to config.json
  - mn d [note_text] command with zero-interaction inline path
  - mn list command with columnar output, 60-char truncation
  - All GhError subclasses caught and mapped to locked error messages
  - Integration tests for CORE-01, CORE-02, CORE-03, CORE-04, UX-02

affects:
  - 03-distribution

tech-stack:
  added: []
  patterns:
    - import module as alias pattern (_gh, _cfg) for monkeypatching in pytest
    - questionary.ask() return checked for None immediately, sys.exit(0) on Ctrl-C
    - GhError subclass catching with locked error messages + sys.exit(1)
    - CliRunner(mix_stderr=False) for clean stdout/stderr separation in tests
    - _MockAsk helper class for questionary prompt mocking

key-files:
  created: []
  modified:
    - src/makenote/cli.py
    - tests/test_cli.py

key-decisions:
  - "Used from __future__ import annotations in cli.py for Python 3.9 compatibility with str | None type hints"
  - "Questionary mocked via monkeypatch.setattr on makenote.cli.questionary.select/text (module-level import pattern)"
  - "Add New placed first in choices list before Separator, existing subjects after"

patterns-established:
  - "questionary mock pattern: _MockAsk class with .ask() returning fixed value, patched onto makenote.cli.questionary"
  - "GhError handling pattern: three except blocks per command (GhNotInstalledError, GhNotAuthError, ShaConflictError) with locked messages"
  - "Config fixture pattern: _make_config(tmp_path) writes temp config.json, monkeypatch CONFIG_PATH points to it"

requirements-completed: [CORE-01, CORE-02, CORE-03, CORE-04, UX-02]

duration: 2min
completed: 2026-03-08
---

# Phase 2 Plan 02: CLI Note Commands Summary

**Full click CLI with questionary subject picker (mn), zero-interaction default command (mn d), columnar list view (mn list), and GhError-to-locked-message mapping for all note commands**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-08T22:12:14Z
- **Completed:** 2026-03-08T22:14:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- mn bare invocation now shows arrow-key subject picker with Add New first, saves new subjects permanently to config.json
- mn d command uses configured default_subject; zero-interaction when note_text provided inline (mn d "text")
- mn list command fetches notes via github.py and prints columnar output with date, subject, and truncated note text
- All GhError subclasses (GhNotInstalledError, GhNotAuthError, ShaConflictError) caught in each command with exact locked error messages
- 8 new integration tests covering all CORE-01/02/03/04 and UX-02 behaviors — full suite green (16 passed, 11 xpassed)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write failing tests for CLI note commands** - `6c54ec5` (test)
2. **Task 2: Implement CLI note commands until all tests pass** - `7352b84` (feat)

_Note: TDD tasks — test commit (RED) then implementation commit (GREEN)_

## Files Created/Modified

- `src/makenote/cli.py` - Added mn interactive flow, mn d, mn list subcommands with full GhError handling; added questionary and makenote.github imports
- `tests/test_cli.py` - Added 8 integration tests: test_mn_interactive, test_subject_picker_add_new, test_mn_no_subjects, test_mn_d_prompts, test_mn_d_inline, test_mn_list, test_mn_gh_not_installed, test_mn_gh_not_authenticated

## Decisions Made

- `from __future__ import annotations` added to cli.py for Python 3.9 compatibility — `str | None` union syntax requires 3.10+ without this import
- Questionary mocked at `makenote.cli.questionary.select`/`text` (not the module directly) because cli.py imports questionary at module level and uses it as `questionary.select(...)` — patching at the cli module level is necessary
- `_MockAsk` helper class defined in test file — provides `.ask()` returning a fixed value, making mock setup concise and readable

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added `from __future__ import annotations` for Python 3.9 compatibility**
- **Found during:** Task 2 (Implement CLI note commands)
- **Issue:** `def default_note(note_text: str | None)` raised `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'` on Python 3.9 — union type syntax with `|` requires Python 3.10+
- **Fix:** Added `from __future__ import annotations` at top of cli.py — enables postponed evaluation of annotations, making all type hints strings at runtime
- **Files modified:** src/makenote/cli.py
- **Verification:** All 16 tests pass after fix
- **Committed in:** 7352b84 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Essential for Python 3.9 compatibility documented in project decisions. No scope creep.

## Issues Encountered

None beyond the Python 3.9 type hint compatibility issue documented above.

## Next Phase Readiness

- All CLI note commands implemented and tested — ready for Phase 3 (Distribution)
- mn d "note" zero-interaction path works end-to-end
- GhError handling consistent across all commands with locked error messages
- No blockers for Phase 3

---
*Phase: 02-core-note-taking*
*Completed: 2026-03-08*
