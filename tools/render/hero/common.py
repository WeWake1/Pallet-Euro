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
