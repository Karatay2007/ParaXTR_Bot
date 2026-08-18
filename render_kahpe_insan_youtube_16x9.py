#!/usr/bin/env python3
"""Arven Solé — Kahpe İnsan YouTube 16:9 Official Lyric Video (no DEVAMI)."""

from __future__ import annotations

import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AUDIO = Path("/workspace/arven_sole_tracks/Kahpe_Insan.mp3")
COVER = Path("/opt/cursor/artifacts/assets/arven-sole-cover.png")
WAV = Path("/tmp/kahpe.wav")
FONT_DIR = Path("/usr/share/fonts/truetype/macos")
FONT_OUTFIT = Path("/workspace/fonts/Outfit.ttf")
FONT_SERIF = Path("/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf")
FONT_LYRIC = Path("/usr/share/fonts/truetype/noto/NotoSansDisplay-Bold.ttf")
ICON_THUMB = Path("/workspace/fonts/icons/thumb_up.png")
ICON_BELL = Path("/workspace/fonts/icons/bell.png")
ART = Path("/opt/cursor/artifacts")
OUT = Path("/workspace/ArvenSole_KahpeInsan_YOUTUBE_16x9.mp4")

W, H = 1920, 1080
FPS = 24
CREAM = (232, 220, 200)
CREAM2 = (210, 195, 170)
WHITE = (255, 255, 255)
MUTED = (168, 162, 152)
PROGRESS_BG = (55, 50, 45)
LIKE_BLUE = (66, 133, 244)

TITLE = "KAHPE İNSAN"
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

# Full-track cleaned clocks. Fixes: Gülüşün / yüzün / Huy / Gözün / Sırtımdan
LINES: list[list[tuple[float, float, str]]] = [
    # Verse 1
    [(39.94, 41.20, "Dost"), (41.20, 41.88, "sandım"), (41.88, 42.26, "seni"), (42.26, 42.66, "yalan"), (42.66, 43.40, "çıktın")],
    [(43.40, 44.06, "Yüzüme"), (44.06, 44.66, "güldün"), (44.70, 45.46, "sırtımdan"), (45.46, 46.52, "vurdun")],
    [(46.52, 47.20, "Sözün"), (47.20, 47.68, "vardı"), (47.70, 47.94, "iş"), (47.94, 49.20, "tutmadın")],
    [(49.20, 50.00, "Kardeş"), (50.00, 50.52, "dedin"), (50.58, 51.08, "satıp"), (51.08, 51.94, "kaçtın")],
    [(51.94, 52.90, "Yanımda"), (52.90, 53.42, "durdun"), (53.42, 53.96, "işin"), (53.96, 54.78, "varken")],
    [(54.78, 55.32, "İş"), (55.32, 56.00, "bitince"), (56.00, 56.52, "yolun"), (56.52, 57.64, "göründü")],
    [(57.64, 58.30, "Aynı"), (58.30, 59.00, "sofrada"), (59.00, 59.56, "lokma"), (59.56, 60.70, "bölüştük")],
    [(60.70, 61.44, "Kapıda"), (61.44, 62.12, "ismim"), (62.12, 63.20, "silindi")],
    [(63.20, 64.12, "Gülüşün"), (64.12, 64.96, "sahte"), (65.28, 65.70, "elin"), (65.70, 66.22, "soğuk")],
    [(66.22, 66.96, "Ağzın"), (66.96, 67.52, "tatlı"), (67.52, 68.38, "niyetin"), (68.38, 68.96, "bozuk")],
    [(68.96, 69.76, "Bugün"), (69.76, 70.50, "dostsun"), (70.54, 71.22, "yarın"), (71.22, 71.88, "düşman")],
    [(71.88, 72.12, "Bu"), (72.12, 72.64, "huyun"), (72.64, 73.06, "belli"), (73.06, 73.50, "sen"), (73.50, 74.60, "kahpesin")],
    # Chorus 1
    [(74.60, 75.46, "Kahpe"), (75.46, 76.20, "insan")],
    [(76.68, 77.22, "tanıdım"), (77.22, 77.72, "seni")],
    [(77.72, 78.68, "Gözün"), (78.68, 79.14, "güler"), (79.34, 79.60, "için"), (79.60, 80.00, "yer"), (80.00, 80.34, "beni")],
    [(80.34, 81.28, "Kahpe"), (81.28, 81.90, "insan")],
    [(82.24, 82.58, "bırakıp"), (82.58, 83.18, "gittin")],
    [(83.18, 83.52, "Dost"), (83.52, 83.90, "gibi"), (83.90, 84.48, "durdun"), (84.58, 85.36, "ihanet"), (85.36, 85.96, "ettin")],
    [(85.96, 86.82, "Kahpe"), (86.82, 87.46, "insan")],
    [(87.84, 88.64, "utanmadın"), (88.64, 88.82, "mı")],
    [(88.84, 89.52, "Sırtımdan"), (89.52, 90.30, "vurdun"), (90.54, 91.02, "dönüp"), (91.02, 91.62, "bakmadın")],
    [(91.62, 92.54, "Kahpe"), (92.54, 93.12, "insan")],
    [(93.54, 93.88, "yazdım"), (93.88, 94.40, "adını")],
    [(94.40, 95.10, "unutmam"), (95.10, 95.70, "seni")],
    [(96.12, 96.58, "silmem"), (96.58, 97.60, "acını")],
    # Verse 2
    [(118.82, 120.22, "Para"), (120.22, 121.12, "konuşunca"), (121.12, 121.74, "dilin"), (121.74, 122.62, "değişti")],
    [(122.62, 123.46, "İhtiyacın"), (123.46, 124.08, "bitince"), (124.08, 124.66, "adım"), (124.66, 125.48, "düştü")],
    [(125.48, 126.22, "Omzuma"), (126.22, 127.06, "koyduğun"), (127.06, 127.28, "el"), (127.28, 128.14, "yalandı")],
    [(128.14, 128.48, "Ben"), (128.48, 129.36, "inanırken"), (129.36, 129.68, "sen"), (129.68, 130.78, "hesaplandın")],
    [(130.78, 131.14, "Ben"), (131.14, 131.90, "düşünce"), (131.90, 132.46, "sen"), (132.46, 133.58, "yükseldin")],
    [(133.58, 133.98, "Ben"), (133.98, 134.72, "susunca"), (134.72, 135.36, "sen"), (135.36, 136.50, "konuştun")],
    [(136.50, 137.06, "Ayna"), (137.06, 137.72, "tuttum"), (137.72, 138.54, "yüzün"), (138.54, 139.20, "düştü")],
    [(139.20, 139.64, "Aynı"), (139.64, 140.38, "masada"), (140.38, 140.94, "iki"), (140.94, 141.16, "yüz"), (141.16, 142.30, "kaldın")],
    [(142.30, 143.14, "Gülüşün"), (143.14, 143.88, "sahte"), (144.24, 144.66, "elin"), (144.66, 145.20, "soğuk")],
    [(145.20, 146.00, "Ağzın"), (146.00, 146.54, "tatlı"), (146.54, 147.40, "niyetin"), (147.40, 147.98, "bozuk")],
    [(147.98, 148.72, "Bugün"), (148.72, 149.48, "dostun"), (149.48, 150.22, "yarın"), (150.22, 150.86, "düşman")],
    [(150.86, 151.12, "Bu"), (151.12, 151.60, "huyun"), (151.60, 152.08, "belli"), (152.08, 152.50, "sen"), (152.50, 153.66, "kahpesin")],
    # Chorus 2
    [(153.66, 154.54, "Kahpe"), (154.54, 155.24, "insan")],
    [(155.24, 156.24, "Tanıdım"), (156.24, 156.86, "seni")],
    [(156.86, 157.70, "Gözün"), (157.70, 158.14, "güler"), (158.14, 158.62, "için"), (158.62, 159.00, "yer"), (159.00, 159.36, "beni")],
    [(159.36, 160.28, "Kahpe"), (160.28, 160.90, "insan")],
    [(160.90, 161.56, "Bırakıp"), (161.56, 162.20, "gittin")],
    [(162.20, 162.52, "Dost"), (162.52, 162.92, "gibi"), (162.92, 163.50, "durdun"), (163.60, 164.40, "ihanet"), (164.40, 164.98, "ettin")],
    [(164.98, 165.94, "Kahpe"), (165.94, 166.50, "insan")],
    [(166.50, 167.64, "Utanmadın"), (167.64, 167.82, "mı")],
    [(167.84, 168.56, "Sırtımdan"), (168.56, 169.30, "vurdun"), (169.62, 170.02, "dönüp"), (170.02, 170.66, "bakmadın")],
    [(170.66, 171.62, "Kahpe"), (171.62, 172.16, "insan")],
    [(172.16, 172.88, "Yazdım"), (172.88, 173.50, "adını")],
    [(173.50, 174.14, "unutmam"), (174.14, 174.60, "seni")],
    [(174.60, 175.64, "Silmem"), (175.64, 176.60, "acını")],
    # Bridge → Chorus 3
    [(198.82, 199.48, "Kim"), (199.48, 199.84, "dost"), (200.12, 200.28, "kim"), (200.28, 200.94, "düşman")],
    [(200.94, 201.54, "Çizgi"), (201.54, 202.20, "duman")],
    [(202.20, 202.72, "İsim"), (202.72, 203.46, "değişir")],
    [(203.46, 203.84, "Huy"), (203.84, 204.44, "aynı"), (204.44, 204.94, "kalır")],
    [(204.94, 205.44, "elini"), (205.44, 206.18, "sıkarken"), (206.18, 207.06, "aklın"), (207.06, 207.86, "başka")],
    [(207.86, 208.36, "Ben"), (208.36, 209.20, "yanarken"), (209.20, 209.54, "sen"), (209.54, 212.86, "hesapta")],
    [(212.86, 213.76, "Kahpe"), (213.76, 214.50, "insan")],
    [(214.92, 215.50, "tanıdım"), (215.50, 215.98, "seni")],
    [(215.98, 216.94, "Gözün"), (216.94, 217.40, "güler"), (217.40, 217.84, "için"), (217.84, 218.28, "yer"), (218.28, 218.60, "beni")],
    [(218.60, 219.52, "Kahpe"), (219.52, 220.14, "insan")],
    [(220.44, 220.84, "bırakıp"), (220.84, 221.44, "gittin")],
    [(221.44, 221.76, "Dost"), (221.76, 222.16, "gibi"), (222.16, 222.74, "durdun"), (222.74, 223.64, "ihanet"), (223.64, 224.24, "ettin")],
    [(224.24, 225.16, "Kahpe"), (225.16, 225.74, "insan")],
    [(226.02, 226.90, "utanmadın"), (226.90, 227.08, "mı")],
    [(227.08, 227.80, "Sırtımdan"), (227.80, 228.58, "vurdun"), (228.86, 229.28, "dönüp"), (229.28, 229.90, "bakmadın")],
    [(229.90, 230.86, "Kahpe"), (230.86, 231.40, "insan")],
    [(231.72, 232.14, "yazdım"), (232.14, 232.74, "adını")],
    [(232.74, 233.36, "Unutmam"), (233.36, 233.92, "seni")],
    [(234.00, 234.84, "silmem"), (234.84, 235.68, "acını")],
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
    ff_log = Path("/tmp/kahpe16_ffmpeg.log")
    ff_err = open(ff_log, "w")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=ff_err)
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
        code = proc.wait()
        ff_err.close()
    if code != 0:
        err = ff_log.read_text(errors="replace")[-2500:]
        print(err, file=sys.stderr)
        raise RuntimeError(f"ffmpeg failed {code}")
    dest = ART / OUT.name
    dest.write_bytes(OUT.read_bytes())
    print(f"Done {OUT} ({OUT.stat().st_size / 1e6:.1f}MB)", flush=True)


if __name__ == "__main__":
    ART.mkdir(parents=True, exist_ok=True)
    render()
