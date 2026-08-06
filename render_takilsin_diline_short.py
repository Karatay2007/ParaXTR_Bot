#!/usr/bin/env python3
"""Arven Solé — Takılsın Diline Shorts.

Updates vs Teninde Kal Short:
- DEVAMI YAYINDA lower (not under status bar)
- Like / ABONE OL / Bell CTA centered
- Slightly smaller lyric size
"""

from __future__ import annotations

import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AUDIO = Path("/workspace/arven_sole_tracks/Takilsin_Diline.mp3")
COVER = Path("/opt/cursor/artifacts/assets/arven-sole-cover.png")
WAV = Path("/tmp/takilsin.wav")
FONT_DIR = Path("/usr/share/fonts/truetype/macos")
FONT_OUTFIT = Path("/workspace/fonts/Outfit.ttf")
FONT_SERIF = Path("/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf")
FONT_LYRIC = Path("/usr/share/fonts/truetype/noto/NotoSansDisplay-Bold.ttf")
FONT_BANNER = Path("/workspace/fonts/ArchivoBlack-Regular.ttf")
ART = Path("/opt/cursor/artifacts")
OUT_SHORT = Path("/workspace/ArvenSole_TakilsinDiline_SHORT.mp4")

W, H = 1080, 1920
FPS = 24
CREAM = (232, 220, 200)
CREAM2 = (210, 195, 170)
WHITE = (255, 255, 255)
MUTED = (168, 162, 152)
PROGRESS_BG = (55, 50, 45)
YT_RED = (255, 0, 0)
INK = (10, 8, 6)

TITLE = "TAKILSIN DİLİNE"
ARTIST = "ARVEN SOLÉ"
CREDIT = "SÖZ · MÜZİK   ARVEN SOLÉ"
TOP_BANNER = "DEVAMI YAYINDA"

# Layout — wide banner; lyrics mid; CTA under Söz-Müzik
BANNER_Y = 250
LYRIC_Y = 780
EQ_Y = 890
EQ_H = 72
CREDIT_TOP = 1220
CTA_Y = 1585
PROGRESS_Y = 1785
LIKE_BLUE = (66, 133, 244)

# Hottest chorus 2
SHORT_T0 = 109.2
SHORT_T1 = 136.2
WORD_LEAD = 0.05

# Cleaned word clocks (chorus 2). "birden maz" → "bir daha anma"
LINES: list[list[tuple[float, float, str]]] = [
    [(109.40, 110.80, "Geçti"), (110.80, 111.06, "o"), (111.06, 113.28, "günler")],
    [(113.72, 114.34, "dönmem"), (114.34, 115.40, "geriye")],
    [(116.46, 117.72, "Değmez"), (117.72, 119.38, "misin")],
    [(119.38, 120.52, "tek"), (120.52, 120.96, "bir"), (120.96, 122.40, "sevgime")],
    [(123.18, 124.20, "Adımı"), (124.20, 126.20, "bir"), (126.20, 127.10, "daha")],
    [(127.10, 128.42, "anma"), (128.42, 129.40, "sakın")],
    [(130.80, 131.72, "Düşmem"), (131.72, 132.90, "artık"), (132.90, 133.92, "senin"), (133.92, 135.62, "tuzağına")],
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
    return tr_upper(raw.strip().strip(",.!?"))


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
    # Slightly smaller than Teninde Kal Short
    fsize = max(46, int(50 * (1.0 + 0.035 * lvl)))
    fnt = font_path(FONT_LYRIC, fsize)
    tracking = 4
    word_gap = 22

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
        _draw_spaced(bd, (cx, y), w, fnt, (*CREAM, int((50 + 55 * lvl) * alpha)), tracking)
        cx += word_widths[i] + word_gap
    img.alpha_composite(bloom.filter(ImageFilter.GaussianBlur(12 + int(4 * lvl))))

    stroke = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stroke)
    cx = x
    offsets = (
        (-3, 0), (3, 0), (0, -3), (0, 3),
        (-3, -3), (3, 3), (-3, 3), (3, -3),
        (-2, 0), (2, 0), (0, -2), (0, 2),
    )
    for i, w in enumerate(texts):
        for ox, oy in offsets:
            _draw_spaced(sd, (cx + ox, y + oy), w, fnt, (0, 0, 0, int(220 * alpha)), tracking)
        cx += word_widths[i] + word_gap
    img.alpha_composite(stroke)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    cx = x
    for i, (ws, we, w) in enumerate(words):
        lead_s = ws - WORD_LEAD
        if t < lead_s:
            col = (210, 200, 188, int(200 * alpha))
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

    bar_x0, bar_x1 = 180, W - 180
    draw.line((bar_x0, PROGRESS_Y, bar_x1, PROGRESS_Y), fill=PROGRESS_BG, width=2)
    px = bar_x0 + int((bar_x1 - bar_x0) * progress)
    draw.line((bar_x0, PROGRESS_Y, px, PROGRESS_Y), fill=CREAM, width=2)
    draw.ellipse((px - 5, PROGRESS_Y - 5, px + 5, PROGRESS_Y + 5), fill=CREAM)


def _draw_hand(d: ImageDraw.ImageDraw, tip_x: int, tip_y: int, scale: float = 1.0) -> None:
    """White cursor hand pointing at tip (reference style)."""
    s = scale
    d.rounded_rectangle(
        (tip_x - int(5 * s), tip_y, tip_x + int(5 * s), tip_y + int(34 * s)),
        radius=4,
        fill=(255, 255, 255, 255),
        outline=(30, 30, 30, 255),
        width=2,
    )
    palm = [
        (tip_x - int(6 * s), tip_y + int(28 * s)),
        (tip_x + int(22 * s), tip_y + int(30 * s)),
        (tip_x + int(26 * s), tip_y + int(58 * s)),
        (tip_x - int(10 * s), tip_y + int(56 * s)),
    ]
    d.polygon(palm, fill=(255, 255, 255, 255))
    d.line(palm + [palm[0]], fill=(30, 30, 30, 255), width=2)
    for ox in (8, 14, 20):
        d.rounded_rectangle(
            (
                tip_x + int(ox * s),
                tip_y + int(32 * s),
                tip_x + int((ox + 6) * s),
                tip_y + int(48 * s),
            ),
            radius=3,
            fill=(255, 255, 255, 255),
            outline=(30, 30, 30, 255),
            width=1,
        )


def _draw_thumb(d: ImageDraw.ImageDraw, cx: int, cy: int, r: int, active: bool) -> None:
    """White circle + light-blue thumbs-up (matches reference)."""
    d.ellipse(
        (cx - r, cy - r, cx + r, cy + r),
        fill=(255, 255, 255, 255),
        outline=(230, 230, 230, 255),
        width=2,
    )
    if active:
        d.ellipse((cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4), outline=(*LIKE_BLUE, 180), width=3)
    blue = (*LIKE_BLUE, 255)
    d.rounded_rectangle((cx - 13, cy - 1, cx + 14, cy + 18), radius=5, fill=blue)
    d.rounded_rectangle((cx - 2, cy - 22, cx + 12, cy + 4), radius=7, fill=blue)
    for ky in (cy + 4, cy + 10):
        d.line((cx - 8, ky, cx + 9, ky), fill=(255, 255, 255, 90), width=1)


def _draw_bell(d: ImageDraw.ImageDraw, cx: int, cy: int, r: int, active: bool) -> None:
    """White circle + clean grey bell."""
    d.ellipse(
        (cx - r, cy - r, cx + r, cy + r),
        fill=(255, 255, 255, 255),
        outline=(230, 230, 230, 255),
        width=2,
    )
    if active:
        d.ellipse((cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4), outline=(80, 80, 80, 160), width=3)
    ink = (70, 70, 70, 255)
    d.pieslice((cx - 15, cy - 12, cx + 15, cy + 14), 200, 340, fill=ink)
    d.ellipse((cx - 15, cy - 1, cx + 15, cy + 17), fill=ink)
    d.ellipse((cx - 3, cy - 18, cx + 3, cy - 10), fill=ink)
    d.ellipse((cx - 5, cy + 15, cx + 5, cy + 23), fill=ink)


def draw_subscribe_cta(img: Image.Image, t_local: float) -> None:
    """Reference-style like · ABONE OL · bell — under Söz-Müzik."""
    phase = (t_local % 3.3) / 1.1
    active = int(phase) % 3
    subphase = phase - int(phase)
    click = math.sin(min(1.0, subphase / 0.35) * math.pi) if subphase < 0.45 else 0.0

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    like_r = int(42 + (5 * click if active == 0 else 0))
    bell_r = int(42 + (5 * click if active == 2 else 0))
    sub_scale = 1.0 + (0.06 * click if active == 1 else 0.0)

    gap = 22
    sub_w, sub_h = int(300 * sub_scale), int(72 * sub_scale)
    total_w = like_r * 2 + gap + sub_w + gap + bell_r * 2
    x0 = (W - total_w) // 2
    cy = CTA_Y

    like_cx = x0 + like_r
    sub_x = like_cx + like_r + gap
    sub_y = cy - sub_h // 2
    bell_cx = sub_x + sub_w + gap + bell_r

    d.rounded_rectangle(
        (sub_x + 4, sub_y + 6, sub_x + sub_w + 4, sub_y + sub_h + 6),
        radius=10,
        fill=(0, 0, 0, 90),
    )

    _draw_thumb(d, like_cx, cy, like_r, active == 0)

    d.rounded_rectangle(
        (sub_x, sub_y, sub_x + sub_w, sub_y + sub_h),
        radius=10,
        fill=(255, 0, 0, 255),
    )
    fnt = font_path(FONT_DIR / "Inter-Bold.ttf", int(32 * sub_scale))
    label = "ABONE OL"
    bb = d.textbbox((0, 0), label, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text(
        (sub_x + (sub_w - tw) // 2, sub_y + (sub_h - th) // 2 - 2),
        label,
        font=fnt,
        fill=(255, 255, 255, 255),
    )

    _draw_bell(d, bell_cx, cy, bell_r, active == 2)

    hy0 = cy + 14
    _draw_hand(
        d,
        like_cx + 8,
        hy0 + (int(8 * (1 - click)) if active == 0 else 6),
        1.0 if active == 0 else 0.92,
    )
    _draw_hand(
        d,
        bell_cx + 8,
        hy0 + (int(8 * (1 - click)) if active == 2 else 6),
        1.0 if active == 2 else 0.92,
    )
    if active == 1:
        _draw_hand(d, sub_x + sub_w // 2 + 6, sub_y + sub_h - 2 + int(6 * (1 - click)), 0.95)

    img.alpha_composite(layer)


def draw_top_banner(img: Image.Image, t_local: float = 0.0) -> None:
    """Wide single-line DEVAMI YAYINDA bar — not a skinny stacked stamp."""
    beat = 0.5 + 0.5 * math.sin(t_local * 2.2)
    scale = 1.0 + 0.025 * beat

    fnt = font_path(FONT_BANNER, int(48 * scale))
    tracking = 8
    text = "DEVAMI YAYINDA"
    probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    tw = _measure_spaced(probe, text, fnt, tracking)
    thb = probe.textbbox((0, 0), text, font=fnt)
    th = thb[3] - thb[1]

    box_w = min(980, max(tw + 120, 860))
    box_h = max(96, th + 44)
    bx = (W - box_w) // 2
    by = BANNER_Y - int(2 * beat)

    cream = (
        min(255, int(245 + 8 * beat)),
        min(255, int(234 + 6 * beat)),
        min(255, int(214 + 4 * beat)),
        255,
    )

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle(
        (bx + 6, by + 8, bx + box_w + 6, by + box_h + 8),
        radius=16,
        fill=(0, 0, 0, 170),
    )
    d.rounded_rectangle((bx, by, bx + box_w, by + box_h), radius=16, fill=cream)
    d.rounded_rectangle(
        (bx, by, bx + box_w, by + box_h),
        radius=16,
        outline=(*INK, 255),
        width=4,
    )
    d.rounded_rectangle(
        (bx + 8, by + 8, bx + box_w - 8, by + box_h - 8),
        radius=12,
        outline=(40, 36, 30, 255),
        width=1,
    )
    _draw_spaced(
        d,
        (bx + (box_w - tw) // 2, by + (box_h - th) // 2 - 2),
        text,
        fnt,
        (*INK, 255),
        tracking,
    )
    img.alpha_composite(layer)


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
    fade_start = CREDIT_TOP - 220
    for yy in range(fade_start, H):
        p = (yy - fade_start) / max(1, H - fade_start)
        a = int(min(245, (p**1.35) * 255))
        d.line([(0, yy), (W, yy)], fill=(0, 0, 0, a))
    out = Image.alpha_composite(img.convert("RGBA"), overlay)
    d2 = ImageDraw.Draw(out)

    line_y = CREDIT_TOP + 40
    line_w = 72
    d2.line(
        ((W - line_w) // 2, line_y, (W + line_w) // 2, line_y),
        fill=CREAM,
        width=2,
    )

    artist_fnt = font_path(FONT_SERIF, 52)
    title_fnt = font_path(FONT_OUTFIT, 26)
    credit_fnt = font_path(FONT_OUTFIT, 20)

    def center_spaced(text: str, fnt, y: int, fill, tracking: int) -> None:
        tw = _measure_spaced(d2, text, fnt, tracking)
        _draw_spaced(d2, ((W - tw) // 2, y), text, fnt, fill, tracking)

    center_spaced(ARTIST, artist_fnt, line_y + 36, WHITE, 6)
    center_spaced(TITLE, title_fnt, line_y + 110, CREAM, 8)
    center_spaced(CREDIT, credit_fnt, line_y + 155, MUTED, 4)
    return out.convert("RGBA")


def render_short() -> None:
    samples, rate = ensure_wav()
    duration = len(samples) / rate
    t0, t1 = SHORT_T0, min(SHORT_T1, duration)
    clip_dur = t1 - t0
    n_frames = int(round(clip_dur * FPS))
    print(f"Rendering SHORT {t0:.1f}-{t1:.1f}s ({n_frames}f)", flush=True)

    audio_clip = Path("/tmp/takilsin_short_clip.wav")
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
            t_local = t - t0
            chunk = samples[start + fi * hop : start + fi * hop + hop * 2]
            rms = float(np.sqrt(np.mean(np.square(chunk)))) if len(chunk) else 0.0
            peak_rms = max(peak_rms * 0.995, rms, 1e-6)
            audio_level = min(1.0, (rms / peak_rms) ** 0.85)
            smooth = 0.55 * smooth + 0.45 * band_energies(chunk, n_bars)
            frame = base.copy()
            draw_top_banner(frame, t_local=t_local)
            draw_subscribe_cta(frame, t_local=t_local)
            draw_kinetic_lyrics(frame, t, audio_level=audio_level)
            d = ImageDraw.Draw(frame)
            draw_eq(d, smooth, t_local / max(0.001, clip_dur))
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
    dest = ART / OUT_SHORT.name
    dest.write_bytes(OUT_SHORT.read_bytes())
    print(f"Done {OUT_SHORT} ({OUT_SHORT.stat().st_size / 1e6:.1f}MB)", flush=True)


if __name__ == "__main__":
    ART.mkdir(parents=True, exist_ok=True)
    render_short()
