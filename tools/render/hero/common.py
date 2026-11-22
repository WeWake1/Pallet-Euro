"""Shared setup for the PROTOTYPE hero scenes (round 4). Run inside Blender; see the scene scripts.

Imports palletkit (exact pallet geometry + approved wood look), then gives the scene scripts:
Cycles on the Metal GPU, a camera helper, simple materials, and a frame loop that writes WebP files.
Flags (after `--`): --recipe epal1 --recipes src/data/pallet-geometry.json --out DIR
                    [--size 1920x1080] [--samples 128] [--frames 0-47|0,12] [--quality 80] [--test]
"""
import argparse
import math
import os
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
args, _ = ap.parse_known_args(argv)

scene = pk.scene
W, H = (int(v) for v in args.size.split("x"))
os.makedirs(args.out, exist_ok=True)


def setup_cycles(view="AgX", look="", exposure=0.0, transparent=False):
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.refresh_devices()
    for d in prefs.devices:
        d.use = d.type == "METAL"  # GPU only; adding the CPU slows Metal down
    cy = scene.cycles
    cy.device = "GPU"
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
