// PROTOTYPE round 3 · "The Mark": an extreme close-up of the corner block, the EPAL mark burns
// into the wood, then the camera pulls back to reveal the whole pallet.
import * as THREE from 'three';
import { createStudio, frame, clamp01, ease } from './studio';
import { detailedPallet, stampSpots, stampMaterial, type Recipe } from './pallet';

/** White silhouette of a stamp image (for the glowing branding-iron moment). The texture is created
 *  only after the image has loaded: resizing a canvas texture after its first upload fails in WebGL. */
function silhouetteInto(url: string, mat: THREE.MeshBasicMaterial) {
  const img = new Image();
  img.onload = () => {
    const c = document.createElement('canvas');
    c.width = img.width;
    c.height = img.height;
    const ctx = c.getContext('2d')!;
    ctx.drawImage(img, 0, 0);
    const d = ctx.getImageData(0, 0, c.width, c.height);
    for (let i = 0; i < d.data.length; i += 4) { d.data[i] = d.data[i + 1] = d.data[i + 2] = 255; }
    ctx.putImageData(d, 0, 0);
    mat.map = new THREE.CanvasTexture(c);
    mat.needsUpdate = true;
  };
  img.src = url;
}

export function mountMark(host: HTMLElement, recipe: Recipe, caption?: HTMLElement) {
  const S = createStudio(host, { shadowBox: 1500 });
  const wood = { side: S.tex('/dev/textures/pine_side.jpg'), end: S.tex('/dev/textures/pine_end.jpg'), fine: S.tex('/dev/textures/wood096_2k.jpg') };
  S.scene.add(detailedPallet(recipe, wood, 330));

  const tex = { epal: S.tex('/dev/stamps/epal.png', false), ippc: S.tex('/dev/stamps/ippc_IN-XXX_HT.png', false) };
  const spots = stampSpots(recipe);
  const hero = spots[0]; // front face, left corner block
  let heroMat: THREE.MeshStandardMaterial | null = null;
  for (const sp of spots) {
    const m = stampMaterial(tex[sp.key], sp === hero ? 0 : 1);
    const pl = new THREE.Mesh(new THREE.PlaneGeometry(sp.w, sp.h), m);
    pl.position.copy(sp.pos);
    pl.rotation.y = sp.rotY;
    S.scene.add(pl);
    if (sp === hero) { heroMat = m; pl.userData.hero = true; }
  }
  // Normal blending: an additive glow washes out to white on pale wood.
  const glowMat = new THREE.MeshBasicMaterial({ color: 0xff5a10, transparent: true, opacity: 0, depthWrite: false, toneMapped: false });
  silhouetteInto('/dev/stamps/epal.png', glowMat);
  const glow = new THREE.Mesh(new THREE.PlaneGeometry(hero.w, hero.h), glowMat);
  glow.position.copy(hero.pos).add(new THREE.Vector3(0, 0, 0.5));
  S.scene.add(glow);
  const heroPlane = S.scene.children.find((c) => c.userData.hero) as THREE.Mesh;

  const startLook = hero.pos.clone();
  const startPos = hero.pos.clone().add(new THREE.Vector3(-46, 26, 240));
  let end = { pos: new THREE.Vector3(), look: new THREE.Vector3() };
  S.onResize(() => {
    const wide = S.size().w > 900;
    end = wide
      ? frame(S.camera, new THREE.Vector3(0, -40, 40), new THREE.Vector3(-0.56, 0.42, 0.72), 3050, 1300, 0.23)
      : frame(S.camera, new THREE.Vector3(60, 60, 0), new THREE.Vector3(-0.56, 0.42, 0.72), 1500, 1200, 0);
  });

  const T = { glowIn: 0.45, burn: 0.75, burnEnd: 1.55, moveStart: 1.7, moveEnd: 4.1 };
  const pos = new THREE.Vector3();
  const look = new THREE.Vector3();
  const drift = new THREE.Vector3();
  S.onFrame((t) => {
    const time = S.reduce ? 99 : t;
    const g = clamp01((time - T.glowIn) / 0.3) * (1 - clamp01((time - T.burn) / (T.burnEnd - T.burn)));
    glowMat.opacity = glowMat.map ? g * 0.95 : 0;
    heroMat!.opacity = clamp01((time - T.burn) / (T.burnEnd - T.burn));
    const press = 1 + 0.08 * (1 - ease.out(clamp01((time - T.glowIn) / 0.5)));
    glow.scale.setScalar(press);
    heroPlane.scale.setScalar(press);
    const k = ease.inOut(clamp01((time - T.moveStart) / (T.moveEnd - T.moveStart)));
    const push = 1 - 0.06 * clamp01(time / T.moveStart);
    pos.copy(startPos).sub(startLook).multiplyScalar(push).add(startLook).lerp(end.pos, k);
    look.copy(startLook).lerp(end.look, k);
    if (time > T.moveEnd) {
      const a = 0.05 * Math.sin((time - T.moveEnd) * 0.4);
      drift.copy(pos).sub(look).applyAxisAngle(new THREE.Vector3(0, 1, 0), a);
      pos.copy(look).add(drift);
    }
    S.camera.position.copy(pos);
    S.camera.lookAt(look);
    if (caption) caption.style.opacity = String(clamp01((time - 0.5) / 0.4) * (1 - clamp01((time - T.moveStart - 0.2) / 0.5)));
  });
  return { replay: S.restart };
}
