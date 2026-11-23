"""PROTOTYPE round 6 · B "Neem shade": an EPAL 1 in a sunlit lime-plaster courtyard (the calm of round 4's
Indian light), under a neem tree the camera never sees. Its dappled shade moves gently in a breeze over the
wall, the stone floor and the pallet. The left of the picture (behind the headline) lies in calm open shade.
A seamless loop: frame COUNT would equal frame 0.

  Blender -b --factory-startup --python tools/render/hero/neem.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/r6/neem [--frames 0-47] [--test]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

COUNT = 48
C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.25)


# ------------------------------------------------------------------ neem canopy (procedural, tileable mask)
def canopy(seed, n=2048, clusters=64, per_cluster=(16, 30), tile_m=3.0):
    """Clusters of pinnate neem leaves (9-15 slim, slightly curved leaflets each) with open gaps between the
    clusters for the sun flecks. 1 = leaf. Drawn on a padded canvas and folded back so it tiles."""
    rng = np.random.default_rng(seed)
    px = n / tile_m                                    # pixels per metre
    P = 80
    can = np.zeros((n + 2 * P, n + 2 * P), np.float32)

    def leaflet(cx, cy, ang, ln, wd):
        r = int(ln) + 2
        x0, y0 = int(cx) - r, int(cy) - r
        if x0 < 0 or y0 < 0 or x0 + 2 * r >= can.shape[1] or y0 + 2 * r >= can.shape[0]:
            return
        ys, xs = np.mgrid[y0:y0 + 2 * r, x0:x0 + 2 * r]
        dx, dy = xs - cx, ys - cy
        u = dx * math.cos(ang) + dy * math.sin(ang)
        v = -dx * math.sin(ang) + dy * math.cos(ang)
        v = v - 0.18 * wd * (u / ln) ** 2 * 4               # a slight sickle curve
        q = np.sqrt((u / ln) ** 2 + (v / wd) ** 2)
        a = np.clip((1 - q) * wd * 0.9 + 0.5, 0, 1)
        sl = can[y0:y0 + 2 * r, x0:x0 + 2 * r]
        np.maximum(sl, a, out=sl)

    for _ in range(clusters):
        ccx, ccy = rng.uniform(P, n + P), rng.uniform(P, n + P)
        for _ in range(rng.integers(*per_cluster)):
            ang = rng.uniform(0, 2 * math.pi)
            dist = rng.uniform(0, 0.16) * px
            sx, sy = ccx + math.cos(ang) * dist, ccy + math.sin(ang) * dist
            L = rng.uniform(0.16, 0.28) * px                 # rachis 16-28 cm
            bend = rng.uniform(-0.35, 0.35)
            k = int(rng.integers(9, 16))
            for j in range(k):
                s = (j + 0.6) / k
                a0 = ang + bend * s
                x, y = sx + math.cos(a0) * L * s, sy + math.sin(a0) * L * s
                side = 1 if j % 2 else -1
                la = a0 + side * rng.uniform(0.75, 1.1)
                ln = rng.uniform(0.028, 0.040) * px * (1 - 0.45 * abs(s - 0.55))
                leaflet(x + math.cos(la) * ln * 0.9, y + math.sin(la) * ln * 0.9, la, ln, ln * 0.24)
            leaflet(sx + math.cos(ang + bend) * (L + 0.02 * px), sy + math.sin(ang + bend) * (L + 0.02 * px),
                    ang + bend, 0.03 * px, 0.008 * px)
    # fold the padding back so the tile repeats without seams
    out = can[P:P + n, P:P + n].copy()
    np.maximum(out[:P, :], can[n + P:, P:P + n], out=out[:P, :])
    np.maximum(out[-P:, :], can[:P, P:P + n], out=out[-P:, :])
    np.maximum(out[:, :P], can[P:P + n, n + P:], out=out[:, :P])
    np.maximum(out[:, -P:], can[P:P + n, :P], out=out[:, -P:])
    return out


# ------------------------------------------------------------------ courtyard: stone floor, lime-plaster wall
C.plane("floor", 24, 24, material=C.stone_floor())
WALL_Y = 1.45
wall = C.plaster("#EEE7DC", "#F6F2EB")
C.plane("back_wall", 24, 6, loc=(0, WALL_Y, 3.0), rot=(math.radians(90), 0, 0), material=wall)
C.plane("plinth_gap", 24, 0.012, loc=(0, WALL_Y + 0.01, 0.006), rot=(math.radians(90), 0, 0), material=wall)

PALLET = Vector((0.32, 0.12, 0.0))
C.build_pallet(rot_deg=-18, loc=PALLET)
C.world("#E6E6E8", 0.85)                                   # open sky plus warm bounce from the sunlit court
sun = C.sun("sun", 7.5, color="#FFE6C4", angle_deg=0.35)
EL, AZ = 46.0, 52.0                                        # high late-morning sun from the front left
C.aim_sun(sun, elev_deg=EL, azim_deg=AZ)
C.area("bounce", (1.8, -0.6, 3.4), 3.0, 40, color="#FFF4E6", look=(0, 0, 0))

el, az = math.radians(EL), math.radians(AZ)
to_sun = Vector((-math.cos(el) * math.cos(az), -math.cos(el) * math.sin(az), math.sin(el)))
rot = to_sun.to_track_quat("Z", "Y")
AIM = PALLET + Vector((0.35, 0.45, 0.25))                  # where the canopy's light falls: pallet and wall behind

# two canopy layers at different heights (near: crisp leaves; far: soft flecks)
LAYERS = []
for i, (dist, size, seed, amp, dense) in enumerate([(2.2, 7.0, 11, 0.55, 34), (4.2, 9.0, 29, 0.35, 40)]):
    img = C.save_mask(f"neem_canopy_{i}", canopy(seed, clusters=dense))
    ob = C.plane(f"canopy_{i}", size, size, material=C.gobo_material(img, size, size, tile=3.0, offset=(0.13 * i, 0.31 * i)))
    C.shadow_only(ob)
    LAYERS.append((ob, AIM + to_sun * dist, amp, i))

# open shade on the left (behind the headline): the dense heart of the tree, with a ragged leafy edge
SW = 6.0
edge = canopy(53, clusters=150, per_cluster=(20, 34))
ramp = np.clip((0.62 - (np.arange(2048) + 0.5) / 2048) / 0.22, 0, 1)[None, :]   # solid on the left, leaves at the edge
shade_mask = np.maximum(ramp ** 1.5, edge * np.clip(ramp * 3.0, 0, 1))
shade = C.plane("shade", SW, SW, material=C.gobo_material(C.save_mask("neem_shade", shade_mask), SW, SW, tile=SW))
C.shadow_only(shade)
shade.rotation_euler = rot.to_euler()
shade.location = AIM + to_sun * 3.0 + rot @ Vector((-2.3, 0, 0))

cam = C.camera(lens=50)
cam.location = (2.2, -4.25, 1.05)
C.look_at(cam, (0.62, 0.35, 0.2))
cam.data.shift_x = -0.25
cam.data.shift_y = 0.03
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = (cam.location - PALLET).length
cam.data.dof.aperture_fstop = 2.8

for f in C.frame_list(COUNT):
    t = f / COUNT                                          # 0..1, loops
    for ob, centre, amp, i in LAYERS:
        ph = 1.7 * i
        sway = math.radians(amp) * (math.sin(2 * math.pi * t + ph) + 0.45 * math.sin(4 * math.pi * t + 2 * ph))
        drift = 0.018 * math.sin(2 * math.pi * t + ph + 0.8)
        pivot = rot @ Vector((2.5, 2.0, 0))                 # sways about the branch it hangs from
        R = rot.to_matrix().to_4x4() @ Matrix.Rotation(sway, 4, "Z")
        ob.matrix_world = Matrix.Translation(centre + pivot - (R.to_3x3() @ (rot.inverted() @ pivot)) + rot @ Vector((drift, 0, 0))) @ R
    C.render_to(os.path.join(C.args.out, f"{f:02d}.webp"))
