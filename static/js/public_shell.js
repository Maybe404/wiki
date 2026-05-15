(function () {
  'use strict';

  // ── TOC scroll-spy ──────────────────────────────────────────────────────
  const tocLinks = Array.from(document.querySelectorAll('.pub-toc-link'));
  if (tocLinks.length) {
    const targets = tocLinks
      .map((link) => {
        const sel = link.dataset.anchor;
        return sel ? document.querySelector(sel) : null;
      })
      .filter(Boolean);

    if (targets.length) {
      const setActive = (id) => {
        tocLinks.forEach((link) => {
          const anchor = link.dataset.anchor || link.getAttribute('href');
          link.classList.toggle('is-active', anchor === '#' + id);
        });
      };

      const observer = new IntersectionObserver(
        (entries) => {
          const visible = entries
            .filter((e) => e.isIntersecting)
            .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
          if (visible && visible.target.id) setActive(visible.target.id);
        },
        { rootMargin: '-24% 0px -62% 0px', threshold: [0.1, 0.3, 0.6] }
      );

      targets.forEach((t) => observer.observe(t));
    }
  }

  // ── Versions drawer (public) ────────────────────────────────────────────
  const drawer = document.getElementById('pub-versions-drawer');
  const scrim = document.getElementById('pub-versions-scrim');
  const openBtn = document.getElementById('btn-pub-versions');
  const closeBtn = document.getElementById('btn-pub-versions-close');

  if (drawer && scrim && openBtn) {
    const open = () => {
      drawer.hidden = false;
      scrim.hidden = false;
    };
    const close = () => {
      drawer.hidden = true;
      scrim.hidden = true;
    };
    openBtn.addEventListener('click', open);
    closeBtn && closeBtn.addEventListener('click', close);
    scrim.addEventListener('click', close);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !drawer.hidden) close();
    });
  }
})();
