// PROTOTYPE round 3 · "The Stack": EPAL pallets drop into tall stacks one after another (scale),
// then the camera sways slowly. Two HTML tags follow points on the main stack.
import * as THREE from 'three';
import { createStudio, frame, clamp01, ease } from './studio';
import { mergedPalletGeometry, stampSpots, stampMaterial, type Recipe } from './pallet';

export function mountStack(host: HTMLElement, recipe: Recipe, tags: HTMLElement[]) {
  const S = createStudio(host, { shadowBox: 3200, keyPos: [-3000, 5600, 3600] });
  const [L, W, H] = recipe.dims;
  const geo = mergedPalletGeometry(recipe);
  const mat = new THREE.MeshStandardMaterial({ map: S.tex('/dev/textures/pine_side.jpg'), color: new THREE.Color().setHSL(0.085, 0.18, 0.95), roughness: 0.8 });
  const stampTex = { epal: S.tex('/dev/stamps/epal.png', false), ippc: S.tex('/dev/stamps/ippc_IN-XXX_HT.png', false) };
  const stampMats = { epal: stampMaterial(stampTex.epal), ippc: stampMaterial(stampTex.ippc) };
  const stampGeo = { epal: new THREE.PlaneGeometry(108, 54), ippc: new THREE.PlaneGeometry(122, 54) };
  const spots = stampSpots(recipe, ['front']);

  const main = { n: 11, x: 0, z: 0, delay: 0.2 };
  const stacks = S.small ? [main] : [main, { n: 7, x: 1750, z: -1450, delay: 1.0 }];
  const STEP = 0.13;
  type P = { g: THREE.Group; y: number; t0: number };
  const pallets: P[] = [];
  for (const s of stacks) {
    for (let i = 0; i < s.n; i++) {
      const g = new THREE.Group();
      const m = new THREE.Mesh(geo, mat);
      m.castShadow = m.receiveShadow = true;
      g.add(m);
      for (const sp of spots) {
        const pl = new THREE.Mesh(stampGeo[sp.key], stampMats[sp.key]);
        pl.position.copy(sp.pos);
        g.add(pl);
      }
      g.position.set(s.x, i * H, s.z);
      g.visible = false;
      S.scene.add(g);
      pallets.push({ g, y: i * H, t0: s.delay + i * STEP });
    }
  }
  const topY = stacks[0].n * H;
  const built = stacks[0].delay + stacks[0].n * STEP + 0.6;

  const target = new THREE.Vector3(0, topY * 0.47, -250);
  const dir = new THREE.Vector3(-0.6, 0.2, 0.78);
  let base = { pos: new THREE.Vector3(), look: new THREE.Vector3() };
  S.onResize(() => {
    const wide = S.size().w > 900;
    base = frame(S.camera, wide ? target : new THREE.Vector3(150, topY * 0.47, 0), dir, wide ? 3400 : 2300, wide ? 2350 : 2500, wide ? 0.22 : 0);
  });

  // Tags sit on the front face of the main stack, near the top and near the base.
  const anchors = [new THREE.Vector3(-L * 0.18, topY - H * 0.3, W / 2), new THREE.Vector3(-L * 0.18, H * 2.4, W / 2)];
  const v = new THREE.Vector3();
  const rot = new THREE.Vector3();
  S.onFrame((t) => {
    const time = S.reduce ? 99 : t;
    for (const p of pallets) {
      const k = clamp01((time - p.t0) / 0.42);
      p.g.visible = k > 0;
      const fall = 1700 * (1 - ease.in(k));
      const settle = k >= 1 ? 14 * Math.sin(Math.PI * clamp01((time - p.t0 - 0.42) / 0.16)) : 0;
      p.g.position.y = p.y + fall + settle;
    }
    const sway = time > built ? 0.11 * Math.sin((time - built) * 0.32) : 0;
    rot.copy(base.pos).sub(base.look).applyAxisAngle(new THREE.Vector3(0, 1, 0), sway);
    S.camera.position.copy(base.look).add(rot);
    S.camera.lookAt(base.look);
    const show = clamp01((time - built) / 0.6);
    const { w, h } = S.size();
    tags.forEach((tag, i) => {
      v.copy(anchors[i]).project(S.camera);
      tag.style.transform = `translate(${(v.x * 0.5 + 0.5) * w}px, ${(-v.y * 0.5 + 0.5) * h}px)`;
      tag.style.opacity = String(show);
    });
  });
  return { replay: S.restart };
}
