#!/usr/bin/env python3
"""
One-shot pipeline: HAESL engine overhaul research → NotebookLM analysis + infographic.
Run this locally after: notebooklm login
"""

import asyncio
import json
import sys
from pathlib import Path
from notebooklm import NotebookLMClient

NOTEBOOK_NAME = "HAESL — Engine Overhaul Research"

YOUTUBE_URLS = [
    # HAESL-specific
    "https://www.youtube.com/watch?v=6cSA9rajvII",   # HAESL - I Believe I Can Fly
    "https://www.youtube.com/watch?v=vCrGCvVnJOE",   # Galvatek Chemical Cleaning Line @ HAESL
    "https://www.youtube.com/watch?v=o2hFVKkBfrM",   # Galvatek WWTP 3D animation @ HAESL
    "https://www.youtube.com/watch?v=cYRB-HGA_nQ",   # Factory Simulation @ SAESL (sister co.)
    # Rolls-Royce Trent (HAESL's engine specialty)
    "https://www.youtube.com/watch?v=Zm9Lc9Z9euI",   # Rolls-Royce Engine Overhaul
    "https://www.youtube.com/watch?v=xKtE89c_aUM",   # Rolls-Royce MRO Network
    "https://www.youtube.com/watch?v=K2R6NTgvEV4",   # How we assemble the Trent XWB
    "https://www.youtube.com/watch?v=KDX6GsFSS3g",   # 787 Comeback: Trent 1000 Issues Solved
    "https://www.youtube.com/watch?v=LfdTnw7iwRI",   # 30 Years of Trent Engines
    "https://www.youtube.com/watch?v=7T-WrY8RnJw",   # Rolls Royce Trent Production
    # CFM56 & engine overhaul processes
    "https://www.youtube.com/watch?v=aCUfQTvC3JI",   # All you want to know about CFM56
    "https://www.youtube.com/watch?v=FHUEcEnKh9M",   # CFM56-7 MRO - Air France / KLM
    "https://www.youtube.com/watch?v=zxhZk_rvfSs",   # AerFin CFM56 In-House MRO
    # General engine overhaul
    "https://www.youtube.com/watch?v=Fvg-9ceqiIA",   # Aircraft Engine Overhaul [How It's Done]
    "https://www.youtube.com/watch?v=rSN05n0t5mk",   # OVERHAULING Aircraft Engines - Airworx
    "https://www.youtube.com/watch?v=TMNI1NrNYc8",   # Tulsa Engine Overhaul Process
    "https://www.youtube.com/watch?v=AQKhAyhAj_g",   # Aircraft Engine Overhaul - IAI
    "https://www.youtube.com/watch?v=HkVMkY7GtUM",   # Aircraft Engine MRO - IAI
    "https://www.youtube.com/watch?v=ph18wpynQXI",   # Expert Engine MRO Solutions - IAI
    "https://www.youtube.com/watch?v=jNffugTeelY",   # Engine MRO at Air France Industries
    # Borescope & inspection technology
    "https://www.youtube.com/watch?v=vA7WqYiPoNA",   # Aerospace Engine Borescope Advancements
    "https://www.youtube.com/watch?v=lv_KdjePMxw",   # Aircraft Turbine Engine Borescope
    "https://www.youtube.com/watch?v=xDajhAzG16k",   # Jet Tech: Turbine Blade Inspection
    "https://www.youtube.com/watch?v=ucYdECY3ecY",   # Gas Turbine Engine Borescope Inspection
    # Aviation MRO overview
    "https://www.youtube.com/watch?v=-IiDLtp2uLE",   # What is MRO in Aviation? Full Breakdown
]

ANALYSIS_QUESTION = (
    "Based on all the videos in this notebook about HAESL and engine overhaul, "
    "what are the top findings? Please cover: "
    "(1) the key stages of an engine overhaul shop visit — from incoming inspection "
    "through teardown, cleaning, repair, reassembly, and test cell; "
    "(2) the specialist capabilities and technologies involved (borescope inspection, "
    "turbine blade repair, chemical cleaning, test equipment); "
    "(3) quality, safety, and regulatory themes (airworthiness, OEM authorisations); "
    "(4) trends in the MRO industry — digitalisation, predictive maintenance, AI, "
    "sustainability; and "
    "(5) what makes world-class engine overhaul facilities stand out. "
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
        (output_dir / "haesl_notebook_id.txt").write_text(notebook_id)

        # Step 2: Add sources in two batches
        log("STEP 2/5 — Adding 25 YouTube sources (batch 1 of 2)")
        batch1, batch2 = YOUTUBE_URLS[:13], YOUTUBE_URLS[13:]

        tasks1 = [client.sources.add_url(notebook_id, url, wait=False) for url in batch1]
        res1 = await asyncio.gather(*tasks1, return_exceptions=True)
        ok1 = sum(1 for r in res1 if not isinstance(r, Exception))
        print(f"Batch 1: {ok1}/{len(batch1)} sources added")

        log("STEP 2/5 — Adding sources (batch 2 of 2)")
        tasks2 = [client.sources.add_url(notebook_id, url, wait=False) for url in batch2]
        res2 = await asyncio.gather(*tasks2, return_exceptions=True)
        ok2 = sum(1 for r in res2 if not isinstance(r, Exception))
        print(f"Batch 2: {ok2}/{len(batch2)} sources added")
        print(f"Total: {ok1 + ok2}/{len(YOUTUBE_URLS)} sources added successfully")

        log("STEP 2/5 — Waiting 30s for sources to process...")
        await asyncio.sleep(30)

        # Step 3: Analysis
        log("STEP 3/5 — Requesting engine overhaul analysis")
        result = await client.chat.ask(notebook_id, ANALYSIS_QUESTION)
        analysis = result.answer
        print("\nANALYSIS:\n")
        print(analysis)
        analysis_path = output_dir / "haesl_analysis.txt"
        analysis_path.write_text(analysis)
        print(f"\nSaved to: {analysis_path}")

        # Step 4: Generate infographic
        log("STEP 4/5 — Generating infographic (portrait orientation)")
        status = await client.artifacts.generate_infographic(notebook_id)
        print(f"Generation started (task: {status.task_id}) — waiting...")
        await client.artifacts.wait_for_completion(notebook_id, status.task_id)
        print("Infographic generation complete.")

        # Step 5: Download
        log("STEP 5/5 — Downloading infographic")
        infographic_path = str(output_dir / "haesl_engine_overhaul_infographic.png")
        await client.artifacts.download_infographic(notebook_id, infographic_path)
        print(f"Saved to: {infographic_path}")

    log("PIPELINE COMPLETE")
    print(f"Notebook ID  : {notebook_id}")
    print(f"Analysis     : {output_dir / 'haesl_analysis.txt'}")
    print(f"Infographic  : {output_dir / 'haesl_engine_overhaul_infographic.png'}")
    print(f"Open notebook: https://notebooklm.google.com")


if __name__ == "__main__":
    asyncio.run(main())
