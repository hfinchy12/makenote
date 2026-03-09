# Milestones

## v1.0 MVP (Shipped: 2026-03-09)

**Phases completed:** 3 phases, 7 plans
**Timeline:** 2026-03-08 → 2026-03-09 (2 days)
**Stats:** 408 LOC source Python, 711 LOC tests, 48 commits

**Key accomplishments:**
- Installable `mn` CLI via `pip install -e .` with `--version`, `--help`, and first-run detection
- Config layer with interactive questionary menu persisted to `~/.config/makenote/config.json`
- GitHub I/O module (`github.py`) — SHA-safe JSONL append via `gh api`, full `GhError` hierarchy
- Complete note commands: `mn` (arrow-key picker), `mn d` (default subject), `mn d "text"` (zero-interaction), `mn list` (columnar output)
- GH-04 complete: all three note commands catch `GhNotInstalledError`/`GhNotAuthError` with locked messages + exit 1
- Homebrew formula with `virtualenv_install_with_resources` + `depends_on "gh"`; `RELEASING.md` release checklist

---

