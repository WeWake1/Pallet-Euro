"""Catalogue renders of all 28 pallets (or the slugs given), with this repo's marks (tools/render/brand.json):
  src/assets/products/<slug>/<n>.webp     studio renders (5 views; the collar 4)
  public/models/<slug>.glb                web 3D model, when brand.json has "glb": true (or --glb)

  python tools/render/render_all.py                          # everything (about 33 min on the Mac's M2 Pro)
  python tools/render/render_all.py euro-pallet-1200x800     # one or more slugs
  options: --res 1600 --samples 128 --views 1,2,3,4,5 --glb --blender PATH

DEV ONLY until the EPAL licence and Pallet Euro's own HT code exist: brand.json carries the EPAL oval and the
IN-XXX placeholder (CLAUDE.md, hard rules 2 and 6). Products and recipes: src/data/products-ambica-source.json
(slug -> pallet recipe), geometry src/data/pallet-geometry.json. Needs cwebp (see make_small.py).
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from run import find_blender  # noqa: E402
from make_small import cwebp  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--res", type=int, default=1600)
    ap.add_argument("--samples", type=int, default=128)
    ap.add_argument("--views", default="1,2,3,4,5")
    ap.add_argument("--glb", action="store_true", help="export the GLB even if brand.json says no")
    ap.add_argument("--blender")
    ap.add_argument("--out-root", default=ROOT, help="write src/assets/products and public/models under this folder")
    a = ap.parse_args()
    products = json.load(open(os.path.join(ROOT, "src", "data", "products-ambica-source.json"), encoding="utf-8"))
    pallet = {p["slug"]: p["pallet"] for p in products}
    slugs = a.slugs or list(pallet)
    for s in slugs:
        if s not in pallet:
            sys.exit(f"Unknown slug {s!r}")
    glb = a.glb or json.load(open(os.path.join(HERE, "brand.json"), encoding="utf-8")).get("glb", False)
    blender = find_blender(a.blender)
    tmp = os.path.join(HERE, "out")
    os.makedirs(tmp, exist_ok=True)
    for s in slugs:
        t0 = time.time()
        cmd = [blender, "--background", "--factory-startup", "--python", os.path.join(HERE, "render_pallet.py"), "--",
               "--recipe", pallet[s], "--name", s, "--out", tmp, "--res", str(a.res), "--samples", str(a.samples),
               "--views", a.views]
        if glb:
            models = os.path.join(a.out_root, "public", "models")
            os.makedirs(models, exist_ok=True)
            cmd += ["--glb", os.path.join(models, f"{s}.glb")]
        p = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
        for line in p.stdout.splitlines():
            if line.startswith(("DEVICE", "WROTE", "WARNING", "Traceback")) or ("Error" in line and "CUEW" not in line):
                print("  " + line)
        if p.returncode:
            sys.exit(f"{s} failed (exit {p.returncode}); last output:\n" + "\n".join(p.stdout.splitlines()[-25:]))
        dest = os.path.join(a.out_root, "src", "assets", "products", s)
        shutil.rmtree(dest, ignore_errors=True)
        os.makedirs(dest)
        for png in sorted(glob.glob(os.path.join(tmp, f"{s}-[0-9].png"))):
            v = os.path.basename(png)[:-4].rsplit("-", 1)[1]
            subprocess.run([cwebp(), "-quiet", "-q", "90", "-m", "6", png, "-o", os.path.join(dest, f"{v}.webp")], check=True)
        print(f"done {s} ({pallet[s]}) in {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
