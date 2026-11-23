"""Trace ID maps (one flat colour per part, PNG red = 10 x id) into clean vector outlines for the page: one SVG path
per part per frame, smoothed and simplified, so the highlight is a crisp anti-aliased line instead of jagged pixels.
The maps are rendered at twice the picture's size (layers.py --job orbit-ids); the paths are written in the
picture's own pixels.

  python tools/render/trace_ids.py tools/render/out/anatomy-ids public/dev/inner/anatomy/outlines.json [--scale 0.5]
Writes {"size": [w, h], "frames": [{"<id>": "M..Z", ...}, ...]} (frames in file-name order). Needs
opencv-python-headless and numpy.
"""
import argparse
import glob
import json
import os

import cv2
import numpy as np


def num(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def trace(png, scale, min_area=40.0, eps=1.7):
    img = cv2.imread(png, cv2.IMREAD_COLOR)
    ids = np.rint(img[..., 2].astype(np.float32) / 10).astype(np.int32)
    out = {}
    for i in sorted(set(np.unique(ids)) - {0}):
        mask = (ids == i).astype(np.uint8) * 255
        if i != 21:   # close pinholes in wood parts (not the nails: they are only a few pixels wide)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        parts = []
        for c in contours:
            if cv2.contourArea(c) < (6.0 if i == 21 else min_area):
                continue
            a = cv2.approxPolyDP(c, eps, True).reshape(-1, 2) * scale
            parts.append("M" + "L".join(f"{num(x)},{num(y)}" for x, y in a) + "Z")
        if parts:
            out[str(i)] = "".join(parts)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("out")
    ap.add_argument("--scale", type=float, default=0.5)
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.folder, "*.png")))
    if not files:
        raise SystemExit(f"no PNG in {a.folder}")
    h, w = cv2.imread(files[0]).shape[:2]
    frames = [trace(f, a.scale) for f in files]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump({"size": [round(w * a.scale), round(h * a.scale)], "frames": frames}, open(a.out, "w"), separators=(",", ":"))
    print(f"traced {len(files)} frames -> {a.out} ({os.path.getsize(a.out) // 1024} KB)")
