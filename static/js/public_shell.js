(function () {
  'use strict';

  // ── TOC scroll-spy ──────────────────────────────────────────────────────
  const tocLinks = Array.from(document.querySelectorAll('.pub-toc-link'));
  if (tocLinks.length) {
    const targetPairs = tocLinks
      .map((link) => {
        const anchor = link.dataset.anchor || link.getAttribute('href');
        try {
          const target = anchor ? document.querySelector(anchor) : null;
          return target ? { link, anchor, target } : null;
        } catch (_) {
          return null;
        }
      })
      .filter(Boolean);
    const targets = targetPairs.map((pair) => pair.target);

    if (targets.length) {
      const setActive = (id) => {
        tocLinks.forEach((link) => {
          const anchor = link.dataset.anchor || link.getAttribute('href');
          link.classList.toggle('is-active', anchor === '#' + id);
        });
      };

      const navOffset = () => {
        const nav = document.querySelector('.pub-topnav');
        return (nav ? nav.getBoundingClientRect().height : 64) + 32;
      };

      const updateActive = () => {
        const offset = navOffset();
        let active = targets[0];

        targets.forEach((target) => {
          if (target.getBoundingClientRect().top <= offset) active = target;
        });

        const doc = document.documentElement;
        const atBottom = window.innerHeight + window.scrollY >= doc.scrollHeight - 4;
        if (atBottom) active = targets[targets.length - 1];
        if (active && active.id) setActive(active.id);
      };

      let ticking = false;
      const queueActiveUpdate = () => {
        if (ticking) return;
        ticking = true;
        window.requestAnimationFrame(() => {
          ticking = false;
          updateActive();
        });
      };

      window.addEventListener('scroll', queueActiveUpdate, { passive: true });
      window.addEventListener('resize', queueActiveUpdate);
      window.addEventListener('hashchange', queueActiveUpdate);
      updateActive();

      // Smooth scroll + immediate active state on click
      tocLinks.forEach((link) => {
        link.addEventListener('click', (e) => {
          const anchor = link.dataset.anchor || link.getAttribute('href');
          if (!anchor || !anchor.startsWith('#')) return;
          const target = document.querySelector(anchor);
          if (!target) return;
          e.preventDefault();
          setActive(anchor.slice(1));
          const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
          const top = target.getBoundingClientRect().top + window.scrollY - navOffset();
          window.scrollTo({ top, behavior: reducedMotion ? 'auto' : 'smooth' });
          if (history.replaceState) history.replaceState(null, '', anchor);
        });
      });
    }
  }

  // ── Public search overlay ───────────────────────────────────────────────
  const overlay = document.getElementById('pub-search-overlay');
  const input = document.getElementById('pub-search-input');
  const body = document.getElementById('pub-search-body');
  const trigger = document.getElementById('pub-search-trigger');

  if (overlay && input && body) {
    let timer = null;
    let activeIdx = -1;
    let flatItems = [];

    const renderHint = (msg) => {
      activeIdx = -1;
      flatItems = [];
      body.innerHTML = `<p class="pub-search-hint">${msg || '输入关键词搜索文档 · 按 Esc 关闭'}</p>`;
    };

    const setOpen = (isOpen) => {
      overlay.hidden = !isOpen;
      overlay.setAttribute('aria-hidden', isOpen ? 'false' : 'true');
      document.body.classList.toggle('pub-search-open', isOpen);
    };

    const open = (event) => {
      if (event) event.preventDefault();
      setOpen(true);
      setTimeout(() => input.focus(), 60);
    };
    const close = () => {
      setOpen(false);
      input.value = '';
      renderHint();
    };

    const renderResults = (groups) => {
      flatItems = [];
      if (!groups || groups.length === 0) {
        body.innerHTML = `<p class="pub-search-empty">未找到匹配的文档</p>`;
        activeIdx = -1;
        return;
      }
      const parts = [];
      groups.forEach((g) => {
        parts.push(
          `<div class="pub-search-group"><div class="pub-search-group-label">${escapeHtml(g.label || '')}</div>`
        );
        g.items.forEach((item) => {
          flatItems.push(item);
          parts.push(
            `<a class="pub-search-result" href="${item.url}" data-idx="${flatItems.length - 1}">
              <strong><span class="pub-search-status pub-search-status--${item.status}"></span>${escapeHtml(item.title)}</strong>
              <small>${item.snippet || ''}</small>
            </a>`
          );
        });
        parts.push('</div>');
      });
      body.innerHTML = parts.join('');
      activeIdx = 0;
      paintActive();
    };

    const paintActive = () => {
      body.querySelectorAll('.pub-search-result').forEach((el) => {
        el.classList.toggle('is-active', Number(el.dataset.idx) === activeIdx);
      });
      const cur = body.querySelector('.pub-search-result.is-active');
      if (cur) cur.scrollIntoView({ block: 'nearest' });
    };

    const escapeHtml = (s) =>
      String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

    const doSearch = async (q) => {
      try {
        const res = await fetch('/search?q=' + encodeURIComponent(q));
        if (!res.ok) throw new Error('search failed');
        const data = await res.json();
        if (input.value.trim() === q) renderResults(data.groups || []);
      } catch (e) {
        console.error(e);
        if (input.value.trim() === q) renderHint('搜索暂时不可用，请稍后重试');
      }
    };

    input.addEventListener('input', () => {
      clearTimeout(timer);
      const q = input.value.trim();
      if (!q) { renderHint(); return; }
      body.innerHTML = `<p class="pub-search-loading">搜索中…</p>`;
      timer = setTimeout(() => doSearch(q), 160);
    });

    input.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown' && flatItems.length) {
        e.preventDefault();
        activeIdx = (activeIdx + 1) % flatItems.length;
        paintActive();
      } else if (e.key === 'ArrowUp' && flatItems.length) {
        e.preventDefault();
        activeIdx = (activeIdx - 1 + flatItems.length) % flatItems.length;
        paintActive();
      } else if (e.key === 'Enter' && flatItems.length) {
        e.preventDefault();
        const item = flatItems[activeIdx >= 0 ? activeIdx : 0];
        if (item) window.location.href = item.url;
      }
    });

    if (trigger) trigger.addEventListener('click', open);
    document.querySelectorAll('[data-open-search]').forEach((el) => el.addEventListener('click', open));
    overlay.querySelectorAll('[data-close]').forEach((el) => el.addEventListener('click', close));

    document.addEventListener('keydown', (e) => {
      const k = e.key.toLowerCase();
      if ((e.metaKey || e.ctrlKey) && k === 'k') {
        e.preventDefault();
        if (overlay.hidden) open(); else close();
      } else if (e.key === 'Escape' && !overlay.hidden) {
        close();
      }
    });

    renderHint();
  }

  // ── Versions drawer (public) ────────────────────────────────────────────
  const drawer = document.getElementById('pub-versions-drawer');
  const scrim = document.getElementById('pub-versions-scrim');
  const openBtn = document.getElementById('btn-pub-versions');
  const closeBtn = document.getElementById('btn-pub-versions-close');

  if (drawer && scrim && openBtn) {
    const open = () => { drawer.hidden = false; scrim.hidden = false; };
    const close = () => { drawer.hidden = true; scrim.hidden = true; };
    openBtn.addEventListener('click', open);
    closeBtn && closeBtn.addEventListener('click', close);
    scrim.addEventListener('click', close);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !drawer.hidden) close();
    });
  }
})();
