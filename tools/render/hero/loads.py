"""PROTOTYPE round 10: eleven loads, one for each industry that ships on EPAL pallets (decisions #69-#75). Every load is
unbranded (no names, logos or readable text) and sits on the deck of an EPAL 1 (1200 x 800 mm). Import inside
Blender after common.py; build(key, parent, deck_z) returns an Empty holding the load, so a scene can lift it away
or lower it in as one piece.

Load coordinates: x along the pallet's length (+-0.6 m), y across (+-0.4 m), z up from the deck.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

import common as C

INDUSTRIES = [
    ("fmcg", "FMCG", "Bottled drinks, layered and stretch-wrapped"),
    ("pharma", "Pharmaceuticals", "Medicine cartons under a thermal cover"),
    ("chemicals", "Chemicals & Polymers", "Two 200-litre drums"),
    ("automotive", "Automotive", "New tyres"),
    ("engineering", "Engineering & Heavy Industries", "An industrial motor"),
    ("manufacturing", "Manufacturing", "Copper wire on reels"),
    ("logistics", "Logistics & Warehousing", "Mixed cartons, stretch-wrapped"),
    ("exports", "Exporters & Importers", "Jute sacks of spices and coffee"),
    ("food", "Food & Agriculture", "Crates of mangoes"),
    ("textiles", "Textiles & Apparel", "Rolls of indigo-dyed cloth"),
    ("building", "Building Materials", "Clay bricks"),
]
scene = C.scene
_mats = {}


# ------------------------------------------------------------------ helpers
def pbsdf(name, colour, rough=0.5, metal=0.0, trans=0.0, ior=1.45, coat=0.0, spec=0.5):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*C.srgb(colour), 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["IOR"].default_value = ior
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Specular IOR Level"].default_value = spec
    _mats[name] = m
    return m


def node_mat(name, build):
    """A material whose Principled BSDF the callback wires up: build(nodes, links, bsdf)."""
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    build(n, l, n["Principled BSDF"])
    _mats[name] = m
    return m


def noise_ramp(n, l, coord, scale, c0, c1, detail=6.0, p0=0.3, p1=0.75):
    nz = n.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = detail
    l.new(coord, nz.inputs["Vector"])
    r = n.new("ShaderNodeValToRGB")
    r.color_ramp.elements[0].position, r.color_ramp.elements[1].position = p0, p1
    r.color_ramp.elements[0].color = (*C.srgb(c0), 1)
    r.color_ramp.elements[1].color = (*C.srgb(c1), 1)
    l.new(nz.outputs["Fac"], r.inputs["Fac"])
    return r, nz


def bump(n, l, height, strength, bsdf):
    b = n.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    l.new(height, b.inputs["Height"])
    l.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return b


def holder(key, parent, deck_z):
    e = bpy.data.objects.new(f"load_{key}", None)
    scene.collection.objects.link(e)
    e.parent = parent
    e.location = (0, 0, deck_z)
    return e


def put(ob, parent, loc, rot=(0, 0, 0)):
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def twin(src, parent, loc, rot=(0, 0, 0)):
    """A copy that shares the mesh (cheap for hundreds of bottles or bricks)."""
    ob = src.copy()
    scene.collection.objects.link(ob)
    return put(ob, parent, loc, rot)


def box(name, size, mat, bevel=0.0, segs=2):
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        bv = ob.modifiers.new("bevel", "BEVEL")
        bv.width, bv.segments = bevel, segs
        bv.limit_method = "ANGLE"
    ob.data.materials.append(mat)
    return ob


def lathe(name, profile, mats=None, steps=48, mat_of=None, smooth=True):
    """A body of revolution around Z from a profile [(r, z), ...] (bottom to top). mat_of(i) gives the material
    index of the i-th profile segment."""
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0, z)) for r, z in profile]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    res = bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=math.tau, steps=steps, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if mat_of:
        zs = [z for _, z in profile]
        for f in bm.faces:
            zc = sum(v.co.z for v in f.verts) / len(f.verts)
            k = max(i for i in range(len(zs) - 1) if zs[i] <= zc + 1e-6) if zc >= zs[0] else 0
            f.material_index = mat_of(k)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    for m in mats or []:
        me.materials.append(m)
    if smooth:
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(40))
    return ob


def wrap_film(name, parent, size, z0, wrinkle=0.006):
    """Stretch film round the sides of a load: a thin, glossy, barely-there sleeve with soft wrinkles."""
    film = node_mat("stretch_film", lambda n, l, b: (
        b.inputs["Base Color"].__setattr__("default_value", (0.96, 0.97, 0.98, 1)),
        b.inputs["Roughness"].__setattr__("default_value", 0.08),
        b.inputs["Transmission Weight"].__setattr__("default_value", 0.96),
        b.inputs["IOR"].__setattr__("default_value", 1.35),
        b.inputs["Alpha"].__setattr__("default_value", 0.5)))
    sx, sy, sz = size
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for f in [f for f in bm.faces if abs(f.normal.z) > 0.5]:      # open top and bottom: a sleeve
        bm.faces.remove(f)
    bm.to_mesh(ob.data)
    bm.free()
    bv = ob.modifiers.new("round", "BEVEL")
    bv.width, bv.segments = 0.02, 4
    sd = ob.modifiers.new("fine", "SUBSURF")
    sd.levels = sd.render_levels = 3
    sd.subdivision_type = "SIMPLE"
    tex = bpy.data.textures.get("film_wrinkles") or bpy.data.textures.new("film_wrinkles", "CLOUDS")
    tex.noise_scale = 0.05
    dp = ob.modifiers.new("wrinkles", "DISPLACE")
    dp.texture, dp.strength, dp.texture_coords = tex, wrinkle, "OBJECT"
    ob.data.materials.append(film)
    ob.data.shade_smooth()
    return put(ob, parent, (0, 0, z0 + sz / 2))


# ------------------------------------------------------------------ materials shared by several loads
def kraft():
    def b(n, l, bsdf):
        tc = n.new("ShaderNodeTexCoord")
        r, nz = noise_ramp(n, l, tc.outputs["Object"], 18.0, "#B98E5C", "#C9A06C")
        l.new(r.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.85
        bump(n, l, nz.outputs["Fac"], 0.05, bsdf)
    return node_mat("kraft", b)


def white_card():
    return pbsdf("white_card", "#F2F1ED", rough=0.7)


def label_mat():
    """A shipping label: white, with a bar-code-like block of thin stripes and two grey lines (nothing readable)."""
    def b(n, l, bsdf):
        tc = n.new("ShaderNodeTexCoord")
        sep = n.new("ShaderNodeSeparateXYZ")
        l.new(tc.outputs["UV"], sep.inputs[0])
        wave = n.new("ShaderNodeTexWave")
        wave.bands_direction = "X"
        wave.wave_profile = "SAW"
        wave.inputs["Scale"].default_value = 60.0
        wave.inputs["Distortion"].default_value = 0.0
        l.new(tc.outputs["UV"], wave.inputs["Vector"])
        st = n.new("ShaderNodeMath")
        st.operation = "GREATER_THAN"
        st.inputs[1].default_value = 0.55
        l.new(wave.outputs["Fac"], st.inputs[0])
        inband = n.new("ShaderNodeMapRange")
        inband.interpolation_type = "STEPPED"
        inband.inputs["From Min"].default_value, inband.inputs["From Max"].default_value = 0.08, 0.5
        l.new(sep.outputs["Y"], inband.inputs["Value"])
        win = n.new("ShaderNodeMath")
        win.operation = "LESS_THAN"
        win.inputs[1].default_value = 0.45
        l.new(sep.outputs["Y"], win.inputs[0])
        a = n.new("ShaderNodeMath")
        a.operation = "MULTIPLY"
        l.new(st.outputs[0], a.inputs[0])
        l.new(win.outputs[0], a.inputs[1])
        mix = n.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        l.new(a.outputs[0], mix.inputs["Factor"])
        mix.inputs["A"].default_value = (*C.srgb("#F7F6F2"), 1)
        mix.inputs["B"].default_value = (*C.srgb("#222222"), 1)
        l.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.6
    return node_mat("label", b)


def plane_label(name, w, h, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for lp, co in zip(me.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[lp.index].uv = co
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


def steel_band():
    return pbsdf("steel_band", "#8C9096", rough=0.35, metal=1.0)


def bands(parent, xs, ly, lz, z0, mat=None, w=0.019):
    """Strapping over the top and down both long sides at each x."""
    mat = mat or steel_band()
    for x in xs:
        top = box("band", (w, ly + 0.006, 0.0012), mat)
        put(top, parent, (x, 0, z0 + lz + 0.0006))
        for s in (-1, 1):
            side = box("band", (w, 0.0012, lz), mat)
            put(side, parent, (x, s * (ly / 2 + 0.0006), z0 + lz / 2))


# ================================================================== the loads
def fmcg(e, rng):
    """Bottled drinks: 1-litre PET bottles, 4 layers on card slip sheets, stretch-wrapped."""
    pet = pbsdf("pet", "#E6F1F7", rough=0.04, trans=1.0, ior=1.33, spec=0.6)
    cap = pbsdf("cap", "#1D5FB8", rough=0.35)
    lab = pbsdf("bottle_label", "#2F7FD0", rough=0.45)
    prof = [(0.0, 0.0), (0.030, 0.0), (0.036, 0.006), (0.037, 0.02), (0.037, 0.085), (0.0385, 0.09), (0.0385, 0.155),
            (0.037, 0.16), (0.037, 0.18), (0.030, 0.205), (0.017, 0.232), (0.0145, 0.24), (0.0145, 0.25),
            (0.0165, 0.252), (0.0165, 0.27), (0.0, 0.271)]
    bottle = lathe("bottle", prof, [pet, lab, cap], steps=32,
                   mat_of=lambda k: 2 if k >= 13 else (1 if k in (5,) else 0))
    D = 0.079
    nx, ny, layers, h = 15, 10, 4, 0.272
    for k in range(layers):
        z = k * (h + 0.004)
        sheet = box("slip", (1.19, 0.79, 0.003), kraft())
        put(sheet, e, (0, 0, z + 0.0015))
        for i in range(nx):
            for j in range(ny):
                twin(bottle, e, ((i - (nx - 1) / 2) * D, (j - (ny - 1) / 2) * D, z + 0.003),
                     (0, 0, rng.uniform(0, 6.28)))
    top = box("top_sheet", (1.19, 0.79, 0.004), kraft())
    put(top, e, (0, 0, layers * (h + 0.004) + 0.002))
    bottle.hide_render = True
    bottle.hide_viewport = True
    wrap_film("film", e, (1.2, 0.8, layers * (h + 0.004) - 0.03), 0.02, wrinkle=0.004)


def pharma(e, rng):
    """Medicine cartons on a card base, under a quilted silver thermal cover with a temperature logger."""
    def quilt(n, l, b):
        tc = n.new("ShaderNodeTexCoord")
        mp = n.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (0, 0, math.radians(45))
        l.new(tc.outputs["Object"], mp.inputs["Vector"])
        sep = n.new("ShaderNodeSeparateXYZ")
        l.new(mp.outputs["Vector"], sep.inputs[0])
        waves = []
        for axis in ("X", "Y", "Z"):
            w = n.new("ShaderNodeMath")
            w.operation = "SINE"
            sc = n.new("ShaderNodeMath")
            sc.operation = "MULTIPLY"
            sc.inputs[1].default_value = 2 * math.pi / 0.11
            l.new(sep.outputs[axis], sc.inputs[0])
            l.new(sc.outputs[0], w.inputs[0])
            ab = n.new("ShaderNodeMath")
            ab.operation = "ABSOLUTE"
            l.new(w.outputs[0], ab.inputs[0])
            waves.append(ab)
        m1 = n.new("ShaderNodeMath")
        m1.operation = "MINIMUM"
        l.new(waves[0].outputs[0], m1.inputs[0])
        l.new(waves[1].outputs[0], m1.inputs[1])
        m2 = n.new("ShaderNodeMath")
        m2.operation = "MINIMUM"
        l.new(m1.outputs[0], m2.inputs[0])
        l.new(waves[2].outputs[0], m2.inputs[1])
        pw = n.new("ShaderNodeMath")
        pw.operation = "POWER"
        pw.inputs[1].default_value = 0.35
        l.new(m2.outputs[0], pw.inputs[0])
        b.inputs["Base Color"].default_value = (*C.srgb("#AEB4BC"), 1)
        b.inputs["Metallic"].default_value = 1.0
        b.inputs["Roughness"].default_value = 0.24
        bump(n, l, pw.outputs[0], 0.9, b)
    cover_m = node_mat("thermal", quilt)
    for i in range(3):
        for j in range(2):
            c = box("carton", (0.39, 0.38, 0.12), white_card(), bevel=0.003)
            put(c, e, ((i - 1) * 0.395, (j - 0.5) * 0.385, 0.06))
    H = 0.92
    cover = box("cover", (1.21, 0.81, H), cover_m, bevel=0.05, segs=6)
    sd = cover.modifiers.new("fine", "SUBSURF")
    sd.levels = sd.render_levels = 2
    sd.subdivision_type = "SIMPLE"
    tex = bpy.data.textures.new("cover_soft", "CLOUDS")
    tex.noise_scale = 0.3
    dp = cover.modifiers.new("soft", "DISPLACE")
    dp.texture, dp.strength, dp.texture_coords = tex, 0.012, "OBJECT"
    cover.data.shade_smooth()
    put(cover, e, (0, 0, 0.1 + H / 2))
    logger = box("logger", (0.07, 0.018, 0.1), pbsdf("logger", "#2B2E33", rough=0.4), bevel=0.006)
    put(logger, e, (0.32, -0.416, 0.62))
    screen = box("logger_screen", (0.05, 0.002, 0.03), pbsdf("logger_screen", "#9FB4A2", rough=0.2), bevel=0.002)
    put(screen, e, (0.32, -0.426, 0.64))
    tag = plane_label("cover_label", 0.16, 0.1, label_mat())
    put(tag, e, (-0.25, -0.418, 0.55))


def chemicals(e, rng):
    """Two 200-litre tight-head HDPE drums with rolling hoops and two bungs each."""
    hdpe = pbsdf("hdpe_blue", "#12398A", rough=0.3, spec=0.55, coat=0.2)
    R, Hd = 0.29, 0.935
    prof = [(0.0, 0.0), (R - 0.03, 0.0), (R - 0.005, 0.01), (R, 0.03), (R, 0.28), (R + 0.012, 0.3), (R + 0.012, 0.33),
            (R, 0.35), (R, 0.58), (R + 0.012, 0.6), (R + 0.012, 0.63), (R, 0.65), (R, Hd - 0.04), (R + 0.006, Hd - 0.02),
            (R + 0.006, Hd), (R - 0.02, Hd), (R - 0.03, Hd - 0.012), (0.0, Hd - 0.012)]
    drum = lathe("drum", prof, [hdpe], steps=72)
    bung = lathe("bung", [(0.0, 0.0), (0.03, 0.0), (0.03, 0.018), (0.024, 0.024), (0.0, 0.024)], [hdpe], steps=24)
    small = lathe("bung_small", [(0.0, 0.0), (0.018, 0.0), (0.018, 0.014), (0.0, 0.016)], [hdpe], steps=20)
    for s in (-1, 1):
        d = twin(drum, e, (s * 0.3, 0, 0), (0, 0, rng.uniform(0, 6.28)))
        twin(bung, e, (s * 0.3 + 0.17, 0.08, Hd - 0.012))
        twin(small, e, (s * 0.3 - 0.17, -0.08, Hd - 0.012))
    for ob in (drum, bung, small):
        ob.hide_render = ob.hide_viewport = True


def automotive(e, rng):
    """New tyres (185/60 R15, about 600 mm across), two stacks of six."""
    def rubber(n, l, b):
        tc = n.new("ShaderNodeTexCoord")
        geo = n.new("ShaderNodeNewGeometry")
        grad = n.new("ShaderNodeTexGradient")               # angle round the tyre
        grad.gradient_type = "RADIAL"
        l.new(tc.outputs["Object"], grad.inputs["Vector"])
        lugs = n.new("ShaderNodeMath")
        lugs.operation = "MULTIPLY"
        lugs.inputs[1].default_value = 96.0
        l.new(grad.outputs["Fac"], lugs.inputs[0])
        fr = n.new("ShaderNodeMath")
        fr.operation = "FRACT"
        l.new(lugs.outputs[0], fr.inputs[0])
        sep = n.new("ShaderNodeSeparateXYZ")
        l.new(tc.outputs["Object"], sep.inputs[0])
        zz = n.new("ShaderNodeMath")                        # three circumferential grooves across the tread
        zz.operation = "MULTIPLY"
        zz.inputs[1].default_value = 2 * math.pi * 4 / 0.15
        l.new(sep.outputs["Z"], zz.inputs[0])
        sz = n.new("ShaderNodeMath")
        sz.operation = "COSINE"
        l.new(zz.outputs[0], sz.inputs[0])
        groove = n.new("ShaderNodeMath")
        groove.operation = "GREATER_THAN"
        groove.inputs[1].default_value = 0.85
        l.new(sz.outputs[0], groove.inputs[0])
        blk = n.new("ShaderNodeMath")
        blk.operation = "GREATER_THAN"
        blk.inputs[1].default_value = 0.78
        l.new(fr.outputs[0], blk.inputs[0])
        mx = n.new("ShaderNodeMath")
        mx.operation = "MAXIMUM"
        l.new(groove.outputs[0], mx.inputs[0])
        l.new(blk.outputs[0], mx.inputs[1])
        sepn = n.new("ShaderNodeSeparateXYZ")               # only on the tread (normals facing outwards)
        l.new(geo.outputs["Normal"], sepn.inputs[0])
        nz = n.new("ShaderNodeMath")
        nz.operation = "ABSOLUTE"
        l.new(sepn.outputs["Z"], nz.inputs[0])
        tread = n.new("ShaderNodeMath")
        tread.operation = "LESS_THAN"
        tread.inputs[1].default_value = 0.35
        l.new(nz.outputs[0], tread.inputs[0])
        h = n.new("ShaderNodeMath")
        h.operation = "MULTIPLY"
        l.new(mx.outputs[0], h.inputs[0])
        l.new(tread.outputs[0], h.inputs[1])
        inv = n.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        l.new(h.outputs[0], inv.inputs[1])
        b.inputs["Base Color"].default_value = (*C.srgb("#1B1B1D"), 1)
        b.inputs["Roughness"].default_value = 0.72
        b.inputs["Specular IOR Level"].default_value = 0.35
        bump(n, l, inv.outputs[0], 1.0, b)
    rub = node_mat("rubber", rubber)
    Ro, Ri, Wt = 0.300, 0.192, 0.185
    G, gd = 0.009, 0.009                                    # tread grooves: width and depth
    tread = [(Ro, 0.04)]
    for zc in (0.068, Wt / 2, Wt - 0.068):                 # three circumferential grooves across the tread
        tread += [(Ro, zc - G / 2), (Ro - gd, zc - G / 2 + 0.001), (Ro - gd, zc + G / 2 - 0.001), (Ro, zc + G / 2)]
    tread += [(Ro, Wt - 0.04)]
    prof = ([(Ri, 0.0), (Ri + 0.006, 0.0), (Ri + 0.012, 0.006), (Ri + 0.022, 0.006),   # the bead and a rim-protector lip
             (Ri + 0.045, 0.01), (Ro - 0.07, 0.014), (Ro - 0.066, 0.018), (Ro - 0.05, 0.018), (Ro - 0.022, 0.026),
             (Ro - 0.006, 0.036)] + tread +
            [(Ro - 0.006, Wt - 0.036), (Ro - 0.022, Wt - 0.026), (Ro - 0.05, Wt - 0.018), (Ro - 0.066, Wt - 0.018),
             (Ro - 0.07, Wt - 0.014), (Ri + 0.045, Wt - 0.01), (Ri + 0.022, Wt - 0.006), (Ri + 0.012, Wt - 0.006),
             (Ri + 0.006, Wt), (Ri, Wt), (Ri - 0.004, Wt / 2), (Ri, 0.0)])
    tyre = lathe("tyre", prof, [rub], steps=144)
    sd = tyre.modifiers.new("smooth", "SUBSURF")
    sd.levels = sd.render_levels = 1
    for s in (-1, 1):
        for k in range(6):
            twin(tyre, e, (s * 0.3, 0, k * (Wt + 0.002)), (0, 0, rng.uniform(0, 6.28)))
    tyre.hide_render = tyre.hide_viewport = True


def engineering(e0, rng):
    """An industrial electric motor (frame size around 280) bolted to two hardwood skids: finned cast frame, feet,
    terminal box with a cable gland, fan cowl, shaft with its key, lifting eye."""
    paint = pbsdf("motor_paint", "#2C4C7C", rough=0.38, coat=0.4)
    steel = pbsdf("shaft_steel", "#C9CDD2", rough=0.18, metal=1.0)
    black = pbsdf("rubber_dark", "#202124", rough=0.6)
    for s in (-1, 1):
        skid = box("skid", (0.18, 0.74, 0.06), pbsdf("skid", "#9A7650", rough=0.8), bevel=0.004)
        put(skid, e0, (s * 0.24, 0, 0.03))
    e = bpy.data.objects.new("motor", None)
    scene.collection.objects.link(e)
    put(e, e0, (0, 0, 0.06))
    R, Lm, axis_z = 0.2, 0.72, 0.30
    body = lathe("motor_body", [(0.0, 0.0), (R, 0.0), (R, Lm), (0.0, Lm)], [paint], steps=64)
    put(body, e, (-Lm / 2, 0, axis_z), (0, math.radians(90), 0))
    for k in range(28):                                     # cooling fins along the frame (none where the feet are)
        a = k / 28 * math.tau
        if math.sin(a) < -0.75:
            continue
        fin = box("fin", (Lm - 0.06, 0.006, 0.05), paint, bevel=0.0015)
        put(fin, e, (0, math.cos(a) * (R + 0.022), axis_z + math.sin(a) * (R + 0.022)), (a + math.radians(90), 0, 0))
    for s in (-1, 1):
        foot = box("foot", (0.12, 0.5, 0.05), paint, bevel=0.004)
        put(foot, e, (s * 0.24, 0, 0.025))
        web = box("foot_web", (0.08, 0.4, axis_z - 0.12), paint, bevel=0.003)
        put(web, e, (s * 0.24, 0, 0.05 + (axis_z - 0.12) / 2))
        for t in (-1, 1):                                   # hold-down bolts through the feet into the skid
            bolt = lathe("bolt", [(0.0, 0.0), (0.016, 0.0), (0.016, 0.012), (0.0, 0.012)], [steel], steps=6, smooth=False)
            put(bolt, e, (s * 0.24, t * 0.2, 0.05))
    for x in (-Lm / 2 - 0.02, Lm / 2 + 0.02):                # end shields
        sh = lathe("shield", [(0.0, 0.0), (R + 0.012, 0.0), (R + 0.012, 0.04), (0.06, 0.06), (0.0, 0.06)], [paint], steps=64)
        put(sh, e, (x, 0, axis_z), (0, math.radians(90 if x > 0 else -90), 0))
    cowl = lathe("cowl", [(0.0, 0.0), (R + 0.005, 0.0), (R + 0.01, 0.16), (R - 0.02, 0.2), (0.0, 0.205)], [paint], steps=64)
    put(cowl, e, (-Lm / 2 - 0.05, 0, axis_z), (0, math.radians(-90), 0))
    shaft = lathe("shaft", [(0.0, 0.0), (0.04, 0.0), (0.04, 0.17), (0.035, 0.175), (0.0, 0.175)], [steel], steps=32)
    put(shaft, e, (Lm / 2 + 0.06, 0, axis_z), (0, math.radians(90), 0))
    key = box("key", (0.12, 0.016, 0.01), steel)
    put(key, e, (Lm / 2 + 0.14, 0, axis_z + 0.04))
    tb = box("terminal_box", (0.24, 0.22, 0.13), paint, bevel=0.012, segs=3)
    put(tb, e, (0.05, 0, axis_z + R + 0.05))
    lid = box("terminal_lid", (0.25, 0.23, 0.02), paint, bevel=0.008, segs=3)
    put(lid, e, (0.05, 0, axis_z + R + 0.125))
    gland = lathe("gland", [(0.0, 0.0), (0.022, 0.0), (0.022, 0.03), (0.016, 0.045), (0.0, 0.045)], [black], steps=20)
    put(gland, e, (0.05, -0.11, axis_z + R + 0.05), (math.radians(90), 0, 0))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.035, minor_radius=0.009, major_segments=32, minor_segments=12)
    eye = bpy.context.active_object
    eye.data.materials.append(steel)
    eye.data.shade_smooth()
    put(eye, e, (-0.2, 0, axis_z + R + 0.06), (math.radians(90), 0, 0))


def manufacturing(e, rng):
    """Enamelled copper wire on black reels: two layers of six, a card sheet between them."""
    def copper(n, l, b):
        tc = n.new("ShaderNodeTexCoord")
        wave = n.new("ShaderNodeTexWave")
        wave.bands_direction = "Z"
        wave.inputs["Scale"].default_value = 220.0
        wave.inputs["Distortion"].default_value = 0.3
        l.new(tc.outputs["Object"], wave.inputs["Vector"])
        b.inputs["Base Color"].default_value = (*C.srgb("#C26A3A"), 1)
        b.inputs["Metallic"].default_value = 1.0
        b.inputs["Roughness"].default_value = 0.22
        bump(n, l, wave.outputs["Fac"], 0.25, b)
    cu = node_mat("copper", copper)
    reel_m = pbsdf("reel", "#1E1F22", rough=0.45)
    Rf, Rw, Hr = 0.185, 0.16, 0.3
    prof = [(0.03, 0.0), (Rf, 0.0), (Rf, 0.018), (Rw, 0.022), (Rw, Hr - 0.022), (Rf, Hr - 0.018), (Rf, Hr), (0.03, Hr),
            (0.03, 0.0)]
    reel = lathe("reel", prof, [reel_m, cu], steps=72, mat_of=lambda k: 1 if k == 3 else 0)
    for k in range(2):
        z = k * (Hr + 0.006)
        if k:
            put(box("slip", (1.19, 0.79, 0.004), kraft()), e, (0, 0, z - 0.002))
        for i in range(3):
            for j in range(2):
                twin(reel, e, ((i - 1) * 0.39, (j - 0.5) * 0.39, z), (0, 0, rng.uniform(0, 6.28)))
    reel.hide_render = reel.hide_viewport = True


def logistics(e, rng):
    """Mixed cartons in a stable stack, packing tape, shipping labels, stretch-wrapped."""
    tape = pbsdf("tape", "#A8814F", rough=0.25, spec=0.7)
    lab = label_mat()
    sizes = [(0.4, 0.3, 0.3), (0.6, 0.4, 0.3), (0.3, 0.2, 0.25), (0.4, 0.4, 0.3)]
    z = 0.0
    layer_h = [0.3, 0.3, 0.3, 0.25]
    for k, h in enumerate(layer_h):
        x = -0.6
        while x < 0.58:
            w = rng.choice([0.4, 0.3, 0.6, 0.4])
            if x + w > 0.601:
                w = round(0.6 - x, 3)
            if w < 0.15:
                break
            y = -0.4
            while y < 0.39:
                d = rng.choice([0.4, 0.4, 0.3])
                if y + d > 0.401:
                    d = round(0.4 - y, 3)
                if d < 0.12:
                    break
                c = box("carton", (w - 0.006, d - 0.006, h - 0.004), kraft(), bevel=0.004)
                put(c, e, (x + w / 2, y + d / 2, z + h / 2))
                t = box("tape", (w - 0.004, 0.048, 0.0008), tape)
                put(t, e, (x + w / 2, y + d / 2, z + h - 0.0016))
                if y < -0.39 and rng.random() < 0.75:     # labels on the front face
                    lb = plane_label("label", 0.1, 0.07, lab)
                    put(lb, e, (x + w / 2 + rng.uniform(-0.05, 0.05), y - 0.0005, z + h * 0.6))
                y += d
            x += w
        z += h
    wrap_film("film", e, (1.21, 0.81, z - 0.02), 0.01)


def exports(e, rng):
    """50 kg jute sacks (spices, coffee): woven, stitched, soft; six layers, turned each layer."""
    def jute(n, l, b):
        tc = n.new("ShaderNodeTexCoord")
        w1 = n.new("ShaderNodeTexWave")
        w1.bands_direction = "X"
        w1.inputs["Scale"].default_value = 320.0
        w1.inputs["Distortion"].default_value = 0.15
        w2 = n.new("ShaderNodeTexWave")
        w2.bands_direction = "Y"
        w2.inputs["Scale"].default_value = 320.0
        w2.inputs["Distortion"].default_value = 0.15
        l.new(tc.outputs["Object"], w1.inputs["Vector"])
        l.new(tc.outputs["Object"], w2.inputs["Vector"])
        mx = n.new("ShaderNodeMath")
        mx.operation = "MAXIMUM"
        l.new(w1.outputs["Fac"], mx.inputs[0])
        l.new(w2.outputs["Fac"], mx.inputs[1])
        r, nz = noise_ramp(n, l, tc.outputs["Object"], 8.0, "#6E5130", "#9C7A4C")
        mul = n.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 0.55
        l.new(r.outputs["Color"], mul.inputs["A"])
        l.new(mx.outputs[0], mul.inputs["B"])
        l.new(mul.outputs["Result"], b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.95
        bump(n, l, mx.outputs[0], 0.6, b)
    jm = node_mat("jute", jute)
    SL, SW, SH = 0.6, 0.4, 0.16
    for k in range(6):
        turned = k % 2
        for i in range(2):
            for j in range(2):
                sack = box("sack", (SL - 0.02, SW - 0.02, SH), jm, bevel=0.06, segs=6)
                sd = sack.modifiers.new("fine", "SUBSURF")
                sd.levels = sd.render_levels = 2
                sd.subdivision_type = "SIMPLE"
                tex = bpy.data.textures.get("lumps") or bpy.data.textures.new("lumps", "CLOUDS")
                tex.noise_scale = 0.12
                dp = sack.modifiers.new("lumps", "DISPLACE")
                dp.texture, dp.strength, dp.texture_coords = tex, 0.02, "OBJECT"
                sack.data.shade_smooth()
                x = (i - 0.5) * SL
                y = (j - 0.5) * SW
                put(sack, e, (x + rng.uniform(-0.01, 0.01), y + rng.uniform(-0.01, 0.01), k * (SH - 0.012) + SH / 2),
                    (rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02), math.radians(rng.uniform(-3, 3))))


def food(e, rng):
    """Mangoes in open wooden crates, three layers of four crates; the top layer shows the fruit."""
    wood = pbsdf("crate_wood", "#D9B98C", rough=0.75)
    def mango(n, l, b):
        tc = n.new("ShaderNodeTexCoord")
        sep = n.new("ShaderNodeSeparateXYZ")
        l.new(tc.outputs["Object"], sep.inputs[0])
        mr = n.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = -0.045, 0.045
        l.new(sep.outputs["X"], mr.inputs["Value"])
        nz = n.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 30.0
        l.new(tc.outputs["Object"], nz.inputs["Vector"])
        add = n.new("ShaderNodeMath")
        add.operation = "MULTIPLY_ADD"
        add.inputs[1].default_value = 0.3
        l.new(nz.outputs["Fac"], add.inputs[0])
        l.new(mr.outputs[0], add.inputs[2])
        ramp = n.new("ShaderNodeValToRGB")
        cr = ramp.color_ramp
        cr.elements[0].position, cr.elements[0].color = 0.15, (*C.srgb("#7FA32E"), 1)
        cr.elements[1].position, cr.elements[1].color = 0.95, (*C.srgb("#E2482A"), 1)
        mid = cr.elements.new(0.55)
        mid.color = (*C.srgb("#F2B630"), 1)
        l.new(add.outputs[0], ramp.inputs["Fac"])
        l.new(ramp.outputs["Color"], b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.42
        b.inputs["Subsurface Weight"].default_value = 0.15
        b.inputs["Coat Weight"].default_value = 0.2
    mm = node_mat("mango", mango)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=14)
    fruit = bpy.context.active_object
    fruit.scale = (0.055, 0.04, 0.038)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for v in fruit.data.vertices:                         # the mango's kidney shape: one end fuller, a slight hook
        x = v.co.x / 0.055
        v.co.y += 0.006 * (1 - x * x) - 0.004 * x
        v.co.z *= 1 + 0.12 * x
    fruit.data.materials.append(mm)
    fruit.data.shade_smooth()
    CW, CD, CH = 0.6, 0.4, 0.25
    def crate(x, y, z):
        for sx, sy, sz, px, py, pz in (
            (CW, CD, 0.012, 0, 0, 0.006),                                 # floor
            (CW, 0.012, 0.07, 0, -CD / 2 + 0.006, 0.05), (CW, 0.012, 0.07, 0, -CD / 2 + 0.006, 0.17),
            (CW, 0.012, 0.07, 0, CD / 2 - 0.006, 0.05), (CW, 0.012, 0.07, 0, CD / 2 - 0.006, 0.17),
            (0.012, CD, 0.07, -CW / 2 + 0.006, 0, 0.05), (0.012, CD, 0.07, -CW / 2 + 0.006, 0, 0.17),
            (0.012, CD, 0.07, CW / 2 - 0.006, 0, 0.05), (0.012, CD, 0.07, CW / 2 - 0.006, 0, 0.17),
            (0.03, 0.03, CH, -CW / 2 + 0.015, -CD / 2 + 0.015, CH / 2), (0.03, 0.03, CH, CW / 2 - 0.015, -CD / 2 + 0.015, CH / 2),
            (0.03, 0.03, CH, -CW / 2 + 0.015, CD / 2 - 0.015, CH / 2), (0.03, 0.03, CH, CW / 2 - 0.015, CD / 2 - 0.015, CH / 2)):
            put(box("slat", (sx, sy, sz), wood, bevel=0.002), e, (x + px, y + py, z + pz))
        for i in range(5):
            for j in range(4):
                for kk in range(2):
                    twin(fruit, e, (x + (i - 2) * 0.108 + rng.uniform(-0.008, 0.008), y + (j - 1.5) * 0.088 + rng.uniform(-0.006, 0.006),
                                    z + 0.05 + kk * 0.072 + rng.uniform(0, 0.01)),
                         (rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), rng.uniform(0, 6.28)))
    for k in range(3):
        for i in range(2):
            for j in range(2):
                crate((i - 0.5) * CW, (j - 0.5) * CD, k * (CH + 0.004))
    fruit.hide_render = fruit.hide_viewport = True


def textiles(e, rng):
    """Rolls of indigo-dyed cotton, hex-stacked 3-2-3-2, the rolled layers showing on each end."""
    def cloth(n, l, b):
        tc = n.new("ShaderNodeTexCoord")
        r, nz = noise_ramp(n, l, tc.outputs["Object"], 3.5, "#030820", "#0E1A4E", p0=0.25, p1=1.2)
        l.new(r.outputs["Color"], b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.88
        b.inputs["Sheen Weight"].default_value = 0.25
        b.inputs["Sheen Tint"].default_value = (*C.srgb("#6F86C8"), 1)
    def ends(n, l, b):
        tc = n.new("ShaderNodeTexCoord")
        rings = n.new("ShaderNodeTexWave")
        rings.wave_type = "RINGS"
        rings.rings_direction = "X"
        rings.inputs["Scale"].default_value = 26.0
        rings.inputs["Distortion"].default_value = 1.5
        l.new(tc.outputs["Object"], rings.inputs["Vector"])
        rr = n.new("ShaderNodeValToRGB")
        rr.color_ramp.elements[0].color = (*C.srgb("#03081E"), 1)
        rr.color_ramp.elements[1].color = (*C.srgb("#16276A"), 1)
        l.new(rings.outputs["Fac"], rr.inputs["Fac"])
        l.new(rr.outputs["Color"], b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.9
    cm, em = node_mat("indigo", cloth), node_mat("roll_ends", ends)
    R0 = 0.118
    for k, n in enumerate([3, 2, 3, 2]):
        z = R0 + k * R0 * math.sqrt(3) + 0.002
        for j in range(n):
            y = (j - (n - 1) / 2) * (2 * R0 + 0.004)
            r = R0 * rng.uniform(0.95, 1.0)
            bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=1.14 + rng.uniform(-0.02, 0.01), vertices=96)
            roll = bpy.context.active_object
            roll.rotation_euler = (0, math.radians(90), 0)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            roll.data.materials.append(cm)
            roll.data.materials.append(em)
            for poly in roll.data.polygons:
                poly.use_smooth = abs(poly.normal.x) < 0.5
                poly.material_index = 1 if abs(poly.normal.x) > 0.5 else 0
            bv = roll.modifiers.new("soft", "BEVEL")
            bv.width, bv.segments, bv.limit_method = 0.008, 3, "ANGLE"
            put(roll, e, (rng.uniform(-0.01, 0.01), y, z - (R0 - r)), (math.radians(rng.uniform(0, 360)), 0, 0))


def building(e, rng):
    """Red clay bricks (230 x 110 x 75 mm), 11 courses, strapped with steel bands."""
    def clay(n, l, b):
        tc = n.new("ShaderNodeTexCoord")
        oi = n.new("ShaderNodeObjectInfo")
        r, nz = noise_ramp(n, l, tc.outputs["Object"], 40.0, "#7A2C18", "#A5482A")
        hue = n.new("ShaderNodeHueSaturation")
        sh = n.new("ShaderNodeMath")
        sh.operation = "MULTIPLY_ADD"
        sh.inputs[1].default_value = 0.25
        sh.inputs[2].default_value = 0.85
        l.new(oi.outputs["Random"], sh.inputs[0])
        l.new(sh.outputs[0], hue.inputs["Value"])
        l.new(r.outputs["Color"], hue.inputs["Color"])
        l.new(hue.outputs["Color"], b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.9
        bump(n, l, nz.outputs["Fac"], 0.3, b)
    cm = node_mat("clay", clay)
    BL, BW, BH = 0.23, 0.11, 0.075
    brick = box("brick", (BL - 0.003, BW - 0.003, BH - 0.002), cm, bevel=0.004)
    nx, ny, courses = 5, 7, 11
    for k in range(courses):
        for i in range(nx):
            for j in range(ny):
                twin(brick, e, ((i - (nx - 1) / 2) * BL, (j - (ny - 1) / 2) * BW, k * BH + BH / 2),
                     (0, 0, math.radians(rng.uniform(-0.6, 0.6))))
    brick.hide_render = brick.hide_viewport = True
    bands(e, [-0.35, 0.0, 0.35], ny * BW, courses * BH, 0.0)


BUILDERS = {k: globals()[k] for k, _, _ in INDUSTRIES}


def build(key, parent, deck_z, seed=0):
    """Build one load on the deck. Returns its holder (an Empty): move it to lift the whole load."""
    e = holder(key, parent, deck_z)
    BUILDERS[key](e, random.Random(f"{key}-{seed}"))
    return e
