# Feature Research

**Domain:** Developer note-logging / work-journaling CLI tool (terminal-first, GitHub-backed)
**Researched:** 2026-03-08
**Confidence:** MEDIUM (training data; external search tools unavailable — ecosystem patterns are well-established but not verified against live sources)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Single-command note entry | Every comparable tool (jrnl, dnote, nb) allows `tool "my note"` with no interaction | LOW | The `mn d "note"` path — this is the habit-forming core |
| Interactive prompt fallback | New/infrequent users need a guided path; raw CLI without guidance feels hostile | LOW | `mn` bare command with questionary picker |
| Note timestamp (auto) | Users never want to manually type dates; timestamps are expected to be automatic | LOW | Captured at write time, stored in JSONL record |
| List / recall recent notes | "What did I do today?" is the primary readback pattern — must work without opening GitHub | LOW-MEDIUM | `mn list` — fetch from GitHub, format for terminal |
| Readable list output | Raw JSON is not acceptable in list view; users expect human-readable formatting | LOW | Date + subject + note content in aligned columns |
| Configuration command | Every CLI with persistent settings needs a way to modify them without editing JSON manually | LOW-MEDIUM | `mn config` interactive editor |
| First-run setup prompt | No config = silent failure is a jarring first experience; auto-triggering setup is expected | LOW | Detect missing config, route to `mn config` |
| Clear error messages | Dependency missing (`gh` not installed), auth failure, network error — must surface clearly | LOW | Specific, actionable messages — not tracebacks |
| `--help` / `-h` flag | Standard CLI contract; any CLI without help text feels unfinished | LOW | Click or argparse provides this automatically |
| Version flag (`--version`) | Required for Homebrew tap updates and user troubleshooting | LOW | Trivial to add with packaging metadata |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but materially improve the experience.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Zero-prompt power path (`mn d "note"`) | Removes all friction from the critical path — the tool disappears into the workflow | LOW | Already planned; this is the core differentiator — protect it from feature creep |
| Subject/project scoping | Most journaling tools are flat; project separation makes notes useful at review time | LOW | Folder-per-subject JSONL structure |
| GitHub as the backing store | Notes are already in the tool developers use for everything else; no new app to check | MEDIUM | `gh api` read/append/write; this is the unique constraint that defines the product |
| `gh` CLI delegation (no credentials) | Zero credential management differentiates from tools that require API tokens | LOW | Hard dependency on `gh` being installed and authed — document clearly |
| JSONL format (machine-readable) | Flat text is searchable with `grep`; JSONL is filterable with `jq` — power users love this | LOW | Format decision, not an implementation cost |
| "Add new subject" inline | Avoiding a separate setup step for new projects reduces friction at exactly the moment it matters | LOW | Add as option in the arrow-key picker |
| Terminal-formatted list output | Aligned columns with date, subject, note vs raw JSON is a UX differentiator for readback | LOW-MEDIUM | Consider `rich` or manual column formatting |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem like natural additions but create scope, maintenance, or UX problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Note editing / deletion | Users sometimes log a mistake or want to correct a note | Mutating GitHub file contents via API is fragile; creates conflict potential; breaks append-only guarantee | Accept imperfection in v1; a future `mn edit` can open the raw JSONL in `$EDITOR` |
| Full-text search / filtering in `mn list` | "Show me notes from last week about Project A" is a natural ask | Filtering requires fetching all JSONL content from GitHub — slow, and `jq` / `grep` already solve this for power users | Document the JSONL format and `gh`/`jq` recipes; a v2 `mn list --subject` filter is fine |
| Offline queue / retry | GitHub down shouldn't lose a note | Adds local state management complexity; now you have two storage locations to sync | Flag the constraint clearly; fail loudly with the note text in the error so users can re-run |
| Note tagging UI (`#bugfix`, `#feature`) | Categorization is appealing at setup time | Tags only pay off at query time; no query in v1 means no value delivered; adds schema complexity | Hashtags in note text are already parsable by `jq` later — no special handling needed in v1 |
| Multi-user / team notes | Teams want shared logging | Fundamentally changes the trust and access model; requires repo permissions UX; out of scope for a personal tool | The GitHub repo itself is the sharing mechanism — just use a shared repo |
| Web viewer / dashboard | A GUI summary of logged notes | Contradicts the terminal-first philosophy; adds build surface area; GitHub already renders JSONL readably | GitHub's raw file view and the `mn list` command cover the readback need |
| Automatic note enrichment (git context) | Auto-attach current branch, last commit message | Ambient context is seductive but wrong — it captures what the user was doing, not what they want to record | Explicit notes are better signal than inferred ones; keep it opt-in if ever added |
| Note templates | Structure for standup notes, incident reports, etc. | Templates become configuration debt; users rarely maintain them | Users naturally develop their own text conventions; JSONL is open for tooling on top |
| Local SQLite / sync | "What if GitHub is slow?" | Adds a local storage layer that must be kept in sync; doubles the failure modes | GitHub via `gh api` is fast enough for append-only operations; optimize the API path if needed |

---

## Feature Dependencies

```
[First-run detection]
    └──requires──> [Config read/write]
                       └──requires──> [Config schema defined]

[mn d "note" (power path)]
    └──requires──> [Config read] (default subject must exist)
    └──requires──> [GitHub write] (gh API append)

[mn list]
    └──requires──> [GitHub read] (gh API fetch JSONL)
    └──requires──> [List formatter] (human-readable output)

[Interactive subject picker]
    └──requires──> [Config read] (subjects list)
    └──enhances──> [Add new subject inline]
                       └──requires──> [Config write]

[mn config]
    └──requires──> [Config read/write]

[GitHub write]
    └──requires──> [gh CLI installed + authenticated]
    └──requires──> [Config read] (target_repo, target_path)

[JSONL append logic]
    └──requires──> [GitHub read] (fetch current file SHA + contents)
    └──requires──> [GitHub write] (update file with appended record)
```

### Dependency Notes

- **Power path requires config:** `mn d "note"` silently fails if no default subject is configured — first-run detection must gate this path and route to `mn config`.
- **GitHub write requires GitHub read:** The `gh api` update endpoint requires the current file SHA; you must read before writing. These are one logical unit, not two separate features.
- **List formatter is independent of GitHub read:** The formatter can be developed and tested against fixture JSONL without live GitHub calls — useful for testing.
- **Add new subject enhances the interactive picker:** Baking "Add New" into the arrow-key list prevents the user from needing `mn config` for the common case of starting a new project.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] `mn d "note"` — zero-prompt logging to default subject; this is the daily habit path
- [ ] `mn` — interactive subject picker + inline note input for non-default subjects
- [ ] `mn d` — skips picker, prompts for note only (default subject)
- [ ] `mn list` — fetch and display last ~10-20 notes, human-readable format
- [ ] `mn config` — interactive editor for repo, default subject, subjects list
- [ ] First-run detection — auto-route to `mn config` if no config exists
- [ ] Clear error messages for missing `gh`, unauthenticated `gh`, and GitHub API failures
- [ ] `--help` and `--version` flags

### Add After Validation (v1.x)

Features to add once the core logging loop is stable and used daily.

- [ ] `mn list --subject <name>` — filter list output by subject; add when "I want to see just Project A" becomes a real friction point
- [ ] "Add New" inline in the subject picker — add when users report needing `mn config` too often just to start a new project
- [ ] Richer list output formatting (column alignment, color) — add when plain output feels insufficient in daily use

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] `mn edit` — open last N notes or specific note in `$EDITOR`; defer because mutating GitHub content via API is complex and v1 establishes the write path
- [ ] Offline queue — defer because it adds a local state layer and complicates the "JSONL in GitHub is the store" model
- [ ] Tag detection (`#bugfix`, `#feature`) in note text — defer because there's no query surface for tags in v1; tags only pay off when filtering exists
- [ ] `mn list --date <range>` — date filtering; defer until users actually request it; JSONL + `jq` covers power users
- [ ] Shell completions (bash/zsh) — defer; useful polish but not needed to validate the concept

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| `mn d "note"` power path | HIGH | LOW | P1 |
| First-run setup detection | HIGH | LOW | P1 |
| GitHub write (append JSONL) | HIGH | MEDIUM | P1 |
| `mn config` interactive editor | HIGH | LOW-MEDIUM | P1 |
| `mn list` recent notes | HIGH | MEDIUM | P1 |
| Interactive subject picker (`mn`) | MEDIUM | LOW | P1 |
| Clear error messages | HIGH | LOW | P1 |
| `--help` / `--version` | MEDIUM | LOW | P1 |
| "Add New" inline in picker | MEDIUM | LOW | P2 |
| `mn list --subject` filter | MEDIUM | LOW | P2 |
| Richer list formatting | LOW | LOW | P2 |
| Shell completions | LOW | MEDIUM | P3 |
| `mn edit` | LOW | HIGH | P3 |
| Offline queue | LOW | HIGH | P3 |
| Tag detection / filtering | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

Comparable tools analyzed from training knowledge (confidence: MEDIUM — patterns are well-established, specific feature sets may have changed).

| Feature | jrnl | dnote | nb | mn (this project) |
|---------|------|-------|----|--------------------|
| Single-command entry | Yes (`jrnl "note"`) | Yes (`dnote add`) | Yes | Yes (`mn d "note"`) |
| Project/subject scoping | Via tags/journals | Via books | Via notebooks | Via subjects (folders) |
| Interactive mode | No | No | Yes | Yes (questionary picker) |
| GitHub backing store | No (local/Dropbox) | Optional sync | No (local) | Yes (native, via gh) |
| List / recall | Yes | Yes | Yes | Yes (`mn list`) |
| Search / filter | Yes (powerful) | Yes | Yes | v2+ only |
| Editing notes | Yes | Yes | Yes | Deliberately deferred |
| Tagging | Yes (inline `@tag`) | Yes | Yes | Deliberately deferred |
| Offline support | Yes (local-first) | Yes | Yes | No (GitHub-required) |
| Encryption | Yes (optional) | No | Yes | No (public repo risk) |
| Configuration | Yes | Yes | Yes | Yes (`mn config`) |
| Distribution | pip/brew | brew/bin | brew/pip | brew + pip |

**Key differentiator for mn:** The combination of zero-prompt power path + GitHub as the native backing store (not a sync target) + `gh` CLI delegation is unique in this space. No comparable tool is built on this model.

**Key gap vs competitors:** No offline support and no editing. These are deliberate trade-offs, not oversights. Document them clearly in the README so users self-select appropriately.

---

## Sources

- Training knowledge of comparable tools: `jrnl` (v4.x), `dnote` (CLI), `nb`, `taskwarrior`, `git-standup` — confidence MEDIUM (patterns verified through broad exposure; specific current feature sets not live-verified due to tool restrictions)
- Project context: `/Users/hunterfinch/Desktop/projects/make-note/.planning/PROJECT.md` and `/Users/hunterfinch/Desktop/projects/notes/project-ideas/make-note/PLAN.md` — confidence HIGH
- Developer CLI UX conventions (XDG config paths, `--help`/`--version` contract, error message patterns) — confidence HIGH (industry standard)

---

*Feature research for: Developer note-logging CLI (mn / MakeNote)*
*Researched: 2026-03-08*
