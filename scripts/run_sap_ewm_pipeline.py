#!/usr/bin/env python3
"""
One-shot pipeline: SAP eWM YouTube research → NotebookLM analysis + infographic.
Run this locally after: notebooklm login
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from notebooklm import NotebookLMClient

NOTEBOOK_NAME = "SAP eWM Research — YouTube Analysis"

YOUTUBE_URLS = [
    "https://www.youtube.com/watch?v=uFlhF3ocCOM",  # SAP EWM Handling Unit Config & Demo
    "https://www.youtube.com/watch?v=ls0ysYd2S5o",  # SAP EWM S/4HANA Implementation
    "https://www.youtube.com/watch?v=yLMGHmb9VKc",  # Post Processing Framework (PPF)
    "https://www.youtube.com/watch?v=LDcKRhRKAB8",  # Connecting SAP S/4HANA & EWM
    "https://www.youtube.com/watch?v=1EY154s6tes",  # How to Connect S/4HANA–EWM
    "https://www.youtube.com/watch?v=GkrPrKPOjKI",  # SAP EWM Tutorial Overview
    "https://www.youtube.com/watch?v=F-mMJ3WC1rU",  # AI-Driven Slotting in SAP EWM
    "https://www.youtube.com/watch?v=HAHeoDbYYSQ",  # SAP EWM Demo S/4HANA in Action
    "https://www.youtube.com/watch?v=0P3YJVf03Yg",  # SAP EWM Live Demo
    "https://www.youtube.com/watch?v=c9nUiW-jluY",  # Goods Receipt Reversal After Putaway
    "https://www.youtube.com/watch?v=M7U67eq9whY",  # SAP MM EWM Integration GR Process
    "https://www.youtube.com/watch?v=4LMNosZ5cTk",  # SAP S/4HANA EWM Demo Session 2025
    "https://www.youtube.com/watch?v=1wKhWqZM4e8",  # SAP EWM RF Devices Overview
    "https://www.youtube.com/watch?v=RNQOgRR7TO0",  # Fastest Way to Learn SAP WM
    "https://www.youtube.com/watch?v=_9J0zuEPCd4",  # EWM Inbound Reception via RFUI
    "https://www.youtube.com/watch?v=0wvQJ7eif8g",  # Labor Management in WM Monitor
    "https://www.youtube.com/watch?v=fYZ2ni8C-AA",  # Configuration Settings for RF
    "https://www.youtube.com/watch?v=rOONCPZ8H9I",  # SAP S4HANA EWM Virtue Solutions
    "https://www.youtube.com/watch?v=-vSjZYxdl8A",  # SAP EWM Explained
    "https://www.youtube.com/watch?v=9ByU2ro9So0",  # SAP EWM Masterclass Multisoft
    "https://www.youtube.com/watch?v=2F1gOwFaA6A",  # What is SAP EWM — Introduction
    "https://www.youtube.com/watch?v=EK95dBZc9Qo",  # EWM with S/4HANA Embedded Overview
    "https://www.youtube.com/watch?v=CiqbCve5-fc",  # EWM Putaway Slotting Rearrangement
    "https://www.youtube.com/watch?v=IyP-5LtAtRA",  # SAP EWM Slotting Condition Technique
    "https://www.youtube.com/watch?v=UfGBP6xkThc",  # EWM Inbound Delivery & Goods Receipt
]

ANALYSIS_QUESTION = (
    "Based on all the SAP eWM videos in this notebook, what are the top findings? "
    "Please cover: (1) the most important eWM concepts and modules featured, "
    "(2) key trends such as AI, S/4HANA integration, and RF/mobility, "
    "(3) the most discussed pain points and best practices, "
    "and (4) what practitioners and trainers emphasize most. "
    "Be specific and comprehensive."
)


def log(msg: str):
    print(f"\n{'='*60}\n{msg}\n{'='*60}")


async def main():
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    async with await NotebookLMClient.from_storage() as client:

        # Step 1: Create notebook
        log("STEP 1/5 — Creating notebook")
        nb = await client.notebooks.create(NOTEBOOK_NAME)
        notebook_id = nb.id
        print(f"Notebook created: {notebook_id}")
        print(f"Name: {NOTEBOOK_NAME}")

        # Save notebook ID for reference
        (output_dir / "notebook_id.txt").write_text(notebook_id)

        # Step 2: Add sources in two batches to avoid timeouts
        log("STEP 2/5 — Adding 25 YouTube sources (batch 1 of 2)")
        batch1 = YOUTUBE_URLS[:13]
        batch2 = YOUTUBE_URLS[13:]

        tasks1 = [client.sources.add_url(notebook_id, url, wait=False) for url in batch1]
        results1 = await asyncio.gather(*tasks1, return_exceptions=True)
        ok1 = sum(1 for r in results1 if not isinstance(r, Exception))
        print(f"Batch 1: {ok1}/{len(batch1)} sources added")

        log("STEP 2/5 — Adding sources (batch 2 of 2)")
        tasks2 = [client.sources.add_url(notebook_id, url, wait=False) for url in batch2]
        results2 = await asyncio.gather(*tasks2, return_exceptions=True)
        ok2 = sum(1 for r in results2 if not isinstance(r, Exception))
        print(f"Batch 2: {ok2}/{len(batch2)} sources added")
        print(f"Total sources added: {ok1 + ok2}/{len(YOUTUBE_URLS)}")

        # Brief wait for sources to process before asking
        log("STEP 2/5 — Waiting 30s for sources to process...")
        await asyncio.sleep(30)

        # Step 3: Ask for analysis
        log("STEP 3/5 — Requesting analysis")
        print("Question:", ANALYSIS_QUESTION[:80] + "...")
        result = await client.chat.ask(notebook_id, ANALYSIS_QUESTION)
        analysis = result.answer
        print("\nANALYSIS:\n")
        print(analysis)
        (output_dir / "analysis.txt").write_text(analysis)
        print(f"\nSaved to: {output_dir / 'analysis.txt'}")

        # Step 4: Generate infographic
        log("STEP 4/5 — Generating infographic (portrait orientation)")
        status = await client.artifacts.generate_infographic(notebook_id)
        print(f"Generation started (task: {status.task_id}) — waiting for completion...")
        await client.artifacts.wait_for_completion(notebook_id, status.task_id)
        print("Infographic generation complete.")

        # Step 5: Download infographic
        log("STEP 5/5 — Downloading infographic")
        infographic_path = str(output_dir / "sap_ewm_infographic.png")
        await client.artifacts.download_infographic(notebook_id, infographic_path)
        print(f"Saved to: {infographic_path}")

    # Final summary
    log("PIPELINE COMPLETE")
    print(f"Notebook ID : {notebook_id}")
    print(f"Analysis    : {output_dir / 'analysis.txt'}")
    print(f"Infographic : {output_dir / 'sap_ewm_infographic.png'}")
    print(f"\nOpen your notebook at: https://notebooklm.google.com")


if __name__ == "__main__":
    asyncio.run(main())
