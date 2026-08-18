#!/usr/bin/env python3
"""Replace Yeşilçam faces with funny 3D characters. Original audio kept."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

SRC = Path("/tmp/yesilcam/source_h264.mp4")
OUT = Path("/workspace/ArvenSole_Yesilcam_3DCHARS_DEMO.mp4")
ART = Path("/opt/cursor/artifacts") / OUT.name
MODEL = Path("/tmp/yesilcam/models/face_detection_yunet_2023mar.onnx")

CHAR_PATHS = [
    Path("/opt/cursor/artifacts/assets/char_mustache_3d.png"),
    Path("/opt/cursor/artifacts/assets/char_bald_3d.png"),
    Path("/opt/cursor/artifacts/assets/char_tough_3d.png"),
]

T0 = 8.0
DUR = 42.0
FPS = 24
W, H = 1024, 576
MIN_SCORE = 0.58
MIN_FACE_W = 40


def chroma_cut(path: Path) -> np.ndarray:
    bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if bgr is None:
        raise FileNotFoundError(path)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    green = cv2.inRange(hsv, (35, 60, 40), (95, 255, 255))
    # soften spill
    green = cv2.dilate(green, np.ones((3, 3), np.uint8), iterations=1)
    green = cv2.GaussianBlur(green, (7, 7), 0)
    alpha = 255 - green
    # keep opaque core
    alpha = np.clip(alpha.astype(np.int16) * 1.15, 0, 255).astype(np.uint8)
    ys, xs = np.where(alpha > 30)
    y0, y1 = max(0, ys.min() - 4), min(bgr.shape[0] - 1, ys.max() + 4)
    x0, x1 = max(0, xs.min() - 4), min(bgr.shape[1] - 1, xs.max() + 4)
    rgba = cv2.cvtColor(bgr[y0 : y1 + 1, x0 : x1 + 1], cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = alpha[y0 : y1 + 1, x0 : x1 + 1]
    return rgba


def paste_rgba(dst: np.ndarray, overlay: np.ndarray, cx: float, cy: float, target_h: int) -> None:
    oh, ow = overlay.shape[:2]
    scale = target_h / max(1, oh)
    nw, nh = max(1, int(ow * scale)), max(1, int(oh * scale))
    resized = cv2.resize(overlay, (nw, nh), interpolation=cv2.INTER_AREA)
    x1 = int(cx - nw / 2)
    y1 = int(cy - nh * 0.55)  # bias up so hair covers forehead
    x2, y2 = x1 + nw, y1 + nh
    H0, W0 = dst.shape[:2]
    sx1, sy1 = max(0, x1), max(0, y1)
    sx2, sy2 = min(W0, x2), min(H0, y2)
    if sx1 >= sx2 or sy1 >= sy2:
        return
    ox1, oy1 = sx1 - x1, sy1 - y1
    ox2, oy2 = ox1 + (sx2 - sx1), oy1 + (sy2 - sy1)
    roi = dst[sy1:sy2, sx1:sx2]
    over = resized[oy1:oy2, ox1:ox2]
    a = over[:, :, 3:4].astype(np.float32) / 255.0
    # slight edge feather
    a = a * a  # gamma for cleaner composite
    rgb = over[:, :, :3].astype(np.float32)
    base = roi.astype(np.float32)
    out = rgb * a + base * (1.0 - a)
    dst[sy1:sy2, sx1:sx2] = np.clip(out, 0, 255).astype(np.uint8)


class Tracker:
    def __init__(self) -> None:
        self.tracks: dict[int, dict] = {}
        self.next_id = 0

    def update(self, faces: list[tuple[float, float, float, float, float]]) -> list[tuple[int, tuple]]:
        """faces: score,x,y,w,h  -> list of (track_id, (cx,cy,w,h))"""
        assigned = {}
        used = set()
        # match by center distance
        for tid, tr in list(self.tracks.items()):
            best_i, best_d = None, 1e9
            for i, (sc, x, y, w, h) in enumerate(faces):
                if i in used:
                    continue
                cx, cy = x + w / 2, y + h / 2
                d = (cx - tr["cx"]) ** 2 + (cy - tr["cy"]) ** 2
                if d < best_d and d < (max(tr["w"], w) * 1.8) ** 2:
                    best_d, best_i = d, i
            if best_i is not None:
                sc, x, y, w, h = faces[best_i]
                cx, cy = x + w / 2, y + h / 2
                # smooth
                tr["cx"] = 0.65 * tr["cx"] + 0.35 * cx
                tr["cy"] = 0.65 * tr["cy"] + 0.35 * cy
                tr["w"] = 0.65 * tr["w"] + 0.35 * w
                tr["h"] = 0.65 * tr["h"] + 0.35 * h
                tr["miss"] = 0
                assigned[tid] = (tr["cx"], tr["cy"], tr["w"], tr["h"])
                used.add(best_i)
            else:
                tr["miss"] += 1
                if tr["miss"] <= 6:
                    assigned[tid] = (tr["cx"], tr["cy"], tr["w"], tr["h"])
                else:
                    del self.tracks[tid]

        for i, (sc, x, y, w, h) in enumerate(faces):
            if i in used:
                continue
            cx, cy = x + w / 2, y + h / 2
            tid = self.next_id
            self.next_id += 1
            self.tracks[tid] = {"cx": cx, "cy": cy, "w": w, "h": h, "miss": 0}
            assigned[tid] = (cx, cy, w, h)

        # stable char index by average x (left→mustache)
        order = sorted(assigned.items(), key=lambda kv: kv[1][0])
        return [(tid, box) for tid, box in order]


def detect_faces(det: cv2.FaceDetectorYN, frame: np.ndarray) -> list[tuple]:
    h, w = frame.shape[:2]
    # run on original + mild upscale for small faces
    cands: list[tuple] = []
    for scale in (1.0, 1.35):
        if scale == 1.0:
            img = frame
        else:
            img = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
        ih, iw = img.shape[:2]
        det.setInputSize((iw, ih))
        _, faces = det.detect(img)
        if faces is None:
            continue
        for f in faces:
            x, y, fw, fh = map(float, f[:4])
            score = float(f[-1])
            x, y, fw, fh = x / scale, y / scale, fw / scale, fh / scale
            if score < MIN_SCORE or fw < MIN_FACE_W or fh < MIN_FACE_W * 0.75:
                continue
            ar = fw / max(1.0, fh)
            if ar < 0.45 or ar > 1.55:
                continue
            cy = y + fh * 0.5
            # Yeşilçam'da alt kadrajda el/çanta/diz sık false-positive veriyor
            if cy > h * 0.72:
                continue
            if y + fh > h * 0.97 and fh < h * 0.22:
                continue
            if fw * fh < 2200:
                continue
            cands.append((score, x, y, fw, fh))

    # NMS by IoU
    cands.sort(key=lambda t: t[0], reverse=True)
    kept: list[tuple] = []
    for c in cands:
        _, x, y, fw, fh = c
        ok = True
        for _, x2, y2, fw2, fh2 in kept:
            xa, ya = max(x, x2), max(y, y2)
            xb, yb = min(x + fw, x2 + fw2), min(y + fh, y2 + fh2)
            inter = max(0, xb - xa) * max(0, yb - ya)
            union = fw * fh + fw2 * fh2 - inter
            if union > 0 and inter / union > 0.35:
                ok = False
                break
        if ok:
            kept.append(c)

    if not kept:
        return []

    kept.sort(key=lambda t: t[3] * t[4], reverse=True)
    # Close-up: one giant face dominates → only that face
    area0 = kept[0][3] * kept[0][4]
    if area0 > 0.15 * w * h or kept[0][3] > 0.32 * w:
        return [kept[0]]

    # Keep faces comparable to the largest (drop tiny false positives)
    thr = area0 * 0.18
    kept = [f for f in kept if f[3] * f[4] >= thr]
    return kept[:4]


def render() -> None:
    chars = [chroma_cut(p) for p in CHAR_PATHS]
    for i, c in enumerate(chars):
        print(f"char{i} {c.shape} alpha>50={(c[:,:,3]>50).mean():.2f}", flush=True)

    det = cv2.FaceDetectorYN.create(str(MODEL), "", (320, 320), 0.55, 0.3, 5000)
    tracker = Tracker()
    # map track_id -> char index permanently once seen order establishes
    char_of: dict[int, int] = {}

    cap = cv2.VideoCapture(str(SRC))
    n_frames = int(DUR * FPS)
    ff_log = Path("/tmp/yesilcam_chars_ffmpeg.log")
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-ss", str(T0), "-t", str(DUR), "-i", str(SRC),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        str(OUT),
    ]
    ff_err = open(ff_log, "w")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=ff_err)
    assert proc.stdin is not None

    src_pos = T0
    step = 1.0 / FPS
    print(f"Rendering 3D char swap {T0}-{T0+DUR:.0f}s ({n_frames}f)", flush=True)
    try:
        for fi in range(n_frames):
            cap.set(cv2.CAP_PROP_POS_MSEC, src_pos * 1000.0)
            ok, frame = cap.read()
            if not ok or frame is None:
                frame = np.zeros((H, W, 3), dtype=np.uint8)
            else:
                frame = cv2.resize(frame, (W, H))

            faces = detect_faces(det, frame)
            ordered = tracker.update(faces)

            out = frame.copy()
            # darken/blur original face a bit under character for cleaner swap
            for tid, (cx, cy, fw, fh) in ordered:
                x1, y1 = int(cx - fw * 0.55), int(cy - fh * 0.55)
                x2, y2 = int(cx + fw * 0.55), int(cy + fh * 0.65)
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(W, x2), min(H, y2)
                if x2 > x1 and y2 > y1:
                    patch = out[y1:y2, x1:x2]
                    out[y1:y2, x1:x2] = cv2.GaussianBlur(patch, (21, 21), 0)

            # Left→mustache, next→bald, next→tough (per frame, stable roles)
            for slot, (tid, (cx, cy, fw, fh)) in enumerate(ordered):
                ci = slot % len(chars)
                char_of[tid] = ci
                target_h = int(max(fh * 2.35, 140))
                paste_rgba(out, chars[ci], cx, cy, target_h)

            proc.stdin.write(out.tobytes())
            src_pos += step
            if fi % 48 == 0:
                print(f"  {fi}/{n_frames} ({100*fi/n_frames:.0f}%) tracks={list(char_of.keys())}", flush=True)
    finally:
        proc.stdin.close()
        code = proc.wait()
        ff_err.close()
        cap.release()

    if code != 0:
        print(ff_log.read_text(errors="replace")[-2000:], file=sys.stderr)
        raise RuntimeError(f"ffmpeg failed {code}")
    ART.parent.mkdir(parents=True, exist_ok=True)
    ART.write_bytes(OUT.read_bytes())
    print(f"Done {OUT} ({OUT.stat().st_size/1e6:.1f}MB)", flush=True)


if __name__ == "__main__":
    render()
