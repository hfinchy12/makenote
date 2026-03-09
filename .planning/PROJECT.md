# MakeNote

## What This Is

MakeNote (`mn`) is a Python CLI tool for developers who want to quickly log notes about completed work directly from the terminal. Notes are stored as JSON Lines in a GitHub repository, using the `gh` CLI for all GitHub interactions — no web app, no database, no friction.

v1.0 is shipped: `mn d "fixed the login bug"` pushes a timestamped note to GitHub in one command.

## Core Value

Logging a note must be as fast as a terminal command — the power-user path (`mn d "note"`) should require zero interaction.

## Requirements

### Validated

- ✓ `mn` launches interactive flow: arrow-key subject picker → inline note input → push to GitHub — v1.0
- ✓ `mn d` skips subject picker, uses default subject, prompts for note inline — v1.0
- ✓ `mn d "note content"` skips all interaction, logs directly — zero prompts — v1.0
- ✓ `mn list` prints the most recent notes across all subjects (last ~10-20, no filter) — v1.0
- ✓ `mn config` interactive editor for repo, default subject, and subject list — v1.0
- ✓ First run with no config auto-triggers `mn config` setup flow — v1.0
- ✓ Notes stored as JSONL — one JSON object per line, appended per note — v1.0
- ✓ GitHub writes via `gh` API directly (no local clone) — read current file, append, update — v1.0
- ✓ Config stored at `~/.config/makenote/config.json` — v1.0
- ✓ Distributed via Homebrew personal tap — v1.0 (formula written; release workflow in RELEASING.md)

### Active

- [ ] Published to PyPI as secondary distribution (DIST-03)
- [ ] Filter `mn list` by subject (LIST-01)
- [ ] Filter `mn list` by date range (LIST-02)

### Out of Scope

- Web app or GUI — terminal-only by design
- Database — JSONL files in GitHub are the store
- Direct credential handling — `gh auth login` is the user's responsibility
- Offline queue / retry on GitHub failure — future idea
- Tag detection (`#bugfix`, `#feature`) — future idea

## Context

- v1.0 shipped 2026-03-09: 408 LOC source Python, 711 LOC tests, 3 phases, 7 plans
- Tech stack: Python 3.9+, click, questionary, pytest; GitHub I/O via `gh` CLI subprocess
- `gh` CLI is a hard dependency; must be installed and authenticated
- Notes repo structure: one folder per subject, one `notes.jsonl` per folder, all under a configurable `target_path` subdirectory
- GitHub writes use `gh api` to read the existing file contents, append the new record, and update in place — no local git clone required
- Known tech debt: `constants.py` is dead code (CONFIG_PATH duplicated in config.py); `default_subject` empty-string edge case; formula needs RELEASING.md workflow before brew install works

## Constraints

- **Language**: Python — chosen for packaging convenience (`pyproject.toml` / `console_scripts`)
- **GitHub interaction**: `gh` CLI subprocess only — no direct API tokens or PyGitHub
- **Distribution**: Homebrew tap (primary) + PyPI (secondary)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|------------|
| JSONL over SQLite/flat text | Trivially parsable, append-only, filterable by any tool | ✓ Good — no friction, `gh api` handles it cleanly |
| `gh` CLI over GitHub API directly | No credential management, users already have it | ✓ Good — clean error paths via stdout/stderr classification |
| Direct API write (no clone) | Faster, no local repo state to manage | ✓ Good — SHA-safe read-modify-write works reliably |
| `questionary` for TUI | Lightweight, arrow-key support, no heavy TUI framework | ✓ Good — minimal deps, questionary 2.0 works well |
| `import makenote.config as _cfg` (module import) | Allows pytest monkeypatching of module-level attributes | ✓ Good — pattern needed for all inter-module test isolation |

---
*Last updated: 2026-03-09 after v1.0 milestone*
