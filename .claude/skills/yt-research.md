# yt-research — YouTube Metadata Research Skill

Search YouTube for video metadata (title, author, views, duration, URL) using yt-dlp.

## Trigger
Invoked when the user says "use the yt-research skill" or types `/yt-research`.

## IMPORTANT: Topic Required
If the user has NOT specified a research topic, stop immediately and ask:
> "What topic would you like to research on YouTube?"
Do not proceed until a topic is given.

## Steps

### 1. Confirm parameters
- **Topic**: required (ask if missing)
- **Count**: default 25; use whatever the user specifies

### 2. Run the search
```bash
python3 /home/user/PLM/scripts/yt_research.py "<TOPIC>" --count <COUNT> --format json
```

### 3. Parse and display results
Present results as a numbered markdown table with columns:
`#` | `Title` | `Author` | `Duration` | `Views` | `URL`

### 4. Report summary
After the table, output:
- Total videos found
- Combined list of all YouTube URLs (one per line) — this is the handoff payload for the notebooklm skill

### 5. Offer to continue
Ask: "Would you like me to send these videos to NotebookLM for analysis?"

## Error handling
- If yt-dlp returns no results, tell the user and suggest refining the query
- If fewer results than requested are returned, note that and continue with what was found
