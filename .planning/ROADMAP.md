# Roadmap: MakeNote

## Overview

MakeNote ships in three phases that follow the dependency topology of the codebase: first the foundation (project scaffold, config layer, and the `mn config` command), then all note-taking functionality (GitHub I/O and every note command including `mn list`), and finally distribution via Homebrew tap. Each phase delivers a coherent, independently verifiable capability.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Scaffold and Config** - Installable `mn` command, config layer, and `mn config` setup flow (completed 2026-03-09)
- [ ] **Phase 2: Core Note-Taking** - GitHub I/O layer and all note commands (`mn`, `mn d`, `mn d "note"`, `mn list`)
- [x] **Phase 3: Distribution** - Homebrew tap formula; tool installable from a personal tap (completed 2026-03-09)

## Phase Details

### Phase 1: Scaffold and Config
**Goal**: Users can install `mn`, run `mn --help` and `mn --version`, and complete first-time setup so the tool knows which GitHub repo and default subject to use
**Depends on**: Nothing (first phase)
**Requirements**: UX-01, CONF-01, CONF-02, CONF-03, CONF-04, CONF-05, CONF-06, CORE-05
**Success Criteria** (what must be TRUE):
  1. Running `mn --help` and `mn --version` produce correct output after a `pip install -e .` install
  2. Running `mn` with no existing config automatically launches the setup flow before doing anything else
  3. User can complete `mn config` to set the target GitHub repo, default subject, and subject list, and the result is written to `~/.config/makenote/config.json`
  4. User can add and remove subjects via `mn config` and see the change persist
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md — Project scaffold (pyproject.toml, package skeleton, test stubs)
- [ ] 01-02-PLAN.md — CLI entry point (click group, --version, --help, first-run detection)
- [ ] 01-03-PLAN.md — Config layer (read/write functions and mn config interactive flow)

### Phase 2: Core Note-Taking
**Goal**: Users can log notes to GitHub from the terminal using any interaction level, and read recent notes back
**Depends on**: Phase 1
**Requirements**: GH-01, GH-02, GH-03, GH-04, CORE-01, CORE-02, CORE-03, CORE-04, UX-02, UX-03
**Success Criteria** (what must be TRUE):
  1. Running `mn d "fixed the login bug"` logs the note to GitHub with zero prompts and confirms success
  2. Running `mn` presents an arrow-key subject picker (including an "Add New" option) and inline note prompt, then pushes to GitHub
  3. Running `mn d` skips the subject picker and prompts only for note text using the configured default subject
  4. Running `mn list` prints the last 10-20 notes across all subjects in human-readable format
  5. When `gh` is not installed or not authenticated, `mn` prints a clear, actionable error message instead of a Python traceback
**Plans**: 3 plans

Plans:
- [ ] 02-01-PLAN.md — GitHub I/O module (github.py with write_note, read_notes, error classes, tests)
- [ ] 02-02-PLAN.md — CLI note commands (mn interactive, mn d, mn list wired to github.py, tests)
- [ ] 02-03-PLAN.md — Gap closure: read_notes() error classification and list_notes() try/except (GH-04 fix)

### Phase 3: Distribution
**Goal**: Users can install `mn` via a Homebrew personal tap on a clean machine with no prior Python setup
**Depends on**: Phase 2
**Requirements**: DIST-01, DIST-02
**Success Criteria** (what must be TRUE):
  1. `brew install <tap>/makenote` succeeds on a clean macOS environment with no pre-installed Python
  2. The Homebrew formula declares `gh` as a dependency so it is installed automatically if absent
  3. After Homebrew install, `mn --version` runs correctly and all note commands work end-to-end
**Plans**: 1 plan

Plans:
- [ ] 03-01-PLAN.md — Homebrew formula and release checklist (Formula/makenote.rb, RELEASING.md)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Scaffold and Config | 3/3 | Complete   | 2026-03-09 |
| 2. Core Note-Taking | 0/3 | Not started | - |
| 3. Distribution | 1/1 | Complete   | 2026-03-09 |
