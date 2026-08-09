#!/usr/bin/env python3
"""Arven Solé — Kahpe İnsan YouTube Short (poster style: yellow title, white dots, timer).

Matches CapCut/list cover look: slanted yellow song name, white-dot EQ,
artist, big MM:SS, red capsule progress. No DEVAMI YAYINDA. No kinetic lyrics.
"""

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
FONT_TITLE = Path("/workspace/fonts/Anton-Regular.ttf")
FONT_ARTIST = Path("/workspace/fonts/Outfit.ttf")
FONT_TIMER = Path("/workspace/fonts/ArchivoBlack-Regular.ttf")
ART = Path("/opt/cursor/artifacts")
OUT = Path("/workspace/ArvenSole_KahpeInsan_YOUTUBE_SHORT.mp4")

W, H = 1080, 1920
FPS = 24

# Same can-alıcı cut: bridge → final chorus
SHORT_T0 = 198.5
SHORT_T1 = 236.2

YELLOW = (255, 214, 0)
YELLOW_SHADOW = (0, 0, 0)
WHITE = (255, 255, 255)
DOT = (245, 245, 245)
RED_BAR = (220, 40, 40)
ARTIST = "ARVEN SOLÉ"
SONG = "Kahpe İnsan"  # title-case slanted yellow, as in reference


def font_path(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


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


def band_energies(chunk: np.ndarray, n: int = 18) -> np.ndarray:
    if len(chunk) < 64:
        return np.zeros(n, dtype=np.float32)
    window = np.hanning(len(chunk))
    spec = np.abs(np.fft.rfft(chunk * window))
    freqs = np.linspace(0, 1, len(spec))
    edges = np.logspace(math.log10(0.02), math.log10(1.0), n + 1)
    vals = np.zeros(n, dtype=np.float32)
    for i in range(n):
        mask = (freqs >= edges[i]) & (freqs < edges[i + 1])
        if mask.any():
            vals[i] = float(spec[mask].mean())
    peak = vals.max()
    if peak > 1e-6:
        vals = vals / peak
    return 0.15 + 0.85 * np.power(np.clip(vals, 0, 1), 0.55)


def base_vertical() -> Image.Image:
    img = Image.open(COVER).convert("RGB")
    scale = max(W / img.width, H / img.height) * 1.08
    nw, nh = int(img.width * scale), int(img.height * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - W) // 2
    top = max(0, int((nh - H) * 0.15))
    if top + H > nh:
        top = nh - H
    img = img.crop((left, top, left + W, top + H)).convert("RGBA")

    # Soft bottom fade so timer/bar read clean
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for yy in range(1100, H):
        p = (yy - 1100) / max(1, H - 1100)
        d.line([(0, yy), (W, yy)], fill=(0, 0, 0, int(min(210, p**1.2 * 210))))
    return Image.alpha_composite(img, overlay)


def draw_yellow_title(img: Image.Image, t_local: float) -> None:
    """Slanted yellow song name — same zone as reference 'sarı' title."""
    bob = math.sin(t_local * 2.0) * 4
    pulse = 0.5 + 0.5 * math.sin(t_local * 2.6)
    size = int(118 + 4 * pulse)
    fnt = font_path(FONT_TITLE, size)

    # Render text on transparent layer then rotate
    probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    bb = probe.textbbox((0, 0), SONG, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pad = 40
    layer = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)

    # Hard black outline
    ox, oy = pad - bb[0], pad - bb[1]
    for dx, dy in (
        (-4, 0), (4, 0), (0, -4), (0, 4),
        (-3, -3), (3, 3), (-3, 3), (3, -3),
        (-2, 0), (2, 0), (0, -2), (0, 2),
    ):
        ld.text((ox + dx, oy + dy), SONG, font=fnt, fill=(*YELLOW_SHADOW, 255))
    ld.text((ox, oy), SONG, font=fnt, fill=(*YELLOW, 255))

    # Soft yellow bloom
    bloom = layer.copy().filter(ImageFilter.GaussianBlur(8))
    # tint bloom
    bloom_arr = np.array(bloom)
    bloom_arr[..., 0] = np.minimum(255, bloom_arr[..., 0] + 40)
    bloom_arr[..., 1] = np.minimum(255, bloom_arr[..., 1] + 20)
    bloom_arr[..., 2] = (bloom_arr[..., 2] * 0.3).astype(np.uint8)
    bloom = Image.fromarray(bloom_arr, "RGBA")

    angled = Image.alpha_composite(
        Image.new("RGBA", layer.size, (0, 0, 0, 0)), bloom
    )
    angled = Image.alpha_composite(angled, layer)
    angled = angled.rotate(8, resample=Image.Resampling.BICUBIC, expand=True)

    # Place in upper-middle — the "sarı nokta / yellow title" zone from reference
    cx = (W - angled.width) // 2 + 10
    cy = int(620 + bob) - angled.height // 2
    img.alpha_composite(angled, (cx, cy))


def draw_dot_eq(img: Image.Image, vals: np.ndarray) -> None:
    """White dots under the yellow title (reference visualizer)."""
    n = len(vals)
    d = ImageDraw.Draw(img)
    gap = 28
    total = (n - 1) * gap
    x0 = (W - total) // 2
    y = 780
    for i, v in enumerate(vals):
        r = int(5 + float(v) * 10)
        cx = x0 + i * gap
        # vertical bob per band
        cy = y - int(float(v) * 18)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*DOT, 245))


def draw_artist(img: Image.Image) -> None:
    d = ImageDraw.Draw(img)
    fnt = font_path(FONT_ARTIST, 36)
    bb = d.textbbox((0, 0), ARTIST, font=fnt)
    tw = bb[2] - bb[0]
    x = (W - tw) // 2
    y = 860
    # subtle stroke
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        d.text((x + dx, y + dy), ARTIST, font=fnt, fill=(0, 0, 0, 220))
    d.text((x, y), ARTIST, font=fnt, fill=(*WHITE, 255))


def draw_timer_and_bar(img: Image.Image, progress: float, clip_dur: float) -> None:
    """Big MM:SS + red capsule with scrubber (yellow/white dot on bar)."""
    d = ImageDraw.Draw(img)
    remain = max(0.0, clip_dur * (1.0 - progress))
    # Show remaining like the reference big clock feel; also works as elapsed look
    # Reference shows total length style "00:37" — use remaining countdown for energy
    mm = int(remain) // 60
    ss = int(remain) % 60
    text = f"{mm:02d}:{ss:02d}"

    fnt = font_path(FONT_TIMER, 92)
    bb = d.textbbox((0, 0), text, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x = (W - tw) // 2
    y = 1480
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2)):
        d.text((x + dx, y + dy), text, font=fnt, fill=(0, 0, 0, 230))
    d.text((x, y), text, font=fnt, fill=(*WHITE, 255))

    # Red capsule progress under timer
    bar_w, bar_h = 420, 28
    bx = (W - bar_w) // 2
    by = y + th + 28
    d.rounded_rectangle((bx, by, bx + bar_w, by + bar_h), radius=bar_h // 2, fill=(*RED_BAR, 255))
    # filled portion slightly brighter
    fill_w = int(bar_w * max(0.02, min(1.0, progress)))
    if fill_w > 8:
        d.rounded_rectangle(
            (bx, by, bx + fill_w, by + bar_h),
            radius=bar_h // 2,
            fill=(255, 70, 70, 255),
        )
    # Scrubber dot — the accent "nokta" on the red bar
    px = bx + fill_w
    pr = 16
    d.ellipse((px - pr, by + bar_h // 2 - pr, px + pr, by + bar_h // 2 + pr), fill=(*YELLOW, 255))
    d.ellipse(
        (px - pr + 3, by + bar_h // 2 - pr + 3, px + pr - 3, by + bar_h // 2 + pr - 3),
        fill=(*WHITE, 255),
    )


def render() -> None:
    samples, rate = ensure_wav()
    duration = len(samples) / rate
    t0, t1 = SHORT_T0, min(SHORT_T1, duration)
    clip_dur = t1 - t0
    n_frames = int(round(clip_dur * FPS))
    print(f"Rendering YT poster SHORT {t0:.1f}-{t1:.1f}s ({n_frames}f)", flush=True)

    audio_clip = Path("/tmp/kahpe_yt_poster_clip.wav")
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
    n_dots = 18
    smooth = np.zeros(n_dots, dtype=np.float32)
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(audio_clip),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        str(OUT),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    start = int(t0 * rate)
    peak_rms = 1e-6
    try:
        for fi in range(n_frames):
            t_local = fi / FPS
            chunk = samples[start + fi * hop : start + fi * hop + hop * 2]
            rms = float(np.sqrt(np.mean(np.square(chunk)))) if len(chunk) else 0.0
            peak_rms = max(peak_rms * 0.995, rms, 1e-6)
            smooth = 0.55 * smooth + 0.45 * band_energies(chunk, n_dots)
            frame = base.copy()
            draw_yellow_title(frame, t_local)
            draw_dot_eq(frame, smooth)
            draw_artist(frame)
            draw_timer_and_bar(frame, t_local / max(0.001, clip_dur), clip_dur)
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
    dest = ART / OUT.name
    dest.write_bytes(OUT.read_bytes())
    print(f"Done {OUT} ({OUT.stat().st_size / 1e6:.1f}MB)", flush=True)


if __name__ == "__main__":
    ART.mkdir(parents=True, exist_ok=True)
    render()
