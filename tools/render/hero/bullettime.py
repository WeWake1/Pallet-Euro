"""PROTOTYPE round 6 · C "Bullet time": one frozen instant. A dropped EPAL 1 meets the studio floor on one corner,
tilted hard; a puff of sawdust bursts from that corner and fine grains spray across the floor, all frozen in
the air. The camera orbits the frozen moment (cursor on computers, by itself on phones). Nothing is simulated:
the grains and the puff are placed by formula, so every frame shows the same instant from a new angle.

  Blender -b --factory-startup --python tools/render/hero/bullettime.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/r6/bullettime [--frames 0-60] [--test]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

COUNT = 61
scene = C.scene
pk = C.pk
C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.25)
C.seamless_studio(bg="#F0EDE8", floor="#EAE6E0", fade=(3.2, 8.0), fill="#EEF0F5", fill_strength=0.6, rough=0.75,
                  bg_strength=3.4)               # as bright as the lit floor: no horizon from a low camera
rng = np.random.default_rng(7)

# ------------------------------------------------------------------ the pallet, tilted onto its front-left corner
C.build_pallet(rot_deg=0, loc=(0, 0, 0))
pk.ROOT.rotation_euler = (math.radians(15), math.radians(-11), math.radians(-28))
bpy.context.view_layer.update()
low, contact = 9.0, None
for ob, _kind in pk.OBJECTS:
    if ob.type != "MESH":
        continue
    for v in ob.data.vertices:
        w = ob.matrix_world @ v.co
        if w.z < low:
            low, contact = w.z, w.copy()
pk.ROOT.location.z -= low                                 # the lowest corner just touches the floor
contact.z = 0.0
bpy.context.view_layer.update()
centre = sum((ob.matrix_world.translation for ob, _ in pk.OBJECTS), Vector()) / len(pk.OBJECTS)


# ------------------------------------------------------------------ frozen sawdust: instanced grains
def grains(name, pts, radii, colour):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in pts], [], [])
    at = me.attributes.new("grain_r", "FLOAT", "POINT")   # not "radius": Mesh to Points makes its own (5 cm)
    at.data.foreach_set("value", np.asarray(radii, np.float32))
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    mat = bpy.data.materials.new(name + "_mat")
    mat.use_nodes = True
    pb = mat.node_tree.nodes["Principled BSDF"]
    pb.inputs["Base Color"].default_value = (*C.srgb(colour), 1)
    pb.inputs["Roughness"].default_value = 0.9
    pb.inputs["Subsurface Weight"].default_value = 0.25
    pb.inputs["Subsurface Radius"].default_value = (0.004, 0.003, 0.002)
    ng = bpy.data.node_groups.new(name + "_gn", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    m2p = N.new("GeometryNodeMeshToPoints")
    ico = N.new("GeometryNodeMeshIcoSphere")
    ico.inputs["Radius"].default_value = 1.0
    ico.inputs["Subdivisions"].default_value = 1
    iop = N.new("GeometryNodeInstanceOnPoints")
    na = N.new("GeometryNodeInputNamedAttribute")
    na.data_type = "FLOAT"
    na.inputs["Name"].default_value = "grain_r"
    sm = N.new("GeometryNodeSetMaterial")
    sm.inputs["Material"].default_value = mat
    L.new(gi.outputs[0], m2p.inputs["Mesh"])
    L.new(m2p.outputs["Points"], iop.inputs["Points"])
    L.new(ico.outputs["Mesh"], iop.inputs["Instance"])
    L.new(na.outputs["Attribute"], iop.inputs["Scale"])
    L.new(iop.outputs["Instances"], sm.inputs["Geometry"])
    L.new(sm.outputs["Geometry"], go.inputs[0])
    ob.modifiers.new("gn", "NODES").node_group = ng
    return ob


# spray: out from the corner, mostly away from the pallet and low over the floor
away = Vector((contact.x - centre.x, contact.y - centre.y, 0)).normalized()
base_ang = math.atan2(away.y, away.x)
K = 22000
ang = base_ang + rng.normal(0, 0.8, K)
d = 0.01 + rng.exponential(0.30, K)
elev = np.radians(rng.uniform(2, 34, K)) * np.exp(-d / 0.5)
pts = np.column_stack([contact.x + np.cos(ang) * d, contact.y + np.sin(ang) * d, 0.002 + d * np.tan(elev)])
grains("spray", pts, rng.uniform(0.0008, 0.0024, K), "#C7A97F")
K2 = 260
ang2 = base_ang + rng.normal(0, 0.9, K2)
d2 = 0.04 + rng.exponential(0.32, K2)
grains("chips", np.column_stack([contact.x + np.cos(ang2) * d2, contact.y + np.sin(ang2) * d2,
                                 0.004 + d2 * np.tan(np.radians(rng.uniform(4, 22, K2)))]),
       rng.uniform(0.0022, 0.0045, K2), "#C29F70")


# ------------------------------------------------------------------ the puff at the corner (volume)
def puff():
    bpy.ops.mesh.primitive_cube_add(size=1, location=(contact.x, contact.y, 0.25))
    ob = bpy.context.active_object
    ob.scale = (1.3, 1.3, 0.5)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    m = bpy.data.materials.new("puff")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.remove(n["Principled BSDF"])
    vol = n.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*C.srgb("#DCC9A9"), 1)
    vol.inputs["Anisotropy"].default_value = 0.45
    l.new(vol.outputs[0], n["Material Output"].inputs["Volume"])
    tc = n.new("ShaderNodeTexCoord")
    # distance from the corner, squashed so the cloud spreads along the floor and leans away from the pallet
    sub = n.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = (contact.x + away.x * 0.12, contact.y + away.y * 0.12, -0.02)
    l.new(tc.outputs["Object"], sub.inputs[0])
    sc = n.new("ShaderNodeVectorMath")
    sc.operation = "MULTIPLY"
    sc.inputs[1].default_value = (1.0, 1.0, 1.7)
    l.new(sub.outputs[0], sc.inputs[0])
    ln = n.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    l.new(sc.outputs[0], ln.inputs[0])
    fall = n.new("ShaderNodeMapRange")
    fall.inputs["From Min"].default_value, fall.inputs["From Max"].default_value = 0.03, 0.34
    fall.inputs["To Min"].default_value, fall.inputs["To Max"].default_value = 1.0, 0.0
    l.new(ln.outputs["Value"], fall.inputs["Value"])
    nz = n.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 7.0
    nz.inputs["Detail"].default_value = 9.0
    nz.inputs["Roughness"].default_value = 0.62
    l.new(tc.outputs["Object"], nz.inputs["Vector"])
    clump = n.new("ShaderNodeMapRange")
    clump.inputs["From Min"].default_value, clump.inputs["From Max"].default_value = 0.45, 0.75
    l.new(nz.outputs["Fac"], clump.inputs["Value"])
    mm = n.new("ShaderNodeMath")
    mm.operation = "MULTIPLY"
    l.new(fall.outputs[0], mm.inputs[0])
    l.new(clump.outputs[0], mm.inputs[1])
    dens = n.new("ShaderNodeMath")
    dens.operation = "MULTIPLY"
    dens.inputs[1].default_value = 16.0
    l.new(mm.outputs[0], dens.inputs[0])
    l.new(dens.outputs[0], vol.inputs["Density"])
    ob.data.materials.append(m)


puff()

# ------------------------------------------------------------------ light: soft key, back rims that make the dust glow
for lamp in (C.area("key", (-2.3, -2.4, 3.0), 2.6, 480, color="#FFF5EA", look=tuple(centre)),
             C.area("rim_r", (2.4, 2.4, 1.0), 1.6, 650, color="#FFF1DE", look=tuple(contact)),
             C.area("rim_l", (-2.6, 2.2, 0.9), 1.6, 450, color="#EEF2FF", look=tuple(contact))):
    lamp.visible_camera = False                      # the orbit looks toward the rims: keep the lamps out of shot
sun = C.sun("sun", 2.8, color="#FFF3E2", angle_deg=1.5)
C.aim_sun(sun, elev_deg=62, azim_deg=50)

# ------------------------------------------------------------------ camera: a low arc around the frozen instant
cam = C.camera(lens=38)
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 5.6
TARGET = Vector((centre.x, centre.y, 0.26))
R, HGT = 3.0, 0.42
for f in C.frame_list(COUNT):
    t = f / (COUNT - 1)
    a = math.radians(-40 + 80 * t)                   # from the front left to the front right
    cam.location = TARGET + Vector((R * math.sin(a), -R * math.cos(a), HGT - TARGET.z))
    C.look_at(cam, TARGET)
    cam.data.shift_x = -0.19
    cam.data.dof.focus_distance = R
    C.render_to(os.path.join(C.args.out, f"{f:02d}.webp"))
