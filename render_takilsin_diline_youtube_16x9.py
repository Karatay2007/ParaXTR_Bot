#!/usr/bin/env python3
"""Arven Solé — Takılsın Diline YouTube 16:9 (Short look, no DEVAMI YAYINDA)."""

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
ICON_THUMB = Path("/workspace/fonts/icons/thumb_up.png")
ICON_BELL = Path("/workspace/fonts/icons/bell.png")
ART = Path("/opt/cursor/artifacts")
OUT = Path("/workspace/ArvenSole_TakilsinDiline_YOUTUBE_16x9.mp4")

W, H = 1920, 1080
FPS = 24
CREAM = (232, 220, 200)
CREAM2 = (210, 195, 170)
WHITE = (255, 255, 255)
MUTED = (168, 162, 152)
PROGRESS_BG = (55, 50, 45)
LIKE_BLUE = (66, 133, 244)

TITLE = "TAKILSIN DİLİNE"
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

# Full-track cleaned word clocks (Whisper + Short chorus fixes).
LINES: list[list[tuple[float, float, str]]] = [
    # Verse 1
    [(7.54, 8.74, "Karanlık"), (8.74, 9.70, "çöktü"), (9.70, 10.08, "yine"), (10.08, 11.00, "şehre")],
    [(11.20, 11.38, "hiç"), (11.38, 12.00, "lüzum"), (12.00, 12.40, "yok"), (12.40, 13.06, "bahane"), (13.06, 14.40, "aramaya")],
    [(15.00, 16.60, "Hesabımı"), (16.60, 17.72, "veremezsin"), (17.72, 18.10, "bu"), (18.10, 18.96, "aşka")],
    [(19.32, 19.88, "gördün"), (19.88, 20.36, "tabii"), (20.36, 21.34, "durumları"), (21.34, 22.02, "şaştın")],
    [(22.02, 22.44, "Sana"), (22.44, 22.92, "kaç"), (22.92, 23.32, "kere"), (23.32, 23.72, "gel"), (23.72, 24.14, "dedim"), (24.14, 24.90, "ama")],
    [(24.90, 25.48, "sen"), (25.48, 25.88, "hep"), (25.88, 26.70, "kendi"), (26.70, 27.68, "sınırını"), (27.68, 28.38, "aştın")],
    [(28.38, 29.30, "Yazdım"), (29.30, 29.94, "kenara"), (29.94, 30.36, "tek"), (30.36, 30.66, "tek"), (30.66, 31.08, "her"), (31.08, 31.70, "şeyi")],
    [(32.20, 32.60, "artık"), (32.60, 33.52, "çözemesin"), (33.52, 33.94, "bu"), (33.94, 34.58, "bilmeceyi")],
    [(35.28, 35.66, "Gaza"), (35.66, 36.58, "bastım"), (36.58, 37.16, "dikiz"), (37.16, 38.38, "aynasında")],
    [(38.90, 39.18, "gözüm"), (39.18, 39.58, "bile"), (39.58, 40.60, "görmez"), (40.60, 41.38, "geriyi")],
    [(41.98, 42.96, "Telefon"), (42.96, 43.64, "çalıyor"), (43.64, 45.08, "açmıyorum")],
    [(45.80, 46.12, "artık"), (46.12, 47.00, "peşinden"), (47.00, 48.36, "koşmuyorum")],
    [(48.36, 48.96, "Sen"), (48.96, 50.46, "kaybettin"), (50.46, 50.84, "bu"), (50.84, 52.12, "oyunu")],
    [(52.42, 52.82, "ben"), (52.82, 53.74, "yoluma"), (53.74, 54.38, "bakıyorum")],
    # Chorus 1
    [(54.38, 56.08, "Geçti"), (56.08, 56.34, "o"), (56.34, 58.52, "günler")],
    [(59.00, 59.64, "dönmem"), (59.64, 60.38, "geriye")],
    [(61.78, 64.46, "Değmezmişsin"), (64.46, 65.80, "tek"), (65.80, 66.24, "bir"), (66.24, 67.82, "sevgime")],
    [(67.82, 69.50, "Adımı"), (69.50, 71.10, "bir"), (71.10, 72.76, "daha")],
    [(72.76, 73.72, "anma"), (73.72, 74.42, "sakın")],
    [(76.12, 77.02, "Düşmem"), (77.02, 78.16, "artık"), (78.16, 79.28, "senin"), (79.28, 81.02, "tuzağına")],
    # Bridge / verse 2
    [(95.56, 96.88, "Ümitleri"), (96.88, 98.12, "söndürdüm"), (98.12, 98.46, "bu"), (98.46, 98.72, "gece")],
    [(98.72, 99.24, "Adın"), (99.24, 100.14, "dökülmez"), (100.14, 101.04, "artık"), (101.04, 101.54, "tek"), (101.54, 102.28, "kelime")],
    [(102.28, 102.80, "Sen"), (102.80, 103.70, "kendi"), (103.70, 104.26, "yoluna")],
    [(104.32, 104.70, "ben"), (104.70, 105.36, "kendi"), (105.36, 106.02, "yoluma")],
    [(106.16, 106.64, "Bak"), (106.64, 107.36, "bakalım"), (107.36, 107.90, "kim"), (107.90, 108.74, "kalacak"), (108.74, 109.40, "ayakta")],
    # Chorus 2 (hand-tuned from Short)
    [(109.40, 110.80, "Geçti"), (110.80, 111.06, "o"), (111.06, 113.28, "günler")],
    [(113.72, 114.34, "dönmem"), (114.34, 115.40, "geriye")],
    [(116.46, 119.38, "Değmezmişsin"), (119.38, 120.52, "tek"), (120.52, 120.96, "bir"), (120.96, 122.40, "sevgime")],
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
