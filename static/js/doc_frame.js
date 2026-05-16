(function () {
  'use strict';

  const MIN_HEIGHT = 200;
  const MAX_HEIGHT = 50000;
  const frames = Array.from(document.querySelectorAll('iframe[data-doc-frame]'));

  if (!frames.length) return;

  window.addEventListener('message', (event) => {
    const frame = frames.find((candidate) => candidate.contentWindow === event.source);
    if (!frame) return;

    const data = event.data;
    if (!data || data.type !== 'atlas-doc-resize') return;

    const nextHeight = Number(data.height);
    if (!Number.isFinite(nextHeight)) return;

    const clamped = Math.min(MAX_HEIGHT, Math.max(MIN_HEIGHT, Math.ceil(nextHeight)));
    frame.style.height = `${clamped}px`;
  });
})();
