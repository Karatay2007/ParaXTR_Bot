#!/usr/bin/env python3
"""Arven Solé — Unutamadım Seni YouTube 16:9 (standard lyric UI, no DEVAMI YAYINDA)."""

from __future__ import annotations

import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AUDIO = Path("/workspace/arven_sole_tracks/Unutamadim_Seni.mp3")
COVER = Path("/opt/cursor/artifacts/assets/arven-sole-cover.png")
WAV = Path("/tmp/unutamadim_full.wav")
FONT_DIR = Path("/usr/share/fonts/truetype/macos")
FONT_OUTFIT = Path("/workspace/fonts/Outfit.ttf")
FONT_SERIF = Path("/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf")
FONT_LYRIC = Path("/usr/share/fonts/truetype/noto/NotoSansDisplay-Bold.ttf")
ICON_THUMB = Path("/workspace/fonts/icons/thumb_up.png")
ICON_BELL = Path("/workspace/fonts/icons/bell.png")
ART = Path("/opt/cursor/artifacts")
OUT = Path("/workspace/ArvenSole_UnutamadimSeni_YOUTUBE_16x9.mp4")

W, H = 1920, 1080
FPS = 24
CREAM = (232, 220, 200)
CREAM2 = (210, 195, 170)
WHITE = (255, 255, 255)
MUTED = (168, 162, 152)
PROGRESS_BG = (55, 50, 45)
LIKE_BLUE = (66, 133, 244)

TITLE = "UNUTAMADIM SENİ"
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
# Fixes: içimde / yine özlüyorum; chorus lines split for 16:9 readability.
LINES: list[list[tuple[float, float, str]]] = [
    # Verse 1
    [(30.00, 30.40, "Bu"), (30.40, 30.72, "gece"), (30.72, 31.42, "yine"), (31.42, 32.12, "boş")],
    [(32.12, 33.12, "Sen"), (33.12, 33.80, "yoksun"), (33.80, 34.98, "yanımda")],
    [(34.98, 36.18, "İçim"), (36.18, 37.02, "sızlıyor"), (37.02, 37.76, "yine")],
    [(37.76, 39.90, "Bırakmıyor"), (39.90, 40.60, "beni")],
    [(41.18, 41.94, "Seni"), (41.94, 43.52, "arıyorum")],
    [(43.52, 45.22, "Sesim"), (45.22, 46.54, "gelmiyor")],
    [(46.54, 47.68, "Adın"), (47.68, 48.46, "dilimde"), (48.46, 49.66, "kaldı")],
    [(49.66, 51.40, "Silinmiyor")],
    [(52.02, 54.04, "Gözlerim"), (54.04, 55.10, "yanıyor")],
    [(55.10, 57.04, "İçim"), (57.04, 58.00, "arıyor")],
    [(58.76, 59.56, "Tutamam"), (59.56, 60.48, "artık"), (60.48, 61.02, "yine"), (61.02, 62.82, "kırılıyorum")],
    # Chorus 1
    [(64.82, 66.22, "Unutamadım"), (66.22, 66.88, "seni")],
    [(66.88, 69.12, "unutamadım"), (69.12, 69.80, "yine")],
    [(70.20, 70.90, "Ne"), (70.90, 71.38, "kadar"), (71.38, 71.92, "uzak"), (71.92, 73.00, "olsan")],
    [(73.00, 73.62, "Sen"), (73.62, 74.76, "kaldın"), (74.76, 75.54, "içimde")],
    [(75.54, 77.66, "Unutamadım"), (77.66, 78.38, "seni")],
    [(78.38, 80.68, "unutamadım"), (80.68, 81.50, "yine")],
    [(81.50, 82.80, "Söyleme"), (82.80, 83.36, "bitti"), (83.36, 84.18, "diye")],
    [(84.18, 85.10, "Ben"), (85.10, 86.30, "bitmedim"), (86.30, 86.96, "seni")],
    # Verse 2
    [(98.39, 99.06, "Sabah"), (99.06, 99.38, "oldu"), (99.38, 99.96, "yine")],
    [(99.96, 100.64, "Her"), (100.64, 101.02, "yer"), (101.02, 101.68, "aynı"), (101.68, 102.80, "duruyor")],
    [(103.87, 104.54, "Bir"), (104.54, 104.90, "tek"), (104.90, 105.28, "sen"), (105.28, 105.98, "yoksun")],
    [(105.98, 106.34, "Ben"), (106.34, 106.76, "yine"), (106.76, 108.38, "bekliyorum")],
    [(109.38, 110.64, "Kapıya"), (110.64, 112.02, "bakıyorum")],
    [(112.02, 113.30, "Belki"), (113.30, 115.26, "dönersin")],
    [(115.26, 116.40, "Gelmiyorsun"), (116.40, 117.78, "biliyorum")],
    [(117.78, 118.24, "Yine"), (118.24, 120.20, "özlüyorum")],
    [(120.20, 122.62, "Gözlerim"), (122.62, 123.66, "yanıyor")],
    [(123.66, 125.60, "İçim"), (125.60, 126.60, "arıyor")],
    # Pre-chorus / Chorus 2 (hand-tuned from Short)
    [(127.22, 128.34, "Tutamam"), (128.34, 129.28, "artık"), (129.36, 129.78, "yine"), (129.78, 132.54, "kırılıyorum")],
    [(133.40, 134.98, "Unutamadım"), (134.98, 135.84, "seni")],
    [(136.72, 137.86, "unutamadım"), (137.86, 139.08, "yine")],
    [(139.08, 139.72, "Ne"), (139.72, 140.16, "kadar"), (140.16, 140.80, "uzak"), (140.80, 141.74, "olsan")],
    [(141.74, 142.48, "sen"), (142.48, 143.42, "kaldın"), (143.42, 144.40, "içimde")],
    [(144.40, 146.40, "Unutamadım"), (146.40, 147.52, "seni")],
    [(148.12, 149.40, "unutamadım"), (149.40, 150.38, "yine")],
    [(150.38, 151.52, "Söyleme"), (151.52, 152.20, "bitti"), (152.20, 153.00, "diye")],
    [(153.30, 154.00, "ben"), (154.00, 155.06, "bitmedim"), (155.06, 156.50, "seni")],
    # Bridge
    [(171.92, 172.55, "Söyleme"), (172.55, 173.00, "bitti"), (173.00, 173.70, "diye")],
    [(173.70, 174.20, "Biraz"), (174.20, 175.10, "susayım")],
    [(175.10, 175.55, "Bu"), (175.55, 176.15, "acı"), (176.15, 177.30, "konuşsun")],
    [(177.30, 178.40, "Sonra"), (178.40, 179.50, "adını"), (179.50, 181.70, "haykırayım"), (181.70, 183.22, "yine")],
    # Chorus 3 / outro
    [(187.66, 189.06, "Unutamadım"), (189.06, 189.72, "seni")],
    [(189.72, 191.96, "unutamadım"), (191.96, 192.60, "yine")],
    [(192.60, 193.78, "Ne"), (193.78, 194.20, "kadar"), (194.20, 194.78, "uzak"), (194.78, 195.90, "olsan")],
    [(195.90, 196.50, "Sen"), (196.50, 197.58, "kaldın"), (197.58, 198.40, "içimde")],
    [(198.40, 200.46, "Unutamadım"), (200.46, 201.22, "seni")],
    [(201.22, 203.44, "unutamadım"), (203.44, 204.28, "yine")],
    [(204.28, 205.64, "Söyleme"), (205.64, 206.28, "bitti"), (206.28, 207.04, "diye")],
    [(207.04, 208.02, "Ben"), (208.02, 209.08, "bitmedim"), (209.08, 209.78, "seni")],
    [(214.50, 215.20, "Söyleme"), (215.20, 215.55, "bitti"), (215.55, 215.95, "diye")],
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
    ff_log = Path("/tmp/unutamadim16_ffmpeg.log")
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
