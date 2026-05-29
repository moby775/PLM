# notebooklm — NotebookLM Pipeline Skill

Create a NotebookLM notebook, load YouTube sources, get AI analysis, and generate deliverables.

## Trigger
Invoked when the user says "use the notebooklm skill", "send to NotebookLM", or types `/notebooklm`.

## Auth check
Before running any command, verify authentication is available. If a command fails with an auth error, stop and tell the user:
> "NotebookLM authentication is missing or expired. Please open a separate terminal and run:
> `notebooklm login`
> Then run `notebooklm auth check --test` to confirm, and retry."

## Pipeline steps

### Step 1 — Create notebook
```bash
python3 /home/user/PLM/scripts/notebooklm_pipeline.py create "<NOTEBOOK_NAME>"
```
Parse the returned JSON to get `id` — store this as `NOTEBOOK_ID` for all subsequent steps.

### Step 2 — Add YouTube sources
Add URLs in a single call (they are processed concurrently):
```bash
python3 /home/user/PLM/scripts/notebooklm_pipeline.py add-sources <NOTEBOOK_ID> <URL1> <URL2> ... <URLN>
```
Report how many sources were added successfully vs failed.

> **Tip for large batches (>15 URLs):** Split into two calls of ~12-13 URLs each to avoid timeouts.

### Step 3 — Request analysis (if asked)
```bash
python3 /home/user/PLM/scripts/notebooklm_pipeline.py ask <NOTEBOOK_ID> "<QUESTION>"
```
Display the answer in full.

Example analysis questions:
- "What are the top findings and key themes across all these videos?"
- "Summarize the most important insights in bullet points."
- "What are the most discussed topics, trends, and expert opinions?"

### Step 4 — Generate deliverable (if requested)

#### Infographic
```bash
python3 /home/user/PLM/scripts/notebooklm_pipeline.py generate <NOTEBOOK_ID> infographic --orientation portrait
```
> Note: NotebookLM's infographic generator does not currently support custom visual styles (e.g. "chalkboard"). The content will reflect the analysis; for styling, open the downloaded image in an image editor or use an image generation tool.

#### Slide deck
```bash
python3 /home/user/PLM/scripts/notebooklm_pipeline.py generate <NOTEBOOK_ID> slide-deck
```

#### Flashcards
```bash
python3 /home/user/PLM/scripts/notebooklm_pipeline.py generate <NOTEBOOK_ID> flashcards
```

#### Quiz
```bash
python3 /home/user/PLM/scripts/notebooklm_pipeline.py generate <NOTEBOOK_ID> quiz
```

#### Audio podcast
```bash
python3 /home/user/PLM/scripts/notebooklm_pipeline.py generate <NOTEBOOK_ID> audio --instructions "<STYLE_INSTRUCTIONS>"
```

#### Mind map
```bash
python3 /home/user/PLM/scripts/notebooklm_pipeline.py generate <NOTEBOOK_ID> mind-map
```

### Step 5 — Download artifact

#### Infographic → PNG
```bash
python3 /home/user/PLM/scripts/notebooklm_pipeline.py download <NOTEBOOK_ID> infographic ./output/infographic.png
```

#### Slide deck → PDF
```bash
python3 /home/user/PLM/scripts/notebooklm_pipeline.py download <NOTEBOOK_ID> slide-deck ./output/slides.pdf
```

#### Flashcards → JSON
```bash
python3 /home/user/PLM/scripts/notebooklm_pipeline.py download <NOTEBOOK_ID> flashcards ./output/flashcards.json --format json
```

#### Quiz → Markdown
```bash
python3 /home/user/PLM/scripts/notebooklm_pipeline.py download <NOTEBOOK_ID> quiz ./output/quiz.md --format markdown
```

#### Audio → MP3
```bash
python3 /home/user/PLM/scripts/notebooklm_pipeline.py download <NOTEBOOK_ID> audio ./output/podcast.mp3
```

After downloading, report the full path to the saved file.

## Full end-to-end example
When the user asks for the complete pipeline (research → analysis → infographic):
1. Run Steps 1–2 with the YouTube URLs from yt-research
2. Run Step 3 asking for top findings
3. Run Step 4 (infographic generation)
4. Run Step 5 to download the infographic
5. Report: notebook ID, analysis summary, and path to the downloaded file

## Output directory
Always save downloads to `./output/` (create if it doesn't exist with `mkdir -p ./output`).
