#!/usr/bin/env python3
"""Nefesim Daralıyor — TikTok Short: chorus only + anxiety footage + long quote. No lyric UI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

AUDIO = Path("/workspace/arven_sole_tracks/Nefesim_Daraliyor.mp3")
OUT = Path("/workspace/ArvenSole_NefesimDaraliyor_TIKTOK_QUOTE.mp4")
ART = Path("/opt/cursor/artifacts")
STOCK = Path("/tmp/nefes_stock")
WORK = Path("/tmp/nefes_quote_short")
FONT = Path("/workspace/fonts/CormorantGaramond-SemiBoldItalic.ttf")
if not FONT.exists():
    FONT = Path("/usr/share/fonts/truetype/noto/NotoSerifDisplay-Italic.ttf")

W, H = 1080, 1920
FPS = 24
T0 = 114.5  # chorus start — Nefesim daralıyor
T1 = 136.0  # keep Short tight (~21.5s) through “sen kaldın içimde”

QUOTE = (
    "Her şey yolundayken bile içimde hep tetikte bekleyen bir taraf var, "
    "sanki az sonra kötü bir şey olacakmış gibi kalbim durmadan sıkışıyor, "
    "nefesim daralıyor, kafam susmayan sorularla ve ihtimallerle dolup taşıyor, "
    "geceleri uyumam gerekirken zihnim beni rahat bırakmıyor ve o bitmeyen "
    "iç gürültünün içinde yavaş yavaş yok oluyorum."
)

# Real video: sleepless night → overthinking → trapped/breathless
SEGMENTS = [
    (STOCK / "48733.mp4", 0.8, 8.0),   # awake in bed, staring at ceiling (night mind)
    (STOCK / "51399.mp4", 0.5, 7.0),   # restless insomnia in bed
    (STOCK / "17536.mp4", 1.0, 7.0),   # hand on fence at night — trapped / breathless
]


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT), size)


def to_vertical(src: Path, t0: float, dur: float, dest: Path) -> None:
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},"
        "eq=brightness=-0.08:saturation=0.82:contrast=1.06,"
        "vignette=PI/4.5"
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
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p",
            str(dest),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return total


def wrap_quote(draw: ImageDraw.ImageDraw, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = QUOTE.split()
    lines: list[str] = []
    cur: list[str] = []
    for word in words:
        trial = (" ".join(cur + [word])).strip()
        bb = draw.textbbox((0, 0), trial, font=fnt)
        if bb[2] - bb[0] <= max_w:
            cur.append(word)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [word]
    if cur:
        lines.append(" ".join(cur))
    # curly quotes wrap whole block
    if lines:
        lines[0] = "“" + lines[0]
        lines[-1] = lines[-1] + "”"
    return lines


def make_quote_overlay() -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    top, bot = 420, 1500
    for y in range(top, bot):
        p = abs((y - (top + bot) / 2) / ((bot - top) / 2))
        a = int(165 * max(0.0, 1.0 - p**1.25))
        wd.line([(48, y), (W - 48, y)], fill=(0, 0, 0, a))
    layer = Image.alpha_composite(layer, wash)

    d = ImageDraw.Draw(layer)
    fnt = _font(40)
    lines = wrap_quote(d, fnt, max_w=W - 160)
    line_gap = 14
    heights = []
    widths = []
    for line in lines:
        bb = d.textbbox((0, 0), line, font=fnt)
        widths.append(bb[2] - bb[0])
        heights.append(bb[3] - bb[1])
    block_h = sum(heights) + line_gap * (len(lines) - 1)
    y = (H - block_h) // 2 - 30

    # champagne rules
    rule_w = 56
    d.rectangle(
        ((W - rule_w) // 2, y - 36, (W + rule_w) // 2, y - 34),
        fill=(232, 214, 170, 220),
    )

    cream = (248, 240, 226, 255)
    accent = (255, 214, 170, 255)  # highlight for "nefesim daralıyor"
    for i, line in enumerate(lines):
        tw = widths[i]
        x = (W - tw) // 2
        for ox, oy in ((2, 2), (3, 3), (1, 1)):
            d.text((x + ox, y + oy), line, font=fnt, fill=(0, 0, 0, 170))
        # highlight phrase if present on this line
        if "nefesim daralıyor" in line.lower():
            # draw whole line cream; then redraw the phrase in accent by splitting
            low = line.lower()
            idx = low.find("nefesim daralıyor")
            before, mid, after = line[:idx], line[idx:idx + len("nefesim daralıyor")], line[idx + len("nefesim daralıyor"):]
            # preserve original casing from line
            mid = line[idx:idx + len("nefesim daralıyor")]
            cx = x
            if before:
                d.text((cx, y), before, font=fnt, fill=cream)
                cx += d.textbbox((0, 0), before, font=fnt)[2]
            d.text((cx, y), mid, font=fnt, fill=accent)
            cx += d.textbbox((0, 0), mid, font=fnt)[2]
            if after:
                d.text((cx, y), after, font=fnt, fill=cream)
        else:
            d.text((x, y), line, font=fnt, fill=cream)
        y += heights[i] + line_gap

    d.rectangle(
        ((W - rule_w) // 2, y + 20, (W + rule_w) // 2, y + 22),
        fill=(232, 214, 170, 220),
    )
    bloom = layer.filter(ImageFilter.GaussianBlur(0.8))
    return Image.alpha_composite(bloom, layer)


def render() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)

    clip_dur = T1 - T0
    print(f"Audio cut {T0:.2f} → {T1:.2f} ({clip_dur:.2f}s)", flush=True)

    fade = 0.65
    segs = list(SEGMENTS)
    raw_sum = sum(d for _, _, d in segs)
    n_fades = len(segs) - 1
    target_raw = clip_dur + fade * n_fades
    scale = target_raw / raw_sum
    segs = [(p, s, d * scale) for p, s, d in segs]
    print("Segment lengths:", [round(d, 2) for _, _, d in segs], flush=True)

    vpaths = []
    durs = []
    for i, (src, ss, dur) in enumerate(segs):
        if not src.exists():
            raise FileNotFoundError(src)
        # don't request longer than source
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
    print(f"Video bed ~{total_v:.2f}s", flush=True)

    # If bed short, loop; then trim exact
    bed2 = WORK / "bed_exact.mp4"
    if total_v + 0.05 < clip_dur:
        subprocess.check_call(
            [
                "ffmpeg", "-y", "-stream_loop", "2", "-i", str(bed),
                "-t", f"{clip_dur:.3f}",
                "-vf", f"fps={FPS},scale={W}:{H}",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p",
                str(bed2),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
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

    quote = make_quote_overlay()
    quote_path = WORK / "quote.png"
    quote.save(quote_path)

    # Quote visible ASAP (no long delay) — fade in 0→0.5s, fade out last 1.0s
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
                f"fade=t=in:st=0:d=0.45:alpha=1,"
                f"fade=t=out:st={clip_dur - 1.0:.3f}:d=1.0:alpha=1[q];"
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
