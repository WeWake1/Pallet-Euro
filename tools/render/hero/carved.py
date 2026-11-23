"""PROTOTYPE round 7 · C "Carved" (the crazy one): a solid slab of spruce, exactly the size of an EPAL 1, is cut away
by an invisible front that crosses it from right to left; the wood turns to sawdust that bursts into the air and
fades, and the finished pallet stands where the slab was, as if it had always been inside. Each frame is one step
of the carving; the page scrubs them with the cursor (by itself on phones). Nothing is simulated: the front and every
grain follow formulas, so the frames are the same whether played forward or back.

  Blender -b --factory-startup --python tools/render/hero/carved.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/r7/carved [--frames 0-47] [--test]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

COUNT = 48
SWEEP_S = 2.4                     # the whole carving, in seconds of "real" time (for the flight of the grains)
scene = C.scene
pk = C.pk
C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.2)
C.seamless_studio(bg="#F3F0EB", floor="#F0ECE6", fade=(2.6, 6.5), fill="#EEF0F5", fill_strength=0.6, rough=0.75,
                  bg_strength=2.7)
rng = np.random.default_rng(11)

PALLET = Vector((0.55, 0.30, 0.0))
C.build_pallet(rot_deg=-28, loc=PALLET)
L, WD, HT = (v * pk.MM for v in pk.R["dims"])
PAD = 0.0025                       # the slab is a little larger than the pallet, so it hides it completely

# ------------------------------------------------------------------ the slab: raw spruce, growth rings along X
timber = bpy.data.materials.new("timber")
timber.use_nodes = True
n, l = timber.node_tree.nodes, timber.node_tree.links
b = n["Principled BSDF"]
b.inputs["Roughness"].default_value = 0.78
tc = n.new("ShaderNodeTexCoord")
mp = n.new("ShaderNodeMapping")
mp.inputs["Location"].default_value = (0.0, 0.62, 0.38)          # the log's heart lies outside the slab
l.new(tc.outputs["Object"], mp.inputs["Vector"])
wave = n.new("ShaderNodeTexWave")
wave.wave_type = "RINGS"
wave.rings_direction = "X"
wave.inputs["Scale"].default_value = 40.0
wave.inputs["Distortion"].default_value = 5.0
wave.inputs["Detail"].default_value = 3.0
wave.inputs["Detail Scale"].default_value = 1.2
l.new(mp.outputs["Vector"], wave.inputs["Vector"])
ramp = n.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.35
ramp.color_ramp.elements[0].color = (*C.srgb("#C9A673"), 1)
ramp.color_ramp.elements[1].position = 0.8
ramp.color_ramp.elements[1].color = (*C.srgb("#EFDFC4"), 1)
l.new(wave.outputs["Fac"], ramp.inputs["Fac"])
fib = n.new("ShaderNodeTexNoise")                                  # fine fibres along the grain
fib.inputs["Scale"].default_value = 90.0
fib.inputs["Detail"].default_value = 6.0
fmap = n.new("ShaderNodeMapping")
fmap.inputs["Scale"].default_value = (0.04, 1.0, 1.0)
l.new(tc.outputs["Object"], fmap.inputs["Vector"])
l.new(fmap.outputs["Vector"], fib.inputs["Vector"])
mix = n.new("ShaderNodeMix")
mix.data_type = "RGBA"
mix.blend_type = "MULTIPLY"
mix.inputs["Factor"].default_value = 0.3
l.new(ramp.outputs["Color"], mix.inputs["A"])
l.new(fib.outputs["Color"], mix.inputs["B"])
l.new(mix.outputs["Result"], b.inputs["Base Color"])
bump = n.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.06
l.new(fib.outputs["Fac"], bump.inputs["Height"])
l.new(bump.outputs["Normal"], b.inputs["Normal"])

bpy.ops.mesh.primitive_cube_add(size=1)
slab = bpy.context.active_object
slab.name = "slab"
slab.scale = (L + 2 * PAD, WD + 2 * PAD, HT + PAD)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
slab.parent = pk.ROOT
slab.location = (0, 0, (HT + PAD) / 2)
slab.data.materials.append(timber)
bv = slab.modifiers.new("eased", "BEVEL")
bv.width, bv.segments = 0.002, 2

# ------------------------------------------------------------------ the cutting front: a box whose -X face is rough
NY, NZ = 150, 40
ys = np.linspace(-WD / 2 - 0.08, WD / 2 + 0.08, NY)
zs = np.linspace(-0.04, HT + 0.08, NZ)
YY, ZZ = np.meshgrid(ys, zs, indexing="ij")
waves = []
for lam, amp, k in ((0.34, 0.050, 4), (0.09, 0.016, 5), (0.026, 0.005, 6)):
    for _ in range(k):
        ang = rng.uniform(0, 2 * math.pi)
        waves.append((2 * math.pi / lam * math.cos(ang), 2 * math.pi / lam * math.sin(ang), rng.uniform(0, 6.3),
                      amp / math.sqrt(k), rng.uniform(-2.0, 2.0)))


def rough(y, z, t):
    return sum(a * np.sin(ky * y + kz * z + ph + sp * t) for ky, kz, ph, a, sp in waves)


def front_x(t):
    return 0.69 - 1.40 * t                          # from past the right end (+X) to past the left end


bm = bmesh.new()
F = [[bm.verts.new((0, y, z)) for z in zs] for y in ys]
B = [[bm.verts.new((1.2, y, z)) for z in zs] for y in ys]
for i in range(NY - 1):
    for j in range(NZ - 1):
        bm.faces.new((F[i][j], F[i + 1][j], F[i + 1][j + 1], F[i][j + 1]))
        bm.faces.new((B[i][j], B[i][j + 1], B[i + 1][j + 1], B[i + 1][j]))
for i in range(NY - 1):
    for j in (0, NZ - 1):
        bm.faces.new((F[i][j], B[i][j], B[i + 1][j], F[i + 1][j]))
for j in range(NZ - 1):
    for i in (0, NY - 1):
        bm.faces.new((F[i][j], F[i][j + 1], B[i][j + 1], B[i][j]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.verts.index_update()
front_idx = np.array([[F[i][j].index for j in range(NZ)] for i in range(NY)]).ravel()
cutter_me = bpy.data.meshes.new("front")
bm.to_mesh(cutter_me)
bm.free()
cutter = bpy.data.objects.new("front", cutter_me)
scene.collection.objects.link(cutter)
cutter.parent = pk.ROOT
cutter.hide_render = True
co = np.zeros(len(cutter_me.vertices) * 3, np.float32)
cutter_me.vertices.foreach_get("co", co)
co = co.reshape(-1, 3)
bo = slab.modifiers.new("carve", "BOOLEAN")
bo.operation, bo.solver, bo.object = "DIFFERENCE", "EXACT", cutter


def set_front(t):
    xs = front_x(t) + rough(YY, ZZ, t)
    co[front_idx, 0] = xs.ravel()
    cutter_me.vertices.foreach_set("co", co.ravel())
    cutter_me.update()


# ------------------------------------------------------------------ sawdust, born on the front as it passes
def births(n, near_face=False):
    tb = rng.uniform(0, 1, n)
    y = rng.uniform(-WD / 2, WD / 2, n)
    z = rng.uniform(0.002, HT, n)
    if near_face:                                    # grains that fall to the floor leave from the long faces
        side = np.where(rng.uniform(0, 1, n) < 0.7, -1.0, 1.0)
        y = side * rng.uniform(WD / 2 - 0.03, WD / 2, n)
    x = front_x(tb) + rough(y, z, tb)
    keep = np.abs(x) < L / 2
    return tb[keep], np.stack([x, y, z], 1)[keep]


tb_air, p_air = births(220000)
na = len(tb_air)
d = np.array([0.45, 0.55, 1.0]) + rng.normal(0, 0.45, (na, 3))     # up and away from the camera
d /= np.linalg.norm(d, axis=1, keepdims=True)
v_air = d * rng.lognormal(math.log(1.1), 0.5, (na, 1))
r_air = np.clip(rng.lognormal(math.log(0.0009), 0.5, na), 0.0002, 0.003)
life = rng.uniform(0.45, 1.5, na)
TAU = 0.5                                            # air drag: grains slow down within half a second

tb_flr, p_flr = births(9000, near_face=True)
nf = len(tb_flr)
side = np.sign(p_flr[:, 1])
v_flr = np.stack([rng.normal(0.25, 0.2, nf), side * rng.uniform(0.15, 0.6, nf), rng.uniform(0.0, 0.5, nf)], 1)
r_flr = np.clip(rng.lognormal(math.log(0.0008), 0.4, nf), 0.0003, 0.0022)

air = C.grains("dust", np.zeros((1, 3)), [0.0], "#E6CFA8")
air.parent = pk.ROOT
flr = C.grains("fallen", np.zeros((1, 3)), [0.0], "#E2C9A0")
flr.parent = pk.ROOT


def dust(t):
    a = (t - tb_air) * SWEEP_S
    alive = (a > 0) & (a < life)
    aa = a[alive][:, None]
    pos = p_air[alive] + v_air[alive] * TAU * (1 - np.exp(-aa / TAU))
    pos[:, 2] -= 0.25 * aa[:, 0] ** 2                # drifts down a little
    r = r_air[alive] * (1 - aa[:, 0] / life[alive]) ** 0.6
    ok = pos[:, 2] > r
    C.set_grains(air, pos[ok], r[ok])
    # the heavier grains: thrown off the long faces, they land on the floor and stay
    a = (t - tb_flr) * SWEEP_S
    born = a > 0
    a = a[born]
    p0, v0, rr = p_flr[born], v_flr[born], r_flr[born]
    g = 9.81
    t_land = (v0[:, 2] + np.sqrt(v0[:, 2] ** 2 + 2 * g * (p0[:, 2] - rr))) / g
    tt = np.minimum(a, t_land)[:, None]
    pos = p0 + v0 * tt
    pos[:, 2] = p0[:, 2] + v0[:, 2] * tt[:, 0] - 0.5 * g * tt[:, 0] ** 2
    pos[:, 2] = np.maximum(pos[:, 2], rr)
    outside = (np.abs(pos[:, 1]) > WD / 2 + rr) | (pos[:, 2] > HT) | (np.abs(pos[:, 0]) > L / 2)
    C.set_grains(flr, pos[outside], rr[outside])


# a thin haze of fine dust along the front, rising behind it
bpy.ops.mesh.primitive_cube_add(size=1)
haze = bpy.context.active_object
haze.name = "haze"
haze.scale = (L + 0.6, WD + 0.6, 0.9)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
haze.parent = pk.ROOT
haze.location = (0, 0.1, 0.45)
hm = bpy.data.materials.new("haze")
hm.use_nodes = True
hn, hl = hm.node_tree.nodes, hm.node_tree.links
hn.remove(hn["Principled BSDF"])
vol = hn.new("ShaderNodeVolumePrincipled")
vol.inputs["Color"].default_value = (*C.srgb("#E9D9BF"), 1)
vol.inputs["Anisotropy"].default_value = 0.5
hl.new(vol.outputs[0], hn["Material Output"].inputs["Volume"])
htc = hn.new("ShaderNodeTexCoord")
sep = hn.new("ShaderNodeSeparateXYZ")
hl.new(htc.outputs["Object"], sep.inputs[0])
FRONT = hn.new("ShaderNodeValue")
dx = hn.new("ShaderNodeMath")                       # distance past the front, into the carved side
dx.operation = "SUBTRACT"
hl.new(sep.outputs["X"], dx.inputs[0])
hl.new(FRONT.outputs[0], dx.inputs[1])
band = hn.new("ShaderNodeMapRange")                 # densest just past the front, gone 35 cm on
band.interpolation_type = "SMOOTHSTEP"
band.inputs["From Min"].default_value, band.inputs["From Max"].default_value = 0.0, 0.35
band.inputs["To Min"].default_value, band.inputs["To Max"].default_value = 1.0, 0.0
hl.new(dx.outputs[0], band.inputs["Value"])
behind = hn.new("ShaderNodeMapRange")               # nothing on the uncut side
behind.inputs["From Min"].default_value, behind.inputs["From Max"].default_value = -0.06, 0.02
hl.new(dx.outputs[0], behind.inputs["Value"])
hz = hn.new("ShaderNodeMapRange")                   # the box's local z: -0.45 (floor) .. 0.45
hz.inputs["From Min"].default_value, hz.inputs["From Max"].default_value = -0.45, 0.4
hz.inputs["To Min"].default_value, hz.inputs["To Max"].default_value = 1.0, 0.0
hl.new(sep.outputs["Z"], hz.inputs["Value"])
nz = hn.new("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value = 9.0
nz.inputs["Detail"].default_value = 8.0
nz.inputs["Roughness"].default_value = 0.6
hl.new(htc.outputs["Object"], nz.inputs["Vector"])
clump = hn.new("ShaderNodeMapRange")
clump.inputs["From Min"].default_value, clump.inputs["From Max"].default_value = 0.42, 0.78
hl.new(nz.outputs["Fac"], clump.inputs["Value"])
dens = band.outputs[0]
for node in (behind, hz, clump):
    m = hn.new("ShaderNodeMath")
    m.operation = "MULTIPLY"
    hl.new(dens, m.inputs[0])
    hl.new(node.outputs[0], m.inputs[1])
    dens = m.outputs[0]
k = hn.new("ShaderNodeMath")
k.operation = "MULTIPLY"
k.inputs[1].default_value = 7.0
hl.new(dens, k.inputs[0])
hl.new(k.outputs[0], vol.inputs["Density"])
haze.data.materials.append(hm)

# ------------------------------------------------------------------ light and camera
sun = C.sun("sun", 5.2, color="#FFF1DE", angle_deg=1.5)
C.aim_sun(sun, elev_deg=36, azim_deg=28)
fill = C.area("fill", (-1.2, -2.6, 1.6), 4.0, 70, color="#F2F5FF", look=(0.55, 0.3, 0.1))
fill.visible_camera = False

cam = C.camera(lens=36)                  # the slab keeps to the right ~55%, clear of the headline on 16:10 screens too
cam.location = (1.30, -2.50, 0.66)
C.look_at(cam, (0.74, 0.30, 0.10))
cam.data.shift_x = -0.237
cam.data.shift_y = 0.02
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = (cam.location - PALLET).length
cam.data.dof.aperture_fstop = 4.0

for f in C.frame_list(COUNT):
    t = f / (COUNT - 1)
    set_front(t)
    dust(t)
    FRONT.outputs[0].default_value = front_x(t)
    C.render_to(os.path.join(C.args.out, f"{f:02d}.webp"))
