#!/usr/bin/env python3
"""Unutamadım Seni — TikTok Short from 2:43, real stock video + elegant quote. No lyric UI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

AUDIO = Path("/workspace/arven_sole_tracks/Unutamadim_Seni.mp3")
OUT = Path("/workspace/ArvenSole_UnutamadimSeni_TIKTOK_SHORT_243.mp4")
ART = Path("/opt/cursor/artifacts")
STOCK = Path("/tmp/unut_stock")
WORK = Path("/tmp/unut_short243")
FONT = Path("/workspace/fonts/CormorantGaramond-SemiBoldItalic.ttf")
if not FONT.exists():
    FONT = Path("/workspace/fonts/CormorantGaramond-SemiBold.ttf")
if not FONT.exists():
    FONT = Path("/usr/share/fonts/truetype/noto/NotoSerifDisplay-Italic.ttf")

W, H = 1080, 1920
FPS = 24
T0 = 163.0  # 02:43
# Exact user quote with stylish curly quotes — line breaks for 9:16
QUOTE_LINES = [
    "“Ölene kadar unutamayacağım kişiyle,",
    "Hiç kavuşamayacağım kişi aynı kişi”",
]

# Real video beds (Mixkit), themed loneliness / night walk
SEGMENTS = [
    (STOCK / "36446-720.mp4", 0.0, 20.0),   # rainy night lonely man
    (STOCK / "27766-720.mp4", 0.0, 18.0),   # walking stairs motion
    (STOCK / "40640-720.mp4", 0.0, 14.96),  # lonely path / city night
]


def ensure_audio_clip(clip_dur: float) -> Path:
    out = WORK / "audio.wav"
    subprocess.check_call(
        [
            "ffmpeg", "-y",
            "-ss", f"{T0:.3f}", "-t", f"{clip_dur:.3f}",
            "-i", str(AUDIO),
            "-ac", "2", "-ar", "44100",
            str(out),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return out


def to_vertical(src: Path, t0: float, dur: float, dest: Path) -> None:
    """Crop/scale any aspect to 9:16 with cinematic grade."""
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},"
        # slight darken + cool grade for quote readability / mood
        "eq=brightness=-0.06:saturation=0.85:contrast=1.05,"
        "vignette=PI/5"
    )
    subprocess.check_call(
        [
            "ffmpeg", "-y",
            "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}",
            "-i", str(src),
            "-vf", vf,
            "-r", str(FPS),
            "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p",
            str(dest),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def concat_xfade(paths: list[Path], durs: list[float], dest: Path, fade: float = 0.6) -> float:
    """Crossfade concat; returns total output duration."""
    if len(paths) == 1:
        dest.write_bytes(paths[0].read_bytes())
        return durs[0]

    # offset timeline for xfade chain
    inputs = []
    for p in paths:
        inputs.extend(["-i", str(p)])

    parts = []
    # first stream
    current = "[0:v]"
    total = durs[0]
    for i in range(1, len(paths)):
        # offset = sum(prev durations) - fade * i
        offset = sum(durs[:i]) - fade * i
        out = f"[v{i}]" if i < len(paths) - 1 else "[vout]"
        parts.append(
            f"{current}[{i}:v]xfade=transition=fade:duration={fade}:offset={offset:.3f}{out}"
        )
        current = out
        total = total + durs[i] - fade

    fc = ";".join(parts)
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", fc,
        "-map", "[vout]",
        "-r", str(FPS),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p",
        str(dest),
    ]
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return total


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT), size)


def make_quote_overlay() -> Image.Image:
    """Elegant centered quote — transparent overlay, no card chrome."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # soft dark wash behind text for readability on moving footage
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    top, bot = 640, 1180
    for y in range(top, bot):
        p = abs((y - (top + bot) / 2) / ((bot - top) / 2))
        a = int(145 * max(0.0, 1.0 - p**1.35))
        wd.line([(56, y), (W - 56, y)], fill=(0, 0, 0, a))
    layer = Image.alpha_composite(layer, wash)

    d = ImageDraw.Draw(layer)
    fnt = _font(50)
    widths = []
    heights = []
    for line in QUOTE_LINES:
        bb = d.textbbox((0, 0), line, font=fnt)
        widths.append(bb[2] - bb[0])
        heights.append(bb[3] - bb[1])
    line_gap = 28
    block_h = sum(heights) + line_gap * (len(QUOTE_LINES) - 1)
    y = (H - block_h) // 2 - 20

    # thin champagne rules
    rule_w = 64
    rule_y = y - 40
    d.rectangle(
        ((W - rule_w) // 2, rule_y, (W + rule_w) // 2, rule_y + 2),
        fill=(232, 214, 170, 220),
    )

    cream = (248, 240, 226, 255)
    for i, line in enumerate(QUOTE_LINES):
        tw = widths[i]
        x = (W - tw) // 2
        for ox, oy in ((3, 3), (2, 2), (1, 1), (-1, 1)):
            d.text((x + ox, y + oy), line, font=fnt, fill=(0, 0, 0, 170))
        d.text((x, y), line, font=fnt, fill=cream)
        y += heights[i] + line_gap

    rule_y = y + 22
    d.rectangle(
        ((W - rule_w) // 2, rule_y, (W + rule_w) // 2, rule_y + 2),
        fill=(232, 214, 170, 220),
    )

    bloom = layer.filter(ImageFilter.GaussianBlur(0.9))
    return Image.alpha_composite(bloom, layer)


def render() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)

    # probe full audio for remaining duration
    import json as _json

    probe = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(AUDIO),
        ],
        text=True,
    ).strip()
    full_dur = float(probe)
    clip_dur = full_dur - T0
    print(f"Audio cut {T0:.2f} → {full_dur:.2f} ({clip_dur:.2f}s)", flush=True)

    # Adjust last segment so video bed matches audio length (after fades)
    fade = 0.65
    fixed = SEGMENTS[:-1]
    used = sum(d for _, _, d in fixed) - fade * (len(fixed))  # approx before last
    # simpler: build segments totaling clip_dur + fades
    segs = list(SEGMENTS)
    raw_sum = sum(d for _, _, d in segs)
    n_fades = len(segs) - 1
    # after xfade total ≈ raw_sum - fade*n_fades
    target_raw = clip_dur + fade * n_fades
    scale = target_raw / raw_sum
    segs = [(p, s, d * scale) for p, s, d in segs]
    print("Segment lengths:", [round(d, 2) for _, _, d in segs], flush=True)

    vpaths = []
    durs = []
    for i, (src, ss, dur) in enumerate(segs):
        if not src.exists():
            raise FileNotFoundError(src)
        dest = WORK / f"v{i:02d}.mp4"
        print(f"  prep {src.name} → {dur:.2f}s", flush=True)
        to_vertical(src, ss, dur, dest)
        vpaths.append(dest)
        durs.append(dur)

    bed = WORK / "bed.mp4"
    total_v = concat_xfade(vpaths, durs, bed, fade=fade)
    print(f"Video bed ~{total_v:.2f}s", flush=True)

    # trim/pad bed to exact clip_dur
    bed2 = WORK / "bed_exact.mp4"
    subprocess.check_call(
        [
            "ffmpeg", "-y", "-i", str(bed),
            "-t", f"{clip_dur:.3f}",
            "-vf", f"fps={FPS},scale={W}:{H}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p",
            str(bed2),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    audio = ensure_audio_clip(clip_dur)
    quote = make_quote_overlay()
    quote_path = WORK / "quote.png"
    quote.save(quote_path)

    # Fade quote in 0.8→2.2s, hold, fade out last 1.2s (via alpha fade filters)
    ff_log = WORK / "ffmpeg.log"
    with open(ff_log, "w") as ff_err:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(bed2),
            "-loop", "1", "-framerate", str(FPS), "-t", f"{clip_dur:.3f}", "-i", str(quote_path),
            "-i", str(audio),
            "-filter_complex",
            (
                f"[1:v]fps={FPS},format=rgba,"
                f"fade=t=in:st=0.8:d=1.4:alpha=1,"
                f"fade=t=out:st={clip_dur - 1.2:.3f}:d=1.2:alpha=1[q];"
                f"[0:v][q]overlay=0:0:format=auto[v]"
            ),
            "-map", "[v]", "-map", "2:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-r", str(FPS),
            "-t", f"{clip_dur:.3f}",
            "-movflags", "+faststart",
            str(OUT),
        ]
        code = subprocess.call(cmd, stdout=ff_err, stderr=subprocess.STDOUT)
    if code != 0:
        print(ff_log.read_text(errors="replace")[-3000:], file=sys.stderr)
        raise RuntimeError(f"ffmpeg failed {code}")

    dest = ART / OUT.name
    dest.write_bytes(OUT.read_bytes())
    print(f"Done {OUT} ({OUT.stat().st_size/1e6:.1f}MB)", flush=True)


if __name__ == "__main__":
    render()
