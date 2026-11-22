// PROTOTYPE: start a hero only once its variant is visible (hidden variants have no size), and
// replay it each time the variant is shown again.
type Api = { replay?: () => void };

export function whenShown(key: string, el: HTMLElement, start: () => Api) {
  let api: Api | null = null;
  const tryStart = () => {
    if (api || el.offsetParent === null) return;
    try {
      api = start();
    } catch (e) {
      console.error(e);
      el.classList.add('no-gl');
      api = {};
    }
  };
  tryStart();
  window.addEventListener('variant:shown', (e) => {
    if ((e as CustomEvent).detail !== key) return;
    if (api) api.replay?.();
    else requestAnimationFrame(tryStart);
  });
  return () => api;
}
