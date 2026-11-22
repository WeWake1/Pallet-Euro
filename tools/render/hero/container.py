"""PROTOTYPE round 5 · "Your next container": the closing scroll story of the home page (photoreal).

A deep-blue 20' container in a pale yard. One frame per scroll step:
  0-70    the locking handles swing out and both doors open (right leaf first, as on a real box)
  40-100  the camera walks up to the open doors: 11 EPAL pallets of cartons, wall to wall
  100-150 it rises over the box while the roof lifts away: the floor plan from above
          (the standard 20' layout: one row of 7 pallets turned, one row of 4 lengthwise)

  Blender -b --factory-startup --python tools/render/hero/container.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/r5/container --size 1600x900 [--frames 0-149] [--test]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

pk = C.pk
scene = C.scene
COUNT = 150
random.seed(7)
C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.15)
scene.cycles.max_bounces = 6

# ISO 20' general purpose (metres): external and internal sizes as in src/lib/containers.ts
L, W, H = 6.058, 2.438, 2.591
IL, IW = 5.898, 2.352
FLOOR_Z = 0.170
Y_DOOR = L / 2


# ------------------------------------------------------------------ materials
def paint(name, hexcol, rough=(0.36, 0.52), wear=1.0):
    """Weathered container paint: tone variation, rain streaks, dirtier and a little rusty low down,
    orange peel and the odd dent. World position, so every panel weathers the same way."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Specular IOR Level"].default_value = 0.5
    geo = n.new("ShaderNodeNewGeometry")
    sep = n.new("ShaderNodeSeparateXYZ")
    l.new(geo.outputs["Position"], sep.inputs[0])
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.6; nz.inputs["Detail"].default_value = 8.0
    l.new(geo.outputs["Position"], nz.inputs["Vector"])
    col = n.new("ShaderNodeValToRGB")
    base = Vector(C.srgb(hexcol))
    col.color_ramp.elements[0].color = (*(base * 0.84), 1)
    col.color_ramp.elements[1].color = (*(base * 1.05), 1)
    l.new(nz.outputs["Fac"], col.inputs["Fac"])
    st = n.new("ShaderNodeVectorMath"); st.operation = "MULTIPLY"
    l.new(geo.outputs["Position"], st.inputs[0]); st.inputs[1].default_value = (30, 30, 1.1)
    sn = n.new("ShaderNodeTexNoise"); sn.inputs["Scale"].default_value = 1.0; sn.inputs["Detail"].default_value = 4.0
    l.new(st.outputs[0], sn.inputs["Vector"])
    sr = n.new("ShaderNodeMapRange")
    sr.inputs["From Min"].default_value, sr.inputs["From Max"].default_value = 0.5, 0.78
    sr.inputs["To Min"].default_value, sr.inputs["To Max"].default_value = 0.0, 0.28 * wear
    l.new(sn.outputs["Fac"], sr.inputs["Value"])
    low = n.new("ShaderNodeMapRange")               # grime near the ground
    low.inputs["From Min"].default_value, low.inputs["From Max"].default_value = 0.9, 0.05
    low.inputs["To Min"].default_value, low.inputs["To Max"].default_value = 0.0, 0.35 * wear
    l.new(sep.outputs["Z"], low.inputs["Value"])
    dirt = n.new("ShaderNodeMath"); dirt.operation = "ADD"; dirt.use_clamp = True
    l.new(sr.outputs[0], dirt.inputs[0]); l.new(low.outputs[0], dirt.inputs[1])
    mix = n.new("ShaderNodeMix"); mix.data_type = "RGBA"
    l.new(dirt.outputs[0], mix.inputs["Factor"])
    l.new(col.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = (*C.srgb("#3B3E44"), 1)
    rn = n.new("ShaderNodeTexNoise"); rn.inputs["Scale"].default_value = 9.0; rn.inputs["Detail"].default_value = 10.0
    l.new(geo.outputs["Position"], rn.inputs["Vector"])
    rlow = n.new("ShaderNodeMapRange")              # rust blooms only low down
    rlow.inputs["From Min"].default_value, rlow.inputs["From Max"].default_value = 0.45, 0.12
    l.new(sep.outputs["Z"], rlow.inputs["Value"])
    rth = n.new("ShaderNodeMapRange")
    rth.inputs["From Min"].default_value, rth.inputs["From Max"].default_value = 0.62, 0.70
    l.new(rn.outputs["Fac"], rth.inputs["Value"])
    rmask = n.new("ShaderNodeMath"); rmask.operation = "MULTIPLY"
    l.new(rlow.outputs[0], rmask.inputs[0]); l.new(rth.outputs[0], rmask.inputs[1])
    rmask2 = n.new("ShaderNodeMath"); rmask2.operation = "MULTIPLY"
    l.new(rmask.outputs[0], rmask2.inputs[0]); rmask2.inputs[1].default_value = 0.85 * wear
    rust = n.new("ShaderNodeMix"); rust.data_type = "RGBA"
    l.new(rmask2.outputs[0], rust.inputs["Factor"])
    l.new(pk.out_of_type(mix, "RGBA"), rust.inputs[6])
    rust.inputs[7].default_value = (*C.srgb("#7B4A2C"), 1)
    l.new(pk.out_of_type(rust, "RGBA"), b.inputs["Base Color"])
    rr = n.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = rough
    l.new(nz.outputs["Fac"], rr.inputs["Value"])
    radd = n.new("ShaderNodeMath"); radd.operation = "MULTIPLY_ADD"; radd.use_clamp = True
    l.new(rmask2.outputs[0], radd.inputs[0]); radd.inputs[1].default_value = 0.4
    l.new(rr.outputs[0], radd.inputs[2])
    l.new(radd.outputs[0], b.inputs["Roughness"])
    dent = n.new("ShaderNodeTexNoise"); dent.inputs["Scale"].default_value = 2.2; dent.inputs["Detail"].default_value = 2.0
    l.new(geo.outputs["Position"], dent.inputs["Vector"])
    peel = n.new("ShaderNodeTexNoise"); peel.inputs["Scale"].default_value = 900.0
    l.new(geo.outputs["Position"], peel.inputs["Vector"])
    hsum = n.new("ShaderNodeMath"); hsum.operation = "MULTIPLY_ADD"
    l.new(peel.outputs["Fac"], hsum.inputs[0]); hsum.inputs[1].default_value = 0.05
    l.new(dent.outputs["Fac"], hsum.inputs[2])
    bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.08; bump.inputs["Distance"].default_value = 0.004
    l.new(hsum.outputs[0], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


BLUE = paint("container_blue", "#1F3D78")
BLUE_DARK = paint("container_blue_dark", "#14306A", rough=(0.45, 0.62))
INNER = paint("container_inner", "#D6D8DA", rough=(0.55, 0.72), wear=0.45)
STEEL = pk.plain_material("galv", "#ADB2B7", metallic=1.0, roughness=0.36)
RUBBER = pk.plain_material("rubber", "#1B1C1E", roughness=0.62)
PLY = pk.wood_material("ply", "hard", tint=0.62)


# ------------------------------------------------------------------ mesh helpers
def mesh_obj(name, verts, faces, materials, smooth_angle=8, solid=0.0, mat_offset=0, bevel=0.0):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    for mm in materials:
        me.materials.append(mm)
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    if bevel:
        bv = ob.modifiers.new("bevel", "BEVEL")
        bv.width = bevel
        bv.segments = 2
        bv.limit_method = "ANGLE"
        bv.angle_limit = math.radians(25)
        bv.use_clamp_overlap = True
    if solid:
        so = ob.modifiers.new("solid", "SOLIDIFY")
        so.thickness = solid
        so.offset = -1
        so.material_offset = mat_offset
        so.use_even_offset = True
    return ob


def box(name, x0, x1, y0, y1, z0, z1, material, bevel=0.004, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (x1 - x0, y1 - y0, z1 - z0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(material)
    if bevel:
        bv = ob.modifiers.new("bevel", "BEVEL")
        bv.width = bevel
        bv.segments = 2
        bv.use_clamp_overlap = True
    bpy.ops.object.shade_smooth()
    if parent:
        ob.parent = parent
        ob.matrix_parent_inverse = parent.matrix_world.inverted()
    return ob


def cylinder(name, r, z0, z1, x, y, material, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=z1 - z0, location=(x, y, (z0 + z1) / 2), vertices=20)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    if parent:
        ob.parent = parent
        ob.matrix_parent_inverse = parent.matrix_world.inverted()
    return ob


def profile(length, pitch, depth, flat_out, flat_in, start_out=True):
    """Trapezoidal corrugation along u in [0, length]: (u, w) with w = 0 outer face, w = depth inner."""
    s = (pitch - flat_out - flat_in) / 2
    seg = [(0.0, 0.0), (flat_out, 0.0), (flat_out + s, depth), (flat_out + s + flat_in, depth), (pitch, 0.0)]
    pts, u0 = [], 0.0
    while u0 < length - 1e-6:
        for du, w in seg:
            u = u0 + du
            if u > length:
                break
            if not pts or u > pts[-1][0] + 1e-6:
                pts.append((u, w))
        u0 += pitch
    if pts[-1][0] < length - 1e-6:
        pts.append((length, 0.0))
    return pts


def corrugated(name, pts, h0, h1, to3d, material, inner=None, out=(0, 0, 1)):
    verts, faces = [], []
    for u, w in pts:
        verts.append(to3d(u, w, h0))
        verts.append(to3d(u, w, h1))
    for i in range(len(pts) - 1):
        a = 2 * i
        faces.append((a, a + 2, a + 3, a + 1))
    v0, v1, v3 = (Vector(verts[i]) for i in (0, 2, 1))
    if (v1 - v0).cross(v3 - v0).dot(Vector(out)) < 0:     # paint outside, light grey inside
        faces = [tuple(reversed(f_)) for f_ in faces]
    mats = [material] + ([inner] if inner else [])
    return mesh_obj(name, verts, faces, mats, solid=0.002, mat_offset=1 if inner else 0, bevel=0.003)


# ------------------------------------------------------------------ the box
POST = 0.15
RAIL_B, RAIL_T = 0.16, 0.10
X_OUT = W / 2
y0, y1 = -L / 2 + POST, L / 2 - 0.26          # side walls between the front and rear corner posts
side_pts = profile(y1 - y0, 0.2785, 0.036, 0.072, 0.068)
for sx in (-1, 1):
    corrugated(f"side_{sx}", side_pts, RAIL_B, H - RAIL_T,
               lambda u, w, h, sx=sx: (sx * (X_OUT - 0.004 - w), y0 + u, h), BLUE, INNER, out=(sx, 0, 0))
    box(f"rail_bottom_{sx}", sx * X_OUT - 0.11 * (sx > 0), sx * X_OUT + 0.11 * (sx < 0), -L / 2, L / 2, 0.012, RAIL_B, BLUE_DARK)
    box(f"rail_top_{sx}", sx * X_OUT - 0.085 * (sx > 0), sx * X_OUT + 0.085 * (sx < 0), -L / 2, L / 2, H - RAIL_T, H, BLUE)
front_pts = profile(W - 2 * POST, 0.226, 0.045, 0.06, 0.06)
corrugated("front_wall", front_pts, RAIL_B, H - RAIL_T,
           lambda u, w, h: (-W / 2 + POST + u, -L / 2 + 0.004 + w, h), BLUE, INNER, out=(0, -1, 0))
box("front_bottom", -W / 2, W / 2, -L / 2, -L / 2 + 0.13, 0.012, RAIL_B, BLUE_DARK)
box("front_top", -W / 2, W / 2, -L / 2, -L / 2 + 0.11, H - 0.13, H, BLUE)
for sx in (-1, 1):
    box(f"post_front_{sx}", sx * X_OUT - POST * (sx > 0), sx * X_OUT + POST * (sx < 0), -L / 2, -L / 2 + POST, 0, H, BLUE)
    box(f"post_rear_{sx}", sx * X_OUT - POST * (sx > 0), sx * X_OUT + POST * (sx < 0), L / 2 - 0.26, L / 2, 0, H, BLUE)
roof_pts = profile(L - 0.24, 0.20, 0.022, 0.07, 0.07)
roof = corrugated("roof", roof_pts, -W / 2 + 0.06, W / 2 - 0.06,
                  lambda u, w, h: (h, -L / 2 + 0.12 + u, H - 0.004 - w), BLUE, INNER, out=(0, 0, 1))
box("header", -W / 2 + POST, W / 2 - POST, L / 2 - 0.18, L / 2, H - 0.24, H, BLUE)
box("sill", -W / 2 + POST, W / 2 - POST, L / 2 - 0.18, L / 2, 0.012, FLOOR_Z + 0.01, BLUE_DARK)
box("floor", -IW / 2, IW / 2, -IL / 2, IL / 2 - 0.02, FLOOR_Z - 0.028, FLOOR_Z, PLY, bevel=0)


def casting(x, y, z):
    ob = box("casting", x - 0.081, x + 0.081, y - 0.089, y + 0.089, z - 0.059, z + 0.059, STEEL, bevel=0.006)
    ob.data.materials[0] = pk.plain_material("casting_paint", "#123A84", metallic=0.2, roughness=0.5)
    for axis, cx, cy in (("x", x + (0.081 if x > 0 else -0.081), y), ("y", x, y + (0.089 if y > 0 else -0.089))):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.06, location=(cx, cy, z), vertices=24,
                                            rotation=(0, math.radians(90), 0) if axis == "x" else (math.radians(90), 0, 0))
        hole = bpy.context.active_object
        hole.scale = (1.0, 1.0, 1.0)
        if axis == "x":
            hole.scale = (1.6, 1.0, 1.0)   # oval: taller than wide (scaled in local X, which is world Z here)
        else:
            hole.scale = (1.0, 1.6, 1.0)
        bm = ob.modifiers.new("hole", "BOOLEAN")
        bm.object = hole
        bm.operation = "DIFFERENCE"
        hole.hide_render = True


for sx in (-1, 1):
    for sy in (-1, 1):
        for z in (0.059, H - 0.059):
            casting(sx * (X_OUT - 0.081), sy * (L / 2 - 0.089), z)

# ------------------------------------------------------------------ doors (hinged on the rear posts)
LEAF_W = 1.172
DOOR_Z0, DOOR_Z1 = FLOOR_Z + 0.02, H - 0.25
HINGE_X = X_OUT - 0.035
door_pivots, bar_pivots = [], []
for side in (1, -1):                                # right leaf (seen from behind) first
    pv = bpy.data.objects.new(f"door_{side}", None)
    scene.collection.objects.link(pv)
    pv.location = (side * HINGE_X, Y_DOOR + 0.07, 0)
    bpy.context.view_layer.update()
    door_pivots.append(pv)
    d = -side                                       # from the hinge toward the middle of the box
    panel_pts = profile(DOOR_Z1 - DOOR_Z0 - 0.16, 0.30, 0.022, 0.12, 0.10)
    corrugated(f"door_panel_{side}", panel_pts, 0.05, LEAF_W - 0.05,
               lambda u, w, h, d=d, pv=pv: (pv.location.x + d * h, pv.location.y - 0.012 - w, DOOR_Z0 + 0.08 + u),
               BLUE, BLUE_DARK, out=(0, 1, 0)).parent = pv
    for ob in pv.children:
        ob.matrix_parent_inverse = pv.matrix_world.inverted()
    x_hinge, x_free = pv.location.x, pv.location.x + d * LEAF_W
    xa, xb = min(x_hinge, x_free), max(x_hinge, x_free)
    yb = pv.location.y
    box(f"frame_top_{side}", xa, xb, yb - 0.06, yb, DOOR_Z1 - 0.08, DOOR_Z1, BLUE, parent=pv)
    box(f"frame_bot_{side}", xa, xb, yb - 0.06, yb, DOOR_Z0, DOOR_Z0 + 0.08, BLUE, parent=pv)
    box(f"frame_in_{side}", xa if d > 0 else xb - 0.05, xa + 0.05 if d > 0 else xb, yb - 0.06, yb, DOOR_Z0, DOOR_Z1, BLUE, parent=pv)
    xf0, xf1 = (xb - 0.05, xb) if d > 0 else (xa, xa + 0.05)
    box(f"frame_free_{side}", xf0, xf1, yb - 0.06, yb, DOOR_Z0, DOOR_Z1, BLUE, parent=pv)
    box(f"gasket_{side}", xf0 - 0.004 if d > 0 else xf0, xf1 if d > 0 else xf1 + 0.004, yb - 0.075, yb - 0.06, DOOR_Z0, DOOR_Z1, RUBBER, bevel=0, parent=pv)
    for zh in (0.42, 1.0, 1.62, 2.12):              # hinges
        box("hinge", x_hinge - 0.022, x_hinge + 0.022, yb - 0.012, yb + 0.03, zh - 0.05, zh + 0.05, STEEL, parent=pv)
    # two locking bars per leaf, each with guides, cams and a handle
    for frac in (0.30, 0.74):
        bx = x_hinge + d * LEAF_W * frac
        by = yb + 0.045
        bp = bpy.data.objects.new("bar", None)
        scene.collection.objects.link(bp)
        bp.location = (bx, by, 0)
        bp.parent = pv
        bp.matrix_parent_inverse = pv.matrix_world.inverted()
        bpy.context.view_layer.update()
        cylinder("rod", 0.0135, DOOR_Z0 - 0.05, DOOR_Z1 + 0.05, bx, by, STEEL, parent=bp)
        for zc in (DOOR_Z0 - 0.03, DOOR_Z1 + 0.03):
            box("cam", bx - 0.012, bx + 0.012, by - 0.01, by + 0.05, zc - 0.025, zc + 0.025, STEEL, parent=bp)
        # handle: lies flat against the door pointing to the middle, swings out with the bar
        box("handle", bx, bx + d * 0.40, by + 0.006, by + 0.022, 1.05, 1.09, STEEL, bevel=0.003, parent=bp)
        box("grip", bx + d * 0.30, bx + d * 0.40, by + 0.006, by + 0.04, 1.045, 1.095, RUBBER, bevel=0.004, parent=bp)
        for zg in (0.55, 1.6, 2.2):
            box("guide", bx - 0.028, bx + 0.028, yb, by + 0.02, zg - 0.03, zg + 0.03, STEEL, parent=pv)
        bar_pivots.append((side, bp, d))
    box("retainer", x_hinge + d * LEAF_W * 0.30 + d * 0.33, x_hinge + d * LEAF_W * 0.30 + d * 0.37, yb, yb + 0.05, 1.02, 1.12, STEEL, parent=pv)
    box("retainer", x_hinge + d * LEAF_W * 0.74 + d * 0.33, x_hinge + d * LEAF_W * 0.74 + d * 0.37, yb, yb + 0.05, 1.02, 1.12, STEEL, parent=pv)

# cam keepers on the header and sill
for side in (1, -1):
    for frac in (0.30, 0.74):
        bx = side * HINGE_X - side * LEAF_W * frac
        for zc in (DOOR_Z0 - 0.03, DOOR_Z1 + 0.03):
            box("keeper", bx - 0.03, bx + 0.03, Y_DOOR, Y_DOOR + 0.2, zc - 0.035, zc + 0.035, STEEL)

# ------------------------------------------------------------------ cargo: 11 EPAL pallets of cartons
C.build_pallet(rot_deg=0, loc=(0, 0, 0))
src = bpy.data.collections.new("pallet_src")
for ob in [pk.ROOT] + [o for o, _ in pk.OBJECTS] + [o for o in bpy.data.objects if o.parent == pk.ROOT]:
    if src.objects.get(ob.name) is None:
        src.objects.link(ob)
    if scene.collection.objects.get(ob.name):
        scene.collection.objects.unlink(ob)

CART = (0.40, 0.266, 0.255)
carton = bpy.data.materials.new("kraft")
carton.use_nodes = True
cn, cl = carton.node_tree.nodes, carton.node_tree.links
cb = cn["Principled BSDF"]
cb.inputs["Specular IOR Level"].default_value = 0.3
oi = cn.new("ShaderNodeObjectInfo")
cr = cn.new("ShaderNodeValToRGB")
cr.color_ramp.elements[0].color = (*C.srgb("#B38A5C"), 1)
cr.color_ramp.elements[1].color = (*C.srgb("#C9A274"), 1)
cl.new(oi.outputs["Random"], cr.inputs["Fac"])
ctc = cn.new("ShaderNodeTexCoord")
csep = cn.new("ShaderNodeSeparateXYZ")
cl.new(ctc.outputs["Object"], csep.inputs[0])
nsep = cn.new("ShaderNodeSeparateXYZ")
cl.new(ctc.outputs["Normal"], nsep.inputs[0])
ax = cn.new("ShaderNodeMath"); ax.operation = "ABSOLUTE"
cl.new(csep.outputs["Y"], ax.inputs[0])
tape = cn.new("ShaderNodeMath"); tape.operation = "LESS_THAN"
cl.new(ax.outputs[0], tape.inputs[0]); tape.inputs[1].default_value = 0.024
upn = cn.new("ShaderNodeMath"); upn.operation = "GREATER_THAN"
cl.new(nsep.outputs["Z"], upn.inputs[0]); upn.inputs[1].default_value = 0.5
endz = cn.new("ShaderNodeMath"); endz.operation = "GREATER_THAN"    # tape runs down the two ends too
axn = cn.new("ShaderNodeMath"); axn.operation = "ABSOLUTE"
cl.new(nsep.outputs["X"], axn.inputs[0])
cl.new(axn.outputs[0], endz.inputs[0]); endz.inputs[1].default_value = 0.5
topz = cn.new("ShaderNodeMath"); topz.operation = "GREATER_THAN"
cl.new(csep.outputs["Z"], topz.inputs[0]); topz.inputs[1].default_value = CART[2] / 2 - 0.06
endtop = cn.new("ShaderNodeMath"); endtop.operation = "MULTIPLY"
cl.new(endz.outputs[0], endtop.inputs[0]); cl.new(topz.outputs[0], endtop.inputs[1])
face = cn.new("ShaderNodeMath"); face.operation = "MAXIMUM"
cl.new(upn.outputs[0], face.inputs[0]); cl.new(endtop.outputs[0], face.inputs[1])
tmask = cn.new("ShaderNodeMath"); tmask.operation = "MULTIPLY"
cl.new(tape.outputs[0], tmask.inputs[0]); cl.new(face.outputs[0], tmask.inputs[1])
tcol = cn.new("ShaderNodeMix"); tcol.data_type = "RGBA"
cl.new(tmask.outputs[0], tcol.inputs["Factor"])
cl.new(cr.outputs["Color"], tcol.inputs[6])
tcol.inputs[7].default_value = (*C.srgb("#9C7448"), 1)
cl.new(pk.out_of_type(tcol, "RGBA"), cb.inputs["Base Color"])
trough = cn.new("ShaderNodeMapRange")
trough.inputs["To Min"].default_value, trough.inputs["To Max"].default_value = 0.82, 0.35
cl.new(tmask.outputs[0], trough.inputs["Value"])
cl.new(trough.outputs[0], cb.inputs["Roughness"])

bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
bmesh.ops.scale(bm, vec=CART, verts=bm.verts)
bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.004, segments=2, affect="EDGES")
carton_me = bpy.data.meshes.new("carton")
bm.to_mesh(carton_me)
bm.free()
carton_me.materials.append(carton)
carton_me.shade_smooth()
carton_me.set_sharp_from_angle(angle=math.radians(40))


def load(cx, cy, rot, layers):
    """3 x 3 cartons per layer on a 1200 x 800 pallet."""
    R = Matrix.Rotation(rot, 4, "Z")
    for k in range(layers):
        for i in range(3):
            for j in range(3):
                ob = bpy.data.objects.new("carton", carton_me)
                scene.collection.objects.link(ob)
                lx = (i - 1) * (CART[0] + 0.002) + random.uniform(-0.004, 0.004)
                ly = (j - 1) * (CART[1] + 0.002) + random.uniform(-0.004, 0.004)
                p = R @ Vector((lx, ly, 0))
                ob.location = (cx + p.x, cy + p.y, FLOOR_Z + 0.144 + CART[2] / 2 + k * (CART[2] + 0.001))
                ob.rotation_euler = (0, 0, rot + random.uniform(-0.012, 0.012))


# floor-fit layout (floorFit in src/lib/containers.ts): x across the box, y along it, from the far end
placed = []
for i in range(7):                                   # strip of pallets turned 90 deg (800 along the box)
    placed.append((-IW / 2 + 0.6, -IL / 2 + 0.4 + i * 0.8, 0.0))
for i in range(4):                                   # strip with the long side along the box
    placed.append((-IW / 2 + 1.2 + 0.4, -IL / 2 + 0.6 + i * 1.2, math.pi / 2))
for n_, (px, py, rot) in enumerate(placed):
    inst = bpy.data.objects.new("pallet", None)
    inst.instance_type = "COLLECTION"
    inst.instance_collection = src
    scene.collection.objects.link(inst)
    inst.location = (px, py, FLOOR_Z)
    inst.rotation_euler = (0, 0, rot + random.uniform(-0.004, 0.004))
    load(px, py, rot, 5 if n_ % 4 else 4)

# ------------------------------------------------------------------ yard, sky and sun
BG = "#E6E6E3"
yard = bpy.data.materials.new("yard")
yard.use_nodes = True
yn, yl = yard.node_tree.nodes, yard.node_tree.links
yb = yn["Principled BSDF"]
yb.inputs["Roughness"].default_value = 0.86
ytc = yn.new("ShaderNodeTexCoord")
slab = yn.new("ShaderNodeTexBrick")
slab.offset = 0.0
slab.inputs["Scale"].default_value = 1.0
slab.inputs["Brick Width"].default_value = 6.0
slab.inputs["Row Height"].default_value = 6.0
slab.inputs["Mortar Size"].default_value = 0.008
slab.inputs["Color1"].default_value = (*C.srgb("#DAD7D1"), 1)
slab.inputs["Color2"].default_value = (*C.srgb("#D3D0C9"), 1)
slab.inputs["Mortar"].default_value = (*C.srgb("#A8A49C"), 1)
yl.new(ytc.outputs["Object"], slab.inputs["Vector"])
yz = yn.new("ShaderNodeTexNoise"); yz.inputs["Scale"].default_value = 0.6; yz.inputs["Detail"].default_value = 9.0
yl.new(ytc.outputs["Object"], yz.inputs["Vector"])
yr = yn.new("ShaderNodeValToRGB")
yr.color_ramp.elements[0].color = (0.88, 0.88, 0.87, 1)
yr.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1)
yl.new(yz.outputs["Fac"], yr.inputs["Fac"])
ymul = yn.new("ShaderNodeMix"); ymul.data_type = "RGBA"; ymul.blend_type = "MULTIPLY"
ymul.inputs["Factor"].default_value = 1.0
yl.new(slab.outputs["Color"], ymul.inputs[6]); yl.new(yr.outputs["Color"], ymul.inputs[7])
yl.new(pk.out_of_type(ymul, "RGBA"), yb.inputs["Base Color"])
yfine = yn.new("ShaderNodeTexNoise"); yfine.inputs["Scale"].default_value = 300.0
ybump = yn.new("ShaderNodeBump"); ybump.inputs["Strength"].default_value = 0.12
yl.new(yfine.outputs["Fac"], ybump.inputs["Height"])
yl.new(ybump.outputs["Normal"], yb.inputs["Normal"])
ycam = yn.new("ShaderNodeCameraData")
yfade = yn.new("ShaderNodeMapRange")
yfade.interpolation_type = "SMOOTHSTEP"
yfade.inputs["From Min"].default_value, yfade.inputs["From Max"].default_value = 14.0, 42.0
yl.new(ycam.outputs["View Distance"], yfade.inputs["Value"])
yem = yn.new("ShaderNodeEmission")
yem.inputs["Color"].default_value = (*C.srgb(BG), 1)
ymix = yn.new("ShaderNodeMixShader")
yl.new(yfade.outputs[0], ymix.inputs["Fac"])
yl.new(yb.outputs["BSDF"], ymix.inputs[1]); yl.new(yem.outputs[0], ymix.inputs[2])
yl.new(ymix.outputs[0], yn["Material Output"].inputs["Surface"])
C.plane("yard", 200, 200, material=yard)

w = C.world("#EEF1F5", 0.9)
wn, wl = w.node_tree.nodes, w.node_tree.links
cam_bg = wn.new("ShaderNodeBackground")
cam_bg.inputs["Color"].default_value = (*C.srgb(BG), 1)
lp = wn.new("ShaderNodeLightPath")
wmix = wn.new("ShaderNodeMixShader")
wl.new(lp.outputs["Is Camera Ray"], wmix.inputs["Fac"])
wl.new(wn["Background"].outputs[0], wmix.inputs[1]); wl.new(cam_bg.outputs[0], wmix.inputs[2])
wl.new(wmix.outputs[0], wn["World Output"].inputs["Surface"])
sun = C.sun("sun", 4.0, color="#FFEEDC", angle_deg=1.5)
C.aim_sun(sun, elev_deg=30, azim_deg=-104)          # behind the doors: lights them and rakes the near side wall

# ------------------------------------------------------------------ camera
cam = C.camera(lens=40)
cam.data.clip_end = 400
tgt = bpy.data.objects.new("target", None)
scene.collection.objects.link(tgt)
con = cam.constraints.new("TRACK_TO")
con.target = tgt
con.track_axis = "TRACK_NEGATIVE_Z"
con.up_axis = "UP_Y"
cam.data.dof.use_dof = True
cam.data.dof.focus_object = tgt
cam.data.dof.aperture_fstop = 9.0


def key(f, loc, look, lens, shift=0.0):
    cam.location = loc
    cam.keyframe_insert("location", frame=f)
    tgt.location = look
    tgt.keyframe_insert("location", frame=f)
    cam.data.lens = lens
    cam.data.keyframe_insert("lens", frame=f)
    cam.data.shift_x = shift
    cam.data.keyframe_insert("shift_x", frame=f)


key(0,   (5.2, 10.4, 1.25), (0.2, 1.2, 1.3), 45, -0.10)      # rear three-quarter, low, doors shut
key(40,  (4.3, 9.3, 1.3),   (0.1, 1.5, 1.25), 45, -0.08)
key(84,  (0.25, 6.9, 1.55), (0.0, 0.0, 1.05), 40, 0.0)       # square on to the open doors
key(102, (0.15, 6.3, 1.6),  (0.0, 0.0, 1.05), 40, 0.0)
key(126, (3.4, 6.0, 6.0),   (0.1, 0.2, 0.9), 38, 0.0)       # rising over the box, swinging round
key(149, (4.6, 0.2, 9.6),   (0.25, -0.1, 0.8), 40, 0.0)      # the floor plan from above, box across the frame


# ------------------------------------------------------------------ per-frame motion
def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


OPEN = math.radians(252)
for f in C.frame_list(COUNT):
    scene.frame_set(f)
    for side, bp, d in bar_pivots:
        t0 = 4 if side == -1 else 22
        bp.rotation_euler = (0, 0, d * math.radians(88) * ease((f - t0) / 12))
    first = ease((f - 16) / 44)     # the leaf on the right as you face the doors (-x)
    second = ease((f - 34) / 44)
    door_pivots[1].rotation_euler = (0, 0, OPEN * first)
    door_pivots[0].rotation_euler = (0, 0, -OPEN * second)
    up = ease((f - 106) / 26)
    roof.location = (-4.5 * ease((f - 112) / 24), 0, 3.2 * up)
    roof.hide_render = f >= 138
    C.render_to(os.path.join(C.args.out, f"{f:03d}.webp"))
