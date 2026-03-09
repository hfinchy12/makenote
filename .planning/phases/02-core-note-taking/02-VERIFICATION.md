---
phase: 02-core-note-taking
verified: 2026-03-09T15:30:00Z
status: passed
score: 10/10 truths verified
re_verification: true
  previous_status: gaps_found
  previous_score: 8/10
  gaps_closed:
    - "When gh is not installed, ALL note commands (including mn list) print locked error and exit 1"
    - "When gh is not authenticated, ALL note commands (including mn list) print locked error and exit 1"
  gaps_remaining: []
  regressions: []
gaps: []
human_verification: []
---

# Phase 2: Core Note-Taking Verification Report

**Phase Goal:** Users can log notes to GitHub from the terminal using any interaction level, and read recent notes back.
**Verified:** 2026-03-09
**Status:** passed
**Re-verification:** Yes — after gap closure via Plan 03.

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | write_note() reads the current file SHA, appends a JSONL record, and PUTs the updated content to GitHub | VERIFIED | github.py lines 108-156: GET sha, append record, PUT with sha= field |
| 2  | write_note() creates the file when it does not yet exist (no SHA on first PUT) | VERIFIED | github.py lines 136-137: existing_sha = None when GET non-zero; PUT omits sha field |
| 3  | Each written record has date (YYYY-MM-DD), subject, and note fields | VERIFIED | github.py lines 116-120: json.dumps with all three keys; test_record_format PASSES |
| 4  | Notes stored at notes/{subject}/notes.jsonl inside the configured repo | VERIFIED | github.py lines 105-106: f"{NOTES_ROOT}/{subject}/notes.jsonl"; test_path_construction PASSES |
| 5  | When gh is not on PATH, caller receives GhNotInstalledError | VERIFIED | github.py line 102-103: shutil.which check in write_note(); line 175-176: shutil.which check in read_notes(); test_gh_not_installed and test_read_notes_gh_not_installed PASS |
| 6  | When gh returns non-zero with auth stderr, caller receives GhNotAuthError | VERIFIED | github.py lines 131-134: auth keyword check in write_note(); lines 189-193: same check in read_notes(); all relevant tests PASS |
| 7  | When PUT returns 422 conflict, caller receives ShaConflictError | VERIFIED | github.py lines 154-155: "422" or "conflict" in PUT stderr; test_sha_conflict PASSES |
| 8  | mn interactive flow: subject picker, Add New, note prompt, write_note(), "Note logged." | VERIFIED | cli.py lines 21-52; test_mn_interactive PASSES; test_subject_picker_add_new PASSES |
| 9  | When gh is not installed, ALL note commands print locked error and exit 1 | VERIFIED | mn: cli.py line 43. mn d: cli.py line 73. mn list: cli.py line 91. All three except _gh.GhNotInstalledError blocks present. test_mn_gh_not_installed, test_mn_list_gh_not_installed PASS |
| 10 | When gh is not authenticated, ALL note commands print locked error and exit 1 | VERIFIED | mn: cli.py line 46. mn d: cli.py line 76. mn list: cli.py line 94. All three except _gh.GhNotAuthError blocks present. test_mn_gh_not_authenticated, test_mn_list_gh_not_authenticated PASS |

**Score:** 10/10 truths verified

---

## Re-verification: Gap Closure Evidence

### Previously Failed: Truth 9 (gh not installed — mn list)

**Previous state:** read_notes() had no shutil.which guard; gh-absent caused uncaught FileNotFoundError in mn list.

**Fix applied (commit 5ec93a6):** github.py line 175 now reads `if not shutil.which("gh"): raise GhNotInstalledError(...)` before the subject loop.

**Fix applied (commit 04393ce):** cli.py list_notes() now wraps `_gh.read_notes()` in try/except blocks at lines 89-99.

**Verified closed:** `test_mn_list_gh_not_installed` PASSES — exit code 1, output contains "Error: gh CLI not found" and "https://cli.github.com".

### Previously Failed: Truth 10 (gh not authenticated — mn list)

**Previous state:** read_notes() silently continued on all non-zero exits, including auth failures; mn list printed "No notes found." instead of the locked message.

**Fix applied (commit 5ec93a6):** github.py lines 189-193 now classify auth-keyword stderr and raise GhNotAuthError before the silent-continue fallthrough for 404/other errors.

**Fix applied (commit 04393ce):** same cli.py try/except block catches GhNotAuthError.

**Verified closed:** `test_mn_list_gh_not_authenticated` PASSES — exit code 1, output contains "Error: gh not authenticated" and "gh auth login".

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/makenote/github.py` | write_note(), read_notes(), _run_gh(), error class hierarchy | VERIFIED (substantive, wired) | 209 lines; shutil.which appears at lines 56, 102, 175 (write_note, write_note guard, read_notes guard); all 5 error classes defined |
| `tests/test_github.py` | Unit tests covering GH-01 through GH-04 and UX-03 | VERIFIED | Now includes test_read_notes_gh_not_installed, test_read_notes_gh_not_authenticated, test_read_notes_404_skipped (added in Plan 03) |
| `src/makenote/cli.py` | mn interactive, mn d, mn list wired to github.py with GhError handling | VERIFIED | All 3 subcommands present; all 3 have identical try/except blocks for GhNotInstalledError, GhNotAuthError, ShaConflictError |
| `tests/test_cli.py` | Integration tests for CORE-01 through CORE-04, UX-02, and error paths including mn list | VERIFIED | 10 non-xfail tests all PASS; includes test_mn_list_gh_not_installed and test_mn_list_gh_not_authenticated |

---

## Key Link Verification

### Plan 01 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| write_note() | gh api GET endpoint | _run_gh() subprocess call | VERIFIED | github.py line 109: subprocess.run(["gh", "api", endpoint], ...) |
| write_note() | gh api PUT endpoint | subprocess.run --method PUT | VERIFIED | github.py lines 143-150: put_args with "--method", "PUT" |
| _run_gh() | shutil.which('gh') | check before subprocess call | VERIFIED | github.py line 56: `if not shutil.which("gh")` |

### Plan 02 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| cli.py mn bare invocation | _gh.write_note() | questionary.select() + questionary.text() | VERIFIED | cli.py line 42: _gh.write_note(cfg["repo"], subject, note_text) |
| cli.py mn d command | _gh.write_note() | default_subject + optional inline argument | VERIFIED | cli.py line 65: subject = cfg["default_subject"]; line 72: _gh.write_note(...) |
| cli.py mn list command | _gh.read_notes() | load_config()['subjects'] passed to read_notes | VERIFIED | cli.py line 90: _gh.read_notes(cfg["repo"], cfg.get("subjects", [])) |
| cli.py error handlers | GhNotInstalledError / GhNotAuthError | except blocks with locked messages | VERIFIED | mn: lines 43-51. mn d: lines 73-81. list_notes: lines 91-99. All three commands now have complete error handling |

### Plan 03 Key Links (Gap Closure)

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| cli.py list_notes() | read_notes() | try/except GhNotInstalledError, GhNotAuthError | VERIFIED | cli.py lines 89-99: try block wraps _gh.read_notes(); three except clauses |
| read_notes() | shutil.which('gh') | guard before subprocess.run loop | VERIFIED | github.py line 175: `if not shutil.which("gh"):` before the for-loop |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| GH-01 | 02-01 | Notes written via gh api — read SHA, append, update | SATISFIED | write_note() GET+PUT with sha; test_write_note_update + test_write_note_create PASS |
| GH-02 | 02-01 | Notes stored as JSONL with date, subject, note fields | SATISFIED | json.dumps with all 3 keys; test_record_format PASSES |
| GH-03 | 02-01 | One notes.jsonl per subject folder under configurable path | SATISFIED | f"{NOTES_ROOT}/{subject}/notes.jsonl"; NOTES_ROOT constant; test_path_construction PASSES |
| GH-04 | 02-01, 02-03 | Clear error when gh not installed or not authenticated | SATISFIED | All three note commands raise GhNotInstalledError/GhNotAuthError with locked messages and exit 1; 4 CLI-level tests plus github.py unit tests all PASS |
| CORE-01 | 02-02 | mn → arrow-key subject picker → note input → push to GitHub | SATISFIED | cli.py questionary.select + write_note(); test_mn_interactive PASSES |
| CORE-02 | 02-02 | mn d → inline note prompt using default subject | SATISFIED | cli.py default_note(); test_mn_d_prompts PASSES |
| CORE-03 | 02-02 | mn d "note content" → zero interaction log | SATISFIED | click.argument note_text; test_mn_d_inline PASSES |
| CORE-04 | 02-02, 02-03 | mn list → recent notes across all subjects | SATISFIED | cli.py list_notes() + read_notes() — happy path works; error paths now fully wired; test_mn_list, test_mn_list_gh_not_installed, test_mn_list_gh_not_authenticated all PASS |
| UX-02 | 02-02 | Subject picker uses arrow-key with "Add New" option | SATISFIED | cli.py choices = ["Add New", questionary.Separator()] + subjects; test_subject_picker_add_new PASSES |
| UX-03 | 02-01 | Each note record includes date field (YYYY-MM-DD) | SATISFIED | datetime.date.today().isoformat(); test_date_field_format PASSES |

**Orphaned requirements check:** REQUIREMENTS.md maps no additional requirements to Phase 2 beyond those claimed in 02-01-PLAN.md, 02-02-PLAN.md, and 02-03-PLAN.md.

---

## Anti-Patterns Found

None. The two blocker anti-patterns from the initial verification (read_notes() silent swallow, list_notes() missing try/except) were both remediated by Plan 03 commits 5ec93a6 and 04393ce.

---

## Human Verification Required

None — all behavioral correctness is determinable from static code analysis and test results.

---

## Full Suite Results

```
21 passed, 11 xpassed in 0.24s
```

- 21 non-xfail tests: all PASS (zero failures, zero errors)
- 11 xpassed: pre-existing xfail tests that now pass (no regression)
- Commits verified: 5ec93a6 (read_notes fix), 04393ce (list_notes wiring + tests)

---

## Gaps Summary

No gaps remain. The two truths that failed in the initial verification are now fully closed:

Truth 9 (gh not installed — all commands): read_notes() now has a shutil.which guard before the subject loop (github.py line 175), matching the same guard in write_note(). list_notes() now catches GhNotInstalledError and prints the locked message with sys.exit(1). test_mn_list_gh_not_installed PASSES.

Truth 10 (gh not authenticated — all commands): read_notes() now classifies auth-keyword stderr and raises GhNotAuthError before falling through to the silent-continue path for 404/other errors (github.py lines 189-193). list_notes() catches GhNotAuthError and prints the locked message with sys.exit(1). test_mn_list_gh_not_authenticated PASSES.

All 10 observable truths are verified. All 10 requirements are satisfied. Phase goal achieved.

---

_Verified: 2026-03-09_
_Verifier: Claude (gsd-verifier)_
_Re-verification after gap closure via Plan 03 (commits 5ec93a6, 04393ce)_
