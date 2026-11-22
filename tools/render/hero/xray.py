"""PROTOTYPE round 5 · "Look inside": an EPAL 1 on a pale studio floor; on the page a round lens follows the
cursor and shows the same pallet as an X-ray in the brand blue (every board edge and all 78 nails, driven
through the boards into the blocks), and names the part under it. Three renders from one camera:
  photo.webp  the photoreal picture
  xray.webp   the X-ray (Standard view: exact brand blue, white lines)
  ids.png     one flat colour per part (R = 10 x part number), for the lens label

  Blender -b --factory-startup --python tools/render/hero/xray.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/r5/xray --size 2400x1350 --pass photo|xray|ids [--test]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

PASS = sys.argv[sys.argv.index("--pass") + 1] if "--pass" in sys.argv else "photo"
pk = C.pk
scene = C.scene
BLUE = "#0B3A9E"
BG = "#E4E7EC"

C.setup_cycles(view="AgX" if PASS == "photo" else "Standard", look="AgX - Medium High Contrast" if PASS == "photo" else "",
               exposure=-0.1 if PASS == "photo" else 0.0)
scene.render.dither_intensity = 0.0               # exact colours in the X-ray and the ID map
C.build_pallet(rot_deg=-24, loc=(0, 0, 0))
woods = [o for o, k in pk.OBJECTS if k == "wood"]
nails = [o for o, k in pk.OBJECTS if k == "nail"]
decals = [o for o, k in pk.OBJECTS if k == "decal"]
bpy.context.view_layer.update()

# nail shanks (palletkit only models the heads): down through the deck into the block, or up from below
shank_m = pk.plain_material("shank", "#B4B3AE", metallic=0.9, roughness=0.4)
shanks = []
for nl in nails:
    p = nl.matrix_world.translation
    down = abs(nl.rotation_euler.x) > 1.0            # floor nails point up into the block
    length = 0.088
    z0 = p.z if down else p.z - length
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0014, depth=length, vertices=8, location=(p.x, p.y, z0 + length / 2))
    sh = bpy.context.active_object
    sh.data.materials.append(shank_m)
    shanks.append(sh)


def flat(name, rgb, strength=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    n.clear()
    e = n.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*rgb, 1)
    e.inputs["Strength"].default_value = strength
    o = n.new("ShaderNodeOutputMaterial")
    m.node_tree.links.new(e.outputs[0], o.inputs["Surface"])
    return m


def ghost(edge_rgb, face_alpha=0.06, power=2.6, strength=1.0):
    """X-ray wood: faces almost clear, edges and grazing surfaces glow, so every layer shows through."""
    m = bpy.data.materials.new("ghost")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    lw = n.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    pw = n.new("ShaderNodeMath"); pw.operation = "POWER"
    l.new(lw.outputs["Facing"], pw.inputs[0]); pw.inputs[1].default_value = power
    fac = n.new("ShaderNodeMath"); fac.operation = "MULTIPLY_ADD"; fac.use_clamp = True
    l.new(pw.outputs[0], fac.inputs[0]); fac.inputs[1].default_value = 1.0 - face_alpha; fac.inputs[2].default_value = face_alpha
    tr = n.new("ShaderNodeBsdfTransparent")
    em = n.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*edge_rgb, 1)
    em.inputs["Strength"].default_value = strength
    mix = n.new("ShaderNodeMixShader")
    l.new(fac.outputs[0], mix.inputs["Fac"])
    l.new(tr.outputs[0], mix.inputs[1]); l.new(em.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], out.inputs["Surface"])
    return m


# ------------------------------------------------------------------ studio (photo pass)
if PASS == "photo":
    for sh in shanks:
        sh.hide_render = True
    fl = bpy.data.materials.new("studio_floor")
    fl.use_nodes = True
    fn, flk = fl.node_tree.nodes, fl.node_tree.links
    fb = fn["Principled BSDF"]
    fb.inputs["Roughness"].default_value = 0.7
    nz = fn.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 10.0
    rp = fn.new("ShaderNodeValToRGB")
    rp.color_ramp.elements[0].color = (*C.srgb("#D9DDE3"), 1)
    rp.color_ramp.elements[1].color = (*C.srgb("#E6E9EE"), 1)
    flk.new(nz.outputs["Fac"], rp.inputs["Fac"])
    flk.new(rp.outputs["Color"], fb.inputs["Base Color"])
    camd = fn.new("ShaderNodeCameraData")
    fade = fn.new("ShaderNodeMapRange"); fade.interpolation_type = "SMOOTHSTEP"
    fade.inputs["From Min"].default_value, fade.inputs["From Max"].default_value = 4.0, 12.0
    flk.new(camd.outputs["View Distance"], fade.inputs["Value"])
    far = fn.new("ShaderNodeEmission"); far.inputs["Color"].default_value = (*C.srgb(BG), 1)
    mx = fn.new("ShaderNodeMixShader")
    flk.new(fade.outputs[0], mx.inputs["Fac"]); flk.new(fb.outputs["BSDF"], mx.inputs[1]); flk.new(far.outputs[0], mx.inputs[2])
    flk.new(mx.outputs[0], fn["Material Output"].inputs["Surface"])
    C.plane("floor", 60, 60, material=fl)
    w = C.world("#EEF1F5", 0.45)
    wn, wl = w.node_tree.nodes, w.node_tree.links
    cb = wn.new("ShaderNodeBackground"); cb.inputs["Color"].default_value = (*C.srgb(BG), 1)
    lp = wn.new("ShaderNodeLightPath"); wm = wn.new("ShaderNodeMixShader")
    wl.new(lp.outputs["Is Camera Ray"], wm.inputs["Fac"])
    wl.new(wn["Background"].outputs[0], wm.inputs[1]); wl.new(cb.outputs[0], wm.inputs[2])
    wl.new(wm.outputs[0], wn["World Output"].inputs["Surface"])
    sun = C.sun("sun", 4.6, color="#FFEEDB", angle_deg=1.6)     # low morning sun from the left: long, crisp shadows
    C.aim_sun(sun, elev_deg=27, azim_deg=22)
    C.area("rim", (2.2, 2.4, 1.6), 2.0, 220, color="#E8EEFA", look=(0, 0, 0.1))
    C.area("fill", (2.8, -3.0, 1.2), 3.0, 120, color="#FFFFFF", look=(0, 0, 0.1))
else:
    w = C.world(BLUE if PASS == "xray" else "#000000", 1.0)
    if PASS == "xray":
        white = (1.0, 1.0, 1.0)
        g = ghost(white)
        for o in woods:
            o.data.materials[0] = g
        steel = flat("xray_nail", white, 1.0)
        for o in nails + shanks:
            o.data.materials[0] = steel
        for d in decals:
            d.hide_render = True
    else:  # ids: one exact colour per wooden part, nails take their part's colour, no anti-aliasing
        scene.cycles.samples = 1
        scene.cycles.use_denoising = False
        scene.cycles.filter_width = 0.01
        scene.view_settings.view_transform = "Standard"
        parts = [p["name"] for p in pk.R["parts"]]
        for o in woods:
            i = parts.index(o.name.split(".")[0]) + 1
            o.data.materials[0] = flat(f"id{i}", C.srgb(f"#{i * 10:02x}0000"))   # PNG red = 10 x part number
        for o in nails + shanks + decals:
            o.hide_render = True

cam = C.camera(lens=40)
cam.location = (1.55, -2.35, 1.42)
C.look_at(cam, (0.05, 0.02, 0.02))
cam.data.shift_x = -0.21
cam.data.shift_y = 0.02
if PASS == "photo":
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = cam.location.length
    cam.data.dof.aperture_fstop = 8.0

if PASS == "ids":
    s = scene.render.image_settings
    s.file_format = "PNG"
    s.color_mode = "RGB"
    s.color_depth = "8"
    scene.render.filepath = os.path.join(C.args.out, "ids.png")
    bpy.ops.render.render(write_still=True)
    print("WROTE ids.png")
else:
    C.render_to(os.path.join(C.args.out, f"{PASS}.webp"))
