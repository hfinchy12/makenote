# Phase 1: Scaffold and Config - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Set up the Python project scaffold (`pyproject.toml`, package structure, CLI entry point) and implement `mn config` so the tool knows which GitHub repo and default subject to use. Includes first-run detection (auto-trigger config when no config exists), `mn --help`, and `mn --version`.

Creating notes (`mn`, `mn d`, `mn list`) and GitHub writes are separate phases.

</domain>

<decisions>
## Implementation Decisions

### CLI Output Style
- `mn --help` → minimal output: just commands and flags, no examples or descriptions
- `mn --version` → `mn 0.1.0` format (name + version)
- All output is plain text — no ANSI colors, no styled output
- Errors use: `Error: <message>` — plain prefix, direct, no emoji or decoration

### Claude's Discretion
- Config flow UX (step-by-step vs menu) — Claude decides
- Subject management UI within `mn config` (inline list vs add/remove prompts) — Claude decides
- First-run experience messaging — Claude decides
- Python package structure (flat vs `src/` layout) — Claude decides
- pyproject.toml contents (Python version, dependencies, metadata) — Claude decides

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for config flow and package structure.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project, no existing code

### Established Patterns
- `questionary` is the chosen library for interactive prompts (arrow-key selection)
- Config at `~/.config/makenote/config.json`
- Python CLI via `pyproject.toml` `console_scripts` entry point (`mn`)

### Integration Points
- Phase 2 will import config reading logic from this phase
- `gh` CLI is a hard dependency; must be installed and authenticated by the user

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-scaffold-and-config*
*Context gathered: 2026-03-08*
