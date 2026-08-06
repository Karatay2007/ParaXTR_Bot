#!/usr/bin/env python3
"""Arven Solé — Teninde Kal YouTube 16:9 (same cover template as Short, landscape).

STYLE (user 2026-08-06): Next lyric videos → make subtitle text MORE prominent
(heavier weight / thicker stroke / slightly larger). Current Outfit can read thin.
"""

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
FONT_OUTFIT = Path("/workspace/fonts/Outfit.ttf")
FONT_SERIF = Path("/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf")
ART = Path("/opt/cursor/artifacts")
OUT = Path("/workspace/ArvenSole_TenindeKal_YOUTUBE_16x9.mp4")

W, H = 1920, 1080
FPS = 24
CREAM = (232, 220, 200)
CREAM2 = (210, 195, 170)
WHITE = (255, 255, 255)
MUTED = (168, 162, 152)
PROGRESS_BG = (55, 50, 45)

TITLE = "TENİNDE KAL"
ARTIST = "ARVEN SOLÉ"
CREDIT = "SÖZ · MÜZİK   ARVEN SOLÉ"

# Landscape cover layout — lyrics + EQ tight; credits breathe below
LYRIC_Y = 620
EQ_Y = 720
EQ_H = 64
CREDIT_TOP = 860
PROGRESS_Y = 1025

WORD_LEAD = 0.05

# Full-track word clocks. Hook = Teninle (never Seninle). Chorus 2 tuned by hand.
LINES: list[list[tuple[float, float, str]]] = [
    # Verse 1
    [(2.30, 3.70, "Işıklar"), (3.70, 5.10, "düşük")],
    [(6.08, 6.38, "sen"), (6.38, 8.00, "yakındasın")],
    [(9.20, 10.30, "Kelimeler"), (10.30, 12.40, "yetmez")],
    [(12.48, 13.02, "ten"), (13.02, 13.62, "yeter"), (13.62, 15.00, "şimdi")],
    [(15.52, 16.36, "Gözlerin"), (16.36, 16.76, "odada"), (16.76, 17.26, "ateş"), (17.26, 18.20, "yakıyor")],
    [(19.16, 19.50, "sustum")],
    [(19.50, 20.16, "Nefesin"), (20.16, 20.62, "bana"), (20.62, 21.90, "bakıyor")],
    [(22.34, 22.44, "bu"), (22.44, 22.78, "gece"), (22.78, 23.68, "konuşmak"), (23.68, 25.16, "istemiyorum")],
    [(25.16, 26.14, "Sadece"), (26.14, 26.48, "kal"), (26.48, 27.10, "yakından"), (27.10, 28.14, "duyuyorum")],
    [(28.28, 28.88, "Parfümün"), (28.88, 29.74, "boynunda"), (29.74, 30.06, "iz"), (30.06, 31.28, "bırakmış")],
    [(31.28, 32.36, "Saatin"), (32.36, 33.20, "anlamı"), (33.20, 33.82, "çoktan"), (33.82, 34.72, "bitmiş")],
    [(35.24, 35.84, "Ellerin"), (35.84, 36.40, "yavaş")],
    [(36.40, 37.54, "Sözlerin"), (37.54, 38.08, "eksik"), (38.08, 38.32, "ama")],
    [(38.32, 39.28, "Bakışın"), (39.28, 39.74, "her"), (39.74, 40.04, "şeyi"), (40.04, 41.54, "bitirmiş")],
    [(41.54, 42.38, "Gel"), (42.38, 43.32, "biraz"), (43.32, 44.00, "daha")],
    [(44.32, 44.86, "çekilme"), (44.86, 45.24, "geri"), (45.24, 45.60, "bu"), (45.60, 46.08, "gece")],
    [(46.08, 47.06, "bende"), (47.06, 47.68, "kal")],
    [(48.76, 50.00, "Yarın"), (50.00, 50.46, "ne"), (50.46, 51.74, "olursa"), (51.74, 53.14, "olsun")],
    # Chorus 1
    [(53.20, 54.86, "Teninle"), (54.86, 55.12, "kal"), (55.12, 55.50, "bu"), (55.50, 56.66, "gece")],
    [(57.28, 57.70, "Aklım"), (57.70, 58.30, "sende"), (58.30, 59.14, "kayboldu")],
    [(60.02, 61.16, "Dudaklar"), (61.16, 61.64, "yalan"), (61.64, 63.42, "söylemesin")],
    [(63.74, 64.40, "Kalbin"), (64.40, 65.72, "burada"), (65.72, 66.66, "olsun")],
    [(66.80, 68.68, "Teninle"), (68.68, 69.14, "kal"), (69.14, 69.44, "bu"), (69.44, 70.18, "gece")],
    [(70.70, 70.94, "Şehir"), (70.94, 72.10, "dışarıda"), (72.10, 74.14, "uyusun")],
    [(74.70, 75.60, "İkimiz"), (75.60, 76.04, "bu"), (76.04, 77.24, "odada")],
    [(77.24, 79.14, "Sabahı"), (79.14, 79.96, "unutalım")],
    # Verse 2
    [(94.50, 95.30, "Telefon"), (95.30, 95.74, "kapalı")],
    [(95.74, 96.18, "dünya"), (96.18, 96.58, "uzak")],
    [(96.80, 96.90, "Senin"), (96.90, 97.34, "her"), (97.34, 97.50, "şey"), (97.50, 97.90, "daha"), (97.90, 98.30, "sıcak")],
    [(98.30, 98.76, "Kıskanç"), (98.76, 99.20, "değilim"), (99.20, 99.62, "sadece"), (99.62, 100.06, "açım")],
    [(100.12, 100.26, "bu"), (100.26, 100.44, "anı"), (100.44, 100.92, "çalmadan")],
    [(100.92, 101.60, "doyasıya"), (101.60, 102.12, "yaşayayım")],
    [(102.12, 102.70, "Saçların"), (102.70, 103.16, "omzumda"), (103.16, 103.64, "dağınık")],
    [(103.96, 104.38, "Gülüşüm"), (104.38, 104.86, "boğazımda"), (104.86, 105.16, "yanık")],
    [(105.16, 105.46, "Bir"), (105.46, 105.68, "gece"), (105.68, 105.86, "mi"), (105.96, 106.08, "bir"), (106.08, 106.30, "ömür"), (106.30, 106.52, "mi")],
    [(106.52, 106.94, "bilmem")],
    [(106.94, 107.18, "ama"), (107.18, 107.42, "şimdi"), (107.42, 107.84, "senden"), (107.84, 108.98, "vazgeçemem")],
    [(108.98, 109.72, "Gel"), (109.72, 110.60, "biraz"), (110.60, 111.36, "daha")],
    [(111.66, 112.16, "çekilme"), (112.16, 112.56, "geri"), (112.56, 112.96, "bu"), (112.96, 113.42, "gece")],
    [(113.42, 114.32, "bende"), (114.32, 115.22, "kal")],
    [(115.40, 117.32, "Yarın"), (117.32, 117.80, "ne"), (117.80, 119.18, "olursa"), (119.18, 120.20, "olsun")],
    # Chorus 2 (hand-tuned from Short)
    [(120.90, 121.95, "Teninle"), (121.95, 122.28, "kal"), (122.28, 122.60, "bu"), (122.60, 123.25, "gece")],
    [(124.10, 124.80, "Aklım"), (124.80, 125.42, "sende"), (125.42, 126.70, "kayboldu")],
    [(127.44, 128.32, "Dudaklar"), (128.32, 128.80, "yalan"), (128.80, 130.55, "söylemesin")],
    [(130.55, 131.55, "Kalbin"), (132.30, 133.00, "burada"), (133.00, 134.30, "olsun")],
    [(134.55, 135.75, "Teninle"), (135.75, 136.25, "kal"), (136.25, 136.58, "bu"), (136.58, 137.20, "gece")],
    [(137.48, 138.18, "Şehir"), (138.18, 139.00, "dışarıda"), (139.00, 141.70, "uyusun")],
    [(141.98, 142.68, "İkimiz"), (142.68, 143.16, "bu"), (143.16, 144.10, "odada")],
    [(144.66, 145.76, "Sabahı"), (145.76, 147.20, "unutalım")],
    [(148.00, 149.05, "Teninle"), (149.05, 149.55, "kal"), (149.55, 150.05, "bu"), (150.05, 151.40, "gece")],
    [(158.86, 160.26, "Sabahı"), (160.26, 161.12, "unutalım")],
]


def font_path(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def tr_upper(s: str) -> str:
    table = str.maketrans(
        {"i": "İ", "ı": "I", "ş": "Ş", "ğ": "Ğ", "ü": "Ü", "ö": "Ö", "ç": "Ç"}
    )
    return s.translate(table).upper()


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
    return 0.12 + 0.88 * np.power(np.clip(vals, 0, 1), 0.6)


def _display_word(raw: str) -> str:
    key = raw.strip().casefold()
    if key in {"seninle", "seninde"}:
        return "TENİNLE"
    # Hook form only — keep possessive "Senin" in verse 2
    if key == "teninle":
        return "TENİNLE"
    return tr_upper(raw.strip())


def line_at(t: float) -> list[tuple[float, float, str]] | None:
    for words in LINES:
        if words[0][0] - 0.10 <= t <= words[-1][1] + 0.14:
            return [(s, e, _display_word(w)) for s, e, w in words]
    return None


def _measure_spaced(draw: ImageDraw.ImageDraw, text: str, fnt, tracking: int) -> int:
    if not text:
        return 0
    total = 0
    for i, ch in enumerate(text):
        bb = draw.textbbox((0, 0), ch, font=fnt)
        total += bb[2] - bb[0]
        if i < len(text) - 1:
            total += tracking
    return total


def _draw_spaced(draw, xy, text, fnt, fill, tracking: int) -> None:
    x, y = xy
    for i, ch in enumerate(text):
        draw.text((x, y), ch, font=fnt, fill=fill)
        bb = draw.textbbox((0, 0), ch, font=fnt)
        x += (bb[2] - bb[0]) + tracking


def draw_kinetic_lyrics(img: Image.Image, t: float, audio_level: float = 0.35) -> None:
    words = line_at(t)
    if not words:
        return

    line_start, line_end = words[0][0], words[-1][1]
    alpha = 1.0
    if t < line_start - WORD_LEAD:
        alpha = max(0.0, 1.0 - (line_start - WORD_LEAD - t) / 0.08)
    elif t > line_end:
        alpha = max(0.0, 1.0 - (t - line_end) / 0.12)
    if alpha <= 0.01:
        return

    lvl = max(0.0, min(1.0, audio_level))
    fsize = max(44, int(50 * (1.0 + 0.04 * lvl)))
    fnt = font_path(FONT_OUTFIT, fsize)
    tracking = 5
    word_gap = 26

    probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    texts = [w for _, _, w in words]
    word_widths = [_measure_spaced(probe, w, fnt, tracking) for w in texts]
    total = sum(word_widths) + word_gap * max(0, len(texts) - 1)
    th_bb = probe.textbbox((0, 0), "A", font=fnt)
    th = th_bb[3] - th_bb[1]
    x = (W - total) // 2
    y = LYRIC_Y - th // 2 - int(5 * lvl)

    bloom = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bloom)
    cx = x
    for i, w in enumerate(texts):
        _draw_spaced(bd, (cx, y), w, fnt, (*CREAM, int((40 + 50 * lvl) * alpha)), tracking)
        cx += word_widths[i] + word_gap
    img.alpha_composite(bloom.filter(ImageFilter.GaussianBlur(12 + int(4 * lvl))))

    stroke = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stroke)
    cx = x
    for i, w in enumerate(texts):
        for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2)):
            _draw_spaced(sd, (cx + ox, y + oy), w, fnt, (0, 0, 0, int(200 * alpha)), tracking)
        cx += word_widths[i] + word_gap
    img.alpha_composite(stroke)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    cx = x
    for i, (ws, we, w) in enumerate(words):
        lead_s = ws - WORD_LEAD
        if t < lead_s:
            col = (150, 145, 138, int(130 * alpha))
            wy = y
        elif t < we:
            frac = (t - lead_s) / max(0.05, we - lead_s)
            col = (*CREAM, int(255 * alpha))
            wy = y - int((4 + 8 * lvl) * math.sin(min(1.0, frac) * math.pi))
        else:
            col = (255, 255, 255, int(255 * alpha))
            wy = y
        _draw_spaced(ld, (cx, wy), w, fnt, col, tracking)
        cx += word_widths[i] + word_gap
    img.alpha_composite(layer)


def draw_eq(draw: ImageDraw.ImageDraw, vals: np.ndarray, progress: float) -> None:
    n = len(vals)
    pill_w, pill_h = 720, EQ_H
    pill_x = (W - pill_w) // 2
    eq_y = EQ_Y
    draw.rounded_rectangle(
        (pill_x, eq_y, pill_x + pill_w, eq_y + pill_h),
        radius=16,
        fill=(14, 12, 11),
        outline=(42, 38, 34),
        width=1,
    )
    margin_x, margin_y = 22, 10
    usable_w = pill_w - 2 * margin_x
    usable_h = pill_h - 2 * margin_y
    gap = 5
    bar_w = max(6, int((usable_w - gap * (n - 1)) / n))
    total = n * bar_w + (n - 1) * gap
    start_x = pill_x + margin_x + (usable_w - total) // 2
    base_y = eq_y + pill_h - margin_y
    for i, v in enumerate(vals):
        bh = int(7 + float(v) * (usable_h - 7))
        x0 = start_x + i * (bar_w + gap)
        color = CREAM if i % 3 != 2 else CREAM2
        draw.rounded_rectangle(
            (x0, base_y - bh, x0 + bar_w, base_y), radius=bar_w // 2, fill=color
        )

    bar_x0, bar_x1 = 420, W - 420
    draw.line((bar_x0, PROGRESS_Y, bar_x1, PROGRESS_Y), fill=PROGRESS_BG, width=2)
    px = bar_x0 + int((bar_x1 - bar_x0) * progress)
    draw.line((bar_x0, PROGRESS_Y, px, PROGRESS_Y), fill=CREAM, width=2)
    draw.ellipse((px - 5, PROGRESS_Y - 5, px + 5, PROGRESS_Y + 5), fill=CREAM)


def base_landscape() -> Image.Image:
    """Full-bleed cinematic cover crop — same language as the Short, 16:9."""
    src = Image.open(COVER).convert("RGB")
    scale = max(W / src.width, H / src.height) * 1.06
    nw, nh = int(src.width * scale), int(src.height * scale)
    img = src.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - W) // 2
    # Bias crop slightly up so face sits well in landscape
    top = max(0, int((nh - H) * 0.22))
    if top + H > nh:
        top = nh - H
    img = img.crop((left, top, left + W, top + H))

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    # Soft top vignette
    for yy in range(0, 160):
        a = int(90 * (1 - yy / 160))
        d.line([(0, yy), (W, yy)], fill=(0, 0, 0, a))
    # Soft bottom fade into credit zone
    fade_start = CREDIT_TOP - 160
    for yy in range(fade_start, H):
        p = (yy - fade_start) / max(1, H - fade_start)
        a = int(min(245, (p**1.25) * 255))
        d.line([(0, yy), (W, yy)], fill=(0, 0, 0, a))
    out = Image.alpha_composite(img.convert("RGBA"), overlay)
    d2 = ImageDraw.Draw(out)

    line_y = CREDIT_TOP + 18
    line_w = 64
    d2.line(
        ((W - line_w) // 2, line_y, (W + line_w) // 2, line_y),
        fill=CREAM,
        width=2,
    )

    artist_fnt = font_path(FONT_SERIF, 40)
    title_fnt = font_path(FONT_OUTFIT, 22)
    credit_fnt = font_path(FONT_OUTFIT, 16)

    def center_spaced(text: str, fnt, y: int, fill, tracking: int) -> None:
        tw = _measure_spaced(d2, text, fnt, tracking)
        _draw_spaced(d2, ((W - tw) // 2, y), text, fnt, fill, tracking)

    center_spaced(ARTIST, artist_fnt, line_y + 22, WHITE, 5)
    center_spaced(TITLE, title_fnt, line_y + 78, CREAM, 8)
    center_spaced(CREDIT, credit_fnt, line_y + 118, MUTED, 3)
    return out.convert("RGBA")


def render() -> None:
    samples, rate = ensure_wav()
    duration = len(samples) / rate
    n_frames = int(round(duration * FPS))
    print(f"Rendering 16:9 FULL 0-{duration:.1f}s ({n_frames}f)", flush=True)

    base = base_landscape()
    hop = rate // FPS
    n_bars = 28
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
    peak_rms = 1e-6
    try:
        for fi in range(n_frames):
            t = fi / FPS
            chunk = samples[fi * hop : fi * hop + hop * 2]
            rms = float(np.sqrt(np.mean(np.square(chunk)))) if len(chunk) else 0.0
            peak_rms = max(peak_rms * 0.995, rms, 1e-6)
            audio_level = min(1.0, (rms / peak_rms) ** 0.85)
            smooth = 0.55 * smooth + 0.45 * band_energies(chunk, n_bars)
            frame = base.copy()
            draw_kinetic_lyrics(frame, t, audio_level=audio_level)
            d = ImageDraw.Draw(frame)
            draw_eq(d, smooth, t / max(0.001, duration))
            proc.stdin.write(frame.convert("RGB").tobytes())
            if fi % 96 == 0:
                print(f"  {fi}/{n_frames} ({100 * fi / n_frames:.0f}%)", flush=True)
    finally:
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        code = proc.wait()
    if code != 0:
        print(err[-2500:], file=sys.stderr)
        raise RuntimeError(f"ffmpeg failed {code}")
    dest = ART / OUT.name
    dest.write_bytes(OUT.read_bytes())
    print(f"Done {OUT} ({OUT.stat().st_size / 1e6:.1f}MB)", flush=True)


if __name__ == "__main__":
    ART.mkdir(parents=True, exist_ok=True)
    render()
