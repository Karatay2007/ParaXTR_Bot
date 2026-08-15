#!/usr/bin/env python3
"""Teninde Kal — Instagram Reels + YouTube Shorts quote variants.

Same poem / chorus family as TikTok, but intentionally different so the three
uploads are not near-duplicates for the algorithm:

  TikTok  (existing): centered Cormorant + Like/ABONE/Bell mouse CTA
  Instagram: left mural text, warmer grade, TAKİP ET CTA, different bed order + cut
  YouTube Shorts: kinetic line reveal, top credit, pulse ABONE, different bed + cut
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AUDIO = Path("/workspace/arven_sole_tracks/Teninde_Kal.mp3")
ART = Path("/opt/cursor/artifacts")
STOCK = Path("/tmp/teninde_quote")
CEMAL_SRC = Path("/opt/cursor/artifacts/assets/cemal_sureya_stencil_v2.png")
CEMAL_RGBA = STOCK / "cemal_rgba_v2.png"
FONT_QUOTE = Path("/workspace/fonts/CormorantGaramond-SemiBoldItalic.ttf")
FONT_INTRO = Path("/workspace/fonts/CormorantGaramond-SemiBold.ttf")
if not FONT_QUOTE.exists():
    FONT_QUOTE = Path("/workspace/fonts/Caveat-Bold.ttf")
    FONT_INTRO = FONT_QUOTE
FONT_DIR = Path("/usr/share/fonts/truetype/macos")

W, H = 1080, 1920
FPS = 24

INTRO_LINES = ["Cemal Süreya’nın dediği gibi;"]
QUOTE_LINES = [
    "“Seni, senin bile",
    "haberinin olmadığı şeylerden dolayı",
    "seviyorum,",
    "sen boşuna saçlarını",
    "düzeltiyorsun…”",
]

# Platform configs — distinct cut / bed / grade / layout / CTA
PLATFORMS = {
    "ig": {
        "out": Path("/workspace/ArvenSole_TenindeKal_REELS_QUOTE.mp4"),
        "work": Path("/tmp/teninde_quote_ig"),
        "t0": 119.2,
        "t1": 151.0,
        "grade": "eq=brightness=0.14:saturation=1.12:contrast=1.00,vignette=PI/16",
        "fade": 0.70,
        "segments": [
            (STOCK / "45856.mp4", 0.8, 7.5),   # couple golden — open intimate
            (STOCK / "4841.mp4", 0.6, 6.5),
            (STOCK / "4624.mp4", 1.2, 7.0),
            (STOCK / "4511.mp4", 0.4, 5.0),
            (STOCK / "4840.mp4", 2.0, 7.0),     # sunset later (TikTok opens on this)
            (STOCK / "45857.mp4", 0.5, 4.0),
        ],
        "layout": "left",
        "cta": "follow",
        "cta_y": 1680,
        "reveal": "soft",
    },
    "yt": {
        "out": Path("/workspace/ArvenSole_TenindeKal_SHORTS_QUOTE.mp4"),
        "work": Path("/tmp/teninde_quote_yt"),
        "t0": 122.4,
        "t1": 156.0,
        "grade": "eq=brightness=0.08:saturation=1.00:contrast=1.06,vignette=PI/11",
        "fade": 0.45,
        "segments": [
            (STOCK / "4511.mp4", 0.3, 6.0),
            (STOCK / "4840.mp4", 0.5, 7.0),
            (STOCK / "45857.mp4", 1.0, 4.5),
            (STOCK / "4624.mp4", 0.5, 7.5),
            (STOCK / "45856.mp4", 1.5, 6.5),
            (STOCK / "4841.mp4", 1.0, 6.0),
        ],
        "layout": "center",
        "cta": "subscribe",
        "cta_y": 1600,
        "reveal": "kinetic",
    },
}


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def ensure_cemal() -> Image.Image:
    if CEMAL_RGBA.exists():
        return Image.open(CEMAL_RGBA).convert("RGBA")
    src = CEMAL_SRC if CEMAL_SRC.exists() else Path("/opt/cursor/artifacts/assets/cemal_sureya_stencil.png")
    im = Image.open(src).convert("RGBA")
    arr = np.array(im)
    lum = arr[:, :, :3].astype(np.float32).mean(axis=2)
    alpha = np.where(lum > 200, 0, 255).astype(np.uint8)
    out = np.zeros_like(arr)
    out[alpha > 0, 0:3] = 12
    out[:, :, 3] = alpha
    ys, xs = np.where(alpha > 0)
    cut = out[max(0, ys.min() - 2) : ys.max() + 3, max(0, xs.min() - 2) : xs.max() + 3]
    Image.fromarray(cut).save(CEMAL_RGBA)
    return Image.fromarray(cut)


def to_vertical(src: Path, t0: float, dur: float, dest: Path, grade: str) -> None:
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},setsar=1,{grade}"
    )
    subprocess.check_call(
        [
            "ffmpeg", "-y",
            "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}",
            "-i", str(src),
            "-vf", vf,
            "-r", str(FPS),
            "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
            str(dest),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def concat_xfade(paths: list[Path], durs: list[float], dest: Path, fade: float) -> float:
    if len(paths) == 1:
        dest.write_bytes(paths[0].read_bytes())
        return durs[0]
    inputs: list[str] = []
    for p in paths:
        inputs.extend(["-i", str(p)])
    parts = []
    current = "[0:v]"
    total = durs[0]
    for i in range(1, len(paths)):
        offset = sum(durs[:i]) - fade * i
        out = f"[v{i}]" if i < len(paths) - 1 else "[vout]"
        parts.append(
            f"{current}[{i}:v]xfade=transition=fade:duration={fade}:offset={offset:.3f}{out}"
        )
        current = out
        total = total + durs[i] - fade
    fc = ";".join(parts)
    subprocess.check_call(
        [
            "ffmpeg", "-y", *inputs,
            "-filter_complex", fc,
            "-map", "[vout]",
            "-r", str(FPS),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
            str(dest),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return total


def _draw_ink_line(
    layer: Image.Image,
    x: int,
    y: int,
    text: str,
    fnt: ImageFont.FreeTypeFont,
    ink=(255, 252, 245, 255),
) -> int:
    d = ImageDraw.Draw(layer)
    bb = d.textbbox((0, 0), text, font=fnt)
    th = bb[3] - bb[1]
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    for ox, oy in ((0, 4), (0, 7), (3, 5), (-3, 5), (0, 10)):
        sd.text((x + ox, y + oy), text, font=fnt, fill=(0, 0, 0, 160))
    for ox, oy in (
        (-6, 0), (6, 0), (0, -6), (0, 6),
        (-5, -5), (5, 5), (-5, 5), (5, -5),
    ):
        sd.text((x + ox, y + oy), text, font=fnt, fill=(0, 0, 0, 110))
    layer.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(5)))
    dd = ImageDraw.Draw(layer)
    for ox, oy in (
        (-3, 0), (3, 0), (0, -3), (0, 3),
        (-2, -2), (2, 2), (-2, 2), (2, -2),
    ):
        dd.text((x + ox, y + oy), text, font=fnt, fill=(0, 0, 0, 230))
    dd.text((x, y), text, font=fnt, fill=ink)
    return th


def make_quote_left(cemal: Image.Image, cta_y: int) -> Image.Image:
    """IG mural: left-aligned stack, Cemal bottom-right of text block."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    intro_fnt = _font(FONT_INTRO, 34)
    quote_fnt = _font(FONT_QUOTE, 50)
    d = ImageDraw.Draw(layer)

    tx, y = 72, 220
    for line in INTRO_LINES:
        y += _draw_ink_line(layer, tx, y, line, intro_fnt) + 6
    y += 18
    for line in QUOTE_LINES:
        y += _draw_ink_line(layer, tx, y, line, quote_fnt) + 12

    cw = 280
    ch = int(cemal.height * (cw / max(1, cemal.width)))
    cemal_r = _cut_cemal(cemal, cw, ch)
    cx = W - cw - 48
    cy = min(y + 20, cta_y - ch - 100)
    layer.alpha_composite(cemal_r, (cx, cy))

    # small IG handle
    handle = "@arven.sole"
    hf = _font(FONT_DIR / "Inter-SemiBold.ttf", 26)
    bb = d.textbbox((0, 0), handle, font=hf)
    hx = 72
    hy = 120
    d.text((hx + 1, hy + 1), handle, font=hf, fill=(0, 0, 0, 140))
    d.text((hx, hy), handle, font=hf, fill=(255, 252, 245, 230))
    return layer


def make_quote_center_static(cemal: Image.Image, cta_y: int) -> Image.Image:
    """Full centered stack (used as base; kinetic reveals per-line layers)."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    intro_fnt = _font(FONT_INTRO, 36)
    quote_fnt = _font(FONT_QUOTE, 54)
    dprobe = ImageDraw.Draw(layer)

    def tw(text, fnt):
        bb = dprobe.textbbox((0, 0), text, font=fnt)
        return bb[2] - bb[0], bb[3] - bb[1]

    lines: list[tuple[str, ImageFont.FreeTypeFont, int]] = []
    for line in INTRO_LINES:
        lines.append((line, intro_fnt, 8))
    lines.append(("", intro_fnt, 18))
    for line in QUOTE_LINES:
        lines.append((line, quote_fnt, 14))

    cw = 290
    ch = int(cemal.height * (cw / max(1, cemal.width)))
    text_h = 0
    for text, fnt, pad in lines:
        if not text:
            text_h += pad
            continue
        text_h += tw(text, fnt)[1] + pad
    block_h = text_h + 52 + ch
    y = max(160, ((cta_y - 110) - block_h) // 2)

    for text, fnt, pad in lines:
        if not text:
            y += pad
            continue
        w, _ = tw(text, fnt)
        y += _draw_ink_line(layer, (W - w) // 2, y, text, fnt) + pad

    cemal_r = _cut_cemal(cemal, cw, ch)
    layer.alpha_composite(cemal_r, ((W - cw) // 2, y + 40))
    return layer


def make_yt_line_layers(cemal: Image.Image, cta_y: int) -> list[Image.Image]:
    """One layer per text line + final Cemal layer for kinetic reveal."""
    intro_fnt = _font(FONT_INTRO, 36)
    quote_fnt = _font(FONT_QUOTE, 54)
    probe = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dprobe = ImageDraw.Draw(probe)

    def tw(text, fnt):
        bb = dprobe.textbbox((0, 0), text, font=fnt)
        return bb[2] - bb[0], bb[3] - bb[1]

    items: list[tuple[str, ImageFont.FreeTypeFont]] = []
    for line in INTRO_LINES:
        items.append((line, intro_fnt))
    for line in QUOTE_LINES:
        items.append((line, quote_fnt))

    cw = 290
    ch = int(cemal.height * (cw / max(1, cemal.width)))
    gaps = [10] + [14] * (len(items) - 1)
    text_h = sum(tw(t, f)[1] + g for (t, f), g in zip(items, gaps))
    y0 = max(200, ((cta_y - 110) - (text_h + 52 + ch)) // 2)

    # top credit (always on)
    credit = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(credit)
    cf = _font(FONT_DIR / "Inter-Bold.ttf", 28)
    label = "ARVEN SOLÉ  ·  TENINDE KAL"
    bb = cd.textbbox((0, 0), label, font=cf)
    lx = (W - (bb[2] - bb[0])) // 2
    cd.text((lx + 1, 96), label, font=cf, fill=(0, 0, 0, 160))
    cd.text((lx, 95), label, font=cf, fill=(255, 252, 245, 235))

    layers: list[Image.Image] = [credit]
    y = y0
    for i, ((text, fnt), gap) in enumerate(zip(items, gaps)):
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        w, th = tw(text, fnt)
        _draw_ink_line(L, (W - w) // 2, y, text, fnt)
        layers.append(L)
        y += th + gap

    cemal_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cemal_layer.alpha_composite(_cut_cemal(cemal, cw, ch), ((W - cw) // 2, y + 36))
    layers.append(cemal_layer)
    return layers


def _cut_cemal(cemal: Image.Image, cw: int, ch: int) -> Image.Image:
    cemal_r = cemal.resize((cw, ch), Image.Resampling.LANCZOS)
    ca = np.array(cemal_r)
    lum = ca[:, :, :3].astype(np.float32).mean(axis=2)
    alpha = ca[:, :, 3].astype(np.float32)
    keep = (alpha > 40) & (lum < 160)
    out = np.zeros_like(ca)
    out[keep, 0:3] = 12
    out[keep, 3] = 255
    a_img = Image.fromarray(out[:, :, 3]).filter(ImageFilter.GaussianBlur(1.2))
    out[:, :, 3] = np.array(a_img)
    return Image.fromarray(out)


def draw_follow_cta(img: Image.Image, t_local: float, cta_y: int) -> None:
    """Instagram-style TAKİP ET pulse — no YouTube mouse UI."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pulse = 0.5 + 0.5 * abs(((t_local * 0.9) % 2) - 1)
    followed = (int(t_local / 3.2) % 2) == 1 and (t_local % 3.2) > 1.4
    label = "TAKİP EDİLİYOR" if followed else "TAKİP ET"
    scale = 1.0 + 0.04 * pulse * (0 if followed else 1)
    bw = int((300 if followed else 260) * scale)
    bh = int(64 * scale)
    x0 = (W - bw) // 2
    y0 = cta_y - bh // 2
    if followed:
        col = (55, 55, 55, 240)
    else:
        # IG-ish warm coral/magenta gradient approximation
        col = (225, 48, 108, 255)
    d.rounded_rectangle((x0 + 3, y0 + 5, x0 + bw + 3, y0 + bh + 5), radius=14, fill=(0, 0, 0, 80))
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=14, fill=col)
    fnt = _font(FONT_DIR / "Inter-Bold.ttf", int(26 * scale))
    bb = d.textbbox((0, 0), label, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text((x0 + (bw - tw) // 2, y0 + (bh - th) // 2 - 2), label, font=fnt, fill=(255, 255, 255, 255))
    img.alpha_composite(layer)


def draw_subscribe_pulse(img: Image.Image, t_local: float, cta_y: int) -> None:
    """YouTube Shorts: single pulsing ABONE OL (no like/bell mouse walk)."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cycle = 3.6
    t = t_local % cycle
    subscribed = t > 1.5
    pulse = 0.0 if subscribed else max(0.0, 1.0 - abs(t - 0.75) / 0.75)
    label = "ABONE OLUNDU" if subscribed else "ABONE OL"
    scale = 1.0 + 0.08 * pulse
    bw = int((340 if subscribed else 300) * scale)
    bh = int(70 * scale)
    x0 = (W - bw) // 2
    y0 = cta_y - bh // 2
    col = (95, 95, 95, 255) if subscribed else (255, 0, 0, 255)
    d.rounded_rectangle((x0 + 4, y0 + 6, x0 + bw + 4, y0 + bh + 6), radius=12, fill=(0, 0, 0, 90))
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=12, fill=col)
    fnt = _font(FONT_DIR / "Inter-Bold.ttf", int(28 * scale if not subscribed else 24 * scale))
    bb = d.textbbox((0, 0), label, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text((x0 + (bw - tw) // 2, y0 + (bh - th) // 2 - 2), label, font=fnt, fill=(255, 255, 255, 255))
    img.alpha_composite(layer)


def render_platform(key: str) -> Path:
    cfg = PLATFORMS[key]
    OUT: Path = cfg["out"]
    WORK: Path = cfg["work"]
    T0, T1 = float(cfg["t0"]), float(cfg["t1"])
    grade = str(cfg["grade"])
    fade = float(cfg["fade"])
    segs = list(cfg["segments"])
    cta_y = int(cfg["cta_y"])

    WORK.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    STOCK.mkdir(parents=True, exist_ok=True)

    clip_dur = T1 - T0
    print(f"[{key}] {T0:.2f}→{T1:.2f} ({clip_dur:.2f}s) layout={cfg['layout']} cta={cfg['cta']}", flush=True)

    raw_sum = sum(d for _, _, d in segs)
    scale = (clip_dur + fade * (len(segs) - 1)) / raw_sum
    segs = [(p, s, d * scale) for p, s, d in segs]

    vpaths, durs = [], []
    for i, (src, ss, dur) in enumerate(segs):
        if not src.exists():
            raise FileNotFoundError(src)
        src_dur = float(
            subprocess.check_output(
                [
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", str(src),
                ],
                text=True,
            ).strip()
        )
        if ss + dur > src_dur - 0.05:
            dur = max(1.0, src_dur - ss - 0.05)
        dest = WORK / f"v{i:02d}.mp4"
        print(f"  prep {src.name} → {dur:.2f}s", flush=True)
        to_vertical(src, ss, dur, dest, grade)
        vpaths.append(dest)
        durs.append(dur)

    bed = WORK / "bed.mp4"
    total_v = concat_xfade(vpaths, durs, bed, fade=fade)
    print(f"bed ~{total_v:.2f}s", flush=True)

    bed2 = WORK / "bed_exact.mp4"
    loop = "2" if total_v + 0.05 < clip_dur else "0"
    subprocess.check_call(
        [
            "ffmpeg", "-y", "-stream_loop", loop, "-i", str(bed),
            "-t", f"{clip_dur:.3f}",
            "-vf", f"fps={FPS},scale={W}:{H}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
            str(bed2),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    audio = WORK / "audio.wav"
    subprocess.check_call(
        [
            "ffmpeg", "-y",
            "-ss", f"{T0:.3f}", "-t", f"{clip_dur:.3f}",
            "-i", str(AUDIO),
            "-ac", "2", "-ar", "44100",
            str(audio),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    cemal = ensure_cemal()
    kinetic_layers: list[Image.Image] | None = None
    quote: Image.Image | None = None
    if cfg["reveal"] == "kinetic":
        kinetic_layers = make_yt_line_layers(cemal, cta_y)
    elif cfg["layout"] == "left":
        quote = make_quote_left(cemal, cta_y)
    else:
        quote = make_quote_center_static(cemal, cta_y)

    n_frames = int(round(clip_dur * FPS))
    ff_log = WORK / "ffmpeg.log"
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(audio),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        str(OUT),
    ]
    ff_err = open(ff_log, "w")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=ff_err)
    assert proc.stdin is not None
    bed_proc = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-i", str(bed2),
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    assert bed_proc.stdout is not None
    frame_bytes = W * H * 3

    print(f"Compositing {n_frames}f…", flush=True)
    try:
        for fi in range(n_frames):
            raw = bed_proc.stdout.read(frame_bytes)
            if len(raw) < frame_bytes:
                break
            frame = Image.frombytes("RGB", (W, H), raw).convert("RGBA")
            t = fi / FPS

            if kinetic_layers is not None:
                # credit always; lines stagger in; cemal last
                frame.alpha_composite(kinetic_layers[0])
                # line i appears at 0.35 + i*0.55
                for i, L in enumerate(kinetic_layers[1:-1]):
                    t0 = 0.25 + i * 0.48
                    if t < t0:
                        continue
                    a = min(1.0, (t - t0) / 0.35)
                    q = L.copy()
                    if a < 1.0:
                        qa = np.array(q)
                        qa[:, :, 3] = (qa[:, :, 3].astype(np.float32) * a).astype(np.uint8)
                        q = Image.fromarray(qa)
                    frame.alpha_composite(q)
                # cemal after last line
                ct0 = 0.25 + (len(kinetic_layers) - 2) * 0.48 + 0.15
                if t >= ct0:
                    a = min(1.0, (t - ct0) / 0.4)
                    q = kinetic_layers[-1].copy()
                    if a < 1.0:
                        qa = np.array(q)
                        qa[:, :, 3] = (qa[:, :, 3].astype(np.float32) * a).astype(np.uint8)
                        q = Image.fromarray(qa)
                    frame.alpha_composite(q)
            else:
                assert quote is not None
                q = quote.copy()
                if t < 0.55:
                    a = t / 0.55
                    qa = np.array(q)
                    qa[:, :, 3] = (qa[:, :, 3].astype(np.float32) * a).astype(np.uint8)
                    q = Image.fromarray(qa)
                elif t > clip_dur - 0.85:
                    a = max(0.0, (clip_dur - t) / 0.85)
                    qa = np.array(q)
                    qa[:, :, 3] = (qa[:, :, 3].astype(np.float32) * a).astype(np.uint8)
                    q = Image.fromarray(qa)
                frame.alpha_composite(q)

            if t >= 2.2:
                if cfg["cta"] == "follow":
                    draw_follow_cta(frame, t - 2.2, cta_y)
                else:
                    draw_subscribe_pulse(frame, t - 2.2, cta_y)

            # YT end card hint (last 1.2s)
            if key == "yt" and t > clip_dur - 1.2:
                end = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ed = ImageDraw.Draw(end)
                a = int(140 * min(1.0, (t - (clip_dur - 1.2)) / 0.4))
                ed.rectangle((0, 0, W, H), fill=(0, 0, 0, a))
                ef = _font(FONT_DIR / "Inter-Bold.ttf", 36)
                msg = "ARVEN SOLÉ"
                bb = ed.textbbox((0, 0), msg, font=ef)
                ed.text(((W - (bb[2] - bb[0])) // 2, H // 2 - 30), msg, font=ef, fill=(255, 255, 255, min(255, a + 80)))
                frame.alpha_composite(end)

            proc.stdin.write(frame.convert("RGB").tobytes())
            if fi % 72 == 0:
                print(f"  {fi}/{n_frames}", flush=True)
    finally:
        proc.stdin.close()
        bed_proc.stdout.close()
        bed_proc.wait()
        code = proc.wait()
        ff_err.close()

    if code != 0:
        print(ff_log.read_text(errors="replace")[-2500:], file=sys.stderr)
        raise RuntimeError(f"ffmpeg failed {code}")

    dest = ART / OUT.name
    dest.write_bytes(OUT.read_bytes())
    print(f"Done {OUT} ({OUT.stat().st_size / 1e6:.1f}MB)", flush=True)
    return OUT


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("platform", nargs="?", default="both", choices=["ig", "yt", "both"])
    args = ap.parse_args()
    keys = ["ig", "yt"] if args.platform == "both" else [args.platform]
    for k in keys:
        render_platform(k)


if __name__ == "__main__":
    main()
