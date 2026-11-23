"""PROTOTYPE round 6 Â· A "Daybreak": one EPAL 1 in a white seamless studio (the simplicity of round 2's studio
hero) under a real sun that travels a whole day: sunrise low on the left (warm, long shadow), noon high behind
(short shadow, neutral light), sunset low on the right. One frame per sun position; the page scrubs them
(the cursor carries the sun across on computers, slow drift on phones).

  Blender -b --factory-startup --python tools/render/hero/daybreak.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/r6/daybreak [--frames 0-47] [--test]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from mathutils import Vector  # noqa: E402

COUNT = 48
C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.35)
C.seamless_studio(bg="#FFFFFF", floor="#F4F2EE", fade=(4.4, 9.0), fill="#D6E1F4", fill_strength=0.9, rough=0.7,
                  bg_strength=1.12)

PALLET = Vector((0.62, 0.32, 0.0))
C.build_pallet(rot_deg=-24, loc=PALLET)
sun = C.sun("sun", 7.0, angle_deg=1.2)
C.area("fill", (-1.8, -3.4, 2.4), 5.0, 60, color="#F6F7FF", look=(0.6, 0.3, 0.1))

cam = C.camera(lens=46)                  # framed for the headline: the pallet keeps to the right ~55% of the picture
cam.location = (1.38, -3.15, 1.3)
C.look_at(cam, (0.84, 0.24, 0.08))
cam.data.shift_x = -0.27
cam.data.shift_y = 0.02
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = (cam.location - PALLET).length
cam.data.dof.aperture_fstop = 4.0

WARM, NOON = C.srgb("#FFC690"), C.srgb("#FFF4E6")
for f in C.frame_list(COUNT):
    t = f / (COUNT - 1)
    h = math.sin(math.pi * t)                       # 0 at sunrise and sunset, 1 at noon
    C.aim_sun(sun, elev_deg=7.0 + 38.0 * h, azim_deg=12.0 - 204.0 * t)   # left, over the back, to the right
    k = h ** 0.6
    sun.data.color = tuple(WARM[i] + (NOON[i] - WARM[i]) * k for i in range(3))
    sun.data.energy = 5.5 + 3.0 * k
    C.render_to(os.path.join(C.args.out, f"{f:02d}.webp"))
