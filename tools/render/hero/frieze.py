"""PROTOTYPE round 7 · B "Eye level": the camera lies on the floor of a sunlit sandstone courtyard, a hand's
height up, close to the long side of one EPAL 1. The pallet becomes architecture: a long low frieze across the
lower part of the picture, its three blocks (EPAL oval, IPPC, EPAL oval) facing the camera, the fork openings
like doorways to the light beyond; behind it, out of focus, a row of pointed arches. Each frame moves the camera
a little along the pallet (parallax through the openings); the page scrubs them with the cursor.

  Blender -b --factory-startup --python tools/render/hero/frieze.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/r7/frieze [--frames 0-40] [--test]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

COUNT = 41
C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=-0.15)
scene = C.scene

C.build_pallet(rot_deg=0, loc=(0, 0, 0))          # long side along X, facing the camera (-Y)
floor = C.plane("floor", 40, 40, material=C.stone_floor("#EFE6D8", "#E8DDCB", "#CDBFA8", slab=(0.9, 0.9)))
C.world("#F3EEE6", 2.1)                            # a warm bright sky, glowing through the arches


def arch_prisms(name, centres, width, spring, y0, y1, steps=14, point=0.32):
    """Pointed (two-centred) arch openings as prisms from y0 to y1, one per x in centres."""
    bm = bmesh.new()
    half = width / 2
    c = point * half                           # each arc's centre sits this far past the middle
    rad = half + c
    apex = math.sqrt(rad * rad - c * c)
    for cx in centres:
        pts = [(cx - half, -0.5), (cx + half, -0.5)]
        a1 = math.atan2(apex, c)                # right arc, centred at cx - c: from the right jamb up to the apex
        for i in range(steps + 1):
            a = a1 * i / steps
            pts.append((cx - c + rad * math.cos(a), spring + rad * math.sin(a)))
        for i in range(1, steps + 1):           # left arc, centred at cx + c: from the apex down to the left jamb
            a = math.pi - a1 + a1 * i / steps
            pts.append((cx + c + rad * math.cos(a), spring + rad * math.sin(a)))
        front = [bm.verts.new((x, y0, z)) for x, z in pts]
        back = [bm.verts.new((x, y1, z)) for x, z in pts]
        bm.faces.new(front[::-1])
        bm.faces.new(back)
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((front[i], front[j], back[j], back[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


def wall(name, x0, x1, y0, y1, height, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, height / 2))
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (x1 - x0, y1 - y0, height)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(material)
    return ob


sand = C.plaster("#E9D6B8", "#F1E3CB")              # honey sandstone, sunlit
arcade = wall("arcade", -12, 12, 7.6, 8.1, 5.2, sand)
cut = arch_prisms("arches", [x * 2.5 for x in range(-5, 6)], 1.5, 2.0, 7.4, 8.3)
bo = arcade.modifiers.new("arches", "BOOLEAN")
bo.operation, bo.solver, bo.object = "DIFFERENCE", "EXACT", cut
cut.hide_render = True
cut.hide_viewport = True

sun = C.sun("sun", 6.0, color="#FFE9CC", angle_deg=0.8)
C.aim_sun(sun, elev_deg=34, azim_deg=-40)
fill = C.area("fill", (-0.2, -3.2, 0.7), 3.0, 90, color="#F4F6FF", look=(0, 0, 0.07))
fill.visible_camera = False

cam = C.camera(lens=30)
cam.data.shift_x = -0.10
cam.data.shift_y = 0.12
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 2.2
YAW = math.radians(-14)

for f in C.frame_list(COUNT):
    t = f / (COUNT - 1)
    cam.location = (-0.78 + 0.16 * t, -1.35, 0.062)
    cam.rotation_euler = (math.radians(90.5), 0, YAW)
    cam.data.dof.focus_distance = 1.0
    C.render_to(os.path.join(C.args.out, f"{f:02d}.webp"))
