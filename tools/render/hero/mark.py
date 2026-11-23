"""PROTOTYPE round 5 · "The Mark", a scroll story for the home page (Apple-style, photoreal).

One continuous shot (story frames below; since 2026-11-23 it renders every half story frame, 335 files, for a
smoother scroll):
  0-40    macro on the left corner block: a steel branding head presses in and lifts away; the EPAL
          mark is left glowing, smokes and cools
  40-72   the camera pulls back and tracks along the long side to the middle block (IPPC HT mark)
  72-128  it drops to fork height and flies through the opening under the deck (light through the
          gaps between the deck boards)
  128-167 it climbs out behind the pallet and turns to the whole EPAL 1

  Blender -b --factory-startup --python tools/render/hero/mark.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/r5/mark --size 1600x900 [--frames 0-167] [--test]
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
scene = C.scene
COUNT = 168                     # story frames (the timeline in the docstring and the camera keys)
STEP = 0.5                      # story frames per rendered frame: 0.5 renders every half frame, for a smoother scroll
FRAMES = int(round((COUNT - 1) / STEP)) + 1   # 335 files, 000-334; file i shows story frame i * STEP
C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.35)
scene.cycles.max_bounces = 6

# ------------------------------------------------------------------ pallet and its marks
C.build_pallet(rot_deg=0, loc=(0, 0, 0))
decals = [ob for ob, kind in pk.OBJECTS if kind == "decal"]


def centroid(ob):
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    return sum(vs, Vector()) / len(vs)


front = sorted((d for d in decals if centroid(d).y < 0), key=lambda d: centroid(d).x)
L_DEC, C_DEC = front[0], front[1]
LC, CC = centroid(L_DEC), centroid(C_DEC)
FACE_Y = LC.y - 0.00035
print("marks at", tuple(round(v, 4) for v in LC), tuple(round(v, 4) for v in CC))


def add_relief(m, strength=0.9):
    """Branded marks are pressed into the wood: the mark's alpha drives a shallow groove."""
    n, l = m.node_tree.nodes, m.node_tree.links
    tex = next(x for x in n if x.type == "TEX_IMAGE")
    bump = n.new("ShaderNodeBump")
    bump.invert = True
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = 0.0007
    l.new(tex.outputs["Alpha"], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], n["Principled BSDF"].inputs["Normal"])
    char = n.new("ShaderNodeMix")                  # burnt wood is dark brown, not ink grey
    char.data_type = "RGBA"
    char.inputs["Factor"].default_value = 0.75
    l.new(tex.outputs["Color"], char.inputs[6])
    char.inputs[7].default_value = (*C.srgb("#2B1B12"), 1)
    l.new(pk.out_of_type(char, "RGBA"), n["Principled BSDF"].inputs["Base Color"])


for m in {d.data.materials[0] for d in decals}:
    add_relief(m)

# the left mark gets its own material: it glows while hot
hot = L_DEC.data.materials[0].copy()
hot.name = "stamp_hot"
L_DEC.data.materials[0] = hot
hn, hl = hot.node_tree.nodes, hot.node_tree.links
bb = hn.new("ShaderNodeBlackbody")
hl.new(bb.outputs["Color"], hn["Principled BSDF"].inputs["Emission Color"])
hn["Principled BSDF"].inputs["Emission Strength"].default_value = 0.0


def scorch_image(path, sigma=9.0):
    """A soft brown halo around the mark's lines (fresh brands scorch the wood around them)."""
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_scorch_" + os.path.basename(path))
    src = bpy.data.images.load(path, check_existing=True)
    w, h = src.size
    a = np.array(src.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., 3]
    pad = int(sigma * 3)
    a = np.pad(a, pad)
    k = np.exp(-0.5 * (np.arange(-pad, pad + 1) / sigma) ** 2)
    k /= k.sum()
    a = np.apply_along_axis(lambda r: np.convolve(r, k, mode="same"), 1, a)
    a = np.apply_along_axis(lambda c: np.convolve(c, k, mode="same"), 0, a)
    a = np.clip(a * 1.6, 0, 1)
    img = bpy.data.images.new("scorch_gen", w + 2 * pad, h + 2 * pad, alpha=True)
    rgba = np.stack([np.full_like(a, 0.16), np.full_like(a, 0.085), np.full_like(a, 0.04), a], -1)
    img.pixels.foreach_set(rgba.astype(np.float32).ravel())
    img.filepath_raw = out
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    return out, (w + 2 * pad) / w, (h + 2 * pad) / h


def add_scorch(dec):
    tex = next(x for x in dec.data.materials[0].node_tree.nodes if x.type == "TEX_IMAGE")
    path, sx, sy = scorch_image(bpy.path.abspath(tex.image.filepath))
    m = bpy.data.materials.new("scorch_" + dec.name)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    t = n.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path, check_existing=True)
    l.new(t.outputs["Color"], b.inputs["Base Color"])
    am = n.new("ShaderNodeMath"); am.operation = "MULTIPLY"
    l.new(t.outputs["Alpha"], am.inputs[0]); am.inputs[1].default_value = 0.34
    l.new(am.outputs[0], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.9
    c = centroid(dec)                  # decal quads are in world space (the pallet sits at the origin)
    me = dec.data.copy()
    toward = 0.00015 if c.y < 0 else -0.00015      # just behind the mark, still in front of the wood
    for v in me.vertices:
        d = v.co - c
        v.co = Vector((c.x + d.x * sx, c.y + toward, c.z + d.z * sy))
    me.materials.clear()
    me.materials.append(m)
    ob = bpy.data.objects.new("scorch", me)
    scene.collection.objects.link(ob)
    ob.parent = dec.parent
    ob.matrix_world = dec.matrix_world.copy()
    return ob


scorches = {d.name: add_scorch(d) for d in decals}

# ------------------------------------------------------------------ the branding head (press)
steel = bpy.data.materials.new("steel")
steel.use_nodes = True
sb = steel.node_tree.nodes["Principled BSDF"]
sb.inputs["Base Color"].default_value = (*C.srgb("#B4B8BD"), 1)
sb.inputs["Metallic"].default_value = 1.0
sb.inputs["Roughness"].default_value = 0.36
sn = steel.node_tree.nodes.new("ShaderNodeTexNoise")
sn.inputs["Scale"].default_value = 90.0
sn.inputs["Detail"].default_value = 6.0
sr = steel.node_tree.nodes.new("ShaderNodeMapRange")
sr.inputs["To Min"].default_value, sr.inputs["To Max"].default_value = 0.20, 0.34
steel.node_tree.links.new(sn.outputs["Fac"], sr.inputs["Value"])
steel.node_tree.links.new(sr.outputs[0], sb.inputs["Roughness"])

press = bpy.data.objects.new("press", None)
scene.collection.objects.link(press)


def box(name, size, loc, material, bevel=0.002):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        bv = ob.modifiers.new("bevel", "BEVEL")
        bv.width = bevel
        bv.segments = 3
    ob.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return ob


# built with its face at y = 0, then the empty moves it: face at FACE_Y - gap
head = box("head", (0.118, 0.040, 0.066), (0, -0.020, 0), steel)
plate = box("plate", (0.150, 0.016, 0.096), (0, -0.048, 0), steel, 0.003)
bpy.ops.mesh.primitive_cylinder_add(radius=0.017, depth=0.70, location=(0, -0.40, 0), rotation=(math.radians(90), 0, 0))
rod = bpy.context.active_object
rod.data.materials.append(steel)
bpy.ops.object.shade_smooth()
for ob in (head, plate, rod):
    ob.parent = press


def place_press(gap):
    press.location = (LC.x, FACE_Y - gap, LC.z)


# ------------------------------------------------------------------ smoke from the fresh brand
smoke_t = None
smoke_amt = None


def smoke_volume():
    global smoke_t, smoke_amt
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object
    ob.name = "smoke"
    ob.scale = (0.30, 0.16, 0.50)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.location = (LC.x, FACE_Y - 0.08, LC.z + 0.21)
    off = Vector(ob.location) - Vector((LC.x, FACE_Y, LC.z))     # object coords -> coords about the mark
    m = bpy.data.materials.new("smoke")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    vol = n.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.95, 0.945, 0.94, 1)
    vol.inputs["Anisotropy"].default_value = 0.35
    l.new(vol.outputs[0], out.inputs["Volume"])

    def M(op, a, b=None, clamp=False):
        node = n.new("ShaderNodeMath")
        node.operation = op
        node.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                node.inputs[i].default_value = v
            else:
                l.new(v, node.inputs[i])
        return node.outputs[0]

    tc = n.new("ShaderNodeTexCoord")
    add = n.new("ShaderNodeVectorMath"); add.operation = "ADD"
    l.new(tc.outputs["Object"], add.inputs[0]); add.inputs[1].default_value = off
    q = n.new("ShaderNodeSeparateXYZ")
    l.new(add.outputs[0], q.inputs[0])
    tval = n.new("ShaderNodeValue"); tval.outputs[0].default_value = 0.0
    aval = n.new("ShaderNodeValue"); aval.outputs[0].default_value = 0.0
    smoke_t, smoke_amt = tval, aval
    h = M("MAXIMUM", q.outputs["Z"], 0.0)                            # height above the mark centre
    d = M("MAXIMUM", M("MULTIPLY", q.outputs["Y"], -1.0), 0.0)       # distance out from the face
    # hugs the face low down, leans out and spreads as it rises
    f_face = M("EXPONENT", M("MULTIPLY", M("DIVIDE", d, M("ADD", 0.006, M("MULTIPLY", h, 0.16))), -1.0))
    wx = M("ADD", 0.05, M("MULTIPLY", h, 0.20))
    rx = M("DIVIDE", q.outputs["X"], wx)
    f_x = M("EXPONENT", M("MULTIPLY", M("MULTIPLY", rx, rx), -1.0))
    f_low = M("MULTIPLY", M("ADD", q.outputs["Z"], 0.032), 40.0, clamp=True)
    f_up = M("EXPONENT", M("MULTIPLY", h, -1.0 / 0.20))
    shape = M("MULTIPLY", M("MULTIPLY", f_face, f_x), M("MULTIPLY", f_low, f_up))
    # turbulence that drifts upward with time
    rise = n.new("ShaderNodeCombineXYZ")
    l.new(M("MULTIPLY", tval.outputs[0], -0.09), rise.inputs["Z"])
    mv = n.new("ShaderNodeVectorMath"); mv.operation = "ADD"
    l.new(add.outputs[0], mv.inputs[0]); l.new(rise.outputs[0], mv.inputs[1])
    noise = n.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    noise.inputs["Scale"].default_value = 26.0
    noise.inputs["Detail"].default_value = 5.0
    noise.inputs["Roughness"].default_value = 0.58
    noise.inputs["Distortion"].default_value = 0.6
    l.new(mv.outputs[0], noise.inputs["Vector"])
    l.new(M("MULTIPLY", tval.outputs[0], 0.7), noise.inputs["W"])
    wisp = M("MULTIPLY", M("MAXIMUM", M("SUBTRACT", noise.outputs["Fac"], 0.47), 0.0), 7.0)
    dens = M("MULTIPLY", M("MULTIPLY", shape, wisp), M("MULTIPLY", aval.outputs[0], 170.0))
    l.new(dens, vol.inputs["Density"])
    ob.data.materials.append(m)
    return ob


smoke = smoke_volume()
smoke.visible_shadow = False      # its shadow read as a dirty smudge on the block

# ------------------------------------------------------------------ studio: pale concrete that fades into a seamless background
BG = "#E8E6E2"          # what the camera sees behind everything; the floor fades into it (no horizon line)
BG_STRENGTH = 1.0
fl = bpy.data.materials.new("concrete")
fl.use_nodes = True
fn, flk = fl.node_tree.nodes, fl.node_tree.links
fb = fn["Principled BSDF"]
fb.inputs["Roughness"].default_value = 0.62
fb.inputs["Specular IOR Level"].default_value = 0.35
n1 = fn.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 4.0; n1.inputs["Detail"].default_value = 10.0
r1 = fn.new("ShaderNodeValToRGB")
r1.color_ramp.elements[0].color = (*C.srgb("#DAD6D0"), 1)
r1.color_ramp.elements[1].color = (*C.srgb("#E9E6E1"), 1)
flk.new(n1.outputs["Fac"], r1.inputs["Fac"])
flk.new(r1.outputs["Color"], fb.inputs["Base Color"])
n2 = fn.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 700.0; n2.inputs["Detail"].default_value = 4.0
b2 = fn.new("ShaderNodeBump"); b2.inputs["Strength"].default_value = 0.06
flk.new(n2.outputs["Fac"], b2.inputs["Height"])
flk.new(b2.outputs["Normal"], fb.inputs["Normal"])
camd = fn.new("ShaderNodeCameraData")
fade = fn.new("ShaderNodeMapRange")
fade.interpolation_type = "SMOOTHSTEP"
fade.inputs["From Min"].default_value, fade.inputs["From Max"].default_value = 3.0, 11.0
flk.new(camd.outputs["View Distance"], fade.inputs["Value"])
far = fn.new("ShaderNodeEmission")
far.inputs["Color"].default_value = (*C.srgb(BG), 1)
far.inputs["Strength"].default_value = BG_STRENGTH
mixf = fn.new("ShaderNodeMixShader")
flk.new(fade.outputs[0], mixf.inputs["Fac"])
flk.new(fb.outputs["BSDF"], mixf.inputs[1])
flk.new(far.outputs[0], mixf.inputs[2])
flk.new(mixf.outputs[0], fn["Material Output"].inputs["Surface"])
C.plane("floor", 60, 60, material=fl)

w = C.world("#F2F1EE", 0.5)                      # soft fill for lighting...
wn, wl = w.node_tree.nodes, w.node_tree.links
cam_bg = wn.new("ShaderNodeBackground")          # ...and a flat backdrop for the camera
cam_bg.inputs["Color"].default_value = (*C.srgb(BG), 1)
cam_bg.inputs["Strength"].default_value = BG_STRENGTH
lp = wn.new("ShaderNodeLightPath")
wmix = wn.new("ShaderNodeMixShader")
wl.new(lp.outputs["Is Camera Ray"], wmix.inputs["Fac"])
wl.new(wn["Background"].outputs[0], wmix.inputs[1])
wl.new(cam_bg.outputs[0], wmix.inputs[2])
wl.new(wmix.outputs[0], wn["World Output"].inputs["Surface"])

sun = C.sun("sun", 4.4, color="#FFEBD3", angle_deg=2.0)   # raking morning light from the front left
C.aim_sun(sun, elev_deg=34, azim_deg=34)
C.area("rim", (1.7, 2.6, 1.9), 2.0, 160, color="#EAF0FF", look=(0, 0, 0.05))


def glossy_card(name, loc, size, strength, look):
    """A softbox only reflections see: gives the steel something to mirror."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nn = m.node_tree.nodes
    nn.clear()
    e = nn.new("ShaderNodeEmission")
    e.inputs["Strength"].default_value = strength
    o = nn.new("ShaderNodeOutputMaterial")
    m.node_tree.links.new(e.outputs[0], o.inputs["Surface"])
    ob = C.plane(name, size[0], size[1], loc=loc, material=m)
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("Z", "Y").to_euler()
    for attr in ("visible_camera", "visible_diffuse", "visible_shadow", "visible_transmission", "visible_volume_scatter"):
        setattr(ob, attr, False)
    return ob


glossy_card("card_top", (LC.x - 0.25, LC.y - 0.55, 0.75), (0.9, 0.5), 9.0, (LC.x, LC.y - 0.2, LC.z))
glossy_card("card_side", (LC.x + 0.55, LC.y - 0.45, 0.10), (0.5, 0.35), 5.0, (LC.x, LC.y - 0.2, LC.z))

# ------------------------------------------------------------------ camera: one continuous move (Bezier keys)
cam = C.camera(lens=55)
cam.data.clip_start = 0.002
tgt = bpy.data.objects.new("target", None)
scene.collection.objects.link(tgt)
con = cam.constraints.new("TRACK_TO")
con.target = tgt
con.track_axis = "TRACK_NEGATIVE_Z"
con.up_axis = "UP_Y"
cam.data.dof.use_dof = True
cam.data.dof.focus_object = tgt
GAP_X = -(0.0725 + 0.455) / 2          # the fork opening between the left and middle blocks
Z_FORK = 0.069


def key(f, loc, look, lens, fstop, shift=0.0):
    cam.location = loc
    cam.keyframe_insert("location", frame=f)
    tgt.location = look
    tgt.keyframe_insert("location", frame=f)
    cam.data.lens = lens
    cam.data.keyframe_insert("lens", frame=f)
    cam.data.dof.aperture_fstop = fstop
    cam.data.dof.keyframe_insert("aperture_fstop", frame=f)
    cam.data.shift_x = shift
    cam.data.keyframe_insert("shift_x", frame=f)


V = Vector
key(0,   LC + V((-0.150, -0.285, 0.050)), LC + V((0.012, 0, 0.000)), 55, 3.2, -0.15)   # macro, bare block
key(40,  LC + V((-0.215, -0.400, 0.085)), LC + V((0.030, 0, 0.000)), 55, 4.0, -0.15)   # the fresh mark
key(72,  CC + V((-0.200, -0.400, 0.075)), CC + V((0.025, 0, 0.000)), 55, 4.0, -0.15)   # IPPC HT, middle block
key(96,  V((GAP_X, -0.95, Z_FORK)), V((GAP_X, 0.6, Z_FORK)), 28, 8.0, 0.0)              # fork height, facing the opening
key(114, V((GAP_X, 0.00, Z_FORK)), V((GAP_X, 1.6, Z_FORK + 0.004)), 24, 8.0, 0.0)       # under the middle of the deck
key(122, V((GAP_X, 0.05, Z_FORK)), V((GAP_X, 1.6, Z_FORK + 0.004)), 24, 8.0, 0.0)
key(140, V((GAP_X - 0.04, -0.85, 0.15)), V((GAP_X + 0.06, 0.4, 0.06)), 28, 8.0, 0.0)    # backs out, rising
key(167, V((-1.55, -1.85, 1.15)), V((0.00, 0.00, 0.04)), 50, 8.0, -0.12)                # the whole pallet


# ------------------------------------------------------------------ per-frame events
def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


if C.args.test:
    from bpy_extras.object_utils import world_to_camera_view
    for f, p in ((0, LC), (40, LC), (72, CC)):
        scene.frame_set(f)
        print("SCREEN", f, tuple(round(v, 3) for v in world_to_camera_view(scene, cam, p)))

CONTACT, LIFT, GONE = 16, 22, 34
for i in C.frame_list(FRAMES):
    f = i * STEP                      # story time: the keys and events above are in story frames 0-167
    scene.frame_set(int(f), subframe=f - int(f))
    # head: comes in 6-16, presses 16-22, lifts away 22-34
    if f < CONTACT:
        gap = 0.42 * (1 - ease((f - 6) / (CONTACT - 6)))
    elif f < LIFT:
        gap = -0.0006
    else:
        gap = 0.46 * ease((f - LIFT) / (GONE - LIFT))
    place_press(gap)
    for ob in (press, head, plate, rod):
        ob.hide_render = f >= GONE
    # the mark exists from contact on; it glows orange from lift-off and cools to char
    L_DEC.hide_render = f < CONTACT
    scorches[L_DEC.name].hide_render = f < CONTACT
    if f >= LIFT:
        bb.inputs["Temperature"].default_value = 950 + 250 * math.exp(-(f - LIFT) / 3.0)
        hn["Principled BSDF"].inputs["Emission Strength"].default_value = 1.1 * math.exp(-(f - LIFT) / 2.5)
    else:
        hn["Principled BSDF"].inputs["Emission Strength"].default_value = 0.0
    # smoke: escapes round the head while it presses, billows at lift-off, thins out
    if f < CONTACT:
        amt = 0.0
    elif f < LIFT:
        amt = 0.35 * ease((f - CONTACT) / (LIFT - CONTACT))
    elif f < LIFT + 8:
        amt = 0.35 + 0.65 * ease((f - LIFT) / 8)
    else:
        amt = math.exp(-(f - LIFT - 8) / 13.0)
    if f >= 50:                       # the last faint haze fades out by frame 56 (saves the slow volume frames)
        amt *= 1 - ease((f - 50) / 6)
    smoke_amt.outputs[0].default_value = amt
    smoke_t.outputs[0].default_value = max(f - CONTACT, 0) * 0.08
    smoke.hide_render = amt < 0.02
    C.render_to(os.path.join(C.args.out, f"{i:03d}.webp"))
