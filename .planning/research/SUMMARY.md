# Project Research Summary

**Project:** MakeNote (`mn`)
**Domain:** Python CLI developer tool — terminal-first note logger with GitHub backing store
**Researched:** 2026-03-08
**Confidence:** MEDIUM

## Executive Summary

MakeNote is a terminal-first developer note logger that uses GitHub as its native backing store via the `gh` CLI. This positions it differently from all comparable tools (jrnl, dnote, nb) which treat local storage as primary and GitHub/cloud as optional sync. The entire credential management problem is delegated to `gh`, which means the tool has zero auth surface area of its own — a genuine differentiator. The recommended implementation approach is a small Python package (Click + questionary + rich) with a 6-module architecture that separates CLI routing, TUI interaction, GitHub I/O, and config management into distinct, independently testable layers.

The recommended build order follows dependency topology: `config.py` first (everything depends on it), then `github.py` (the only subprocess boundary), then the thin CLI router in `main.py`, then the interactive flow and list display, and finally packaging and Homebrew distribution. The MVP feature set is small and deliberate — four subcommands (`mn`, `mn d`, `mn list`, `mn config`) plus first-run detection and clear error messages. Everything else is explicitly deferred to v1.x or v2+. The key design constraint is protecting the zero-friction power path (`mn d "note"`) from feature creep.

The dominant risks are in the GitHub I/O layer: the `gh api` PUT endpoint requires the existing file SHA (invisible during prototyping against a fresh repo, surfaces on second write), base64-encoded content from GitHub includes embedded newlines that must not be stripped before decoding, and JSONL append logic must guard against missing trailing newlines or two records fuse into one unparseable line. These are specific, well-defined problems with specific prevention strategies — they are addressable, not architectural risks. The Homebrew distribution phase has its own distinct gotchas (resource blocks, SHA pinning) that are isolated to that phase and do not affect core functionality.

## Key Findings

### Recommended Stack

The stack is minimal and appropriate for the problem. Python 3.11+ with Click 8.1 for CLI argument parsing, questionary 2.x for interactive arrow-key prompts, and rich 13.x for formatted list output covers the entire runtime surface. The build backend is hatchling (PyPA-recommended for new projects), the dev toolchain is uv + ruff, and testing uses pytest + pytest-subprocess for mocking `gh` calls without spawning real processes. All dependencies are well-matched to the use case — no framework is overweight for what it's doing.

Full details: `.planning/research/STACK.md`

**Core technologies:**
- Python 3.11+: runtime — 3.11+ required for stdlib `tomllib` and improved error messages
- Click 8.1: CLI argument parsing and command dispatch — de-facto standard, explicit style preferred over Typer for a 4-command surface
- questionary 2.x: interactive prompts — correct fit for arrow-key select + text input; explicitly named in PROJECT.md
- rich 13.x: formatted terminal output for `mn list` — aligned columns, color, note previews
- hatchling: build backend — PyPA-recommended default; `[project.scripts]` entry point wires `mn` command
- uv: dev dependency management — dramatically faster than pip+venv; 2025 community standard
- pytest + pytest-subprocess: testing — mock `gh` CLI calls without hitting GitHub

**What NOT to use:**
- PyInstaller/shiv — binary bundling is wrong approach for Homebrew Python formula
- PyGitHub / direct API tokens — `gh` CLI is the auth layer by design
- Textual/Urwid — full TUI frameworks are massive overkill for two interaction patterns

### Expected Features

The MVP is well-scoped. All table-stakes features are achievable with low-to-medium complexity. The zero-prompt power path (`mn d "note"`) is the core differentiator and must be protected from scope creep. The "Add New" subject inline option and `mn list --subject` filtering are natural v1.x additions once daily use confirms the friction points.

Full details: `.planning/research/FEATURES.md`

**Must have (table stakes):**
- `mn d "note"` — zero-interaction note logging to default subject; the daily habit path
- `mn` — interactive subject picker + note input for non-default subjects
- `mn list` — fetch and display last 10-20 notes in human-readable format
- `mn config` — interactive editor for repo, default subject, subjects list
- First-run detection — auto-route to `mn config` if no config exists; no silent failure
- Clear error messages — missing `gh`, unauthenticated `gh`, GitHub API failures all produce actionable messages
- `--help` and `--version` flags — standard CLI contract

**Should have (competitive):**
- "Add New" inline in the subject picker — eliminates needing `mn config` just to start a new project
- `mn list --subject <name>` — filter output by subject; add when "Project A only" becomes real friction
- Richer list formatting (color, column alignment) — add when plain output feels insufficient in daily use

**Defer (v2+):**
- `mn edit` — mutating GitHub file contents via API is complex; accept imperfection in v1
- Offline queue — adds local state management and dual-storage complexity
- Tag detection / filtering — tags only pay off when query surface exists; `jq` covers power users for now
- Shell completions — useful polish, but not needed to validate the concept
- Full-text search in `mn list` — requires fetching all JSONL from GitHub; `jq`/`grep` on raw JSONL covers this

**Deliberate trade-offs (not oversights):** No offline support, no note editing, no encryption. Document in README so users self-select appropriately.

### Architecture Approach

The architecture is a 4-layer separation: Entry (CLI routing in `main.py`), Interaction (TUI flows in `flow.py`, `config_ui.py`, `list.py`), Service (pure business logic in `config.py`, `github.py`), and External (`gh` CLI subprocess and `~/.config/makenote/config.json`). The critical structural rule is that `github.py` is the only subprocess boundary — no other module calls `subprocess` directly. This makes mocking external calls trivial in tests. Config is loaded by `main.py` and passed as arguments to service modules — service modules do not reach for config themselves.

Full details: `.planning/research/ARCHITECTURE.md`

**Major components:**
1. `main.py` — entry point, argument parsing, command dispatch, first-run detection guard, preflight checks
2. `flow.py` — interactive TUI: subject picker (questionary) + note input; calls `github.py` after collecting input
3. `config.py` — load/save `~/.config/makenote/config.json`; validate keys; supply defaults; filesystem-only (never calls GitHub)
4. `github.py` — all `subprocess.run(["gh", "api", ...])` calls; read JSONL, build payload, append record, write back; typed Python functions as the public API
5. `list.py` — reads all JSONL via `github.py`; sorts by date; formats and prints N recent records
6. `config_ui.py` — interactive TUI for config editing; calls `config.py` functions; never imports `github.py`

**Key data flow constraints:**
- Config never calls GitHub
- TUI modules never call `gh` directly
- `main.py` never builds GitHub payloads
- `github.py` never prompts the user

### Critical Pitfalls

Full details: `.planning/research/PITFALLS.md`

1. **gh api requires SHA for file updates** — GitHub Contents API PUT requires the existing file SHA; missing it causes HTTP 422. The bug is invisible on a fresh repo (first write creates file without SHA), surfaces on every write after that. Fix: GET and PUT are an atomic pair in one function in `github.py`. Test: write two notes to the same subject, verify both persist.

2. **Base64 content from GitHub has embedded newlines** — GitHub base64 includes `\n` every ~76 chars. Do not strip or transform before calling `base64.b64decode()`. Stripping silently corrupts multi-line content. Test with a fixture that simulates real GitHub base64 response.

3. **JSONL append missing trailing newline** — if existing content doesn't end with `\n`, appending a new record fuses two JSON objects on one line; both become unparseable. The defensive formula: `existing.rstrip('\n') + '\n' + new_record + '\n'` if content exists, else `new_record + '\n'`.

4. **gh not installed / not authenticated** — without a startup preflight check, `mn` fails with a Python traceback (`FileNotFoundError`) when `gh` is absent. Run `shutil.which('gh')` and `gh auth status` at CLI entry before any command logic executes.

5. **questionary crashes on non-TTY stdin** — running `mn` in CI, piped input, or scripted contexts causes `prompt_toolkit` to hang or crash. Guard every interactive flow with `sys.stdin.isatty()` before calling any `questionary` function. Never call the `questionary` layer in tests — test flow and GitHub logic independently with mocks.

6. **Homebrew virtualenv_install_with_resources requires all transitive dependencies declared** — `questionary` depends on `prompt_toolkit`; both must appear as `resource` blocks in the formula. Use `poet makenote` to auto-generate correct resource blocks with SHA256 for every release.

## Implications for Roadmap

Based on combined research, the architecture's dependency topology and pitfall prevention map directly onto a natural phase structure. The build order from ARCHITECTURE.md is the phase order.

### Phase 1: Project Scaffold and Entry Point

**Rationale:** The `pyproject.toml` entry point (`mn = makenote.main:main`) must be verified working end-to-end before any logic is added. Pitfall 8 (wrong `console_scripts` target) is invisible at install time and only surfaces at runtime — catching it first prevents a false foundation. Everything downstream depends on the `mn` command being real.
**Delivers:** Installable `mn` command that prints a version string; `pyproject.toml` configured with hatchling; `uv` dev environment wired; `ruff` configured; pytest running.
**Addresses:** `--help`, `--version` table-stakes features; first-run smoke test habit established.
**Avoids:** Pitfall 8 (wrong entry point target); technical debt of "put all logic in main.py."

### Phase 2: Config Layer

**Rationale:** `config.py` has zero dependencies and everything else needs it. Building and fully testing it before any other module prevents the most common source of silent failures (missing config causing `KeyError` deep in a command). Pitfall 5 (first-run config not detected) must be addressed here, not retrofitted later.
**Delivers:** `config.py` with load/save/validate/defaults; `ConfigNotFoundError` exception; `mn config` interactive setup via `config_ui.py`; `~/.config/makenote/config.json` written correctly.
**Addresses:** `mn config` command; first-run detection; table-stakes config command feature.
**Avoids:** Pitfall 5 (missing config causes traceback); global variable anti-pattern (config loaded at dispatch, passed as argument).

### Phase 3: GitHub I/O Layer

**Rationale:** `github.py` is the only subprocess boundary and the highest-risk module. All critical pitfalls (SHA requirement, base64 decode, stderr capture, JSONL newlines) live here. Building and fully testing this layer in isolation — with `pytest-subprocess` mocking all `gh` calls — before wiring it into the interactive flow prevents these bugs from being obscured by UI complexity.
**Delivers:** `github.py` with `read_jsonl()`, `write_jsonl()`, `append_note()` functions; `GhCommandError` exception class surfacing stderr; `gh` preflight check (`shutil.which` + `gh auth status`).
**Addresses:** GitHub write (the highest-value table-stakes feature); clear error messages for auth/network failures.
**Avoids:** Pitfall 1 (SHA for updates), Pitfall 2 (base64 decode), Pitfall 3 (stderr not captured), Pitfall 4 (gh not installed), Pitfall 6 (JSONL newline corruption).

### Phase 4: Core Note-Taking Commands

**Rationale:** With config and GitHub I/O tested, the interactive flow (`flow.py`) and zero-interaction path (`mn d "note"`) can be wired together without hidden complexity. The TTY guard for questionary (Pitfall 7) and Ctrl-C handling belong in this phase.
**Delivers:** `mn d "note"` zero-interaction path; `mn` interactive subject picker + note input; `mn d` (default subject, prompt for note only); confirmation output after every successful write.
**Addresses:** P1 table-stakes: `mn d "note"` power path, interactive subject picker, clear success feedback.
**Avoids:** Pitfall 7 (questionary non-TTY crash); TUI/I/O mixing anti-pattern; global state anti-pattern.

### Phase 5: Note Recall (`mn list`)

**Rationale:** Read-only GitHub access via the already-tested `github.py`. Lower risk than write operations; good confidence builder. `list.py` can be developed and tested against JSONL fixtures without any live GitHub calls.
**Delivers:** `mn list` fetching and displaying last N notes across all subjects in human-readable format using `rich`; "Fetching notes..." feedback for slow connections.
**Addresses:** `mn list` table-stakes feature; readable list output.
**Avoids:** UX pitfall of silent hang on slow connections.

### Phase 6: Packaging and Homebrew Distribution

**Rationale:** Distribution is isolated from core functionality. Homebrew pitfalls (SHA256 pinning, missing resource blocks) are entirely specific to this phase and do not affect PyPI or development installs. This phase has the highest external verification requirements — clean-environment testing is mandatory before publishing.
**Delivers:** PyPI-publishable package; Homebrew tap with formula; release checklist including `poet`-generated resource blocks, SHA256 verification, and clean-environment install test.
**Addresses:** Homebrew and PyPI distribution table-stakes.
**Avoids:** Pitfall 9 (Homebrew SHA mismatch after re-tagging), Pitfall 10 (missing resource blocks in formula).

### Phase Ordering Rationale

- **Config before GitHub:** `github.py` accepts explicit parameters (repo, path) — it does not read config. But every caller of `github.py` gets those values from config. Config must exist and be tested before it's safe to wire callers.
- **GitHub before flow:** `flow.py` calls `github.py`. Testing flow logic in isolation requires mocking `github.py` functions — those functions must exist before they can be mocked meaningfully.
- **Commands before list:** `mn list` is read-only and lower-risk. The write path (`mn d`, `mn`) is higher-value and higher-risk — validate it first.
- **Everything before packaging:** Homebrew distribution requires a stable, tested package. Attempting Homebrew setup on a partially-functional tool wastes significant time.

### Research Flags

Phases with well-documented patterns (can skip research-phase):
- **Phase 1 (Scaffold):** Standard pyproject.toml + hatchling + uv — PyPA docs cover this completely.
- **Phase 2 (Config):** JSON config with pathlib — trivial; no research needed.
- **Phase 4 (Commands):** questionary + Click patterns are well-established.
- **Phase 5 (List):** rich formatting is well-documented.

Phases that may benefit from targeted research during planning:
- **Phase 3 (GitHub I/O):** Verify current `gh api` behavior for file update endpoint (SHA requirement, base64 format) against `gh api --help` and GitHub REST docs before implementing. The core pattern is known but the exact request format should be confirmed — do not rely solely on training data for the payload structure.
- **Phase 6 (Homebrew):** Run `brew audit` against the formula and verify `virtualenv_install_with_resources` behavior against current Homebrew Python documentation before publishing the tap. Homebrew's Python formula guidelines have evolved.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Click, questionary, rich, hatchling are stable and well-matched. Specific version numbers (questionary 2.0.x, Click 8.1.x, rich 13.x) require verification at PyPI before pinning — training data cutoff means newer minor versions may have shipped. |
| Features | HIGH | Feature landscape is well-established. Competitor feature analysis and table-stakes expectations are grounded in stable CLI tool conventions and direct project brief constraints. MVP scope is clear and defensible. |
| Architecture | MEDIUM | Patterns (thin CLI layer, subprocess isolation in gateway module, config-as-argument) are conservative, well-established Python CLI idioms. The 6-module structure directly matches the project's complexity level. Verify `questionary` null-return on Ctrl-C behavior in docs during implementation. |
| Pitfalls | MEDIUM | GitHub Contents API SHA requirement and base64 format are specific, verifiable behaviors — medium confidence because `gh api` passthrough behavior should be confirmed against current `gh` docs. JSONL and entry-point pitfalls are HIGH confidence (trivially verifiable). Homebrew patterns are MEDIUM (formula guidelines evolve). |

**Overall confidence:** MEDIUM

### Gaps to Address

- **Exact `gh api` request format for file updates:** Confirm SHA field name, base64 encoding expectations, and commit message requirements against `gh api repos/{owner}/{repo}/contents/{path} --help` or GitHub REST API reference during Phase 3. Do not implement from training data alone.
- **questionary version at PyPI:** Before pinning `questionary>=2.0` in `pyproject.toml`, verify at pypi.org/project/questionary that 2.x is current stable and check the changelog for any breaking changes since the training data cutoff.
- **Homebrew Python formula guidelines:** Before Phase 6, read https://docs.brew.sh/Python-for-Formula-Authors to confirm `virtualenv_install_with_resources` is still the correct pattern and that `poet` is still the recommended resource-block generator.
- **`gh auth status` exit code behavior:** Confirm that exit 0 = authenticated, exit 1 = not authenticated (vs. other failure modes) before implementing the preflight check.

## Sources

### Primary (HIGH confidence)
- `.planning/PROJECT.md` — project intent, questionary and `gh` CLI constraints, command surface (`mn`, `mn d`, `mn list`, `mn config`)
- `.planning/notes/PLAN.md` — original project planning notes; confirms module structure intent
- Python Packaging Authority (pypa.io) — pyproject.toml, hatchling, console_scripts entry point behavior
- JSONL specification (jsonlines.org) — newline-terminated JSON records format

### Secondary (MEDIUM confidence)
- Training knowledge (cutoff August 2025) — Click, questionary, rich, hatchling, uv ecosystem state; GitHub Contents API read/write via `gh api`; Homebrew Python formula patterns; jrnl/dnote/nb feature comparison
- Python CLI architecture conventions — thin CLI layer, subprocess isolation, config-as-argument patterns; stable idioms in Click and Typer documentation

### Tertiary (LOW confidence / needs verification)
- questionary 2.0.x version number — verify at pypi.org before pinning
- Click 8.1.x version number — verify at pypi.org (Click 8.2 may have shipped)
- rich 13.x version number — verify at pypi.org (rich releases frequently)
- `gh api` exact request payload format — verify against `gh` docs or GitHub REST API reference before implementing `github.py`

---
*Research completed: 2026-03-08*
*Ready for roadmap: yes*
