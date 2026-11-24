"""Phone versions of the round-5 renders in public/dev/r5/ (the pages pick them on screens up to 900 px wide):
  films   mark, container      every second frame at 800 x 450 -> mark-sm/00.webp ..
  frames  anamorph             every frame at 960 x 540         -> anamorph-sm/
  stills  worlds, xray         1200 x 675                        -> worlds/europe-sm.webp ..

  python tools/render/make_small.py            # everything
  python tools/render/make_small.py film mark  # one

Needs cwebp (Google libwebp): Mac `brew install webp`; Windows: download libwebp from
https://developers.google.com/speed/webp/download, unzip, and put its bin folder on PATH (or set CWEBP).
"""
import glob
import os
import shutil
import subprocess
import sys

DEV = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "public", "dev")
R5 = os.path.join(DEV, "r5")


def dev_dir(name):
    """"mark" means public/dev/r5/mark; a name with a slash ("r6/neem") is relative to public/dev."""
    return os.path.join(DEV, name) if "/" in name else os.path.join(R5, name)


def cwebp():
    c = os.environ.get("CWEBP") or shutil.which("cwebp")
    if not c:
        sys.exit("cwebp not found: see the note at the top of tools/render/make_small.py")
    return c


def conv(src, dst, w, h, q):
    subprocess.run([cwebp(), "-quiet", "-q", str(q), "-resize", str(w), str(h), src, "-o", dst], check=True)


def run(kind, name):
    if kind == "film":
        out = dev_dir(name) + "-sm"
        os.makedirs(out, exist_ok=True)
        for old in glob.glob(os.path.join(out, "*.webp")):   # the frame count may have changed
            os.remove(old)
        evens = [f for f in sorted(glob.glob(os.path.join(dev_dir(name), "*.webp"))) if int(os.path.basename(f)[:-5]) % 2 == 0]
        width = 3 if len(evens) > 100 else 2                    # the page's frame player pads names the same way
        for f in evens:
            n = int(os.path.basename(f)[:-5])
            conv(f, os.path.join(out, f"{n // 2:0{width}d}.webp"), 800, 450, 72)
    elif kind == "frames":
        out = dev_dir(name) + "-sm"
        os.makedirs(out, exist_ok=True)
        for f in sorted(glob.glob(os.path.join(dev_dir(name), "*.webp"))):
            conv(f, os.path.join(out, os.path.basename(f)), 960, 0, 74)   # 960 wide, the same shape
    elif kind == "stills":
        for folder, files, q in (("worlds", ("europe", "india"), 78), ("xray", ("photo", "xray"), 80),
                                 (os.path.join(DEV, "inner"), ("photo", "generic"), 80),
                                 (os.path.join(DEV, "r8", "scenes"), ("still",), 78),
                                 (os.path.join(DEV, "r9"), ("indigo", "plan", "upright", "macro"), 80)):
            for n in files:
                src = os.path.join(R5, folder, f"{n}.webp")     # an absolute folder ignores R5
                if os.path.exists(src):
                    w, h = (1200, 750) if "inner" in folder else (1200, 675)
                    conv(src, os.path.join(R5, folder, f"{n}-sm.webp"), w, h, q)
        out = R5
    else:
        sys.exit(f"unknown kind {kind}")
    print(f"phone versions: {kind} {name} -> {os.path.relpath(out)}")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        run(sys.argv[1], sys.argv[2])
    else:
        for k, n in (("film", "mark"), ("film", "container"), ("frames", "anamorph"), ("stills", "all")):
            run(k, n)
