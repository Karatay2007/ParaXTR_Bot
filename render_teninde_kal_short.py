#!/usr/bin/env python3
"""Arven Solé — Teninde Kal Shorts with real kinetic lyric effects."""

from __future__ import annotations

import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AUDIO = Path("/workspace/arven_sole_tracks/Teninde_Kal.mp3")
COVER = Path("/opt/cursor/artifacts/assets/arven-sole-cover.png")
WAV = Path("/tmp/teninde.wav")
FONT_DIR = Path("/usr/share/fonts/truetype/macos")
ART = Path("/opt/cursor/artifacts")
OUT_SHORT = Path("/workspace/ArvenSole_TenindeKal_SHORT.mp4")

W, H = 1080, 1920
FPS = 24
CREAM = (232, 220, 200)
CREAM2 = (210, 195, 170)
WHITE = (255, 255, 255)
MUTED = (168, 162, 152)
PROGRESS_BG = (55, 50, 45)

TITLE = "Teninde Kal"
ARTIST = "Arven Solé"
CREDIT = "Söz-Müzik: Arven Solé"

# Hottest chorus block (~2:00–2:35)
SHORT_T0 = 120.0
SHORT_T1 = 155.5

LYRICS: list[tuple[float, float, str]] = [
    (120.00, 123.00, "Seninle kal bu gece"),
    (123.00, 127.00, "Aklım sende kayboldu"),
    (127.00, 130.00, "Dudaklar yalan söylemesin"),
    (130.00, 134.00, "Kalbin burada olsun"),
    (134.00, 137.00, "Seninle kal bu gece"),
    (137.00, 142.00, "Şehir dışarıda uyusun"),
    (142.00, 145.00, "İkimiz bu odada"),
    (145.00, 149.00, "Sabahı unutalım"),
    (149.00, 155.50, "Seninle kal bu gece"),
]


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def ensure_wav() -> tuple[np.ndarray, int]:
    if not WAV.exists() or WAV.stat().st_size < 1_000_000:
        subprocess.check_call(
            ["ffmpeg", "-y", "-i", str(AUDIO), "-ac", "1", "-ar", "44100", str(WAV)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    with wave.open(str(WAV)) as w:
        rate = w.getframerate()
        samples = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(
            np.float32
        ) / 32768.0
    return samples, rate


def band_energies(chunk: np.ndarray, n_bars: int = 24) -> np.ndarray:
    if len(chunk) < 64:
        return np.zeros(n_bars, dtype=np.float32)
    window = np.hanning(len(chunk))
    spec = np.abs(np.fft.rfft(chunk * window))
    freqs = np.linspace(0, 1, len(spec))
    edges = np.logspace(math.log10(0.02), math.log10(1.0), n_bars + 1)
    vals = np.zeros(n_bars, dtype=np.float32)
    for i in range(n_bars):
        mask = (freqs >= edges[i]) & (freqs < edges[i + 1])
        if mask.any():
            vals[i] = float(spec[mask].mean())
    peak = vals.max()
    if peak > 1e-6:
        vals = vals / peak
    return 0.12 + 0.88 * np.power(np.clip(vals, 0, 1), 0.6)


def lyric_at(t: float) -> tuple[str | None, float, float]:
    for s, e, text in LYRICS:
        if s <= t < e:
            return text, s, e
    return None, 0.0, 0.0


def ease_out_back(x: float) -> float:
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def draw_kinetic_lyrics(img: Image.Image, t: float) -> None:
    """Visible kinetic lyrics: band, bloom, word karaoke, fat underline."""
    cur, s, e = lyric_at(t)
    if not cur:
        return

    dur = max(0.05, e - s)
    local = t - s
    if local < 0.4:
        p = min(1.0, local / 0.4)
        pop = 0.7 + 0.45 * math.sin(p * math.pi * 0.5) + 0.15 * math.sin(p * math.pi)
        alpha = min(1.0, p / 0.2)
    else:
        pop = 1.0
        alpha = 1.0
    if e - t < 0.28:
        alpha *= max(0.0, (e - t) / 0.28)

    fsize = max(40, int(64 * pop))
    fnt = font("Inter-Bold.ttf", fsize)

    probe = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    bbox = ImageDraw.Draw(probe).textbbox((0, 0), cur, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    y = 880 - th // 2

    # Dark atmospheric band + cream side rails
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    by0, by1 = y - 40, y + th + 50
    mid = (by0 + by1) / 2
    half = (by1 - by0) / 2 + 1e-6
    for yy in range(by0, by1):
        a = int(170 * alpha * (1 - abs((yy - mid) / half) * 0.35))
        bd.line((0, yy, W, yy), fill=(0, 0, 0, max(0, min(200, a))))
    bd.rectangle((0, by0 + 8, 8, by1 - 8), fill=(*CREAM, int(220 * alpha)))
    bd.rectangle((W - 8, by0 + 8, W, by1 - 8), fill=(*CREAM, int(220 * alpha)))
    img.alpha_composite(band)

    words = cur.split()
    space_w = ImageDraw.Draw(Image.new("RGBA", (8, 8))).textbbox((0, 0), " ", font=fnt)
    space_w = space_w[2] - space_w[0]
    word_widths = []
    for w in words:
        bb = ImageDraw.Draw(Image.new("RGBA", (8, 8))).textbbox((0, 0), w, font=fnt)
        word_widths.append(bb[2] - bb[0])
    total = sum(word_widths) + space_w * max(0, len(words) - 1)
    x = (W - total) // 2

    # Bloom under full line
    bloom = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(bloom).text((x, y), cur, font=fnt, fill=(*CREAM, int(150 * alpha)))
    img.alpha_composite(bloom.filter(ImageFilter.GaussianBlur(18)))

    # Thick outline per word
    stroke = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stroke)
    cx = x
    for i, w in enumerate(words):
        for ox in range(-5, 6):
            for oy in range(-5, 6):
                if ox * ox + oy * oy <= 25:
                    sd.text((cx + ox, y + oy), w, font=fnt, fill=(0, 0, 0, int(240 * alpha)))
        cx += word_widths[i] + space_w
    img.alpha_composite(stroke)

    # Word karaoke
    prog = min(1.0, max(0.0, local / dur))
    active_f = prog * max(1, len(words))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    cx = x
    for i, w in enumerate(words):
        word_prog = max(0.0, min(1.0, active_f - i))
        if word_prog <= 0:
            col = (170, 170, 170, int(130 * alpha))
            wy = y
        elif word_prog < 1:
            col = (*CREAM, int(255 * alpha))
            wy = y - int(10 * math.sin(word_prog * math.pi))
        else:
            col = (255, 255, 255, int(255 * alpha))
            wy = y
        ld.text((cx, wy), w, font=fnt, fill=col)
        cx += word_widths[i] + space_w
    img.alpha_composite(layer)

    # Fat underline + diamonds
    ly = y + th + 18
    pad = 16
    line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    full = total + 2 * pad
    x0 = x - pad
    ld.line((x0, ly, x0 + full, ly), fill=(60, 55, 50, int(120 * alpha)), width=5)
    ld.line((x0, ly, x0 + int(full * prog), ly), fill=(*CREAM, int(255 * alpha)), width=5)
    for dx in (x0, x0 + int(full * prog)):
        ld.polygon(
            [(dx, ly - 7), (dx + 7, ly), (dx, ly + 7), (dx - 7, ly)],
            fill=(*CREAM, int(255 * alpha)),
        )
    img.alpha_composite(line)



def draw_eq(draw: ImageDraw.ImageDraw, vals: np.ndarray, progress: float) -> None:
    n = len(vals)
    pill_w, pill_h = 760, 100
    pill_x = (W - pill_w) // 2
    eq_y = 1280
    draw.rounded_rectangle(
        (pill_x, eq_y, pill_x + pill_w, eq_y + pill_h),
        radius=22,
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
    base_y = eq_y + pill_h - margin_y
    for i, v in enumerate(vals):
        bh = int(10 + float(v) * (usable_h - 10))
        x0 = start_x + i * (bar_w + gap)
        color = CREAM if i % 3 != 2 else CREAM2
        draw.rounded_rectangle(
            (x0, base_y - bh, x0 + bar_w, base_y), radius=bar_w // 2, fill=color
        )
    progress_y = 1740
    bar_x0, bar_x1 = 130, W - 130
    draw.line((bar_x0, progress_y, bar_x1, progress_y), fill=PROGRESS_BG, width=3)
    px = bar_x0 + int((bar_x1 - bar_x0) * progress)
    draw.line((bar_x0, progress_y, px, progress_y), fill=CREAM, width=3)
    draw.ellipse((px - 6, progress_y - 6, px + 6, progress_y + 6), fill=CREAM)


def base_vertical() -> Image.Image:
    img = Image.open(COVER).convert("RGB")
    scale = max(W / img.width, H / img.height) * 1.08
    nw, nh = int(img.width * scale), int(img.height * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - W) // 2
    top = max(0, int((nh - H) * 0.15))
    if top + H > nh:
        top = nh - H
    img = img.crop((left, top, left + W, top + H))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    credit_top = 1480
    for i in range(18):
        a = int(12 + i * 10)
        y0 = credit_top - 90 + i * 5
        d.rectangle((0, y0, W, H), fill=(0, 0, 0, min(240, a)))
    d.rectangle((0, credit_top, W, H), fill=(0, 0, 0, 255))
    out = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    d2 = ImageDraw.Draw(out)

    def center(text, fnt, y, fill):
        bbox = d2.textbbox((0, 0), text, font=fnt)
        tw = bbox[2] - bbox[0]
        d2.text(((W - tw) // 2, y), text, font=fnt, fill=fill)

    center(ARTIST, font("Inter-Bold.ttf", 48), 1535, WHITE)
    center(TITLE, font("Inter-SemiBold.ttf", 30), 1595, CREAM)
    center(CREDIT, font("Inter-Regular.ttf", 22), 1645, MUTED)
    return out


def render_short() -> None:
    samples, rate = ensure_wav()
    duration = len(samples) / rate
    t0, t1 = SHORT_T0, min(SHORT_T1, duration)
    n_frames = int(round((t1 - t0) * FPS))
    print(f"Rendering SHORT {t0:.1f}-{t1:.1f}s ({n_frames}f)", flush=True)
    base = base_vertical()
    hop = rate // FPS
    n_bars = 24
    smooth = np.zeros(n_bars, dtype=np.float32)
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-ss", str(t0), "-t", str(t1 - t0), "-i", str(AUDIO),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        str(OUT_SHORT),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    start = int(t0 * rate)
    try:
        for fi in range(n_frames):
            t = t0 + fi / FPS
            chunk = samples[start + fi * hop : start + fi * hop + hop * 2]
            smooth = 0.55 * smooth + 0.45 * band_energies(chunk, n_bars)
            frame = base.copy().convert("RGBA")
            draw_kinetic_lyrics(frame, t)
            d = ImageDraw.Draw(frame)
            draw_eq(d, smooth, (t - t0) / max(0.001, t1 - t0))
            proc.stdin.write(frame.convert("RGB").tobytes())
            if fi % 48 == 0:
                print(f"  {fi}/{n_frames} ({100*fi/n_frames:.0f}%)", flush=True)
    finally:
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        code = proc.wait()
    if code != 0:
        print(err[-2500:], file=sys.stderr)
        raise RuntimeError(f"ffmpeg failed {code}")
    dest = ART / OUT_SHORT.name
    dest.write_bytes(OUT_SHORT.read_bytes())
    print(f"Done {OUT_SHORT} ({OUT_SHORT.stat().st_size/1e6:.1f}MB)", flush=True)


if __name__ == "__main__":
    ART.mkdir(parents=True, exist_ok=True)
    render_short()
