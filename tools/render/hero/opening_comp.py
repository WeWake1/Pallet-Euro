"""PROTOTYPE round 11 · D "Through the opening": lay the frames of opening.py together (system Python: Pillow, numpy).

For each place in turn, each seg frame (RGBA: the hole in B's far opening) goes over the next place's portal frame
of the same number; while the camera passes through the opening, the whole picture cross-fades to the portal frame,
so the boards round the camera take the next place's light. Writes public/dev/r11/opening/000.webp .. (one loop).

  python tools/render/hero/opening_comp.py [--test]      (tools/render/run.py r11-opening runs it by itself)
"""
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ORDER = ["factory", "india", "port", "europe"]


def run(test=False):
    src = os.path.join(ROOT, ".render-test" if test else os.path.join("tools", "render", "out"), "opening")
    dst = os.path.join(src, "final") if test else os.path.join(ROOT, "public", "dev", "r11", "opening")
    os.makedirs(dst, exist_ok=True)
    n = 0
    first_seen = {}                              # per place: the first frame where the place after next shows
    for k, place in enumerate(ORDER):
        meta_path = os.path.join(src, "seg", place, "meta.json")
        if not os.path.exists(meta_path):
            print("opening_comp: no frames for", place)
            continue
        meta = json.load(open(meta_path))
        F, holes, through = meta["frames"], set(meta["holes"]), meta["through"]
        nxt, nxt2 = ORDER[(k + 1) % len(ORDER)], ORDER[(k + 2) % len(ORDER)]
        for i in range(F):
            seg_p = os.path.join(src, "seg", place, f"{i:02d}.png")
            if not os.path.exists(seg_p):
                continue
            seg = np.asarray(Image.open(seg_p).convert("RGBA"), np.float32) / 255
            rgb, a = seg[..., :3], seg[..., 3:]
            out = rgb
            por_p = os.path.join(src, "portal", nxt, f"{i:02d}.png")
            if i in holes:
                if not os.path.exists(por_p):
                    print(f"opening_comp: {place} {i:02d} has a hole but no portal frame from {nxt}")
                else:
                    por = np.asarray(Image.open(por_p).convert("RGBA"), np.float32) / 255
                    por, pa = por[..., :3], por[..., 3:]
                    if pa.min() < 0.999:          # the far pallet's opening: the place after next shows there
                        p2_p = os.path.join(src, "portal2", nxt2, f"{i:02d}.png")
                        if os.path.exists(p2_p):
                            p2 = np.asarray(Image.open(p2_p).convert("RGB"), np.float32) / 255
                            por = por * pa + p2 * (1 - pa)
                            seen = float(((1 - a) * (1 - pa)).sum())
                            if seen > 1 and place not in first_seen:
                                first_seen[place] = i
                        else:
                            print(f"opening_comp: {place} {i:02d}: portal has a hole but no portal2 frame from {nxt2}")
                    out = rgb * a + por * (1 - a)
                    w = through[i]
                    out = out * (1 - w) + por * w
            img = Image.fromarray(np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8), "RGB")
            img.save(os.path.join(dst, f"{k * F + i:03d}.webp"), quality=80, method=5)
            n += 1
    print(f"opening_comp: {n} frames -> {os.path.relpath(dst, ROOT)}; the place after next first shows at {first_seen}")


if __name__ == "__main__":
    run(test="--test" in sys.argv)
