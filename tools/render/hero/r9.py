"""PROTOTYPE round 9 · four bold, simple pictures (decision #65: "something more unique, cool yet simple"). Stills
first: the owner picks the picture, then its motion is designed. One script, one scene per --scene:

  indigo   an EPAL 1 carrying a neat load of indigo-dyed cotton: India's own blue, almost the brand's deep blue,
           the one strong colour on a white studio
  plan     the EPAL 1 seen straight from above in low sun: a graphic poster of boards and long shadows
  upright  the EPAL 1 standing on its end, leaning on a lime-washed wall in morning light, like a piece of design
  macro    a close, cinematic crop of one corner: deck board ends, the chamfer, the block, nail heads, shallow focus

  Blender -b --factory-startup --python tools/render/hero/r9.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/r9 --size 2400x1350 --scene indigo [--test]
Writes <scene>.webp.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import bpy  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402

SCENE = sys.argv[sys.argv.index("--scene") + 1] if "--scene" in sys.argv else "indigo"
pk = C.pk
scene = C.scene
MM = pk.MM
L, WD, HT = (v * MM for v in pk.R["dims"])


def white_studio(exposure=0.3, bg="#FFFFFF", floor="#F5F4F1"):
    C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=exposure)
    C.seamless_studio(bg=bg, floor=floor, fade=(4.4, 9.0), fill="#EEF1F6", fill_strength=0.8, rough=0.7, bg_strength=3.0)


def soft_lights(aim, top=190, key=150, fill=40):
    C.area("top", (aim[0], aim[1] - 0.2, 3.4), 4.0, top, look=aim)
    C.area("key", (aim[0] - 2.2, aim[1] - 2.4, 3.0), 3.5, key, look=aim)
    C.area("fill", (aim[0] + 2.8, aim[1] - 1.6, 1.8), 3.0, fill, look=aim)
    for o in [o for o in scene.objects if o.type == "LIGHT" and o.data.type == "AREA"]:
        o.visible_camera = False


def rounded_box(name, size, loc, rot, mat, bevel=0.012):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    ob.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bv = ob.modifiers.new("soft", "BEVEL")
    bv.width, bv.segments = bevel, 4
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def indigo_cloth():
    """Indigo-dyed cotton: deep, slightly uneven blue, matte, a fine weave and faint fold lines."""
    m = bpy.data.materials.new("indigo")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.88
    b.inputs["Sheen Weight"].default_value = 0.25
    b.inputs["Sheen Tint"].default_value = (*C.srgb("#6F86C8"), 1)
    tc = n.new("ShaderNodeTexCoord")
    nz = n.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.5
    nz.inputs["Detail"].default_value = 6.0
    l.new(tc.outputs["Object"], nz.inputs["Vector"])
    oi = n.new("ShaderNodeObjectInfo")
    mixf = n.new("ShaderNodeMath")
    mixf.operation = "MULTIPLY_ADD"
    mixf.inputs[1].default_value = 0.5
    l.new(nz.outputs["Fac"], mixf.inputs[0])
    l.new(oi.outputs["Random"], mixf.inputs[2])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.25
    ramp.color_ramp.elements[0].color = (*C.srgb("#030820"), 1)
    ramp.color_ramp.elements[1].position = 1.2
    ramp.color_ramp.elements[1].color = (*C.srgb("#0E1A4E"), 1)
    l.new(mixf.outputs[0], ramp.inputs["Fac"])
    l.new(ramp.outputs["Color"], b.inputs["Base Color"])
    weave = n.new("ShaderNodeTexWave")
    weave.inputs["Scale"].default_value = 900.0
    weave.inputs["Distortion"].default_value = 1.0
    l.new(tc.outputs["Object"], weave.inputs["Vector"])
    folds = n.new("ShaderNodeTexWave")                 # the folded layers of cloth, seen on the sides
    folds.wave_profile = "SAW"
    folds.bands_direction = "Z"
    folds.inputs["Scale"].default_value = 70.0
    folds.inputs["Distortion"].default_value = 0.6
    l.new(tc.outputs["Object"], folds.inputs["Vector"])
    hmix = n.new("ShaderNodeMath")
    hmix.operation = "MULTIPLY_ADD"
    hmix.inputs[1].default_value = 0.35
    l.new(weave.outputs["Fac"], hmix.inputs[0])
    l.new(folds.outputs["Fac"], hmix.inputs[2])
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.18
    l.new(hmix.outputs[0], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def strap_mat():
    return C.mat("strap", "#EDE7DA", rough=0.55, spec=0.4)


# ================================================================== scenes
if SCENE == "indigo":
    white_studio(exposure=0.15)
    PALLET = Vector((0.62, 0.32, 0.0))
    C.build_pallet(rot_deg=-24, loc=PALLET)
    cloth = indigo_cloth()
    ends = bpy.data.materials.new("roll_ends")      # the rolled-up layers of cloth, seen on each end
    ends.use_nodes = True
    en, el = ends.node_tree.nodes, ends.node_tree.links
    eb = en["Principled BSDF"]
    eb.inputs["Roughness"].default_value = 0.9
    etc = en.new("ShaderNodeTexCoord")
    rings = en.new("ShaderNodeTexWave")
    rings.wave_type = "RINGS"
    rings.rings_direction = "X"
    rings.inputs["Scale"].default_value = 26.0
    rings.inputs["Distortion"].default_value = 1.5
    el.new(etc.outputs["Object"], rings.inputs["Vector"])
    rr = en.new("ShaderNodeValToRGB")
    rr.color_ramp.elements[0].color = (*C.srgb("#03081E"), 1)
    rr.color_ramp.elements[1].color = (*C.srgb("#16276A"), 1)
    el.new(rings.outputs["Fac"], rr.inputs["Fac"])
    el.new(rr.outputs["Color"], eb.inputs["Base Color"])
    rng = random.Random(9)
    R0 = 0.118
    rows = [3, 2, 3, 2]
    for k, n in enumerate(rows):
        z = HT + R0 + k * R0 * math.sqrt(3) + 0.002
        for j in range(n):
            y = (j - (n - 1) / 2) * (2 * R0 + 0.004)
            r = R0 * rng.uniform(0.95, 1.0)
            bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=L - 0.06 + rng.uniform(-0.02, 0.01), vertices=96)
            roll = bpy.context.active_object
            roll.rotation_euler = (0, math.radians(90), 0)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            roll.data.materials.append(cloth)
            roll.data.materials.append(ends)
            for poly in roll.data.polygons:
                poly.use_smooth = abs(poly.normal.x) < 0.5
                poly.material_index = 1 if abs(poly.normal.x) > 0.5 else 0
            bv = roll.modifiers.new("soft", "BEVEL")
            bv.width, bv.segments, bv.limit_method = 0.008, 3, "ANGLE"
            roll.parent = pk.ROOT
            roll.location = (rng.uniform(-0.01, 0.01), y, z - (R0 - r))
            roll.rotation_euler = (math.radians(rng.uniform(0, 360)), 0, 0)
    AIM = (PALLET.x, PALLET.y, 0.5)
    soft_lights(AIM, top=150, key=120, fill=40)
    sun = C.sun("sun", 5.5, color="#FFF2E2", angle_deg=2.0)
    C.aim_sun(sun, elev_deg=42, azim_deg=24)
    cam = C.camera(lens=46)
    cam.location = (1.55, -3.55, 1.42)
    C.look_at(cam, (0.86, 0.24, 0.48))
    cam.data.shift_x = -0.27
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = (cam.location - PALLET).length
    cam.data.dof.aperture_fstop = 6.0

elif SCENE == "plan":
    C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.35)
    PALLET = Vector((0.0, 0.0, 0.0))
    C.build_pallet(rot_deg=0, loc=PALLET)
    C.plane("floor", 40, 40, material=C.stone_floor("#EFE7DA", "#E9DFCF", "#D2C6B2", slab=(0.9, 0.9)))
    C.world("#E6ECF5", 0.55)
    sun = C.sun("sun", 8.5, color="#FFE3BE", angle_deg=0.6)
    C.aim_sun(sun, elev_deg=20, azim_deg=-30)          # low, from the upper left of the picture: long shadows down-right
    cam = C.camera(lens=50)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 3.3
    cam.location = (-0.55, 0.12, 6.0)                 # the pallet sits right of the headline
    cam.rotation_euler = (0, 0, 0)

elif SCENE == "upright":
    C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.25)
    C.plane("floor", 30, 30, material=C.stone_floor("#EDE6DA", "#E6DECF", "#CFC5B4", slab=(0.8, 0.8)))
    wall = C.plane("wall", 30, 8, loc=(0, 0.75, 4), rot=(math.radians(90), 0, 0), material=C.plaster("#F1ECE3", "#F7F3EC"))
    C.world("#E9EDF3", 0.8)
    C.build_pallet(rot_deg=0, loc=(0, 0, 0))
    lean = math.radians(9)
    # on its short end: the long side stands up, the deck faces the camera, leaning back on the wall
    pk.ROOT.rotation_euler = Euler((math.radians(90) - lean, math.radians(90), math.radians(0)), "XYZ")
    bpy.context.view_layer.update()
    pts = [ob.matrix_world @ v.co for ob, _ in pk.OBJECTS if ob.type == "MESH" for v in ob.data.vertices]
    minz, maxy = min(p.z for p in pts), max(p.y for p in pts)
    pk.ROOT.location = (0.55, 0.75 - maxy - 0.002, -minz)
    sun = C.sun("sun", 7.5, color="#FFE4C0", angle_deg=0.5)
    C.aim_sun(sun, elev_deg=26, azim_deg=146)          # low from the front right: the slats' shadows stripe the wall
    C.area("fill", (-1.0, -3.0, 1.6), 4.0, 70, color="#EEF2FF", look=(0.5, 0.6, 0.6)).visible_camera = False
    cam = C.camera(lens=45)
    cam.location = (0.2, -2.55, 0.9)
    C.look_at(cam, (0.5, 0.6, 0.66))
    cam.data.shift_x = -0.2
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = 3.0
    cam.data.dof.aperture_fstop = 4.0

elif SCENE == "macro":
    white_studio(exposure=0.2, floor="#F1EFEA")
    C.build_pallet(rot_deg=-34, loc=(0.0, 0.0, 0.0))
    bpy.context.view_layer.update()
    corner = pk.ROOT.matrix_world @ Vector((L / 2, -WD / 2, HT * 0.62))   # the front right corner
    sun = C.sun("sun", 6.0, color="#FFEBD0", angle_deg=1.0)
    C.aim_sun(sun, elev_deg=30, azim_deg=-8)         # raking across the end grain from the right
    C.area("fill", (corner.x - 1.6, corner.y - 1.8, 1.2), 3.0, 50, color="#EEF2FF", look=tuple(corner)).visible_camera = False
    cam = C.camera(lens=85)
    d = Vector((0.55, -1.0, 0.36)).normalized()
    cam.location = corner + d * 1.05
    C.look_at(cam, corner + Vector((-0.06, 0.02, -0.01)))
    cam.data.shift_x = -0.18
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = 1.05
    cam.data.dof.aperture_fstop = 2.2

else:
    raise SystemExit(f"unknown scene {SCENE}")

C.render_to(os.path.join(C.args.out, f"{SCENE}.webp"))
