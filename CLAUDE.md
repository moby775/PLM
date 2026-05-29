# PLM — YouTube → NotebookLM Research Pipeline

Automated pipeline: search YouTube for video metadata, feed results into NotebookLM,
and generate analysis deliverables (infographics, slide decks, flashcards, podcasts).

## Quick start

```bash
pip install -r requirements.txt
playwright install chromium
notebooklm login          # one-time Google auth (opens browser)
notebooklm auth check --test
```

## Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `yt-research` | `/yt-research` or "use the yt-research skill" | Search YouTube, return metadata + URLs |
| `notebooklm` | `/notebooklm` or "use the notebooklm skill" | Create notebook, add sources, analyse, generate deliverables |

### Example command
```
Use the yt-research skill to find the 25 latest trending videos on SAP eWM.
Once we have those videos, send them over to NotebookLM using the notebooklm skill.
Give me its analysis on the top findings, then have NotebookLM create an infographic.
```

**If no topic is specified, always ask the user before proceeding.**

## Scripts

| Script | Description |
|--------|-------------|
| `scripts/yt_research.py` | CLI: search YouTube, output JSON or text |
| `scripts/notebooklm_pipeline.py` | CLI: create notebook, add sources, ask, generate, download |

### yt_research.py usage
```bash
python3 scripts/yt_research.py "SAP eWM" --count 25 --format json
python3 scripts/yt_research.py "AI trends" --count 10 --format text
```

### notebooklm_pipeline.py usage
```bash
python3 scripts/notebooklm_pipeline.py create "My Research"
python3 scripts/notebooklm_pipeline.py add-sources <ID> <URL1> <URL2> ...
python3 scripts/notebooklm_pipeline.py ask <ID> "What are the key themes?"
python3 scripts/notebooklm_pipeline.py generate <ID> infographic --orientation portrait
python3 scripts/notebooklm_pipeline.py download <ID> infographic ./output/infographic.png
```

## Authentication

NotebookLM requires a Google account. Auth is handled by the `notebooklm-py` CLI:

```bash
notebooklm login                          # interactive Google sign-in
notebooklm auth check --test              # verify
notebooklm auth refresh --quiet           # refresh token (cron-friendly)
notebooklm profile list                   # show all Google accounts
notebooklm profile switch <name>          # switch account
```

Auth credentials are stored in `~/.config/notebooklm/` and persist across sessions.

## Dependencies

- `yt-dlp` — YouTube metadata scraping (no API key required)
- `notebooklm-py[browser]` — unofficial NotebookLM Python API + CLI by Teng Lin
- `playwright` + Chromium — browser automation for NotebookLM auth
