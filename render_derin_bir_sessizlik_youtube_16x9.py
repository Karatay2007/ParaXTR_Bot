#!/usr/bin/env python3
"""Arven Solé — Derin Bir Sessizlik YouTube 16:9 (Short look, no DEVAMI YAYINDA)."""

from __future__ import annotations

import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AUDIO = Path("/workspace/arven_sole_tracks/DerinBirSessizlik.mp3")
COVER = Path("/opt/cursor/artifacts/assets/arven-sole-cover.png")
WAV = Path("/tmp/derin.wav")
FONT_DIR = Path("/usr/share/fonts/truetype/macos")
FONT_OUTFIT = Path("/workspace/fonts/Outfit.ttf")
FONT_SERIF = Path("/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf")
FONT_LYRIC = Path("/usr/share/fonts/truetype/noto/NotoSansDisplay-Bold.ttf")
ICON_THUMB = Path("/workspace/fonts/icons/thumb_up.png")
ICON_BELL = Path("/workspace/fonts/icons/bell.png")
ART = Path("/opt/cursor/artifacts")
OUT = Path("/workspace/ArvenSole_DerinBirSessizlik_YOUTUBE_16x9.mp4")

W, H = 1920, 1080
FPS = 24
CREAM = (232, 220, 200)
CREAM2 = (210, 195, 170)
WHITE = (255, 255, 255)
MUTED = (168, 162, 152)
PROGRESS_BG = (55, 50, 45)
LIKE_BLUE = (66, 133, 244)

TITLE = "DERİN BİR SESSİZLİK"
ARTIST = "ARVEN SOLÉ"
CREDIT = "SÖZ · MÜZİK   ARVEN SOLÉ"

# Pulled up — lyrics+EQ high, credit stack, CTA, open air below
LYRIC_Y = 430
EQ_Y = 520
EQ_H = 90
CREDIT_TOP = 640
CTA_Y = 880
PROGRESS_Y = 1025

WORD_LEAD = 0.05

# Full-track cleaned word clocks (Whisper + Short chorus-2 hand-tune).
# Fixes: Geçmişin / o tren / şehrin / o rüya
LINES: list[list[tuple[float, float, str]]] = [
    # Verse 1
    [(14.02, 15.42, "Karanlık"), (15.42, 16.20, "sokaklar"), (16.20, 16.74, "ıslak"), (16.74, 17.96, "kaldırımlar")],
    [(17.96, 19.00, "Geçmişin"), (19.00, 19.58, "yükünü"), (19.58, 20.78, "sırtımdan"), (20.78, 21.56, "attım")],
    [(21.56, 22.46, "Camları"), (22.46, 23.00, "döven"), (23.00, 23.30, "şu"), (23.30, 23.84, "soğuk"), (23.84, 24.84, "damlalar")],
    [(24.84, 25.38, "Seni"), (25.38, 26.60, "hatırlatmaz"), (26.60, 27.18, "artık"), (27.18, 28.46, "unuttum")],
    [(28.46, 28.98, "Boşuna"), (28.98, 29.48, "bakma"), (29.48, 30.10, "o tren"), (30.10, 31.16, "çoktan"), (31.16, 31.96, "kalktı")],
    [(31.96, 32.90, "Geriye"), (32.90, 33.46, "sadece"), (33.46, 34.62, "dumanı"), (34.62, 35.46, "kaldı")],
    [(35.46, 36.18, "gözümün"), (36.18, 36.92, "önünde"), (36.92, 37.48, "yalan"), (37.48, 37.86, "bir"), (37.86, 38.58, "resim")],
    [(38.72, 39.42, "Ben"), (39.42, 39.58, "o"), (39.58, 40.60, "çerçeveyi"), (40.60, 41.36, "duvardan"), (41.36, 43.00, "söktüm")],
    [(43.00, 43.50, "Kimse"), (43.50, 44.06, "kimseden"), (44.06, 45.30, "alacaklı"), (45.30, 45.68, "değil")],
    [(45.68, 46.18, "bu"), (46.18, 46.64, "hesap"), (46.64, 47.06, "burada"), (47.06, 48.36, "kapandı"), (48.36, 49.14, "çoktan")],
    [(49.14, 49.96, "Gölgen"), (49.96, 50.36, "bile"), (50.36, 50.96, "geçmez"), (50.96, 51.54, "artık"), (51.54, 52.54, "kapımdan")],
    [(52.54, 52.94, "Eski"), (52.94, 53.18, "bir"), (53.18, 53.78, "anısın"), (53.78, 54.12, "sadece"), (54.12, 55.06, "geçen"), (55.06, 56.12, "zamandan")],
    # Chorus 1
    [(56.12, 56.86, "Yalan"), (56.86, 57.34, "bir"), (57.34, 58.44, "masaldı")],
    [(58.44, 59.20, "sonunu"), (59.20, 59.56, "ben"), (59.56, 60.72, "yazdım")],
    [(60.72, 61.36, "Adını"), (61.36, 62.06, "karlı"), (62.06, 62.34, "bir"), (62.34, 62.62, "cama"), (62.62, 63.46, "kazıdım")],
    [(63.46, 64.04, "eridi"), (64.04, 64.50, "gitti")],
    [(64.50, 65.40, "Ne"), (65.40, 65.56, "bir"), (65.56, 66.18, "sitem"), (66.18, 66.54, "var"), (66.54, 67.08, "içimde")],
    [(67.08, 67.38, "ne"), (67.38, 67.58, "bir"), (67.58, 68.72, "kırgınlık")],
    [(68.72, 69.26, "sadece"), (69.26, 70.30, "derin"), (70.30, 70.84, "bir"), (70.84, 72.20, "sessizlik")],
    [(72.20, 75.18, "bitti")],
    # Verse 2
    [(84.38, 85.78, "İşıkları"), (85.78, 86.54, "söndü"), (86.54, 86.80, "bu"), (86.80, 87.10, "koca"), (87.10, 88.06, "şehrin")],
    [(88.06, 88.86, "Herkes"), (88.86, 89.28, "kendi"), (89.28, 90.46, "dünyasında"), (90.46, 91.44, "sürgün")],
    [(91.44, 91.98, "Dün"), (91.98, 92.24, "gece"), (92.24, 93.48, "zihnimde"), (93.48, 93.92, "dönen"), (93.92, 94.62, "o rüya")],
    [(94.62, 96.28, "Gündüzün"), (96.28, 96.88, "tozuna"), (96.88, 97.72, "karıştı"), (97.72, 98.16, "bugün")],
    # Chorus 2 (hand-tuned from Short)
    [(98.16, 98.68, "Yalan"), (98.68, 99.14, "bir"), (99.14, 100.24, "masaldı")],
    [(100.24, 101.02, "sonunu"), (101.02, 101.34, "ben"), (101.34, 102.14, "yazdım")],
    [(102.14, 103.16, "Adını"), (103.16, 103.80, "karlı"), (103.80, 104.10, "bir"), (104.10, 104.38, "cama"), (104.38, 105.22, "kazıdım")],
    [(105.22, 105.78, "eridi"), (105.78, 106.36, "gitti")],
    [(106.36, 107.16, "Ne"), (107.16, 107.30, "bir"), (107.30, 107.96, "sitem"), (107.96, 108.30, "var"), (108.30, 108.84, "içimde")],
    [(108.84, 109.14, "ne"), (109.14, 109.32, "bir"), (109.32, 110.44, "kırgınlık")],
    [(110.44, 111.02, "sadece"), (111.02, 112.10, "derin"), (112.10, 112.62, "bir"), (112.62, 114.14, "sessizlik")],
    [(114.14, 116.88, "bitti")],
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
    # Bolder / more prominent than Short (user note for lyric videos)
    fsize = max(54, int(60 * (1.0 + 0.04 * lvl)))
    fnt = font_path(FONT_LYRIC, fsize)
    tracking = 4
    word_gap = 24

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
    img.alpha_composite(bloom.filter(ImageFilter.GaussianBlur(14 + int(4 * lvl))))

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
    """Bars only — no black plate; punchier amplitude (Short language)."""
    n = len(vals)
    pill_w, pill_h = 820, EQ_H
    pill_x = (W - pill_w) // 2
    eq_y = EQ_Y
    margin_x, margin_y = 12, 4
    usable_w = pill_w - 2 * margin_x
    usable_h = pill_h - 2 * margin_y
    gap = 5
    bar_w = max(8, int((usable_w - gap * (n - 1)) / n))
    total = n * bar_w + (n - 1) * gap
    start_x = pill_x + margin_x + (usable_w - total) // 2
    base_y = eq_y + pill_h - margin_y
    for i, v in enumerate(vals):
        vv = float(min(1.0, v ** 0.75 * 1.25))
        bh = int(12 + vv * (usable_h - 12))
        x0 = start_x + i * (bar_w + gap)
        color = CREAM if i % 3 != 2 else CREAM2
        draw.rounded_rectangle(
            (x0 - 1, base_y - bh - 1, x0 + bar_w + 1, base_y + 1),
            radius=bar_w // 2,
            fill=(18, 14, 12),
        )
        draw.rounded_rectangle(
            (x0, base_y - bh, x0 + bar_w, base_y), radius=bar_w // 2, fill=color
        )

    bar_x0, bar_x1 = 420, W - 420
    draw.line((bar_x0, PROGRESS_Y, bar_x1, PROGRESS_Y), fill=PROGRESS_BG, width=2)
    px = bar_x0 + int((bar_x1 - bar_x0) * progress)
    draw.line((bar_x0, PROGRESS_Y, px, PROGRESS_Y), fill=CREAM, width=2)
    draw.ellipse((px - 5, PROGRESS_Y - 5, px + 5, PROGRESS_Y + 5), fill=CREAM)


def _draw_mouse(d: ImageDraw.ImageDraw, x: int, y: int, press: float = 0.0) -> None:
    s = 1.0 - 0.08 * press
    pts = [
        (x, y),
        (x + int(4 * s), y + int(22 * s)),
        (x + int(10 * s), y + int(18 * s)),
        (x + int(18 * s), y + int(30 * s)),
        (x + int(22 * s), y + int(27 * s)),
        (x + int(12 * s), y + int(14 * s)),
        (x + int(20 * s), y + int(14 * s)),
    ]
    d.polygon(pts, fill=(255, 255, 255, 255))
    d.line(pts + [pts[0]], fill=(20, 20, 20, 255), width=2)


def _paste_icon(layer: Image.Image, icon: Image.Image, cx: int, cy: int, size: int) -> None:
    ic = icon.resize((size, size), Image.Resampling.LANCZOS)
    layer.alpha_composite(ic, (cx - size // 2, cy - size // 2))


def _circle_btn(d: ImageDraw.ImageDraw, cx: int, cy: int, r: int, active: bool, ring) -> None:
    d.ellipse(
        (cx - r, cy - r, cx + r, cy + r),
        fill=(255, 255, 255, 255),
        outline=(225, 225, 225, 255),
        width=2,
    )
    if active:
        d.ellipse((cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5), outline=(*ring, 210), width=3)


def draw_subscribe_cta(img: Image.Image, t: float) -> None:
    """Like / ABONE OL / bell — same language as Short (slightly smaller for 16:9)."""
    cycle = 4.8
    tt = t % cycle
    if tt < 1.6:
        stage, local = 0, tt / 1.6
    elif tt < 3.2:
        stage, local = 1, (tt - 1.6) / 1.6
    else:
        stage, local = 2, (tt - 3.2) / 1.6

    if local < 0.55:
        travel, press = local / 0.55, 0.0
    elif local < 0.85:
        travel, press = 1.0, (local - 0.55) / 0.30
    else:
        travel, press = 1.0, max(0.0, 1.0 - (local - 0.85) / 0.15)

    subscribed = (stage == 1 and local >= 0.55) or stage == 2

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    like_r = int(36 + (5 * press if stage == 0 and local >= 0.55 else 0))
    bell_r = int(36 + (5 * press if stage == 2 and local >= 0.55 else 0))
    sub_scale = 1.0 + (0.06 * press if stage == 1 and local >= 0.55 else 0.0)

    gap = 18
    label = "ABONE OLUNDU" if subscribed else "ABONE OL"
    sub_w = int((300 if subscribed else 260) * sub_scale)
    sub_h = int(60 * sub_scale)
    total_w = like_r * 2 + gap + sub_w + gap + bell_r * 2
    x0 = (W - total_w) // 2
    cy = CTA_Y

    like_cx = x0 + like_r
    sub_x = like_cx + like_r + gap
    sub_y = cy - sub_h // 2
    bell_cx = sub_x + sub_w + gap + bell_r
    targets = [(like_cx, cy), (sub_x + sub_w // 2, cy), (bell_cx, cy)]
    prev = targets[stage - 1] if stage > 0 else (targets[0][0] - 120, targets[0][1] + 40)
    cur = targets[stage]
    mx = int(prev[0] + (cur[0] - prev[0]) * travel)
    my = int(prev[1] + (cur[1] - prev[1]) * travel) + int(10 * (1 - press) if local >= 0.55 else 0)

    _circle_btn(d, like_cx, cy, like_r, stage == 0 and local >= 0.55, LIKE_BLUE)
    thumb = Image.open(ICON_THUMB).convert("RGBA")
    _paste_icon(layer, thumb, like_cx, cy, int(like_r * 1.15))

    if subscribed:
        btn_col = (95, 95, 95, 255)
        d.rounded_rectangle(
            (sub_x + 3, sub_y + 5, sub_x + sub_w + 3, sub_y + sub_h + 5),
            radius=10,
            fill=(0, 0, 0, 70),
        )
    else:
        btn_col = (255, 0, 0, 255)
        d.rounded_rectangle(
            (sub_x + 3, sub_y + 5, sub_x + sub_w + 3, sub_y + sub_h + 5),
            radius=10,
            fill=(0, 0, 0, 90),
        )
    d.rounded_rectangle((sub_x, sub_y, sub_x + sub_w, sub_y + sub_h), radius=10, fill=btn_col)
    fnt = font_path(FONT_DIR / "Inter-Bold.ttf", int(22 * sub_scale if subscribed else 26 * sub_scale))
    bb = d.textbbox((0, 0), label, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text(
        (sub_x + (sub_w - tw) // 2, sub_y + (sub_h - th) // 2 - 2),
        label,
        font=fnt,
        fill=(255, 255, 255, 255),
    )

    _circle_btn(d, bell_cx, cy, bell_r, stage == 2 and local >= 0.55, (70, 70, 70))
    bell = Image.open(ICON_BELL).convert("RGBA")
    _paste_icon(layer, bell, bell_cx, cy, int(bell_r * 1.15))

    _draw_mouse(d, mx + 8, my + 6, press=press if local >= 0.55 else 0.0)
    img.alpha_composite(layer)


def base_landscape() -> Image.Image:
    src = Image.open(COVER).convert("RGB")
    scale = max(W / src.width, H / src.height) * 1.06
    nw, nh = int(src.width * scale), int(src.height * scale)
    img = src.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - W) // 2
    top = max(0, int((nh - H) * 0.22))
    if top + H > nh:
        top = nh - H
    img = img.crop((left, top, left + W, top + H))

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for yy in range(0, 120):
        a = int(80 * (1 - yy / 120))
        d.line([(0, yy), (W, yy)], fill=(0, 0, 0, a))
    fade_start = CREDIT_TOP - 100
    fade_end = min(H, CREDIT_TOP + 280)
    for yy in range(fade_start, fade_end):
        p = (yy - fade_start) / max(1, fade_end - fade_start)
        a = int(min(220, (p**1.15) * 220))
        d.line([(0, yy), (W, yy)], fill=(0, 0, 0, a))
    for yy in range(980, H):
        p = (yy - 980) / max(1, H - 980)
        d.line([(0, yy), (W, yy)], fill=(0, 0, 0, int(120 * p)))
    out = Image.alpha_composite(img.convert("RGBA"), overlay)
    d2 = ImageDraw.Draw(out)

    line_y = CREDIT_TOP + 12
    line_w = 64
    d2.line(
        ((W - line_w) // 2, line_y, (W + line_w) // 2, line_y),
        fill=CREAM,
        width=2,
    )

    artist_fnt = font_path(FONT_SERIF, 38)
    title_fnt = font_path(FONT_OUTFIT, 20)
    credit_fnt = font_path(FONT_OUTFIT, 15)

    def center_spaced(text: str, fnt, y: int, fill, tracking: int) -> None:
        tw = _measure_spaced(d2, text, fnt, tracking)
        _draw_spaced(d2, ((W - tw) // 2, y), text, fnt, fill, tracking)

    center_spaced(ARTIST, artist_fnt, line_y + 18, WHITE, 5)
    center_spaced(TITLE, title_fnt, line_y + 68, CREAM, 8)
    center_spaced(CREDIT, credit_fnt, line_y + 104, MUTED, 3)
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
            draw_subscribe_cta(frame, t)
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
