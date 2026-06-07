#!/usr/bin/env python3
"""
Transcribe video/audio files to Markdown using OpenAI Whisper,
then add the transcripts as sources to a NotebookLM notebook.

Usage:
    python scripts/video_to_notebooklm.py <notebook_id> <directory> [--model small] [--recursive]
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
import argparse

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".wmv", ".flv", ".mpg", ".mpeg"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".wma", ".flac"}
ALL_MEDIA = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS


FFMPEG_CANDIDATES = [
    "ffmpeg",
    r"C:\ffmpeg\bin\ffmpeg.exe",
    r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
]


def find_ffmpeg() -> str:
    import shutil
    for candidate in FFMPEG_CANDIDATES:
        if shutil.which(candidate) or Path(candidate).exists():
            return candidate
    return None


def ensure_whisper():
    try:
        import whisper
        return whisper
    except ImportError:
        print("openai-whisper not found — installing...", file=sys.stderr)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai-whisper"])
        import whisper
        return whisper


def transcribe(filepath: Path, model) -> str:
    print(f"  Transcribing: {filepath.name} ...", file=sys.stderr)
    result = model.transcribe(str(filepath), fp16=False)
    return result["text"].strip()


def to_markdown(filepath: Path, transcript: str, output_dir: Path) -> Path:
    md_path = output_dir / f"{filepath.stem}.md"
    md_path.write_text(
        f"# {filepath.stem}\n\n"
        f"**Source file:** `{filepath.name}`\n\n"
        f"## Transcript\n\n{transcript}\n",
        encoding="utf-8",
    )
    return md_path


async def upload_to_notebooklm(notebook_id: str, md_files: list) -> dict:
    from notebooklm import NotebookLMClient

    results = []
    async with NotebookLMClient.from_storage() as client:
        for f in md_files:
            try:
                await client.sources.add_file(notebook_id, str(f))
                results.append({"file": f.name, "status": "added"})
                print(f"  Uploaded: {f.name}", file=sys.stderr)
            except Exception as e:
                results.append({"file": f.name, "status": "error", "error": str(e)})
                print(f"  Failed:   {f.name} — {e}", file=sys.stderr)

    successful = sum(1 for r in results if r["status"] == "added")
    return {
        "notebook_id": notebook_id,
        "sources": results,
        "total": len(md_files),
        "successful": successful,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe video files → Markdown → NotebookLM"
    )
    parser.add_argument("notebook_id", help="NotebookLM notebook ID")
    parser.add_argument("directory", help="Folder containing video/audio files")
    parser.add_argument(
        "--model",
        default="small",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size. small = good balance of speed/accuracy (default)",
    )
    parser.add_argument("--recursive", "-r", action="store_true", help="Include subfolders")
    parser.add_argument("--transcripts-dir", help="Where to save .md files (default: <directory>/transcripts/)")
    parser.add_argument("--transcribe-only", action="store_true", help="Transcribe only, do not upload to NotebookLM")
    args = parser.parse_args()

    base = Path(args.directory)
    if not base.exists():
        print(json.dumps({"error": f"Directory not found: {args.directory}"}))
        sys.exit(1)

    pattern = "**/*" if args.recursive else "*"
    media_files = sorted(
        f for f in base.glob(pattern)
        if f.is_file() and f.suffix.lower() in ALL_MEDIA
    )

    if not media_files:
        exts = ", ".join(sorted(ALL_MEDIA))
        print(json.dumps({"error": f"No video/audio files found in: {args.directory}", "looked_for": exts}))
        sys.exit(1)

    print(f"Found {len(media_files)} media file(s):", file=sys.stderr)
    for f in media_files:
        print(f"  {f.name}", file=sys.stderr)

    output_dir = Path(args.transcripts_dir) if args.transcripts_dir else base / "transcripts"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nTranscripts will be saved to: {output_dir}", file=sys.stderr)

    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        print(
            "\nERROR: ffmpeg not found. Install it and ensure it is on your PATH.\n"
            "  Option 1: winget install --id Gyan.FFmpeg -e\n"
            "  Option 2: Download from https://www.gyan.dev/ffmpeg/builds/\n"
            "            Extract to C:\\ffmpeg and re-run.\n"
            "  If already extracted to C:\\ffmpeg, the script will find it automatically.",
            file=sys.stderr,
        )
        sys.exit(1)

    if ffmpeg_path != "ffmpeg":
        import os
        ffmpeg_dir = str(Path(ffmpeg_path).parent)
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
        print(f"Using ffmpeg from: {ffmpeg_path}", file=sys.stderr)

    print(f"\nLoading Whisper model '{args.model}' (downloads on first use)...", file=sys.stderr)
    whisper = ensure_whisper()
    model = whisper.load_model(args.model)

    md_files = []
    for vf in media_files:
        print(f"\n[{media_files.index(vf)+1}/{len(media_files)}] {vf.name}", file=sys.stderr)
        try:
            transcript = transcribe(vf, model)
            md_path = to_markdown(vf, transcript, output_dir)
            md_files.append(md_path)
            print(f"  Saved: {md_path}", file=sys.stderr)
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)

    if not md_files:
        print(json.dumps({"error": "No files were transcribed successfully"}))
        sys.exit(1)

    print(f"\n{len(md_files)} transcript(s) ready.", file=sys.stderr)

    if args.transcribe_only:
        print(json.dumps({"transcripts": [str(f) for f in md_files], "total": len(md_files)}, indent=2))
        return

    print(f"Uploading to NotebookLM notebook {args.notebook_id}...\n", file=sys.stderr)
    result = asyncio.run(upload_to_notebooklm(args.notebook_id, md_files))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
