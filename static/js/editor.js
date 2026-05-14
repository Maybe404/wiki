'use strict';

/**
 * EditorManager — 就地编辑器
 *
 * 边界保护策略：
 * 1. 只对 [data-editable] 元素设 contenteditable="true"，其余保持不可编辑默认状态。
 *    浏览器本身把光标锁在 contenteditable 边界内，这是最可靠的结构保护。
 * 2. MutationObserver 作为安全网：若检测到 [data-editable] 外部的 DOM 变动（拖拽等
 *    极端 case），立即从快照恢复。
 * 3. paste 事件强制纯文本。
 * 4. Enter 键拦截为 insertLineBreak（<br>），阻止浏览器创建新块元素。
 * 5. Backspace/Delete 在可编辑块边界处阻止删除父结构。
 * 6. IME（中文输入法）：compositionstart/end 维护 isComposing 标志，
 *    输入法候选词确认期间不触发自动保存也不拦截 Enter。
 */
const EditorManager = (() => {
  // ── 状态 ──────────────────────────────────────────────────────────────────
  let editing = false;
  let dirty = false;
  let isComposing = false;
  let autosaveTimer = null;
  let observer = null;
  let snapshot = new Map(); // editable-id → innerHTML 快照

  // 配置（由 init() 注入）
  let docId = '';
  let csrfToken = '';

  // DOM 引用
  let docContent = null;   // #doc-content
  let toolbar = null;      // #editor-toolbar
  let editableEls = [];    // [data-editable] NodeList 快照

  // 每个 editable 元素对应的 AbortController（用于清理事件监听）
  let abortControllers = [];

  // ── 初始化 ────────────────────────────────────────────────────────────────
  function init(options) {
    docId = options.docId || '';
    csrfToken = options.csrfToken || '';
    toolbar = document.getElementById('editor-toolbar');

    // ⌘S / Ctrl+S
    document.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's' && editing) {
        e.preventDefault();
        showVersionNoteModal();
      }
    });

    // beforeunload — 有未保存改动时拦截离开
    window.addEventListener('beforeunload', (e) => {
      if (dirty) {
        e.preventDefault();
        // returnValue 在现代浏览器会被忽略，但需要赋值才触发对话框
        e.returnValue = '';
      }
    });
  }

  // ── 进入编辑模式 ──────────────────────────────────────────────────────────
  function enterEditMode() {
    if (editing) return;

    docContent = document.getElementById('doc-content');
    if (!docContent) {
      showToast('无可编辑内容', true);
      return;
    }

    editing = true;
    document.body.classList.add('editing-mode');

    // 收集所有 data-editable 元素
    editableEls = Array.from(docContent.querySelectorAll('[data-editable]'));

    // 为每个可编辑元素开启 contenteditable 并绑定处理器
    abortControllers = editableEls.map((el) => {
      el.setAttribute('contenteditable', 'true');
      el.setAttribute('spellcheck', 'false');
      const ctrl = new AbortController();
      attachHandlers(el, ctrl.signal);
      return ctrl;
    });

    // 拍快照（用于 MutationObserver 恢复）
    captureSnapshot();

    // 工具栏滑下
    if (toolbar) {
      toolbar.classList.add('toolbar--visible');
      toolbar.removeAttribute('aria-hidden');
    }

    // 切换按钮显示
    const btnEdit = document.getElementById('btn-edit');
    const btnExit = document.getElementById('btn-exit-edit');
    if (btnEdit) btnEdit.style.display = 'none';
    if (btnExit) btnExit.style.display = '';

    // 启动 MutationObserver 安全网
    setupObserver();
  }

  // ── 退出编辑模式 ──────────────────────────────────────────────────────────
  function exitEditMode() {
    if (!editing) return;

    if (dirty) {
      const ok = window.confirm('有未保存的改动，确认离开？未保存内容将丢失。');
      if (!ok) return;
    }

    // 断开 Observer
    if (observer) {
      observer.disconnect();
      observer = null;
    }

    // 移除所有事件监听
    abortControllers.forEach((ctrl) => ctrl.abort());
    abortControllers = [];

    // 清除 contenteditable
    editableEls.forEach((el) => {
      el.removeAttribute('contenteditable');
      el.removeAttribute('spellcheck');
    });
    editableEls = [];
    snapshot.clear();

    // 工具栏收起
    if (toolbar) {
      toolbar.classList.remove('toolbar--visible');
      toolbar.setAttribute('aria-hidden', 'true');
    }

    // 切换按钮
    const btnEdit = document.getElementById('btn-edit');
    const btnExit = document.getElementById('btn-exit-edit');
    if (btnEdit) btnEdit.style.display = '';
    if (btnExit) btnExit.style.display = 'none';

    document.body.classList.remove('editing-mode');
    dirty = false;
    clearTimeout(autosaveTimer);
    editing = false;
  }

  // ── 为单个 editable 元素绑定处理器 ───────────────────────────────────────
  function attachHandlers(el, signal) {
    const opts = { signal };

    // IME 组合输入状态跟踪
    el.addEventListener('compositionstart', () => {
      isComposing = true;
    }, opts);

    el.addEventListener('compositionend', () => {
      isComposing = false;
      markDirty();
    }, opts);

    // 输入事件 → 标记 dirty + 触发自动保存倒计时
    el.addEventListener('input', () => {
      if (isComposing) return; // 等待 compositionend
      markDirty();
    }, opts);

    // 粘贴 → 强制纯文本
    el.addEventListener('paste', (e) => {
      e.preventDefault();
      const text = (e.clipboardData || window.clipboardData)?.getData('text/plain') ?? '';
      // insertText 保持撤销历史
      document.execCommand('insertText', false, text);
    }, opts);

    // 键盘拦截
    el.addEventListener('keydown', (e) => {
      // IME 确认过程中不干预（避免吃掉候选词的 Enter）
      if (isComposing) return;

      // Enter → insertLineBreak（<br>），阻止浏览器创建 <div>/<p>
      if (e.key === 'Enter') {
        e.preventDefault();
        document.execCommand('insertLineBreak');
        return;
      }

      // Backspace 在首位置 → 阻止删除父元素内容
      if (e.key === 'Backspace' && !e.metaKey && !e.ctrlKey && !e.altKey) {
        if (isCursorAtStart(el)) {
          e.preventDefault();
        }
        return;
      }

      // Delete 在末位置 → 阻止删越边界
      if (e.key === 'Delete' && !e.metaKey && !e.ctrlKey && !e.altKey) {
        if (isCursorAtEnd(el)) {
          e.preventDefault();
        }
      }
    }, opts);

    // 阻止拖拽到非 editable 区域
    el.addEventListener('dragover', (e) => e.preventDefault(), opts);
    el.addEventListener('drop', (e) => {
      // 只允许在同一个 editable 内部的纯文本拖拽
      const targetEditable = e.target.closest('[data-editable]');
      if (!targetEditable) {
        e.preventDefault();
        return;
      }
      // 纯文本化
      e.preventDefault();
      const text = e.dataTransfer?.getData('text/plain') ?? '';
      if (text) document.execCommand('insertText', false, text);
    }, opts);
  }

  // ── MutationObserver 安全网 ───────────────────────────────────────────────
  function captureSnapshot() {
    snapshot.clear();
    editableEls.forEach((el) => {
      const id = el.dataset.editableId || el.dataset.editable || String(Math.random());
      snapshot.set(id, el.innerHTML);
    });
  }

  function setupObserver() {
    if (!docContent) return;

    observer = new MutationObserver((mutations) => {
      const hasUnauthorized = mutations.some((m) => {
        const target = m.target;
        // TextNode 用 parentElement 代替
        const el = target.nodeType === Node.ELEMENT_NODE
          ? target
          : target.parentElement;
        return !el || !el.closest('[data-editable]');
      });

      if (hasUnauthorized) {
        // 断开 → 从快照恢复 → 重连
        observer.disconnect();
        restoreFromSnapshot();
        observer.observe(docContent, observeOpts);
      }
    });

    const observeOpts = { childList: true, subtree: true, characterData: true };
    observer.observe(docContent, observeOpts);
  }

  function restoreFromSnapshot() {
    editableEls.forEach((el) => {
      const id = el.dataset.editableId || el.dataset.editable;
      const saved = snapshot.get(id);
      if (saved !== undefined) el.innerHTML = saved;
    });
  }

  // ── 光标位置工具 ──────────────────────────────────────────────────────────
  function isCursorAtStart(el) {
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0 || !sel.isCollapsed) return false;
    const range = sel.getRangeAt(0);

    // 创建从 el 起点到光标的 range，看其字符长度
    const checkRange = document.createRange();
    checkRange.selectNodeContents(el);
    checkRange.setEnd(range.startContainer, range.startOffset);
    return checkRange.toString().length === 0;
  }

  function isCursorAtEnd(el) {
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0 || !sel.isCollapsed) return false;
    const range = sel.getRangeAt(0);

    const checkRange = document.createRange();
    checkRange.selectNodeContents(el);
    checkRange.setStart(range.endContainer, range.endOffset);
    return checkRange.toString().length === 0;
  }

  // ── 自动保存 ──────────────────────────────────────────────────────────────
  function markDirty() {
    dirty = true;
    clearTimeout(autosaveTimer);
    autosaveTimer = setTimeout(() => {
      if (editing && !isComposing) {
        save(true, '');
      }
    }, 3000);
  }

  // ── 收集可编辑块 ──────────────────────────────────────────────────────────
  function collectBlocks() {
    const blocks = {};
    editableEls.forEach((el) => {
      const id = el.dataset.editableId;
      if (id) blocks[id] = el.innerHTML;
    });
    return blocks;
  }

  // ── 保存到服务端 ──────────────────────────────────────────────────────────
  async function save(isAuto, note) {
    if (!editing || !docId) return;

    const blocks = collectBlocks();

    try {
      const resp = await fetch(`/admin/doc/${docId}/save/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ editable_blocks: blocks, note, is_auto: isAuto }),
      });

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        showToast(`保存失败：${data.error || resp.status}`, true);
        return;
      }

      const data = await resp.json();
      dirty = false;
      // 取消挂起的自动保存定时器，避免保存成功后立即再触发一次冗余写入
      clearTimeout(autosaveTimer);
      captureSnapshot();
      const label = isAuto ? `自动保存 · ${data.saved_at}` : `已保存 · ${data.saved_at}`;
      showToast(label);
    } catch {
      showToast('保存失败，请检查网络', true);
    }
  }

  // ── 版本说明 Modal ────────────────────────────────────────────────────────
  function showVersionNoteModal() {
    if (!editing) return;
    const modal = document.getElementById('version-note-modal');
    const input = document.getElementById('version-note-input');
    if (!modal) return;
    modal.removeAttribute('hidden');
    if (input) {
      input.value = '';
      input.focus();
      // Enter 键在 input 里直接确认
      input.onkeydown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          confirmSaveWithNote();
        }
        if (e.key === 'Escape') hideVersionNoteModal();
      };
    }
  }

  function hideVersionNoteModal() {
    const modal = document.getElementById('version-note-modal');
    if (modal) modal.setAttribute('hidden', '');
  }

  function confirmSaveWithNote() {
    const input = document.getElementById('version-note-input');
    const note = (input?.value || '').trim() || '手动保存';
    hideVersionNoteModal();
    save(false, note);
  }

  // ── 工具栏命令 ────────────────────────────────────────────────────────────
  function execCmd(cmd) {
    document.execCommand(cmd, false, null);
  }

  function insertLink() {
    const url = window.prompt('输入链接地址（包含 https://）：');
    if (url && /^https?:\/\//i.test(url)) {
      document.execCommand('createLink', false, url);
      // 为新创建的 <a> 补充 rel="noopener"
      const sel = window.getSelection();
      if (sel && sel.anchorNode) {
        const a = sel.anchorNode.parentElement?.closest('a');
        if (a) a.setAttribute('rel', 'noopener noreferrer');
      }
    } else if (url !== null) {
      showToast('链接地址无效，请以 https:// 开头', true);
    }
  }

  // ── Toast ─────────────────────────────────────────────────────────────────
  function showToast(msg, isError = false) {
    // 移除已有 toast（避免堆叠）
    document.querySelectorAll('.editor-toast').forEach((t) => t.remove());

    const toast = document.createElement('div');
    toast.className = 'editor-toast' + (isError ? ' editor-toast--error' : '');
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');

    const text = document.createTextNode(msg);
    toast.appendChild(text);

    if (isError) {
      const retry = document.createElement('button');
      retry.className = 'editor-toast-retry';
      retry.textContent = '重试';
      retry.addEventListener('click', () => {
        toast.remove();
        save(false, '手动保存');
      });
      toast.appendChild(retry);
    }

    document.body.appendChild(toast);

    // 强制 reflow 再加 visible 类，触发 transition
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        toast.classList.add('editor-toast--visible');
      });
    });

    setTimeout(() => {
      toast.classList.remove('editor-toast--visible');
      setTimeout(() => toast.remove(), 400);
    }, 2500);
  }

  // ── 公开 API ─────────────────────────────────────────────────────────────
  return {
    init,
    enterEditMode,
    exitEditMode,
    save,
    execCmd,
    insertLink,
    showVersionNoteModal,
    hideVersionNoteModal,
    confirmSaveWithNote,
    isEditing: () => editing,
    isDirty: () => dirty,
  };
})();
