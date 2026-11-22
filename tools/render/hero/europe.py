"""PROTOTYPE round 5 · "Two worlds", the European half: the same EPAL 1, from the same camera as the jaali
room (jaali.py), in a north-European warehouse: white-painted brick, grey concrete with a worn yellow
floor line, cool daylight through a steel factory window (its grid falls where the jaali stars fall).
The page splits the two renders at the cursor: Europe's standard on the left, India on the right.

  Blender -b --factory-startup --python tools/render/hero/europe.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/r5/worlds --size 2400x1350 [--test]
The Indian half is jaali.py frame 24 at the same size (--frames 24).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

pk = C.pk
C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.42)

# the pallet first, exactly as in jaali.py (palletkit seeds its randomness from the recipe name)
PALLET = Vector((0.3, 0.1, 0.07))
C.build_pallet(rot_deg=-18, loc=(PALLET.x, PALLET.y, 0))


# ------------------------------------------------------------------ concrete floor with a worn yellow line
def concrete():
    m = bpy.data.materials.new("concrete")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Specular IOR Level"].default_value = 0.45
    tc = n.new("ShaderNodeTexCoord")
    mot = n.new("ShaderNodeTexNoise"); mot.inputs["Scale"].default_value = 1.4; mot.inputs["Detail"].default_value = 12.0
    l.new(tc.outputs["Object"], mot.inputs["Vector"])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*C.srgb("#BDBDBA"), 1)
    ramp.color_ramp.elements[1].color = (*C.srgb("#D4D4D1"), 1)
    l.new(mot.outputs["Fac"], ramp.inputs["Fac"])
    # the line: 100 mm wide, parallel to the wall, paint worn through in places
    sep = n.new("ShaderNodeSeparateXYZ")
    l.new(tc.outputs["Object"], sep.inputs[0])
    d = n.new("ShaderNodeMath"); d.operation = "SUBTRACT"
    l.new(sep.outputs["Y"], d.inputs[0]); d.inputs[1].default_value = 1.02
    ad = n.new("ShaderNodeMath"); ad.operation = "ABSOLUTE"
    l.new(d.outputs[0], ad.inputs[0])
    band = n.new("ShaderNodeMath"); band.operation = "LESS_THAN"
    l.new(ad.outputs[0], band.inputs[0]); band.inputs[1].default_value = 0.05
    wear = n.new("ShaderNodeTexNoise"); wear.inputs["Scale"].default_value = 14.0; wear.inputs["Detail"].default_value = 8.0
    l.new(tc.outputs["Object"], wear.inputs["Vector"])
    wr = n.new("ShaderNodeMapRange")
    wr.inputs["From Min"].default_value, wr.inputs["From Max"].default_value = 0.38, 0.5
    l.new(wear.outputs["Fac"], wr.inputs["Value"])
    line = n.new("ShaderNodeMath"); line.operation = "MULTIPLY"
    l.new(band.outputs[0], line.inputs[0]); l.new(wr.outputs[0], line.inputs[1])
    mix = n.new("ShaderNodeMix"); mix.data_type = "RGBA"
    l.new(line.outputs[0], mix.inputs["Factor"])
    l.new(ramp.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = (*C.srgb("#D9A922"), 1)
    l.new(pk.out_of_type(mix, "RGBA"), b.inputs["Base Color"])
    rough = n.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value, rough.inputs["To Max"].default_value = 0.22, 0.5
    l.new(mot.outputs["Fac"], rough.inputs["Value"])
    l.new(rough.outputs[0], b.inputs["Roughness"])
    fine = n.new("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 420.0; fine.inputs["Detail"].default_value = 4.0
    l.new(tc.outputs["Object"], fine.inputs["Vector"])
    bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.07
    l.new(fine.outputs["Fac"], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


# ------------------------------------------------------------------ white-painted brick wall (Flemish-style courses)
def painted_brick():
    m = bpy.data.materials.new("brick")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.88
    b.inputs["Specular IOR Level"].default_value = 0.25
    tc = n.new("ShaderNodeTexCoord")
    mp = n.new("ShaderNodeMapping")                 # the wall plane's object Y runs up the wall after rotation
    l.new(tc.outputs["Object"], mp.inputs["Vector"])
    br = n.new("ShaderNodeTexBrick")
    br.offset = 0.5
    br.offset_frequency = 1
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = 0.225
    br.inputs["Row Height"].default_value = 0.075
    br.inputs["Mortar Size"].default_value = 0.009
    br.inputs["Mortar Smooth"].default_value = 0.5
    br.inputs["Color1"].default_value = (*C.srgb("#F2F1ED"), 1)
    br.inputs["Color2"].default_value = (*C.srgb("#E3E1DB"), 1)
    br.inputs["Mortar"].default_value = (*C.srgb("#CFCDC6"), 1)
    br.inputs["Bias"].default_value = -0.2
    l.new(mp.outputs["Vector"], br.inputs["Vector"])
    chip = n.new("ShaderNodeTexNoise"); chip.inputs["Scale"].default_value = 9.0; chip.inputs["Detail"].default_value = 10.0
    l.new(tc.outputs["Object"], chip.inputs["Vector"])
    cr = n.new("ShaderNodeMapRange")                # a few chips where the old red brick shows through
    cr.inputs["From Min"].default_value, cr.inputs["From Max"].default_value = 0.70, 0.74
    l.new(chip.outputs["Fac"], cr.inputs["Value"])
    mix = n.new("ShaderNodeMix"); mix.data_type = "RGBA"
    l.new(cr.outputs[0], mix.inputs["Factor"])
    l.new(br.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = (*C.srgb("#B07A62"), 1)
    l.new(pk.out_of_type(mix, "RGBA"), b.inputs["Base Color"])
    face = n.new("ShaderNodeTexNoise"); face.inputs["Scale"].default_value = 80.0; face.inputs["Detail"].default_value = 6.0
    l.new(tc.outputs["Object"], face.inputs["Vector"])
    h = n.new("ShaderNodeMath"); h.operation = "MULTIPLY_ADD"
    l.new(face.outputs["Fac"], h.inputs[0]); h.inputs[1].default_value = 0.22
    l.new(br.outputs["Fac"], h.inputs[2])
    bump = n.new("ShaderNodeBump"); bump.invert = True
    bump.inputs["Strength"].default_value = 0.9
    bump.inputs["Distance"].default_value = 0.007
    l.new(h.outputs[0], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


C.plane("floor", 24, 24, material=concrete())
WALL_Y = 1.45
wall = C.plane("back_wall", 24, 6, loc=(0, WALL_Y, 3.0), rot=(math.radians(90), 0, 0), material=painted_brick())


# ------------------------------------------------------------------ gobo: a steel factory window the camera never sees
def window_tile(n=512, bar=0.075):
    """One pane of a steel window: 1 = steel (shadow), 0 = glass. Thin glazing bars on each edge."""
    ys, xs = np.mgrid[0:n, 0:n]
    u = (xs + 0.5) / n
    v = (ys + 0.5) / n
    edge = np.minimum(np.minimum(u, 1 - u), np.minimum(v, 1 - v))
    steel = np.clip((bar / 2 - edge) / (1.6 / n) + 0.5, 0.0, 1.0).astype(np.float32)
    img = bpy.data.images.new("window_gen", n, n, alpha=False)
    img.pixels.foreach_set(np.stack([steel, steel, steel, np.ones_like(steel)], -1).ravel())
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_window_tile.png")
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = "Non-Color"
    return img


def gobo_material(pane_w, pane_h, size_x, size_y):
    m = bpy.data.materials.new("window")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    mix = n.new("ShaderNodeMixShader")
    tr = n.new("ShaderNodeBsdfTransparent")
    df = n.new("ShaderNodeBsdfDiffuse")
    tc = n.new("ShaderNodeTexCoord")
    mp = n.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (size_x / pane_w, size_y / pane_h, 1)
    tex = n.new("ShaderNodeTexImage")
    tex.image = window_tile()
    tex.extension = "REPEAT"
    l.new(tc.outputs["UV"], mp.inputs["Vector"])
    l.new(mp.outputs["Vector"], tex.inputs["Vector"])
    l.new(tex.outputs["Color"], mix.inputs["Fac"])
    l.new(tr.outputs[0], mix.inputs[1])
    l.new(df.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], out.inputs["Surface"])
    return m


def shadow_only(ob):
    for attr in ("visible_camera", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
        setattr(ob, attr, False)
    ob.visible_shadow = True


EL, AZ = 32.0, 58.0                        # the gobo faces jaali.py's middle sun, so the pattern lands in the same place
el, az = math.radians(EL), math.radians(AZ)
to_sun = Vector((-math.cos(el) * math.cos(az), -math.cos(el) * math.sin(az), math.sin(el)))
centre = PALLET + Vector((0.45, 0.55, 0)) + to_sun * 3.2
rot = to_sun.to_track_quat("Z", "Y")
GW, GH, BIG = 2.9, 2.4, 30.0
gobo = C.plane("window", GW, GH, material=gobo_material(0.48, 0.40, GW, GH))
blockers = [(-(GW + BIG) / 2, 0, BIG, 2 * BIG), ((GW + BIG) / 2, 0, BIG, 2 * BIG),
            (0, (GH + BIG) / 2, GW, BIG), (0, -(GH + BIG) / 2, GW, BIG)]
for ob, (du, dv) in [(gobo, (0, 0))] + [(C.plane("block", w, h, material=C.mat("block", "#777777")), (u, v))
                                        for u, v, w, h in blockers]:
    ob.rotation_euler = rot.to_euler()
    ob.location = centre + rot @ Vector((du, dv, 0))
    shadow_only(ob)

# ------------------------------------------------------------------ cool northern daylight, same camera as jaali.py
C.world("#E3E9F1", 0.85)
sun = C.sun("sun", 5.2, color="#E9EFFA", angle_deg=2.2)
C.aim_sun(sun, elev_deg=31.97, azim_deg=58.17)   # = jaali.py frame 24
C.area("room_fill", (3.8, -3.2, 2.3), 5.0, 260, color="#E8EEF8", look=(0, 0, 0.4))
C.area("bounce", (1.8, -0.5, 3.6), 3.0, 60, color="#F3F6FB", look=(0, 0, 0))
scene = C.scene
try:
    scene.view_settings.use_white_balance = True
    scene.view_settings.white_balance_temperature = 6200
except (AttributeError, TypeError):
    print("WARNING no white balance in this Blender")

cam = C.camera(lens=50)
cam.location = (2.2, -4.25, 1.05)
C.look_at(cam, (0.62, 0.35, 0.2))
cam.data.shift_x = -0.25
cam.data.shift_y = 0.03
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = (cam.location - PALLET).length
cam.data.dof.aperture_fstop = 2.8

C.render_to(os.path.join(C.args.out, "europe.webp"))
