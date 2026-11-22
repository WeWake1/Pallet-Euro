"""PROTOTYPE round 5 · "In its place": an anamorphic installation in a white gallery. The EPAL 1's 20 wooden
parts (with their nails and marks) hang on fine steel wires at very different depths, each scaled about the
viewer's eye so that from one spot, and only one, they line up into the exact pallet. One frame per camera
angle on an orbit of +/-24 deg; frame 30 is the sweet spot. The page eases into it on load (the pallet
"assembles") and pushes the camera off it when the cursor moves (the pallet comes apart, then settles).

  Blender -b --factory-startup --python tools/render/hero/anamorph.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/r5/anamorph [--frames 0-60] [--test]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

pk = C.pk
scene = C.scene
COUNT, SWEET, SWING = 61, 30, 24.0
C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=-1.25)

# ------------------------------------------------------------------ the pallet as seen from the sweet spot
P0 = Vector((0.0, 0.0, 1.32))                   # where the pallet appears to float
DIST, ELEV, AZ0 = 4.4, math.radians(10.0), math.radians(32.0)
C0 = P0 + Vector((math.sin(AZ0) * math.cos(ELEV), -math.cos(AZ0) * math.cos(ELEV), math.sin(ELEV))) * DIST

C.build_pallet(rot_deg=0, loc=(0, 0, 0))
pk.ROOT.location = P0 - Vector((0, 0, 0.072))
pk.ROOT.rotation_euler = (math.radians(13), 0, math.radians(-16))   # tilted toward the eye, so the deck shows
bpy.context.view_layer.update()

woods = [o for o, k in pk.OBJECTS if k == "wood"]
others = [o for o, k in pk.OBJECTS if k != "wood"]


def local_box(ob):
    vs = [ob.matrix_local @ v.co for v in ob.data.vertices]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return lo, hi


boxes = {o.name: local_box(o) for o in woods}


def host_of(ob):
    if ob.type == "MESH" and ob.name.startswith("decal"):
        p = sum((ob.matrix_local @ v.co for v in ob.data.vertices), Vector()) / len(ob.data.vertices)
    else:
        p = ob.matrix_local.translation
    best, bd = None, 1e9
    for w in woods:
        lo, hi = boxes[w.name]
        d = max(lo.x - p.x, p.x - hi.x, lo.y - p.y, p.y - hi.y, lo.z - p.z, p.z - hi.z, 0.0)
        if d < bd:
            best, bd = w, d
    return best


# Depth order must survive the scaling, or a part pulled toward the eye shows through one that should hide it:
# deck boards come closest, then the stringer boards, the blocks, and the bottom boards farthest; within a
# layer, front to back. From the sweet spot the pallet is exact; off it, the layers fan out like an exploded drawing.
LAYERS = {"top": (0.58, 0.76), "cross": (0.86, 1.0), "block": (1.08, 1.42), "bottom": (1.52, 1.82)}
role = {p["name"]: p["role"] for p in pk.R["parts"]}
S = {}
for r, (lo_s, hi_s) in LAYERS.items():
    layer = sorted((w for w in woods if role[w.name.split(".")[0]] == r), key=lambda w: (w.matrix_world.translation - C0).length)
    for i, w in enumerate(layer):
        S[w.name] = lo_s + (hi_s - lo_s) * (i / max(len(layer) - 1, 1))


def about_eye(s):
    return Matrix.Translation(C0) @ Matrix.Scale(s, 4) @ Matrix.Translation(-C0)


world_before = {o.name: o.matrix_world.copy() for o in woods + others}
hosts = {o.name: host_of(o) for o in others}
attach = []
for w in woods:
    lo, hi = boxes[w.name]
    long_x = (hi.x - lo.x) >= (hi.y - lo.y)
    pts = []
    for f in (0.22, 0.78):
        if long_x:
            pts.append(Vector((lo.x + f * (hi.x - lo.x), (lo.y + hi.y) / 2, hi.z)))
        else:
            pts.append(Vector(((lo.x + hi.x) / 2, lo.y + f * (hi.y - lo.y), hi.z)))
    attach.append((w, pts))
for o in woods:
    o.matrix_world = about_eye(S[o.name]) @ world_before[o.name]
for o in others:
    o.matrix_world = about_eye(S[hosts[o.name].name]) @ world_before[o.name]
bpy.context.view_layer.update()

# fine steel wires from each part up to the ceiling
wire_m = pk.plain_material("wire", "#5E6266", metallic=1.0, roughness=0.3)
CEIL = 5.6
for w, pts in attach:
    M = about_eye(S[w.name]) @ pk.ROOT.matrix_world
    for p in pts:
        a = M @ p
        bpy.ops.mesh.primitive_cylinder_add(radius=0.00045, depth=CEIL - a.z, vertices=6,
                                            location=(a.x, a.y, (a.z + CEIL) / 2))
        bpy.context.active_object.data.materials.append(wire_m)


# ------------------------------------------------------------------ the gallery
def plaster(hexcol, rough=0.9):
    m = bpy.data.materials.new("plaster")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.2
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.6; nz.inputs["Detail"].default_value = 4.0
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*(Vector(C.srgb(hexcol)) * 0.965), 1)
    ramp.color_ramp.elements[1].color = (*C.srgb(hexcol), 1)
    l.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    l.new(ramp.outputs["Color"], b.inputs["Base Color"])
    fine = n.new("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 140.0; fine.inputs["Detail"].default_value = 8.0
    bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.1
    l.new(fine.outputs["Fac"], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def polished_concrete():
    m = bpy.data.materials.new("gallery_floor")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Specular IOR Level"].default_value = 0.5
    tc = n.new("ShaderNodeTexCoord")
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.9; nz.inputs["Detail"].default_value = 12.0
    l.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*C.srgb("#CFCDC8"), 1)
    ramp.color_ramp.elements[1].color = (*C.srgb("#E2E0DB"), 1)
    l.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    l.new(ramp.outputs["Color"], b.inputs["Base Color"])
    rr = n.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = 0.16, 0.34
    l.new(nz.outputs["Fac"], rr.inputs["Value"])
    l.new(rr.outputs[0], b.inputs["Roughness"])
    fine = n.new("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 500.0
    l.new(tc.outputs["Object"], fine.inputs["Vector"])
    bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.04
    l.new(fine.outputs["Fac"], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


WALL = plaster("#F3F1ED")
C.plane("floor", 30, 30, material=polished_concrete())
C.plane("back_wall", 30, 7, loc=(0, 6.0, 3.5), rot=(math.radians(90), 0, 0), material=WALL)
C.plane("left_wall", 30, 7, loc=(-6.5, 0, 3.5), rot=(math.radians(90), 0, math.radians(-90)), material=WALL)
C.plane("right_wall", 30, 7, loc=(9.0, 0, 3.5), rot=(math.radians(90), 0, math.radians(90)), material=WALL)
C.plane("front_wall", 30, 7, loc=(0, -9.0, 3.5), rot=(math.radians(90), 0, math.radians(180)), material=WALL)
C.plane("ceiling", 30, 30, loc=(0, 0, CEIL + 0.05), rot=(math.radians(180), 0, 0), material=plaster("#F6F5F2"))
for (x, y, rz) in ((0, 6.0 - 0.012, 0), (-6.5 + 0.012, 0, -90), (9.0 - 0.012, 0, 90)):   # shadow gap at the floor
    C.plane("gap", 30, 0.016, loc=(x, y, 0.008), rot=(math.radians(90), 0, math.radians(rz)), material=C.mat("gap", "#A9A6A0", 0.8))

C.world("#EFEFEC", 0.35)
C.area("skylight", (0.4, 0.6, CEIL - 0.02), 4.2, 1300, color="#FFF8F0", look=(0.4, 0.6, 0))
C.area("window", (-6.4, -1.0, 2.6), 3.2, 1700, color="#EEF3FA", look=(0, -0.6, 1.0))
C.area("fill", (4.0, -6.0, 2.4), 4.0, 420, color="#FFFFFF", look=(0, 0, 1.0))

# ------------------------------------------------------------------ the camera orbits the floating pallet
cam = C.camera(lens=62)
cam.data.shift_x = -0.21
cam.data.clip_end = 60
if C.args.test:
    from bpy_extras.object_utils import world_to_camera_view
    cam.location = C0
    C.look_at(cam, P0)
    bpy.context.view_layer.update()
    print("SCREEN pallet", tuple(round(v, 3) for v in world_to_camera_view(scene, cam, P0)))

for f in C.frame_list(COUNT):
    a = math.radians(SWING) * (f - SWEET) / SWEET
    cam.location = P0 + Matrix.Rotation(a, 4, "Z") @ (C0 - P0)
    C.look_at(cam, P0)
    C.render_to(os.path.join(C.args.out, f"{f:02d}.webp"))
