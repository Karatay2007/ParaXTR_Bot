#!/usr/bin/env python3
"""Render Arven Solé — Gece Modu 16:9 YouTube lyric video (not Shorts)."""

from __future__ import annotations

import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Import synced lyrics from vertical renderer
from render_gece_modu_youtube import LYRICS, ensure_wav, band_energies, font as _font

W, H = 1920, 1080
FPS = 24
COVER = Path("/opt/cursor/artifacts/assets/arven-sole-cover.png")
AUDIO = Path("/home/ubuntu/.cursor/projects/workspace/uploads/gece_modu_b627.mp3")
FONT_DIR = Path("/usr/share/fonts/truetype/macos")
OUT = Path("/workspace/ArvenSole_GeceModu_YOUTUBE_16x9.mp4")
ART = Path("/opt/cursor/artifacts")

CREAM = (232, 220, 200)
CREAM2 = (210, 195, 170)
WHITE = (255, 255, 255)
MUTED = (168, 162, 152)
PROGRESS_BG = (55, 50, 45)

# Landscape layout
LYRIC_Y = 780
EQ_Y = 860
CREDIT_Y0 = 970
PROGRESS_Y = 1040


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def cover_base() -> Image.Image:
    """Cinematic 16:9: blurred full-bleed bg + sharp cover panel on left."""
    src = Image.open(COVER).convert("RGB")

    # Blurred background fill
    bg = src.resize((W, H), Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(28))
    # Darken
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    bg = Image.blend(bg, dark, 0.55)

    # Sharp cover on left (square, height-fitted with margin)
    side = 820
    cover = src.resize((side, side), Image.Resampling.LANCZOS)
    cx, cy = 120, (H - side) // 2 - 20
    canvas = bg.convert("RGBA")
    # Soft shadow behind cover
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        (cx + 10, cy + 14, cx + side + 10, cy + side + 14),
        radius=8,
        fill=(0, 0, 0, 160),
    )
    canvas = Image.alpha_composite(canvas, shadow)
    canvas.paste(cover, (cx, cy))

    # Bottom plate for UI
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(20):
        a = int(10 + i * 11)
        y0 = 720 + i * 8
        d.rectangle((0, y0, W, H), fill=(0, 0, 0, min(245, a)))
    d.rectangle((0, 900, W, H), fill=(0, 0, 0, 255))
    out = Image.alpha_composite(canvas, overlay).convert("RGB")

    # Static credits (right of cover / bottom)
    d2 = ImageDraw.Draw(out)
    f_artist = font("Inter-Bold.ttf", 44)
    f_title = font("Inter-SemiBold.ttf", 28)
    f_credit = font("Inter-Regular.ttf", 20)

    # Right-side brand block (beside cover, above bottom UI)
    rx = 1020
    d2.text((rx, 320), "Arven Solé", font=f_artist, fill=WHITE)
    d2.text((rx, 380), "Gece Modu", font=f_title, fill=CREAM)
    d2.text((rx, 425), "Söz-Müzik: Arven Solé", font=f_credit, fill=MUTED)
    # Thin cream accent
    d2.line((rx, 300, rx + 160, 300), fill=CREAM, width=3)

    # Bottom centered credit strip
    def center(text, fnt, y, fill):
        bbox = d2.textbbox((0, 0), text, font=fnt)
        tw = bbox[2] - bbox[0]
        d2.text(((W - tw) // 2, y), text, font=fnt, fill=fill)

    center("Arven Solé  ·  Gece Modu  ·  Söz-Müzik: Arven Solé", font("Inter-Medium.ttf", 22), CREDIT_Y0, MUTED)
    return out


def draw_eq(draw: ImageDraw.ImageDraw, vals: np.ndarray, progress: float) -> None:
    n = len(vals)
    pill_w, pill_h = 1100, 78
    pill_x = (W - pill_w) // 2
    pill_y = EQ_Y
    draw.rounded_rectangle(
        (pill_x, pill_y, pill_x + pill_w, pill_y + pill_h),
        radius=20,
        fill=(18, 16, 14),
        outline=(38, 34, 30),
        width=2,
    )
    margin_x, margin_y = 28, 14
    usable_w = pill_w - 2 * margin_x
    usable_h = pill_h - 2 * margin_y
    gap = 6
    bar_w = max(8, int((usable_w - gap * (n - 1)) / n))
    total = n * bar_w + (n - 1) * gap
    start_x = pill_x + margin_x + (usable_w - total) // 2
    base_y = pill_y + pill_h - margin_y
    for i, v in enumerate(vals):
        h = int(10 + float(v) * (usable_h - 10))
        x0 = start_x + i * (bar_w + gap)
        y0 = base_y - h
        color = CREAM if i % 3 != 2 else CREAM2
        draw.rounded_rectangle(
            (x0, y0, x0 + bar_w, base_y), radius=bar_w // 2, fill=color
        )

    bar_x0, bar_x1 = 280, W - 280
    draw.line((bar_x0, PROGRESS_Y, bar_x1, PROGRESS_Y), fill=PROGRESS_BG, width=3)
    px = bar_x0 + int((bar_x1 - bar_x0) * progress)
    draw.line((bar_x0, PROGRESS_Y, px, PROGRESS_Y), fill=CREAM, width=3)
    draw.ellipse((px - 6, PROGRESS_Y - 6, px + 6, PROGRESS_Y + 6), fill=CREAM)


def lyric_at(t: float) -> tuple[str | None, float, float]:
    for s, e, text in LYRICS:
        if s <= t < e:
            return text, s, e
    return None, 0.0, 0.0


def draw_lyrics(img: Image.Image, t: float) -> None:
    cur, s, e = lyric_at(t)
    if not cur:
        return
    fade = 0.18
    alpha = 1.0
    if t - s < fade:
        alpha = (t - s) / fade
    elif e - t < fade:
        alpha = (e - t) / fade
    alpha = max(0.0, min(1.0, alpha))

    f_cur = font("Inter-Bold.ttf", 48)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(layer)
    bbox = td.textbbox((0, 0), cur, font=f_cur)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (W - tw) // 2
    y = LYRIC_Y
    td.text((x + 2, y + 3), cur, font=f_cur, fill=(0, 0, 0, int(180 * alpha)))
    td.text((x, y), cur, font=f_cur, fill=(255, 255, 255, int(255 * alpha)))
    ly = y + th + 10
    td.line((x - 6, ly, x + tw + 6, ly), fill=(*CREAM, int(200 * alpha)), width=2)
    img.alpha_composite(layer)


def render() -> None:
    samples, rate = ensure_wav()
    duration = len(samples) / rate
    n_frames = int(round(duration * FPS))
    print(f"Rendering 16:9 {OUT.name}: {duration:.1f}s → {n_frames} frames", flush=True)

    base = cover_base()
    hop = rate // FPS
    n_bars = 32
    smooth = np.zeros(n_bars, dtype=np.float32)

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(AUDIO),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        str(OUT),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for fi in range(n_frames):
            t = fi / FPS
            si = fi * hop
            chunk = samples[si : si + hop * 2]
            vals = band_energies(chunk, n_bars)
            smooth = 0.55 * smooth + 0.45 * vals
            frame = base.copy().convert("RGBA")
            draw_lyrics(frame, t)
            d = ImageDraw.Draw(frame)
            draw_eq(d, smooth, t / duration)
            proc.stdin.write(frame.convert("RGB").tobytes())
            if fi % 48 == 0:
                print(f"  frame {fi}/{n_frames} ({100 * fi / n_frames:.0f}%)", flush=True)
    finally:
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        code = proc.wait()
    if code != 0:
        print(err[-3000:], file=sys.stderr)
        raise RuntimeError(f"ffmpeg failed ({code})")
    dest = ART / OUT.name
    dest.write_bytes(OUT.read_bytes())
    print(f"Done: {OUT} ({OUT.stat().st_size / 1e6:.1f} MB) → {dest}", flush=True)


if __name__ == "__main__":
    render()
