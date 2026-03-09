# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-09
**Phases:** 3 | **Plans:** 7 | **Sessions:** ~3-4

### What Was Built
- Installable `mn` CLI with first-run detection and `mn config` interactive setup
- GitHub I/O module (`github.py`) with SHA-safe JSONL append, `read_notes`, and full `GhError` hierarchy
- Four note commands covering zero-interaction to fully-interactive use cases
- Homebrew formula with isolated Python virtualenv + `gh` dependency; complete release checklist

### What Worked
- Wave-based plan structure (scaffold → wire → test) kept each plan's scope coherent
- Phase 2 gap discovery was caught before Phase 3 — `mn list` error handling was absent, plan 02-03 closed it cleanly
- `import makenote.config as _cfg` module-import pattern was the right call for pytest monkeypatching; discovered during Phase 1 and applied consistently
- VERIFICATION.md re-verification cycle (Phase 2 went gaps_found → passed after one gap-closure plan) worked as designed

### What Was Inefficient
- Phase 2's ROADMAP.md was never updated to check off `[x]` during execution — auditor caught the discrepancy; this should be automated or gated
- `constants.py` was scaffolded in Phase 1 as a future re-export target but never consumed — dead code shipped in v1.0
- `default_subject` empty-string edge case was caught by the integration checker at audit time, not during Phase 2 planning — worth a pre-plan checklist item for config-dependent commands

### Patterns Established
- `import module as _alias` throughout `cli.py` for all inter-module calls enables pytest monkeypatching without import-time binding issues
- xfail stubs written first, then implementations XPASS them — good TDD signal for CLI commands
- Gap-closure plans (02-03 style) are a valid and efficient pattern: keep the main plan clean, ship a small plan to close the verified gap

### Key Lessons
1. **Verification gap detection is a feature**: Phase 2's initial `gaps_found` status was worth catching. The re-verification cycle cost one extra plan but produced a cleaner, fully-tested codebase.
2. **Distribution phase is not the place to discover integration issues**: All three flow paths (gh not installed, gh not authenticated, happy path) should be verified at the note-command phase, not assumed to work at distribution time.
3. **Dead code in scaffold is easy to miss**: Constants extracted for "future use" during scaffold often become orphaned as plans evolve. Audit dead exports at phase completion.

### Cost Observations
- Model mix: ~100% sonnet (balanced profile throughout)
- Sessions: ~3-4 across 48 commits
- Notable: Phase 2 gap closure (02-03) was 2 focused commits — efficient

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | ~4 | 3 | First milestone — baseline established |

### Cumulative Quality

| Milestone | Tests | LOC (source) | Notes |
|-----------|-------|--------------|-------|
| v1.0 | 32 (21 pass + 11 xpass) | 408 | 711 LOC test coverage |

### Top Lessons (Verified Across Milestones)

1. Module-import aliasing (`as _alias`) is essential for pytest monkeypatching in Click CLI projects
2. Re-verification after gap closure is worth the extra plan — clean verification is better than tech-debt-laden `passed`
