"""PROTOTYPE round 10: a counterbalance forklift (B "Lift", C "The delivery") and pallet racking. Import inside Blender
after common.py. Unbranded: no maker's name or logo anywhere.

build_forklift(parent) builds a forklift whose forks point along -X (it drives forward to the left), with its
front wheels' axle at x = 0 on the floor. Returns a dict: root (move it to drive), carriage (move its z to lift the
forks, 0 = forks on the floor), wheels (rotate them about Y as it drives), fork_x (where the fork blades start, just
in front of the mast; the blades run from there to fork_x - 1.15).
"""
import math

import bmesh
import bpy

import common as C
import loads as LD

scene = C.scene
put, box, lathe, pbsdf = LD.put, LD.box, LD.lathe, LD.pbsdf


def side_prism(name, pts, width, mat, bevel=0.0):
    """An outline in the XZ plane [(x, z), ...] extruded across Y (centred)."""
    bm = bmesh.new()
    a = [bm.verts.new((x, -width / 2, z)) for x, z in pts]
    b = [bm.verts.new((x, width / 2, z)) for x, z in pts]
    bm.faces.new(a)
    bm.faces.new(b[::-1])
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    me.materials.append(mat)
    if bevel:
        bv = ob.modifiers.new("bevel", "BEVEL")
        bv.width, bv.segments, bv.limit_method = bevel, 3, "ANGLE"
    return ob


def wheel(name, r, w, tyre, hub, nuts):
    root = bpy.data.objects.new(name, None)
    scene.collection.objects.link(root)
    t = lathe(name + "_tyre", [(r * 0.62, -w / 2), (r * 0.9, -w / 2), (r, -w / 2 + 0.025), (r, w / 2 - 0.025),
                               (r * 0.9, w / 2), (r * 0.62, w / 2)], [tyre], steps=64)
    put(t, root, (0, 0, 0), (math.radians(90), 0, 0))
    h = lathe(name + "_hub", [(0.0, -w / 2 + 0.03), (r * 0.62, -w / 2 + 0.03), (r * 0.62, w / 2 - 0.03), (0.0, w / 2 - 0.03)],
              [hub], steps=48)
    put(h, root, (0, 0, 0), (math.radians(90), 0, 0))
    cap = lathe(name + "_cap", [(0.0, 0.0), (r * 0.22, 0.0), (r * 0.2, 0.03), (0.0, 0.04)], [nuts], steps=32)
    put(cap, root, (0, -w / 2 + 0.03, 0), (math.radians(90), 0, 0))
    for k in range(6):                                      # wheel nuts: they show the wheel turning
        a = k / 6 * math.tau
        nut = lathe(name + "_nut", [(0.0, 0.0), (0.016, 0.0), (0.016, 0.022), (0.0, 0.022)], [nuts], steps=6, smooth=False)
        put(nut, root, (math.cos(a) * r * 0.36, -w / 2 + 0.01, math.sin(a) * r * 0.36), (math.radians(90), 0, 0))
    return root


def build_forklift(parent=None, body_colour="#0D2C6E", fork_y=0.186):
    """fork_y: the forks' distance from the centre line. 0.186 m slips them between the block rows of an EPAL 1
    entered from its short (800 mm) side."""
    paint = pbsdf("truck_paint", body_colour, rough=0.32, coat=0.35)
    dark = pbsdf("truck_dark", "#26282C", rough=0.45, coat=0.2)
    steel = pbsdf("fork_steel", "#5A5E64", rough=0.4, metal=0.9)
    chrome = pbsdf("rod_chrome", "#D8DCE0", rough=0.08, metal=1.0)
    tyre = pbsdf("truck_tyre", "#1A1A1C", rough=0.75)
    hub = pbsdf("truck_hub", "#2E3135", rough=0.45, metal=0.3)
    seat_m = pbsdf("seat", "#2A2B2E", rough=0.7)
    root = bpy.data.objects.new("forklift", None)
    scene.collection.objects.link(root)
    if parent:
        root.parent = parent
    W = 1.12                                                 # truck width
    # body: from just behind the front wheels to the rounded counterweight at the rear
    body = side_prism("body", [(0.18, 0.12), (2.05, 0.12), (2.32, 0.3), (2.36, 0.62), (2.25, 1.0), (1.55, 1.08),
                               (1.45, 1.0), (0.62, 1.0), (0.45, 0.78), (0.18, 0.62)], W, paint, bevel=0.03)
    put(body, root, (0, 0, 0))
    weight = side_prism("counterweight", [(2.0, 0.12), (2.07, 0.12), (2.34, 0.3), (2.38, 0.62), (2.27, 1.0), (2.12, 1.0),
                                          (2.2, 0.62), (2.18, 0.3)], W + 0.02, dark, bevel=0.02)
    put(weight, root, (0, 0, 0))
    skirt = side_prism("skirt", [(0.18, 0.12), (2.05, 0.12), (2.05, 0.2), (0.18, 0.2)], W + 0.01, dark, bevel=0.01)
    put(skirt, root, (0, 0, 0))
    for s in (-1, 1):
        lamp = lathe("lamp", [(0.0, 0.0), (0.045, 0.0), (0.045, 0.03), (0.0, 0.035)], [pbsdf("lamp", "#F4F1E6", rough=0.1)], steps=24)
        put(lamp, root, (0.52, s * 0.42, 1.95), (0, math.radians(-90), 0))
    hood = side_prism("hood", [(1.35, 1.0), (1.95, 1.0), (1.98, 1.18), (1.42, 1.2)], W - 0.18, paint, bevel=0.03)
    put(hood, root, (0, 0, 0))
    step = side_prism("step", [(0.62, 0.42), (1.0, 0.42), (1.0, 0.5), (0.62, 0.5)], W + 0.06, dark, bevel=0.008)
    put(step, root, (0, 0, 0))
    seat = box("seat", (0.42, 0.48, 0.12), seat_m, bevel=0.03, segs=3)
    put(seat, root, (1.48, 0, 1.25))
    back = box("seat_back", (0.1, 0.48, 0.5), seat_m, bevel=0.03, segs=3)
    put(back, root, (1.68, 0, 1.5), (0, math.radians(-12), 0))
    col = box("steer_column", (0.06, 0.06, 0.62), dark)
    put(col, root, (0.82, 0, 1.25), (0, math.radians(-28), 0))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.17, minor_radius=0.016, major_segments=40, minor_segments=10)
    sw = bpy.context.active_object
    sw.data.materials.append(dark)
    sw.data.shade_smooth()
    put(sw, root, (0.95, 0, 1.52), (0, math.radians(-30), 0))
    # overhead guard: two front posts, two rear posts, a slatted roof
    for x, lean in ((0.55, 8), (1.92, -4)):
        for s in (-1, 1):
            post = box("guard_post", (0.06, 0.06, 1.18), dark, bevel=0.008)
            put(post, root, (x, s * (W / 2 - 0.05), 1.0 + 0.59), (0, math.radians(lean), 0))
    for s in (-1, 1):                                        # an open overhead guard: two rails and cross slats
        rail = box("guard_rail", (1.5, 0.06, 0.06), dark, bevel=0.008)
        put(rail, root, (1.24, s * (W / 2 - 0.05), 2.2))
    for k in range(9):
        slat = box("guard_slat", (0.04, W - 0.1, 0.035), dark, bevel=0.004)
        put(slat, root, (0.56 + k * 0.17, 0, 2.2))
    # wheels: front (drive) under the mast end, rear (steer) under the counterweight
    wheels = []
    for x, r, w in ((0.0 + 0.32, 0.33, 0.23), (1.88, 0.27, 0.19)):
        for s in (-1, 1):
            wh = wheel("wheel", r, w, tyre, hub, steel)
            put(wh, root, (x, s * (W / 2 - w / 2 + 0.02), r))
            if s > 0:                                       # the far wheels face outwards too
                wh.rotation_euler = (0, 0, math.radians(180))
            wheels.append(wh)
    # mast: two channels at the front, tilt cylinders, lift cylinder, chains
    mast_x = -0.05
    inner_root = bpy.data.objects.new("mast_inner_stage", None)   # the telescoping inner stage (see lift())
    scene.collection.objects.link(inner_root)
    put(inner_root, root, (0, 0, 0))
    for s in (-1, 1):
        ch = box("mast_channel", (0.11, 0.07, 2.3), dark, bevel=0.006)
        put(ch, root, (mast_x, s * 0.36, 0.12 + 1.15))
        inner = box("mast_inner", (0.09, 0.05, 2.25), dark, bevel=0.005)
        put(inner, inner_root, (mast_x - 0.01, s * 0.29, 0.14 + 1.12))
        tilt = lathe("tilt_cyl", [(0.0, 0.0), (0.035, 0.0), (0.035, 0.36), (0.0, 0.36)], [dark], steps=20)
        put(tilt, root, (0.25, s * 0.42, 0.72), (0, math.radians(-70), 0))
        rod = lathe("tilt_rod", [(0.0, 0.0), (0.018, 0.0), (0.018, 0.26), (0.0, 0.26)], [chrome], steps=16)
        put(rod, root, (0.08, s * 0.42, 0.66), (0, math.radians(-70), 0))
    for z0, z1, mat, r, par in ((0.2, 1.5, dark, 0.05, root), (1.5, 2.25, chrome, 0.026, inner_root)):
        cyl = lathe("lift_cyl", [(0.0, 0.0), (r, 0.0), (r, z1 - z0), (0.0, z1 - z0)], [mat], steps=24)
        put(cyl, par, (mast_x + 0.1, 0, z0))
    top = box("mast_head", (0.12, 0.66, 0.08), dark, bevel=0.006)
    put(top, inner_root, (mast_x - 0.01, 0, 2.43))
    outer_top = box("mast_tie", (0.12, 0.8, 0.06), dark, bevel=0.006)
    put(outer_top, root, (mast_x, 0, 2.39))
    # carriage: plate, load guard grille, and the two forks hanging on it
    carriage = bpy.data.objects.new("carriage", None)
    scene.collection.objects.link(carriage)
    put(carriage, root, (0, 0, 0))
    plate = box("carriage_plate", (0.06, 0.98, 0.42), dark, bevel=0.006)
    put(plate, carriage, (mast_x - 0.1, 0, 0.3))
    for z in (0.1, 0.5):
        bar = box("carriage_bar", (0.07, 1.0, 0.05), dark, bevel=0.005)
        put(bar, carriage, (mast_x - 0.11, 0, z))
    for k in range(7):
        g = box("guard_bar", (0.025, 0.025, 0.72), dark)
        put(g, carriage, (mast_x - 0.12, -0.42 + k * 0.14, 0.86))
    gtop = box("guard_top", (0.04, 0.98, 0.04), dark)
    put(gtop, carriage, (mast_x - 0.12, 0, 1.22))
    fork_x = mast_x - 0.16
    for s in (-1, 1):
        shank = box("fork_shank", (0.045, 0.1, 0.5), steel, bevel=0.004)
        put(shank, carriage, (fork_x + 0.02, s * fork_y, 0.27))
        blade = side_prism("fork_blade", [(0.0, 0.0), (-1.1, 0.0), (-1.15, 0.012), (-1.15, 0.035), (-0.05, 0.045), (0.0, 0.045)],
                           0.1, steel, bevel=0.004)
        put(blade, carriage, (fork_x + 0.04, s * fork_y, 0.0))
    def lift(z):
        """Raise the forks to z (m above the floor); the inner mast stage follows once the carriage nears its top."""
        carriage.location.z = z
        inner_root.location.z = max(0.0, z - 0.95)
    return {"root": root, "carriage": carriage, "inner": inner_root, "lift": lift, "wheels": wheels, "fork_x": fork_x,
            "wheel_r": (0.33, 0.27)}


def build_rack(bays, levels, bay_w=2.7, depth=1.1, beam_h=1.5, parent=None, upright="#2A4F8F", beam="#E2781F"):
    """Selective pallet racking: uprights every bay_w along X, `levels` beam levels above the floor; the face is at
    y = 0, the back at y = depth. Returns the beam top heights."""
    up = pbsdf("rack_upright", upright, rough=0.45, coat=0.3)
    bm = pbsdf("rack_beam", beam, rough=0.4, coat=0.3)
    root = bpy.data.objects.new("rack", None)
    scene.collection.objects.link(root)
    if parent:
        root.parent = parent
    H = beam_h * levels + 1.0
    tops = []
    for i in range(bays + 1):
        x = i * bay_w
        for y in (0.04, depth - 0.04):
            post = box("upright", (0.09, 0.07, H), up, bevel=0.004)
            put(post, root, (x, y, H / 2))
            plate = box("foot_plate", (0.16, 0.14, 0.008), up)
            put(plate, root, (x, y, 0.004))
        for k in range(int(H / 0.9)):                       # bracing between front and back uprights
            br = box("brace", (0.03, depth - 0.1, 0.03), up)
            put(br, root, (x, depth / 2, 0.3 + k * 0.9), (math.radians(28 if k % 2 else -28), 0, 0))
    for lv in range(1, levels + 1):
        z = lv * beam_h
        tops.append(z)
        for i in range(bays):
            x = i * bay_w + bay_w / 2
            for y in (0.04, depth - 0.04):
                b = box("beam", (bay_w - 0.09, 0.05, 0.12), bm, bevel=0.004)
                put(b, root, (x, y, z - 0.06))
    return root, tops
