# Architecture Research

**Domain:** Python CLI tool — developer note logger with GitHub integration
**Researched:** 2026-03-08
**Confidence:** MEDIUM — core patterns drawn from well-established Python CLI conventions (training knowledge); no external sources available to verify during this session. Patterns are conservative and grounded in `click`/`questionary` idioms that have been stable for several years.

---

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Entry Layer                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  main.py  — command routing (mn / mn d / mn list /       │   │
│  │             mn config), first-run detection              │   │
│  └──────────────┬──────────────┬───────────────┬────────────┘   │
└─────────────────┼──────────────┼───────────────┼────────────────┘
                  │              │               │
┌─────────────────┼──────────────┼───────────────┼────────────────┐
│              Interaction Layer (TUI flows)                      │
│  ┌───────────┐  │  ┌─────────────────┐  │  ┌──────────────┐    │
│  │  flow.py  │◄─┘  │   config_ui.py  │◄─┘  │   list.py    │    │
│  │ (note     │     │  (interactive   │     │  (display    │    │
│  │  intake)  │     │   config edit)  │     │   recent)    │    │
│  └─────┬─────┘     └────────┬────────┘     └──────┬───────┘    │
└────────┼───────────────────┼──────────────────────┼────────────┘
         │                   │                      │
┌────────┼───────────────────┼──────────────────────┼────────────┐
│              Service Layer (pure business logic)                │
│         ▼                  ▼                      ▼            │
│  ┌─────────────┐  ┌──────────────┐        ┌────────────────┐   │
│  │  github.py  │  │  config.py   │        │  config.py     │   │
│  │  (read,     │  │  (load/save) │        │  (load/save)   │   │
│  │   append,   │  └──────────────┘        └────────────────┘   │
│  │   update)   │                                               │
│  └──────┬──────┘                                               │
└─────────┼──────────────────────────────────────────────────────┘
          │
┌─────────┼──────────────────────────────────────────────────────┐
│              External Layer                                     │
│         ▼                                                       │
│  ┌──────────────┐      ┌───────────────────────┐               │
│  │  gh CLI      │      │  ~/.config/makenote/  │               │
│  │  (subprocess)│      │  config.json          │               │
│  └──────────────┘      └───────────────────────┘               │
│         │                                                       │
│  ┌──────────────┐                                               │
│  │  GitHub API  │                                               │
│  │  (via gh)    │                                               │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Communicates With |
|-----------|----------------|-------------------|
| `main.py` | Entry point, argument parsing, command dispatch, first-run detection | `flow.py`, `config_ui.py`, `list.py`, `config.py` |
| `flow.py` | Interactive TUI for note intake: subject picker + note prompt | `config.py` (reads subjects/defaults), `github.py` (writes note) |
| `config_ui.py` | Interactive TUI for config editing: repo, default subject, subject list | `config.py` (reads/writes config) |
| `config.py` | Load and save `~/.config/makenote/config.json`; validate structure; provide defaults | `~/.config/makenote/config.json` (filesystem) |
| `github.py` | Read current JSONL file via `gh api`, append new record, write back via `gh api` | `gh` CLI subprocess |
| `list.py` | Read all JSONL data via `gh api`, sort by date, format and print recent N records | `github.py` (or directly calls `gh` for read-only fetches) |

---

## Recommended Project Structure

```
makenote/
├── pyproject.toml          # packaging; declares `mn = makenote.main:main`
├── README.md
├── tests/
│   ├── test_config.py
│   ├── test_github.py
│   ├── test_flow.py
│   └── test_list.py
└── makenote/
    ├── __init__.py         # version constant
    ├── main.py             # entry point + command routing
    ├── flow.py             # interactive note intake TUI
    ├── config_ui.py        # interactive config editor TUI (or inline in config.py for small scope)
    ├── config.py           # config read/write, schema validation, defaults
    ├── github.py           # all gh subprocess calls: read file, build payload, write file
    └── list.py             # fetch notes, format for terminal output
```

### Structure Rationale

- **`main.py` as thin router:** Argument parsing lives here and nowhere else. Each command dispatches to the appropriate module function — no business logic in `main.py`. This means each module is independently testable without invoking Click/argument parsing.
- **`flow.py` separated from `github.py`:** TUI interaction (questionary prompts) is separate from GitHub I/O. This allows testing the flow logic by injecting mock prompt responses without needing a live `gh` CLI.
- **`github.py` as the only subprocess boundary:** All `subprocess.run(['gh', ...])` calls live in one file. This makes mocking external calls trivial in tests — mock one module, not scattered calls.
- **`config.py` as pure data:** No TUI in config.py. It reads and writes JSON, validates keys, supplies defaults. The `config_ui.py` (or a `config` function in `main.py` for small scope) calls config.py functions — config.py never imports questionary.
- **`tests/` at package root:** Standard `pytest` convention. Tests import from `makenote.*` directly.

---

## Architectural Patterns

### Pattern 1: Thin CLI Layer, Fat Service Layer

**What:** The Click-decorated command functions in `main.py` do nothing except validate arguments and call into service modules. All logic lives in service modules that accept plain Python values (strings, dicts), not Click objects.

**When to use:** Always, for any CLI tool larger than a single-file script.

**Trade-offs:** Slightly more files to create upfront; enables full test coverage without Click test runner overhead.

**Example:**
```python
# main.py — THIN
@click.command()
@click.argument("note", required=False)
def default_cmd(note):
    cfg = config.load()
    if note:
        github.append_note(cfg, cfg["default_subject"], note)
    else:
        flow.run_default(cfg)

# flow.py — FAT (testable independently)
def run_default(cfg: dict) -> None:
    note_text = questionary.text("Note:").ask()
    if note_text:
        github.append_note(cfg, cfg["default_subject"], note_text)
```

### Pattern 2: Subprocess Isolation in a Gateway Module

**What:** All `subprocess.run(["gh", ...])` calls are funneled through a single `github.py` module that exposes typed Python functions (`read_file(repo, path) -> str`, `write_file(repo, path, content, sha) -> None`). No other module ever calls `subprocess` directly.

**When to use:** Any time an external process is a hard dependency.

**Trade-offs:** Adds one indirection layer; pay-off is that tests mock `github.py` functions rather than patching `subprocess` throughout the codebase.

**Example:**
```python
# github.py
def read_jsonl(repo: str, path: str) -> tuple[str, str]:
    """Returns (content_decoded, sha) for the file at path in repo."""
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/contents/{path}"],
        capture_output=True, text=True, check=True
    )
    data = json.loads(result.stdout)
    content = base64.b64decode(data["content"]).decode()
    return content, data["sha"]

def write_jsonl(repo: str, path: str, content: str, sha: str, message: str) -> None:
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "sha": sha,
    }
    subprocess.run(
        ["gh", "api", "--method", "PUT", f"repos/{repo}/contents/{path}",
         "--input", "-"],
        input=json.dumps(payload), capture_output=True, text=True, check=True
    )
```

### Pattern 3: First-Run Guard at Entry Point

**What:** `main.py` checks for a valid config before dispatching any command (except `mn config`). If config is absent or incomplete, it immediately redirects to the config setup flow and exits cleanly.

**When to use:** Any CLI tool that requires user configuration before first use.

**Trade-offs:** Slight coupling between `main.py` and `config.py`; acceptable because first-run detection is a routing concern.

**Example:**
```python
def main():
    cfg = config.load()
    if not config.is_valid(cfg) and not is_config_command():
        click.echo("No config found. Running setup...")
        config_ui.run_setup(cfg)
        return
    # proceed with normal routing
```

---

## Data Flow

### Flow: `mn d "note content"` (zero-interaction path)

```
User: mn d "Fixed OAuth bug"
    ↓
main.py: parse args → note="Fixed OAuth bug", command=default
    ↓
config.py: load() → cfg dict
    ↓
github.py: read_jsonl(cfg["target_repo"], path_for_subject)
    ↓ (content_str, sha)
github.py: build new record {"date":..., "subject":..., "note":...}
    ↓ append to content_str
github.py: write_jsonl(repo, path, new_content, sha, commit_message)
    ↓
gh CLI → GitHub API → file updated in repo
    ↓
main.py: print confirmation to stdout
```

### Flow: `mn` (full interactive path)

```
User: mn
    ↓
main.py: no args → dispatch to flow.run_interactive(cfg)
    ↓
flow.py: questionary.select(subjects + "Add New") → subject
    ↓ (if "Add New": prompt for name, config.add_subject(), save)
flow.py: questionary.text("Note:") → note_text
    ↓
github.py: read_jsonl → append → write_jsonl
    ↓
stdout: confirmation
```

### Flow: `mn config`

```
User: mn config
    ↓
main.py: dispatch to config_ui.run_editor(cfg)
    ↓
config_ui.py: questionary prompts for repo / default_subject / subjects
    ↓
config.py: save(updated_cfg) → ~/.config/makenote/config.json
    ↓
stdout: "Config saved."
```

### Flow: `mn list`

```
User: mn list
    ↓
main.py: dispatch to list.run(cfg)
    ↓
list.py: for each subject in cfg["subjects"]:
         github.py: read_jsonl(repo, path) → raw JSONL string
    ↓
list.py: parse all records, sort by date descending, take N
    ↓
list.py: format and print to stdout
```

### Key Data Flow Boundaries

1. **Config never calls GitHub.** `config.py` is filesystem-only. It does not know about GitHub.
2. **TUI modules never call `gh` directly.** `flow.py` and `config_ui.py` call `github.py` functions — never `subprocess` directly.
3. **`main.py` never builds GitHub payloads.** It reads config and dispatches; it does not construct JSON or base64-encode content.
4. **`github.py` never prompts the user.** It raises exceptions on failure; callers decide how to surface errors.

---

## Suggested Build Order

Dependencies between components drive this order. Build the layer that has no dependencies first.

| Step | Component | Rationale |
|------|-----------|-----------|
| 1 | `config.py` | No dependencies. Everything else needs config. Build and test first. |
| 2 | `github.py` | Depends only on stdlib + `gh` binary. Core I/O layer. Mock it for all downstream tests. |
| 3 | `main.py` skeleton | Routing shell with stub dispatchers. Establishes the `mn` command works end-to-end (even if stubs). |
| 4 | `flow.py` | Depends on `config.py` + `github.py`. The core use case (`mn` and `mn d`). |
| 5 | `list.py` | Read-only GitHub access via `github.py`. Lower risk, good confidence builder. |
| 6 | `config_ui.py` | Depends on `config.py`. Editing flow. Less critical than note-taking. |
| 7 | First-run detection | Wire `main.py` guard once `config_ui.py` exists. |
| 8 | Packaging + distribution | `pyproject.toml`, Homebrew formula. Final step once functionality is solid. |

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| `gh` CLI | `subprocess.run(["gh", "api", ...])`, `capture_output=True`, `check=True` | All in `github.py`. Raises `subprocess.CalledProcessError` on non-zero exit. Check `gh auth status` on startup if desired. |
| GitHub Contents API | JSON request/response via `gh api` (REST, not GraphQL) | Read: `GET /repos/{owner}/{repo}/contents/{path}`. Write: `PUT` with `message`, `content` (base64), `sha`. Requires file SHA for updates — must read before write. |
| `~/.config/makenote/config.json` | Standard `json.load` / `json.dump` via `pathlib.Path` | Create parent dirs with `mkdir(parents=True, exist_ok=True)`. Handle `FileNotFoundError` as "no config yet". |
| `questionary` | Direct API calls (`questionary.select()`, `questionary.text()`) | Returns `None` if user hits Ctrl-C; callers must handle `None` gracefully (abort without traceback). |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `main.py` → `flow.py` | Direct function call with `cfg` dict | Pass config as argument, not global state |
| `main.py` → `github.py` | Never — main does not call github directly | All GitHub I/O goes through flow/list modules |
| `flow.py` → `github.py` | Direct function call | `github.append_note(cfg, subject, note_text)` |
| `config_ui.py` → `config.py` | Direct function call | `config.save(updated_cfg)` |
| `list.py` → `github.py` | Direct function call | Read-only: `github.read_jsonl(repo, path)` |

---

## Anti-Patterns

### Anti-Pattern 1: Mixing TUI and I/O in the Same Module

**What people do:** Put `questionary` prompts and `subprocess.run(["gh", ...])` calls in the same function, or inside `main.py` command handlers.

**Why it's wrong:** Makes unit testing require both a mocked terminal AND a mocked subprocess. Doubles the test setup complexity for every test.

**Do this instead:** Keep `flow.py` responsible for prompts only. It calls `github.py` functions after collecting input. Mock `github.py` in flow tests; mock `questionary` separately.

### Anti-Pattern 2: Reading Config Inside Service Modules

**What people do:** `github.py` or `flow.py` calls `config.load()` internally to get the repo path.

**Why it's wrong:** Creates hidden coupling. Tests for `github.py` now require a real or mocked config file on disk. Harder to unit-test with arbitrary inputs.

**Do this instead:** Callers (main.py, flow.py) load config once and pass required values as function arguments. Service modules accept explicit parameters (`repo: str`, `path: str`) — they do not reach for config themselves.

### Anti-Pattern 3: Ignoring `gh` Exit Codes

**What people do:** Call `subprocess.run(["gh", "api", ...])` without `check=True` and proceed assuming success.

**Why it's wrong:** Silent failures. If `gh` is not authenticated or the repo doesn't exist, the process exits non-zero but the Python code continues, potentially overwriting a file with corrupt data.

**Do this instead:** Always use `check=True` (raises `subprocess.CalledProcessError` on non-zero exit). Catch it at the command level in `main.py` and print a human-friendly error.

### Anti-Pattern 4: Storing State Between Commands via Global Variables

**What people do:** Load config into a module-level global dict at import time; other modules reference it directly.

**Why it's wrong:** Test isolation breaks — tests share state. Module import order affects behavior.

**Do this instead:** Load config at the top of each command dispatch in `main.py` and pass it down as a function argument. Stateless service modules.

---

## Scaling Considerations

This is a local CLI tool; "scaling" means handling more subjects and notes, not user traffic.

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 10 subjects, 500 notes | Current architecture is exactly right. Single JSONL per subject, read whole file per request. |
| 50 subjects, 10k notes | `mn list` becomes slow (fetches all subject files). Add date-range metadata or a local cache file. No rewrite needed. |
| 100+ subjects | Consider an index file (one JSON dict mapping subject → last-modified date) to avoid fetching all JSONL files for `mn list`. Single architecture addition, no structural change. |

**First bottleneck:** `mn list` fetches one file per subject via `gh api`. At ~20 subjects this is already 20 sequential HTTP calls. Solution: parallelize with `concurrent.futures.ThreadPoolExecutor` in `list.py`, or add a flat index. No architectural change required.

---

## Sources

- Python CLI architecture patterns: training knowledge, conservative conventions from `click` and `typer` documentation idioms (MEDIUM confidence — well-established, stable patterns)
- GitHub Contents API read/write via `gh api`: knowledge of `gh api` REST passthrough behavior (MEDIUM confidence — verify SHA-required-for-update behavior against `gh api --help` or GitHub REST docs before implementation)
- `questionary` null-return on Ctrl-C: documented behavior in questionary library (MEDIUM confidence — verify in questionary docs during implementation)
- Project structure proposal: directly derived from PLAN.md in `.planning/notes/` (HIGH confidence for intent match)

---

*Architecture research for: MakeNote (`mn`) — Python CLI developer note logger*
*Researched: 2026-03-08*
