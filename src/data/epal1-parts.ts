// The parts of an EPAL 1 Euro pallet, for the part inspector (prototype, product pages). Sizes come from
// src/data/pallet-geometry.json (EPAL's drawing); counts and the notes on nails and markings only use facts checked
// on EPAL's EPAL 1 page (docs/decisions.md, after round 4). `ids` are the colours of the ID map rendered by
// tools/render/hero/inspect.py (PNG red = 10 x id): 1-20 the parts in recipe order, 21 nails, 22 EPAL marks, 23 IPPC.

export type PartGroup = { key: string; name: string; size: string; qty: string; note?: string; ids: number[] };

export const EPAL1_PARTS: PartGroup[] = [
  { key: 'top-wide', name: 'Top deck board, wide', size: '1200 × 145 × 22', qty: '3', ids: [16, 18, 20] },
  { key: 'top-narrow', name: 'Top deck board, narrow', size: '1200 × 100 × 22', qty: '2', ids: [17, 19] },
  { key: 'stringer', name: 'Stringer board', size: '800 × 145 × 22', qty: '3', ids: [13, 14, 15] },
  { key: 'block', name: 'Block', size: '145 × 100 × 78', qty: '6', ids: [4, 6, 7, 9, 10, 12] },
  { key: 'block-centre', name: 'Block, centre row', size: '145 × 145 × 78', qty: '3', ids: [5, 8, 11] },
  { key: 'bottom-outer', name: 'Bottom deck board, outer', size: '1200 × 100 × 22', qty: '2', ids: [1, 3] },
  { key: 'bottom-middle', name: 'Bottom deck board, middle', size: '1200 × 145 × 22', qty: '1', ids: [2] },
  { key: 'nails', name: 'Nails', size: 'positions set by EPAL', qty: '78', ids: [21] },
  { key: 'epal-mark', name: 'EPAL in oval', size: 'branded on the left and right corner blocks', qty: '', ids: [22] },
  { key: 'ippc-mark', name: 'IPPC mark and EPAL ID', size: 'ISPM 15 heat treatment, on the middle block', qty: '', ids: [23] },
];
