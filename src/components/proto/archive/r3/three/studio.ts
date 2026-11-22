// PROTOTYPE round 3: a light studio for the 3D heroes. Units are millimetres.
import * as THREE from 'three';

export type StudioOpts = { fov?: number; exposure?: number; shadowBox?: number; keyPos?: [number, number, number] };
export type Studio = ReturnType<typeof createStudio>;

export function createStudio(host: HTMLElement, o: StudioOpts = {}) {
  const small = window.matchMedia('(max-width: 700px)').matches;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const canvas = document.createElement('canvas');
  host.prepend(canvas);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, small ? 1.5 : 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = o.exposure ?? 1.16;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(o.fov ?? 26, 1, 5, 120000);
  scene.add(new THREE.HemisphereLight(0xffffff, 0xe4e8ef, 1.5));
  const key = new THREE.DirectionalLight(0xffffff, 2.3);
  key.position.set(...(o.keyPos ?? [-1500, 2800, 1900]));
  key.castShadow = true;
  const sb = o.shadowBox ?? 1400;
  key.shadow.mapSize.set(small ? 1024 : 2048, small ? 1024 : 2048);
  Object.assign(key.shadow.camera, { left: -sb, right: sb, top: sb, bottom: -sb, near: 100, far: 30000 });
  key.shadow.bias = -0.0005;
  key.shadow.normalBias = 2;
  scene.add(key, key.target);
  const fill = new THREE.DirectionalLight(0xe6edff, 0.75);
  fill.position.set(2000, 900, -1400);
  scene.add(fill);
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(80000, 80000), new THREE.ShadowMaterial({ opacity: 0.14 }));
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);

  const loader = new THREE.TextureLoader();
  const tex = (url: string, repeat = true) => {
    const t = loader.load(url);
    t.colorSpace = THREE.SRGBColorSpace;
    if (repeat) t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.anisotropy = renderer.capabilities.getMaxAnisotropy();
    return t;
  };

  const frames: ((t: number) => void)[] = [];
  const resizes: (() => void)[] = [];
  const size = () => ({ w: host.clientWidth, h: host.clientHeight });
  const fit = () => {
    const { w, h } = size();
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    resizes.forEach((f) => f());
  };
  new ResizeObserver(fit).observe(host);
  let visible = true;
  new IntersectionObserver((es) => { visible = es.some((e) => e.isIntersecting); }).observe(host);
  let t0 = performance.now();
  const loop = () => {
    requestAnimationFrame(loop);
    if (!visible || document.hidden) return;
    const t = (performance.now() - t0) / 1000;
    frames.forEach((f) => f(t));
    renderer.render(scene, camera);
  };
  fit();
  requestAnimationFrame(loop);

  return {
    renderer, scene, camera, key, small, reduce, size, tex,
    onFrame: (f: (t: number) => void) => frames.push(f),
    onResize: (f: () => void) => { resizes.push(f); f(); },
    restart: () => { t0 = performance.now(); },
  };
}

/**
 * Camera placement that fits fitW × fitH (mm) around `target`, looking along -dir, and shifts the
 * subject sideways on screen by `shift` (fraction of the view width; positive moves it right).
 */
export function frame(camera: THREE.PerspectiveCamera, target: THREE.Vector3, dir: THREE.Vector3, fitW: number, fitH: number, shift = 0) {
  const ht = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
  const dist = Math.max(fitH / (2 * ht), fitW / (2 * ht * camera.aspect));
  const pos = target.clone().addScaledVector(dir.clone().normalize(), dist);
  const fwd = target.clone().sub(pos).normalize();
  const right = new THREE.Vector3().crossVectors(fwd, new THREE.Vector3(0, 1, 0)).normalize();
  const off = right.multiplyScalar(-shift * 2 * dist * ht * camera.aspect);
  return { pos: pos.add(off), look: target.clone().add(off) };
}

export const ease = {
  inOut: (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  out: (t: number) => 1 - Math.pow(1 - t, 3),
  in: (t: number) => t * t,
};
export const clamp01 = (t: number) => Math.min(1, Math.max(0, t));
