// PROTOTYPE round 3 · "The Container": the doors of a deep-blue 20' container swing open to show
// it loaded on EPAL pallets, laid out with the real floor-fit maths (11 Euro pallets).
import * as THREE from 'three';
import { createStudio, frame, clamp01, ease } from './studio';
import { mergedPalletGeometry, stampSpots, stampMaterial, type Recipe } from './pallet';
import { floorFit } from '../../../../../lib/containers';

export function mountContainer(host: HTMLElement, recipe: Recipe) {
  const S = createStudio(host, { shadowBox: 4800, keyPos: [-5600, 9000, 8200], exposure: 1.12 });
  const C = { L: 6058, W: 2438, H: 2591, t: 40 };
  const IN = { L: 5898, W: 2352 };
  const g = new THREE.Group();
  S.scene.add(g);
  const blue = new THREE.MeshStandardMaterial({ color: 0x0b3a9e, roughness: 0.5, metalness: 0.3 });
  const blueDark = new THREE.MeshStandardMaterial({ color: 0x082c78, roughness: 0.55, metalness: 0.3 });
  const inner = new THREE.MeshStandardMaterial({ color: 0xe7ebf2, roughness: 0.9, side: THREE.DoubleSide });
  const steel = new THREE.MeshStandardMaterial({ color: 0xc4cad4, roughness: 0.35, metalness: 0.8 });
  const floorMat = new THREE.MeshStandardMaterial({ map: S.tex('/dev/textures/pine_side.jpg'), color: 0x9a7650, roughness: 0.9 });
  const box = (w: number, h: number, d: number, mat: THREE.Material, x: number, y: number, z: number, parent: THREE.Object3D = g) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
    m.position.set(x, y, z);
    m.castShadow = m.receiveShadow = true;
    parent.add(m);
    return m;
  };

  // Shell: base, floor, walls, roof, far end, rear frame.
  box(C.W, 160, C.L, blueDark, 0, 80, 0);
  box(IN.W, 24, IN.L, floorMat, 0, 172, 0);
  box(C.t, C.H - 160, C.L, blue, -C.W / 2 + C.t / 2, 160 + (C.H - 160) / 2, 0);
  box(C.t, C.H - 160, C.L, blue, C.W / 2 - C.t / 2, 160 + (C.H - 160) / 2, 0);
  box(C.W, C.t, C.L, blue, 0, C.H - C.t / 2, 0);
  box(C.W, C.H - 160, C.t, blue, 0, 160 + (C.H - 160) / 2, -C.L / 2 + C.t / 2);
  const inPlane = (w: number, h: number, x: number, y: number, z: number, ry = 0, rx = 0) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), inner);
    m.position.set(x, y, z);
    m.rotation.set(rx, ry, 0);
    m.receiveShadow = true;
    g.add(m);
  };
  const ih = C.H - 160 - C.t;
  inPlane(C.L - 2, ih, -C.W / 2 + C.t + 1, 160 + ih / 2, 0, Math.PI / 2);
  inPlane(C.L - 2, ih, C.W / 2 - C.t - 1, 160 + ih / 2, 0, -Math.PI / 2);
  inPlane(C.W - 2 * C.t, C.L - 2, 0, C.H - C.t - 1, 0, 0, Math.PI / 2);
  inPlane(C.W - 2 * C.t, ih, 0, 160 + ih / 2, -C.L / 2 + C.t + 1);
  const post = 150;
  box(post, C.H, post, blueDark, -C.W / 2 + post / 2, C.H / 2, C.L / 2 - post / 2);
  box(post, C.H, post, blueDark, C.W / 2 - post / 2, C.H / 2, C.L / 2 - post / 2);
  box(C.W, 230, post, blueDark, 0, C.H - 115, C.L / 2 - post / 2);
  box(C.W, 170, post, blueDark, 0, 85, C.L / 2 - post / 2);
  for (const sx of [-1, 1]) for (const sy of [0, 1]) box(178, 118, 162, steel, sx * (C.W / 2 - 89), sy ? C.H - 59 : 59, C.L / 2 - 81);

  // Corrugation ribs on both long sides.
  const ribGeo = new THREE.BoxGeometry(26, C.H - 470, 70);
  const n = Math.floor((C.L - 400) / 140);
  const ribs = new THREE.InstancedMesh(ribGeo, blue, n * 2);
  const mtx = new THREE.Matrix4();
  for (let i = 0; i < n; i++) {
    const z = -C.L / 2 + 200 + i * 140;
    mtx.makeTranslation(-C.W / 2 - 13, C.H / 2 + 30, z); ribs.setMatrixAt(i * 2, mtx);
    mtx.makeTranslation(C.W / 2 + 13, C.H / 2 + 30, z); ribs.setMatrixAt(i * 2 + 1, mtx);
  }
  ribs.castShadow = ribs.receiveShadow = true;
  g.add(ribs);

  // Doors, hinged on the rear posts.
  const doorW = (C.W - 2 * post) / 2 + 6;
  const doorH = C.H - 230 - 170;
  const doors: THREE.Group[] = [];
  for (const side of [-1, 1]) {
    const pivot = new THREE.Group();
    pivot.position.set(side * (C.W / 2 - post), 170 + doorH / 2, C.L / 2 + 26);
    const panel = new THREE.Group();
    panel.position.x = -side * (doorW / 2);
    box(doorW, doorH, 44, blue, 0, 0, 0, panel);
    for (let i = 0; i < 4; i++) box(doorW / 6, doorH - 160, 18, blueDark, -doorW / 2 + doorW * (0.16 + i * 0.23), 0, 30, panel);
    for (const bx of [-0.24, 0.24]) {
      const bar = new THREE.Mesh(new THREE.CylinderGeometry(17, 17, doorH + 60, 16), steel);
      bar.position.set(bx * doorW, 0, 52);
      bar.castShadow = true;
      panel.add(bar);
      box(36, 260, 30, steel, bx * doorW + 40, -doorH * 0.1, 66, panel);
    }
    pivot.add(panel);
    g.add(pivot);
    doors.push(pivot);
  }

  // Cargo: EPAL 1 pallets with carton loads, at the floor-fit positions.
  const pGeo = mergedPalletGeometry(recipe);
  const pMat = new THREE.MeshStandardMaterial({ map: S.tex('/dev/textures/pine_side.jpg'), color: new THREE.Color().setHSL(0.085, 0.18, 0.95), roughness: 0.8 });
  const kraft = [0xc8a274, 0xbf9868, 0xcfa97c].map((c) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.92 }));
  const wrap = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.25, metalness: 0, transparent: true, opacity: 0.16 });
  const epalTex = S.tex('/dev/stamps/epal.png', false);
  const ippcTex = S.tex('/dev/stamps/ippc_IN-XXX_HT.png', false);
  const sMats = { epal: stampMaterial(epalTex), ippc: stampMaterial(ippcTex) };
  const fit = floorFit(IN, 1200, 800);
  fit.placed.forEach((r, i) => {
    const pal = new THREE.Group();
    const m = new THREE.Mesh(pGeo, pMat);
    m.castShadow = m.receiveShadow = true;
    pal.add(m);
    for (const sp of stampSpots(recipe, ['front', 'back'])) {
      const pl = new THREE.Mesh(new THREE.PlaneGeometry(sp.w, sp.h), sMats[sp.key]);
      pl.position.copy(sp.pos);
      pl.rotation.y = sp.rotY;
      pal.add(pl);
    }
    const longAlongContainer = r.w > r.h;
    pal.rotation.y = longAlongContainer ? Math.PI / 2 : 0;
    const z = -IN.L / 2 + r.x + r.w / 2;
    const x = -IN.W / 2 + r.y + r.h / 2;
    pal.position.set(x, 184, z);
    g.add(pal);
    const loadH = 1020 + ((i * 53) % 90);
    box(r.h - 40, loadH, r.w - 40, kraft[i % 3], x, 184 + 144 + loadH / 2, z);
    box(r.h - 30, loadH + 10, r.w - 30, wrap, x, 184 + 144 + loadH / 2, z).castShadow = false;
  });

  const inside = new THREE.PointLight(0xffffff, 1.1, 0, 0);
  inside.position.set(0, C.H - 300, C.L / 2 - 1400);
  S.scene.add(inside);

  // Seen from the rear right, so the body recedes to the right, away from the headline.
  const target = new THREE.Vector3(0, 1250, C.L / 2 - 1100);
  const dir = new THREE.Vector3(0.5, 0.22, 0.84);
  let end = { pos: new THREE.Vector3(), look: new THREE.Vector3() };
  let start = { pos: new THREE.Vector3(), look: new THREE.Vector3() };
  S.onResize(() => {
    const wide = S.size().w > 900;
    end = frame(S.camera, target, dir, wide ? 8000 : 4600, wide ? 4500 : 5000, wide ? 0.27 : 0);
    start = frame(S.camera, target, dir, wide ? 10200 : 6000, wide ? 5800 : 6400, wide ? 0.27 : 0);
  });
  const OPEN = 2.85;
  S.onFrame((t) => {
    const time = S.reduce ? 99 : t;
    const k = ease.inOut(clamp01((time - 0.6) / 1.9));
    doors[0].rotation.y = -OPEN * k;
    doors[1].rotation.y = OPEN * k;
    const c = ease.inOut(clamp01((time - 0.5) / 3.0));
    S.camera.position.lerpVectors(start.pos, end.pos, c);
    const look = start.look.clone().lerp(end.look, c);
    S.camera.lookAt(look);
  });
  return { replay: S.restart };
}
