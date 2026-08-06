#!/usr/bin/env python3
"""Render Arven Solé — Hâlâ Sensin: Shorts (9:16) + YouTube 16:9 with stylish center lyrics."""

from __future__ import annotations

import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AUDIO = Path("/workspace/arven_sole_tracks/Hala_Sensin.mp3")
COVER = Path("/opt/cursor/artifacts/assets/arven-sole-cover.png")
WAV = Path("/tmp/hala_render.wav")
FONT_DIR = Path("/usr/share/fonts/truetype/macos")
ART = Path("/opt/cursor/artifacts")
OUT_SHORT = Path("/workspace/ArvenSole_HalaSensin_SHORT.mp4")
OUT_16X9 = Path("/workspace/ArvenSole_HalaSensin_YOUTUBE_16x9.mp4")

FPS = 24
CREAM = (232, 220, 200)
CREAM2 = (210, 195, 170)
WHITE = (255, 255, 255)
MUTED = (168, 162, 152)
PROGRESS_BG = (55, 50, 45)

TITLE = "Hâlâ Sensin"
ARTIST = "Arven Solé"
CREDIT = "Söz-Müzik: Arven Solé"

# Whisper-synced, cleaned
LYRICS: list[tuple[float, float, str]] = [
    (0.20, 4.40, "Gece yine çöküyor üstüme"),
    (4.40, 8.94, "Adın aklımda dönüp duruyor"),
    (8.94, 12.80, "Kapattım kapıyı, sustum sandım"),
    (12.80, 17.72, "Ama kalbim seni çağırıyor"),
    (18.72, 23.20, "Nefesim kesiliyor bir anda"),
    (23.20, 28.50, "Kanım hızlanıyor adınla"),
    # Chorus 1
    (29.72, 32.20, "Hâlâ sensin"),
    (32.20, 34.60, "Hâlâ sensin"),
    (34.60, 38.50, "İçimde durmayan yangın"),
    (39.50, 42.00, "Hâlâ sensin"),
    (42.00, 44.40, "Hâlâ sensin"),
    (44.40, 46.84, "Kalp çarpıyor, kaçsam da"),
    (47.50, 50.80, "Bağırıyorum, duyulsun diye"),
    (50.80, 56.12, "Bu gece yine sensin"),
    (56.12, 59.00, "Hâlâ sensin"),
    (59.00, 61.20, "Hâlâ sensin"),
    (61.20, 63.58, "Bitti demem, bitmedin"),
    # Verse 2
    (81.20, 85.20, "Camlara vuruyor yağmur yine"),
    (85.20, 89.32, "Her damla senin izini taşıyor"),
    (90.32, 94.20, "Unuttum dedim, güldüm sandım"),
    (94.20, 98.24, "Dönünce gözüm yine sende kalıyor"),
    (99.32, 103.80, "Nefesim kesiliyor bir anda"),
    (103.80, 108.42, "Kanım hızlanıyor adınla"),
    # Chorus 2
    (109.90, 112.40, "Hâlâ sensin"),
    (112.40, 114.80, "Hâlâ sensin"),
    (114.80, 118.20, "İçimde durmayan yangın"),
    (118.20, 120.80, "Hâlâ sensin"),
    (120.80, 123.40, "Hâlâ sensin"),
    (123.40, 126.84, "Kalp çarpıyor, kaçsam da"),
    (126.84, 130.40, "Bağırıyorum, duyulsun diye"),
    (130.40, 135.92, "Bu gece yine sensin"),
    (135.92, 138.80, "Hâlâ sensin"),
    (138.80, 141.00, "Hâlâ sensin"),
    (141.00, 143.86, "Bitti demem, bitmedin"),
    # Bridge
    (144.84, 148.40, "Bir saniye sus, bir saniye patla"),
    (148.40, 152.12, "İçimde fırtına kopuyor"),
    (153.12, 156.80, "Ne kadar uzak olsan da"),
    (156.80, 160.48, "Yine sana çarpıyorum"),
    # Final
    (162.94, 166.00, "Hâlâ sensin"),
    (166.00, 169.20, "Hâlâ sensin"),
    (169.20, 173.50, "Hâlâ sensin"),
    (173.50, 178.00, "Hâlâ sensin"),
    (178.00, 181.12, "Kalp çarpıyor"),
    (183.12, 186.50, "Kaçsam da"),
]

SHORT_T0 = 29.5
SHORT_T1 = 63.8


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


def band_energies(chunk: np.ndarray, n_bars: int = 28) -> np.ndarray:
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
    vals = np.power(np.clip(vals, 0, 1), 0.6)
    return 0.12 + 0.88 * vals


def lyric_at(t: float) -> tuple[str | None, float, float]:
    for s, e, text in LYRICS:
        if s <= t < e:
            return text, s, e
    return None, 0.0, 0.0


def draw_stylish_lyrics(
    img: Image.Image, t: float, w: int, h: int, center_y: int, size: int = 52
) -> None:
    """Center lyrics: fade + soft plate + cream rule + subtle scale-in."""
    cur, s, e = lyric_at(t)
    if not cur:
        return

    fade = 0.22
    alpha = 1.0
    if t - s < fade:
        alpha = (t - s) / fade
    elif e - t < fade:
        alpha = (e - t) / fade
    alpha = max(0.0, min(1.0, alpha))

    # Subtle scale-in at cue start
    scale = 0.92 + 0.08 * min(1.0, (t - s) / 0.28)
    fsize = max(28, int(size * scale))
    f_cur = font("Inter-Bold.ttf", fsize)

    # Measure on temp
    tmp = Image.new("RGBA", (w, 200), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    bbox = td.textbbox((0, 0), cur, font=f_cur)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    plate_w = min(w - 80, tw + 80)
    plate_h = th + 56
    plate = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    px0 = (w - plate_w) // 2
    py0 = center_y - plate_h // 2
    # Soft dark glass plate
    pd.rounded_rectangle(
        (px0, py0, px0 + plate_w, py0 + plate_h),
        radius=22,
        fill=(0, 0, 0, int(150 * alpha)),
    )
    # Thin cream border
    pd.rounded_rectangle(
        (px0, py0, px0 + plate_w, py0 + plate_h),
        radius=22,
        outline=(*CREAM, int(90 * alpha)),
        width=1,
    )
    img.alpha_composite(plate)

    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    x = (w - tw) // 2
    y = center_y - th // 2 - 4
    # Soft shadow
    ld.text((x + 2, y + 3), cur, font=f_cur, fill=(0, 0, 0, int(200 * alpha)))
    ld.text((x, y), cur, font=f_cur, fill=(255, 255, 255, int(255 * alpha)))

    # Cream underline with progress fill
    ly = y + th + 12
    pad = 10
    prog = (t - s) / max(0.05, e - s)
    ld.line((x - pad, ly, x + tw + pad, ly), fill=(80, 75, 68, int(110 * alpha)), width=2)
    fill_w = int((tw + 2 * pad) * prog)
    ld.line(
        (x - pad, ly, x - pad + fill_w, ly),
        fill=(*CREAM, int(240 * alpha)),
        width=2,
    )
    # Tiny end dots
    ld.ellipse(
        (x - pad - 3, ly - 3, x - pad + 3, ly + 3),
        fill=(*CREAM, int(180 * alpha)),
    )
    img.alpha_composite(layer)


def draw_eq(
    draw: ImageDraw.ImageDraw,
    vals: np.ndarray,
    progress: float,
    w: int,
    pill_w: int,
    pill_h: int,
    eq_y: int,
    progress_y: int,
) -> None:
    n = len(vals)
    pill_x = (w - pill_w) // 2
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
    bar_x0, bar_x1 = int(w * 0.12), int(w * 0.88)
    draw.line((bar_x0, progress_y, bar_x1, progress_y), fill=PROGRESS_BG, width=3)
    px = bar_x0 + int((bar_x1 - bar_x0) * progress)
    draw.line((bar_x0, progress_y, px, progress_y), fill=CREAM, width=3)
    draw.ellipse((px - 6, progress_y - 6, px + 6, progress_y + 6), fill=CREAM)


def base_vertical() -> Image.Image:
    W, H = 1080, 1920
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


def base_landscape() -> Image.Image:
    W, H = 1920, 1080
    src = Image.open(COVER).convert("RGB")
    bg = src.resize((W, H), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(28))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (0, 0, 0)), 0.55)
    side = 820
    cover = src.resize((side, side), Image.Resampling.LANCZOS)
    cx, cy = 120, (H - side) // 2 - 20
    canvas = bg.convert("RGBA")
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (cx + 10, cy + 14, cx + side + 10, cy + side + 14), radius=8, fill=(0, 0, 0, 160)
    )
    canvas = Image.alpha_composite(canvas, shadow)
    canvas.paste(cover, (cx, cy))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(20):
        a = int(10 + i * 11)
        y0 = 720 + i * 8
        d.rectangle((0, y0, W, H), fill=(0, 0, 0, min(245, a)))
    d.rectangle((0, 900, W, H), fill=(0, 0, 0, 255))
    out = Image.alpha_composite(canvas, overlay).convert("RGB")
    d2 = ImageDraw.Draw(out)
    rx = 1020
    d2.text((rx, 300), ARTIST, font=font("Inter-Bold.ttf", 44), fill=WHITE)
    d2.text((rx, 360), TITLE, font=font("Inter-SemiBold.ttf", 28), fill=CREAM)
    d2.text((rx, 405), CREDIT, font=font("Inter-Regular.ttf", 20), fill=MUTED)
    d2.line((rx, 280, rx + 160, 280), fill=CREAM, width=3)
    line = f"{ARTIST}  ·  {TITLE}  ·  {CREDIT}"
    f = font("Inter-Medium.ttf", 22)
    bbox = d2.textbbox((0, 0), line, font=f)
    tw = bbox[2] - bbox[0]
    d2.text(((W - tw) // 2, 970), line, font=f, fill=MUTED)
    return out


def render(
    out_path: Path,
    w: int,
    h: int,
    base: Image.Image,
    t0: float,
    t1: float | None,
    lyric_y: int,
    eq_y: int,
    pill_w: int,
    pill_h: int,
    progress_y: int,
    lyric_size: int,
) -> None:
    samples, rate = ensure_wav()
    duration = len(samples) / rate
    if t1 is None:
        t1 = duration
    t1 = min(t1, duration)
    n_frames = int(round((t1 - t0) * FPS))
    print(f"Rendering {out_path.name}: {t0:.1f}-{t1:.1f}s → {n_frames}f {w}x{h}", flush=True)

    hop = rate // FPS
    n_bars = 28 if w > 1200 else 24
    smooth = np.zeros(n_bars, dtype=np.float32)
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-",
        "-ss", str(t0), "-t", str(t1 - t0), "-i", str(AUDIO),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        str(out_path),
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
            draw_stylish_lyrics(frame, t, w, h, lyric_y, lyric_size)
            d = ImageDraw.Draw(frame)
            if t0 > 0.5:
                progress = (t - t0) / max(0.001, t1 - t0)
            else:
                progress = t / duration
            draw_eq(d, smooth, progress, w, pill_w, pill_h, eq_y, progress_y)
            proc.stdin.write(frame.convert("RGB").tobytes())
            if fi % 48 == 0:
                print(f"  {fi}/{n_frames} ({100 * fi / n_frames:.0f}%)", flush=True)
    finally:
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        code = proc.wait()
    if code != 0:
        print(err[-2500:], file=sys.stderr)
        raise RuntimeError(f"ffmpeg failed {code}")
    dest = ART / out_path.name
    dest.write_bytes(out_path.read_bytes())
    print(f"Done {out_path} ({out_path.stat().st_size / 1e6:.1f}MB)", flush=True)


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    # Shorts — first chorus, lyrics more centered on face area
    render(
        OUT_SHORT,
        1080,
        1920,
        base_vertical(),
        SHORT_T0,
        SHORT_T1,
        lyric_y=980,  # more center
        eq_y=1280,
        pill_w=760,
        pill_h=100,
        progress_y=1740,
        lyric_size=50,
    )
    # Long 16:9 — lyrics mid-frame
    render(
        OUT_16X9,
        1920,
        1080,
        base_landscape(),
        0.0,
        None,
        lyric_y=540,  # true center-ish above bottom UI
        eq_y=860,
        pill_w=1100,
        pill_h=78,
        progress_y=1040,
        lyric_size=54,
    )
    print("All done.")


if __name__ == "__main__":
    main()
