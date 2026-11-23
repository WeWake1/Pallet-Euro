"""PROTOTYPE round 7 · A "From the drawing": one EPAL 1 in a white studio (round 2's simplicity), half technical
drawing, half real. Frame 0 is the pallet as a drawing only (deep-blue ink lines, hidden edges dashed); each
later frame turns one more part into real wood, in the order a pallet is assembled (bottom boards, blocks,
stringer boards, deck boards, then the nails and the marks). The page scrubs the frames with the cursor.

Each frame is rendered twice: the photo (Cycles, the drawn parts invisible) and the ink lines alone (Freestyle on
holdout geometry, transparent). tools/render/compose_lines.py lays the lines over the photo in the exact brand blue
(run.py does it after rendering). Also writes dims.json: the pallet's corners in picture pixels, for the
dimension lines drawn by the page.

  Blender -b --factory-startup --python tools/render/hero/blueprint.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/r7/blueprint [--frames 0-21] [--test]
  python tools/render/compose_lines.py public/dev/r7/blueprint
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import palletkit as pk  # noqa: E402
import bpy  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Vector  # noqa: E402

scene = C.scene
C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.3)
SAMPLES = scene.cycles.samples
C.seamless_studio(bg="#FFFFFF", floor="#F5F4F1", fade=(3.6, 7.5), fill="#EEF1F6", fill_strength=0.8, rough=0.7,
                  bg_strength=3.0)

PALLET = Vector((0.62, 0.32, 0.0))
C.build_pallet(rot_deg=-24, loc=PALLET)
AIM = (PALLET.x, PALLET.y, 0.07)
C.area("top", (0.6, 0.1, 3.2), 4.0, 190, look=AIM)
C.area("key", (-1.6, -2.4, 3.0), 3.5, 150, look=AIM)
C.area("fill", (3.4, -1.2, 1.8), 3.0, 40, look=AIM)
sun = C.sun("sun", 5.0, color="#FFF6EA", angle_deg=2.5)
C.aim_sun(sun, elev_deg=52, azim_deg=28)

cam = C.camera(lens=46)                  # the daybreak framing: the pallet keeps to the right ~55% of the picture
cam.location = (1.38, -3.15, 1.42)
C.look_at(cam, (0.84, 0.24, 0.08))
cam.data.shift_x = -0.27
cam.data.shift_y = 0.03
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = (cam.location - PALLET).length
cam.data.dof.aperture_fstop = 5.6

# ------------------------------------------------------------------ parts in assembly order
wood = {ob.name: ob for ob, k in pk.OBJECTS if k == "wood"}
nails = [ob for ob, k in pk.OBJECTS if k == "nail"]
decals = [ob for ob, k in pk.OBJECTS if k == "decal"]
bpy.context.view_layer.update()


def far_first(names):
    return sorted(names, key=lambda n: -(wood[n].matrix_world.translation - cam.location).length)


layers = [[n for n in wood if n.startswith(p)] for p in ("bottom", "block", "cross", "top")]
STEPS = [[n] for layer in layers for n in far_first(layer)] + [["nails+marks"]]
COUNT = len(STEPS) + 1                    # frame 0: drawing only; frame k: the first k steps are real

ghost = bpy.data.materials.new("drawn")   # seen by nothing; Freestyle still draws its edges
ghost.use_nodes = True
gn = ghost.node_tree.nodes
gn.remove(gn["Principled BSDF"])
gn.new("ShaderNodeBsdfTransparent")
ghost.node_tree.links.new(gn["Transparent BSDF"].outputs[0], gn["Material Output"].inputs["Surface"])
real_mat = {n: ob.data.materials[0] for n, ob in wood.items()}

drawn = bpy.data.collections.new("drawn")
scene.collection.children.link(drawn)

# ------------------------------------------------------------------ Freestyle ink
r = scene.render
r.line_thickness_mode = "ABSOLUTE"
r.line_thickness = 1.0
fs = scene.view_layers[0].freestyle_settings
fs.crease_angle = math.radians(140)       # 90° box edges and the 45° corner chamfers
ink = 1.0 if not C.args.test else 0.7     # test frames are half size


def lineset(ls, visibility, thick, alpha, dashed):
    ls.select_by_visibility = True
    ls.visibility = visibility
    ls.select_by_edge_types = True
    ls.select_silhouette = ls.select_border = ls.select_crease = True
    ls.select_by_collection = True
    ls.collection = drawn
    st = ls.linestyle
    st.color = (1, 1, 1)
    st.alpha = alpha
    st.thickness = thick * ink
    st.thickness_position = "CENTER"
    st.caps = "ROUND"
    st.use_dashed_line = dashed
    if dashed:
        st.dash1, st.gap1 = 7, 5


visible = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("visible")
visible.linestyle = bpy.data.linestyles.new("visible")
lineset(visible, "VISIBLE", 1.7, 1.0, False)
hidden = fs.linesets.new("hidden")
hidden.linestyle = bpy.data.linestyles.new("hidden")
lineset(hidden, "HIDDEN", 1.1, 0.38, True)


def set_state(k):
    real = {n for step in STEPS[:k] for n in step}
    for n, ob in wood.items():
        is_real = n in real
        ob.data.materials[0] = real_mat[n] if is_real else ghost
        ob.visible_shadow = is_real
        ob.modifiers["eased edges"].show_render = is_real      # drawn parts keep sharp edges for the ink
        if is_real and n in drawn.objects:
            drawn.objects.unlink(ob)
        elif not is_real and n not in drawn.objects:
            drawn.objects.link(ob)
    done = "nails+marks" in real
    for ob in nails + decals:
        ob.hide_render = not done


def render_png(path, rgba):
    s = r.image_settings
    s.file_format = "PNG"
    s.color_mode = "RGBA" if rgba else "RGB"
    s.color_depth = "8"
    s.compression = 15
    r.filepath = path
    bpy.ops.render.render(write_still=True)
    print("WROTE", path, flush=True)


meshes = [ob for ob in scene.objects if ob.type == "MESH"]
raw = os.path.join(C.args.out, "_raw")
os.makedirs(raw, exist_ok=True)

# dims.json: the bounding box corners in pixels of the full-size picture (x right, y down)
L, Wd, Hh = (v * pk.MM for v in pk.R["dims"])
corners = {}
for sx in (-1, 1):
    for sy in (-1, 1):
        for sz in (0, 1):
            co = pk.ROOT.matrix_world @ Vector((sx * L / 2, sy * Wd / 2, sz * Hh))
            v = world_to_camera_view(scene, cam, co)
            corners[f"{'LR'[sx > 0]}{'FB'[sy > 0]}{'BT'[sz]}"] = [round(v.x * C.W, 1), round((1 - v.y) * C.H, 1)]
json.dump({"size": [C.W, C.H], "mm": pk.R["dims"], "corners": corners, "frames": COUNT,
           "steps": [s[0] for s in STEPS]}, open(os.path.join(C.args.out, "dims.json"), "w"), indent=1)

for f in C.frame_list(COUNT):
    set_state(f)
    # 1. photo (no ink)
    r.use_freestyle = False
    r.film_transparent = False
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    render_png(os.path.join(raw, f"{f:02d}.png"), rgba=False)
    # 2. ink alone: every surface fully transparent (Freestyle draws nothing over holdouts), transparent film;
    #    Freestyle still uses the geometry, so real parts hide the lines behind them
    kept = [(ob, list(ob.data.materials)) for ob in meshes]
    for ob, _ in kept:
        for i in range(len(ob.data.materials)):
            ob.data.materials[i] = ghost
    r.use_freestyle = True
    r.film_transparent = True
    scene.cycles.samples = 16
    scene.cycles.use_denoising = False
    render_png(os.path.join(raw, f"{f:02d}-lines.png"), rgba=True)
    for ob, ms in kept:
        for i, m in enumerate(ms):
            ob.data.materials[i] = m
