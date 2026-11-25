"""PROTOTYPE round 10 (decisions #69-#75): the EPAL 1 and the eleven industry loads (loads.py).

  --job still --load KEY      one load on the EPAL 1 in the studio, for checking it: <KEY>.webp
  --job industries            A "The industries": the camera circles slowly; every few seconds the load lifts away and the
                              next lowers onto the deck and settles (frames 000..; industries.json says which load when)
  --job lift                  B "Lift": a forklift raises a loaded EPAL 1 to the second beam level of a stocked racking,
                              drives it in, sets it down and backs out; the camera rises with the load (lift/000..)
  --job delivery              C "The delivery": a forklift carrying each load, seen from the side by an orthographic camera,
                              on a transparent background with its shadow, four wheel-turn phases per load
                              (<load>-<k>.webp); the page drives it in and out. delivery.json maps metres to pixels.

  Blender -b --factory-startup --python tools/render/hero/r10.py -- --recipe epal1 \
      --recipes src/data/pallet-geometry.json --out public/dev/r10/industries --job industries [--frames 0-10] [--test]
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import loads as LD  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
JOB = arg("--job", "still")
pk = C.pk
scene = C.scene
HT = pk.R["dims"][2] * pk.MM

C.setup_cycles(view="AgX", look="AgX - Medium High Contrast", exposure=0.1)
scene.cycles.max_bounces = 10
scene.cycles.transmission_bounces = 8
C.seamless_studio(bg="#FFFFFF", floor="#F4F2EE", fade=(4.6, 9.5), fill="#EEF1F6", fill_strength=0.8, rough=0.7, bg_strength=3.0)
PALLET = Vector((0.0, 0.0, 0.0))
C.build_pallet(rot_deg=0, loc=PALLET)
AIM = (0.0, 0.0, 0.55)
for name, loc, size, power in (("top", (0.0, -0.3, 3.6), 4.0, 210), ("key", (-2.4, -2.6, 3.2), 3.5, 160),
                               ("fill", (2.8, -1.8, 1.9), 3.0, 45), ("rim", (1.2, 3.2, 2.6), 3.0, 90)):
    a = C.area(name, loc, size, power, look=AIM)
    a.visible_camera = False
sun = C.sun("sun", 4.5, color="#FFF3E4", angle_deg=2.0)
C.aim_sun(sun, elev_deg=50, azim_deg=30)

cam = C.camera(lens=50)
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 7.0


def orbit(az_deg, el_deg=17.0, dist=4.6, aim=Vector((0.0, 0.0, 0.5)), shift=-0.25):
    """The camera on a circle round the pallet; shift puts the pallet in the right half (the headline is left)."""
    az, el = math.radians(az_deg), math.radians(el_deg)
    cam.location = aim + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * dist
    C.look_at(cam, aim)
    cam.data.shift_x = shift
    cam.data.dof.focus_distance = dist


if JOB == "still":
    key = arg("--load", "fmcg")
    LD.build(key, pk.ROOT, HT)
    orbit(-32)
    C.render_to(os.path.join(C.args.out, f"{key}.webp"))
    sys.exit(0)

# ------------------------------------------------------------------ A "The industries"
ORDER = ["fmcg", "automotive", "pharma", "chemicals", "engineering", "food", "manufacturing", "logistics", "textiles",
         "exports", "building"]
SWAP, HOLD, FPS_SWAP, FPS_HOLD = 18, 16, 24, 8          # frames per segment and their playback speeds
SEG = SWAP + HOLD
SEG_S = SWAP / FPS_SWAP + HOLD / FPS_HOLD
TRAVEL = 3.0                                            # how far above the deck a load starts and leaves (out of frame)


def frame_time(f):
    k, i = divmod(f, SEG)
    return k * SEG_S + (i / FPS_SWAP if i < SWAP else SWAP / FPS_SWAP + (i - SWAP) / FPS_HOLD)


if JOB == "industries":
    holders = {k: LD.build(k, pk.ROOT, HT) for k in ORDER}
    total_s = len(ORDER) * SEG_S
    names = {k: n for k, n, _ in LD.INDUSTRIES}
    json.dump({"frames": len(ORDER) * SEG, "swap": SWAP, "hold": HOLD, "fpsSwap": FPS_SWAP, "fpsHold": FPS_HOLD,
               "segments": [{"key": k, "name": names[k]} for k in ORDER]},
              open(os.path.join(C.args.out, "industries.json"), "w"), indent=1)
    for f in C.frame_list(len(ORDER) * SEG):
        k, i = divmod(f, SEG)
        cur, prev = ORDER[k], ORDER[k - 1]
        for key, h in holders.items():
            show = key == cur or (key == prev and i <= 8)
            for ob in [h] + list(h.children_recursive):
                ob.hide_render = not show
        out = min(i / 8, 1.0)                           # the previous load rises away, faster and faster
        holders[prev].location.z = HT + TRAVEL * out ** 2.6
        inn = min(max((i - 7) / 10, 0.0), 1.0)          # the new one comes down and settles softly
        holders[cur].location.z = HT + TRAVEL * (1 - inn) ** 3
        t = frame_time(f) / total_s
        orbit(-30 + 24 * math.sin(math.tau * t), el_deg=16 + 2.5 * math.sin(math.tau * 2 * t))
        C.render_to(os.path.join(C.args.out, f"{f:03d}.webp"))


# ------------------------------------------------------------------ C "The delivery"
if JOB == "delivery":
    import warehouse as WH
    scene.render.film_transparent = True
    for ob in list(scene.objects):                       # a plain floor that only catches the shadow
        if ob.name.startswith("floor"):
            ob.data.materials.clear()
            ob.data.materials.append(C.mat("catcher", "#FFFFFF", rough=0.9))
            ob.is_shadow_catcher = True
    holders = {k: LD.build(k, pk.ROOT, HT) for k in ORDER}
    fl = WH.build_forklift()
    CARRY = 0.18                                         # forks this high while driving
    fl["carriage"].location.z = CARRY
    pk.ROOT.location = (fl["fork_x"] + 0.03 - 0.6, 0.0, CARRY + 0.045 - 0.100)   # forks under the cross boards
    cam.data.type = "ORTHO"
    cam.data.dof.use_dof = False
    cam.data.ortho_scale = 7.4
    yaw, pitch = math.radians(-24), math.radians(10)
    aim = Vector((0.35, 0.0, 0.95))
    d = Vector((math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch), math.sin(pitch)))
    cam.location = aim + d * 20
    C.look_at(cam, aim)
    cam.data.shift_x = 0.0
    bpy.context.view_layer.update()
    from bpy_extras.object_utils import world_to_camera_view
    p0 = world_to_camera_view(scene, cam, Vector((0, 0, 0)))
    p1 = world_to_camera_view(scene, cam, Vector((1, 0, 0)))
    W, H = C.W, C.H
    json.dump({"size": [W, H], "perMetre": [round((p1.x - p0.x) * W, 2), round(-(p1.y - p0.y) * H, 2)],
               "phases": 4, "wheelR": 0.33, "phaseDeg": 15, "order": ORDER,
               "segments": [{"key": k, "name": n} for k, n, _ in LD.INDUSTRIES if k in ORDER]},
              open(os.path.join(C.args.out, "delivery.json"), "w"), indent=1)
    base = {w: w.rotation_euler.copy() for w in fl["wheels"]}
    jobs = [(k, ph) for k in ORDER for ph in range(4)]
    for idx in C.frame_list(len(jobs)):
        key, ph = jobs[idx]
        for k2, h in holders.items():
            for ob in [h] + list(h.children_recursive):
                ob.hide_render = k2 != key
        for w in fl["wheels"]:
            r = 0.33 if w.location.x < 1.0 else 0.27
            w.rotation_euler = base[w].copy()
            w.rotation_euler.y += math.radians(ph * 15 * 0.33 / r) * (-1 if w.rotation_euler.z == 0 else 1)   # rolling forward
        C.render_to(os.path.join(C.args.out, f"{key}-{ph}.webp"), rgba=True)


# ------------------------------------------------------------------ B "Lift"
def clone_pallet(name):
    """Another EPAL 1 sharing the meshes of the one palletkit built."""
    e = bpy.data.objects.new(name, None)
    scene.collection.objects.link(e)
    for ob, _kind in pk.OBJECTS:
        c = ob.copy()
        scene.collection.objects.link(c)
        c.parent = e
        c.matrix_parent_inverse = ob.matrix_parent_inverse.copy()
    return e


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


if JOB == "lift":
    import random
    import warehouse as WH
    LIFT_N = 132
    Y0, BAY, LEVEL = 0.0, 2.7, 1.5                       # rack face at y = Y0; bays along x; beam levels every 1.5 m
    rack, tops = WH.build_rack(3, 3, bay_w=BAY, depth=1.1, beam_h=LEVEL, upright="#183E8C", beam="#C9CED6")
    rack.location = (-1.5 * BAY, Y0, 0)
    rng = random.Random(4)
    stock = [k for k in ORDER if k != "fmcg"]
    # each kind of loaded pallet is built once, into its own collection kept out of the scene, and placed in the rack
    # as collection instances (thousands of objects copied one by one would slow Blender to a crawl)
    kinds = {}
    for key in stock:
        coll = bpy.data.collections.new(f"stock_{key}")
        pal = clone_pallet(f"stock_pallet_{key}")
        LD.build(key, pal, HT, seed=1)
        for ob in [pal] + list(pal.children_recursive):
            for c in list(ob.users_collection):
                c.objects.unlink(ob)
            coll.objects.link(ob)
        kinds[key] = coll
    n = 0
    for b in range(3):
        for lv, z in enumerate([0.0] + tops):
            for slot in range(3):
                x = (b - 1) * BAY + (slot - 1) * 0.9
                if (b, lv, slot) == (1, 2, 1) or rng.random() < 0.2:      # the target slot stays empty, and a few others
                    continue
                inst = bpy.data.objects.new(f"stock{n}", None)
                inst.instance_type = "COLLECTION"
                inst.instance_collection = kinds[stock[(n * 3 + b) % len(stock)]]
                scene.collection.objects.link(inst)
                inst.location = (x, Y0 + 0.55, z)
                inst.rotation_euler = (0, 0, math.radians(90))
                n += 1
    held = LD.build("fmcg", pk.ROOT, HT)
    fl = WH.build_forklift()
    fl["root"].rotation_euler = (0, 0, math.radians(-90))  # forks point +y, at the rack
    FX, Y_IN = 0.0, Y0 + 0.55 - 0.78
    Y_OUT = Y_IN - 1.45
    target = tops[1]
    base = {w: w.rotation_euler.copy() for w in fl["wheels"]}

    def state(f):
        """Fork height, truck position along y, and whether the pallet now rests on the beams."""
        lift = 0.16 + (target + 0.135 - 0.16) * ease((f - 10) / 60)
        y = Y_OUT + (Y_IN - Y_OUT) * ease((f - 72) / 24)
        lift -= 0.135 * ease((f - 96) / 10)
        y -= (Y_IN - Y_OUT) * ease((f - 108) / 22)
        return lift, y, f >= 96 + 4

    track = []
    for f in range(LIFT_N):
        lift, y, rest = state(f)
        pz = target if rest and lift + 0.045 - 0.1 < target else lift + 0.045 - 0.1
        py = (Y_IN + 0.78) if f >= 96 else y + 0.78
        track.append((lift, y, pz, py))
    # the camera follows the load: a smoothed target, low and close at first, rising with it, easing back at the end
    cam_t, prev = [], None
    for f, (lift, y, pz, py) in enumerate(track):
        t = Vector((FX + 0.2, py - 0.95, 0.85 * pz + 0.95))         # between the load and the truck, a little above
        prev = t if prev is None else prev + (t - prev) * 0.16
        cam_t.append(prev.copy())
    for f in C.frame_list(LIFT_N):
        lift, y, pz, py = track[f]
        fl["lift"](lift)
        fl["root"].location = (FX, y, 0)
        d = y - Y_OUT
        for w in fl["wheels"]:
            r = 0.33 if w.location.x < 1.0 else 0.27
            w.rotation_euler = base[w].copy()
            w.rotation_euler.y += (-1 if base[w].z == 0 else 1) * d / r
        pk.ROOT.location = (FX, py, pz)
        pk.ROOT.rotation_euler = (0, 0, math.radians(90))
        aim = cam_t[f]
        back = ease((f - 100) / 32)
        off = Vector((5.4, -4.9, 0.7)) * (1 + 0.12 * back)
        cam.location = aim + off
        C.look_at(cam, aim + Vector((0, 0.3 * back, 0)))
        cam.data.lens = 38
        cam.data.shift_x = -0.24
        cam.data.dof.focus_distance = off.length
        C.render_to(os.path.join(C.args.out, f"{f:03d}.webp"))

