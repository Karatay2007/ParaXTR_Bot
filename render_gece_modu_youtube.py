#!/usr/bin/env python3
"""Render Arven Solé — Gece Modu YouTube lyric video (TikTok-style layout)."""

from __future__ import annotations

import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

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
MUTED = (168, 162, 152)
PROGRESS_BG = (55, 50, 45)

# Layout — lyrics just above EQ (not on face); more cover; tight credits
LYRIC_Y = 1185
EQ_Y = 1280
CREDIT_TOP = 1480
ARTIST_Y = 1535
TITLE_Y = 1595
CREDIT_Y = 1645
PROGRESS_Y = 1740

# Whisper-synced cues (cleaned lyrics, sentence case). (start, end, line)
LYRICS: list[tuple[float, float, str]] = [
    (3.36, 6.20, "Gece Modu açık"),
    (6.20, 9.10, "Sessizlik ağır"),
    (9.10, 12.00, "Kalp ritmi bozuk"),
    (12.00, 15.02, "Sokaklar şahit"),
    (15.02, 16.70, "Aynada bir yüz var"),
    (16.70, 18.34, "Tanımaz oldum"),
    (18.34, 20.00, "Dertler cebimde"),
    (20.00, 21.56, "Gülüşüm borçtu"),
    (21.56, 23.20, "Kimse sormadı"),
    (23.20, 24.78, "İyi misin diye"),
    (24.78, 26.40, "Herkes uzaktan"),
    (26.40, 28.00, "Herkes bir hikaye"),
    (28.36, 29.40, "Adım adım yürüdüm"),
    (29.40, 30.40, "Yüzüm silindi"),
    (30.40, 32.56, "Dost sandıklarım gerildi"),
    (32.56, 34.00, "Telefon suskun"),
    (34.00, 35.60, "Mesajlar soğuk"),
    (35.60, 37.30, "İçeride fırtına"),
    (37.30, 39.06, "Dışarıda durgun"),
    (40.36, 43.46, "Ben bu gecede kaybolmadım"),
    (43.46, 45.82, "Sadece kimse bakmadı"),
    # Nakarat
    (46.36, 47.60, "Gece Modu"),
    (47.60, 48.80, "Kalbim kapalı"),
    (48.80, 50.50, "Işıklar yanıyor"),
    (50.50, 52.30, "İçim karanlık"),
    (52.30, 53.80, "Kimseyi anlatmam"),
    (53.80, 55.36, "Tutmam hesabı"),
    (55.61, 57.40, "Bu sokak benim"),
    (57.40, 59.47, "Bu dert benim malım"),
    (59.47, 61.00, "Gece Modu"),
    (61.00, 62.43, "Sesim tok"),
    (62.43, 64.20, "Rüyalar pahalı"),
    (64.20, 65.91, "Gerçek ucuz"),
    (65.91, 67.47, "Ne gelir ne gider"),
    (67.47, 69.00, "Hepsi bir oyun"),
    (69.00, 70.51, "Ben ayaktayım"),
    (70.51, 73.01, "Yeter bu kadar olsun"),
    # Bridge
    (73.61, 75.00, "Eski defterler"),
    (75.00, 76.05, "Yanmış sayfalar"),
    (76.05, 77.83, "Yeminler ucuz sözler"),
    (77.83, 79.20, "Bir bakış yeter"),
    (79.20, 80.41, "Her şey bozulur"),
    (80.41, 82.19, "Güven bir kere gider"),
    (83.19, 86.51, "Bir daha gelmez"),
    (86.51, 87.70, "Param yoktu"),
    (87.70, 88.77, "Gururum vardı"),
    (88.77, 90.59, "İkisi de yarım kaldı"),
    (90.59, 92.37, "İnanma sakın"),
    (92.37, 94.31, "O gülüş maske"),
    (94.31, 98.13, "Ben bu gecede kaybolmadım"),
    (98.13, 100.37, "Sadece kimse bakmadı"),
    # Nakarat 2
    (100.37, 101.80, "Gece Modu"),
    (101.80, 103.37, "Kalbim kapalı"),
    (103.37, 104.80, "Işıklar yanıyor"),
    (104.80, 106.19, "İçim karanlık"),
    (106.79, 108.50, "Kimseyi anlatmam"),
    (108.50, 110.37, "Tutmam hesabı"),
    (110.37, 112.00, "Bu sokak benim"),
    (112.00, 113.71, "Bu dert benim malım"),
    (114.37, 115.50, "Gece Modu"),
    (115.50, 116.85, "Sesim tok"),
    (117.37, 119.00, "Rüyalar pahalı"),
    (119.00, 120.35, "Gerçek ucuz"),
    (120.35, 121.79, "Ne gelir ne gider"),
    (122.37, 123.70, "Hepsi bir oyun"),
    (123.70, 124.91, "Ben ayaktayım"),
    (124.91, 127.35, "Yeter bu kadar olsun"),
    (127.35, 130.00, "Gece Modu"),
    (130.00, 132.53, "Kalbim kapalı"),
    (134.87, 137.50, "Ayaktayım"),
]

# Shorts = first nakarat (with short pre-hook)
SHORT_T0 = 40.0
SHORT_T1 = 73.2


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
    # Fill 9:16 — bias crop upward so face sits higher, room for UI below
    scale = max(W / img.width, H / img.height) * 1.08
    nw, nh = int(img.width * scale), int(img.height * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - W) // 2
    # Prefer upper portion of portrait
    top = max(0, int((nh - H) * 0.15))
    if top + H > nh:
        top = nh - H
    img = img.crop((left, top, left + W, top + H))

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    # Soft fade into compact credit plate — keep more of the cover visible
    for i in range(18):
        a = int(12 + i * 10)
        y0 = CREDIT_TOP - 90 + i * 5
        d.rectangle((0, y0, W, H), fill=(0, 0, 0, min(240, a)))
    d.rectangle((0, CREDIT_TOP, W, H), fill=(0, 0, 0, 255))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def draw_static_credits(base: Image.Image) -> Image.Image:
    img = base.copy()
    d = ImageDraw.Draw(img)
    f_artist = font("Inter-Bold.ttf", 48)
    f_title = font("Inter-SemiBold.ttf", 30)
    f_credit = font("Inter-Regular.ttf", 22)

    def center_text(text, fnt, y, fill):
        bbox = d.textbbox((0, 0), text, font=fnt)
        tw = bbox[2] - bbox[0]
        d.text(((W - tw) // 2, y), text, font=fnt, fill=fill)

    center_text("Arven Solé", f_artist, ARTIST_Y, WHITE)
    center_text("Gece Modu", f_title, TITLE_Y, CREAM)
    center_text("Söz-Müzik: Arven Solé", f_credit, CREDIT_Y, MUTED)
    return img


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
    vals = np.power(np.clip(vals, 0, 1), 0.6)
    # Keep a living floor so bars never look dead
    vals = 0.12 + 0.88 * vals
    return vals


def draw_eq(draw: ImageDraw.ImageDraw, vals: np.ndarray, progress: float) -> None:
    n = len(vals)
    pill_w, pill_h = 760, 100
    pill_x = (W - pill_w) // 2
    pill_y = EQ_Y
    draw.rounded_rectangle(
        (pill_x, pill_y, pill_x + pill_w, pill_y + pill_h),
        radius=24,
        fill=(18, 16, 14),
        outline=(38, 34, 30),
        width=2,
    )
    margin_x, margin_y = 32, 18
    usable_w = pill_w - 2 * margin_x
    usable_h = pill_h - 2 * margin_y
    gap = 7
    bar_w = max(8, int((usable_w - gap * (n - 1)) / n))
    total = n * bar_w + (n - 1) * gap
    start_x = pill_x + margin_x + (usable_w - total) // 2
    base_y = pill_y + pill_h - margin_y
    for i, v in enumerate(vals):
        h = int(12 + float(v) * (usable_h - 12))
        x0 = start_x + i * (bar_w + gap)
        y0 = base_y - h
        color = CREAM if i % 3 != 2 else CREAM2
        draw.rounded_rectangle(
            (x0, y0, x0 + bar_w, base_y), radius=bar_w // 2, fill=color
        )

    bar_x0, bar_x1 = 160, W - 160
    draw.line((bar_x0, PROGRESS_Y, bar_x1, PROGRESS_Y), fill=PROGRESS_BG, width=3)
    px = bar_x0 + int((bar_x1 - bar_x0) * progress)
    draw.line((bar_x0, PROGRESS_Y, px, PROGRESS_Y), fill=CREAM, width=3)
    draw.ellipse((px - 6, PROGRESS_Y - 6, px + 6, PROGRESS_Y + 6), fill=CREAM)


def lyric_at(t: float) -> tuple[str | None, float, float]:
    """Return (text, start, end) for active lyric, else (None,0,0)."""
    for s, e, text in LYRICS:
        if s <= t < e:
            return text, s, e
    return None, 0.0, 0.0


def draw_lyrics(img: Image.Image, t: float) -> None:
    """Modern karaoke: single line above EQ, soft shadow, full cream rule."""
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

    f_cur = font("Inter-Bold.ttf", 44)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    bbox = sd.textbbox((0, 0), cur, font=f_cur)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (W - tw) // 2
    y = LYRIC_Y
    sd.text((x + 2, y + 3), cur, font=f_cur, fill=(0, 0, 0, int(180 * alpha)))
    img.alpha_composite(shadow)

    text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(text_layer)
    td.text((x, y), cur, font=f_cur, fill=(255, 255, 255, int(255 * alpha)))

    # Full-width cream rule under the line (not progressive — cleaner)
    ly = y + th + 12
    pad = 8
    td.line(
        (x - pad, ly, x + tw + pad, ly),
        fill=(*CREAM, int(200 * alpha)),
        width=2,
    )
    img.alpha_composite(text_layer)


def render(out_path: Path, t0: float = 0.0, t1: float | None = None) -> None:
    samples, rate = ensure_wav()
    duration = len(samples) / rate
    if t1 is None:
        t1 = duration
    t1 = min(t1, duration)
    n_frames = int(round((t1 - t0) * FPS))
    print(
        f"Rendering {out_path.name}: {t0:.1f}-{t1:.1f}s → {n_frames} frames @ {FPS}fps",
        flush=True,
    )

    base = draw_static_credits(cover_base())
    hop = rate // FPS
    n_bars = 24
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
            # Shorts: progress within the cut; full: whole track
            if t0 > 0.5 or (t1 is not None and t1 < duration - 1):
                progress = (t - t0) / max(0.001, t1 - t0)
            else:
                progress = t / duration
            draw_eq(d, smooth, progress)

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
    print(f"Done: {out_path} ({out_path.stat().st_size / 1e6:.1f} MB)", flush=True)


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    render(OUT_FULL, 0.0, None)
    render(OUT_SHORT, SHORT_T0, SHORT_T1)
    for p in (OUT_FULL, OUT_SHORT):
        dest = ART / p.name
        dest.write_bytes(p.read_bytes())
        print(f"Copied → {dest}")


if __name__ == "__main__":
    main()
