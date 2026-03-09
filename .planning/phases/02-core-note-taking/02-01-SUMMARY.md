---
phase: 02-core-note-taking
plan: "01"
subsystem: api
tags: [github, subprocess, base64, jsonl, pytest, monkeypatch]

# Dependency graph
requires:
  - phase: 01-scaffold-and-config
    provides: config.py load_config/save_config, cli.py Click group, module-import pattern for monkeypatching
provides:
  - src/makenote/github.py with write_note(), read_notes(), _run_gh(), and full error class hierarchy
  - tests/test_github.py with 8 unit tests covering GH-01 through GH-04 and UX-03
affects:
  - 02-02 (cli.py note commands — imports github as _gh)
  - 02-03 (mn list command — calls read_notes())

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Read-modify-write with GitHub Contents API: GET sha, append JSONL, PUT with sha"
    - "shutil.which() check before subprocess to give clean GhNotInstalledError"
    - "Auth error detection from gh stderr: 'not logged in' or 'auth' keywords"
    - "NOTES_ROOT module constant for configurable path prefix"
    - "subprocess.run with capture_output=True, text=True for all gh calls"
    - "GET 404 treated as 'create new file' not an error (no sha in PUT)"

key-files:
  created:
    - src/makenote/github.py
    - tests/test_github.py
  modified: []

key-decisions:
  - "write_note() does direct subprocess.run for GET (not _run_gh) because 404 is a normal/expected response"
  - "NOTES_ROOT = 'notes' as module constant — promotes to config field in future phase without inline hardcoding"
  - "Auth error detection via stderr keyword matching ('not logged in', 'auth') — MEDIUM confidence per research"
  - "ShaConflictError triggered by '422' or 'conflict' in PUT stderr — matches GitHub Contents API behavior"

patterns-established:
  - "Pattern: import makenote.github as _gh in cli.py (module-level) — enables monkeypatching in tests"
  - "Pattern: all tests monkeypatch subprocess.run + shutil.which — zero real network calls"
  - "Pattern: SimpleNamespace for fake subprocess result objects in tests"

requirements-completed: [GH-01, GH-02, GH-03, GH-04, UX-03]

# Metrics
duration: 1min
completed: 2026-03-08
---

# Phase 2 Plan 01: GitHub I/O Module Summary

**github.py implementing read-modify-write via gh CLI subprocess with GhNotInstalledError/GhNotAuthError/ShaConflictError hierarchy, tested with 8 fully-passing monkeypatched unit tests**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-09T02:28:09Z
- **Completed:** 2026-03-09T02:29:30Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Implemented `write_note()` with full read-modify-write workflow: GET sha, append JSONL record, PUT with sha when updating or without sha when creating
- Implemented `read_notes()` fetching JSONL per subject, decoding base64, returning sorted newest-first up to 20 records
- Established clean error hierarchy (GhError > GhNotInstalledError, GhNotAuthError, ShaConflictError, GhApiError) for cli.py to catch and surface locked UX messages
- All 8 unit tests pass; full suite green (8 passed, 11 xpassed)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write failing tests for github.py** - `a5e6f58` (test — RED)
2. **Task 2: Implement github.py until all tests pass** - `c7db2ac` (feat — GREEN)

_Note: TDD plan — test commit followed by implementation commit._

## Files Created/Modified

- `src/makenote/github.py` - Full GitHub I/O module: GhError hierarchy, _run_gh(), write_note(), read_notes(), NOTES_ROOT constant
- `tests/test_github.py` - 8 unit tests covering GH-01 (update + create), GH-02 (record format), GH-03 (path construction), GH-04 (not installed + not authenticated), UX-03 (date format), and SHA conflict

## Decisions Made

- `write_note()` uses direct `subprocess.run` for the GET step rather than `_run_gh()` because a non-zero GET response is expected/normal when the file does not yet exist. `_run_gh()` raises on any non-zero exit code, which would break the create-new-file path.
- `NOTES_ROOT = "notes"` as a module-level constant rather than reading from config — keeps Phase 2 scope clean; Phase 3 can promote it to a config field if needed.
- Auth error detection for the GET step: checks `get_result.stderr.lower()` for "not logged in" or "auth" (excluding lines that also contain "404"/"not found") to distinguish auth failure from a normal missing-file response.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. (gh CLI must be installed and authenticated separately by the user, which is the expected pre-condition per project design.)

## Next Phase Readiness

- `write_note()` and `read_notes()` are ready for `cli.py` to call in Plan 02-02
- Import pattern: `import makenote.github as _gh` in cli.py enables test monkeypatching
- Error classes ready to catch in cli.py: `GhNotInstalledError`, `GhNotAuthError`, `ShaConflictError`
- No blockers for Plan 02-02

---
*Phase: 02-core-note-taking*
*Completed: 2026-03-08*
