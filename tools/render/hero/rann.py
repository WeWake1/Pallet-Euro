"""PROTOTYPE round 4 · "Rann": one EPAL 1 alone on a white salt desert (after the Great Rann of Kutch),
physical sky, low morning sun. The camera sways slowly around the pallet; the frames form one
seamless loop (sine), so the page can play them forever.

  Blender -b --factory-startup --python tools/render/hero/rann.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/r4/rann [--frames 0-71] [--test]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

COUNT = 72
SUN_EL, SUN_AZ = 23.0, 34.0          # sun at the left, a little behind the camera: long shadows to the right
C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=-0.05)
vs = C.scene.view_settings
if hasattr(vs, "use_white_balance"):   # warm morning balance, so the salt is not sky-blue
    vs.use_white_balance = True
    vs.white_balance_temperature = 9600
    vs.white_balance_tint = 4
else:
    print("WARNING no white balance in this Blender")


# ------------------------------------------------------------------ sky + sun
def sky_world():
    w = bpy.data.worlds.new("sky")
    C.scene.world = w
    w.use_nodes = True
    n, l = w.node_tree.nodes, w.node_tree.links
    sky = n.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_disc = False
    el, az = math.radians(SUN_EL), math.radians(SUN_AZ)
    sky.sun_elevation = el
    sky.sun_rotation = math.atan2(-math.cos(az), -math.sin(az))   # Blender sky: 0 = +Y, 90 deg = +X
    sky.altitude = 2.0
    sky.air_density = 1.0
    sky.aerosol_density = 1.6       # a little dust: pale horizon, clear sky above
    sky.ozone_density = 1.0
    bg = n["Background"]
    bg.inputs["Strength"].default_value = 0.13
    l.new(sky.outputs["Color"], bg.inputs["Color"])
    return w


sky_world()
sun = C.sun("sun", 4.6, color="#FFE8CE", angle_deg=0.53)
C.aim_sun(sun, SUN_EL, SUN_AZ)


# ------------------------------------------------------------------ salt crust
def salt():
    m = bpy.data.materials.new("salt")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.82
    b.inputs["Specular IOR Level"].default_value = 0.3
    tc = n.new("ShaderNodeTexCoord")
    warp = n.new("ShaderNodeTexNoise")              # bends the polygon edges so they are not ruler-straight
    warp.inputs["Scale"].default_value = 1.4
    warp.inputs["Detail"].default_value = 3.0
    l.new(tc.outputs["Object"], warp.inputs["Vector"])
    wsc = n.new("ShaderNodeVectorMath")
    wsc.operation = "SCALE"
    wsc.inputs["Scale"].default_value = 0.22
    l.new(warp.outputs["Color"], wsc.inputs[0])
    wco = n.new("ShaderNodeVectorMath")
    wco.operation = "ADD"
    l.new(tc.outputs["Object"], wco.inputs[0])
    l.new(wsc.outputs["Vector"], wco.inputs[1])
    vor = n.new("ShaderNodeTexVoronoi")             # polygon crust, cells about a metre across
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 0.85
    vor.inputs["Randomness"].default_value = 1.0
    l.new(wco.outputs["Vector"], vor.inputs["Vector"])
    vor2 = n.new("ShaderNodeTexVoronoi")            # finer secondary cracks
    vor2.feature = "DISTANCE_TO_EDGE"
    vor2.inputs["Scale"].default_value = 3.1
    l.new(wco.outputs["Vector"], vor2.inputs["Vector"])
    r2 = n.new("ShaderNodeMapRange")
    r2.interpolation_type = "SMOOTHSTEP"
    r2.inputs["From Max"].default_value = 0.03
    r2.inputs["To Min"].default_value = 0.35
    r2.inputs["To Max"].default_value = 0.0
    l.new(vor2.outputs["Distance"], r2.inputs["Value"])
    ridge = n.new("ShaderNodeMapRange")             # raised ridges along the cell edges
    ridge.interpolation_type = "SMOOTHSTEP"
    ridge.inputs["From Min"].default_value = 0.0
    ridge.inputs["From Max"].default_value = 0.085
    ridge.inputs["To Min"].default_value = 1.0
    ridge.inputs["To Max"].default_value = 0.0
    l.new(vor.outputs["Distance"], ridge.inputs["Value"])
    grain = n.new("ShaderNodeTexNoise")             # crystalline roughness
    grain.inputs["Scale"].default_value = 90.0
    grain.inputs["Detail"].default_value = 10.0
    l.new(tc.outputs["Object"], grain.inputs["Vector"])
    hgt = n.new("ShaderNodeMath")
    hgt.operation = "MULTIPLY_ADD"
    l.new(grain.outputs["Fac"], hgt.inputs[0])
    hgt.inputs[1].default_value = 0.3
    rsum = n.new("ShaderNodeMath")
    rsum.operation = "ADD"
    l.new(ridge.outputs["Result"], rsum.inputs[0])
    l.new(r2.outputs["Result"], rsum.inputs[1])
    l.new(rsum.outputs["Value"], hgt.inputs[2])
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 1.0
    bump.inputs["Distance"].default_value = 0.022
    l.new(hgt.outputs["Value"], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], b.inputs["Normal"])
    # colour: ridges whitest, cell floors a touch greyer and patchy, far ground fades into the haze
    patch = n.new("ShaderNodeTexNoise")
    patch.inputs["Scale"].default_value = 0.22
    patch.inputs["Detail"].default_value = 5.0
    l.new(tc.outputs["Object"], patch.inputs["Vector"])
    pr = n.new("ShaderNodeValToRGB")
    pr.color_ramp.elements[0].position = 0.35
    pr.color_ramp.elements[0].color = (*C.srgb("#E6E0D6"), 1)
    pr.color_ramp.elements[1].position = 0.7
    pr.color_ramp.elements[1].color = (*C.srgb("#F1EDE6"), 1)
    l.new(patch.outputs["Fac"], pr.inputs["Fac"])
    lift = n.new("ShaderNodeMapRange")              # ridge -> 0..1 toward white
    lift.inputs["To Max"].default_value = 0.8
    l.new(ridge.outputs["Result"], lift.inputs["Value"])
    white = n.new("ShaderNodeValToRGB")
    white.color_ramp.elements[0].color = (0, 0, 0, 1)
    white.color_ramp.elements[1].color = (1, 1, 1, 1)
    l.new(lift.outputs["Result"], white.inputs["Fac"])
    top = n.new("ShaderNodeVectorMath")             # lerp(patch, #F7F6F3, ridge)
    top.operation = "SUBTRACT"
    top.inputs[0].default_value = C.srgb("#F8F6F1")
    l.new(pr.outputs["Color"], top.inputs[1])
    scl = n.new("ShaderNodeVectorMath")
    scl.operation = "MULTIPLY"
    l.new(top.outputs["Vector"], scl.inputs[0])
    l.new(white.outputs["Color"], scl.inputs[1])
    add = n.new("ShaderNodeVectorMath")
    add.operation = "ADD"
    l.new(scl.outputs["Vector"], add.inputs[0])
    l.new(pr.outputs["Color"], add.inputs[1])
    cam = n.new("ShaderNodeCameraData")             # aerial perspective: far salt takes the haze colour
    far = n.new("ShaderNodeMapRange")
    far.interpolation_type = "SMOOTHSTEP"
    far.inputs["From Min"].default_value = 25.0
    far.inputs["From Max"].default_value = 900.0
    far.inputs["To Max"].default_value = 0.85
    l.new(cam.outputs["View Distance"], far.inputs["Value"])
    hz = n.new("ShaderNodeVectorMath")
    hz.operation = "SUBTRACT"
    hz.inputs[0].default_value = C.srgb("#E6EAF0")
    l.new(add.outputs["Vector"], hz.inputs[1])
    hzs = n.new("ShaderNodeVectorMath")
    hzs.operation = "SCALE"
    l.new(hz.outputs["Vector"], hzs.inputs[0])
    l.new(far.outputs["Result"], hzs.inputs["Scale"])
    fin = n.new("ShaderNodeVectorMath")
    fin.operation = "ADD"
    l.new(hzs.outputs["Vector"], fin.inputs[0])
    l.new(add.outputs["Vector"], fin.inputs[1])
    l.new(fin.outputs["Vector"], b.inputs["Base Color"])
    return m


C.plane("salt", 20000, 20000, material=salt())

# ------------------------------------------------------------------ pallet + camera
C.build_pallet(rot_deg=22)
TARGET = Vector((0.0, 0.0, 0.08))
cam = C.camera(lens=50)
cam.data.shift_x = -0.17
cam.data.shift_y = 0.035          # horizon a little below the middle: more sky for the copy
cam.data.clip_end = 30000
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 5.6
DIST, HEIGHT, BASE_ANG = 5.0, 0.55, math.radians(-14)      # camera on -Y, a little to the left
SWAY = math.radians(3.0)

for f in C.frame_list(COUNT):
    a = BASE_ANG + SWAY * math.sin(2 * math.pi * f / COUNT)
    cam.location = TARGET + Vector((DIST * math.sin(a), -DIST * math.cos(a), HEIGHT - TARGET.z))
    look = Vector((TARGET.x, TARGET.y, HEIGHT))             # level camera: horizon through the centre
    C.look_at(cam, look)
    cam.data.dof.focus_distance = (cam.location - TARGET).length
    C.render_to(os.path.join(C.args.out, f"{f:02d}.webp"))
