# makenote

Fast terminal note logging to GitHub. Log notes from your terminal and store them as JSONL files in a GitHub repo — no database, no server, just `gh` and Git.

## Why

Developers do a lot — shipped features, fixed bugs, unblocked teammates, learned something new — and most of it goes unrecorded. Come performance review time, or when updating your resume, that work is hard to reconstruct.

`makenote` is a lightweight habit for capturing those moments as they happen. A two-second note from the terminal is low enough friction to actually stick. Over time, your notes become a running log of your progress and impact, stored in a GitHub repo you already own and can query however you like.

## How it works

`mn` appends timestamped notes to `notes/<subject>/notes.jsonl` in a GitHub repo you configure. Notes are stored as newline-delimited JSON records and written directly via the GitHub Contents API (through the `gh` CLI).

## Requirements

- Python 3.9+
- [gh CLI](https://cli.github.com) — authenticated (`gh auth login`)
- A GitHub repo to store your notes in

## Installation

### Homebrew (recommended)

```bash
brew tap hfinchy12/tap
brew install makenote
```

### pip

```bash
pip install makenote
```

## Setup

On first run, `mn` launches an interactive config wizard:

```bash
mn
```

Or run it explicitly at any time:

```bash
mn config
```

You'll be prompted to set:
- **GitHub repo** — the `owner/repo` where notes will be stored
- **Subjects** — categories for your notes (e.g. `work`, `ideas`, `todo`)
- **Default subject** — used by `mn d` for fast logging

Config is saved to `~/.config/makenote/config.json`.

## Usage

### Interactive note (with subject picker)

```bash
mn
```

Prompts you to select a subject, then enter your note.

### Quick note to default subject

```bash
mn d "your note here"
```

Or without an argument to be prompted:

```bash
mn d
```

### List recent notes

```bash
mn list
```

Shows the 20 most recent notes across all subjects, sorted newest first.

To filter by a specific subject:

```bash
mn list --subject work
mn list -s ideas
```

### Edit config

```bash
mn config
```

### Version

```bash
mn --version
```

## Contributing

Pull requests are welcome. For significant changes, please open an issue first to discuss the approach.

1. Fork the repo
2. Create a feature branch (`git checkout -b my-feature`)
3. Make your changes
4. Run the test suite (`pytest tests/ -x -q`)
5. Open a pull request

## License

MIT
