#!/usr/bin/env python3
"""Arven Solé — Aramabeni YouTube Short (latest Short language)."""

from __future__ import annotations

import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AUDIO = Path("/workspace/arven_sole_tracks/Aramabeni.mp3")
COVER = Path("/opt/cursor/artifacts/assets/arven-sole-cover.png")
WAV = Path("/tmp/aramabeni.wav")
FONT_DIR = Path("/usr/share/fonts/truetype/macos")
FONT_OUTFIT = Path("/workspace/fonts/Outfit.ttf")
FONT_SERIF = Path("/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf")
FONT_LYRIC = Path("/usr/share/fonts/truetype/noto/NotoSansDisplay-Bold.ttf")
FONT_BANNER = Path("/workspace/fonts/ArchivoBlack-Regular.ttf")
ICON_THUMB = Path("/workspace/fonts/icons/thumb_up.png")
ICON_BELL = Path("/workspace/fonts/icons/bell.png")
ART = Path("/opt/cursor/artifacts")
OUT_SHORT = Path("/workspace/ArvenSole_Aramabeni_SHORT.mp4")

W, H = 1080, 1920
FPS = 24
CREAM = (232, 220, 200)
CREAM2 = (210, 195, 170)
WHITE = (255, 255, 255)
MUTED = (168, 162, 152)
PROGRESS_BG = (55, 50, 45)
LIKE_BLUE = (66, 133, 244)

TITLE = "ARAMABENİ"
ARTIST = "ARVEN SOLÉ"
CREDIT = "SÖZ · MÜZİK   ARVEN SOLÉ"

BANNER_Y = 250
LYRIC_Y = 780
EQ_Y = 890
EQ_H = 110
CREDIT_TOP = 1220
CTA_Y = 1585
PROGRESS_Y = 1785

# Hottest: Değmezmişsin → Beni arama chorus 2
SHORT_T0 = 68.8
SHORT_T1 = 104.2
WORD_LEAD = 0.05

LINES: list[list[tuple[float, float, str]]] = [
    [(68.98, 69.62, "Dönüp"), (69.62, 69.86, "de"), (69.86, 70.30, "bakmam"), (70.30, 70.66, "artık"), (70.66, 71.62, "geriye")],
    [(71.62, 73.32, "Değmezmişsin"), (73.32, 73.60, "tek"), (73.60, 74.06, "bir"), (74.06, 75.84, "sevgiye")],
    [(75.84, 77.64, "Gecenin"), (77.64, 78.14, "körü"), (78.14, 78.72, "telefon"), (78.72, 80.32, "sessizde")],
    [(80.32, 81.02, "Adın"), (81.02, 81.42, "bile"), (81.42, 81.84, "yok"), (81.84, 82.38, "artık"), (82.38, 83.80, "zihnimde")],
    [(83.80, 84.50, "Gaza"), (84.50, 85.36, "bastım")],
    [(85.36, 86.22, "Geride"), (86.22, 87.08, "kaldın"), (87.08, 87.62, "bu"), (87.62, 88.06, "kez")],
    [(88.06, 88.40, "Ben"), (88.40, 88.96, "tamam"), (88.96, 89.64, "sen"), (89.64, 90.58, "yandın")],
    [(90.58, 90.96, "Beni"), (90.96, 91.80, "arama")],
    [(92.16, 92.84, "Bir"), (92.84, 93.16, "daha"), (93.16, 93.94, "sorma"), (93.94, 94.52, "geçti"), (94.52, 94.80, "o"), (94.80, 95.78, "günler")],
    [(95.78, 96.72, "Boşuna"), (96.72, 97.50, "yorma"), (97.50, 98.24, "ritim"), (98.24, 98.92, "vurur")],
    [(98.92, 99.98, "Kalbim"), (99.98, 100.64, "durur"), (100.64, 101.00, "artık"), (101.00, 101.54, "adın"), (101.54, 101.80, "bile")],
    [(101.80, 102.48, "Beni"), (102.48, 103.62, "unutur")],
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
    pill_w, pill_h = 720, EQ_H
    pill_x = (W - pill_w) // 2
    eq_y = EQ_Y
    margin_x, margin_y = 10, 4
    usable_w = pill_w - 2 * margin_x
    usable_h = pill_h - 2 * margin_y
    gap = 5
    bar_w = max(8, int((usable_w - gap * (n - 1)) / n))
    total = n * bar_w + (n - 1) * gap
    start_x = pill_x + margin_x + (usable_w - total) // 2
    base_y = eq_y + pill_h - margin_y
    for i, v in enumerate(vals):
        vv = float(min(1.0, v ** 0.75 * 1.25))
        bh = int(14 + vv * (usable_h - 14))
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

    bar_x0, bar_x1 = 180, W - 180
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


def draw_subscribe_cta(img: Image.Image, t_local: float) -> None:
    cycle = 4.8
    t = t_local % cycle
    if t < 1.6:
        stage, local = 0, t / 1.6
    elif t < 3.2:
        stage, local = 1, (t - 1.6) / 1.6
    else:
        stage, local = 2, (t - 3.2) / 1.6

    if local < 0.55:
        travel, press = local / 0.55, 0.0
    elif local < 0.85:
        travel, press = 1.0, (local - 0.55) / 0.30
    else:
        travel, press = 1.0, max(0.0, 1.0 - (local - 0.85) / 0.15)

    subscribed = (stage == 1 and local >= 0.55) or stage == 2

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    like_r = int(44 + (6 * press if stage == 0 and local >= 0.55 else 0))
    bell_r = int(44 + (6 * press if stage == 2 and local >= 0.55 else 0))
    sub_scale = 1.0 + (0.06 * press if stage == 1 and local >= 0.55 else 0.0)

    gap = 22
    label = "ABONE OLUNDU" if subscribed else "ABONE OL"
    sub_w = int((350 if subscribed else 300) * sub_scale)
    sub_h = int(72 * sub_scale)
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
    fnt = font_path(FONT_DIR / "Inter-Bold.ttf", int(27 * sub_scale if subscribed else 32 * sub_scale))
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


def draw_top_banner(img: Image.Image, t_local: float = 0.0) -> None:
    bob = math.sin(t_local * 2.2) * 6
    pulse = 0.5 + 0.5 * math.sin(t_local * 3.0)
    scale = 1.0 + 0.04 * pulse

    fnt = font_path(FONT_BANNER, int(52 * scale))
    tracking = 12
    text = "DEVAMI YAYINDA"
    probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    tw = _measure_spaced(probe, text, fnt, tracking)
    thb = probe.textbbox((0, 0), text, font=fnt)
    th = thb[3] - thb[1]
    x = (W - tw) // 2
    y = int(BANNER_Y + 20 + bob)

    cream = (
        min(255, int(245 + 10 * pulse)),
        min(255, int(232 + 8 * pulse)),
        min(255, int(210 + 6 * pulse)),
        255,
    )

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    pad = 28
    for yy in range(y - pad, y + th + pad):
        p = abs((yy - (y + th / 2)) / (th / 2 + pad))
        a = int(70 * max(0.0, 1.0 - p))
        wd.line([(x - 40, yy), (x + tw + 40, yy)], fill=(0, 0, 0, a))
    layer.alpha_composite(wash)

    bloom = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bloom)
    _draw_spaced(bd, (x, y), text, fnt, (*cream[:3], int(110 + 60 * pulse)), tracking)
    layer.alpha_composite(bloom.filter(ImageFilter.GaussianBlur(10 + int(4 * pulse))))

    stroke = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stroke)
    for ox, oy in (
        (-3, 0), (3, 0), (0, -3), (0, 3),
        (-3, -3), (3, 3), (-3, 3), (3, -3),
        (-2, 0), (2, 0), (0, -2), (0, 2),
    ):
        _draw_spaced(sd, (x + ox, y + oy), text, fnt, (0, 0, 0, 230), tracking)
    layer.alpha_composite(stroke)

    fill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fill)
    _draw_spaced(fd, (x, y), text, fnt, cream, tracking)
    layer.alpha_composite(fill)

    ud = ImageDraw.Draw(layer)
    uw = int(tw * (0.48 + 0.16 * pulse))
    ux = x + (tw - uw) // 2
    glyph_bottom = y + thb[3]
    uy = glyph_bottom + 78
    ud.rounded_rectangle((ux, uy, ux + uw, uy + 3), radius=2, fill=(*cream[:3], 190))

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

    audio_clip = Path("/tmp/aramabeni_short_clip.wav")
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
