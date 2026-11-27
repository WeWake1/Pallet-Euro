"""Render the round-5 prototype scenes with the settings they were made with, on a Mac or a Windows/Linux PC.

  python tools/render/run.py --list
  python tools/render/run.py mark                 # one scene, then its phone versions
  python tools/render/run.py europe india xray     # several, one after another (one Blender at a time is fastest)
  python tools/render/run.py all
  python tools/render/run.py mark --test --frames 0,26,72,114,167   # quick check: half size, 24 samples, into .render-test/

Options: --frames 0-47|0,12   --samples N   --device auto|HIP|OPTIX|CUDA|METAL|CPU   --no-small   --blender PATH
Blender: --blender, else env BLENDER, else the usual install folder for this OS, else `blender` on PATH.
Phone versions (every second film frame at 800 px, hero frames at 960 px, stills at 1200 px) need cwebp:
see tools/render/make_small.py. Run from anywhere; paths are relative to the repo root.
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERO = os.path.join("tools", "render", "hero")
BASE = ["--recipe", "epal1", "--recipes", os.path.join("src", "data", "pallet-geometry.json")]

# name: (script, output folder, size, samples, webp quality, extra flags, phone-version kind)
PRESETS = {
    "mark":       ("mark.py",      "public/dev/r5/mark",      "1600x900",  48,  80, [], "film"),
    "container":  ("container.py", "public/dev/r5/container", "1600x900",  32,  80, [], "film"),
    "anamorph":   ("anamorph.py",  "public/dev/r5/anamorph",  "1920x1080", 40,  80, [], "frames"),
    "europe":     ("europe.py",    "public/dev/r5/worlds",    "2400x1350", 128, 84, [], "stills"),
    "india":      ("jaali.py",     "public/dev/r5/worlds",    "2400x1350", 128, 84, ["--frames", "24"], "stills"),
    "xray-photo": ("xray.py",      "public/dev/r5/xray",      "2400x1350", 128, 86, ["--pass", "photo"], "stills"),
    "xray-xray":  ("xray.py",      "public/dev/r5/xray",      "2400x1350", 128, 86, ["--pass", "xray"], "stills"),
    "xray-ids":   ("xray.py",      "public/dev/r5/xray",      "2400x1350", 1,   86, ["--pass", "ids"], None),
    # round 6 heroes
    "daybreak":   ("daybreak.py",  "public/dev/r6/daybreak",  "1920x1080", 64,  82, [], "frames"),
    "neem":       ("neem.py",      "public/dev/r6/neem",      "1920x1080", 64,  82, [], "frames"),
    "bullettime": ("bullettime.py", "public/dev/r6/bullettime", "1920x1080", 48, 82, [], "frames"),
    # round 7 heroes (blueprint: run.py lays its ink lines over the photos with compose_lines.py)
    "blueprint":  ("blueprint.py", "public/dev/r7/blueprint", "1920x1080", 64,  82, [], "frames"),
    "frieze":     ("frieze.py",    "public/dev/r7/frieze",    "1920x1080", 64,  82, [], "frames"),
    "carved":     ("carved.py",    "public/dev/r7/carved",    "1920x1080", 64,  82, [], "frames"),
    # inner pages: the part inspector (photo + ID map) and the before/after (generic worn pallet + photo)
    "inner-photo":   ("inspect.py", "public/dev/inner", "1920x1200", 128, 86, ["--pass", "photo"], "stills"),
    "inner-generic": ("inspect.py", "public/dev/inner", "1920x1200", 128, 86, ["--pass", "generic"], "stills"),
    "inner-ids":     ("inspect.py", "public/dev/inner", "1920x1200", 1,   86, ["--pass", "ids"], None),
    # round 8 (layers.py: one pallet in its layers) and the anatomy guide
    "r8-explode":    ("layers.py", "public/dev/r8/explode", "1920x1080", 64, 82, ["--job", "explode"], "frames"),
    "r8-asm-epal1":  ("layers.py", "public/dev/r8/assemble/epal1", "1920x1080", 48, 82, ["--job", "assemble", "--recipe", "epal1"], "frames"),
    "r8-asm-epal2":  ("layers.py", "public/dev/r8/assemble/epal2", "1920x1080", 48, 82, ["--job", "assemble", "--recipe", "epal2"], "frames"),
    "r8-asm-epal3":  ("layers.py", "public/dev/r8/assemble/epal3", "1920x1080", 48, 82, ["--job", "assemble", "--recipe", "epal3"], "frames"),
    "r8-asm-cp1":    ("layers.py", "public/dev/r8/assemble/cp1", "1920x1080", 48, 82, ["--job", "assemble", "--recipe", "cp1"], "frames"),
    "anatomy-film":  ("layers.py", "public/dev/inner/anatomy/film", "1600x1000", 64, 82, ["--job", "film"], "frames"),
    "anatomy-orbit": ("layers.py", "public/dev/inner/anatomy/orbit", "1600x1000", 64, 82, ["--job", "orbit"], "frames"),
    "anatomy-ids":   ("layers.py", "tools/render/out/anatomy-ids", "1600x1000", 1, 86, ["--job", "orbit-ids"], None),
    "r8-container":  ("container.py", "public/dev/r8/scenes", "2400x1350", 48, 84, ["--still"], "stills"),
    "r8-glide":      ("jaali.py", "public/dev/r8/glide", "1920x1080", 64, 82, ["--glide"], "frames"),
    # round 9: four stills (r9.py --scene)
    "r9-indigo":     ("r9.py", "public/dev/r9", "2400x1350", 128, 86, ["--scene", "indigo"], "stills"),
    "r9-plan":       ("r9.py", "public/dev/r9", "2400x1350", 128, 86, ["--scene", "plan"], "stills"),
    "r9-upright":    ("r9.py", "public/dev/r9", "2400x1350", 128, 86, ["--scene", "upright"], "stills"),
    "r9-macro":      ("r9.py", "public/dev/r9", "2400x1350", 128, 86, ["--scene", "macro"], "stills"),
    # round 10 (r10.py; the eleven loads in loads.py)
    "r10-industries": ("r10.py", "public/dev/r10/industries", "1920x1080", 48, 80, ["--job", "industries"], "frames"),
    "r10-lift":       ("r10.py", "public/dev/r10/lift", "1920x1080", 32, 80, ["--job", "lift"], "frames"),
    "r10-delivery":   ("r10.py", "public/dev/r10/delivery", "1920x1080", 48, 84, ["--job", "delivery"], None),
    # round 11: six seamless loops (r11.py --job; opening.py)
    "r11-sliced":     ("r11.py", "public/dev/r11/sliced", "1920x1080", 48, 80, ["--job", "sliced"], "frames"),
    "r11-fit":        ("r11.py", "public/dev/r11/fit", "1920x1080", 48, 80, ["--job", "fit"], "frames"),
    "r11-infinity":   ("r11.py", "public/dev/r11/infinity", "1920x1080", 64, 80, ["--job", "infinity"], "frames"),
    "r11-silk":       ("r11.py", "public/dev/r11/silk", "1920x1080", 48, 80, ["--job", "silk"], "frames"),
    "r11-dominoes":   ("r11.py", "public/dev/r11/dominoes", "1920x1080", 48, 80, ["--job", "dominoes"], "frames"),
    # D "Through the opening": one run per place and pass into tools/render/out/opening, then opening_comp.py
    **{f"r11-open-{pl}-{ps}": ("opening.py", "tools/render/out/opening", "1920x1080", 40, 90, ["--place", pl, "--pass", ps], None)
       for ps in ("seg", "portal", "portal2") for pl in ("factory", "india", "port", "europe")},
}
GROUPS = {"xray": ["xray-photo", "xray-xray", "xray-ids"], "worlds": ["europe", "india"],
          "r6": ["daybreak", "neem", "bullettime"], "r7": ["blueprint", "frieze", "carved"],
          "inner": ["inner-photo", "inner-generic", "inner-ids"],
          "r8-layers": ["r8-explode", "r8-asm-epal1", "r8-asm-epal2", "r8-asm-epal3", "r8-asm-cp1"],
          "anatomy": ["anatomy-film", "anatomy-orbit", "anatomy-ids"], "r8-more": ["r8-container", "r8-glide"],
          "r9": ["r9-indigo", "r9-plan", "r9-upright", "r9-macro"],
          "r11": ["r11-sliced", "r11-fit", "r11-infinity", "r11-silk", "r11-dominoes"],
          "r11-opening": [f"r11-open-{pl}-{ps}" for ps in ("seg", "portal", "portal2") for pl in ("factory", "india", "port", "europe")],
          "all": list(PRESETS)}


def find_blender(given):
    for c in (given, os.environ.get("BLENDER")):
        if c:
            return c
    if sys.platform == "darwin":
        c = "/Applications/Blender.app/Contents/MacOS/Blender"
        if os.path.exists(c):
            return c
    if os.name == "nt":
        found = sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe"))
        if found:
            return found[-1]
    c = shutil.which("blender")
    if c:
        return c
    sys.exit("Blender not found: install Blender 5.x, or pass --blender PATH, or set BLENDER.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenes", nargs="*")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--test", action="store_true", help="half size, 24 samples, output in .render-test/")
    ap.add_argument("--frames", default="")
    ap.add_argument("--samples", type=int)
    ap.add_argument("--device", default="")
    ap.add_argument("--no-small", action="store_true")
    ap.add_argument("--blender")
    a = ap.parse_args()
    if a.list or not a.scenes:
        for k, (script, out, size, spp, q, extra, small) in PRESETS.items():
            print(f"{k:11} {script:13} -> {out:26} {size:9} {spp:>3} spp  {' '.join(extra)}")
        print("groups:", ", ".join(f"{g} = {' '.join(v)}" for g, v in GROUPS.items() if g != "all"), ", all")
        return
    names = []
    for s in a.scenes:
        for n in GROUPS.get(s, [s]):
            if n not in PRESETS:
                sys.exit(f"Unknown scene {n!r}; see --list")
            if n not in names:
                names.append(n)
    blender = find_blender(a.blender)
    print("Blender:", blender)
    smalls = set()
    for n in names:
        script, out, size, spp, q, extra, small = PRESETS[n]
        if a.test:
            out = os.path.join(".render-test", n)
        if a.frames:
            extra = [x for i, x in enumerate(extra) if not (x == "--frames" or (i and extra[i - 1] == "--frames"))]
            extra += ["--frames", a.frames]
        cmd = [blender, "-b", "--factory-startup", "--python", os.path.join(HERO, script), "--", *BASE,
               "--out", out, "--size", size, "--samples", str(a.samples or spp), "--quality", str(q), *extra]
        if a.test:
            cmd.append("--test")
        if a.device:
            cmd += ["--device", a.device]
        print(f"\n== {n}: {' '.join(cmd[1:])}", flush=True)
        t0 = time.time()
        p = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
        for line in p.stdout.splitlines():
            if "CUEW" in line:   # Windows without an NVIDIA card: Blender cannot load CUDA (harmless)
                continue
            if line.startswith(("DEVICE", "WARNING", "WROTE", "Traceback", "SCREEN")) or "Error" in line:
                print("  " + line.replace(ROOT + os.sep, ""))
        if p.returncode:
            sys.exit(f"{n} failed (exit {p.returncode}); last output:\n" + "\n".join(p.stdout.splitlines()[-25:]))
        if os.path.isdir(os.path.join(ROOT, out, "_raw")):   # ink lines rendered apart (blueprint.py)
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import compose_lines
            compose_lines.run(os.path.join(ROOT, out), q)
        if n == "india" and not a.test:   # jaali.py names its frame by number
            src, dst = os.path.join(ROOT, out, "24.webp"), os.path.join(ROOT, out, "india.webp")
            if os.path.exists(src):
                os.replace(src, dst)
        print(f"   {n} done in {time.time() - t0:.0f} s", flush=True)
        if small and not a.test and not a.no_small and not a.frames:
            smalls.add((small, os.path.basename(out) if "/r5/" in out else out.split("public/dev/")[1]))
    if any(n.startswith("r11-open-") for n in names):   # lay the seg frames over their portals
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "hero"))
        import opening_comp
        opening_comp.run(test=a.test)
        if not a.test and not a.no_small and not a.frames:
            smalls.add(("frames", "r11/opening"))
    if smalls:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import make_small
        for kind, name in sorted(smalls):
            make_small.run(kind, name)


if __name__ == "__main__":
    main()
