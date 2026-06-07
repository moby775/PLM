#!/usr/bin/env python3
"""YouTube metadata scraper using yt-dlp."""

import json
import sys
import argparse
import yt_dlp


def format_duration(seconds):
    if not seconds:
        return "N/A"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_views(views):
    if views is None:
        return "N/A"
    if views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M"
    if views >= 1_000:
        return f"{views / 1_000:.1f}K"
    return str(views)


def search_youtube(query: str, max_results: int = 25, no_check_cert: bool = False) -> list:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "nocheckcertificate": no_check_cert,
    }

    videos = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)

        if not result or "entries" not in result:
            return videos

        for i, entry in enumerate(result["entries"], 1):
            if not entry:
                continue
            video_id = entry.get("id", "")
            url = (
                f"https://www.youtube.com/watch?v={video_id}"
                if video_id
                else entry.get("url", "")
            )
            videos.append(
                {
                    "rank": i,
                    "title": entry.get("title", "N/A"),
                    "url": url,
                    "author": entry.get("uploader") or entry.get("channel") or "N/A",
                    "duration_seconds": entry.get("duration"),
                    "duration": format_duration(entry.get("duration")),
                    "views": entry.get("view_count"),
                    "views_formatted": format_views(entry.get("view_count")),
                    "upload_date": entry.get("upload_date", "N/A"),
                    "description": (entry.get("description") or "")[:200],
                }
            )

    return videos


def main():
    parser = argparse.ArgumentParser(
        description="Search YouTube and return video metadata"
    )
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--count", "-n", type=int, default=25, help="Number of results (default: 25)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format",
    )
    parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="Skip SSL certificate verification (use behind corporate proxies)",
    )
    args = parser.parse_args()

    videos = search_youtube(args.query, args.count, no_check_cert=args.no_verify_ssl)

    if args.format == "json":
        print(json.dumps(videos, indent=2, ensure_ascii=False))
    else:
        print(f"\nYouTube Search Results for: '{args.query}'")
        print(f"Found {len(videos)} videos\n")
        print("-" * 80)
        for v in videos:
            print(f"{v['rank']:2}. {v['title']}")
            print(
                f"    Author: {v['author']} | Duration: {v['duration']} | Views: {v['views_formatted']}"
            )
            print(f"    URL: {v['url']}")
            print()


if __name__ == "__main__":
    main()
