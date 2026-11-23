"""PROTOTYPE round 4 · "Jaali": an EPAL 1 in a pale room, morning sun through a jaali (Indian stone
lattice) window on the left throwing its pattern across the floor and the pallet. One frame per sun
position; the page scrubs them (cursor on desktop, slow drift on phones).

  Blender -b --factory-startup --python tools/render/hero/jaali.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/r4/jaali [--frames 0-47] [--test]
  --glide: round 8's "Plays by itself" instead: 72 frames of a slow camera glide (public/dev/r8/glide)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

COUNT = 48
C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.42)


# ------------------------------------------------------------------ jaali pattern (procedural tile)
def jaali_tile(n=512, a=0.30, d=0.13):
    """One repeat of an eight-point-star lattice. 1 = stone, 0 = open. Signed distances, anti-aliased."""
    ys, xs = np.mgrid[0:n, 0:n]
    u = (xs + 0.5) / n - 0.5
    v = (ys + 0.5) / n - 0.5
    ax, ay = np.abs(u), np.abs(v)
    star = np.minimum(np.maximum(ax, ay) - a, (ax + ay) / math.sqrt(2) - a)   # two squares = 8-point star
    cx, cy = 0.5 - ax, 0.5 - ay
    corner = (cx + cy) / math.sqrt(2) - d / math.sqrt(2)                        # small diamond at the corners
    hole = np.minimum(star, corner)
    stone = np.clip(hole / (1.6 / n) + 0.5, 0.0, 1.0).astype(np.float32)
    img = bpy.data.images.new("jaali_gen", n, n, alpha=False)
    img.pixels.foreach_set(np.stack([stone, stone, stone, np.ones_like(stone)], -1).ravel())
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_jaali_tile.png")   # Cycles reads it reliably from a file
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = "Non-Color"
    return img


def jaali_material(tile_m, size_x, size_y):
    m = bpy.data.materials.new("jaali")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    mix = n.new("ShaderNodeMixShader")
    tr = n.new("ShaderNodeBsdfTransparent")
    df = n.new("ShaderNodeBsdfDiffuse")
    df.inputs["Color"].default_value = (*C.srgb("#E8DCC8"), 1)
    tc = n.new("ShaderNodeTexCoord")
    mp = n.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (size_x / tile_m, size_y / tile_m, 1)
    tex = n.new("ShaderNodeTexImage")
    tex.image = jaali_tile()
    tex.extension = "REPEAT"
    tex.interpolation = "Linear"
    l.new(tc.outputs["UV"], mp.inputs["Vector"])
    l.new(mp.outputs["Vector"], tex.inputs["Vector"])
    l.new(tex.outputs["Color"], mix.inputs["Fac"])
    l.new(tr.outputs[0], mix.inputs[1])
    l.new(df.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], out.inputs["Surface"])
    return m


# ------------------------------------------------------------------ room: honed stone slabs, one plaster wall
def stone_floor():
    m = bpy.data.materials.new("floor")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.36
    b.inputs["Specular IOR Level"].default_value = 0.4
    tc = n.new("ShaderNodeTexCoord")
    brick = n.new("ShaderNodeTexBrick")            # 1200 x 600 mm slabs, running bond, fine joints
    brick.offset = 0.5
    brick.offset_frequency = 1
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Brick Width"].default_value = 1.2
    brick.inputs["Row Height"].default_value = 0.6
    brick.inputs["Mortar Size"].default_value = 0.0025
    brick.inputs["Mortar Smooth"].default_value = 0.4
    brick.inputs["Bias"].default_value = 0.0
    brick.inputs["Color1"].default_value = (*C.srgb("#EDE7DD"), 1)
    brick.inputs["Color2"].default_value = (*C.srgb("#E3DCCF"), 1)
    brick.inputs["Mortar"].default_value = (*C.srgb("#CBC2B3"), 1)
    l.new(tc.outputs["Object"], brick.inputs["Vector"])
    noise = n.new("ShaderNodeTexNoise")            # soft mottling inside each slab
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Detail"].default_value = 8.0
    l.new(tc.outputs["Object"], noise.inputs["Vector"])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.95, 0.95, 0.94, 1)
    ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1)
    l.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    mul = n.new("ShaderNodeVectorMath")
    mul.operation = "MULTIPLY"
    l.new(brick.outputs["Color"], mul.inputs[0])
    l.new(ramp.outputs["Color"], mul.inputs[1])
    l.new(mul.outputs["Vector"], b.inputs["Base Color"])
    bump = n.new("ShaderNodeBump")                 # joints sit a hair below the slabs
    bump.invert = True
    bump.inputs["Strength"].default_value = 0.5
    bump.inputs["Distance"].default_value = 0.001
    l.new(brick.outputs["Fac"], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def plaster(hexcol):
    m = bpy.data.materials.new("plaster")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.92
    b.inputs["Specular IOR Level"].default_value = 0.2
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2.2
    noise.inputs["Detail"].default_value = 4.0
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*C.srgb("#EAE4DA"), 1)
    ramp.color_ramp.elements[1].color = (*C.srgb(hexcol), 1)
    l.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    l.new(ramp.outputs["Color"], b.inputs["Base Color"])
    fine = n.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = 160.0
    fine.inputs["Detail"].default_value = 8.0
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    l.new(fine.outputs["Fac"], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


C.plane("floor", 24, 24, material=stone_floor())
WALL_Y = 1.45
wall_m = plaster("#F3EFE8")
C.plane("back_wall", 24, 6, loc=(0, WALL_Y, 3.014), rot=(math.radians(90), 0, 0), material=wall_m)
C.plane("shadow_gap", 24, 0.014, loc=(0, WALL_Y + 0.012, 0.007), rot=(math.radians(90), 0, 0), material=wall_m)


# ------------------------------------------------------------------ gobo: the jaali the camera never sees
def shadow_only(ob):
    for attr in ("visible_camera", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
        setattr(ob, attr, False)
    ob.visible_shadow = True


PALLET = Vector((0.3, 0.1, 0.07))
EL0, AZ0 = 32.0, 58.0                      # the jaali faces the sun's middle position
el, az = math.radians(EL0), math.radians(AZ0)
to_sun = Vector((-math.cos(el) * math.cos(az), -math.cos(el) * math.sin(az), math.sin(el)))
centre = PALLET + Vector((0.45, 0.55, 0)) + to_sun * 3.2   # beam lands behind-right: calm floor under the copy
rot = to_sun.to_track_quat("Z", "Y")
JW, JH, BIG = 2.6, 2.3, 30.0
jaali = C.plane("jaali", JW, JH, material=jaali_material(0.31, JW, JH))
blockers = [(-(JW + BIG) / 2, 0, BIG, 2 * BIG), ((JW + BIG) / 2, 0, BIG, 2 * BIG),
            (0, (JH + BIG) / 2, JW, BIG), (0, -(JH + BIG) / 2, JW, BIG)]
for ob, (du, dv) in [(jaali, (0, 0))] + [(C.plane("block", w, h, material=C.mat("block", "#777777")), (u, v))
                                          for u, v, w, h in blockers]:
    ob.rotation_euler = rot.to_euler()
    ob.location = centre + rot @ Vector((du, dv, 0))
    shadow_only(ob)

# ------------------------------------------------------------------ pallet, light, camera
C.build_pallet(rot_deg=-18, loc=(PALLET.x, PALLET.y, 0))
C.world("#F3EEE6", 0.6)
sun = C.sun("sun", 8.5, color="#FFE6C7", angle_deg=0.3)
C.area("room_fill", (3.8, -3.2, 2.3), 5.0, 230, color="#EEF2FF", look=(0, 0, 0.4))
C.area("bounce", (1.8, -0.5, 3.6), 3.0, 60, color="#FFF6EA", look=(0, 0, 0))

cam = C.camera(lens=50)
cam.location = (2.2, -4.25, 1.05)
C.look_at(cam, (0.62, 0.35, 0.2))
cam.data.shift_x = -0.25
cam.data.shift_y = 0.03
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = (cam.location - PALLET).length
cam.data.dof.aperture_fstop = 2.8

if "--glide" in sys.argv:
    # round 8 D "Plays by itself": a living photograph. The camera glides slowly in and across while the sun's pattern
    # drifts a little; the page plays the frames forward and back with easing, so it never shows a seam.
    GLIDE = 72
    start = cam.location.copy()
    aim0 = Vector((0.62, 0.35, 0.2))
    for f in C.frame_list(GLIDE):
        t = f / (GLIDE - 1)
        cam.location = start + Vector((-0.78, 0.6, 0.06)) * t
        C.look_at(cam, aim0 + Vector((-0.06, 0.04, -0.02)) * t)
        cam.data.dof.focus_distance = (cam.location - PALLET).length
        C.aim_sun(sun, elev_deg=EL0 + 1.0 - 2.0 * t, azim_deg=AZ0 - 5 + 10 * t)
        C.render_to(os.path.join(C.args.out, f"{f:02d}.webp"))
    sys.exit(0)
for f in C.frame_list(COUNT):
    t = f / (COUNT - 1)
    C.aim_sun(sun, elev_deg=EL0 + 1.5 - 3.0 * t, azim_deg=AZ0 - 8 + 16 * t)
    C.render_to(os.path.join(C.args.out, f"{f:02d}.webp"))
