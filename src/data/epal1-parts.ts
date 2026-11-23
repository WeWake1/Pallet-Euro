// The parts of an EPAL 1 Euro pallet, layer by layer, for the anatomy viewer (prototype; the guide page "What makes an
// EPAL pallet", decision #60). Sizes come from src/data/pallet-geometry.json (EPAL's drawing); counts and the notes on
// nails and markings only use facts checked on EPAL's EPAL 1 page (docs/decisions.md, after round 4). `ids` are the
// colours of the ID maps rendered by tools/render/hero/layers.py (PNG red = 10 x id): 1-20 the parts in recipe order,
// 21 nails, 22 EPAL marks, 23 IPPC mark.

export type Part = { name: string; size: string; qty: string; ids: number[] };
export type Layer = { key: string; name: string; count: string; note: string; parts: Part[] };

export const EPAL1_LAYERS: Layer[] = [
  {
    key: 'top', name: 'Top deck boards', count: '5', note: 'Three wide boards and two narrow ones, nailed across the stringer boards.',
    parts: [
      { name: 'Top deck board, wide', size: '1200 × 145 × 22', qty: '3', ids: [16, 18, 20] },
      { name: 'Top deck board, narrow', size: '1200 × 100 × 22', qty: '2', ids: [17, 19] },
    ],
  },
  {
    key: 'stringer', name: 'Stringer boards', count: '3', note: 'They run across the pallet and tie the blocks together.',
    parts: [{ name: 'Stringer board', size: '800 × 145 × 22', qty: '3', ids: [13, 14, 15] }],
  },
  {
    key: 'blocks', name: 'Blocks', count: '9', note: 'Three rows of three. The corner blocks carry EPAL in oval; the middle block carries the IPPC mark and the EPAL ID.',
    parts: [
      { name: 'Block', size: '145 × 100 × 78', qty: '6', ids: [4, 6, 7, 9, 10, 12] },
      { name: 'Block, centre row', size: '145 × 145 × 78', qty: '3', ids: [5, 8, 11] },
      { name: 'EPAL in oval', size: 'on the left and right corner blocks', qty: '', ids: [22] },
      { name: 'IPPC mark and EPAL ID', size: 'ISPM 15 heat treatment, middle block', qty: '', ids: [23] },
    ],
  },
  {
    key: 'bottom', name: 'Bottom deck boards', count: '3', note: 'The pallet stands on these: two outer boards and a wider one in the middle.',
    parts: [
      { name: 'Bottom deck board, outer', size: '1200 × 100 × 22', qty: '2', ids: [1, 3] },
      { name: 'Bottom deck board, middle', size: '1200 × 145 × 22', qty: '1', ids: [2] },
    ],
  },
  {
    key: 'nails', name: 'Nails', count: '78', note: 'EPAL stipulates the position of every one of the 78 nails.',
    parts: [{ name: 'Nails', size: 'positions set by EPAL', qty: '78', ids: [21] }],
  },
];

/** The part (and its layer) for an ID-map colour. */
export const partOf = (id: number) => {
  for (const l of EPAL1_LAYERS) for (const p of l.parts) if (p.ids.includes(id)) return { layer: l, part: p };
  return null;
};
