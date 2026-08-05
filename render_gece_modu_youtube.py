#!/usr/bin/env python3
"""Render Arven Solé — Gece Modu YouTube lyric video (TikTok-style layout)."""

from __future__ import annotations

import math
import subprocess
import sys
import wave
from array import array
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FPS = 24
COVER = Path("/opt/cursor/artifacts/assets/arven-sole-cover.png")
AUDIO = Path("/home/ubuntu/.cursor/projects/workspace/uploads/gece_modu_b627.mp3")
WAV = Path("/tmp/gece_yt_render.wav")
FONT_DIR = Path("/usr/share/fonts/truetype/macos")
OUT_FULL = Path("/workspace/ArvenSole_GeceModu_YOUTUBE_FULL.mp4")
OUT_SHORT = Path("/workspace/ArvenSole_GeceModu_YOUTUBE_SHORT.mp4")
ART = Path("/opt/cursor/artifacts")

CREAM = (232, 220, 200)
CREAM2 = (210, 195, 170)
WHITE = (255, 255, 255)
MUTED = (180, 175, 165)
DIM = (140, 135, 128)
PROGRESS_BG = (55, 50, 45)
PILL_BG = (18, 16, 14, 210)

# Timed lyric lines (start, end, text). Hand-tuned to Gece Modu structure.
LYRICS: list[tuple[float, float, str]] = [
    (1.8, 4.0, "Gece modu açık"),
    (4.0, 6.2, "Sessizlik ağır"),
    (6.2, 8.6, "Kalp ritmi bozuk"),
    (8.6, 11.2, "Sokaklar şahit"),
    (11.2, 13.8, "Aynada bir yüz var"),
    (13.8, 16.2, "Tanımaz oldum"),
    (16.2, 18.8, "Kimse sormadı"),
    (18.8, 21.5, "İyi misin diye"),
    (22.0, 25.0, "Dost sandıklarım bir bildi"),
    (25.0, 27.5, "Telefon suskun"),
    (27.5, 30.0, "Mesajlar soğuk"),
    (30.0, 34.0, "İçeride fırtına"),
    (34.0, 37.5, "Dışarıda durgun"),
    (37.5, 41.5, "Ben bu gecede kaybolmadım"),
    (41.5, 45.5, "Sadece kimseye bakmadım"),
    (46.0, 48.5, "Gece modu"),
    (48.5, 51.0, "Kalbim kapalı"),
    (51.0, 53.8, "Işıklar yanıyor"),
    (53.8, 56.5, "İçim karanlık"),
    (56.5, 59.5, "Bu sokak benim"),
    (59.5, 63.0, "Bu dert benim malım"),
    (63.0, 66.0, "Ben ayaktayım"),
    (66.0, 70.0, "Yeter bu kadar olsun"),
    (71.0, 74.0, "Eski defterler"),
    (74.0, 77.0, "Yalnız sayfalar"),
    (77.0, 80.5, "Ucuz sözler"),
    (80.5, 84.0, "Bir bakış yeter"),
    (84.5, 88.0, "Gece modu"),
    (88.0, 91.0, "Kalbim kapalı"),
    (91.0, 94.0, "Işıklar yanıyor"),
    (94.0, 97.0, "İçim karanlık"),
    (97.5, 101.0, "Bu sokak benim"),
    (101.0, 105.0, "Bu dert benim malım"),
    (105.0, 108.5, "Ben ayaktayım"),
    (108.5, 113.0, "Yeter bu kadar olsun"),
    (114.0, 117.5, "Gece modu açık"),
    (117.5, 121.0, "Sessizlik ağır"),
    (121.0, 124.5, "Gece modu"),
    (124.5, 128.0, "Kalbim kapalı"),
    (128.0, 132.0, "Işıklar yanıyor"),
    (132.0, 136.0, "Bu sokak benim"),
    (136.0, 140.5, "Bu dert benim malım"),
]


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def ensure_wav() -> tuple[np.ndarray, int]:
    if not WAV.exists() or WAV.stat().st_size < 1_000_000:
        subprocess.check_call(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(AUDIO),
                "-ac",
                "1",
                "-ar",
                "44100",
                str(WAV),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    with wave.open(str(WAV)) as w:
        rate = w.getframerate()
        raw = w.readframes(w.getnframes())
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    return samples, rate


def cover_base() -> Image.Image:
    img = Image.open(COVER).convert("RGB")
    # Cover is square — scale to fill vertical 9:16, center crop
    scale = max(W / img.width, H / img.height)
    nw, nh = int(img.width * scale), int(img.height * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - W) // 2
    top = (nh - H) // 2
    img = img.crop((left, top, left + W, top + H))
    # Soft vignette toward bottom so credits read cleanly
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i, a in enumerate(range(0, 200, 8)):
        y0 = H - 520 + i * 8
        d.rectangle((0, y0, W, H), fill=(0, 0, 0, min(230, a + 40)))
    # Solid credit plate
    d.rectangle((0, H - 340, W, H), fill=(0, 0, 0, 255))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    return img


def draw_static_credits(base: Image.Image) -> Image.Image:
    img = base.copy()
    d = ImageDraw.Draw(img)
    f_artist = font("Inter-Bold.ttf", 54)
    f_title = font("Inter-Medium.ttf", 34)
    f_credit = font("Inter-Regular.ttf", 26)

    artist = "Arven Solé"
    title = "Gece Modu"
    credit = "Söz-Müzik: Arven Solé"

    y_artist = H - 250
    y_title = H - 185
    y_credit = H - 135

    def center_text(text, fnt, y, fill):
        bbox = d.textbbox((0, 0), text, font=fnt)
        tw = bbox[2] - bbox[0]
        d.text(((W - tw) // 2, y), text, font=fnt, fill=fill)

    center_text(artist, f_artist, y_artist, WHITE)
    center_text(title, f_title, y_title, CREAM)
    center_text(credit, f_credit, y_credit, MUTED)
    return img


def band_energies(chunk: np.ndarray, n_bars: int = 26) -> np.ndarray:
    if len(chunk) < 64:
        return np.zeros(n_bars, dtype=np.float32)
    # Windowed FFT
    window = np.hanning(len(chunk))
    spec = np.abs(np.fft.rfft(chunk * window))
    # Log-frequency grouping
    freqs = np.linspace(0, 1, len(spec))
    edges = np.logspace(math.log10(0.02), math.log10(1.0), n_bars + 1)
    vals = np.zeros(n_bars, dtype=np.float32)
    for i in range(n_bars):
        mask = (freqs >= edges[i]) & (freqs < edges[i + 1])
        if mask.any():
            vals[i] = float(spec[mask].mean())
    # Normalize with soft compression
    peak = vals.max()
    if peak > 1e-6:
        vals = vals / peak
    vals = np.power(vals, 0.65)
    return vals


def draw_eq(draw: ImageDraw.ImageDraw, vals: np.ndarray, progress: float) -> None:
    n = len(vals)
    pill_w, pill_h = 820, 118
    pill_x = (W - pill_w) // 2
    pill_y = H - 420
    # Rounded pill background
    draw.rounded_rectangle(
        (pill_x, pill_y, pill_x + pill_w, pill_y + pill_h),
        radius=28,
        fill=(22, 20, 18),
        outline=(40, 36, 32),
        width=2,
    )
    margin_x = 36
    margin_y = 22
    usable_w = pill_w - 2 * margin_x
    usable_h = pill_h - 2 * margin_y
    gap = 8
    bar_w = max(8, int((usable_w - gap * (n - 1)) / n))
    total = n * bar_w + (n - 1) * gap
    start_x = pill_x + margin_x + (usable_w - total) // 2
    base_y = pill_y + pill_h - margin_y
    for i, v in enumerate(vals):
        h = int(14 + v * (usable_h - 14))
        x0 = start_x + i * (bar_w + gap)
        y0 = base_y - h
        color = CREAM if i % 3 != 2 else CREAM2
        draw.rounded_rectangle((x0, y0, x0 + bar_w, base_y), radius=bar_w // 2, fill=color)

    # Progress bar
    bar_y = H - 58
    bar_x0, bar_x1 = 120, W - 120
    draw.line((bar_x0, bar_y, bar_x1, bar_y), fill=PROGRESS_BG, width=4)
    px = bar_x0 + int((bar_x1 - bar_x0) * progress)
    draw.line((bar_x0, bar_y, px, bar_y), fill=CREAM, width=4)
    draw.ellipse((px - 7, bar_y - 7, px + 7, bar_y + 7), fill=CREAM)


def lyric_at(t: float) -> tuple[str | None, str | None]:
    """Return (current, next) lyric lines for time t."""
    cur = None
    nxt = None
    for i, (s, e, text) in enumerate(LYRICS):
        if s <= t < e:
            cur = text
            if i + 1 < len(LYRICS):
                nxt = LYRICS[i + 1][2]
            break
        if t < s:
            nxt = text
            break
    return cur, nxt


def draw_lyrics(img: Image.Image, t: float) -> None:
    cur, nxt = lyric_at(t)
    if not cur:
        return
    d = ImageDraw.Draw(img)
    f_cur = font("Inter-Bold.ttf", 48)
    f_next = font("Inter-Regular.ttf", 28)

    # Soft dark plate behind lyrics for readability
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    cy = H - 560
    pd.rounded_rectangle((80, cy - 70, W - 80, cy + 90), radius=24, fill=(0, 0, 0, 140))
    img.alpha_composite(plate)

    d = ImageDraw.Draw(img)
    bbox = d.textbbox((0, 0), cur, font=f_cur)
    tw = bbox[2] - bbox[0]
    d.text(((W - tw) // 2, cy - 30), cur, font=f_cur, fill=WHITE)

    if nxt:
        bbox2 = d.textbbox((0, 0), nxt, font=f_next)
        tw2 = bbox2[2] - bbox2[0]
        d.text(((W - tw2) // 2, cy + 40), nxt, font=f_next, fill=DIM)


def render(out_path: Path, t0: float = 0.0, t1: float | None = None) -> None:
    samples, rate = ensure_wav()
    duration = len(samples) / rate
    if t1 is None:
        t1 = duration
    t1 = min(t1, duration)
    n_frames = int(round((t1 - t0) * FPS))
    print(f"Rendering {out_path.name}: {t0:.1f}-{t1:.1f}s → {n_frames} frames @ {FPS}fps", flush=True)

    base = draw_static_credits(cover_base())
    hop = rate // FPS
    n_bars = 26
    # Smooth EQ with simple EMA
    smooth = np.zeros(n_bars, dtype=np.float32)

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{W}x{H}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-ss",
        str(t0),
        "-t",
        str(t1 - t0),
        "-i",
        str(AUDIO),
        "-map",
        "0:v",
        "-map",
        "1:a",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(out_path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None

    start_sample = int(t0 * rate)
    try:
        for fi in range(n_frames):
            t = t0 + fi / FPS
            si = start_sample + fi * hop
            chunk = samples[si : si + hop * 2]
            vals = band_energies(chunk, n_bars)
            smooth = 0.55 * smooth + 0.45 * vals

            frame = base.copy().convert("RGBA")
            draw_lyrics(frame, t)
            d = ImageDraw.Draw(frame)
            progress = (t - t0) / max(0.001, t1 - t0)
            # Absolute progress for full track feel on shorts too
            abs_progress = t / duration
            draw_eq(d, smooth, abs_progress)

            rgb = frame.convert("RGB")
            proc.stdin.write(rgb.tobytes())
            if fi % 48 == 0:
                print(f"  frame {fi}/{n_frames} ({100 * fi / n_frames:.0f}%)", flush=True)
    finally:
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        code = proc.wait()
    if code != 0:
        print(err[-3000:], file=sys.stderr)
        raise RuntimeError(f"ffmpeg failed ({code})")
    print(f"Done: {out_path} ({out_path.stat().st_size / 1e6:.1f} MB)", flush=True)


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    # Full official lyric video
    render(OUT_FULL, 0.0, None)
    # Shorts: intro → first chorus (~55s) — discovery cut
    render(OUT_SHORT, 0.0, 55.0)
    for p in (OUT_FULL, OUT_SHORT):
        dest = ART / p.name
        dest.write_bytes(p.read_bytes())
        print(f"Copied → {dest}")


if __name__ == "__main__":
    main()
