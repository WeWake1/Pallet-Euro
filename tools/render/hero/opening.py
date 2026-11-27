"""PROTOTYPE round 11 · D "Through the opening" (decision #78): an endless flight through the fork openings of EPAL 1
pallets. In every place two pallets stand on the floor: the camera comes out of the first (A), flies low across the
place and into a fork opening of the second (B), past its branded blocks. Through B's opening the next place is
already visible, and the camera comes out of A there. Places: factory -> india -> port -> europe -> factory (a loop).
Nothing may stand behind A (y < -0.5): the portal frames look through A from there.

One Blender run per place and pass (`python tools/render/run.py r11-opening` runs all eight, then opening_comp.py):
  --place NAME --pass seg      its own stretch of the flight, RGBA: B's far opening is a holdout where the next place
                               will show: <root>/seg/<place>/NN.png, plus meta.json (which frames have a hole, and
                               how far through the opening the camera is)
  --place NAME --pass portal   the previous place's stretch seen from inside this place, only the frames whose seg
                               picture has a hole; RGBA again: this place's own B opening is a holdout too
                               (<root>/portal/<place>/NN.png and meta.json)
  --place NAME --pass portal2  the stretch two places back, seen from inside this place, only inside that holdout (a
                               render border round it): what shows through the far pallet once the camera is in the
                               opening, so it does not flip from wall to the next place at the seam
                               (<root>/portal2/<place>/NN.png)
<root> is tools/render/out/opening (.render-test/opening with --test). opening_comp.py lays each seg frame over its
portal frame (and that over its portal2 frame), cross-fades the walls of the opening as the camera passes through,
and writes public/dev/r11/opening/.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PLACE = arg("--place", "factory")
PASS = arg("--pass", "seg")
OUT = os.path.join(ROOT, ".render-test" if C.args.test else os.path.join("tools", "render", "out"), "opening")
ORDER = ["factory", "india", "port", "europe"]
F = 84                                   # frames per place (3.5 s at 24 fps; the loop is 336 frames)
XO, ZT, HALF = -0.26375, 0.072, 0.40     # the opening flown through: long side, left of the middle block; faces at y = -/+0.40
VE = 0.035                               # camera speed in the openings, metres per frame
pk = C.pk
scene = C.scene

# where B stands in each place (x, y, yaw), and the middle of the flight between the pallets (x, y, height)
PLACES = {
    "factory": dict(b=(1.9, 4.8, -28.0), mid=(1.3, 2.4, 0.55)),
    "india":  dict(b=(-1.8, 4.6, 24.0), mid=(-0.6, 2.4, 0.65)),
    "port":   dict(b=(1.5, 5.0, -18.0), mid=(1.2, 2.5, 1.0)),
    "europe": dict(b=(-1.6, 4.5, 20.0), mid=(-1.0, 2.3, 0.6)),
}


def pose(x, y, yaw):
    return Matrix.Translation((x, y, 0)) @ Matrix.Rotation(math.radians(yaw), 4, "Z")


def catmull(P, samples=80):
    """Centripetal Catmull-Rom through P[1] .. P[-2] (P[0] and P[-1] only steer the ends)."""
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        t0 = 0.0
        t1 = t0 + (p1 - p0).length ** 0.5
        t2 = t1 + (p2 - p1).length ** 0.5
        t3 = t2 + (p3 - p2).length ** 0.5
        for k in range(samples):
            t = t1 + (t2 - t1) * k / samples
            a1 = p0 * ((t1 - t) / (t1 - t0)) + p1 * ((t - t0) / (t1 - t0))
            a2 = p1 * ((t2 - t) / (t2 - t1)) + p2 * ((t - t1) / (t2 - t1))
            a3 = p2 * ((t3 - t) / (t3 - t2)) + p3 * ((t - t2) / (t3 - t2))
            b1 = a1 * ((t2 - t) / (t2 - t0)) + a2 * ((t - t0) / (t2 - t0))
            b2 = a2 * ((t3 - t) / (t3 - t1)) + a3 * ((t - t1) / (t3 - t1))
            out.append(b1 * ((t2 - t) / (t2 - t1)) + b2 * ((t - t1) / (t2 - t1)))
    out.append(P[-2].copy())
    return out


class Flight:
    """The camera's stretch in one place: out of A's opening (A stands at the origin), across, through B's opening."""

    def __init__(self, name):
        self.name = name
        p = PLACES[name]
        self.B = pose(*p["b"])
        A = Matrix.Identity(4)
        pt = lambda M, y, dz=0.0: M @ Vector((XO, y, ZT + dz))
        P = [pt(A, -HALF), pt(A, HALF), pt(A, 1.1, 0.05), Vector(p["mid"]), pt(self.B, -1.7, 0.04), pt(self.B, -HALF),
             pt(self.B, HALF), pt(self.B, 1.3)]
        self.pts = catmull(P)
        d = [0.0]
        for a, b in zip(self.pts, self.pts[1:]):
            d.append(d[-1] + (b - a).length)
        self.d = np.array(d)
        self.L = d[-1]
        self.entry = self.d[4 * 80]                   # arc length where the camera enters B (sample boundary at P[5])
        self.v0 = (P[2] - P[1]).normalized()
        self.v1 = (P[-1] - P[-2]).normalized()

    def at(self, s):
        if s <= 0:
            return self.pts[0] + self.v0 * s
        if s >= self.L:                               # past B: on along the next place's path (its A is our B), so
            nxt = flight(ORDER[(ORDER.index(self.name) + 1) % len(ORDER)])   # the look-ahead turns the same way at a seam
            return self.B @ nxt.at(min(s - self.L, nxt.L))
        j = int(np.searchsorted(self.d, s)) - 1
        t = (s - self.d[j]) / (self.d[j + 1] - self.d[j])
        return self.pts[j].lerp(self.pts[j + 1], t)

    def s_of(self, i):
        """Arc length at frame i (0..F): slow (VE) in the openings at both ends, faster across the place."""
        u = i / F
        vm = 2 * self.L / F - VE
        return F * (VE * u + (vm - VE) * (u / 2 - math.sin(math.tau * u) / (2 * math.tau)))

    def cam(self, i):
        s = self.s_of(i)
        loc = self.at(s)
        rot = (self.at(s + 0.5) - loc).to_track_quat("-Z", "Y")
        return Matrix.Translation(loc) @ rot.to_matrix().to_4x4()

    def through(self, i):
        """0 before B's opening, 1 at its far face: how far the camera is through it."""
        x = (self.s_of(i) - self.entry) / (self.L - self.entry)
        x = min(max(x, 0.0), 1.0)
        return x * x * (3 - 2 * x)


FLIGHTS = {}


def flight(name):
    if name not in FLIGHTS:
        FLIGHTS[name] = Flight(name)
    return FLIGHTS[name]


# ================================================================== materials and helpers for the places
def emission(name, hexcol, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    n.remove(n["Principled BSDF"])
    e = n.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*C.srgb(hexcol), 1)
    e.inputs["Strength"].default_value = strength
    m.node_tree.links.new(e.outputs[0], n["Material Output"].inputs["Surface"])
    return m


def concrete(line_y=None):
    """Polished warehouse concrete; with line_y a worn yellow floor line (100 mm) along x."""
    m = bpy.data.materials.new("concrete")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Specular IOR Level"].default_value = 0.45
    tc = n.new("ShaderNodeTexCoord")
    mot = n.new("ShaderNodeTexNoise"); mot.inputs["Scale"].default_value = 1.4; mot.inputs["Detail"].default_value = 12.0
    l.new(tc.outputs["Object"], mot.inputs["Vector"])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*C.srgb("#C9C9C6"), 1)
    ramp.color_ramp.elements[1].color = (*C.srgb("#DCDCD9"), 1)
    l.new(mot.outputs["Fac"], ramp.inputs["Fac"])
    col = ramp.outputs["Color"]
    if line_y is not None:
        sep = n.new("ShaderNodeSeparateXYZ")
        l.new(tc.outputs["Object"], sep.inputs[0])
        d = n.new("ShaderNodeMath"); d.operation = "SUBTRACT"
        l.new(sep.outputs["Y"], d.inputs[0]); d.inputs[1].default_value = line_y
        ad = n.new("ShaderNodeMath"); ad.operation = "ABSOLUTE"
        l.new(d.outputs[0], ad.inputs[0])
        band = n.new("ShaderNodeMath"); band.operation = "LESS_THAN"
        l.new(ad.outputs[0], band.inputs[0]); band.inputs[1].default_value = 0.05
        wear = n.new("ShaderNodeTexNoise"); wear.inputs["Scale"].default_value = 14.0; wear.inputs["Detail"].default_value = 8.0
        l.new(tc.outputs["Object"], wear.inputs["Vector"])
        wr = n.new("ShaderNodeMapRange")
        wr.inputs["From Min"].default_value, wr.inputs["From Max"].default_value = 0.38, 0.5
        l.new(wear.outputs["Fac"], wr.inputs["Value"])
        ln = n.new("ShaderNodeMath"); ln.operation = "MULTIPLY"
        l.new(band.outputs[0], ln.inputs[0]); l.new(wr.outputs[0], ln.inputs[1])
        mix = n.new("ShaderNodeMix"); mix.data_type = "RGBA"
        l.new(ln.outputs[0], mix.inputs["Factor"])
        l.new(col, mix.inputs[6])
        mix.inputs[7].default_value = (*C.srgb("#D9A922"), 1)
        col = pk.out_of_type(mix, "RGBA")
    l.new(col, b.inputs["Base Color"])
    rough = n.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value, rough.inputs["To Max"].default_value = 0.25, 0.55
    l.new(mot.outputs["Fac"], rough.inputs["Value"])
    l.new(rough.outputs[0], b.inputs["Roughness"])
    fine = n.new("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 420.0; fine.inputs["Detail"].default_value = 4.0
    l.new(tc.outputs["Object"], fine.inputs["Vector"])
    bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.07
    l.new(fine.outputs["Fac"], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def painted_brick():
    m = bpy.data.materials.new("brick")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.88
    b.inputs["Specular IOR Level"].default_value = 0.25
    tc = n.new("ShaderNodeTexCoord")
    br = n.new("ShaderNodeTexBrick")
    br.offset, br.offset_frequency = 0.5, 1
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = 0.225
    br.inputs["Row Height"].default_value = 0.075
    br.inputs["Mortar Size"].default_value = 0.009
    br.inputs["Mortar Smooth"].default_value = 0.5
    br.inputs["Color1"].default_value = (*C.srgb("#F2F1ED"), 1)
    br.inputs["Color2"].default_value = (*C.srgb("#E3E1DB"), 1)
    br.inputs["Mortar"].default_value = (*C.srgb("#CFCDC6"), 1)
    br.inputs["Bias"].default_value = -0.2
    l.new(tc.outputs["Object"], br.inputs["Vector"])
    l.new(br.outputs["Color"], b.inputs["Base Color"])
    bump = n.new("ShaderNodeBump"); bump.invert = True
    bump.inputs["Strength"].default_value = 0.9
    bump.inputs["Distance"].default_value = 0.007
    l.new(br.outputs["Fac"], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def corrugated_paint(hexcol, pitch=0.28):
    """Container paint with its corrugation as a bump across x (object space)."""
    m = bpy.data.materials.new("container_paint")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.45
    b.inputs["Specular IOR Level"].default_value = 0.5
    tc = n.new("ShaderNodeTexCoord")
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.2; nz.inputs["Detail"].default_value = 6.0
    l.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = n.new("ShaderNodeValToRGB")
    base = Vector(C.srgb(hexcol))
    ramp.color_ramp.elements[0].color = (*(base * 0.86), 1)
    ramp.color_ramp.elements[1].color = (*(base * 1.04), 1)
    l.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    l.new(ramp.outputs["Color"], b.inputs["Base Color"])
    wv = n.new("ShaderNodeTexWave")
    wv.wave_type = "BANDS"
    wv.bands_direction = "X"
    wv.wave_profile = "TRI"
    wv.inputs["Scale"].default_value = 1.0 / pitch
    wv.inputs["Distortion"].default_value = 0.0
    l.new(tc.outputs["Object"], wv.inputs["Vector"])
    cl = n.new("ShaderNodeMapRange")                 # flat faces with sloped flanks
    cl.inputs["From Min"].default_value, cl.inputs["From Max"].default_value = 0.3, 0.7
    l.new(wv.outputs["Fac"], cl.inputs["Value"])
    bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 1.0; bump.inputs["Distance"].default_value = 0.03
    l.new(cl.outputs[0], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def box(name, x0, x1, y0, y1, z0, z1, material):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((x1 if v.co.x > 0 else x0, y1 if v.co.y > 0 else y0, z1 if v.co.z > 0 else z0))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


def gobo(img, size, centre, to_sun, tile):
    """A patterned screen between the sun and the floor, seen only by shadows, with blockers round it."""
    rot = to_sun.to_track_quat("Z", "Y")
    w, h = size
    big = 40.0
    parts = [(C.plane("gobo", w, h, material=C.gobo_material(img, w, h, tile=tile)), (0, 0))]
    for u, v, bw, bh in ((-(w + big) / 2, 0, big, 2 * big), ((w + big) / 2, 0, big, 2 * big), (0, (h + big) / 2, w, big),
                         (0, -(h + big) / 2, w, big)):
        parts.append((C.plane("blocker", bw, bh, material=C.mat("blocker", "#777777")), (u, v)))
    for ob, (du, dv) in parts:
        ob.rotation_euler = rot.to_euler()
        ob.location = centre + rot @ Vector((du, dv, 0))
        C.shadow_only(ob)


def sun_dir(el, az):
    el, az = math.radians(el), math.radians(az)
    return Vector((-math.cos(el) * math.cos(az), -math.cos(el) * math.sin(az), math.sin(el)))


# ================================================================== the four places
def stack(coll, x, y, yaw, n, rng):
    """n EPAL 1 pallets stacked, each a little off square, as they come off the line."""
    for j in range(n):
        e = bpy.data.objects.new("stacked", None)
        e.instance_type = "COLLECTION"
        e.instance_collection = coll
        scene.collection.objects.link(e)
        e.location = (x + rng.uniform(-0.012, 0.012), y + rng.uniform(-0.012, 0.012), j * pk.R["dims"][2] * pk.MM)
        e.rotation_euler = (0, 0, math.radians(yaw + rng.choice((0, 180)) + rng.uniform(-0.8, 0.8)))


def build_factory(fl, coll):
    """A bright pallet factory: rows of fresh EPAL 1 stacks either side of the flight, skylights overhead."""
    import random
    rng = random.Random(3)
    C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.4)
    C.plane("floor", 60, 60, loc=(0, 10, 0), material=concrete())
    C.plane("back_wall", 40, 10, loc=(0, 13.0, 5.0), rot=(math.radians(90), 0, 0), material=C.plaster("#F7F5F1", "#FBFAF7"))
    wl = C.area("wall_wash", (0.5, 7.0, 4.0), 10.0, 2200, color="#FFF8EE", look=(0.5, 13.0, 3.0))
    wl.visible_camera = False
    roof = C.plane("roof", 40, 40, loc=(0, 6.0, 7.5), rot=(math.pi, 0, 0), material=C.mat("roof", "#F4F3F0", rough=0.9))
    roof.visible_shadow = False
    glow = emission("skylight", "#F7F9FF", 3.0)
    for x in (-4.5, 0.8, 6.0):                        # skylight strips in the roof
        sk = C.plane("skylight", 1.6, 30, loc=(x, 6.0, 7.49), rot=(math.pi, 0, 0), material=glow)
        sk.visible_shadow = False
    for y in (1.2, 2.7, 4.2, 5.7, 7.2, 8.7):          # rows across the hall, clear of the flight
        for x in (-3.4, -2.0, 3.6, 5.0) if y < 4 else (-3.6, -2.2, -0.8, 3.8, 5.2):
            stack(coll, x, y, 0, rng.randint(7, 15), rng)
    C.world("#F2F3F5", 0.9)
    for k, y in enumerate((1.0, 5.0, 9.0)):           # skylights
        a = C.area(f"sky{k}", (0.8, y, 6.5), 4.0, 1400, color="#F4F7FF", look=(0.8, y, 0))
        a.visible_camera = False
    s = C.sun("sun", 3.5, color="#FFF3E4", angle_deg=1.0)
    C.aim_sun(s, elev_deg=58, azim_deg=40)


def build_india(fl, coll):
    C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.45)
    C.plane("floor", 40, 40, loc=(0, 3, 0), material=C.stone_floor())
    bx, by = PLACES["india"]["b"][:2]
    wall = C.plaster("#F3EFE8")
    C.plane("back_wall", 30, 8, loc=(0, by + 2.2, 4.0), rot=(math.radians(90), 0, 0), material=wall)
    side = C.plane("side_wall", 30, 8, loc=(-7.0, 3, 4.0), rot=(math.radians(90), 0, math.radians(90)), material=wall)
    side.visible_shadow = False                       # the sun comes in through its jaali (the gobo below)
    n = 512                                           # the jaali: an eight-point-star lattice (as in round 4)
    ys, xs = np.mgrid[0:n, 0:n]
    u, v = (xs + 0.5) / n - 0.5, (ys + 0.5) / n - 0.5
    ax, ay = np.abs(u), np.abs(v)
    star = np.minimum(np.maximum(ax, ay) - 0.30, (ax + ay) / math.sqrt(2) - 0.30)
    corner = ((0.5 - ax) + (0.5 - ay)) / math.sqrt(2) - 0.13 / math.sqrt(2)
    stone = np.clip(np.minimum(star, corner) / (1.6 / n) + 0.5, 0.0, 1.0)
    img = C.save_mask("opening_jaali", stone)
    to_sun = sun_dir(30, 35)                          # low morning sun from the front left, through the side wall's jaali
    gobo(img, (6.5, 4.6), Vector((-1.0, 3.4, 0.0)) + to_sun * 4.0, to_sun, 0.34)
    C.world("#F3EEE6", 0.6)
    s = C.sun("sun", 8.0, color="#FFE6C7", angle_deg=0.3)
    s.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()
    C.area("fill", (2.5, -1.0, 2.6), 6.0, 300, color="#EEF2FF", look=(0, 2.5, 0.3))
    C.area("bounce", (0.0, 3.0, 4.0), 6.0, 140, color="#FFF6EA", look=(0, 3.0, 0))


def build_port(fl, coll):
    C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.25)
    C.plane("floor", 60, 60, loc=(0, 3, 0), material=concrete(line_y=PLACES["port"]["b"][1] + 1.2))
    bx, by = PLACES["port"]["b"][:2]
    blue = corrugated_paint("#1F3D78")
    blue2 = corrugated_paint("#163066")
    W40, H = 12.19, 2.59
    y0 = by + 2.0                                     # a row of 40' containers behind B, one stacked on top, set back
    for k, (x0, z0, mat_) in enumerate(((-W40 + 2.2, 0.0, blue), (2.4, 0.0, blue2), (-4.0, H, blue2))):
        box(f"container{k}", x0, x0 + W40, y0 + (0.3 if z0 else 0.0), y0 + 2.44 + (0.3 if z0 else 0.0), z0, z0 + H, mat_)
    import random
    rng = random.Random(5)
    for x, y, n in ((-2.6, 3.0, 6), (-3.8, 4.2, 9), (3.4, 2.4, 5), (4.4, 3.8, 8)):   # stacks waiting on the quay
        stack(coll, x, y, 0, n, rng)
    C.world("#EAF1FA", 1.0)
    s = C.sun("sun", 5.5, color="#FFF4E6", angle_deg=0.6)
    C.aim_sun(s, elev_deg=42, azim_deg=55)
    C.area("fill", (0.0, -3.0, 3.0), 6.0, 200, color="#EEF4FF", look=(0, 3, 0.4))


def build_europe(fl, coll):
    C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.42)
    bx, by = PLACES["europe"]["b"][:2]
    C.plane("floor", 40, 40, loc=(0, 3, 0), material=concrete(line_y=by + 1.05))
    C.plane("back_wall", 30, 8, loc=(0, by + 1.7, 4.0), rot=(math.radians(90), 0, 0), material=painted_brick())
    n = 512                                           # a steel factory window: thin glazing bars
    ys, xs = np.mgrid[0:n, 0:n]
    u, v = (xs + 0.5) / n, (ys + 0.5) / n
    edge = np.minimum(np.minimum(u, 1 - u), np.minimum(v, 1 - v))
    steel = np.clip((0.075 / 2 - edge) / (1.6 / n) + 0.5, 0.0, 1.0)
    img = C.save_mask("opening_window", steel)
    to_sun = sun_dir(32, 30)
    gobo(img, (3.4, 2.6), Vector((-0.8, 2.6, 0.0)) + to_sun * 3.2, to_sun, 0.45)
    import random
    rng = random.Random(9)
    for x, n in ((-4.2, 12), (-3.0, 9), (1.4, 10), (2.6, 13), (3.8, 8)):    # stacks along the brick wall
        stack(coll, x, by + 1.05, 0, n, rng)
    C.world("#E3E9F1", 0.85)
    s = C.sun("sun", 5.2, color="#E9EFFA", angle_deg=2.2)
    s.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()
    C.area("fill", (3.0, -1.5, 2.4), 5.0, 260, color="#E8EEF8", look=(0, 2.5, 0.4))
    try:
        scene.view_settings.use_white_balance = True
        scene.view_settings.white_balance_temperature = 6200
    except (AttributeError, TypeError):
        pass


BUILD = {"factory": build_factory, "india": build_india, "port": build_port, "europe": build_europe}

# ================================================================== the run
fl = flight(PLACE)
C.build_pallet()
coll = bpy.data.collections.new("epal1")
for ob in [pk.ROOT] + [o for o, _ in pk.OBJECTS]:
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
BUILD[PLACE](fl, coll)
scene.cycles.samples = 24 if C.args.test else C.args.samples
scene.render.use_motion_blur = True
scene.render.motion_blur_shutter = 0.4
for name, M in (("A", Matrix.Identity(4)), ("B", fl.B)):
    e = bpy.data.objects.new(name, None)
    e.instance_type = "COLLECTION"
    e.instance_collection = coll
    scene.collection.objects.link(e)
    e.matrix_world = M

cd = bpy.data.cameras.new("cam")
cd.lens = 20
cd.sensor_width = 36
cd.clip_start = 0.004                                 # inside the opening the boards are a few centimetres away
cam = bpy.data.objects.new("cam", cd)
scene.collection.objects.link(cam)
scene.camera = cam
cam.rotation_mode = "QUATERNION"


def key_camera(mats):
    """Keyframe the camera on every frame (scene frame = i + 1) so Cycles blurs the motion between frames."""
    prev = None
    for i, M in enumerate(mats):
        loc, q, _ = M.decompose()
        if prev is not None:
            q.make_compatible(prev)
        prev = q
        cam.location = loc
        cam.rotation_quaternion = q
        cam.keyframe_insert("location", frame=i + 1)
        cam.keyframe_insert("rotation_quaternion", frame=i + 1)


def save_png(path, rgba):
    s = scene.render.image_settings
    s.file_format = "PNG"
    s.color_mode = "RGBA" if rgba else "RGB"
    s.color_depth = "8"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("WROTE", path, flush=True)


CARD = (-0.455 - 0.002, -0.0725 + 0.002, 0.022 - 0.002, 0.122 + 0.002)   # x0, x1, z0, z1 of the opening's far face


def hole_card(M):
    """A holdout card on the far face of the opening of the pallet at M, seen only by the camera: alpha 0 there."""
    x0, x1, z0, z1 = CARD
    me = bpy.data.meshes.new("portal")
    me.from_pydata([(x0, HALF + 0.001, z0), (x1, HALF + 0.001, z0), (x1, HALF + 0.001, z1), (x0, HALF + 0.001, z1)], [],
                   [(0, 1, 2, 3)])
    hold = bpy.data.materials.new("holdout")
    hold.use_nodes = True
    hn = hold.node_tree.nodes
    hn.remove(hn["Principled BSDF"])
    hold.node_tree.links.new(hn.new("ShaderNodeHoldout").outputs[0], hn["Material Output"].inputs["Surface"])
    me.materials.append(hold)
    ob = bpy.data.objects.new("portal", me)
    scene.collection.objects.link(ob)
    ob.matrix_world = M
    for attr in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter", "visible_shadow"):
        setattr(ob, attr, False)


def render_holes(d, frames):
    """Render the frames as RGBA PNGs into d; return the frames that have a hole (kept in d/meta.json)."""
    os.makedirs(d, exist_ok=True)
    meta_path = os.path.join(d, "meta.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {"holes": []}
    holes = set(meta["holes"])
    for i in frames:
        scene.frame_set(i + 1)
        path = os.path.join(d, f"{i:02d}.png")
        save_png(path, rgba=True)
        img = bpy.data.images.load(path)
        px = np.empty(img.size[0] * img.size[1] * 4, np.float32)
        img.pixels.foreach_get(px)
        bpy.data.images.remove(img)
        if px[3::4].min() < 0.999:
            holes.add(i)
        else:
            holes.discard(i)
    return holes, meta_path


if PASS == "seg":
    hole_card(fl.B)
    key_camera([fl.cam(i) for i in range(F + 1)])
    holes, meta_path = render_holes(os.path.join(OUT, "seg", PLACE), C.frame_list(F))
    json.dump({"frames": F, "holes": sorted(holes), "through": [round(fl.through(i), 4) for i in range(F)]},
              open(meta_path, "w"), indent=1)

if PASS == "portal":
    prev = ORDER[(ORDER.index(PLACE) - 1) % len(ORDER)]
    inv = flight(prev).B.inverted()                  # the previous place's B is this place's A (at the origin)
    hole_card(fl.B)                                  # where the place after this one will show
    key_camera([inv @ flight(prev).cam(i) for i in range(F + 1)])
    seg_holes = json.load(open(os.path.join(OUT, "seg", prev, "meta.json")))["holes"]
    want = set(C.frame_list(F))
    holes, meta_path = render_holes(os.path.join(OUT, "portal", PLACE), [i for i in seg_holes if i in want])
    json.dump({"frames": F, "holes": sorted(holes)}, open(meta_path, "w"), indent=1)

if PASS == "portal2":
    from bpy_extras.object_utils import world_to_camera_view
    p1 = ORDER[(ORDER.index(PLACE) - 1) % len(ORDER)]
    p2 = ORDER[(ORDER.index(PLACE) - 2) % len(ORDER)]
    M = flight(p1).B.inverted() @ flight(p2).B.inverted()
    key_camera([M @ flight(p2).cam(i) for i in range(F + 1)])
    meta_path = os.path.join(OUT, "portal", p1, "meta.json")
    holes = json.load(open(meta_path))["holes"] if os.path.exists(meta_path) else []
    d = os.path.join(OUT, "portal2", PLACE)
    os.makedirs(d, exist_ok=True)
    x0, x1, z0, z1 = CARD                            # p1's B opening, seen from here, is our A's far face
    corners = [Vector((x, HALF, z)) for x in (x0, x1) for z in (z0, z1)]
    want = set(C.frame_list(F))
    r = scene.render
    for i in holes:
        if i not in want:
            continue
        xs, ys = [], []
        for sub in (-0.3, 0.0, 0.3):                 # across the shutter, for the blur
            f0 = math.floor(sub)
            scene.frame_set(i + 1 + f0, subframe=sub - f0)
            for c in corners:
                v = world_to_camera_view(scene, cam, c)
                if v.z > 0:
                    xs.append(v.x)
                    ys.append(v.y)
        scene.frame_set(i + 1)
        if not xs:
            continue
        r.use_border, r.use_crop_to_border = True, False
        r.border_min_x, r.border_max_x = max(min(xs) - 0.02, 0.0), min(max(xs) + 0.02, 1.0)
        r.border_min_y, r.border_max_y = max(min(ys) - 0.03, 0.0), min(max(ys) + 0.03, 1.0)
        if r.border_max_x - r.border_min_x < 0.002 or r.border_max_y - r.border_min_y < 0.002:
            continue
        save_png(os.path.join(d, f"{i:02d}.png"), rgba=True)
