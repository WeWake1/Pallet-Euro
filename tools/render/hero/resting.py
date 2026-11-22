"""PROTOTYPE round 4 · "Resting": an EPAL 1 seen almost face-on, on a transparent background, so the page
can set it down on the headline. Two layers: the pallet, and its soft contact shadow (shadow catcher).
Lit with the approved catalogue studio (overhead softbox, key, fill, rim).

  Blender -b --factory-startup --python tools/render/hero/resting.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/r4/resting --size 2400x760
Writes pallet.png, shadow.png (convert: cwebp -q 88 -alpha_q 100 -exact) and frame.json (where the pallet's bottom edge sits, in 0..1 of the image).
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import bpy  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Vector  # noqa: E402
import numpy as np  # noqa: E402

C.setup_cycles(view="Standard", exposure=0.0, transparent=True)
C.scene.render.film_transparent = True

L, Wd, Ht = (v * 0.001 for v in C.pk.R["dims"])
C.build_pallet(rot_deg=0)
catcher = C.plane("catcher", 20, 20, material=C.mat("catcher", "#FFFFFF", rough=0.9))
catcher.is_shadow_catcher = True

C.world("#F4F4F4", 0.45)
C.area("top", (0.0, -0.3, 3.0), 4.0, 420, look=(0, 0, 0.07))       # the catalogue studio (render_pallet.py)
C.area("key", (-2.2, -2.6, 3.4), 3.5, 150, look=(0, 0, 0.07))
C.area("fill", (3.0, -1.6, 1.8), 3.0, 35, look=(0, 0, 0.07))
C.area("rim", (0.8, 3.2, 2.4), 2.5, 80, look=(0, 0, 0.07))

ELEV, AZIM = math.radians(9.0), math.radians(-7.0)       # nearly face-on: the bottom edge stays level
cam = C.camera(lens=105)
d = Vector((math.sin(AZIM) * math.cos(ELEV), -math.cos(AZIM) * math.cos(ELEV), math.sin(ELEV)))
centre = Vector((0, 0, Ht / 2))
corners = [Vector((sx * L / 2, sy * Wd / 2, z)) for sx in (-1, 1) for sy in (-1, 1) for z in (0, Ht)]


def place(dist):
    cam.location = centre + d * dist
    C.look_at(cam, centre)
    bpy.context.view_layer.update()
    return [world_to_camera_view(C.scene, cam, p) for p in corners]


lo, hi = 1.0, 60.0                         # fit the pallet to 84 % of the width
for _ in range(50):
    mid = (lo + hi) / 2
    pts = place(mid)
    span = max(p.x for p in pts) - min(p.x for p in pts)
    lo, hi = (mid, hi) if span > 0.84 else (lo, mid)
pts = place(hi)
xs, ys = [p.x for p in pts], [p.y for p in pts]
cam.data.shift_x = ((max(xs) + min(xs)) / 2 - 0.5) * 1.0
cam.data.shift_y = ((max(ys) + min(ys)) / 2 - 0.5) * C.H / C.W
bpy.context.view_layer.update()
pts = [world_to_camera_view(C.scene, cam, p) for p in corners]
front_bottom = [p for p, c in zip(pts, corners) if c.z == 0 and c.y < 0]

pallet_obs = [ob for ob, _ in C.pk.OBJECTS]
out = C.args.out


def render_clean(name):
    """RGBA PNG with the denoiser's near-zero alpha set to exactly 0 (otherwise the page shows a faint box).
    The shell converts it to WebP afterwards (cwebp)."""
    png = os.path.join(out, name + ".png")
    st = C.scene.render.image_settings
    st.file_format, st.color_mode, st.color_depth = "PNG", "RGBA", "8"
    C.scene.render.filepath = png
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(png)
    a = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)
    al = a[..., 3]
    al[al < 0.025] = 0.0
    if name == "shadow":
        # the catcher also records a very faint, wide occlusion: fade it out well inside the image edges
        h, w = al.shape
        yy, xx = np.mgrid[0:h, 0:w]
        ex = np.clip(np.minimum(xx, w - 1 - xx) / (0.07 * w), 0, 1)
        ey = np.clip(np.minimum(yy, h - 1 - yy) / (0.16 * h), 0, 1)
        fall = (ex * ey) ** 1.5
        al *= fall * fall * (3 - 2 * fall)   # smoothstep
        al[al < 0.02] = 0.0
    a[..., 3] = al
    a[..., :3][al == 0] = 1.0   # fully transparent pixels white: any edge bleed is then invisible on the page
    img.pixels.foreach_set(a.ravel())
    img.filepath_raw = png
    img.save()
    bpy.data.images.remove(img)
    print("WROTE", png, flush=True)

# 1) the pallet alone: the floor still bounces light onto it, but the camera does not see the floor
catcher.visible_camera = False
render_clean("pallet")
# 2) the shadow alone: the pallet still casts, but the camera does not see it
catcher.visible_camera = True
for ob in pallet_obs:
    ob.visible_camera = False
render_clean("shadow")

meta = {
    "w": C.W, "h": C.H,
    "bottom_y": 1 - min(p.y for p in front_bottom),       # image space, 0 = top
    "left_x": min(p.x for p in pts), "right_x": max(p.x for p in pts),
    "top_y": 1 - max(p.y for p in pts),
}
json.dump(meta, open(os.path.join(out, "frame.json"), "w"), indent=1)
print("META", meta)
