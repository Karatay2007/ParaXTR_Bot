#!/usr/bin/env python3
"""Arven Solé — Teninde Kal Shorts with real kinetic lyric effects.

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
FONT_DIR = Path("/usr/share/fonts/truetype/macos")
FONT_OUTFIT = Path("/workspace/fonts/Outfit.ttf")
FONT_SERIF = Path("/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf")
ART = Path("/opt/cursor/artifacts")
OUT_SHORT = Path("/workspace/ArvenSole_TenindeKal_SHORT.mp4")

W, H = 1080, 1920
FPS = 24
CREAM = (232, 220, 200)
CREAM2 = (210, 195, 170)
WHITE = (255, 255, 255)
MUTED = (168, 162, 152)
PROGRESS_BG = (55, 50, 45)

TITLE = "TENİNDE KAL"
ARTIST = "ARVEN SOLÉ"
CREDIT = "SÖZ · MÜZİK   ARVEN SOLÉ"

# Cover layout — lyrics + EQ tight & high; credits breathe below
LYRIC_Y = 760
EQ_Y = 870
EQ_H = 72
CREDIT_TOP = 1280
PROGRESS_Y = 1765

# Hottest chorus block — start just before first hook word
SHORT_T0 = 120.7
SHORT_T1 = 154.5

# Highlight starts slightly early so the word lights with the sung onset (feels instant).
WORD_LEAD = 0.05

# Word clocks from Whisper on hook clip (offset +118s), Senin/de → Teninle.
# Each word: (start, end, text). Ends clamped to next word.
LINES: list[list[tuple[float, float, str]]] = [
    [(120.90, 121.95, "Teninle"), (121.95, 122.28, "kal"), (122.28, 122.60, "bu"), (122.60, 123.25, "gece")],
    [(124.10, 124.80, "Aklım"), (124.80, 125.42, "sende"), (125.42, 126.70, "kayboldu")],
    [(127.44, 128.32, "Dudaklar"), (128.32, 128.80, "yalan"), (128.80, 130.55, "söylemesin")],
    [(130.55, 131.55, "Kalbin"), (132.30, 133.00, "burada"), (133.00, 134.30, "olsun")],
    [(134.55, 135.75, "Teninle"), (135.75, 136.25, "kal"), (136.25, 136.58, "bu"), (136.58, 137.20, "gece")],
    [(137.48, 138.18, "Şehir"), (138.18, 139.00, "dışarıda"), (139.00, 141.70, "uyusun")],
    [(141.98, 142.68, "İkimiz"), (142.68, 143.16, "bu"), (143.16, 144.10, "odada")],
    [(144.66, 145.76, "Sabahı"), (145.76, 147.20, "unutalım")],
    # last hook: "bu" must NOT swallow the held "gece"
    [(148.00, 149.05, "Teninle"), (149.05, 149.55, "kal"), (149.55, 150.05, "bu"), (150.05, 151.40, "gece")],
]


def font_path(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def font_inter(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def tr_upper(s: str) -> str:
    """Turkish-aware uppercase (i→İ, ı→I, …)."""
    table = str.maketrans(
        {
            "i": "İ",
            "ı": "I",
            "ş": "Ş",
            "ğ": "Ğ",
            "ü": "Ü",
            "ö": "Ö",
            "ç": "Ç",
            "I": "I",
            "İ": "İ",
        }
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


def _display_word(raw: str) -> str:
    """Force hook spelling — never Seninle / Senin de. Always UPPERCASE."""
    key = raw.strip().casefold()
    if key in {"seninle", "senin", "seninde", "senin de"}:
        return "TENİNLE"
    return tr_upper(raw.strip())


def line_at(t: float) -> list[tuple[float, float, str]] | None:
    """Return the active line's word timings for absolute time t."""
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


def _draw_spaced(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fnt,
    fill,
    tracking: int,
) -> None:
    x, y = xy
    for i, ch in enumerate(text):
        draw.text((x, y), ch, font=fnt, fill=fill)
        bb = draw.textbbox((0, 0), ch, font=fnt)
        x += (bb[2] - bb[0]) + tracking


def draw_kinetic_lyrics(img: Image.Image, t: float, audio_level: float = 0.35) -> None:
    """Instant per-word highlight — stylish uppercase + tracking."""
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
    fsize = max(48, int(54 * (1.0 + 0.04 * lvl)))
    fnt = font_path(FONT_OUTFIT, fsize)
    tracking = 5  # airy uppercase look
    word_gap = 28

    probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    texts = [w for _, _, w in words]
    word_widths = [_measure_spaced(probe, w, fnt, tracking) for w in texts]
    total = sum(word_widths) + word_gap * max(0, len(texts) - 1)
    th_bb = probe.textbbox((0, 0), "A", font=fnt)
    th = th_bb[3] - th_bb[1]
    x = (W - total) // 2
    y = LYRIC_Y - th // 2 - int(6 * lvl)

    # Soft cream bloom behind the line
    bloom = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bloom)
    cx = x
    for i, w in enumerate(texts):
        _draw_spaced(bd, (cx, y), w, fnt, (*CREAM, int((40 + 50 * lvl) * alpha)), tracking)
        cx += word_widths[i] + word_gap
    img.alpha_composite(bloom.filter(ImageFilter.GaussianBlur(12 + int(4 * lvl))))

    # Dark stroke for readability
    stroke = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stroke)
    cx = x
    for i, w in enumerate(texts):
        for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)):
            _draw_spaced(
                sd, (cx + ox, y + oy), w, fnt, (0, 0, 0, int(200 * alpha)), tracking
            )
        cx += word_widths[i] + word_gap
    img.alpha_composite(stroke)

    # Active word = clock window (with lead)
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
            wy = y - int((5 + 10 * lvl) * math.sin(min(1.0, frac) * math.pi))
        else:
            col = (255, 255, 255, int(255 * alpha))
            wy = y
        _draw_spaced(ld, (cx, wy), w, fnt, col, tracking)
        cx += word_widths[i] + word_gap
    img.alpha_composite(layer)


def draw_eq(draw: ImageDraw.ImageDraw, vals: np.ndarray, progress: float) -> None:
    n = len(vals)
    pill_w, pill_h = 620, EQ_H
    pill_x = (W - pill_w) // 2
    eq_y = EQ_Y
    draw.rounded_rectangle(
        (pill_x, eq_y, pill_x + pill_w, eq_y + pill_h),
        radius=18,
        fill=(14, 12, 11),
        outline=(42, 38, 34),
        width=1,
    )
    margin_x, margin_y = 24, 12
    usable_w = pill_w - 2 * margin_x
    usable_h = pill_h - 2 * margin_y
    gap = 5
    bar_w = max(7, int((usable_w - gap * (n - 1)) / n))
    total = n * bar_w + (n - 1) * gap
    start_x = pill_x + margin_x + (usable_w - total) // 2
    base_y = eq_y + pill_h - margin_y
    for i, v in enumerate(vals):
        bh = int(8 + float(v) * (usable_h - 8))
        x0 = start_x + i * (bar_w + gap)
        color = CREAM if i % 3 != 2 else CREAM2
        draw.rounded_rectangle(
            (x0, base_y - bh, x0 + bar_w, base_y), radius=bar_w // 2, fill=color
        )

    # Slim progress near bottom of cover block
    bar_x0, bar_x1 = 180, W - 180
    draw.line((bar_x0, PROGRESS_Y, bar_x1, PROGRESS_Y), fill=PROGRESS_BG, width=2)
    px = bar_x0 + int((bar_x1 - bar_x0) * progress)
    draw.line((bar_x0, PROGRESS_Y, px, PROGRESS_Y), fill=CREAM, width=2)
    draw.ellipse((px - 5, PROGRESS_Y - 5, px + 5, PROGRESS_Y + 5), fill=CREAM)


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

    # Soft vignette into credit zone — cover-like, not a hard black slab
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    fade_start = CREDIT_TOP - 220
    for yy in range(fade_start, H):
        p = (yy - fade_start) / max(1, H - fade_start)
        # ease into deep black for readability
        a = int(min(245, (p**1.35) * 255))
        d.line([(0, yy), (W, yy)], fill=(0, 0, 0, a))
    out = Image.alpha_composite(img.convert("RGBA"), overlay)
    d2 = ImageDraw.Draw(out)

    # Cover credit stack — breathing room under EQ
    line_y = CREDIT_TOP + 40
    line_w = 72
    d2.line(
        ((W - line_w) // 2, line_y, (W + line_w) // 2, line_y),
        fill=CREAM,
        width=2,
    )

    artist_fnt = font_path(FONT_SERIF, 52)
    title_fnt = font_path(FONT_OUTFIT, 28)
    credit_fnt = font_path(FONT_OUTFIT, 20)

    def center_spaced(text: str, fnt, y: int, fill, tracking: int) -> None:
        tw = _measure_spaced(d2, text, fnt, tracking)
        _draw_spaced(d2, ((W - tw) // 2, y), text, fnt, fill, tracking)

    center_spaced(ARTIST, artist_fnt, line_y + 36, WHITE, 6)
    center_spaced(TITLE, title_fnt, line_y + 110, CREAM, 10)
    center_spaced(CREDIT, credit_fnt, line_y + 168, MUTED, 4)
    return out.convert("RGBA")


def render_short() -> None:
    samples, rate = ensure_wav()
    duration = len(samples) / rate
    t0, t1 = SHORT_T0, min(SHORT_T1, duration)
    clip_dur = t1 - t0
    n_frames = int(round(clip_dur * FPS))
    print(f"Rendering SHORT {t0:.1f}-{t1:.1f}s ({n_frames}f)", flush=True)

    # Pre-cut audio so mux has zero seek drift vs frame clock
    audio_clip = Path("/tmp/teninde_short_clip.wav")
    subprocess.check_call(
        [
            "ffmpeg", "-y",
            "-ss", f"{t0:.3f}", "-t", f"{clip_dur:.3f}",
            "-i", str(AUDIO),
            "-ac", "2", "-ar", "44100",
            str(audio_clip),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    base = base_vertical()
    hop = rate // FPS
    n_bars = 24
    smooth = np.zeros(n_bars, dtype=np.float32)
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(audio_clip),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        str(OUT_SHORT),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    start = int(t0 * rate)
    peak_rms = 1e-6
    try:
        for fi in range(n_frames):
            t = t0 + fi / FPS
            chunk = samples[start + fi * hop : start + fi * hop + hop * 2]
            rms = float(np.sqrt(np.mean(np.square(chunk)))) if len(chunk) else 0.0
            peak_rms = max(peak_rms * 0.995, rms, 1e-6)
            audio_level = min(1.0, (rms / peak_rms) ** 0.85)
            smooth = 0.55 * smooth + 0.45 * band_energies(chunk, n_bars)
            frame = base.copy()
            draw_kinetic_lyrics(frame, t, audio_level=audio_level)
            d = ImageDraw.Draw(frame)
            draw_eq(d, smooth, (t - t0) / max(0.001, clip_dur))
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
