#!/usr/bin/env python3
"""NotebookLM pipeline operations via notebooklm-py Python API."""

import asyncio
import json
import sys
import argparse
from pathlib import Path
from notebooklm import NotebookLMClient

SUPPORTED_EXTENSIONS = {
    ".pdf", ".txt", ".md", ".docx",
    ".html", ".htm",
}


async def get_client():
    try:
        return await NotebookLMClient.from_storage()
    except Exception as e:
        print(
            json.dumps(
                {
                    "error": "Authentication failed. Run: notebooklm login",
                    "details": str(e),
                }
            )
        )
        sys.exit(1)


async def create_notebook(name: str) -> dict:
    async with await get_client() as client:
        nb = await client.notebooks.create(name)
        return {"id": nb.id, "name": name, "status": "created"}


async def add_youtube_sources(
    notebook_id: str, urls: list, wait: bool = False
) -> dict:
    results = []
    async with await get_client() as client:
        tasks = [
            client.sources.add_url(notebook_id, url, wait=wait) for url in urls
        ]
        raw = await asyncio.gather(*tasks, return_exceptions=True)
        for url, r in zip(urls, raw):
            if isinstance(r, Exception):
                results.append({"url": url, "status": "error", "error": str(r)})
            else:
                results.append({"url": url, "status": "added"})

    successful = sum(1 for r in results if r["status"] == "added")
    return {
        "notebook_id": notebook_id,
        "sources": results,
        "total": len(urls),
        "successful": successful,
    }


async def add_local_files(notebook_id: str, directory: str, recursive: bool = False) -> dict:
    base = Path(directory)
    if not base.exists():
        return {"error": f"Path not found: {directory}"}

    if base.is_file():
        files = [base]
    else:
        pattern = "**/*" if recursive else "*"
        files = [
            f for f in base.glob(pattern)
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

    if not files:
        return {
            "error": f"No supported files found in: {directory}",
            "supported_types": sorted(SUPPORTED_EXTENSIONS),
        }

    results = []
    async with NotebookLMClient.from_storage() as client:
        for f in files:
            try:
                await client.sources.add_file(notebook_id, str(f))
                results.append({"file": f.name, "status": "added"})
                print(f"  Added: {f.name}", file=sys.stderr)
            except Exception as e:
                results.append({"file": f.name, "status": "error", "error": str(e)})
                print(f"  Failed: {f.name} — {e}", file=sys.stderr)

    successful = sum(1 for r in results if r["status"] == "added")
    return {
        "notebook_id": notebook_id,
        "files": results,
        "total": len(files),
        "successful": successful,
    }


async def ask_question(notebook_id: str, question: str) -> dict:
    async with await get_client() as client:
        result = await client.chat.ask(notebook_id, question)
        return {"answer": result.answer}


async def generate_artifact(notebook_id: str, artifact_type: str, **kwargs) -> dict:
    generators = {
        "infographic": "generate_infographic",
        "slide-deck": "generate_slide_deck",
        "flashcards": "generate_flashcards",
        "quiz": "generate_quiz",
        "audio": "generate_audio",
        "video": "generate_video",
        "mind-map": "generate_mind_map",
        "data-table": "generate_data_table",
    }

    if artifact_type not in generators:
        return {
            "error": f"Unknown artifact type: {artifact_type}. Valid: {list(generators.keys())}"
        }

    async with await get_client() as client:
        gen_fn = getattr(client.artifacts, generators[artifact_type])
        # Filter kwargs to only those accepted by the method
        try:
            status = await gen_fn(notebook_id, **kwargs)
        except TypeError:
            status = await gen_fn(notebook_id)
        await client.artifacts.wait_for_completion(notebook_id, status.task_id)
        return {
            "notebook_id": notebook_id,
            "artifact_type": artifact_type,
            "status": "completed",
            "task_id": status.task_id,
        }


async def download_artifact(
    notebook_id: str, artifact_type: str, output_path: str, **kwargs
) -> dict:
    downloaders = {
        "infographic": "download_infographic",
        "slide-deck": "download_slide_deck",
        "flashcards": "download_flashcards",
        "quiz": "download_quiz",
        "audio": "download_audio",
        "video": "download_video",
        "mind-map": "download_mind_map",
        "data-table": "download_data_table",
    }

    if artifact_type not in downloaders:
        return {"error": f"Unknown artifact type: {artifact_type}"}

    async with await get_client() as client:
        dl_fn = getattr(client.artifacts, downloaders[artifact_type])
        try:
            await dl_fn(notebook_id, output_path, **kwargs)
        except TypeError:
            await dl_fn(notebook_id, output_path)
        return {"downloaded": output_path, "artifact_type": artifact_type}


def main():
    parser = argparse.ArgumentParser(description="NotebookLM pipeline operations")
    sub = parser.add_subparsers(dest="command", required=True)

    # create
    p = sub.add_parser("create", help="Create a new notebook")
    p.add_argument("name", help="Notebook name")

    # add-sources
    p = sub.add_parser("add-sources", help="Add YouTube URLs as sources")
    p.add_argument("notebook_id", help="Notebook ID")
    p.add_argument("urls", nargs="+", help="YouTube URLs to add")
    p.add_argument("--wait", action="store_true", help="Wait for each source to process")

    # add-files
    p = sub.add_parser("add-files", help="Add local files from a directory as sources")
    p.add_argument("notebook_id", help="Notebook ID")
    p.add_argument("directory", help="Directory path (or single file path)")
    p.add_argument("--recursive", "-r", action="store_true", help="Include subdirectories")

    # ask
    p = sub.add_parser("ask", help="Ask NotebookLM a question")
    p.add_argument("notebook_id", help="Notebook ID")
    p.add_argument("question", help="Question to ask")

    # generate
    p = sub.add_parser("generate", help="Generate an artifact")
    p.add_argument("notebook_id", help="Notebook ID")
    p.add_argument(
        "artifact_type",
        choices=["infographic", "slide-deck", "flashcards", "quiz", "audio", "video", "mind-map", "data-table"],
        help="Type of artifact to generate",
    )
    p.add_argument("--instructions", help="Style or content instructions")
    p.add_argument(
        "--orientation",
        choices=["portrait", "landscape"],
        help="Orientation (infographic only)",
    )
    p.add_argument("--style", help="Visual style (video only)")

    # download
    p = sub.add_parser("download", help="Download a generated artifact")
    p.add_argument("notebook_id", help="Notebook ID")
    p.add_argument(
        "artifact_type",
        choices=["infographic", "slide-deck", "flashcards", "quiz", "audio", "video", "mind-map", "data-table"],
    )
    p.add_argument("output_path", help="Output file path")
    p.add_argument("--format", dest="output_format", help="Output format (json, markdown, pdf)")

    args = parser.parse_args()

    async def run():
        if args.command == "create":
            result = await create_notebook(args.name)

        elif args.command == "add-sources":
            result = await add_youtube_sources(
                args.notebook_id, args.urls, wait=args.wait
            )

        elif args.command == "add-files":
            result = await add_local_files(
                args.notebook_id, args.directory, recursive=args.recursive
            )

        elif args.command == "ask":
            result = await ask_question(args.notebook_id, args.question)

        elif args.command == "generate":
            kwargs = {}
            if getattr(args, "instructions", None):
                kwargs["instructions"] = args.instructions
            if getattr(args, "orientation", None):
                kwargs["orientation"] = args.orientation
            if getattr(args, "style", None):
                kwargs["style"] = args.style
            result = await generate_artifact(args.notebook_id, args.artifact_type, **kwargs)

        elif args.command == "download":
            kwargs = {}
            if getattr(args, "output_format", None):
                kwargs["output_format"] = args.output_format
            result = await download_artifact(
                args.notebook_id, args.artifact_type, args.output_path, **kwargs
            )

        print(json.dumps(result, indent=2))

    asyncio.run(run())


if __name__ == "__main__":
    main()
