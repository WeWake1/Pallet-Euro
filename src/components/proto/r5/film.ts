// PROTOTYPE round 5: Apple-style scroll film from pre-rendered Blender frames.
// Computers (wider than 900 px): the stage is pinned while its tall section scrolls past; the scroll position
// picks the frame (eased a little, so a flick glides) and each caption fades in and out over its range.
// Phones: no scroll-driven or pinned motion (CLAUDE.md rule 7). When the picture is mostly in view it plays
// once by itself, the caption list following along, then holds the last frame; "Play again" replays it.
// Reduced motion: the last frame and every caption; nothing moves.
// Frames start loading only when the section gets near the viewport.
import { createSeq, frames, type Seq } from './seq';

const smooth = (a: number, b: number, x: number) => {
  const t = Math.min(Math.max((x - a) / (b - a), 0), 1);
  return t * t * (3 - 2 * t);
};

export function mountFilm(root: HTMLElement) {
  const d = root.dataset;
  const frame = root.querySelector<HTMLElement>('[data-frame]')!;
  const canvas = frame.querySelector('canvas')!;
  const beats = [...root.querySelectorAll<HTMLElement>('[data-in]')].map((el) => ({ el, a: Number(el.dataset.in), b: Number(el.dataset.out) }));
  const replay = root.querySelector<HTMLButtonElement>('[data-replay]');
  const wide = matchMedia('(min-width: 901px)').matches;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const dir = wide ? d.dir! : d.phoneDir!;
  const count = Number(wide ? d.count : d.phoneCount);
  const focus = { x: Number(d.fx ?? 0.5), y: Number(d.fy ?? 0.5) };
  let seq: Seq | null = null;
  let cur = 0;

  // computers: captions fade in and out with the scroll
  const fadeBeats = (p: number) => {
    for (const { el, a, b } of beats) {
      const f = 0.03;
      const v = (a <= 0 ? 1 : smooth(a, a + f, p)) * (b >= 1 ? 1 : 1 - smooth(b - f, b, p));
      el.style.opacity = v.toFixed(3);
      el.style.transform = `translateY(${((1 - v) * 22).toFixed(1)}px)`;
      el.inert = v < 0.5;
    }
  };
  // phones: the caption for the current moment is highlighted in the list under the picture
  const markBeats = (p: number) => {
    let best = beats[0];
    for (const bt of beats) if (p >= bt.a - 0.02) best = bt;
    for (const bt of beats) bt.el.classList.toggle('on', bt === best);
  };

  const start = () => {
    if (seq) return;
    seq = createSeq(canvas, frames(dir, count), focus, reduce ? count - 1 : 0);
    if (reduce) { root.classList.add('static'); return; }
    if (wide) runScroll();
    else runPlay();
  };
  new IntersectionObserver((es, io) => {
    if (es.some((e) => e.isIntersecting)) { start(); io.disconnect(); }
  }, { rootMargin: '150% 0px' }).observe(root);

  function runScroll() {
    let last = performance.now(), active = false, running = false;
    const progress = () => {
      const r = root.getBoundingClientRect();
      const span = r.height - innerHeight;
      return span > 0 ? Math.min(Math.max(-r.top / span, 0), 1) : 0;
    };
    const tick = (now: number) => {
      const dt = Math.min(now - last, 64);
      last = now;
      const target = Math.round(progress() * (count - 1));   // rest on a whole frame: no half-blended ghost when the scroll stops
      cur += (target - cur) * (1 - Math.exp(-dt / 90));
      if (Math.abs(target - cur) < 0.01) cur = target;
      seq!.show(cur);
      fadeBeats(cur / (count - 1));
      if (active || cur !== target) requestAnimationFrame(tick);
      else running = false;
    };
    const kick = () => {
      if (!running) { running = true; last = performance.now(); requestAnimationFrame(tick); }
    };
    new IntersectionObserver((es) => { active = es.some((e) => e.isIntersecting); if (active) kick(); }).observe(root);
    addEventListener('scroll', kick, { passive: true });
    addEventListener('resize', kick);
    kick();
  }

  function runPlay() {
    const dur = Number(d.duration ?? 8000);
    let playing = false;
    const play = () => {
      if (playing) return;
      playing = true;
      root.classList.remove('ended');
      const t0 = performance.now();
      const step = (now: number) => {
        const t = Math.min((now - t0) / dur, 1);
        const e = t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
        cur = e * (count - 1);
        seq!.show(cur);
        markBeats(e);
        if (t < 1) requestAnimationFrame(step);
        else { playing = false; root.classList.add('ended'); }
      };
      requestAnimationFrame(step);
    };
    markBeats(0);
    let played = false;
    new IntersectionObserver((es) => {
      if (!played && es.some((e) => e.intersectionRatio > 0.6)) { played = true; seq!.done.then(play); }
    }, { threshold: [0, 0.6, 1] }).observe(frame);
    replay?.addEventListener('click', play);
  }
}
