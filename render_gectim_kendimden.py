#!/usr/bin/env python3
"""Render Arven Solé — Geçtim Kendimden: Shorts (9:16) + YouTube 16:9."""

from __future__ import annotations

import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AUDIO = Path("/home/ubuntu/.cursor/projects/workspace/uploads/Ge_tim_Kendimden_54cb.mp3")
COVER = Path("/opt/cursor/artifacts/assets/arven-sole-cover.png")
WAV = Path("/tmp/gectim_render.wav")
FONT_DIR = Path("/usr/share/fonts/truetype/macos")
ART = Path("/opt/cursor/artifacts")
OUT_SHORT = Path("/workspace/ArvenSole_GectimKendimden_SHORT.mp4")
OUT_16X9 = Path("/workspace/ArvenSole_GectimKendimden_YOUTUBE_16x9.mp4")
OUT_MP3 = Path("/workspace/ArvenSole_GectimKendimden_FULL.mp3")

FPS = 24
CREAM = (232, 220, 200)
CREAM2 = (210, 195, 170)
WHITE = (255, 255, 255)
MUTED = (168, 162, 152)
PROGRESS_BG = (55, 50, 45)

TITLE = "Geçtim Kendimden"
ARTIST = "Arven Solé"
CREDIT = "Söz-Müzik: Arven Solé"

# Whisper-synced cues (cleaned)
LYRICS: list[tuple[float, float, str]] = [
    (30.00, 33.50, "Geceler uzuyor yine içimde"),
    (33.50, 37.00, "Adın dönüyor durmadan dilimde"),
    (37.00, 40.50, "Sustum sandım, bitti sandım"),
    (40.50, 44.50, "Ama kalbim hâlâ senin peşinde"),
    (44.50, 46.80, "Nefesim daralıyor her an"),
    (46.80, 49.50, "Seni düşününce hızlanıyor kan"),
    # Chorus 1
    (49.74, 52.80, "Geçtim kendimden"),
    (52.80, 55.80, "Geçemedim senden"),
    (55.80, 58.50, "Yandı içim"),
    (58.50, 61.10, "Sönmedi ateşin"),
    (63.42, 66.50, "Geçtim kendimden"),
    (66.50, 69.50, "Geçemedim senden"),
    (69.50, 72.20, "Kalp çarpıyor"),
    (72.20, 75.24, "Her yerdesin"),
    (76.24, 78.80, "Bağırıyorum"),
    (78.80, 81.24, "Duymuyor musun?"),
    (81.24, 82.40, "Bu gece yine sensin"),
    (82.52, 85.50, "Geçtim kendimden"),
    (85.50, 88.20, "Geçemedim senden"),
    (88.20, 91.26, "Bitti sandım, bitmedin"),
    # Verse 2
    (103.48, 106.50, "Sokaklar boş ama sen dolusun"),
    (106.50, 109.26, "Her ışıkta bir gölgen kalıyor"),
    (110.26, 113.20, "Kaçtım, uzaklaştım, unuttum dedim"),
    (113.20, 116.42, "Dönünce yine sen çıkıyorsun"),
    (116.42, 119.50, "Nefesim daralıyor her an"),
    (119.50, 122.86, "Seni düşününce hızlanıyor kan"),
    # Chorus 2
    (124.26, 127.30, "Geçtim kendimden"),
    (127.30, 130.30, "Geçemedim senden"),
    (130.30, 132.80, "Yandı içim"),
    (132.80, 135.52, "Sönmedi ateşin"),
    (137.74, 140.80, "Geçtim kendimden"),
    (140.80, 143.80, "Geçemedim senden"),
    (143.80, 146.50, "Kalp çarpıyor"),
    (146.50, 149.52, "Her yerdesin"),
    (150.46, 153.00, "Bağırıyorum"),
    (153.00, 155.88, "Duymuyor musun?"),
    (155.88, 156.80, "Bu gece yine sensin"),
    (156.88, 160.00, "Geçtim kendimden"),
    (160.00, 162.80, "Geçemedim senden"),
    (162.80, 165.20, "Bitti sandım, bitmedin"),
    # Bridge
    (165.42, 168.50, "Bir an sus, bir an bağır"),
    (168.50, 172.00, "İçimde fırtına kopuyor"),
    (172.00, 175.20, "Ne kadar kaçsam da senden"),
    (175.20, 178.38, "Yine sana çarpıyorum"),
    # Chorus 3
    (179.38, 182.50, "Geçtim kendimden"),
    (182.50, 185.50, "Geçemedim senden"),
    (185.50, 188.00, "Yandı içim"),
    (188.00, 190.46, "Sönmedi ateşin"),
    (192.60, 195.70, "Geçtim kendimden"),
    (195.70, 198.70, "Geçemedim senden"),
    (198.70, 201.20, "Kalp çarpıyor"),
    (201.20, 203.64, "Her yerdesin"),
]

SHORT_T0 = 49.5
SHORT_T1 = 91.5


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


def draw_lyrics(img: Image.Image, t: float, w: int, h: int, lyric_y: int, size: int = 44) -> None:
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
    f_cur = font("Inter-Bold.ttf", size)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    td = ImageDraw.Draw(layer)
    bbox = td.textbbox((0, 0), cur, font=f_cur)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (w - tw) // 2
    y = lyric_y
    td.text((x + 2, y + 3), cur, font=f_cur, fill=(0, 0, 0, int(180 * alpha)))
    td.text((x, y), cur, font=f_cur, fill=(255, 255, 255, int(255 * alpha)))
    td.line((x - 6, y + th + 10, x + tw + 6, y + th + 10), fill=(*CREAM, int(200 * alpha)), width=2)
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
    d2.text((rx, 320), ARTIST, font=font("Inter-Bold.ttf", 44), fill=WHITE)
    d2.text((rx, 380), TITLE, font=font("Inter-SemiBold.ttf", 28), fill=CREAM)
    d2.text((rx, 425), CREDIT, font=font("Inter-Regular.ttf", 20), fill=MUTED)
    d2.line((rx, 300, rx + 160, 300), fill=CREAM, width=3)
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
            draw_lyrics(frame, t, w, h, lyric_y, lyric_size)
            d = ImageDraw.Draw(frame)
            if t0 > 0.5:
                progress = (t - t0) / max(0.001, t1 - t0)
            else:
                progress = t / duration
            draw_eq(d, smooth, progress, w, pill_w, pill_h, eq_y, progress_y)
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
    dest = ART / out_path.name
    dest.write_bytes(out_path.read_bytes())
    print(f"Done {out_path} ({out_path.stat().st_size/1e6:.1f}MB)", flush=True)


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    OUT_MP3.write_bytes(AUDIO.read_bytes())
    # Shorts — nakarat
    render(
        OUT_SHORT, 1080, 1920, base_vertical(),
        SHORT_T0, SHORT_T1,
        lyric_y=1185, eq_y=1280, pill_w=760, pill_h=100, progress_y=1740, lyric_size=44,
    )
    # Long 16:9
    render(
        OUT_16X9, 1920, 1080, base_landscape(),
        0.0, None,
        lyric_y=780, eq_y=860, pill_w=1100, pill_h=78, progress_y=1040, lyric_size=48,
    )
    (ART / OUT_MP3.name).write_bytes(OUT_MP3.read_bytes())
    print("All done.")


if __name__ == "__main__":
    main()
