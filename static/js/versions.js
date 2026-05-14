'use strict';

/**
 * VersionManager — 版本历史抽屉 + 双栏 Diff + 还原
 *
 * 职责分界：
 * - 抽屉（#version-drawer）管理打开/关闭动画和版本列表渲染
 * - Diff 视图（#diff-view）替换 #doc-body 显示双栏对比
 * - 还原流程：二次确认 modal → POST → 页面刷新
 */
const VersionManager = (() => {
  let docId = '';
  let csrfToken = '';
  let adminDocUrl = '';

  const state = {
    isDrawerOpen: false,
    isDiffMode: false,
    selectedVersionId: null,
    cachedVersions: null, // page-lifetime cache; cleared on restore (page reload)
  };

  // ── 初始化 ────────────────────────────────────────────────────────────────
  function init(options) {
    docId = options.docId || '';
    csrfToken = options.csrfToken || '';
    adminDocUrl = options.adminDocUrl || '';

    // ESC: 优先退出 diff，其次关闭抽屉
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        if (state.isDiffMode) exitDiff();
        else if (state.isDrawerOpen) closeDrawer();
      }
    });
  }

  // ── 抽屉开关 ──────────────────────────────────────────────────────────────
  function toggleDrawer() {
    if (state.isDrawerOpen) closeDrawer();
    else openDrawer();
  }

  function openDrawer() {
    const drawer = document.getElementById('version-drawer');
    const scrim = document.getElementById('version-drawer-scrim');
    if (!drawer) return;

    state.isDrawerOpen = true;
    scrim?.removeAttribute('hidden');
    // 强制 reflow 再加类，保证 transition 触发
    drawer.getBoundingClientRect();
    drawer.classList.add('drawer--open');

    loadVersions();
  }

  function closeDrawer() {
    const drawer = document.getElementById('version-drawer');
    const scrim = document.getElementById('version-drawer-scrim');

    state.isDrawerOpen = false;
    drawer?.classList.remove('drawer--open');
    scrim?.setAttribute('hidden', '');
  }

  // ── 版本列表加载与渲染 ────────────────────────────────────────────────────
  async function loadVersions() {
    const list = document.getElementById('version-list');
    if (!list) return;

    if (state.cachedVersions !== null) {
      renderVersionList(state.cachedVersions);
      return;
    }

    list.innerHTML = '<div class="version-loading">加载中…</div>';

    try {
      const resp = await fetch(`/admin/doc/${docId}/versions/`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      state.cachedVersions = data.versions || [];
      renderVersionList(state.cachedVersions);
    } catch {
      list.innerHTML = '<div class="version-error">加载失败，请刷新重试</div>';
    }
  }

  function renderVersionList(versions) {
    const list = document.getElementById('version-list');
    if (!list) return;

    if (!versions.length) {
      list.innerHTML = '<div class="version-empty">暂无版本记录</div>';
      return;
    }

    list.innerHTML = versions
      .map((v) => {
        const noteText = v.is_auto ? '自动保存' : (v.note || '手动保存');
        const autoClass = v.is_auto ? ' version-item--auto' : '';
        const stats =
          v.added > 0 || v.removed > 0
            ? `<span class="version-item-stats">+${v.added} / -${v.removed}</span>`
            : '';
        // 将 meta 序列化为 data attribute，避免 onclick 内联 JSON 转义问题
        const metaJson = JSON.stringify({ note: noteText, created_at: v.created_at });
        return `
          <button class="version-item${autoClass}"
                  data-vid="${v.id}"
                  data-meta="${metaJson.replace(/"/g, '&quot;')}"
                  onclick="VersionManager._onVersionClick(this)">
            <div class="version-item-header">
              <span class="version-item-note">${noteText}</span>
              <span class="version-item-time">${v.created_at}</span>
            </div>
            <div class="version-item-meta">
              <span>${v.author}</span>${stats}
            </div>
          </button>`;
      })
      .join('');
  }

  // data attribute 方式读取 meta，避免 onclick 内联 JSON 引号问题
  function _onVersionClick(btn) {
    const vid = btn.dataset.vid;
    let meta = {};
    try {
      meta = JSON.parse(btn.dataset.meta);
    } catch {
      // ignore parse errors
    }
    viewDiff(vid, meta);
  }

  // ── Diff 视图 ─────────────────────────────────────────────────────────────
  async function viewDiff(vid, meta) {
    closeDrawer();
    state.selectedVersionId = vid;

    const docBody = document.getElementById('doc-body');
    const diffView = document.getElementById('diff-view');
    if (!diffView) return;

    // 切换主区域到 diff 视图
    state.isDiffMode = true;
    if (docBody) docBody.style.display = 'none';
    diffView.classList.add('diff-view--active');

    // 显示 loading，隐藏列内容
    const loading = document.getElementById('diff-loading');
    const columns = document.getElementById('diff-columns');
    if (loading) loading.style.display = 'flex';
    if (columns) columns.style.display = 'none';

    // 更新标签文字
    const label = document.getElementById('diff-version-label');
    if (label && meta) {
      label.textContent = `对比：${meta.note || '历史版本'} · ${meta.created_at || ''}`;
    }

    // 更新"在新标签打开"链接（指向当前文档管理页）
    const newTabLink = document.getElementById('diff-new-tab-link');
    if (newTabLink) newTabLink.href = adminDocUrl;

    try {
      const resp = await fetch(`/admin/doc/${docId}/versions/${vid}/diff/`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      const leftContent = document.getElementById('diff-left-content');
      const rightContent = document.getElementById('diff-right-content');
      if (leftContent) leftContent.innerHTML = data.left_html || '';
      if (rightContent) rightContent.innerHTML = data.right_html || '';

      if (loading) loading.style.display = 'none';
      if (columns) columns.style.display = 'grid';
    } catch {
      if (loading) {
        loading.textContent = '加载对比数据失败，请重试';
      }
    }
  }

  function exitDiff() {
    state.isDiffMode = false;
    state.selectedVersionId = null;

    const docBody = document.getElementById('doc-body');
    const diffView = document.getElementById('diff-view');
    if (docBody) docBody.style.display = '';
    diffView?.classList.remove('diff-view--active');

    // 清空 diff 内容，释放内存
    const leftContent = document.getElementById('diff-left-content');
    const rightContent = document.getElementById('diff-right-content');
    if (leftContent) leftContent.innerHTML = '';
    if (rightContent) rightContent.innerHTML = '';
  }

  // ── 还原确认 ──────────────────────────────────────────────────────────────
  function showRestoreConfirm() {
    if (!state.selectedVersionId) return;
    document.getElementById('restore-confirm-modal')?.removeAttribute('hidden');
  }

  function hideRestoreConfirm() {
    document.getElementById('restore-confirm-modal')?.setAttribute('hidden', '');
  }

  async function confirmRestore() {
    if (!state.selectedVersionId) return;
    hideRestoreConfirm();

    try {
      const resp = await fetch(
        `/admin/doc/${docId}/versions/${state.selectedVersionId}/restore/`,
        {
          method: 'POST',
          headers: { 'X-CSRFToken': csrfToken },
        },
      );
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      if (data.ok) {
        window.location.reload();
      }
    } catch {
      // 复用 EditorManager 的 toast（两个脚本共存于同一页面）
      if (typeof EditorManager !== 'undefined') {
        EditorManager.showToast('还原失败，请重试', true);
      }
    }
  }

  // ── 公开 API ──────────────────────────────────────────────────────────────
  return {
    init,
    toggleDrawer,
    openDrawer,
    closeDrawer,
    viewDiff,
    exitDiff,
    showRestoreConfirm,
    hideRestoreConfirm,
    confirmRestore,
    _onVersionClick, // 内部使用，由渲染的 HTML 调用
  };
})();
