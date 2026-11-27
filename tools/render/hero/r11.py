"""PROTOTYPE round 11 (decisions #77-#80): six heroes, each a seamless loop that plays by itself (no cursor, no scroll).

  --job sliced     A "Sliced": the EPAL 1 cut into thin slices; a twist runs through it, every slice turning once
                   round the long axis, and it settles whole again (frame N would equal frame 0)
  --job fit        B "Exact fit": pallet after pallet comes out of a plaster wall on a flush belt, through a hole cut to
                   the exact end shape of an EPAL 1 (constant speed: frame N would equal frame 0)
  --job infinity   C "Infinity room": one EPAL 1 in a white room with mirror walls, repeated to infinity; the camera
                   drifts on a closed path
  --job silk       E "Blue silk": a sheet of deep-blue silk floats down over the EPAL 1, settles, and the wind lifts it
                   away; bare pallet at both ends of the loop
  --job dominoes   F "Dominoes": EPAL 1 pallets standing on end topple one after another along a curve (the page then
                   plays the frames back in reverse: they rise again)
  ("Through the opening", D, is opening.py.)

  Blender -b --factory-startup --python tools/render/hero/r11.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/r11/sliced --job sliced [--frames 0-10] [--test]
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

arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
JOB = arg("--job", "sliced")
pk = C.pk
scene = C.scene
MM = pk.MM
LEN, WID, HT = (v * MM for v in pk.R["dims"])          # 1.2, 0.8, 0.144 m


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ease5(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * x * (x * (6 * x - 15) + 10)


def studio(aim=(0.0, 0.0, 0.3), exposure=0.1, sun=True, floor="#F4F2EE", fade=(4.6, 9.5)):
    """Round 10's white studio: seamless floor, soft area lights, a warm sun for crisp shadows."""
    C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=exposure)
    C.seamless_studio(bg="#FFFFFF", floor=floor, fade=fade, fill="#EEF1F6", fill_strength=0.8, rough=0.7, bg_strength=3.0)
    for name, loc, size, power in (("top", (0.0, -0.3, 3.6), 4.0, 210), ("key", (-2.4, -2.6, 3.2), 3.5, 160),
                                   ("fill", (2.8, -1.8, 1.9), 3.0, 45), ("rim", (1.2, 3.2, 2.6), 3.0, 90)):
        a = C.area(name, loc, size, power, look=aim)
        a.visible_camera = False
    if sun:
        s = C.sun("sun", 4.5, color="#FFF3E4", angle_deg=2.0)
        C.aim_sun(s, elev_deg=50, azim_deg=30)
        return s


def orbit_cam(cam, az_deg, el_deg, dist, aim, shift=-0.25, lens=50):
    az, el = math.radians(az_deg), math.radians(el_deg)
    aim = Vector(aim)
    cam.location = aim + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * dist
    C.look_at(cam, aim)
    cam.data.lens = lens
    cam.data.shift_x = shift
    cam.data.dof.focus_distance = dist


def own_random():
    """The wood material varies tone and texture offset by Object Info > Random, which differs for every object.
    Read a per-object property "pe_rand" instead, so the pieces cut from one part keep that part's look."""
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        nt = m.node_tree
        for oi in [n for n in nt.nodes if n.bl_idname == "ShaderNodeObjectInfo"]:
            at = nt.nodes.new("ShaderNodeAttribute")
            at.attribute_type = "OBJECT"
            at.attribute_name = "pe_rand"
            for lk in list(nt.links):
                if lk.from_node == oi and lk.from_socket.name == "Random":
                    nt.links.new(at.outputs["Fac"], lk.to_socket)


def pallet_collection(name="pallet_coll"):
    """Move the pallet palletkit built into its own collection, kept out of the scene, for collection instances."""
    coll = bpy.data.collections.new(name)
    for ob in [pk.ROOT] + [o for o, _ in pk.OBJECTS]:
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        coll.objects.link(ob)
    return coll


def instance(coll, name, parent=None):
    e = bpy.data.objects.new(name, None)
    e.instance_type = "COLLECTION"
    e.instance_collection = coll
    scene.collection.objects.link(e)
    if parent:
        e.parent = parent
    return e


cam = C.camera(lens=50)
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 7.0
out = lambda f: os.path.join(C.args.out, f"{f:03d}.webp")


# ================================================================== A "Sliced"
if JOB == "sliced":
    N_SLICE, N = 40, 120
    studio(aim=(0.0, 0.0, 0.35))
    C.build_pallet()
    own_random()
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    edges = [-LEN / 2 + LEN * i / N_SLICE for i in range(N_SLICE + 1)]
    ZC = HT / 2
    pivots = []
    for i in range(N_SLICE):
        e = bpy.data.objects.new(f"slice{i}", None)
        scene.collection.objects.link(e)
        e.location = ((edges[i] + edges[i + 1]) / 2, 0.0, ZC)
        pivots.append(e)
    bpy.context.view_layer.update()

    def adopt(ob, i):
        ob.parent = pivots[i]
        ob.matrix_parent_inverse = pivots[i].matrix_world.inverted()

    rng = random.Random(11)
    for ob, kind in list(pk.OBJECTS):
        mw = ob.matrix_world.copy()
        if kind == "nail":
            ob["pe_rand"] = 0.5
            i = min(max(int((mw.translation.x + LEN / 2) / LEN * N_SLICE), 0), N_SLICE - 1)
            ob.parent = None
            ob.matrix_world = mw
            adopt(ob, i)
            continue
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        cn = me.attributes.get("custom_normal")
        if cn:
            me.attributes.remove(cn)
        bm0 = bmesh.new()
        bm0.from_mesh(me)
        xs = [(mw @ v.co).x for v in bm0.verts]
        x0, x1 = min(xs), max(xs)
        inv = mw.inverted()
        nrm = (inv.to_3x3() @ Vector((1, 0, 0))).normalized()
        solid = kind == "wood"
        rand = rng.random()
        for i in range(N_SLICE):
            a, b = edges[i], edges[i + 1]
            if b <= x0 + 1e-6 or a >= x1 - 1e-6:
                continue
            bm = bm0.copy()
            if a > x0 + 1e-6:
                bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-7,
                                       plane_co=inv @ Vector((a, 0, 0)), plane_no=nrm, clear_inner=True)
            if b < x1 - 1e-6:
                bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-7,
                                       plane_co=inv @ Vector((b, 0, 0)), plane_no=nrm, clear_outer=True)
            if solid:
                bnd = [e for e in bm.edges if e.is_boundary]
                if bnd:
                    bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
                bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
            if not bm.faces:
                bm.free()
                continue
            sme = bpy.data.meshes.new(f"{ob.name}_{i}")
            bm.to_mesh(sme)
            bm.free()
            for mt in me.materials:
                sme.materials.append(mt)
            if solid:
                sme.shade_smooth()
                sme.set_sharp_from_angle(angle=math.radians(35))
            so = bpy.data.objects.new(sme.name, sme)
            scene.collection.objects.link(so)
            for k in ("grain_u", "grain_kind"):
                if k in ob.keys():
                    so[k] = ob[k]
            so["pe_rand"] = rand
            so.matrix_world = mw
            adopt(so, i)
        bm0.free()
        bpy.data.objects.remove(ob, do_unlink=True)

    # the loaf: the slices draw apart along the length (round the middle), so the end profile repeats in
    # perspective, while a soft sideways ripple runs through them; then they close up into the whole pallet again
    GAP, AMP = float(arg("--gap", "0.024")), float(arg("--amp", "0.10"))
    REST = 0.12                                       # share of the loop held whole at each end

    def envelope(t):
        return ease5((t - REST) / 0.30) * ease5((1 - REST - t) / 0.30)

    X0 = [e.location.x for e in pivots]
    orbit_cam(cam, -38, 20, 7.0, (0.0, 0.0, 0.25), shift=-0.25)
    for f in C.frame_list(N):
        t = f / N
        env = envelope(t)
        tr = (t - REST) / (1 - 2 * REST)
        for i, e in enumerate(pivots):
            u = (i + 0.5) / N_SLICE
            e.location.x = X0[i] + GAP * (i - (N_SLICE - 1) / 2) * env
            e.location.y = AMP * env * math.sin(math.tau * (1.1 * u - 1.5 * tr))
            e.location.z = ZC
        C.render_to(out(f))


# ================================================================== B "Exact fit"
if JOB == "fit":
    N, PITCH, CLR = 120, 1.8, 0.006                  # frames per loop, pallet spacing (m), clearance round the pallet (m)
    C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.05)
    C.seamless_studio(bg="#FFFFFF", floor="#F3F1ED", fade=(7.0, 16.0), fill="#EEF1F6", fill_strength=0.7, rough=0.7,
                      bg_strength=3.0)
    sun = C.sun("sun", 5.0, color="#FFF1DE", angle_deg=1.2)
    C.aim_sun(sun, elev_deg=float(arg("--sun-el", "30")), azim_deg=float(arg("--sun-az", "-78")))   # raking across the wall
    for name, loc, size, power in (("top", (-1.5, 1.0, 4.0), 5.0, 220), ("fill", (-4.0, 4.0, 1.8), 4.0, 90)):
        a = C.area(name, loc, size, power, look=(0, 0, 0.3))
        a.visible_camera = False
    # the wall: a white slab across the path, with the EPAL 1's end shape cut through it (plus the clearance)
    THK = float(arg("--thk", "0.07"))
    wall_mat = C.plaster("#E9E3D9", "#F1ECE4")
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.0, 1.8))
    wall = bpy.context.active_object
    wall.name = "wall"
    wall.scale = (THK, 16.0, 3.6)
    bpy.ops.object.transform_apply(scale=True)
    wall.data.materials.append(wall_mat)
    rects = []                                       # (y0, y1, z0, z1) in mm: the silhouette seen along the pallet's length
    for p in pk.R["parts"]:
        rects.append((p["y"][0], p["y"][1], p["z"][0], p["z"][1]))
    c = CLR / MM
    for k, (y0, y1, z0, z1) in enumerate(rects):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= THK + 0.4
            v.co.y = ((y1 + c) if v.co.y > 0 else (y0 - c)) * MM
            v.co.z = ((z1 + c) if v.co.z > 0 else ((z0 - c) if z0 > 0.5 else -40.0)) * MM
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        me = bpy.data.meshes.new(f"cut{k}")
        bm.to_mesh(me)
        bm.free()
        cut = bpy.data.objects.new(f"cut{k}", me)
        scene.collection.objects.link(cut)
        cut.hide_render = True
        cut.hide_viewport = True
        bo = wall.modifiers.new(f"cut{k}", "BOOLEAN")
        bo.operation = "DIFFERENCE"
        bo.solver = "EXACT"
        bo.object = cut
    # behind the wall the belt runs in a dim tunnel, so the empty hole reads as a dark EPAL silhouette and each
    # pallet comes out of shade into the light
    tun = C.mat("tunnel", "#4A4741", rough=0.9)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = (THK / 2 - 0.01) if v.co.x < 0 else 9.0
        v.co.y = 0.75 if v.co.y > 0 else -0.75
        v.co.z = 0.5 if v.co.z > 0 else -0.01
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().x < 0.5], context="FACES")   # open at the wall
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("tunnel")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(tun)
    tunnel = bpy.data.objects.new("tunnel", me)
    scene.collection.objects.link(tunnel)
    bv = wall.modifiers.new("edge", "BEVEL")
    bv.width = 0.0015
    bv.segments = 2
    bv.limit_method = "ANGLE"
    # a belt flush with the floor carries the pallets through; fine ribs across it, moving with them
    belt_mat = bpy.data.materials.new("belt")
    belt_mat.use_nodes = True
    bn, bl = belt_mat.node_tree.nodes, belt_mat.node_tree.links
    bb = bn["Principled BSDF"]
    bb.inputs["Roughness"].default_value = 0.75
    tc = bn.new("ShaderNodeTexCoord")
    mp = bn.new("ShaderNodeMapping")
    wv = bn.new("ShaderNodeTexWave")
    wv.wave_type = "BANDS"
    wv.bands_direction = "X"
    wv.wave_profile = "SAW"
    wv.inputs["Scale"].default_value = 1.0 / 0.03   # Blender's bands repeat every 1/scale (object space, metres)
    wv.inputs["Distortion"].default_value = 0.0
    bl.new(tc.outputs["Object"], mp.inputs["Vector"])
    bl.new(mp.outputs["Vector"], wv.inputs["Vector"])
    ramp = bn.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*C.srgb("#AEB2B8"), 1)
    ramp.color_ramp.elements[1].position = 0.15
    ramp.color_ramp.elements[1].color = (*C.srgb("#C3C6CB"), 1)
    bl.new(wv.outputs["Fac"], ramp.inputs["Fac"])
    bl.new(ramp.outputs["Color"], bb.inputs["Base Color"])
    belt = C.plane("belt", 40.0, 0.86, loc=(0, 0, 0.0008), material=belt_mat)
    C.build_pallet()
    coll = pallet_collection()
    K = range(-4, 3)
    trains = [instance(coll, f"p{k}") for k in K]
    X0 = 0.0
    cam.data.dof.use_dof = False
    cam.data.lens = float(arg("--lens", "45"))
    cam.location = (-3.0, 2.3, 0.85)               # the exit side: each pallet comes out of the wall toward the camera
    C.look_at(cam, (0.1, -0.1, 0.2))
    cam.data.shift_x = -0.12
    for f in C.frame_list(N):
        d = PITCH * f / N
        for k, e in zip(K, trains):
            e.location = (X0 - k * PITCH - d, 0.0, 0.0)
        mp.inputs["Location"].default_value = (d, 0, 0)
        C.render_to(out(f))


# ================================================================== C "Infinity room"
if JOB == "infinity":
    N = 144
    C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.25)
    cy = scene.cycles
    cy.max_bounces = 64
    cy.glossy_bounces = 64
    cy.diffuse_bounces = 3
    cy.transmission_bounces = 2
    cy.sample_clamp_indirect = 8.0
    C.world("#FFFFFF", 0.0)
    S, H = 1.6, 2.7                                  # half the room's width, its height
    floor = C.mat("floor", "#EDEBE6", rough=0.55, spec=0.3)
    C.plane("floor", 2 * S, 2 * S, material=floor)
    ceil = C.mat("ceiling", "#F6F5F2", rough=0.9)
    C.plane("ceiling", 2 * S, 2 * S, loc=(0, 0, H), rot=(math.pi, 0, 0), material=ceil)
    glow = bpy.data.materials.new("panel")
    glow.use_nodes = True
    gn = glow.node_tree.nodes
    gn.remove(gn["Principled BSDF"])
    em = gn.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*C.srgb("#FFF8EE"), 1)
    em.inputs["Strength"].default_value = 6.0
    glow.node_tree.links.new(em.outputs[0], gn["Material Output"].inputs["Surface"])
    C.plane("panel", 2 * S - 0.14, 2 * S - 0.14, loc=(0, 0, H - 0.01), rot=(math.pi, 0, 0), material=glow)
    mirror = bpy.data.materials.new("mirror")
    mirror.use_nodes = True
    mb = mirror.node_tree.nodes["Principled BSDF"]
    mb.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1)
    mb.inputs["Metallic"].default_value = 1.0
    mb.inputs["Roughness"].default_value = 0.0
    # far reflections fade into a soft white haze (aerial perspective) instead of going black where the bounces run out
    mn, ml = mirror.node_tree.nodes, mirror.node_tree.links
    lp = mn.new("ShaderNodeLightPath")
    mr = mn.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHSTEP"
    mr.inputs["From Min"].default_value = float(arg("--haze0", "4"))
    mr.inputs["From Max"].default_value = float(arg("--haze1", "32"))
    ml.new(lp.outputs["Glossy Depth"], mr.inputs["Value"])
    hz = mn.new("ShaderNodeEmission")
    hz.inputs["Color"].default_value = (*C.srgb("#F3F2EF"), 1)
    hz.inputs["Strength"].default_value = float(arg("--haze", "1.9"))
    mix = mn.new("ShaderNodeMixShader")
    ml.new(mr.outputs[0], mix.inputs["Fac"])
    ml.new(mb.outputs["BSDF"], mix.inputs[1])
    ml.new(hz.outputs[0], mix.inputs[2])
    ml.new(mix.outputs[0], mn["Material Output"].inputs["Surface"])
    skirt = C.mat("skirting", "#F2F0EC", rough=0.6)
    SK = 0.07                                        # white skirting and cornice
    for k, (loc, rot) in enumerate((((S, 0, H / 2), (0, -math.pi / 2, 0)), ((-S, 0, H / 2), (0, math.pi / 2, 0)),
                                    ((0, S, H / 2), (math.pi / 2, 0, 0)), ((0, -S, H / 2), (-math.pi / 2, 0, 0)))):
        C.plane(f"mirror{k}", (H - 2 * SK) if k < 2 else 2 * S, 2 * S if k < 2 else (H - 2 * SK), loc=loc, rot=rot,
                material=mirror)
    for sx in (-1, 1):
        for z in (SK / 2, H - SK / 2):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(sx * (S - 0.006), 0, z))
            o = bpy.context.active_object
            o.scale = (0.012, 2 * S, SK)
            o.data.materials.append(skirt)
            bpy.ops.mesh.primitive_cube_add(size=1, location=(0, sx * (S - 0.006), z))
            o = bpy.context.active_object
            o.scale = (2 * S, 0.012, SK)
            o.data.materials.append(skirt)
    C.build_pallet(rot_deg=0)
    cam.data.dof.use_dof = False
    cam.data.lens = float(arg("--lens", "22"))
    CX, CY, CZ = (float(v) for v in arg("--cam", "-1.36,-1.38,0.86").split(","))
    TX, TY, TZ = (float(v) for v in arg("--target", "0.55,0.75,0.42").split(","))
    for f in C.frame_list(N):
        t = math.tau * f / N                       # a small closed loop: the whole infinite grid swings with it
        cam.location = (CX + 0.12 * math.cos(t), CY + 0.08 * math.sin(t), CZ + 0.05 * math.sin(t))
        C.look_at(cam, (TX + 0.08 * math.sin(t), TY, TZ))
        cam.data.shift_x = -0.1
        C.render_to(out(f))


# ================================================================== F "Dominoes"
if JOB == "dominoes":
    N_SIM = int(arg("--sim", "144"))
    sun = studio(aim=(0.3, 0.0, 0.6), fade=(15.0, 28.0))
    C.aim_sun(sun, elev_deg=float(arg("--sun-el", "34")), azim_deg=float(arg("--sun-az", "-24")))   # low, from the left
    C.build_pallet()
    coll = pallet_collection()
    # the path: a gentle S in the floor plane, pallets on end every SP metres, each facing along the path
    SP, COUNT = 0.72, int(arg("--count", "13"))
    path = []
    for i in range(COUNT):                            # from far away toward the camera, winding gently
        s = i * SP
        path.append(Vector((0.85 * math.sin(s / 1.9 + 0.4), 4.3 - s, 0)))
    bpy.ops.rigidbody.world_add()
    rbw = scene.rigidbody_world
    rbw.substeps_per_frame = 20
    rbw.time_scale = float(arg("--slow", "0.72"))     # slow motion
    rbw.solver_iterations = 30
    rbw.point_cache.frame_start = 1
    rbw.point_cache.frame_end = N_SIM + 1
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.5))
    ground = bpy.context.active_object
    ground.scale = (40, 40, 1)
    ground.hide_render = True
    with bpy.context.temp_override(object=ground, active_object=ground, selected_objects=[ground]):
        bpy.ops.rigidbody.object_add(type="PASSIVE")
    ground.rigid_body.friction = 0.8
    proxies = []
    for i, p in enumerate(path):
        nxt = path[min(i + 1, COUNT - 1)] - path[max(i - 1, 0)]
        yaw = math.atan2(nxt.y, nxt.x)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(p.x, p.y, LEN / 2))
        pr = bpy.context.active_object
        pr.name = f"dom{i}"
        pr.scale = (HT, WID, LEN)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        pr.rotation_euler = (0, 0, yaw)
        pr.hide_render = True
        with bpy.context.temp_override(object=pr, active_object=pr, selected_objects=[pr]):
            bpy.ops.rigidbody.object_add(type="ACTIVE")
        rb = pr.rigid_body
        rb.mass = 25.0
        rb.collision_shape = "BOX"
        rb.friction = 0.6
        rb.restitution = 0.05
        rb.collision_margin = 0.002
        rb.linear_damping = 0.05
        rb.angular_damping = 0.1
        vis = instance(coll, f"vis{i}", parent=pr)
        vis.location = (-HT / 2, 0, 0)                 # pallet origin: centre of its underside
        vis.rotation_euler = (0, math.radians(90), 0)   # its length upright, its deck facing the way it falls
        proxies.append(pr)
    # the first one starts leaning just past its balance point
    first = proxies[0]
    lean = math.radians(9)
    d = Vector((math.cos(first.rotation_euler.z), math.sin(first.rotation_euler.z), 0))
    first.rotation_euler = (Matrix.Rotation(lean, 3, Vector((-d.y, d.x, 0))) @ first.rotation_euler.to_matrix()).to_euler()
    first.location += d * (LEN / 2) * math.sin(lean)
    first.location.z = LEN / 2 * math.cos(lean) + HT / 2 * math.sin(lean)
    mats = []
    for f in range(1, N_SIM + 1):
        scene.frame_set(f)
        mats.append([pr.matrix_world.copy() for pr in proxies])
    for pr in proxies:
        with bpy.context.temp_override(object=pr, active_object=pr, selected_objects=[pr]):
            bpy.ops.rigidbody.object_remove()
    with bpy.context.temp_override(object=ground, active_object=ground, selected_objects=[ground]):
        bpy.ops.rigidbody.object_remove()
    bpy.ops.rigidbody.world_remove()
    scene.frame_set(1)
    orbit_cam(cam, float(arg("--az", "-34")), float(arg("--el", "27")), float(arg("--dist", "15.5")), (0.35, -1.25, 0.3),
              shift=-0.25, lens=float(arg("--lens", "50")))
    cam.data.dof.aperture_fstop = 11
    for f in C.frame_list(N_SIM):
        for pr, m in zip(proxies, mats[f]):
            pr.matrix_world = m
        C.render_to(out(f))


# ================================================================== E "Blue silk"
if JOB == "silk":
    # Two cloth simulations: (1) the silk floats down over the pallet and settles; (2) from that settled shape, one
    # edge is pinned to an invisible hand that draws it up and away to the right, like a car launch. Wind could not
    # lift a sheet lying flat. Bare pallet at both ends of the loop.
    N, F_A = int(arg("--sim", "180")), int(arg("--pull", "96"))
    studio(aim=(0.0, 0.0, 0.3), sun=True)
    C.build_pallet()
    for ob, kind in pk.OBJECTS:                       # the silk drapes over the real boards and blocks
        if kind == "wood":
            ob.modifiers.new("col", "COLLISION")
            ob.collision.thickness_outer = 0.003
            ob.collision.cloth_friction = 1.5
    for ob in scene.objects:
        if ob.name.startswith("floor"):
            ob.modifiers.new("col", "COLLISION")
            ob.collision.thickness_outer = 0.003
            ob.collision.cloth_friction = 2.0
    m = bpy.data.materials.new("silk")
    m.use_nodes = True
    sb = m.node_tree.nodes["Principled BSDF"]
    sb.inputs["Base Color"].default_value = (*C.srgb(arg("--blue", "#0A2A84")), 1)
    sb.inputs["Roughness"].default_value = 0.48
    sb.inputs["Anisotropic"].default_value = 0.6
    sb.inputs["Sheen Weight"].default_value = 0.55              # silk: deep colour, a soft sheen toward the edges
    sb.inputs["Sheen Roughness"].default_value = 0.3
    sb.inputs["Sheen Tint"].default_value = (*C.srgb("#C9D6FF"), 1)
    sb.inputs["Specular IOR Level"].default_value = 0.16

    def cloth(ob, start, end, pin=None):
        cl = ob.modifiers.new("cloth", "CLOTH")
        st = cl.settings
        st.quality = 10
        st.mass = 0.1
        st.air_damping = float(arg("--air", "2.0"))
        st.tension_stiffness = st.compression_stiffness = 8.0
        st.shear_stiffness = 4.0
        st.bending_stiffness = 0.015
        st.time_scale = float(arg("--slow", "0.75"))
        if pin:
            st.vertex_group_mass = pin
            st.pin_stiffness = 1.0
        cs = cl.collision_settings
        cs.distance_min = 0.004
        cs.use_self_collision = True
        cs.self_distance_min = 0.003
        cs.collision_quality = 4
        cl.point_cache.frame_start = start
        cl.point_cache.frame_end = end
        return cl

    def finish(ob):
        ob.modifiers.new("smooth", "SUBSURF").levels = 1
        ob.modifiers.new("thick", "SOLIDIFY").thickness = 0.0012
        for poly in ob.data.polygons:
            poly.use_smooth = True
        ob.data.materials.append(m)

    RES = int(arg("--res", "110"))
    SX, SY = float(arg("--sx", "1.85")), float(arg("--sy", "1.45"))
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=RES, y_subdivisions=int(RES * SY / SX), size=1,
                                    location=(0.05, 0.0, float(arg("--drop", "1.6"))))
    silk = bpy.context.active_object
    silk.name = "silk"
    silk.scale = (SX, SY, 1)
    silk.rotation_euler = (math.radians(4), math.radians(-6), math.radians(9))
    bpy.ops.object.transform_apply(location=True, scale=True, rotation=True)
    for v in silk.data.vertices:                      # a soft ripple, so it does not land like a flat board
        v.co.z += 0.05 * math.sin(v.co.x * 3.1) * math.cos(v.co.y * 2.3)
    right = [v.index for v in silk.data.vertices if v.co.x > max(w.co.x for w in silk.data.vertices) - SX / RES * 1.5]
    cloth(silk, 1, F_A)
    finish(silk)
    orbit_cam(cam, -30, 17, 4.9, (0.0, 0.0, 0.32), shift=-0.24)
    want = set(C.frame_list(N))
    for f in range(1, F_A + 1):
        scene.frame_set(f)
        if f - 1 in want:
            C.render_to(out(f - 1))
    # the settled shape becomes the start of the second simulation
    for md in silk.modifiers:
        if md.type != "CLOTH":
            md.show_viewport = md.show_render = False
    dg = bpy.context.evaluated_depsgraph_get()
    me_a = bpy.data.meshes.new_from_object(silk.evaluated_get(dg), depsgraph=dg)
    silk.hide_render = True
    silk2 = bpy.data.objects.new("silk2", me_a)
    scene.collection.objects.link(silk2)
    me_a.materials.clear()
    vg = silk2.vertex_groups.new(name="pin")
    vg.add(right, 1.0, "REPLACE")
    hand = bpy.data.objects.new("hand", None)
    scene.collection.objects.link(hand)
    c0 = sum((me_a.vertices[i].co for i in right), Vector()) / len(right)
    hand.location = c0
    bpy.context.view_layer.update()
    hk = silk2.modifiers.new("hook", "HOOK")
    hk.object = hand
    hk.vertex_indices_set(right)
    hk.matrix_inverse = hand.matrix_world.inverted()
    PULL = int(arg("--pull-frames", "72"))
    path = [(0.0, Vector((0, 0, 0))), (0.25, Vector((0.25, 0.05, 0.55))), (0.6, Vector((1.4, 0.2, 1.5))),
            (1.0, Vector((3.4, 0.5, 2.6)))]
    for k in range(PULL + 1):                         # an easing pull: slow lift, then away up and out of frame
        u = k / PULL
        for (u0, p0), (u1, p1) in zip(path, path[1:]):
            if u0 <= u <= u1:
                w = ease((u - u0) / (u1 - u0))
                hand.location = c0 + p0.lerp(p1, w)
                break
        hand.keyframe_insert("location", frame=F_A + k)
    cloth(silk2, F_A, N + 1, pin="pin")
    finish(silk2)
    for f in range(F_A, N + 1):
        scene.frame_set(f)
        if f - 1 in want and f > F_A:
            C.render_to(out(f - 1))
