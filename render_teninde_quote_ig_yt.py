#!/usr/bin/env python3
"""Teninde Kal — IG Reels + YT Shorts = same master as TikTok quote Short.

User request: keep Instagram / YouTube identical to the TikTok cut
(layout, bed, CTA, audio). No platform remix.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

MASTER = Path("/workspace/ArvenSole_TenindeKal_TIKTOK_QUOTE.mp4")
ART = Path("/opt/cursor/artifacts")
OUTS = {
    "ig": Path("/workspace/ArvenSole_TenindeKal_REELS_QUOTE.mp4"),
    "yt": Path("/workspace/ArvenSole_TenindeKal_SHORTS_QUOTE.mp4"),
}


def sync(platform: str) -> None:
    if not MASTER.exists():
        raise FileNotFoundError(f"TikTok master missing: {MASTER}")
    keys = ["ig", "yt"] if platform == "both" else [platform]
    ART.mkdir(parents=True, exist_ok=True)
    for k in keys:
        dest = OUTS[k]
        shutil.copy2(MASTER, dest)
        shutil.copy2(MASTER, ART / dest.name)
        print(f"{k}: copied {MASTER.name} → {dest.name} ({dest.stat().st_size / 1e6:.1f}MB)", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("platform", nargs="?", default="both", choices=["ig", "yt", "both"])
    args = ap.parse_args()
    sync(args.platform)


if __name__ == "__main__":
    main()
