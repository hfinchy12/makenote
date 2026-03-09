# Requirements: MakeNote

**Defined:** 2026-03-08
**Core Value:** Logging a note must be as fast as a terminal command — the power-user path (`mn d "note"`) should require zero interaction.

## v1 Requirements

### Core Commands

- [ ] **CORE-01**: User can run `mn` to get arrow-key subject picker → inline note input → note pushed to GitHub
- [ ] **CORE-02**: User can run `mn d` to skip subject picker and get inline note prompt using default subject
- [ ] **CORE-03**: User can run `mn d "note content"` to log a note with zero interaction
- [ ] **CORE-04**: User can run `mn list` to see the most recent notes across all subjects printed to terminal
- [x] **CORE-05**: User can run `mn config` to interactively edit repo, default subject, and subject list

### Config

- [x] **CONF-01**: First run with no config auto-triggers setup flow before proceeding
- [x] **CONF-02**: Config stored at `~/.config/makenote/config.json`
- [x] **CONF-03**: User can set/change the target GitHub repo
- [x] **CONF-04**: User can set/change the default subject
- [x] **CONF-05**: User can add a new subject
- [x] **CONF-06**: User can remove an existing subject

### GitHub

- [ ] **GH-01**: Notes written via `gh api` — read current SHA → append record → update file
- [ ] **GH-02**: Notes stored as JSONL with `date`, `subject`, `note` fields per record
- [ ] **GH-03**: One `notes.jsonl` per subject folder, under configurable `target_path` in the repo
- [ ] **GH-04**: Clear error message when `gh` is not installed or not authenticated

### UX

- [x] **UX-01**: `mn --help` and `mn --version` work correctly
- [ ] **UX-02**: Subject picker uses arrow-key selection with "Add New" option
- [ ] **UX-03**: Each note record includes a `date` field (YYYY-MM-DD)

### Distribution

- [ ] **DIST-01**: Tool installable via Homebrew personal tap
- [ ] **DIST-02**: Homebrew formula declares `gh` as a dependency

## v2 Requirements

### Distribution

- **DIST-03**: Published to PyPI (`pip install makenote`)

### Note Recall

- **LIST-01**: Filter `mn list` by subject
- **LIST-02**: Filter `mn list` by date range

### Features

- **FEAT-01**: Offline queue — save locally if GitHub unreachable, push on next run
- **FEAT-02**: Auto-detect hashtags in note text for future filtering (`#bugfix`, `#feature`)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Web app or GUI | Terminal-only by design |
| Database | JSONL files in GitHub are the store |
| Direct credential handling | `gh auth login` is the user's responsibility |
| Note editing | Breaks append-only model |
| Real-time sync | Unnecessary complexity for a logging tool |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CORE-01 | Phase 2 | Pending |
| CORE-02 | Phase 2 | Pending |
| CORE-03 | Phase 2 | Pending |
| CORE-04 | Phase 2 | Pending |
| CORE-05 | Phase 1 | Complete |
| CONF-01 | Phase 1 | Complete |
| CONF-02 | Phase 1 | Complete |
| CONF-03 | Phase 1 | Complete |
| CONF-04 | Phase 1 | Complete |
| CONF-05 | Phase 1 | Complete |
| CONF-06 | Phase 1 | Complete |
| GH-01 | Phase 2 | Pending |
| GH-02 | Phase 2 | Pending |
| GH-03 | Phase 2 | Pending |
| GH-04 | Phase 2 | Pending |
| UX-01 | Phase 1 | Complete |
| UX-02 | Phase 2 | Pending |
| UX-03 | Phase 2 | Pending |
| DIST-01 | Phase 3 | Pending |
| DIST-02 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0

---
*Requirements defined: 2026-03-08*
*Last updated: 2026-03-08 after roadmap creation*
