---
phase: 3
slug: distribution
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing, configured in `pyproject.toml`) |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/` + `grep 'depends_on "gh"' Formula/makenote.rb`
- **Before `/gsd:verify-work`:** Full suite must be green + `brew install --build-from-source Formula/makenote.rb` passes
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | DIST-01, DIST-02 | manual/inspection | `grep 'depends_on "gh"' Formula/makenote.rb` | ❌ Wave 0 | ⬜ pending |
| 3-01-02 | 01 | 1 | DIST-01 | smoke | `brew install --build-from-source Formula/makenote.rb && brew test makenote` | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `Formula/makenote.rb` — formula file covering DIST-01 and DIST-02
- [ ] `RELEASING.md` — release documentation

*No pytest test file gaps — existing infrastructure covers regressions; distribution requirements verified via formula inspection and brew tooling, not pytest.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `brew install hunterfinch/tap/makenote` succeeds on clean macOS | DIST-01 | Requires macOS + Homebrew environment; no CI equivalent | Run `brew install --build-from-source ./Formula/makenote.rb` locally; confirm `mn --version` outputs version string |
| `gh` installed automatically as dependency | DIST-02 | Requires clean machine without `gh` pre-installed | Inspect `grep 'depends_on "gh"' Formula/makenote.rb`; optionally test on a fresh environment |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
