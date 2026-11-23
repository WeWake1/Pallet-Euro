"""PROTOTYPE (inner pages) · renders for two refined ideas from the round-6 verdict (decisions #49):
  photo    an EPAL 1 in the white studio, 3/4 view (the product page's part inspector, and the "after" of About)
  ids      the same view, one exact flat colour per part (PNG red = 10 x id): the page finds the part under the
           cursor; tools/render/inspect_post.py turns it into one blue outline per part
  generic  the same view and light, a generic, unmarked, worn pallet of the same size (the "before" of About):
           uneven sawn boards, a missing and a broken deck board, a split-off corner, a twisted block, a short bottom board,
           grey weathered timber with grime and mould, rusty nails standing proud

  Blender -b --factory-startup --python tools/render/hero/inspect.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/inner --size 1920x1200 --pass photo|ids|generic
ids: 1-20 the parts in recipe order (bottom1-3, block1-9, cross1-3, top1-5), 21 nails, 22 EPAL marks, 23 IPPC mark.
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

PASS = "photo"
if "--pass" in sys.argv:
    PASS = sys.argv[sys.argv.index("--pass") + 1]
pk = C.pk
scene = C.scene
MM = pk.MM

C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.3)
C.seamless_studio(bg="#FFFFFF", floor="#F5F4F1", fade=(4.4, 9.0), fill="#EEF1F6", fill_strength=0.8, rough=0.7,
                  bg_strength=3.0)
AIM = (0, 0, 0.07)
C.area("top", (0.0, -0.2, 3.2), 4.0, 190, look=AIM)
C.area("key", (-2.2, -2.4, 3.0), 3.5, 150, look=AIM)
C.area("fill", (2.8, -1.6, 1.8), 3.0, 40, look=AIM)
sun = C.sun("sun", 5.0, color="#FFF6EA", angle_deg=2.5)
C.aim_sun(sun, elev_deg=52, azim_deg=28)

C.build_pallet(rot_deg=0, loc=(0, 0, 0))
woods = [ob for ob, k in pk.OBJECTS if k == "wood"]
nails = [ob for ob, k in pk.OBJECTS if k == "nail"]
decals = [ob for ob, k in pk.OBJECTS if k == "decal"]

AZ, EL, DIST = math.radians(-36), math.radians(26), 2.4
cam = C.camera(lens=50)
cam.location = (math.sin(AZ) * math.cos(EL) * DIST, -math.cos(AZ) * math.cos(EL) * DIST, math.sin(EL) * DIST + 0.07)
C.look_at(cam, (0, 0, 0.05))
cam.data.dof.use_dof = PASS != "ids"
cam.data.dof.focus_distance = DIST
cam.data.dof.aperture_fstop = 8.0


def flat(name, hexcol):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    n.clear()
    e = n.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*C.srgb(hexcol), 1)
    o = n.new("ShaderNodeOutputMaterial")
    m.node_tree.links.new(e.outputs[0], o.inputs["Surface"])
    return m


def weathered(name, grey=0.5, grime=0.85, tint=0.92):
    """The approved spruce, aged: faded toward silver grey, with grime and specks of mould (world-space noise, so no
    two boards look alike)."""
    m = pk.wood_material(name, "pine", tint=tint)
    n, l = m.node_tree.nodes, m.node_tree.links
    bsdf = next(x for x in n if x.type == "BSDF_PRINCIPLED")
    src = bsdf.inputs["Base Color"].links[0].from_socket
    geo = n.new("ShaderNodeNewGeometry")
    fade = n.new("ShaderNodeMix")
    fade.data_type = "RGBA"
    fade.inputs["Factor"].default_value = grey
    l.new(src, fade.inputs["A"])
    fade.inputs["B"].default_value = (*C.srgb("#8F887C"), 1)
    nz = n.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 5.0
    nz.inputs["Detail"].default_value = 9.0
    nz.inputs["Roughness"].default_value = 0.65
    l.new(geo.outputs["Position"], nz.inputs["Vector"])
    rp = n.new("ShaderNodeValToRGB")
    rp.color_ramp.elements[0].position = 0.38
    rp.color_ramp.elements[0].color = (1, 1, 1, 1)
    rp.color_ramp.elements[1].position = 0.78
    rp.color_ramp.elements[1].color = (*C.srgb("#564C3E"), 1)
    l.new(nz.outputs["Fac"], rp.inputs["Fac"])
    dirt = n.new("ShaderNodeMix")
    dirt.data_type = "RGBA"
    dirt.blend_type = "MULTIPLY"
    dirt.inputs["Factor"].default_value = grime
    l.new(fade.outputs["Result"], dirt.inputs["A"])
    l.new(rp.outputs["Color"], dirt.inputs["B"])
    spots = n.new("ShaderNodeTexNoise")
    spots.inputs["Scale"].default_value = 70.0
    spots.inputs["Detail"].default_value = 3.0
    l.new(geo.outputs["Position"], spots.inputs["Vector"])
    big = n.new("ShaderNodeTexNoise")
    big.inputs["Scale"].default_value = 3.0
    l.new(geo.outputs["Position"], big.inputs["Vector"])
    sp = n.new("ShaderNodeMath")
    sp.operation = "MULTIPLY"
    l.new(spots.outputs["Fac"], sp.inputs[0])
    l.new(big.outputs["Fac"], sp.inputs[1])
    th = n.new("ShaderNodeMapRange")
    th.inputs["From Min"].default_value, th.inputs["From Max"].default_value = 0.40, 0.46
    l.new(sp.outputs[0], th.inputs["Value"])
    mould = n.new("ShaderNodeMix")
    mould.data_type = "RGBA"
    l.new(th.outputs[0], mould.inputs["Factor"])
    l.new(dirt.outputs["Result"], mould.inputs["A"])
    mould.inputs["B"].default_value = (*C.srgb("#2E3129"), 1)
    l.new(mould.outputs["Result"], bsdf.inputs["Base Color"])
    rough = bsdf.inputs["Roughness"]
    for lk in list(rough.links):
        l.remove(lk)
    rough.default_value = 0.92
    return m


def prism(name, pts, z0, z1, parent_M):
    """A closed prism from a polygon (x, y in mm, local frame) between local z0 and z1 (mm)."""
    bm = bmesh.new()
    lo = [bm.verts.new((x * MM, y * MM, z0 * MM)) for x, y in pts]
    hi = [bm.verts.new((x * MM, y * MM, z1 * MM)) for x, y in pts]
    bm.faces.new(lo[::-1])
    bm.faces.new(hi)
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    ob.matrix_world = parent_M
    ob.hide_render = True
    return ob


def cut(ob, cutter):
    m = ob.modifiers.new("cut_" + cutter.name, "BOOLEAN")
    m.operation, m.solver, m.object = "DIFFERENCE", "EXACT", cutter
    ob.modifiers.move(len(ob.modifiers) - 1, 0)     # before the eased edges


def board(p, lx, ly, lz, M, mat, name=None):
    bm = bmesh.new()
    pk.mesh_box(bm, lx, ly, lz)
    me = bpy.data.meshes.new(name or p["name"])
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name or p["name"], me)
    scene.collection.objects.link(ob)
    ob.matrix_world = M
    ob.data.materials.append(mat)
    ob["grain_u"] = random.random()
    bv = ob.modifiers.new("eased", "BEVEL")
    bv.width, bv.segments, bv.limit_method = 2.0 * MM, 2, "ANGLE"
    return ob


def generic():
    random.seed(5)
    for ob in woods + decals:
        ob.hide_render = True
    old = weathered("old", grey=0.66, grime=1.0, tint=0.88)
    older = weathered("older", grey=0.8, grime=1.0, tint=0.8)
    repair = weathered("repair", grey=0.12, grime=0.5, tint=0.72)        # a mismatched, darker replacement board
    rust = C.mat("rust", "#6E4630", rough=0.85, spec=0.3)
    for o in nails:
        o.data.materials[0] = rust
    for p in pk.R["parts"]:
        lx, ly, lz, c, rot, M = pk.frame_of(p)
        name, role = p["name"], p["role"]
        if name == "top2":                              # one deck board is missing altogether
            continue
        lx2 = lx + random.uniform(-16, 6)
        ly2 = ly * random.uniform(0.9, 1.0)
        dx, dy = random.uniform(-6, 6), random.uniform(-3, 3)
        yaw = math.radians(random.uniform(-0.9, 0.9) if role != "block" else random.uniform(-4, 4))
        mat = older if random.random() < 0.4 else old
        if name == "top4":
            mat = repair
        if name == "block9":                            # a twisted corner block, pushed out
            yaw, dx, dy = math.radians(11), 10, 14
        if name == "bottom1":                           # the front bottom board is short at one end
            lx2, dx = lx - 140, -70
        Mp = M @ Matrix.Translation((dx * MM, dy * MM, 0)) @ Matrix.Rotation(yaw, 4, "Z")
        if name == "top1":                              # the front deck board is broken in two
            zig = [(random.uniform(-12, 12), y) for y in [ly2 / 2 + 2] + [ly2 / 2 - (i + 0.5) * ly2 / 7 for i in range(7)] + [-ly2 / 2 - 2]]
            split, gap, far = 150, 7, 900
            left = [(split - gap + x, y) for x, y in zig]
            right = [(split + gap + x, y) for x, y in zig]
            a = board(p, lx2, ly2, lz, Mp, mat, "top1a")
            cut(a, prism("cutR", left + [(far, -ly2), (far, ly2)], -5, lz + 5, Mp))
            # the broken end of the right-hand piece springs up, pivoting where it is still nailed (its far end);
            # its cutter moves with it, so the break stays where it was cut
            pivot = Vector((lx2 / 2 * MM, 0, 0))
            Mb = Mp @ Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(4.0), 4, "Y") @ Matrix.Translation(-pivot)
            b = board(p, lx2, ly2, lz, Mb, mat, "top1b")
            cut(b, prism("cutL", right + [(-far, -ly2), (-far, ly2)], -5, lz + 5, Mb))
            continue
        ob = board(p, lx2, ly2, lz, Mp, mat)
        if name == "top5":                              # a corner split off the back deck board
            cut(ob, prism("chunk", [(lx2 / 2 - 170, ly2 / 2 + 5), (lx2 / 2 + 5, ly2 / 2 + 5), (lx2 / 2 + 5, -ly2 / 2 + 40),
                                    (lx2 / 2 - 60, 10), (lx2 / 2 - 120, ly2 / 2 - 30)], -5, lz + 5, Mp))
        if name == "top3":                              # a long split along the grain
            pts = [(x, 18 + 3 * math.sin(x / 60)) for x in range(-420, 100, 40)]
            slit = pts + [(x, y - 1.6) for x, y in pts[::-1]]
            cut(ob, prism("split", slit, lz - 9, lz + 5, Mp))
    # nails: the ones on the lifted piece go; a few stand proud of the deck (in mm: how far)
    bpy.context.view_layer.update()
    keep = [o for o in nails if not (o.location.z > 0.12 and ((o.location.y < -0.27 and o.location.x > 0.15) or
                                                             -0.213 < o.location.y < -0.113))]
    for o in nails:
        if o not in keep:
            o.hide_render = True
    tops = [o for o in keep if o.location.z > 0.12]
    for o in random.sample(tops, 9):
        up = random.uniform(5, 13) * MM
        o.location.z += up
        bpy.ops.mesh.primitive_cylinder_add(radius=1.4 * MM, depth=up + 4 * MM, vertices=8,
                                            location=(o.location.x, o.location.y, o.location.z - (up + 4 * MM) / 2))
        sh = bpy.context.active_object
        sh.rotation_euler = (math.radians(random.uniform(-8, 8)), math.radians(random.uniform(-8, 8)), 0)
        sh.data.materials.append(rust)


if PASS == "ids":
    scene.cycles.samples = 1
    scene.cycles.use_denoising = False
    scene.cycles.filter_width = 0.01
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    for nd in scene.world.node_tree.nodes:
        if nd.type == "BACKGROUND":
            nd.inputs["Strength"].default_value = 0.0
    black = flat("id0", "#000000")
    for ob in scene.objects:
        if ob.type == "MESH" and ob not in woods + nails + decals:
            ob.data.materials.clear()
            ob.data.materials.append(black)
    names = [p["name"] for p in pk.R["parts"]]
    for o in woods:
        i = names.index(o.name.split(".")[0]) + 1
        o.data.materials[0] = flat(f"id{i}", f"#{i * 10:02x}0000")
    for o in nails:
        o.data.materials[0] = flat("id21", f"#{210:02x}0000")
    for o in decals:
        i = 23 if "ippc" in o.name else 22
        o.data.materials[0] = flat(f"id{i}", f"#{i * 10:02x}0000")
    s = scene.render.image_settings
    s.file_format = "PNG"
    s.color_mode = "RGB"
    s.color_depth = "8"
    scene.render.filepath = os.path.join(C.args.out, "ids.png")
    bpy.ops.render.render(write_still=True)
    print("WROTE ids.png")
else:
    if PASS == "generic":
        generic()
    C.render_to(os.path.join(C.args.out, f"{PASS}.webp"))
