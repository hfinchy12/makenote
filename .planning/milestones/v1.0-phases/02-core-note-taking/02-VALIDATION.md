---
phase: 2
slug: core-note-taking
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-08
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (current install) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/test_github.py tests/test_cli.py -x -q` |
| **Full suite command** | `pytest -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_github.py tests/test_cli.py -x -q`
- **After every plan wave:** Run `pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 0 | GH-01 | unit | `pytest tests/test_github.py::test_write_note_update -x` | ❌ W0 | ⬜ pending |
| 2-01-02 | 01 | 0 | GH-01 | unit | `pytest tests/test_github.py::test_write_note_create -x` | ❌ W0 | ⬜ pending |
| 2-01-03 | 01 | 0 | GH-02 | unit | `pytest tests/test_github.py::test_record_format -x` | ❌ W0 | ⬜ pending |
| 2-01-04 | 01 | 0 | GH-03 | unit | `pytest tests/test_github.py::test_path_construction -x` | ❌ W0 | ⬜ pending |
| 2-01-05 | 01 | 0 | GH-04 | unit | `pytest tests/test_github.py::test_gh_not_installed -x` | ❌ W0 | ⬜ pending |
| 2-01-06 | 01 | 0 | GH-04 | unit | `pytest tests/test_github.py::test_gh_not_authenticated -x` | ❌ W0 | ⬜ pending |
| 2-01-07 | 01 | 0 | UX-03 | unit | `pytest tests/test_github.py::test_date_field_format -x` | ❌ W0 | ⬜ pending |
| 2-02-01 | 02 | 1 | CORE-01 | integration | `pytest tests/test_cli.py::test_mn_interactive -x` | ❌ W0 | ⬜ pending |
| 2-02-02 | 02 | 1 | UX-02 | unit | `pytest tests/test_cli.py::test_subject_picker_add_new -x` | ❌ W0 | ⬜ pending |
| 2-02-03 | 02 | 1 | CORE-02 | integration | `pytest tests/test_cli.py::test_mn_d_prompts -x` | ❌ W0 | ⬜ pending |
| 2-02-04 | 02 | 1 | CORE-03 | integration | `pytest tests/test_cli.py::test_mn_d_inline -x` | ❌ W0 | ⬜ pending |
| 2-02-05 | 02 | 1 | CORE-04 | integration | `pytest tests/test_cli.py::test_mn_list -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_github.py` — stubs for GH-01, GH-02, GH-03, GH-04, UX-03
- [ ] `src/makenote/github.py` — module stub with error classes and function signatures

*(test_cli.py already exists; new test functions for CORE-01 through CORE-04 and UX-02 are added to existing file)*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `mn d "note"` actually writes to GitHub repo | GH-01 | Requires real gh auth + network | Run `mn d "test note"`, check GitHub repo file content |
| `mn list` shows real notes from GitHub | CORE-04 | Requires real gh auth + network | Run `mn list` after writing a note, verify output |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
