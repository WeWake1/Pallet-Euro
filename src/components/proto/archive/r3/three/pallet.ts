// PROTOTYPE round 3: EPAL pallets built from the production geometry (pallet-geometry.json).
// Pallet coords: X along the top boards, Y across, Z up. three.js: X = X, Y = Z (up), Z = -Y (front = +Z).
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

type Span = [number, number];
export type Part = { name: string; role: string; x: Span; y: Span; z: Span; grain: 'x' | 'y' };
export type Recipe = { id: string; dims: [number, number, number]; parts: Part[] };
export type Wood = { side: THREE.Texture; end: THREE.Texture; fine?: THREE.Texture };

/** Planar UVs with the texture's grain (image V axis) along the part's grain axis. */
function woodUV(geo: THREE.BufferGeometry, size: THREE.Vector3, grainAxis: number, seed: number, tile: number) {
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
      v = p[grainAxis] / tile + off * 3;
      u = p[other] / (tile * 1.08) + off;
    }
    uv.setXY(i, u, v);
  }
  uv.needsUpdate = true;
}

type PartGeo = { geo: THREE.BufferGeometry; role: string; grainAxis: number; final: THREE.Vector3 };
function partGeos(recipe: Recipe, blockTile = 760): PartGeo[] {
  return recipe.parts.map((p, i) => {
    const sx = p.x[1] - p.x[0], sy = p.z[1] - p.z[0], sz = p.y[1] - p.y[0];
    const geo = new RoundedBoxGeometry(sx, sy, sz, 2, 2.2);
    // Blocks show side grain on their marked faces, as in the studio renders.
    const grainAxis = p.role === 'block' || p.grain === 'x' ? 0 : 2;
    woodUV(geo, new THREE.Vector3(sx, sy, sz), grainAxis, i + 1, p.role === 'block' ? blockTile : 760);
    return { geo, role: p.role, grainAxis, final: new THREE.Vector3((p.x[0] + p.x[1]) / 2, (p.z[0] + p.z[1]) / 2, -(p.y[0] + p.y[1]) / 2) };
  });
}

const tint = (k: number) => new THREE.Color().setHSL(0.085, 0.18, 0.93 + k / 100);

/** One mesh per part, with side- and end-grain materials (for close-ups). */
export function detailedPallet(recipe: Recipe, wood: Wood, blockTile = 760) {
  const mats = [0, 4, 8].map((k) => ({
    side: new THREE.MeshStandardMaterial({ map: wood.side, color: tint(k), roughness: 0.8 }),
    end: new THREE.MeshStandardMaterial({ map: wood.end, color: tint(k).multiplyScalar(0.92), roughness: 0.88 }),
  }));
  const fine = wood.fine ? new THREE.MeshStandardMaterial({ map: wood.fine, color: tint(5), roughness: 0.78 }) : null;
  const group = new THREE.Group();
  partGeos(recipe, blockTile).forEach((pg, i) => {
    const m = mats[i % mats.length];
    const side = pg.role === 'block' && fine ? fine : m.side;
    const mesh = new THREE.Mesh(pg.geo, [0, 1, 2, 3, 4, 5].map((f) => (Math.floor(f / 2) === pg.grainAxis ? m.end : side)));
    mesh.position.copy(pg.final);
    mesh.castShadow = mesh.receiveShadow = true;
    group.add(mesh);
  });
  return group;
}

/** All parts merged into one geometry (one draw call per pallet), for stacks and loads. */
export function mergedPalletGeometry(recipe: Recipe) {
  const geos = partGeos(recipe).map((pg) => {
    const g = pg.geo.clone();
    g.clearGroups();
    g.translate(pg.final.x, pg.final.y, pg.final.z);
    return g;
  });
  return mergeGeometries(geos, false)!;
}

export type Spot = { key: 'epal' | 'ippc'; pos: THREE.Vector3; rotY: number; w: number; h: number };

/** Marking positions per EPAL's sheets: EPAL oval on the corner blocks, IPPC mark on the centre block. */
export function stampSpots(recipe: Recipe, sides: ('front' | 'back')[] = ['front', 'back']): Spot[] {
  const W = recipe.dims[1];
  const blocks = recipe.parts.filter((p) => p.role === 'block' && Math.abs(p.y[0] + W / 2) < 1);
  const xs = blocks.map((b) => (b.x[0] + b.x[1]) / 2).sort((a, b) => a - b);
  if (xs.length !== 3) return [];
  const zMid = (blocks[0].z[0] + blocks[0].z[1]) / 2;
  const face = W / 2 + 0.8;
  const out: Spot[] = [];
  for (const s of sides) {
    const back = s === 'back';
    const put = (key: Spot['key'], x: number, w: number) =>
      out.push({ key, pos: new THREE.Vector3(back ? -x : x, zMid, back ? -face : face), rotY: back ? Math.PI : 0, w, h: 54 });
    put('epal', xs[0], 108);
    put('ippc', xs[1], 122);
    put('epal', xs[2], 108);
  }
  return out;
}

export function stampMaterial(map: THREE.Texture, opacity = 1) {
  return new THREE.MeshStandardMaterial({ map, transparent: true, opacity, depthWrite: false, roughness: 0.95, polygonOffset: true, polygonOffsetFactor: -4 });
}
