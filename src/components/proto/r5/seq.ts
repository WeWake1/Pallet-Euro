// PROTOTYPE round 5 (from round 4): plays pre-rendered Blender frames on a canvas (no live 3D).
// Frames load coarse-to-fine (every 8th, then 4th, 2nd, all) so scrubbing works almost at once;
// a fractional frame cross-fades its two neighbours, so 48 frames move smoothly.
// The picture covers the canvas around a focus point (0..1), so the pallet stays in view at any shape.

export type Seq = {
  count: number;
  /** Draw a (fractional) frame. */
  show: (f: number) => void;
  /** Resolves when every frame has loaded. */
  done: Promise<void>;
};

export function createSeq(canvas: HTMLCanvasElement, urls: string[], focus = { x: 0.5, y: 0.5 }, start = 0, loop = false): Seq {
  const ctx = canvas.getContext('2d', { alpha: false })!;
  const count = urls.length;
  const imgs: (HTMLImageElement | null)[] = new Array(count).fill(null);
  let current = start;

  const order: number[] = [start];
  for (const step of [8, 4, 2, 1]) for (let i = 0; i < count; i += step) if (!order.includes(i)) order.push(i);
  if (!order.includes(count - 1)) order.splice(1, 0, count - 1);

  const nearest = (f: number) => {
    for (let d = 0; d < count; d++) {
      const a = Math.round(f) - d, b = Math.round(f) + d;
      if (a >= 0 && imgs[a]) return a;
      if (b < count && imgs[b]) return b;
    }
    return -1;
  };

  const blit = (img: HTMLImageElement, alpha: number) => {
    const cw = canvas.width, ch = canvas.height;
    const iw = img.naturalWidth, ih = img.naturalHeight;
    const s = Math.max(cw / iw, ch / ih);
    const sw = cw / s, sh = ch / s;
    const sx = Math.min(Math.max(focus.x * iw - sw / 2, 0), iw - sw);
    const sy = Math.min(Math.max(focus.y * ih - sh / 2, 0), ih - sh);
    ctx.globalAlpha = alpha;
    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, cw, ch);
  };

  const show = (f: number) => {
    current = loop ? ((f % count) + count) % count : Math.min(Math.max(f, 0), count - 1);
    // in a loop the last frame blends into the first, so there is no seam
    const i0 = Math.floor(current), i1 = loop ? (i0 + 1) % count : Math.min(i0 + 1, count - 1), t = current - i0;
    if (imgs[i0] && imgs[i1]) {
      blit(imgs[i0]!, 1);
      if (t > 0.001 && i1 !== i0) blit(imgs[i1]!, t);
    } else {
      const n = nearest(current);
      if (n >= 0) blit(imgs[n]!, 1);
    }
    ctx.globalAlpha = 1;
  };

  const fit = () => {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = Math.round(canvas.clientWidth * dpr), h = Math.round(canvas.clientHeight * dpr);
    if (!w || !h) return;
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    show(current);
  };
  new ResizeObserver(fit).observe(canvas);

  const done = (async () => {
    for (const i of order) {
      const img = new Image();
      img.decoding = 'async';
      img.src = urls[i];
      try { await img.decode(); } catch { continue; }
      imgs[i] = img;
      if (i === start || Math.abs(i - current) < 1.5) show(current);
      if (i === start) canvas.classList.add('ready');
    }
  })();
  fit();
  return { count, show, done };
}

/** Frame URLs 00.webp .. NN.webp (000.webp .. when there are more than 100) in a public folder. */
export const frames = (dir: string, count: number) =>
  Array.from({ length: count }, (_, i) => `${dir}/${String(i).padStart(count > 100 ? 3 : 2, '0')}.webp`);
