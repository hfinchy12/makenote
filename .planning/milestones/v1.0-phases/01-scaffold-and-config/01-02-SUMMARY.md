---
phase: 01-scaffold-and-config
plan: "02"
subsystem: infra
tags: [python, click, cli, tdd]

# Dependency graph
requires:
  - phase: 01-scaffold-and-config
    plan: "01"
    provides: "Installable package with xfail test stubs and makenote.__init__/constants"
provides:
  - src/makenote/cli.py — click group with --version, first-run detection, and config subcommand
affects: [01-03, 01-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "click group with invoke_without_command=True for correct subcommand + no-args routing"
    - "version_option message='%(prog)s %(version)s' to control exact version output format"
    - "ctx.invoked_subcommand guard to prevent double-triggering config flow"

key-files:
  created:
    - src/makenote/cli.py
  modified: []

key-decisions:
  - "message='%(prog)s %(version)s' required on version_option — click default adds comma and 'version' word which breaks UX-01"
  - "ctx.invoked_subcommand != 'config' guard required — prevents auto-setup from firing when user runs mn config explicitly"
  - "Tests remain xfail until Plan 03 implements config.py — correct behavior for this plan"

patterns-established:
  - "cli.py imports config_exists and run_config_flow from makenote.config — forward contract for Plan 03"
  - "All click output via click.echo(), never print()"
  - "Short one-line docstrings only — click uses them verbatim in --help output"

requirements-completed: [UX-01, CONF-01, CORE-05]

# Metrics
duration: 2min
completed: 2026-03-08
---

# Phase 1 Plan 02: CLI Entry Point Summary

**Click group CLI (`mn`) with --version outputting 'mn 0.1.0', first-run config auto-trigger guard, and `mn config` subcommand — all wired to makenote.config forward contracts**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-09T01:56:58Z
- **Completed:** 2026-03-09T01:58:30Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- click group with `invoke_without_command=True` routes no-args invocation to help display
- `--version` flag outputs exactly `mn 0.1.0` (not click's default `mn, version 0.1.0`)
- First-run guard calls `run_config_flow()` only when config absent AND subcommand is not `config`
- `mn config` subcommand registered and delegates to `run_config_flow()`
- All 5 test_cli.py tests remain xfail as expected (config.py not yet implemented in Plan 03)

## Task Commits

Each task was committed atomically:

1. **Task 1: CLI entry point — click group with --version, --help, first-run detection, config subcommand** - `4b6f116` (feat)

**Plan metadata:** (docs commit to follow)

_Note: TDD tasks — RED phase confirmed (5 xfail before implementation), GREEN phase implemented and manually verified with config stub._

## Files Created/Modified
- `src/makenote/cli.py` - Click group `main`, `--version` with custom message format, first-run guard, `config` subcommand

## Decisions Made
- `message="%(prog)s %(version)s"` on `@click.version_option` — the click default includes "version" text and a comma, which breaks the exact `mn 0.1.0` output required by UX-01
- `ctx.invoked_subcommand != "config"` guard — without this, `mn config` would call `run_config_flow()` twice (once from the group callback, once from the subcommand handler)
- No `sys` import needed — click handles exit codes internally; removed the unused import from the plan's code snippet

## Deviations from Plan

None - plan executed exactly as written. The plan's code snippet included an unused `import sys` which was not included in the final implementation (it was never referenced in the snippet's function bodies either).

## Issues Encountered

None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `src/makenote/cli.py` is in place; Plan 03 (config.py) can now implement `config_exists()` and `run_config_flow()` to make all 5 test_cli.py tests turn green
- The `mn` entry point is fully wired via pyproject.toml console_scripts from Plan 01

## Self-Check: PASSED

- src/makenote/cli.py: FOUND
- Commit 4b6f116: FOUND
- Syntax check: PASSED (`ast.parse` exits 0)
- Manual behavior verification: PASSED (version='mn 0.1.0', help lists 'config', config --help exits 0)

---
*Phase: 01-scaffold-and-config*
*Completed: 2026-03-08*
