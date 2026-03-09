# Phase 3: Distribution - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Create a Homebrew personal tap so users can install `mn` via `brew install hunterfinch/tap/makenote` on a clean macOS machine with no prior Python setup. Covers writing the formula, setting up the tap structure, and documenting the release process. The actual v0.1.0 tag and first publish happen separately after Phase 2 is verified working.

</domain>

<decisions>
## Implementation Decisions

### Tap repo structure
- Dedicated `homebrew-tap` GitHub repo: `hunterfinch/homebrew-tap`
- Install command for users: `brew tap hunterfinch/tap` → `brew install makenote`
- Formula lives at `Formula/makenote.rb` in the make-note repo (source of truth) — copied to tap repo on each release
- User will create the `homebrew-tap` GitHub repo manually; this phase only writes the formula file

### Python formula approach
- Use `virtualenv_install_with_resources` pattern — installs Homebrew Python and bundles `click` and `questionary` into an isolated venv; works on a completely clean machine
- Source URL: GitHub release tarball (`https://github.com/hunterfinch/make-note/archive/refs/tags/v0.1.0.tar.gz`)
- SHA256: placeholder in formula during development, with a clear comment explaining how to compute the real hash before publishing

### Release & publish workflow
- Manual checklist process: bump version in `pyproject.toml` → create git tag → compute SHA256 of tarball → update `Formula/makenote.rb` → push formula to `homebrew-tap` repo
- Include `RELEASING.md` in the make-note repo root with step-by-step release instructions
- This phase delivers the formula and tap setup only; tagging v0.1.0 and first publish are deferred until Phase 2 is fully working

### Formula test block
- `brew test makenote` verifies `mn --version` only — fast, no side effects, confirms binary is installed and wired correctly
- Plan includes a local verification task: `brew install --build-from-source ./Formula/makenote.rb` to confirm the formula works before pushing to the tap

### Claude's Discretion
- Exact `virtualenv_install_with_resources` resource declarations for click and questionary versions
- Formula `desc`, `homepage`, and metadata fields
- Structure of RELEASING.md (headings, detail level)

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard Homebrew Python formula patterns. Note from STATE.md: research current Homebrew Python formula guidelines before writing the formula, as `virtualenv_install_with_resources` patterns may have evolved.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pyproject.toml`: already has `name = "makenote"`, `version = "0.1.0"`, `requires-python = ">=3.9"`, `dependencies = ["click>=8.1", "questionary>=2.0"]` — formula resource versions should match these

### Established Patterns
- `src/` layout with `setuptools` build backend — formula installs from source tarball via standard Python packaging
- `[project.scripts] mn = "makenote.cli:main"` — the `mn` binary is wired via console_scripts; Homebrew venv approach preserves this

### Integration Points
- `Formula/makenote.rb` (new file in make-note repo) → copied to `homebrew-tap/Formula/makenote.rb` on release
- `RELEASING.md` (new file in repo root) → standalone doc, no code dependencies

</code_context>

<deferred>
## Deferred Ideas

- PyPI distribution (`pip install makenote`) — DIST-03, explicitly v2 requirement
- GitHub Actions to auto-update the formula on new tags — manual workflow is sufficient for v1

</deferred>

---

*Phase: 03-distribution*
*Context gathered: 2026-03-09*
