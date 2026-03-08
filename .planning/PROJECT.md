# MakeNote

## What This Is

MakeNote (`mn`) is a Python CLI tool for developers who want to quickly log notes about completed work directly from the terminal. Notes are stored as JSON Lines in a GitHub repository, using the `gh` CLI for all GitHub interactions — no web app, no database, no friction.

## Core Value

Logging a note must be as fast as a terminal command — the power-user path (`mn d "note"`) should require zero interaction.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] `mn` launches interactive flow: arrow-key subject picker → inline note input → push to GitHub
- [ ] `mn d` skips subject picker, uses default subject, prompts for note inline
- [ ] `mn d "note content"` skips all interaction, logs directly — zero prompts
- [ ] `mn list` prints the most recent notes across all subjects (last ~10-20, no filter)
- [ ] `mn config` interactive editor for repo, default subject, and subject list
- [ ] First run with no config auto-triggers `mn config` setup flow
- [ ] Notes stored as JSONL — one JSON object per line, appended per note
- [ ] GitHub writes via `gh` API directly (no local clone) — read current file, append, update
- [ ] Config stored at `~/.config/makenote/config.json`
- [ ] Distributed via Homebrew personal tap
- [ ] Published to PyPI as secondary distribution

### Out of Scope

- Web app or GUI — terminal-only by design
- Database — JSONL files in GitHub are the store
- Direct credential handling — `gh auth login` is the user's responsibility
- Note filtering in `mn list` (v1 shows latest N, filtering is future)
- Offline queue / retry on GitHub failure — future idea
- Tag detection (`#bugfix`, `#feature`) — future idea

## Context

- Targets developers already using terminal + git + GitHub daily
- `gh` CLI is a hard dependency; must be installed and authenticated
- Notes repo structure: one folder per subject, one `notes.jsonl` per folder, all under a configurable `target_path` subdirectory
- GitHub writes use `gh api` to read the existing file contents, append the new record, and update in place — no local git clone required
- `questionary` library handles arrow-key interactive selection

## Constraints

- **Language**: Python — chosen for packaging convenience (`pyproject.toml` / `console_scripts`)
- **GitHub interaction**: `gh` CLI subprocess only — no direct API tokens or PyGitHub
- **Distribution**: Homebrew tap (primary) + PyPI (secondary)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|------------|
| JSONL over SQLite/flat text | Trivially parsable, append-only, filterable by any tool | — Pending |
| `gh` CLI over GitHub API directly | No credential management, users already have it | — Pending |
| Direct API write (no clone) | Faster, no local repo state to manage | — Pending |
| `questionary` for TUI | Lightweight, arrow-key support, no heavy TUI framework | — Pending |

---
*Last updated: 2026-03-08 after initialization*
