---
phase: 1
slug: scaffold-and-config
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-08
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (latest) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` — Wave 0 installs |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 0 | UX-01, CONF-01, CORE-05 | unit | `pytest tests/test_cli.py -x -q` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 0 | CONF-02–CONF-06 | unit | `pytest tests/test_config.py -x -q` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | UX-01 | unit | `pytest tests/test_cli.py::test_version tests/test_cli.py::test_help -x` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 1 | CONF-01 | unit (mock) | `pytest tests/test_cli.py::test_first_run_triggers_config -x` | ❌ W0 | ⬜ pending |
| 1-02-03 | 02 | 1 | CONF-01 | unit (mock) | `pytest tests/test_cli.py::test_config_cmd_no_double_trigger -x` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 2 | CONF-02 | unit | `pytest tests/test_config.py::test_config_path tests/test_config.py::test_config_dir_created -x` | ❌ W0 | ⬜ pending |
| 1-03-02 | 03 | 2 | CONF-03 | unit (mock) | `pytest tests/test_config.py::test_save_repo -x` | ❌ W0 | ⬜ pending |
| 1-03-03 | 03 | 2 | CONF-04 | unit (mock) | `pytest tests/test_config.py::test_save_default_subject -x` | ❌ W0 | ⬜ pending |
| 1-03-04 | 03 | 2 | CONF-05 | unit (mock) | `pytest tests/test_config.py::test_add_subject -x` | ❌ W0 | ⬜ pending |
| 1-03-05 | 03 | 2 | CONF-06 | unit (mock) | `pytest tests/test_config.py::test_remove_subject -x` | ❌ W0 | ⬜ pending |
| 1-03-06 | 03 | 2 | CORE-05 | unit | `pytest tests/test_cli.py::test_config_cmd_exists -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/__init__.py` — package marker
- [ ] `tests/test_cli.py` — stubs for UX-01, CONF-01, CORE-05
- [ ] `tests/test_config.py` — stubs for CONF-02, CONF-03, CONF-04, CONF-05, CONF-06
- [ ] `pyproject.toml` `[tool.pytest.ini_options]` — testpaths = ["tests"]
- [ ] `pip install pytest` + `pip install -e .` — framework install

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Arrow-key navigation works in terminal | CONF-03, CONF-04, CONF-05, CONF-06 | questionary's curses rendering can't be captured by CliRunner | Run `mn config`, navigate with arrow keys; confirm selection registers correctly |
| First-run message displays before setup | CONF-01 | Requires real terminal interaction | Run `mn` with no config file; confirm "No config found" message appears before prompts |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
