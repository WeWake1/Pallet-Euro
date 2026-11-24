"""PROTOTYPE round 8 and the anatomy guide: one pallet in its layers, in the white studio. One script, several jobs
(--job), all from the same exact geometry (palletkit):

  explode    hero framing (copy on the left): assembled -> exploded into its layers (A "Built as you scroll")
  assemble   product framing, any recipe: the parts drop in from above, layer by layer, and settle; played
             backwards they fly out (C "Tap to transform": public/dev/r8/assemble/<recipe>/)
  film       anatomy framing: assembled -> exploded while the camera rises a little (the guide's playable animation)
  orbit      anatomy framing: the exploded pallet from 72 angles around it, every 5° (drag to turn)
  orbit-ids  every second of those angles (36, every 10°), one flat colour per part, twice the size, lossless PNG (traced into clean outlines
             by tools/render/trace_ids.py; not published)

Layers, bottom to top: bottom deck boards, blocks (with their marks), stringer boards, top deck boards, nails (the
nails that hold the top deck, drawn whole: head and shank). Writes layers.json: each layer's screen position in the
last frame, for the labels on the page. IDs as in inspect.py: 1-20 the parts in recipe order, 21 nails, 22 EPAL
marks, 23 IPPC mark (PNG red = 10 x id).

  Blender -b --factory-startup --python tools/render/hero/layers.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/r8/explode --job explode [--frames 0-59] [--test]
"""
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import bpy  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Vector  # noqa: E402

JOB = sys.argv[sys.argv.index("--job") + 1] if "--job" in sys.argv else "explode"
COUNT = {"explode": 60, "assemble": 36, "film": 48, "orbit": 72, "orbit-ids": 36}[JOB]   # orbit: every 5°; its even frames match the 36 ID maps
IDS = JOB == "orbit-ids"
pk = C.pk
scene = C.scene
MM = pk.MM

if IDS:
    C.setup_cycles(view="Standard", exposure=0.0)
    scene.cycles.samples = 1
    scene.cycles.use_denoising = False
    scene.cycles.filter_width = 0.01
    scene.render.dither_intensity = 0.0
    C.W, C.H = C.W * 2, C.H * 2                     # traced at twice the size for smooth outlines
    scene.render.resolution_x, scene.render.resolution_y = C.W, C.H
    scene.render.resolution_percentage = 100
    C.world("#000000", 0.0)
else:
    C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.3)
    C.seamless_studio(bg="#FFFFFF", floor="#F5F4F1", fade=(4.4, 9.0), fill="#EEF1F6", fill_strength=0.8, rough=0.7,
                      bg_strength=3.0)

HERO = JOB == "explode"
PALLET = Vector((0.62, 0.32, 0.0)) if HERO else Vector((0, 0, 0))
C.build_pallet(rot_deg=-24 if HERO else (-28 if JOB == "assemble" else 0), loc=PALLET)
AIM = (PALLET.x, PALLET.y, 0.2)
if not IDS:
    C.area("top", (PALLET.x, PALLET.y - 0.2, 3.4), 4.0, 200, look=AIM)
    C.area("key", (PALLET.x - 2.2, PALLET.y - 2.4, 3.0), 3.5, 150, look=AIM)
    C.area("fill", (PALLET.x + 2.8, PALLET.y - 1.6, 1.8), 3.0, 40, look=AIM)
    for o in [o for o in scene.objects if o.type == "LIGHT" and o.data.type == "AREA"]:
        o.visible_camera = False
    sun = C.sun("sun", 5.0, color="#FFF6EA", angle_deg=2.5)
    C.aim_sun(sun, elev_deg=55, azim_deg=28)

woods = [o for o, k in pk.OBJECTS if k == "wood"]
heads = [o for o, k in pk.OBJECTS if k == "nail"]
decals = [o for o, k in pk.OBJECTS if k == "decal"]
bpy.context.view_layer.update()

# whole nails for the top deck (palletkit models only the heads): a shank down through the deck into the block
steel = heads[0].data.materials[0] if heads else C.mat("steel", "#B4B3AE")
nails = []
for h in heads:
    if h.location.z < 0.05:                          # floor nails stay with the bottom boards, out of sight
        continue
    bpy.ops.mesh.primitive_cylinder_add(radius=1.8 * MM, depth=0.088, vertices=10, location=(0, 0, -0.044))
    sh = bpy.context.active_object
    sh.data.materials.append(steel)
    sh.parent = h
    nails.append(h)

LAYER = {}
for o in woods:
    LAYER[o] = {"bottom": 0, "block": 1, "cross": 2, "top": 3}[next(p["role"] for p in pk.R["parts"] if p["name"] == o.name.split(".")[0])]
for d in decals:
    LAYER[d] = 1
for h in heads:
    LAYER[h] = 4 if h in nails else 0
BASE = {o: (o.location.copy(), o.rotation_euler.copy()) for o in LAYER}
H = pk.R["dims"][2] * MM
LIFT = [0.0, 0.16, 0.35, 0.57, 0.86]                 # exploded height of each layer above its place (m)
rng = random.Random(3)
TUMBLE = {o: Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) for o in LAYER}


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def out_quart(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 4


def pose(lift, tumble=0.0):
    """lift: height per layer (m); tumble: 0..1, how far each part is turned off its place (for falling parts)."""
    for o, layer in LAYER.items():
        loc, rot = BASE[o]
        o.location = (loc.x, loc.y, loc.z + lift[layer])
        k = 0.0 if layer == 1 else tumble            # blocks (and their marks) fall straight; boards and nails turn
        tw = TUMBLE[o]
        o.rotation_euler = (rot.x + math.radians(7) * tw.x * k, rot.y + math.radians(7) * tw.y * k, rot.z + math.radians(10) * tw.z * k)


def exploded(t):
    """0 = assembled, 1 = fully apart. The top layers leave first."""
    starts = [0.0, 0.36, 0.24, 0.12, 0.0]
    return [LIFT[i] * ease((t - starts[i]) / 0.6) for i in range(5)]


def dropping(t):
    """0 = every layer far above the frame, 1 = assembled. The bottom boards land first, the nails last."""
    starts = [0.0, 0.14, 0.28, 0.42, 0.56]
    return [1.6 * (1 - out_quart((t - s) / 0.44)) for s in starts]


# ------------------------------------------------------------------ camera
cam = C.camera(lens=46 if HERO else 50)
if HERO:
    cam.location = (1.40, -3.40, 1.70)
    C.look_at(cam, (0.86, 0.24, 0.40))
    cam.data.shift_x = -0.30
    HERO_AIM = Vector((0.86, 0.24, 0.40))
    HERO_OFF = (cam.location - HERO_AIM) * 1.08
elif JOB == "assemble":                            # room for the widest (1200 x 1200 footprints), right of the headline
    cam.location = Vector((1.35, -3.55, 1.72)) * 1.18 + Vector((0, 0, -0.02))
    C.look_at(cam, (0.0, 0.0, 0.10))
    cam.data.shift_x = -0.23
    cam.data.shift_y = 0.03
cam.data.dof.use_dof = not IDS
cam.data.dof.aperture_fstop = 8.0


def place_orbit(az_deg, el_deg, dist):
    az, el = math.radians(az_deg), math.radians(el_deg)
    cam.location = (math.sin(az) * math.cos(el) * dist, -math.cos(az) * math.cos(el) * dist, math.sin(el) * dist + 0.38)
    C.look_at(cam, (0, 0, 0.38))
    cam.data.dof.focus_distance = dist


# ------------------------------------------------------------------ the ID map
if IDS:
    def flat(name, i):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        n = m.node_tree.nodes
        n.clear()
        e = n.new("ShaderNodeEmission")
        e.inputs["Color"].default_value = (*C.srgb(f"#{i * 10:02x}0000"), 1)
        m.node_tree.links.new(e.outputs[0], n.new("ShaderNodeOutputMaterial").inputs["Surface"])
        return m
    names = [p["name"] for p in pk.R["parts"]]
    for o in woods:
        o.data.materials[0] = flat(f"id{o.name}", names.index(o.name.split(".")[0]) + 1)
    nid = flat("id21", 21)
    for h in heads:
        h.data.materials[0] = nid
        for ch in h.children:
            ch.data.materials[0] = nid
    for d in decals:
        d.data.materials[0] = flat(d.name, 23 if "ippc" in d.name else 22)


def anchors():
    """Screen position (pixels of the full-size frame) of each layer's right-hand end, for the labels."""
    bpy.context.view_layer.update()
    out = []
    for layer in range(5):
        pts = [o.matrix_world.translation for o in LAYER if LAYER[o] == layer and o not in decals]
        if not pts:
            continue
        mid_z = sum(p.z for p in pts) / len(pts) + (0.04 if layer < 4 else 0.0)
        ends = {}
        for side, pick in (("x", max), ("lx", min)):              # right-hand end, left-hand end
            e = pick(pts, key=lambda p: world_to_camera_view(scene, cam, p).x)
            v = world_to_camera_view(scene, cam, Vector((e.x, e.y, mid_z)))
            ends[side] = round(v.x * C.W, 1)
            ends["y" if side == "x" else "ly"] = round((1 - v.y) * C.H, 1)
        out.append({"layer": layer, **ends})
    return out


def save(f, name=None):
    path = os.path.join(C.args.out, name or f"{f:02d}.webp")
    if IDS:
        s = scene.render.image_settings
        s.file_format, s.color_mode, s.color_depth = "PNG", "RGB", "8"
        scene.render.filepath = path.replace(".webp", ".png")
        bpy.ops.render.render(write_still=True)
        print("WROTE", scene.render.filepath, flush=True)
    else:
        C.render_to(path)


meta = {"job": JOB, "recipe": pk.R["id"], "frames": COUNT, "size": [C.W // (2 if IDS else 1), C.H // (2 if IDS else 1)]}
for f in C.frame_list(COUNT):
    t = f / (COUNT - 1)
    if JOB in ("explode", "film"):
        pose(exploded(t))
        if JOB == "film":                             # the camera rises and turns a little as the layers part
            place_orbit(-36 + 10 * ease(t), 24 + 6 * ease(t), 2.9 + 0.8 * ease(t))
        else:                                         # close on the assembled pallet, pulling back as it parts
            cam.location = HERO_AIM + HERO_OFF * (0.86 + 0.14 * ease(t))
            cam.data.dof.focus_distance = (cam.location - PALLET).length
    elif JOB == "assemble":
        lifts = dropping(t)
        pose(lifts, tumble=max(0.0, 1 - out_quart(t * 1.25)))
        cam.data.dof.focus_distance = (cam.location - PALLET).length
    else:                                            # orbit and orbit-ids: the exploded pallet all round
        pose(exploded(1.0))
        place_orbit(-26 + 360 * f / COUNT, 30, 3.7)
    save(f)
if JOB in ("explode", "film"):
    meta["labels"] = anchors()
json.dump(meta, open(os.path.join(C.args.out, "layers.json"), "w"), indent=1)
