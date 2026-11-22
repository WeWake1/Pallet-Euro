// PROTOTYPE · Direction B: a live 3D EPAL pallet that assembles itself, built from the production
// geometry (pallet-geometry.json). Units are millimetres. Pallet coords: X along the top boards,
// Y across, Z up. three.js coords: X = pallet X, Y = pallet Z (up), Z = -pallet Y (front = +Z).
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';

type Span = [number, number];
export type Part = { name: string; role: string; x: Span; y: Span; z: Span; grain: 'x' | 'y' };
export type Recipe = { id: string; dims: [number, number, number]; parts: Part[] };
export type Marks = { epal: string; ippc: string };

const ORDER = ['bottom', 'block', 'cross', 'top'];
const LIFT: Record<string, number> = { bottom: 0, block: 105, cross: 230, top: 350 };
const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);
const easeOutBack = (t: number) => { const c1 = 1.3, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); };
const clamp01 = (t: number) => Math.min(1, Math.max(0, t));

/** Planar wood UVs: the texture's grain (image V axis) runs along the part's grain axis. */
function woodUV(geo: THREE.BufferGeometry, size: THREE.Vector3, grainAxis: number, seed: number) {
  const pos = geo.attributes.position, nor = geo.attributes.normal, uv = geo.attributes.uv;
  const off = (seed * 0.61803) % 1;
  for (let i = 0; i < pos.count; i++) {
    const n = [Math.abs(nor.getX(i)), Math.abs(nor.getY(i)), Math.abs(nor.getZ(i))];
    const p = [pos.getX(i), pos.getY(i), pos.getZ(i)];
    const na = n.indexOf(Math.max(...n));
    const axes = [0, 1, 2].filter((a) => a !== na);
    let u: number, v: number;
    if (na === grainAxis) {
      const m = Math.max(size.getComponent(axes[0]), size.getComponent(axes[1])) * 2.2;
      u = 0.35 + off * 0.3 + p[axes[0]] / m;
      v = 0.35 + off * 0.3 + p[axes[1]] / m;
    } else {
      const other = axes.find((a) => a !== grainAxis)!;
      v = p[grainAxis] / 760 + off * 3;
      u = p[other] / 820 + off;
    }
    uv.setXY(i, u, v);
  }
  uv.needsUpdate = true;
}

export function mountAssembly(host: HTMLElement, overlay: SVGSVGElement, recipe: Recipe, marks: Marks) {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const small = window.matchMedia('(max-width: 700px)').matches;
  const canvas = document.createElement('canvas');
  host.prepend(canvas);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, small ? 1.5 : 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.16;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const [L, W, H] = recipe.dims;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(26, 1, 10, 40000);
  // Aim a little below the pallet so it sits higher in the frame, leaving room for the dimension lines.
  const target = new THREE.Vector3(0, -110, 60);

  scene.add(new THREE.HemisphereLight(0xffffff, 0xe4e8ef, 1.5));
  const key = new THREE.DirectionalLight(0xffffff, 2.3);
  key.position.set(-1500, 2800, 1900);
  key.castShadow = true;
  key.shadow.mapSize.set(small ? 1024 : 2048, small ? 1024 : 2048);
  Object.assign(key.shadow.camera, { left: -1300, right: 1300, top: 1300, bottom: -1300, near: 200, far: 7000 });
  key.shadow.bias = -0.0005;
  key.shadow.normalBias = 2;
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xe6edff, 0.75);
  fill.position.set(2000, 900, -1400);
  scene.add(fill);

  const ground = new THREE.Mesh(new THREE.PlaneGeometry(16000, 16000), new THREE.ShadowMaterial({ opacity: 0.14 }));
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);

  const tl = new THREE.TextureLoader();
  const tex = (url: string) => {
    const t = tl.load(url);
    t.colorSpace = THREE.SRGBColorSpace;
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.anisotropy = renderer.capabilities.getMaxAnisotropy();
    return t;
  };
  const sideTex = tex('/dev/textures/pine_side.jpg');
  const endTex = tex('/dev/textures/pine_end.jpg');

  type Item = { mesh: THREE.Object3D; role: string; final: THREE.Vector3; from: THREE.Vector3; rotFrom: THREE.Euler; t0: number; dur: number; ease: (t: number) => number };
  const items: Item[] = [];
  const group = new THREE.Group();
  scene.add(group);

  const parts = [...recipe.parts].sort((a, b) => ORDER.indexOf(a.role) - ORDER.indexOf(b.role));
  const roleStart: Record<string, number> = { bottom: 0, block: 0.6, cross: 1.45, top: 2.05 };
  const roleCount: Record<string, number> = {};
  parts.forEach((p, idx) => {
    const sx = p.x[1] - p.x[0], sy = p.z[1] - p.z[0], sz = p.y[1] - p.y[0];
    const geo = new RoundedBoxGeometry(sx, sy, sz, 2, 2.2);
    // Blocks show side grain on their marked faces, as in the studio renders.
    const grainAxis = p.role === 'block' || p.grain === 'x' ? 0 : 2;
    woodUV(geo, new THREE.Vector3(sx, sy, sz), grainAxis, idx + 1);
    const tint = new THREE.Color().setHSL(0.085, 0.18, 0.93 + ((idx * 37) % 9) / 100);
    const side = new THREE.MeshStandardMaterial({ map: sideTex, color: tint, roughness: 0.8, metalness: 0 });
    const end = new THREE.MeshStandardMaterial({ map: endTex, color: tint.clone().multiplyScalar(0.92), roughness: 0.88, metalness: 0 });
    const mats = [0, 1, 2, 3, 4, 5].map((f) => (Math.floor(f / 2) === grainAxis ? end : side));
    const mesh = new THREE.Mesh(geo, mats);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    const final = new THREE.Vector3((p.x[0] + p.x[1]) / 2, (p.z[0] + p.z[1]) / 2, -(p.y[0] + p.y[1]) / 2);
    mesh.position.copy(final);
    mesh.userData.role = p.role;
    group.add(mesh);
    const n = (roleCount[p.role] = (roleCount[p.role] ?? -1) + 1);
    const from = final.clone();
    const rotFrom = new THREE.Euler();
    let ease = easeOutBack;
    if (p.role === 'bottom') { from.x -= 2200; ease = easeOutCubic; }
    else if (p.role === 'block') from.y += 760;
    else if (p.role === 'cross') { from.y += 820; rotFrom.z = n % 2 ? 0.22 : -0.22; ease = easeOutCubic; }
    else { from.y += 940; rotFrom.x = 0.12; }
    const stagger = p.role === 'top' ? 0.12 : p.role === 'block' ? 0.07 : 0.1;
    items.push({ mesh, role: p.role, final, from, rotFrom, t0: (roleStart[p.role] ?? 0) + n * stagger, dur: 0.78, ease });
  });

  // Branding: EPAL oval on the corner blocks, IPPC mark on the centre block, both long sides.
  const front = W / 2 + 0.8;
  const blocks = recipe.parts.filter((p) => p.role === 'block' && Math.abs(p.y[0] + W / 2) < 1);
  const xs = blocks.map((b) => (b.x[0] + b.x[1]) / 2).sort((a, b) => a - b);
  const zMid = blocks.length ? (blocks[0].z[0] + blocks[0].z[1]) / 2 : H / 2;
  const stamps: THREE.Mesh[] = [];
  const stamp = (url: string, x: number, w: number, h: number, back: boolean) => {
    const m = new THREE.MeshStandardMaterial({ map: tex(url), transparent: true, opacity: 0, depthWrite: false, roughness: 0.95, polygonOffset: true, polygonOffsetFactor: -4 });
    const s = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m);
    s.position.set(back ? -x : x, zMid, back ? -front : front);
    if (back) s.rotation.y = Math.PI;
    s.userData.role = 'block';
    s.userData.base = s.position.clone();
    group.add(s);
    stamps.push(s);
  };
  if (xs.length === 3) {
    for (const back of [false, true]) {
      stamp(marks.epal, xs[0], 108, 54, back);
      stamp(marks.ippc, xs[1], 122, 54, back);
      stamp(marks.epal, xs[2], 108, 54, back);
    }
  }

  // Dimension lines drawn in an SVG overlay, following the pallet as it turns.
  const NS = 'http://www.w3.org/2000/svg';
  const dims = [
    // On the two faces the camera starts on (front and left), so the lines never cross the deck.
    { a: new THREE.Vector3(-L / 2, 0, W / 2 + 150), b: new THREE.Vector3(L / 2, 0, W / 2 + 150), label: `${L} mm` },
    { a: new THREE.Vector3(-L / 2 - 150, 0, W / 2), b: new THREE.Vector3(-L / 2 - 150, 0, -W / 2), label: `${W} mm` },
    { a: new THREE.Vector3(-L / 2 - 80, 0, W / 2 + 80), b: new THREE.Vector3(-L / 2 - 80, H, W / 2 + 80), label: `${H} mm` },
  ].map((d) => {
    const g = document.createElementNS(NS, 'g');
    const line = document.createElementNS(NS, 'line');
    const t1 = document.createElementNS(NS, 'circle');
    const t2 = document.createElementNS(NS, 'circle');
    const text = document.createElementNS(NS, 'text');
    t1.setAttribute('r', '3'); t2.setAttribute('r', '3');
    text.textContent = d.label;
    g.append(line, t1, t2, text);
    overlay.append(g);
    return { ...d, g, line, t1, t2, text };
  });
  const v = new THREE.Vector3();
  const toScreen = (p: THREE.Vector3, w: number, h: number) => {
    v.copy(p).applyMatrix4(group.matrixWorld).project(camera);
    return [(v.x * 0.5 + 0.5) * w, (-v.y * 0.5 + 0.5) * h];
  };

  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.dampingFactor = 0.07;
  controls.enablePan = false;
  controls.enableZoom = false;
  controls.rotateSpeed = 0.7;
  controls.minPolarAngle = 0.55;
  controls.maxPolarAngle = 1.32;
  controls.autoRotateSpeed = 0.7;
  controls.target.copy(target);
  let resumeTimer = 0;
  controls.addEventListener('start', () => { controls.autoRotate = false; window.clearTimeout(resumeTimer); });
  controls.addEventListener('end', () => { resumeTimer = window.setTimeout(() => { if (built) controls.autoRotate = !reduce; }, 3500); });

  const fit = () => {
    const w = host.clientWidth, h = host.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    const halfTan = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
    const dist = Math.max(2750, 2250 / (2 * halfTan * Math.max(0.5, camera.aspect)));
    const dir = new THREE.Vector3(-0.56, 0.42, 0.72).normalize();
    camera.position.copy(target).addScaledVector(dir, dist);
    camera.updateProjectionMatrix();
    overlay.setAttribute('viewBox', `0 0 ${w} ${h}`);
  };
  fit();
  new ResizeObserver(fit).observe(host);
  controls.update();
  const az0 = controls.getAzimuthalAngle();
  const turnedAway = () => {
    let d = Math.abs(controls.getAzimuthalAngle() - az0) % (Math.PI * 2);
    if (d > Math.PI) d = Math.PI * 2 - d;
    return clamp01((d - 0.3) / 0.3);
  };

  let start = performance.now() / 1000;
  let built = false;
  let exploded = 0;
  let explodeTarget = 0;
  let visible = true;
  const ASSEMBLY_END = 3.6;
  const reset = () => {
    start = performance.now() / 1000;
    built = false;
    controls.autoRotate = false;
    stamps.forEach((s) => ((s.material as THREE.MeshStandardMaterial).opacity = 0));
    host.dataset.phase = 'building';
  };
  host.dataset.phase = 'building';

  const tick = () => {
    requestAnimationFrame(tick);
    if (!visible) return;
    const now = performance.now() / 1000;
    const t = reduce ? 99 : now - start;
    exploded += (explodeTarget - exploded) * 0.09;
    for (const it of items) {
      const k = clamp01((t - it.t0) / it.dur);
      const e = it.ease(k);
      it.mesh.position.lerpVectors(it.from, it.final, e);
      it.mesh.position.y += LIFT[it.role] * exploded;
      it.mesh.rotation.set(it.rotFrom.x * (1 - e), 0, it.rotFrom.z * (1 - e));
      it.mesh.visible = k > 0;
    }
    stamps.forEach((s, i) => {
      const k = clamp01((t - (ASSEMBLY_END + 0.15 * (i % 3))) / 0.35);
      (s.material as THREE.MeshStandardMaterial).opacity = k;
      s.scale.setScalar(1 + (1 - easeOutCubic(k)) * 0.5);
      s.position.copy(s.userData.base);
      s.position.y += LIFT.block * exploded;
    });
    if (!built && t > ASSEMBLY_END + 0.9) {
      built = true;
      controls.autoRotate = !reduce;
      host.dataset.phase = 'built';
    }
    controls.target.y = target.y + 170 * exploded;
    controls.update();
    renderer.render(scene, camera);
    const w = host.clientWidth, h = host.clientHeight;
    const dimK = clamp01((t - (ASSEMBLY_END + 0.6)) / 0.6) * (1 - exploded) * (1 - turnedAway());
    for (const d of dims) {
      const [x1, y1] = toScreen(d.a, w, h);
      const [x2, y2] = toScreen(d.b, w, h);
      d.line.setAttribute('x1', String(x1)); d.line.setAttribute('y1', String(y1));
      d.line.setAttribute('x2', String(x1 + (x2 - x1) * easeOutCubic(dimK))); d.line.setAttribute('y2', String(y1 + (y2 - y1) * easeOutCubic(dimK)));
      d.t1.setAttribute('cx', String(x1)); d.t1.setAttribute('cy', String(y1));
      d.t2.setAttribute('cx', String(x2)); d.t2.setAttribute('cy', String(y2));
      d.text.setAttribute('x', String((x1 + x2) / 2 + 10)); d.text.setAttribute('y', String((y1 + y2) / 2 - 10));
      d.g.style.opacity = String(dimK);
    }
  };
  requestAnimationFrame(tick);

  new IntersectionObserver((es) => { visible = es.some((e) => e.isIntersecting); }).observe(host);
  document.addEventListener('visibilitychange', () => { visible = !document.hidden; });

  return {
    rebuild: reset,
    toggleLayers: () => { explodeTarget = explodeTarget ? 0 : 1; return explodeTarget === 1; },
  };
}
