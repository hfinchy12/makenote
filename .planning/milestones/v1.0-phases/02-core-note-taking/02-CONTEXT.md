# Phase 2: Core Note-Taking - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can log notes to GitHub from the terminal using any interaction level, and read recent notes back. Covers `mn` (interactive subject picker + note input), `mn d` (skip picker, prompt for note), `mn d "note"` (zero interaction), `mn list` (read recent notes), and GitHub write via `gh api`. Distribution and config management are separate phases.

</domain>

<decisions>
## Implementation Decisions

### mn command flow
- Note input uses `questionary.text("Note:")` — consistent with existing config flow pattern
- After successful push: print `Note logged.` — brief confirmation, plain text
- When no subjects configured: print `Error: no subjects configured. Run mn config to add subjects.` and exit
- "Add New" in the subject picker persists the new subject to `config.json` permanently (not session-only)

### GitHub write errors
- All failures: error-and-exit, no retry — consistent with the no-offline-queue decision in PROJECT.md
- `gh` not installed: `Error: gh CLI not found. Install from https://cli.github.com`
- `gh` not authenticated: `Error: gh not authenticated. Run: gh auth login`
- SHA conflict (stale write): `Error: write conflict — file may have changed. Try again.`
- All errors follow the established `Error: <message>` format from Phase 1

### Claude's Discretion
- `mn list` display format (fields shown, ordering, truncation) — Claude decides
- Exact `gh api` endpoint and payload structure — Claude determines from `gh` docs during research
- Module structure for `github.py` — Claude decides

</decisions>

<specifics>
## Specific Ideas

No specific requirements beyond what's captured above — open to standard approaches for list display and github.py structure.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `config.load_config()`: returns `{repo, default_subject, subjects}` — Phase 2 reads this for all note commands
- `config.save_config(data)`: Phase 2 uses this when "Add New" persists a subject
- `questionary.select()` and `questionary.text()`: already imported and tested; note input and subject picker use these
- `cli.py` `@main.command()` pattern: `mn`, `mn d`, and `mn list` are new Click subcommands on the existing `main` group

### Established Patterns
- Every `questionary.ask()` return checked for `None` → `sys.exit(0)` (Ctrl-C exits cleanly)
- `cli.py` imports config as `import makenote.config as _cfg` for monkeypatching compatibility
- Plain text output only — no ANSI colors, no styled output
- Errors: `Error: <message>` prefix, direct, no emoji

### Integration Points
- `mn` and `mn d` call `load_config()` to get `default_subject` and `subjects`
- GitHub write module (`github.py`, new) called from note commands; takes `repo`, `subject`, `note_text`
- `mn list` reads from GitHub via `gh api` and prints to stdout

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-core-note-taking*
*Context gathered: 2026-03-08*
