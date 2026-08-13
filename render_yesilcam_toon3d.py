#!/usr/bin/env python3
"""Yeşilçam clip → stylized 3D/toon animation look. Original audio untouched."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

SRC = Path("/tmp/yesilcam/source_h264.mp4")
OUT = Path("/workspace/ArvenSole_Yesilcam_TOON3D_DEMO.mp4")
ART = Path("/opt/cursor/artifacts") / OUT.name

# Classic lobby dialogue stretch
T0 = 8.0
DUR = 42.0
FPS = 24
W, H = 1024, 576


def toon_3d(frame_bgr: np.ndarray) -> np.ndarray:
    """Cel-shaded / plastic-3D stylization (CPU)."""
    img = cv2.resize(frame_bgr, (W, H), interpolation=cv2.INTER_AREA)
    # Mild denoise before stylize
    soft = cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)
    soft = cv2.bilateralFilter(soft, d=9, sigmaColor=60, sigmaSpace=60)

    # Color flatten (posterize-ish) for CG look
    hsv = cv2.cvtColor(soft, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = cv2.split(hsv)
    s = np.clip(s * 1.25, 0, 255)
    # Quantize value into bands → soft shading steps
    bands = 6.0
    v = np.floor(v / (256.0 / bands)) * (256.0 / bands) + (128.0 / bands)
    v = np.clip(v, 0, 255)
    hsv2 = cv2.merge([h, s, v]).astype(np.uint8)
    flat = cv2.cvtColor(hsv2, cv2.COLOR_HSV2BGR)

    # Extra smooth for plastic skin/surfaces
    flat = cv2.bilateralFilter(flat, d=7, sigmaColor=50, sigmaSpace=50)

    # Ink outlines
    gray = cv2.cvtColor(soft, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 7)
    edges = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 2
    )
    edges = cv2.medianBlur(edges, 3)
    # Thicken lines slightly
    kernel = np.ones((2, 2), np.uint8)
    edges = cv2.erode(edges, kernel, iterations=1)

    # Soft rim / fake AO vignette for 3D depth
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2.0, H / 2.0
    dist = np.sqrt(((xx - cx) / (W * 0.65)) ** 2 + ((yy - cy) / (H * 0.65)) ** 2)
    vignette = np.clip(1.15 - 0.45 * dist, 0.55, 1.0)[:, :, None]

    out = flat.astype(np.float32) * vignette
    # Warm Yeşilçam grade
    out[:, :, 0] *= 0.92  # B
    out[:, :, 1] *= 1.02  # G
    out[:, :, 2] *= 1.08  # R
    out = np.clip(out, 0, 255).astype(np.uint8)

    # Multiply edges
    out = cv2.bitwise_and(out, out, mask=edges)

    # Specular-ish highlight pass (cheap)
    lab = cv2.cvtColor(out, cv2.COLOR_BGR2LAB).astype(np.float32)
    l, a, b = cv2.split(lab)
    glow = cv2.GaussianBlur(l, (0, 0), 3)
    l = np.clip(l + 0.12 * np.maximum(glow - 140, 0), 0, 255)
    out = cv2.cvtColor(cv2.merge([l, a, b]).astype(np.uint8), cv2.COLOR_LAB2BGR)

    # Subtle film-clean: reduce noise, keep edge
    out = cv2.detailEnhance(out, sigma_s=8, sigma_r=0.15)
    return out


def render() -> None:
    if not SRC.exists():
        raise SystemExit(f"missing {SRC}")

    cap = cv2.VideoCapture(str(SRC))
    if not cap.isOpened():
        raise SystemExit("cannot open source")
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    start_frame = int(T0 * src_fps)
    n_frames = int(DUR * FPS)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    ff_log = Path("/tmp/yesilcam_toon_ffmpeg.log")
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-ss", str(T0), "-t", str(DUR), "-i", str(SRC),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        str(OUT),
    ]
    ff_err = open(ff_log, "w")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=ff_err)
    assert proc.stdin is not None

    # Sample source frames at target FPS
    src_pos = T0
    step = 1.0 / FPS
    print(f"Rendering toon3d {T0}-{T0+DUR:.0f}s ({n_frames}f)", flush=True)
    try:
        for fi in range(n_frames):
            cap.set(cv2.CAP_PROP_POS_MSEC, src_pos * 1000.0)
            ok, frame = cap.read()
            if not ok or frame is None:
                frame = np.zeros((H, W, 3), dtype=np.uint8)
            stylized = toon_3d(frame)
            proc.stdin.write(stylized.tobytes())
            src_pos += step
            if fi % 48 == 0:
                print(f"  {fi}/{n_frames} ({100*fi/n_frames:.0f}%)", flush=True)
    finally:
        proc.stdin.close()
        code = proc.wait()
        ff_err.close()
        cap.release()

    if code != 0:
        print(ff_log.read_text(errors="replace")[-2000:], file=sys.stderr)
        raise RuntimeError(f"ffmpeg failed {code}")

    ART.parent.mkdir(parents=True, exist_ok=True)
    ART.write_bytes(OUT.read_bytes())
    print(f"Done {OUT} ({OUT.stat().st_size/1e6:.1f}MB)", flush=True)


if __name__ == "__main__":
    render()
