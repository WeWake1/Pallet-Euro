"""Pallet builder for Blender scenes: a copy of the geometry and materials half of the Ambica render
pipeline (/Users/wewake/VSC/APIPL/apiplSite/tools/render/render_pallet.py, lines 1-741), unchanged
except for this docstring and parse_known_args (so scene scripts can add their own flags).

Exact EPAL/CP geometry from recipes.json, the approved wood look (5 Nov 2026: pale straight-grain
spruce, Wood096, eased edges, small bright nails, a few knots), and the markings from brand.json.

Use from a scene script run by Blender:
  Blender --background --factory-startup --python tools/render/hero/<scene>.py -- \
      --recipe epal1 --recipes src/data/pallet-geometry.json [scene flags]
  then:  import palletkit as pk; pk.build_recipe(pk.R); pk.ROOT is the pallet's parent empty.
"""
import argparse
import json
import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
MM = 0.001

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--recipe", required=True)
ap.add_argument("--name", help="output base name (defaults to recipe id)")
ap.add_argument("--recipes", default=os.path.join(HERE, "recipes.json"))
ap.add_argument("--brand", default=os.path.join(HERE, "brand.json"))
ap.add_argument("--out", default=os.path.join(HERE, "out"))
ap.add_argument("--views", default="1,2,3,4,5")
ap.add_argument("--res", type=int, default=1600)
ap.add_argument("--samples", type=int, default=128)
ap.add_argument("--textures", default=os.path.join(HERE, "textures"))
ap.add_argument("--glb", default="", help="also export a web GLB model to this path")
ap.add_argument("--blend", action="store_true")
ap.add_argument("--detail-index", type=int, default=0, help="view 9: which marking to frame (0 = first)")
ap.add_argument("--anim", default="", help="render the board-by-board assembly animation to this .mp4 (home hero)")
ap.add_argument("--bg", default="#FFFFFF", help="background colour of the output (the film uses the page colour)")
ap.add_argument("--pine-tex", default="Wood096", help="ambientCG texture for pine/spruce (Wood096, Wood095, ...)")
ap.add_argument("--exposure", type=float, default=1.4, help="brightness of the pallet against the background")
ap.add_argument("--anim-res", type=int, default=1280)
ap.add_argument("--anim-only", default="", help="comma-separated frame numbers to render (quick tests)")
ap.add_argument("--anim-samples", type=int, default=40)
args = ap.parse_known_args(argv)[0]

RECIPES = json.load(open(args.recipes))
R = RECIPES[args.recipe]
BRAND = json.load(open(args.brand))
NAME = args.name or args.recipe
random.seed(sum(ord(c) for c in NAME))

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def srgb(hexstr):
    h = hexstr.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def out_of_type(node, kind):
    return next(o for o in node.outputs if o.type == kind)


# ================================================================ materials (Cycles)
# Clean, fresh-sawn look (owner, Nov 2026): pale straight-grain spruce, the texture's own colour, only
# slight differences between boards. knot_amt pulls dark knots toward knot_tone; tone = per-board tint
# range (pale .. warm); fib = rough-sawn fibre shading range.
GRAIN = {"Wood096": "v", "Wood095": "u"}
# Where across each texture (u, 0..1 per tile) a board strip is free of knots, and strips with a few
# knots. Measured from the colour map (dark-blob density per column). Owner: only a few knots per pallet.
KNOT_MAP = {
    "Wood096": dict(clear=[(0.125, 0.281), (0.906, 1.062)], knotty=[0.33, 0.49]),
}
WOODS = {
    "pine": dict(tex=args.pine_tex, grain=GRAIN.get(args.pine_tex, "v"), tile=0.95, sat=1.2, hue=(0.498, 0.502),
                 val=(0.98, 1.04), contrast=-0.08, rough=(0.6, 0.85), knot=(0.22, 0.42), knot_tone="#A88356",
                 knot_amt=0.3, tone=((1.02, 1.02, 1.01), (0.95, 0.93, 0.9)), fib=(0.97, 1.02),
                 web_gain=(0.847, 0.862, 0.862)),
    "hard": dict(tex="Wood060", grain="u", tile=0.8, sat=1.25, hue=(0.496, 0.506), val=(0.92, 1.08),
                 contrast=-0.05, rough=(0.6, 0.9), knot=(0.03, 0.08), knot_tone="#5A3A26",
                 knot_amt=0.5, tone=((1.03, 1.02, 1.0), (0.92, 0.88, 0.84)), fib=(0.95, 1.03),
                 web_gain=(0.954, 1.196, 1.603)),
}
CURVE = 1.0        # photo_contrast gamma (1.0 = off); the high-key look gets its contrast from the top light
EDGE_MM = 3.0      # every board and block edge is eased (rounded) by this much, as on real sawn timber


def wood_material(name, kind="pine", tint=1.0):
    spec = WOODS[kind]
    prefix = os.path.join(args.textures, spec["tex"], spec["tex"] + "_2K-JPG_")
    tile = spec["tile"]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    bsdf = n.new("ShaderNodeBsdfPrincipled")
    l.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    tc = n.new("ShaderNodeTexCoord")
    oi = n.new("ShaderNodeObjectInfo")
    sep = n.new("ShaderNodeSeparateXYZ")
    l.new(tc.outputs["Object"], sep.inputs[0])
    nsep = n.new("ShaderNodeSeparateXYZ")
    l.new(tc.outputs["Normal"], nsep.inputs[0])
    r2m = n.new("ShaderNodeMath"); r2m.operation = "MULTIPLY"
    l.new(oi.outputs["Random"], r2m.inputs[0]); r2m.inputs[1].default_value = 17.31
    r2 = n.new("ShaderNodeMath"); r2.operation = "FRACT"
    l.new(r2m.outputs[0], r2.inputs[0])
    gu = n.new("ShaderNodeAttribute"); gu.attribute_type = "OBJECT"; gu.attribute_name = "grain_u"

    def uv(across, along):
        ua = n.new("ShaderNodeMath"); ua.operation = "MULTIPLY_ADD"
        l.new(across, ua.inputs[0]); ua.inputs[1].default_value = 1.0 / tile
        l.new(gu.outputs["Fac"], ua.inputs[2])
        vb = n.new("ShaderNodeMath"); vb.operation = "MULTIPLY_ADD"
        l.new(along, vb.inputs[0]); vb.inputs[1].default_value = 1.0 / tile
        l.new(r2.outputs[0], vb.inputs[2])
        cmb = n.new("ShaderNodeCombineXYZ")
        if spec["grain"] == "v":
            l.new(ua.outputs[0], cmb.inputs[0]); l.new(vb.outputs[0], cmb.inputs[1])
        else:
            l.new(vb.outputs[0], cmb.inputs[0]); l.new(ua.outputs[0], cmb.inputs[1])
        return cmb.outputs[0]

    uv_top = uv(sep.outputs["Y"], sep.outputs["X"])
    uv_side = uv(sep.outputs["Z"], sep.outputs["X"])
    absz = n.new("ShaderNodeMath"); absz.operation = "ABSOLUTE"
    l.new(nsep.outputs["Z"], absz.inputs[0])
    absx = n.new("ShaderNodeMath"); absx.operation = "ABSOLUTE"
    l.new(nsep.outputs["X"], absx.inputs[0])
    is_top = n.new("ShaderNodeMath"); is_top.operation = "GREATER_THAN"
    l.new(absz.outputs[0], is_top.inputs[0]); is_top.inputs[1].default_value = 0.5
    is_end = n.new("ShaderNodeMath"); is_end.operation = "GREATER_THAN"
    l.new(absx.outputs[0], is_end.inputs[0]); is_end.inputs[1].default_value = 0.6
    uvmix = n.new("ShaderNodeMix"); uvmix.data_type = "VECTOR"
    l.new(is_top.outputs[0], uvmix.inputs["Factor"])
    l.new(uv_side, uvmix.inputs[4]); l.new(uv_top, uvmix.inputs[5])

    def img(kind_, colorspace):
        t = n.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(prefix + kind_ + ".jpg", check_existing=True)
        t.image.colorspace_settings.name = colorspace
        t.interpolation = "Cubic"
        l.new(out_of_type(uvmix, "VECTOR"), t.inputs["Vector"])
        return t

    col = img("Color", "sRGB")
    rough = img("Roughness", "Non-Color")
    disp = img("Displacement", "Non-Color")
    soft = n.new("ShaderNodeBrightContrast")
    soft.inputs["Contrast"].default_value = spec["contrast"]
    soft.inputs["Bright"].default_value = 0.02
    l.new(col.outputs["Color"], soft.inputs["Color"])
    hsv = n.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = spec["sat"]
    hmap = n.new("ShaderNodeMapRange")
    hmap.inputs["To Min"].default_value, hmap.inputs["To Max"].default_value = spec["hue"]
    l.new(oi.outputs["Random"], hmap.inputs["Value"])
    l.new(hmap.outputs[0], hsv.inputs["Hue"])
    vmap = n.new("ShaderNodeMapRange")
    vmap.inputs["To Min"].default_value = spec["val"][0] * tint
    vmap.inputs["To Max"].default_value = spec["val"][1] * tint
    l.new(r2.outputs[0], vmap.inputs["Value"])
    l.new(vmap.outputs[0], hsv.inputs["Value"])
    l.new(soft.outputs["Color"], hsv.inputs["Color"])
    lum = n.new("ShaderNodeRGBToBW")
    l.new(col.outputs["Color"], lum.inputs["Color"])
    kmask = n.new("ShaderNodeMapRange")
    kmask.inputs["From Min"].default_value, kmask.inputs["From Max"].default_value = spec["knot"]
    kmask.inputs["To Min"].default_value, kmask.inputs["To Max"].default_value = spec["knot_amt"], 0.0
    l.new(lum.outputs["Val"], kmask.inputs["Value"])
    deknot = n.new("ShaderNodeMix"); deknot.data_type = "RGBA"
    l.new(kmask.outputs[0], deknot.inputs["Factor"])
    l.new(hsv.outputs["Color"], deknot.inputs[6])
    deknot.inputs[7].default_value = (*srgb(spec["knot_tone"]), 1)
    base = out_of_type(deknot, "RGBA")
    endc = n.new("ShaderNodeVectorMath"); endc.operation = "ADD"
    l.new(tc.outputs["Object"], endc.inputs[0]); endc.inputs[1].default_value = (0, 0.075, 0.06)
    ring = n.new("ShaderNodeTexWave"); ring.wave_type = "RINGS"; ring.rings_direction = "X"
    ring.inputs["Scale"].default_value = 40
    ring.inputs["Distortion"].default_value = 0.6
    ring.inputs["Detail"].default_value = 1.5
    l.new(endc.outputs[0], ring.inputs["Vector"])
    rr = n.new("ShaderNodeValToRGB")
    rr.color_ramp.elements[0].color = (0.78, 0.66, 0.52, 1)
    rr.color_ramp.elements[1].color = (0.92, 0.86, 0.78, 1)
    l.new(ring.outputs["Fac"], rr.inputs["Fac"])
    ring_col = n.new("ShaderNodeMix"); ring_col.data_type = "RGBA"; ring_col.blend_type = "MULTIPLY"
    ring_col.inputs["Factor"].default_value = 1.0
    l.new(base, ring_col.inputs[6]); l.new(rr.outputs["Color"], ring_col.inputs[7])
    final = n.new("ShaderNodeMix"); final.data_type = "RGBA"
    l.new(is_end.outputs[0], final.inputs["Factor"])
    l.new(base, final.inputs[6])
    l.new(out_of_type(ring_col, "RGBA"), final.inputs[7])
    # rough-sawn fibres: fine noise stretched along the grain (object space, metres)
    fsc = n.new("ShaderNodeVectorMath"); fsc.operation = "MULTIPLY"
    l.new(tc.outputs["Object"], fsc.inputs[0])
    fsc.inputs[1].default_value = (12, 260, 260)   # the grain runs along object X (see uv() above)
    fib = n.new("ShaderNodeTexNoise")
    fib.inputs["Scale"].default_value = 1.0
    fib.inputs["Detail"].default_value = 3
    fib.inputs["Roughness"].default_value = 0.6
    l.new(fsc.outputs[0], fib.inputs["Vector"])
    fmap = n.new("ShaderNodeMapRange")
    fmap.inputs["From Min"].default_value, fmap.inputs["From Max"].default_value = 0.3, 0.7
    fmap.inputs["To Min"].default_value, fmap.inputs["To Max"].default_value = spec["fib"]
    l.new(fib.outputs["Fac"], fmap.inputs["Value"])
    tone = n.new("ShaderNodeValToRGB")
    tone.color_ramp.interpolation = "EASE"
    tone.color_ramp.elements[0].color = (*spec["tone"][0], 1)
    tone.color_ramp.elements[1].position = 0.6
    tone.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1)
    el = tone.color_ramp.elements.new(1.0)
    el.color = (*spec["tone"][1], 1)
    l.new(r2.outputs[0], tone.inputs["Fac"])
    shade = fmap
    toned = n.new("ShaderNodeMix"); toned.data_type = "RGBA"; toned.blend_type = "MULTIPLY"
    toned.inputs["Factor"].default_value = 1.0
    l.new(out_of_type(final, "RGBA"), toned.inputs[6])
    shade_rgb = n.new("ShaderNodeCombineColor")
    for i in range(3):
        l.new(shade.outputs[0], shade_rgb.inputs[i])
    tint = n.new("ShaderNodeMix"); tint.data_type = "RGBA"; tint.blend_type = "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    l.new(shade_rgb.outputs[0], tint.inputs[6]); l.new(tone.outputs["Color"], tint.inputs[7])
    l.new(out_of_type(tint, "RGBA"), toned.inputs[7])
    l.new(out_of_type(toned, "RGBA"), bsdf.inputs["Base Color"])
    rmap = n.new("ShaderNodeMapRange")
    rmap.inputs["To Min"].default_value, rmap.inputs["To Max"].default_value = spec["rough"]
    l.new(rough.outputs["Color"], rmap.inputs["Value"])
    radd = n.new("ShaderNodeMath"); radd.operation = "MULTIPLY_ADD"; radd.use_clamp = True
    l.new(fib.outputs["Fac"], radd.inputs[0]); radd.inputs[1].default_value = 0.2
    l.new(rmap.outputs[0], radd.inputs[2])
    l.new(radd.outputs[0], bsdf.inputs["Roughness"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.3
    # band-saw marks: faint ridges across the grain every ~5 mm, slightly wavy
    saw = n.new("ShaderNodeTexWave"); saw.wave_type = "BANDS"; saw.bands_direction = "X"
    saw.inputs["Scale"].default_value = 63
    saw.inputs["Distortion"].default_value = 1.5
    saw.inputs["Detail"].default_value = 1
    l.new(tc.outputs["Object"], saw.inputs["Vector"])
    hgt = n.new("ShaderNodeMath"); hgt.operation = "MULTIPLY_ADD"
    l.new(fib.outputs["Fac"], hgt.inputs[0]); hgt.inputs[1].default_value = 0.25
    l.new(disp.outputs["Color"], hgt.inputs[2])
    hgt2 = n.new("ShaderNodeMath"); hgt2.operation = "MULTIPLY_ADD"
    l.new(saw.outputs["Fac"], hgt2.inputs[0]); hgt2.inputs[1].default_value = 0.18
    l.new(hgt.outputs[0], hgt2.inputs[2])
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.4
    bump.inputs["Distance"].default_value = 0.0005
    l.new(hgt2.outputs[0], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def plain_material(name, hexcol, metallic=0.0, roughness=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*srgb(hexcol), 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = roughness
    return m


def stamp_material(name, path):
    """Burnt-in / printed marking decal: PNG alpha (x wear noise) drives a dark ink."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    t = n.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path, check_existing=True)
    m["aspect"] = t.image.size[0] / t.image.size[1]   # the decal takes the mark's proportions from its PNG
    t.interpolation = "Linear"     # crisper thin lines than Cubic at this size
    l.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.88
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 260.0
    noise.inputs["Detail"].default_value = 4.0
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = (0.84, 0.84, 0.84, 1)   # light wear only: heavy wear blurred the mark
    ramp.color_ramp.elements[1].position = 0.62
    l.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    mul = n.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    l.new(t.outputs["Alpha"], mul.inputs[0])
    l.new(out_of_type(ramp, "RGBA"), mul.inputs[1])
    mul2 = n.new("ShaderNodeMath"); mul2.operation = "MULTIPLY"
    l.new(mul.outputs[0], mul2.inputs[0]); mul2.inputs[1].default_value = 0.96
    l.new(mul2.outputs[0], b.inputs["Alpha"])
    return m


MATS = {
    "pine": wood_material("pine", "pine"),
    "hard": wood_material("hard", "hard"),
    "block": wood_material("block_pine", "pine", tint=0.96),
    "block_hard": wood_material("block_hard", "hard", tint=0.97),
}
NAIL = plain_material("nail", "#B4B3AE", metallic=0.9, roughness=0.38)
STEEL = plain_material("galvanised", "#B6BABD", metallic=1.0, roughness=0.32)

ROOT = bpy.data.objects.new("pallet", None)
scene.collection.objects.link(ROOT)
OBJECTS = []   # (object, kind) for every renderable pallet object


def link(ob, kind, parent=None):
    scene.collection.objects.link(ob)
    ob.parent = parent or ROOT
    OBJECTS.append((ob, kind))
    return ob


# ================================================================ geometry
def frame_of(p):
    """Local frame: local X = grain (length), local Y across, local Z up from z0."""
    x0, x1 = p["x"]; y0, y1 = p["y"]; z0, z1 = p["z"]
    if p["grain"] == "x":
        lx, ly, rot = x1 - x0, y1 - y0, 0.0
    else:
        lx, ly, rot = y1 - y0, x1 - x0, 90.0
    c = Vector(((x0 + x1) / 2, (y0 + y1) / 2, z0))
    M = Matrix.Translation(c * MM) @ Matrix.Rotation(math.radians(rot), 4, "Z")
    return lx, ly, z1 - z0, c, rot, M


def chamfer_profile(lx, openings_local, D, off=12.0, run=42.0):
    """Sampled (s, depth) along the board for the EPAL lower-edge-board chamfer.
    Full depth D between the run-outs; run-outs follow the arc of a disc cutter."""
    pts = {round(-lx / 2, 4): 0.0, round(lx / 2, 4): 0.0}
    for a, b in openings_local:
        s0, s3 = a + off, b - off
        run_ = run if s3 - s0 >= 2 * run + 10 else max(10.0, (s3 - s0 - 10) / 2)
        Rr = (run_ * run_ + D * D) / (2 * D)
        s1, s2 = s0 + run_, s3 - run_
        for k in range(15):
            u = run_ * (1 - k / 14)
            d = max(math.sqrt(max(Rr * Rr - u * u, 0)) - (Rr - D), 0.0)
            for s in (s1 - u, s2 + u):
                key = round(s, 4)
                pts[key] = max(pts.get(key, 0.0), d)
    return sorted(pts.items())


def mesh_box(bm, lx, ly, lz):
    vs = {}
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (0, 1):
                vs[(sx, sy, sz)] = bm.verts.new((sx * lx / 2 * MM, sy * ly / 2 * MM, sz * lz * MM))
    quads = [((-1, -1, 0), (-1, 1, 0), (1, 1, 0), (1, -1, 0)), ((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)),
             ((-1, -1, 0), (1, -1, 0), (1, -1, 1), (-1, -1, 1)), ((-1, 1, 0), (-1, 1, 1), (1, 1, 1), (1, 1, 0)),
             ((-1, -1, 0), (-1, -1, 1), (-1, 1, 1), (-1, 1, 0)), ((1, -1, 0), (1, 1, 0), (1, 1, 1), (1, -1, 1))]
    for q in quads:
        bm.faces.new([vs[k] for k in q])


def mesh_chamfer_board(bm, lx, ly, lz, sgn, profile):
    """Board along local X whose upper edge on side sgn*Y is chamfered by depth d(s)."""
    secs = []
    w2 = ly / 2
    for s, d in profile:
        d = max(d, 0.05)
        ring = [(-w2, 0.0), (w2, 0.0), (w2, lz - d), (w2 - d, lz), (-w2, lz)]
        if sgn < 0:
            ring = [(-y, z) for y, z in ring][::-1]
        secs.append([bm.verts.new((s * MM, y * MM, z * MM)) for y, z in ring])
    k = len(secs[0])
    for i in range(len(secs) - 1):
        a, b = secs[i], secs[i + 1]
        for j in range(k):
            bm.faces.new([a[j], a[(j + 1) % k], b[(j + 1) % k], b[j]])
    bm.faces.new(secs[0][::-1])
    bm.faces.new(secs[-1])


def mesh_notched(bm, lx, ly, lz, notches_local):
    """Stringer along local X with notches cut from the underside (rounded top corners)."""
    prof = [(-lx / 2, 0.0)]
    for c, length, depth, r in sorted(notches_local):
        xl, xr = c - length / 2, c + length / 2
        prof.append((xl, 0.0))
        if depth - r > 0.5:
            prof.append((xl, depth - r))
        for k in range(1, 9):
            a = math.pi - k * (math.pi / 2) / 8
            prof.append((xl + r + r * math.cos(a), depth - r + r * math.sin(a)))
        for k in range(0, 8):
            a = math.pi / 2 - k * (math.pi / 2) / 8
            prof.append((xr - r + r * math.cos(a), depth - r + r * math.sin(a)))
        if depth - r > 0.5:
            prof.append((xr, depth - r))
        prof.append((xr, 0.0))
    prof += [(lx / 2, 0.0), (lx / 2, lz), (-lx / 2, lz)]
    front = [bm.verts.new((x * MM, -ly / 2 * MM, z * MM)) for x, z in prof]
    back = [bm.verts.new((x * MM, ly / 2 * MM, z * MM)) for x, z in prof]
    bm.faces.new(front)
    bm.faces.new(back[::-1])
    k = len(prof)
    for i in range(k):
        j = (i + 1) % k
        bm.faces.new([front[i], back[i], back[j], front[j]])


def corner_planes(p, recipe):
    """World cut planes (point, normal) of every corner chamfer that reaches this part."""
    planes = []
    for reg in recipe["corners"]:
        if p["z"][0] < reg["z"][0] - 0.01 or p["z"][1] > reg["z"][1] + 0.01:
            continue
        c = reg["c"]
        for sx in (-1, 1):
            for sy in (-1, 1):
                X = reg["x"][1] if sx > 0 else reg["x"][0]
                Y = reg["y"][1] if sy > 0 else reg["y"][0]
                nrm = Vector((sx, sy, 0)).normalized()
                pt = Vector((X - sx * c, Y, 0))
                reach = max(nrm.dot(Vector((x, y, 0)) - pt) for x in p["x"] for y in p["y"])
                if reach > 0.01:
                    planes.append((pt, nrm))
    return planes


def build_part(p, recipe, z_offset=0.0):
    lx, ly, lz, c, rot, M = frame_of(p)
    M = Matrix.Translation((0, 0, z_offset * MM)) @ M
    bm = bmesh.new()
    if "edge_chamfer" in p:
        ec = p["edge_chamfer"]
        if p["grain"] == "x":
            sgn = 1 if ec["side"] == "+y" else -1
            ops = [[a - c.x, b - c.x] for a, b in ec["openings"]]
        else:
            sgn = -1 if ec["side"] == "+x" else 1
            ops = [[a - c.y, b - c.y] for a, b in ec["openings"]]
        mesh_chamfer_board(bm, lx, ly, lz, sgn, chamfer_profile(lx, ops, ec["depth"]))
    elif "notches" in p:
        off = c.x if p["grain"] == "x" else c.y
        mesh_notched(bm, lx, ly, lz, [(nt["center"] - off, nt["length"], nt["depth"], nt["radius"]) for nt in p["notches"]])
    else:
        mesh_box(bm, lx, ly, lz)
    Minv = M.inverted()
    for pt, nrm in corner_planes(p, recipe):
        co = Minv @ ((pt + Vector((0, 0, z_offset))) * MM)
        no = (Minv.to_3x3() @ nrm).normalized()
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-7, plane_co=co, plane_no=no, clear_outer=True)
        bnd = [e for e in bm.edges if e.is_boundary]
        if bnd:
            bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    big = [f for f in bm.faces if len(f.verts) > 4]
    if big:
        bmesh.ops.triangulate(bm, faces=big, quad_method="BEAUTY", ngon_method="EAR_CLIP")
    me = bpy.data.meshes.new(p["name"])
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(30))
    ob = bpy.data.objects.new(p["name"], me)
    ob.matrix_world = M
    if EDGE_MM > 0:
        bv = ob.modifiers.new("eased edges", "BEVEL")
        bv.width = EDGE_MM * MM
        bv.segments = 3
        bv.limit_method = "ANGLE"
        bv.angle_limit = math.radians(30)
        bv.use_clamp_overlap = True
        bv.harden_normals = True
    hard = recipe["_wood"] == "hard"
    if p.get("wood") == "block":
        mat = MATS["block_hard"] if hard else MATS["block"]
    else:
        mat = MATS["hard"] if p.get("wood") == "hard" else MATS["pine"]
    ob.data.materials.append(mat)
    ob["grain_kind"] = "hard" if (p.get("wood") == "hard" or (p.get("wood") == "block" and hard)) else "pine"
    ob["grain_u"] = grain_strip(p, recipe)
    return link(ob, "wood")


def nail_head(x, y, z, down=False):
    me = bpy.data.meshes.get("nail_head")
    if me is None:
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=2.9 * MM, radius2=2.6 * MM, depth=0.6 * MM)
        me = bpy.data.meshes.new("nail_head")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(NAIL)
    ob = bpy.data.objects.new("nail", me)
    ob.location = (x * MM, y * MM, (z + (-0.15 if down else 0.15)) * MM)
    if down:
        ob.rotation_euler.x = math.pi
    return link(ob, "nail")


def overlap(a, b):
    x0, x1 = max(a["x"][0], b["x"][0]), min(a["x"][1], b["x"][1])
    y0, y1 = max(a["y"][0], b["y"][0]), min(a["y"][1], b["y"][1])
    return (x0, x1, y0, y1) if x1 - x0 > 5 and y1 - y0 > 5 else None


def place_nails(parts, z_offset=0.0):
    """Nails where top deck boards cross the members below, and on the floor layer
    where it meets the member above (seen in the underside view)."""
    for p in parts:
        floor = p["role"] == "bottom" and p["z"][0] < 0.01
        if p["role"] != "top" and not floor:
            continue
        for q in parts:
            if q is p:
                continue
            touching = abs(q["z"][1] - p["z"][0]) < 0.01 if p["role"] == "top" else abs(q["z"][0] - p["z"][1]) < 0.01
            if not touching:
                continue
            ov = overlap(p, q)
            if not ov:
                continue
            x0, x1, y0, y1 = ov
            across = (y1 - y0) if p["grain"] == "x" else (x1 - x0)
            along = (x1 - x0) if p["grain"] == "x" else (y1 - y0)
            na = 3 if across >= 130 else 2 if across >= 85 else 1
            nl = 2 if along >= 120 else 1
            for i in range(na):
                fa = (i + 1) / (na + 1)
                for j in range(nl):
                    fl = (j + 1) / (nl + 1)
                    shift = 0.06 if (na > 1 and nl > 1 and i % 2) else 0.0
                    if p["grain"] == "x":
                        x, y = x0 + (fl + shift) * (x1 - x0), y0 + fa * (y1 - y0)
                    else:
                        x, y = x0 + fa * (x1 - x0), y0 + (fl + shift) * (y1 - y0)
                    if floor:
                        nail_head(x, y, z_offset, down=True)
                    else:
                        nail_head(x, y, p["z"][1] + z_offset)


# ================================================================ markings
_stamp_mats = {}


def stamp_file(mark):
    if mark == "ippc":
        ip = BRAND["ippc"]
        return os.path.join(HERE, "stamps", f"ippc_{ip['country']}-{ip['code']}_{ip['treatment']}.png")
    return os.path.join(HERE, "stamps", f"{mark}.png")


def decal(mark, centre, normal, face_w, face_h):
    """Flat marking on a vertical face (centre in mm, world)."""
    if mark not in _stamp_mats:
        _stamp_mats[mark] = stamp_material("stamp_" + mark, stamp_file(mark))
    asp = _stamp_mats[mark]["aspect"]
    w = min(face_w * 0.80, face_h * 0.66 * asp)
    h = w / asp
    n = Vector(normal).normalized()
    up = Vector((0, 0, 1))
    right = up.cross(n).normalized()
    c = Vector(centre) + n * 0.35
    corners = [c - right * w / 2 - up * h / 2, c + right * w / 2 - up * h / 2,
               c + right * w / 2 + up * h / 2, c - right * w / 2 + up * h / 2]
    me = bpy.data.meshes.new("decal")
    me.from_pydata([tuple(v * MM) for v in corners], [], [(0, 1, 2, 3)])
    uvl = me.uv_layers.new(name="UVMap")
    for loop, uvv in zip(me.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        uvl.data[loop.index].uv = uvv
    me.materials.append(_stamp_mats[mark])
    return link(bpy.data.objects.new("decal_" + mark, me), "decal")


def marks_for(recipe):
    m = BRAND.get("marks", {})
    rid = recipe["id"]
    if rid in m:
        return m[rid]
    if rid.startswith("cp") and "cp*" in m:
        return {k: (f"cp{rid[2:]}" if v == "cp" else v) for k, v in m["cp*"].items()}
    return m.get("default", {"L": "ippc"})


def place_marks(recipe, z_offset=0.0, marks=None):
    marks = marks if marks is not None else marks_for(recipe)
    if not marks:
        return
    parts = recipe["parts"]
    axis = recipe.get("stamp_axis", "y")
    L, W = recipe["dims"][0], recipe["dims"][1]
    c_leg = max([reg["c"] for reg in recipe["corners"] if reg["z"][0] <= 30] or [0])
    blocks = [p for p in parts if p["role"] == "block"]
    stringers = [p for p in parts if p["role"] == "stringer"]
    for face in (-1, 1):
        if blocks:
            if axis == "y":
                edge = min(b["y"][0] for b in blocks) if face < 0 else max(b["y"][1] for b in blocks)
                row = [b for b in blocks if abs((b["y"][0] if face < 0 else b["y"][1]) - edge) < 0.5]
                row.sort(key=lambda b: b["x"][0] * (1 if face < 0 else -1))      # viewer's left -> right
            else:
                edge = min(b["x"][0] for b in blocks) if face < 0 else max(b["x"][1] for b in blocks)
                row = [b for b in blocks if abs((b["x"][0] if face < 0 else b["x"][1]) - edge) < 0.5]
                row.sort(key=lambda b: -b["y"][0] * (1 if face < 0 else -1))
            slots = {"L": row[0], "R": row[-1], "C": row[len(row) // 2]}
            for slot, mark in marks.items():
                b = slots.get(slot)
                if b is None:
                    continue
                if axis == "y":
                    a0, a1, lim = b["x"][0], b["x"][1], L / 2
                else:
                    a0, a1, lim = b["y"][0], b["y"][1], W / 2
                # a corner chamfer shortens the flat face of corner blocks
                at_edge = abs(edge) >= (W / 2 if axis == "y" else L / 2) - 0.5
                if at_edge and c_leg and a0 <= -lim + 0.5:
                    a0 += c_leg
                if at_edge and c_leg and a1 >= lim - 0.5:
                    a1 -= c_leg
                mid = (a0 + a1) / 2
                zc = (b["z"][0] + b["z"][1]) / 2 + z_offset
                centre = (mid, edge, zc) if axis == "y" else (edge, mid, zc)
                normal = (0, face, 0) if axis == "y" else (face, 0, 0)
                decal(mark, centre, normal, a1 - a0, b["z"][1] - b["z"][0])
        elif stringers:
            edge = min(s["x"][0] for s in stringers) if face < 0 else max(s["x"][1] for s in stringers)
            s = next(s for s in stringers if abs((s["x"][0] if face < 0 else s["x"][1]) - edge) < 0.5)
            ys = {"L": W / 2 - W / 6, "C": 0.0, "R": -W / 2 + W / 6}
            for slot, mark in marks.items():
                if slot not in ys:
                    continue
                y = ys[slot] * (1 if face < 0 else -1)
                for nt in s.get("notches", []):   # keep clear of notches
                    lo, hi = nt["center"] - nt["length"] / 2 - 10, nt["center"] + nt["length"] / 2 + 10
                    if lo < y < hi:
                        y = (hi + W / 2) / 2 if y > 0 else (lo - W / 2) / 2
                centre = (edge, y, (s["z"][0] + s["z"][1]) / 2 + z_offset)
                decal(mark, centre, (face, 0, 0), min(220, W / 3), s["z"][1] - s["z"][0])


# ================================================================ build
def prep(recipe):
    recipe["_wood"] = "hard" if any(p.get("wood") == "hard" for p in recipe["parts"]) else "pine"
    return recipe


def grain_strip(p, recipe):
    """Centre (u) of the texture strip a part shows. With a knot map: one deck board per pallet (two on
    pallets with many deck boards) and the odd block or bottom board show a few knots; the rest are clear."""
    kind = "hard" if (p.get("wood") == "hard" or (p.get("wood") == "block" and recipe["_wood"] == "hard")) else "pine"
    spec = WOODS[kind]
    km = KNOT_MAP.get(spec["tex"]) if kind == "pine" else None
    if not km:
        return random.random()
    width_u = (min(p["x"][1] - p["x"][0], p["y"][1] - p["y"][0]) if p.get("role") != "block" else
               max(p["x"][1] - p["x"][0], p["y"][1] - p["y"][0])) * MM / spec["tile"]
    if p["name"] in recipe.get("_knotty", ()) or (p.get("role") != "top" and random.random() < 0.15):
        return random.choice(km["knotty"]) + random.uniform(-0.01, 0.01)
    lo, hi = random.choice(km["clear"])
    a, b = lo + width_u / 2, hi - width_u / 2
    return random.uniform(a, b) if b > a else (lo + hi) / 2


def build_recipe(recipe, z_offset=0.0, marks=None):
    prep(recipe)
    tops = [p["name"] for p in recipe["parts"] if p.get("role") == "top"]
    recipe["_knotty"] = set(random.sample(tops, min(len(tops), 1 if len(tops) <= 6 else 2))) if tops else set()
    for p in recipe["parts"]:
        build_part(p, recipe, z_offset)
    place_nails(recipe["parts"], z_offset)
    place_marks(recipe, z_offset, marks)


def hinge(x, y, sx, sy, z0, h):
    """Galvanised corner hinge: one leaf on each board face + knuckle at the corner."""
    leaf, t = 105.0, 2.0
    for along in ("x", "y"):
        bm = bmesh.new()
        if along == "x":
            cx, cy, wx, wy = x - sx * leaf / 2, y + sy * t / 2, leaf, t
        else:
            cx, cy, wx, wy = x + sx * t / 2, y - sy * leaf / 2, t, leaf
        mesh_box(bm, wx, wy, h)
        me = bpy.data.meshes.new("hinge")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(STEEL)
        ob = bpy.data.objects.new("hinge", me)
        ob.location = (cx * MM, cy * MM, z0 * MM)
        link(ob, "steel")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=5 * MM, radius2=5 * MM, depth=h * MM)
    me = bpy.data.meshes.new("knuckle")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(STEEL)
    ob = bpy.data.objects.new("knuckle", me)
    ob.location = ((x + sx * 3) * MM, (y + sy * 3) * MM, (z0 + h / 2) * MM)
    link(ob, "steel")


def build_collar(stack=1, on_pallet=True):
    base_h = 0.0
    if on_pallet:
        base = RECIPES[R["meta"]["base"]]
        build_recipe(base, 0.0, marks=marks_for(base))
        base_h = base["dims"][2]
    H = R["dims"][2]
    prep(R)
    for k in range(stack):
        z = base_h + k * H
        for p in R["parts"]:
            build_part(p, R, z)
        for sx in (-1, 1):
            for sy in (-1, 1):
                hinge(sx * 600, sy * 400, sx, sy, z + 22, H - 44)
        decal("ippc", (-420, -400, z + H / 2), (0, -1, 0), 200, H * 0.55)
    return base_h + stack * H


def clear_pallet():
    for ob, _ in list(OBJECTS):
        bpy.data.objects.remove(ob, do_unlink=True)
    OBJECTS.clear()


# ================================================================ studio
