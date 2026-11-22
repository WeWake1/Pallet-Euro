// Orthographic technical drawing of a pallet, generated from the production geometry
// (src/data/pallet-geometry.json, exported by the render pipeline's pallets.py).
// Coordinates there: mm, origin at the centre of the footprint, z up; X = direction of the top boards.
import geometry from '../data/pallet-geometry.json';

type Span = [number, number];
type Part = { name: string; role: string; x: Span; y: Span; z: Span };
type Recipe = { id: string; dims: [number, number, number]; parts: Part[]; corners?: { c: number }[]; meta?: { official?: Record<string, number> } };

export type Rect = { x: number; y: number; w: number; h: number; role: string; hidden: boolean };

export function palletDrawing(id: string) {
  const g = (geometry as unknown as Record<string, Recipe>)[id];
  if (!g) throw new Error(`no geometry for ${id}`);
  const [L, W, H] = g.dims;
  const chamfer = g.corners?.[0]?.c ?? 0;
  const parts = [...g.parts].sort((p, q) => p.z[0] - q.z[0]);
  const topZ = Math.max(...parts.map((p) => p.z[1]));

  // Top view: X right, Y up. Only the top deck is a visible edge; everything below is a hidden line.
  const top: Rect[] = parts.map((p) => ({
    x: p.x[0] + L / 2,
    y: W / 2 - p.y[1],
    w: p.x[1] - p.x[0],
    h: p.y[1] - p.y[0],
    role: p.role,
    hidden: p.z[1] < topZ - 0.5,
  }));
  // Front view (from -Y): X right, Z up. Members touching the front face, or spanning it, are visible.
  const front: Rect[] = parts.map((p) => ({
    x: p.x[0] + L / 2,
    y: H - p.z[1],
    w: p.x[1] - p.x[0],
    h: p.z[1] - p.z[0],
    role: p.role,
    hidden: p.y[0] > -W / 2 + 0.5,
  }));
  // Side view (from +X): Y right, Z up.
  const side: Rect[] = parts.map((p) => ({
    x: p.y[0] + W / 2,
    y: H - p.z[1],
    w: p.y[1] - p.y[0],
    h: p.z[1] - p.z[0],
    role: p.role,
    hidden: p.x[1] < L / 2 - 0.5,
  }));
  return { L, W, H, chamfer, top, front, side, official: g.meta?.official ?? {} };
}
