"""Lay Freestyle ink lines over their photo frames in the exact brand blue (scenes that write a _raw folder, e.g.
tools/render/hero/blueprint.py). Blender's view transform would shift a blue line colour, so the lines are rendered
white on transparent and coloured here. Writes <dir>/NN.webp and removes <dir>/_raw.

  python tools/render/compose_lines.py public/dev/r7/blueprint [--quality 82] [--keep]
Needs Pillow (pip install pillow).
"""
import argparse
import glob
import os
import shutil

import numpy as np
from PIL import Image

BLUE = (0x0B, 0x3A, 0x9E)


def run(folder, quality=82, keep=False):
    raw = os.path.join(folder, "_raw")
    blue = np.array(BLUE, np.float32)
    n = 0
    for photo in sorted(glob.glob(os.path.join(raw, "[0-9][0-9].png")) + glob.glob(os.path.join(raw, "[0-9][0-9][0-9].png"))):
        stem = os.path.basename(photo)[:-4]
        ink = os.path.join(raw, f"{stem}-lines.png")
        img = np.asarray(Image.open(photo).convert("RGB"), np.float32)
        if os.path.exists(ink):
            a = np.asarray(Image.open(ink).convert("RGBA"), np.float32)[..., 3:4] / 255.0
            img = img * (1 - a) + blue * a
        Image.fromarray(np.clip(img + 0.5, 0, 255).astype(np.uint8)).save(
            os.path.join(folder, f"{stem}.webp"), quality=quality, method=6)
        n += 1
    if not keep:
        shutil.rmtree(raw, ignore_errors=True)
    print(f"composed {n} frames in {folder}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--quality", type=int, default=82)
    ap.add_argument("--keep", action="store_true", help="keep the _raw folder")
    a = ap.parse_args()
    run(a.folder, a.quality, a.keep)
