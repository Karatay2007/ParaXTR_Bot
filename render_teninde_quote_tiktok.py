#!/usr/bin/env python3
"""Teninde Kal — TikTok quote Short (premium mural layout + ferah stock + ABONE CTA)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AUDIO = Path("/workspace/arven_sole_tracks/Teninde_Kal.mp3")
OUT = Path("/workspace/ArvenSole_TenindeKal_TIKTOK_QUOTE.mp4")
ART = Path("/opt/cursor/artifacts")
STOCK = Path("/tmp/teninde_quote")
WORK = Path("/tmp/teninde_quote_short_v3")
CEMAL_SRC = Path("/opt/cursor/artifacts/assets/cemal_sureya_stencil_v2.png")
CEMAL_RGBA = STOCK / "cemal_rgba_v2.png"
FONT = Path("/workspace/fonts/Caveat-Bold.ttf")
if not FONT.exists():
    FONT = Path("/workspace/fonts/IndieFlower-Regular.ttf")
FONT_DIR = Path("/usr/share/fonts/truetype/macos")
ICON_THUMB = Path("/workspace/fonts/icons/thumb_up.png")
ICON_BELL = Path("/workspace/fonts/icons/bell.png")

W, H = 1080, 1920
FPS = 24
T0 = 120.7
T1 = 154.5
CTA_Y = 1640
LIKE_BLUE = (66, 133, 244)

INTRO = "Cemal Süreya’nın dediği gibi;"
# Manual mural line breaks — left column, clean rhythm
# Exact mural line breaks (reference wall photo)
QUOTE_LINES = [
    "“Seni, senin bile",
    "haberinin olmadığı",
    "şeylerden dolayı",
    "seviyorum,",
    "sen boşuna",
    "saçlarını",
    "düzeltiyorsun…”",
]
INTRO_LINES = [
    "Cemal Süreya’nın",
    "dediği gibi;",
]

# Ferah cinematic beds matching intimacy / stay-close lyric
SEGMENTS = [
    (STOCK / "4840.mp4", 1.0, 8.5),     # golden sunset open air
    (STOCK / "45857.mp4", 0.2, 4.8),    # holding hands
    (STOCK / "45856.mp4", 0.5, 8.0),    # couple golden hour
    (STOCK / "4841.mp4", 0.4, 7.5),     # bright airy
    (STOCK / "4511.mp4", 0.2, 5.5),    # window light
    (STOCK / "4624.mp4", 1.0, 8.0),    # warm romantic
]


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


def to_vertical(src: Path, t0: float, dur: float, dest: Path) -> None:
    # Center-weighted 9:16, lifted exposure (ferah), gentle vignette
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},"
        "eq=brightness=0.14:saturation=1.08:contrast=1.02,"
        "vignette=PI/12"
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


def concat_xfade(paths: list[Path], durs: list[float], dest: Path, fade: float = 0.55) -> float:
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


def make_quote_overlay(cemal: Image.Image) -> Image.Image:
    """Mural typography on video: black hand lettering TL, Cemal BR. No frosted card."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # Soft light wash only behind text+figure for readability (not a box)
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    for y in range(260, 1280):
        p = abs((y - 760) / 520)
        a = int(95 * max(0.0, 1.0 - p ** 1.2))
        wd.line([(40, y), (W - 40, y)], fill=(255, 250, 242, a))
    wash = wash.filter(ImageFilter.GaussianBlur(12))
    layer = Image.alpha_composite(layer, wash)
    d = ImageDraw.Draw(layer)

    ink = (10, 8, 7, 255)
    intro_fnt = _font(FONT, 46)
    quote_fnt = _font(FONT, 54)

    def draw_ink(x: int, y: int, text: str, fnt) -> int:
        # white halo so black reads on any footage
        for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            d.text((x + ox, y + oy), text, font=fnt, fill=(255, 252, 247, 200))
        d.text((x + 1, y + 1), text, font=fnt, fill=(0, 0, 0, 50))
        d.text((x, y), text, font=fnt, fill=ink)
        bb = d.textbbox((0, 0), text, font=fnt)
        return bb[3] - bb[1]

    tx, y = 64, 300
    for line in INTRO_LINES:
        h = draw_ink(tx, y, line, intro_fnt)
        y += h + 2
    y += 16
    for line in QUOTE_LINES:
        h = draw_ink(tx, y, line, quote_fnt)
        y += h + 4

    cw = 400
    ch = int(cemal.height * (cw / max(1, cemal.width)))
    cemal_r = cemal.resize((cw, ch), Image.Resampling.LANCZOS)
    # soft white rim behind cemal for punch
    rim = Image.new("RGBA", (cw + 24, ch + 24), (0, 0, 0, 0))
    ca = np.array(cemal_r)
    mask = ca[:, :, 3] > 20
    # expand mask for rim
    from PIL import ImageFilter as IF
    alpha = Image.fromarray(ca[:, :, 3]).filter(IF.MaxFilter(7))
    rim_a = np.array(alpha)
    rim_img = np.zeros((ch, cw, 4), dtype=np.uint8)
    rim_img[:, :, 0:3] = 255
    rim_img[:, :, 3] = (rim_a.astype(np.float32) * 0.55).astype(np.uint8)
    rim_pil = Image.fromarray(rim_img).filter(IF.GaussianBlur(3))
    cx = W - cw - 48
    cy = min(CTA_Y - ch - 180, 980)
    layer.alpha_composite(rim_pil, (cx, cy))
    layer.alpha_composite(cemal_r, (cx, cy))
    return layer


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

    like_r = int(40 + (5 * press if stage == 0 and local >= 0.55 else 0))
    bell_r = int(40 + (5 * press if stage == 2 and local >= 0.55 else 0))
    sub_scale = 1.0 + (0.06 * press if stage == 1 and local >= 0.55 else 0.0)

    gap = 18
    label = "ABONE OLUNDU" if subscribed else "ABONE OL"
    sub_w = int((320 if subscribed else 280) * sub_scale)
    sub_h = int(66 * sub_scale)
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
    fnt = _font(FONT_DIR / "Inter-Bold.ttf", int(24 * sub_scale if subscribed else 28 * sub_scale))
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


def render() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    STOCK.mkdir(parents=True, exist_ok=True)

    clip_dur = T1 - T0
    print(f"TikTok ferah + mural text  {T0:.2f}→{T1:.2f} ({clip_dur:.2f}s)", flush=True)

    fade = 0.55
    segs = list(SEGMENTS)
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
        to_vertical(src, ss, dur, dest)
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

    quote = make_quote_overlay(ensure_cemal())
    quote_path = WORK / "quote.png"
    quote.save(quote_path)

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
            "ffmpeg", "-v", "error",
            "-i", str(bed2),
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
            "-",
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
            q = quote.copy()
            if t < 0.35:
                a = t / 0.35
                qa = np.array(q)
                qa[:, :, 3] = (qa[:, :, 3].astype(np.float32) * a).astype(np.uint8)
                q = Image.fromarray(qa)
            elif t > clip_dur - 0.9:
                a = max(0.0, (clip_dur - t) / 0.9)
                qa = np.array(q)
                qa[:, :, 3] = (qa[:, :, 3].astype(np.float32) * a).astype(np.uint8)
                q = Image.fromarray(qa)
            frame.alpha_composite(q)
            draw_subscribe_cta(frame, t)
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


if __name__ == "__main__":
    render()
