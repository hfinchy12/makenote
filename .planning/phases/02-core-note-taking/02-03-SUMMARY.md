---
phase: 02-core-note-taking
plan: "03"
subsystem: cli
tags: [gh-cli, error-handling, subprocess, shutil]

# Dependency graph
requires:
  - phase: 02-core-note-taking/02-01
    provides: write_note() with GhNotInstalledError/GhNotAuthError error hierarchy
  - phase: 02-core-note-taking/02-02
    provides: list_notes() CLI command; read_notes() in github.py

provides:
  - read_notes() raises GhNotInstalledError before loop when gh absent
  - read_notes() raises GhNotAuthError on auth-keyword stderr
  - list_notes() catches GhNotInstalledError, GhNotAuthError, ShaConflictError with locked messages
  - test_mn_list_gh_not_installed and test_mn_list_gh_not_authenticated

affects:
  - 03-distribution
  - any future callers of read_notes()

# Tech tracking
tech-stack:
  added: []
  patterns: [shutil.which guard before subprocess loop, auth-keyword stderr classification, locked error messages across all note commands]

key-files:
  created: []
  modified:
    - src/makenote/github.py
    - src/makenote/cli.py
    - tests/test_github.py
    - tests/test_cli.py

key-decisions:
  - "read_notes() shutil.which guard placed before the for-loop, not inside it — one check covers all subjects"
  - "Auth-keyword check in read_notes() uses same pattern as write_note() GET path for consistency"
  - "ShaConflictError included in list_notes() try/except for completeness even though read_notes() does not raise it directly"

patterns-established:
  - "All three note commands (mn interactive, mn d, mn list) share identical try/except blocks with locked error messages"
  - "GhNotInstalledError always checked with shutil.which before entering subprocess loop"

requirements-completed: [GH-04, CORE-04]

# Metrics
duration: 2min
completed: 2026-03-09
---

# Phase 2 Plan 03: Gap Closure — read_notes() Error Classification Summary

**Added shutil.which guard and auth-keyword stderr classification to read_notes(), then wired identical try/except error handling into list_notes() — all three note commands now surface locked messages and exit 1 for gh-absent and unauthenticated states.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-09T15:16:37Z
- **Completed:** 2026-03-09T15:18:11Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- read_notes() raises GhNotInstalledError when gh not on PATH (shutil.which guard before loop)
- read_notes() raises GhNotAuthError on auth-keyword stderr; silently skips on 404/other (unchanged)
- list_notes() in cli.py catches GhNotInstalledError, GhNotAuthError, ShaConflictError with locked messages
- 5 new tests added (3 for read_notes, 2 for list_notes CLI paths); full suite 21 passed + 11 xpassed

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix read_notes() error classification in github.py** - `5ec93a6` (feat)
2. **Task 2: Add try/except to list_notes() in cli.py and write the two missing tests** - `04393ce` (feat)

**Plan metadata:** committed separately (docs)

_Note: TDD tasks included RED test commit integrated into feat commits per task._

## Files Created/Modified
- `src/makenote/github.py` - Added shutil.which guard + auth-keyword stderr classification in read_notes()
- `src/makenote/cli.py` - Added try/except GhNotInstalledError, GhNotAuthError, ShaConflictError in list_notes()
- `tests/test_github.py` - Added test_read_notes_gh_not_installed, test_read_notes_gh_not_authenticated, test_read_notes_404_skipped
- `tests/test_cli.py` - Added test_mn_list_gh_not_installed, test_mn_list_gh_not_authenticated

## Decisions Made
- shutil.which guard placed before the for-loop in read_notes(), not inside it — one check covers all subjects, cleaner semantics
- Auth-keyword check uses same pattern already established in write_note() GET path for consistency
- ShaConflictError included in list_notes() try/except for completeness (mn/mn d already catch it)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All three note commands (mn, mn d, mn list) now behave identically for gh-absent and unauthenticated states
- Verification truths 9 and 10 from 02-VERIFICATION.md are now satisfied
- Phase 2 gap closure complete; ready for Phase 3 (distribution)

---
*Phase: 02-core-note-taking*
*Completed: 2026-03-09*
