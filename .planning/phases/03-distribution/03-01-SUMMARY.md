---
phase: 03-distribution
plan: 01
subsystem: infra
tags: [homebrew, formula, virtualenv, release, distribution]

# Dependency graph
requires:
  - phase: 02-core-note-taking
    provides: working mn CLI with click and questionary dependencies
provides:
  - Homebrew formula using virtualenv_install_with_resources for isolated Python install
  - Release checklist documenting SHA256 computation, resource regeneration, and tap publish
affects: [tap-publish, user-install]

# Tech tracking
tech-stack:
  added: [Homebrew formula (Ruby DSL), brew update-python-resources]
  patterns: [virtualenv_install_with_resources for Python CLI distribution via Homebrew]

key-files:
  created:
    - Formula/makenote.rb
    - RELEASING.md
  modified: []

key-decisions:
  - "Formula sha256 field left as PLACEHOLDER_COMPUTE_BEFORE_PUBLISHING — v0.1.0 tarball does not exist yet; correct behavior for development formula"
  - "Resource stanzas (click, questionary, prompt-toolkit, wcwidth) left as PLACEHOLDER — brew update-python-resources requires formula inside a tap directory; included comment with exact command to regenerate at release time"
  - "depends_on python@3.12 (specific minor version per plan — not alias python3)"
  - "depends_on gh declared (DIST-02) — gh installed automatically on user machine"
  - "Formula lives at Formula/makenote.rb in make-note repo (source of truth), copied to hunterfinch/homebrew-tap on release"

patterns-established:
  - "Homebrew formula: class name matches formula file name (Makenote / makenote.rb)"
  - "Release workflow: compute SHA256 after tag push, regenerate resources, local brew test, then publish to tap"

requirements-completed: [DIST-01, DIST-02]

# Metrics
duration: 2min
completed: 2026-03-09
---

# Phase 3 Plan 01: Distribution Formula Summary

**Homebrew formula with virtualenv_install_with_resources, gh dependency (DIST-02), and a full release checklist covering SHA256 computation, resource regeneration via brew update-python-resources, and tap publish**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-09T16:30:56Z
- **Completed:** 2026-03-09T16:32:57Z
- **Tasks:** 2 of 3 auto tasks complete (Task 3 is human checkpoint — awaiting verification)
- **Files modified:** 2

## Accomplishments

- `Formula/makenote.rb` written with correct Homebrew Python formula structure: `virtualenv_install_with_resources`, `depends_on "gh"`, `system bin/"mn", "--version"` test block, and resource stanzas for all four dependencies
- `RELEASING.md` written with 10-step release checklist including SHA256 computation, resource stanza regeneration, local brew test, and tap-repo publish steps
- Existing pytest suite remains green (21 passed, 11 xpassed)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write Formula/makenote.rb** - `b715aef` (feat)
2. **Task 2: Write RELEASING.md** - `b3e1609` (feat)

## Files Created/Modified

- `Formula/makenote.rb` — Homebrew formula using virtualenv isolation, declares gh dependency, tests mn --version
- `RELEASING.md` — Step-by-step release workflow from version bump through tap publish

## Decisions Made

- Formula sha256 field left as PLACEHOLDER — v0.1.0 tarball does not yet exist; this is correct and expected per the plan
- Resource stanzas left as PLACEHOLDER — `brew update-python-resources` requires the formula to be inside a tap directory (not a bare file path), so it cannot be run during development; a note in both the formula and RELEASING.md explains the exact command and workaround for release time
- `depends_on "python@3.12"` — specific minor version per locked decisions, not the `python3` alias
- Formula source-of-truth lives in this repo; released copy goes to `hunterfinch/homebrew-tap`

## Deviations from Plan

None — plan executed exactly as written. `brew update-python-resources` failed as expected (tarball not published), resource stanzas left as PLACEHOLDER with comments.

## Issues Encountered

`brew update-python-resources --print-only Formula/makenote.rb` returned `Error: Homebrew requires formulae to be in a tap` — this is the expected failure mode documented in the plan. The RELEASING.md troubleshooting section includes a workaround (copy formula to local tap dir first) and the note in the formula file explains the correct command for release time.

## User Setup Required

None — no external service configuration required during this plan. The `hunterfinch/homebrew-tap` GitHub repo must be created before first release (documented in RELEASING.md Prerequisites).

## Next Phase Readiness

- Phase 3 delivery complete: formula and release checklist both exist
- To publish v0.1.0: tag the release, compute SHA256, regenerate resource stanzas, run `brew install --build-from-source`, copy to tap repo
- Human checkpoint (Task 3) is the final gate — once approved, requirements DIST-01 and DIST-02 are satisfied

---
*Phase: 03-distribution*
*Completed: 2026-03-09*
