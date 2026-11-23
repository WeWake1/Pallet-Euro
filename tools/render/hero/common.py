"""Shared setup for the PROTOTYPE hero scenes and scroll films (rounds 4-5). Run inside Blender; see the
scene scripts, or use tools/render/run.py, which knows every scene's settings.

Imports palletkit (exact pallet geometry + approved wood look), then gives the scene scripts:
Cycles on the GPU (Metal on a Mac; OptiX/HIP/CUDA/oneAPI elsewhere, e.g. HIP on an AMD Radeon), a camera
helper, simple materials, and a frame loop that writes WebP files.
Flags (after `--`): --recipe epal1 --recipes src/data/pallet-geometry.json --out DIR
                    [--size 1920x1080] [--samples 128] [--frames 0-47|0,12] [--quality 80] [--test]
                    [--device auto|METAL|HIP|OPTIX|CUDA|ONEAPI|CPU]   (or env PE_RENDER_DEVICE)
"""
import argparse
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import palletkit as pk  # noqa: E402  (resets the scene and builds the materials on import)
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--size", default="1920x1080")
ap.add_argument("--samples", type=int, default=128)
ap.add_argument("--frames", default="", help="frames to render, e.g. 0-47 or 0,24,47 (default: all)")
ap.add_argument("--quality", type=int, default=82)
ap.add_argument("--test", action="store_true", help="quarter size, few samples")
ap.add_argument("--device", default=os.environ.get("PE_RENDER_DEVICE", "auto"),
                help="Cycles device: auto (Metal on a Mac, else OptiX, HIP, CUDA, oneAPI), one of those, or CPU")
args, _ = ap.parse_known_args(argv)
# Blender on Windows resolves a relative output path from the drive root (C:\), not the working folder.
args.out = os.path.abspath(args.out)

scene = pk.scene
W, H = (int(v) for v in args.size.split("x"))
os.makedirs(args.out, exist_ok=True)


GPU_ORDER = ["METAL"] if sys.platform == "darwin" else ["OPTIX", "HIP", "CUDA", "ONEAPI"]


def is_integrated(name):
    """The GPU built into the CPU, e.g. "AMD Radeon(TM) Graphics" next to the RX 9060 XT on the owner's PC."""
    return re.search(r"Radeon(\(TM\))?( \w+)* Graphics$|Intel\(R\) (UHD|Iris|HD) ", name) is not None


def pick_device():
    """First GPU backend that has a device. On the owner's Windows PC (Radeon RX 9060 XT) that is HIP."""
    prefs = bpy.context.preferences.addons["cycles"].preferences
    wanted = GPU_ORDER if args.device.lower() == "auto" else [args.device.upper()]
    for kind in wanted:
        if kind == "CPU":
            break
        try:
            prefs.compute_device_type = kind
        except TypeError:          # this Blender build has no such backend
            continue
        prefs.refresh_devices()
        gpus = [d for d in prefs.devices if d.type == kind]
        if gpus:
            gpus = [d for d in gpus if not is_integrated(d.name)] or gpus
            ids = {d.id for d in gpus}
            for d in prefs.devices:
                d.use = d.id in ids        # dedicated GPU only: the CPU or the CPU's own GPU slows the render down
            print(f"DEVICE {kind}: " + ", ".join(d.name for d in gpus), flush=True)
            return "GPU"
    print("WARNING no GPU found for Cycles; rendering on the CPU (much slower)", flush=True)
    return "CPU"


def setup_cycles(view="AgX", look="", exposure=0.0, transparent=False):
    scene.render.engine = "CYCLES"
    cy = scene.cycles
    cy.device = pick_device()
    cy.samples = 24 if args.test else args.samples
    cy.use_denoising = True
    cy.max_bounces = 8
    cy.transparent_max_bounces = 24
    scene.render.film_transparent = transparent
    try:
        scene.view_settings.view_transform = view
    except TypeError:
        scene.view_settings.view_transform = "Standard"
    if look:
        try:
            scene.view_settings.look = look
        except TypeError:
            print("WARNING look not available:", look)
    scene.view_settings.exposure = exposure
    scene.render.resolution_x, scene.render.resolution_y = W, H
    scene.render.resolution_percentage = 50 if args.test else 100


def camera(lens=50.0, sensor=36.0):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.sensor_width = sensor
    cam = bpy.data.objects.new("cam", cd)
    scene.collection.objects.link(cam)
    scene.camera = cam
    return cam


def look_at(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat("-Z", "Y").to_euler()


def srgb(hexstr):
    return pk.srgb(hexstr)


def mat(name, hexcol, rough=0.5, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*srgb(hexcol), 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    return m


def plane(name, size_x, size_y, loc=(0, 0, 0), rot=(0, 0, 0), material=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (size_x, size_y, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material:
        ob.data.materials.append(material)
    return ob


def sun(name, strength, color="#FFFFFF", angle_deg=0.53):
    ld = bpy.data.lights.new(name, "SUN")
    ld.energy = strength
    ld.color = srgb(color)
    ld.angle = math.radians(angle_deg)
    ob = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(ob)
    return ob


def aim_sun(ob, elev_deg, azim_deg):
    """Point a sun lamp. azim 0 = sun at -X (left of a camera on -Y), 90 = sun at -Y (behind the camera)."""
    el, az = math.radians(elev_deg), math.radians(azim_deg)
    to_sun = Vector((-math.cos(el) * math.cos(az), -math.cos(el) * math.sin(az), math.sin(el)))
    ob.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()


def area(name, loc, size, power, color="#FFFFFF", look=(0, 0, 0.1)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.size = size
    ld.energy = power
    ld.color = srgb(color)
    ob = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(ob)
    ob.location = loc
    look_at(ob, look)
    return ob


def world(hexcol, strength):
    w = bpy.data.worlds.new("world")
    scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*srgb(hexcol), 1)
    bg.inputs["Strength"].default_value = strength
    return w


def frame_list(count):
    if not args.frames:
        return list(range(count))
    out = []
    for part in args.frames.split(","):
        if "-" in part:
            a, b = (int(v) for v in part.split("-"))
            out += range(a, b + 1)
        elif part:
            out.append(int(part))
    return [f for f in out if 0 <= f < count]


def render_to(path, rgba=False):
    s = scene.render.image_settings
    s.file_format = "WEBP"
    s.color_mode = "RGBA" if rgba else "RGB"
    s.quality = args.quality
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("WROTE", path, flush=True)


def build_pallet(rot_deg=0.0, loc=(0, 0, 0)):
    pk.build_recipe(pk.R)
    pk.ROOT.rotation_euler = (0, 0, math.radians(rot_deg))
    pk.ROOT.location = loc
    return pk.ROOT


# ------------------------------------------------------------------ shared by the round-6 scenes
def shadow_only(ob):
    """Seen by nothing but the shadows it casts (gobos, light blockers)."""
    for attr in ("visible_camera", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
        setattr(ob, attr, False)
    ob.visible_shadow = True


def seamless_studio(bg="#F2F1EE", floor="#EEECE8", fade=(4.0, 12.0), fill="#F3F2EF", fill_strength=0.5, rough=0.6,
                    bg_strength=1.0):
    """Studio without a horizon: the floor takes light and shadow near the camera and fades into the flat backdrop
    colour with camera distance; the world lights the scene softly but shows the camera only the backdrop."""
    m = bpy.data.materials.new("studio_floor")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.3
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Detail"].default_value = 6.0
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*srgb(floor), 1)
    ramp.color_ramp.elements[1].color = (*[min(1.0, c * 1.02) for c in srgb(floor)], 1)
    l.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    l.new(ramp.outputs["Color"], b.inputs["Base Color"])
    cd = n.new("ShaderNodeCameraData")
    mr = n.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHSTEP"
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = fade
    l.new(cd.outputs["View Distance"], mr.inputs["Value"])
    far = n.new("ShaderNodeEmission")
    far.inputs["Color"].default_value = (*srgb(bg), 1)
    far.inputs["Strength"].default_value = bg_strength
    mix = n.new("ShaderNodeMixShader")
    l.new(mr.outputs[0], mix.inputs["Fac"])
    l.new(b.outputs["BSDF"], mix.inputs[1])
    l.new(far.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], n["Material Output"].inputs["Surface"])
    plane("floor", 80, 80, material=m)
    w = world(fill, fill_strength)
    wn, wl = w.node_tree.nodes, w.node_tree.links
    flat = wn.new("ShaderNodeBackground")
    flat.inputs["Color"].default_value = (*srgb(bg), 1)
    flat.inputs["Strength"].default_value = bg_strength
    lp = wn.new("ShaderNodeLightPath")
    wm = wn.new("ShaderNodeMixShader")
    wl.new(lp.outputs["Is Camera Ray"], wm.inputs["Fac"])
    wl.new(wn["Background"].outputs[0], wm.inputs[1])
    wl.new(flat.outputs[0], wm.inputs[2])
    wl.new(wm.outputs[0], wn["World Output"].inputs["Surface"])
    return m


def stone_floor(c1="#EDE7DD", c2="#E3DCCF", joint="#CBC2B3", slab=(1.2, 0.6)):
    """Honed stone slabs in running bond with fine joints (the round-4 jaali room's floor)."""
    m = bpy.data.materials.new("stone_floor")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.36
    b.inputs["Specular IOR Level"].default_value = 0.4
    tc = n.new("ShaderNodeTexCoord")
    br = n.new("ShaderNodeTexBrick")
    br.offset, br.offset_frequency = 0.5, 1
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = slab[0]
    br.inputs["Row Height"].default_value = slab[1]
    br.inputs["Mortar Size"].default_value = 0.0025
    br.inputs["Mortar Smooth"].default_value = 0.4
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Color1"].default_value = (*srgb(c1), 1)
    br.inputs["Color2"].default_value = (*srgb(c2), 1)
    br.inputs["Mortar"].default_value = (*srgb(joint), 1)
    l.new(tc.outputs["Object"], br.inputs["Vector"])
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Detail"].default_value = 8.0
    l.new(tc.outputs["Object"], noise.inputs["Vector"])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.95, 0.95, 0.94, 1)
    ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1)
    l.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    mul = n.new("ShaderNodeVectorMath")
    mul.operation = "MULTIPLY"
    l.new(br.outputs["Color"], mul.inputs[0])
    l.new(ramp.outputs["Color"], mul.inputs[1])
    l.new(mul.outputs["Vector"], b.inputs["Base Color"])
    bump = n.new("ShaderNodeBump")
    bump.invert = True
    bump.inputs["Strength"].default_value = 0.5
    bump.inputs["Distance"].default_value = 0.001
    l.new(br.outputs["Fac"], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def plaster(c1="#EAE4DA", c2="#F3EFE8"):
    """Lime plaster: matte, a soft cloudy tone and a fine trowelled texture."""
    m = bpy.data.materials.new("plaster")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    b = n["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.92
    b.inputs["Specular IOR Level"].default_value = 0.2
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2.2
    noise.inputs["Detail"].default_value = 4.0
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*srgb(c1), 1)
    ramp.color_ramp.elements[1].color = (*srgb(c2), 1)
    l.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    l.new(ramp.outputs["Color"], b.inputs["Base Color"])
    fine = n.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = 160.0
    fine.inputs["Detail"].default_value = 8.0
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    l.new(fine.outputs["Fac"], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def save_mask(name, arr):
    """Save a 2-D float array (1 = opaque) as a PNG next to the scenes and load it back (Cycles reads generated
    images reliably only from a file)."""
    h, w = arr.shape
    img = bpy.data.images.new(name, w, h, alpha=False)
    a = arr.astype("float32")
    import numpy as np
    img.pixels.foreach_set(np.stack([a, a, a, np.ones_like(a)], -1).ravel())
    path = os.path.join(HERE, f"_{name}.png")
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = "Non-Color"
    return img


def gobo_material(img, size_x, size_y, tile=None, offset=(0.0, 0.0)):
    """Transparent where the mask is 0, an opaque grey card where it is 1 (only its shadow matters)."""
    m = bpy.data.materials.new("gobo_" + img.name)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    mix = n.new("ShaderNodeMixShader")
    tr = n.new("ShaderNodeBsdfTransparent")
    df = n.new("ShaderNodeBsdfDiffuse")
    tc = n.new("ShaderNodeTexCoord")
    mp = n.new("ShaderNodeMapping")
    t = tile or max(size_x, size_y)
    mp.inputs["Scale"].default_value = (size_x / t, size_y / t, 1)
    mp.inputs["Location"].default_value = (offset[0], offset[1], 0)
    tex = n.new("ShaderNodeTexImage")
    tex.image = img
    tex.extension = "REPEAT"
    l.new(tc.outputs["UV"], mp.inputs["Vector"])
    l.new(mp.outputs["Vector"], tex.inputs["Vector"])
    l.new(tex.outputs["Color"], mix.inputs["Fac"])
    l.new(tr.outputs[0], mix.inputs[1])
    l.new(df.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], out.inputs["Surface"])
    return m


# ------------------------------------------------------------------ round 7
def grains(name, pts, radii, colour, sss=0.25):
    """Sawdust: one small ico sphere instanced on every point, scaled by its radius (in metres). Geometry Nodes
    instancing keeps tens of thousands of grains cheap. The radius attribute is "grain_r": Mesh to Points makes its
    own "radius" (5 cm). Update the points with set_grains()."""
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    set_grains(ob, pts, radii)
    m = bpy.data.materials.new(name + "_mat")
    m.use_nodes = True
    pb = m.node_tree.nodes["Principled BSDF"]
    pb.inputs["Base Color"].default_value = (*srgb(colour), 1)
    pb.inputs["Roughness"].default_value = 0.9
    pb.inputs["Subsurface Weight"].default_value = sss
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
    rot = N.new("FunctionNodeRandomValue")          # tumble each grain so the ico facets do not line up
    rot.data_type = "FLOAT_VECTOR"
    rot.inputs["Max"].default_value = (6.3, 6.3, 6.3)
    sm = N.new("GeometryNodeSetMaterial")
    sm.inputs["Material"].default_value = m
    L.new(gi.outputs[0], m2p.inputs["Mesh"])
    L.new(m2p.outputs["Points"], iop.inputs["Points"])
    L.new(ico.outputs["Mesh"], iop.inputs["Instance"])
    L.new(na.outputs["Attribute"], iop.inputs["Scale"])
    L.new(rot.outputs["Value"], iop.inputs["Rotation"])
    L.new(iop.outputs["Instances"], sm.inputs["Geometry"])
    L.new(sm.outputs["Geometry"], go.inputs[0])
    ob.modifiers.new("gn", "NODES").node_group = ng
    return ob


def set_grains(ob, pts, radii):
    import numpy as np
    me = ob.data
    me.clear_geometry()
    pts = np.asarray(pts, np.float32).reshape(-1, 3)
    me.vertices.add(len(pts))
    me.vertices.foreach_set("co", pts.ravel())
    at = me.attributes.get("grain_r") or me.attributes.new("grain_r", "FLOAT", "POINT")
    at.data.foreach_set("value", np.asarray(radii, np.float32))
    me.update()
