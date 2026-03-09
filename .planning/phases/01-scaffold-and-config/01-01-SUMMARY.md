---
phase: 01-scaffold-and-config
plan: "01"
subsystem: infra
tags: [python, setuptools, pyproject, click, questionary, pytest]

# Dependency graph
requires: []
provides:
  - Installable Python package (pip install -e . with mn entry point)
  - src/makenote package with __version__ and CONFIG_PATH constant
  - pytest test infrastructure with xfail stubs for all Phase 1 requirements
affects: [01-02, 01-03, 01-04]

# Tech tracking
tech-stack:
  added: [click>=8.1, questionary>=2.0, pytest>=8.0, setuptools>=68]
  patterns: [src layout, pyproject.toml build system, xfail stubs for TDD wave structure]

key-files:
  created:
    - pyproject.toml
    - src/makenote/__init__.py
    - src/makenote/constants.py
    - tests/__init__.py
    - tests/test_cli.py
    - tests/test_config.py
  modified: []

key-decisions:
  - "Lowered requires-python from >=3.10 to >=3.9 — system Python is 3.9.6, no 3.10-specific syntax used"
  - "Used Path.home() / '.config' / 'makenote' / 'config.json' for CONFIG_PATH — portable, no hardcoded strings"
  - "All test stubs marked xfail(strict=False) — suite stays green before Wave 1/2 implementations"

patterns-established:
  - "src layout: package code lives in src/makenote/, discovered via tool.setuptools.packages.find"
  - "xfail stubs: test contracts defined before implementation, Wave 0 → Wave N structure"
  - "CONFIG_PATH defined in constants.py and imported by both config.py (Wave 2) and test stubs"

requirements-completed: [UX-01, CONF-01, CONF-02, CONF-03, CONF-04, CONF-05, CONF-06, CORE-05]

# Metrics
duration: 2min
completed: 2026-03-08
---

# Phase 1 Plan 01: Scaffold and Config Summary

**Installable Python package (mn entry point via setuptools) with xfail test stubs covering all 11 Phase 1 requirements across CLI and config behavior**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-08T17:12:29Z
- **Completed:** 2026-03-08T17:14:09Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- pyproject.toml establishes package metadata, mn console_scripts entry point, and pytest config
- src/makenote package with __version__ = "0.1.0" and CONFIG_PATH using Path.home()
- 11 xfail test stubs define contracts for UX-01, CONF-01 to CONF-06, and CORE-05 before any implementation

## Task Commits

Each task was committed atomically:

1. **Task 1: Project scaffold — pyproject.toml and package skeleton** - `490c1e6` (feat)
2. **Task 2: Test stubs — test_cli.py and test_config.py** - `e1db59e` (feat)

## Files Created/Modified
- `pyproject.toml` - Build system, project metadata, mn entry point, pytest config
- `src/makenote/__init__.py` - Package marker with __version__ = "0.1.0"
- `src/makenote/constants.py` - CONFIG_PATH = Path.home() / ".config" / "makenote" / "config.json"
- `tests/__init__.py` - Package marker (empty)
- `tests/test_cli.py` - xfail stubs: test_version, test_help, test_first_run_triggers_config, test_config_cmd_no_double_trigger, test_config_cmd_exists
- `tests/test_config.py` - xfail stubs: test_config_path, test_config_dir_created, test_save_repo, test_save_default_subject, test_add_subject, test_remove_subject

## Decisions Made
- Lowered requires-python to >=3.9 because system Python is 3.9.6 and no 3.10-specific syntax is used
- Used Path.home() for CONFIG_PATH portability (no hardcoded tilde strings)
- All stubs use xfail(strict=False) so the test suite exits 0 before implementations exist

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Lowered requires-python from >=3.10 to >=3.9**
- **Found during:** Task 1 (Project scaffold)
- **Issue:** Plan specified requires-python = ">=3.10" but the only available Python is 3.9.6; pip refused to install with the mismatch
- **Fix:** Changed requires-python to ">=3.9" in pyproject.toml — no 3.10-specific syntax is present or planned
- **Files modified:** pyproject.toml
- **Verification:** pip install -e . exits 0; python3 -c "import makenote; from makenote.constants import CONFIG_PATH" succeeds
- **Committed in:** 490c1e6 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug: incompatible Python version constraint)
**Impact on plan:** Necessary fix — package would not install without it. No functional scope change.

## Issues Encountered
- System pip (21.2.4) does not support pyproject.toml editable installs; upgraded pip to 26.0.1 via --user install before running pip install -e .

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Package is installable and test infrastructure is in place
- Wave 1 (cli.py) and Wave 2 (config.py) can now be implemented against the test contracts
- mn entry point declared; implementation plans 01-02 and 01-03 can proceed in parallel

## Self-Check: PASSED

- pyproject.toml: FOUND
- src/makenote/__init__.py: FOUND
- src/makenote/constants.py: FOUND
- tests/__init__.py: FOUND
- tests/test_cli.py: FOUND
- tests/test_config.py: FOUND
- Commit 490c1e6: FOUND
- Commit e1db59e: FOUND

---
*Phase: 01-scaffold-and-config*
*Completed: 2026-03-08*
