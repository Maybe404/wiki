/**
 * PublishManager — 发布/撤回抽屉控制器
 *
 * 依赖：doc_detail.html 中的 #publish-drawer、#unpublish-drawer 等 DOM 元素。
 * 初始化：PublishManager.init({ docId, csrfToken, currentSlug })
 */
const PublishManager = (() => {
  let _docId = '';
  let _csrfToken = '';
  let _currentSlug = '';

  // ── DOM refs ──────────────────────────────────────────────────────────────

  const $ = (id) => document.getElementById(id);

  // ── Init ──────────────────────────────────────────────────────────────────

  function init({ docId, csrfToken, currentSlug }) {
    _docId = docId;
    _csrfToken = csrfToken;
    _currentSlug = currentSlug;
  }

  // ── Publish drawer ────────────────────────────────────────────────────────

  function openPublishDrawer() {
    const input = $('publish-slug-input');
    input.value = _currentSlug;
    _updateUrlPreview(_currentSlug);
    _clearPublishError();
    $('publish-drawer-scrim').removeAttribute('hidden');
    $('publish-drawer').classList.add('drawer--open');
    // Focus input after transition starts
    setTimeout(() => input.focus(), 60);
  }

  function closePublishDrawer() {
    $('publish-drawer').classList.remove('drawer--open');
    $('publish-drawer-scrim').setAttribute('hidden', '');
    _resetPublishBtn();
  }

  function onSlugInput(e) {
    _updateUrlPreview(e.target.value.trim());
    _clearPublishError();
  }

  function _updateUrlPreview(slug) {
    const el = $('publish-url-preview');
    if (el) el.textContent = slug ? `/d/${slug}/` : '/d/…/';
  }

  function _clearPublishError() {
    const el = $('publish-error');
    if (el) el.textContent = '';
  }

  function _resetPublishBtn() {
    const btn = $('publish-confirm-btn');
    if (btn) { btn.disabled = false; btn.textContent = '确认发布'; }
  }

  async function confirmPublish() {
    const input = $('publish-slug-input');
    const slug = input.value.trim();
    const btn = $('publish-confirm-btn');
    const errEl = $('publish-error');

    if (!slug) {
      errEl.textContent = 'slug 不能为空';
      input.focus();
      return;
    }

    btn.disabled = true;
    btn.textContent = '发布中…';
    errEl.textContent = '';

    try {
      const resp = await fetch(`/admin/doc/${_docId}/publish/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': _csrfToken },
        body: JSON.stringify({ slug }),
      });
      const data = await resp.json();
      if (data.ok) {
        window.location.reload();
      } else {
        errEl.textContent = data.error || '发布失败，请重试';
        _resetPublishBtn();
      }
    } catch {
      errEl.textContent = '网络错误，请重试';
      _resetPublishBtn();
    }
  }

  // ── Unpublish drawer ──────────────────────────────────────────────────────

  function openUnpublishDrawer() {
    $('unpublish-drawer-scrim').removeAttribute('hidden');
    $('unpublish-drawer').classList.add('drawer--open');
  }

  function closeUnpublishDrawer() {
    $('unpublish-drawer').classList.remove('drawer--open');
    $('unpublish-drawer-scrim').setAttribute('hidden', '');
    _resetUnpublishBtn();
  }

  function _resetUnpublishBtn() {
    const btn = $('unpublish-confirm-btn');
    if (btn) { btn.disabled = false; btn.textContent = '确认撤回'; }
  }

  async function confirmUnpublish() {
    const btn = $('unpublish-confirm-btn');
    btn.disabled = true;
    btn.textContent = '撤回中…';

    try {
      const resp = await fetch(`/admin/doc/${_docId}/unpublish/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': _csrfToken },
        body: '{}',
      });
      const data = await resp.json();
      if (data.ok) {
        window.location.reload();
      } else {
        closeUnpublishDrawer();
        // Reuse the editor toast for error feedback
        if (typeof EditorManager !== 'undefined' && EditorManager.showToast) {
          EditorManager.showToast(data.error || '撤回失败', true);
        }
        _resetUnpublishBtn();
      }
    } catch {
      closeUnpublishDrawer();
      _resetUnpublishBtn();
    }
  }

  // ── Keyboard ──────────────────────────────────────────────────────────────

  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    const publishOpen = $('publish-drawer')?.classList.contains('drawer--open');
    const unpublishOpen = $('unpublish-drawer')?.classList.contains('drawer--open');
    if (publishOpen) closePublishDrawer();
    if (unpublishOpen) closeUnpublishDrawer();
  });

  // ── Public API ────────────────────────────────────────────────────────────

  return {
    init,
    openPublishDrawer,
    closePublishDrawer,
    onSlugInput,
    confirmPublish,
    openUnpublishDrawer,
    closeUnpublishDrawer,
    confirmUnpublish,
  };
})();
