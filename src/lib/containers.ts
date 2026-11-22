// How many pallets fit on a container floor. Internal dimensions in mm (typical ISO values).
export type Container = { id: string; name: string; short: string; L: number; W: number; H: number };

export const CONTAINERS: Container[] = [
  { id: '20', name: "20' standard", short: "20' ST", L: 5898, W: 2352, H: 2393 },
  { id: '40', name: "40' standard", short: "40' ST", L: 12032, W: 2352, H: 2393 },
  { id: '40hc', name: "40' high cube", short: "40' HC", L: 12032, W: 2352, H: 2698 },
  { id: '45pw', name: "45' pallet-wide", short: "45' PW", L: 13556, W: 2440, H: 2698 },
];

export type Placed = { x: number; y: number; w: number; h: number };
export type Fit = { count: number; placed: Placed[] };

/**
 * Best single-tier floor layout from strips running the length of the container:
 * strips with the pallet's long side along the container, and strips turned 90°.
 * This reproduces the standard tables (e.g. 11 Euro pallets in a 20', 25 in a 40', 33 in a 45' pallet-wide).
 * Theoretical maximum: no allowance for door clearance or overhang.
 */
export function floorFit(c: Pick<Container, 'L' | 'W'>, a: number, b: number): Fit {
  const long = Math.max(a, b);
  const short = Math.min(a, b);
  const perLong = Math.floor(c.L / long); // pallets in a strip with the long side along the container
  const perShort = Math.floor(c.L / short); // pallets in a turned strip
  let best = { count: 0, nA: 0, nB: 0 };
  for (let nA = 0; nA * short <= c.W; nA++) {
    for (let nB = 0; nA * short + nB * long <= c.W; nB++) {
      const count = nA * perLong + nB * perShort;
      if (count > best.count) best = { count, nA, nB };
    }
  }
  const placed: Placed[] = [];
  let y = 0;
  for (let s = 0; s < best.nB; s++, y += long)
    for (let i = 0; i < perShort; i++) placed.push({ x: i * short, y, w: short, h: long });
  for (let s = 0; s < best.nA; s++, y += short)
    for (let i = 0; i < perLong; i++) placed.push({ x: i * long, y, w: long, h: short });
  return { count: best.count, placed };
}
