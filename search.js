// ヒロラボ — クライアントサイド検索
// 使い方: ナビゲーションの 🔍 ボタンをクリックで開く
(function () {
  'use strict';

  var INDEX_URL = 'search-index.json';
  var indexCache = null;
  var modalEl = null;
  var inputEl = null;
  var resultsEl = null;
  var lastFocus = null;

  // ====== インデックス読み込み ======
  function loadIndex() {
    if (indexCache) return Promise.resolve(indexCache);
    return fetch(INDEX_URL, { cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(function (data) { indexCache = data; return data; })
      .catch(function () { return { items: [] }; });
  }

  // ====== モーダル作成 ======
  function ensureModal() {
    if (modalEl) return;
    modalEl = document.createElement('div');
    modalEl.className = 'search-modal';
    modalEl.setAttribute('role', 'dialog');
    modalEl.setAttribute('aria-modal', 'true');
    modalEl.setAttribute('aria-label', 'サイト内検索');
    modalEl.hidden = true;
    modalEl.innerHTML = [
      '<div class="search-modal__backdrop" data-close></div>',
      '<div class="search-modal__panel">',
      '  <div class="search-modal__header">',
      '    <span class="search-modal__icon">🔍</span>',
      '    <input type="search" class="search-modal__input" placeholder="記事・タグ・ページを検索..." aria-label="検索">',
      '    <button class="search-modal__close" data-close aria-label="閉じる">✕</button>',
      '  </div>',
      '  <div class="search-modal__results" aria-live="polite"></div>',
      '  <div class="search-modal__hint">↑↓ で移動 · Enter で開く · Esc で閉じる</div>',
      '</div>'
    ].join('');
    document.body.appendChild(modalEl);

    inputEl = modalEl.querySelector('.search-modal__input');
    resultsEl = modalEl.querySelector('.search-modal__results');

    // Close handlers
    modalEl.querySelectorAll('[data-close]').forEach(function (el) {
      el.addEventListener('click', closeModal);
    });

    // Input
    inputEl.addEventListener('input', onInput);
    inputEl.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        moveSelection(e.key === 'ArrowDown' ? 1 : -1);
      } else if (e.key === 'Enter') {
        var sel = resultsEl.querySelector('.search-result.is-selected');
        if (sel) { e.preventDefault(); sel.click(); }
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !modalEl.hidden) closeModal();
    });
  }

  // ====== 開く / 閉じる ======
  function openModal() {
    ensureModal();
    lastFocus = document.activeElement;
    modalEl.hidden = false;
    document.body.style.overflow = 'hidden';
    loadIndex().then(function () { inputEl.focus(); });
  }
  function closeModal() {
    if (!modalEl) return;
    modalEl.hidden = true;
    document.body.style.overflow = '';
    inputEl.value = '';
    resultsEl.innerHTML = '';
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  // ====== 検索ロジック ======
  function onInput() {
    var q = inputEl.value.trim().toLowerCase();
    if (!q) { resultsEl.innerHTML = ''; return; }
    if (!indexCache) return;
    var results = indexCache.items
      .map(function (item) { return { item: item, score: score(item, q) }; })
      .filter(function (r) { return r.score > 0; })
      .sort(function (a, b) { return b.score - a.score; })
      .slice(0, 10);
    render(results);
  }

  function score(item, q) {
    var title = (item.title || '').toLowerCase();
    var excerpt = (item.excerpt || '').toLowerCase();
    var category = (item.category || '').toLowerCase();
    var tags = (item.tags || []).join(' ').toLowerCase();
    var url = (item.url || '').toLowerCase();
    var s = 0;
    if (title.indexOf(q) >= 0) s += 10;
    if (title.toLowerCase().indexOf(q) === 0) s += 5;
    if (tags.indexOf(q) >= 0) s += 6;
    if (category.toLowerCase().indexOf(q) >= 0) s += 3;
    if (excerpt.indexOf(q) >= 0) s += 2;
    if (url.indexOf(q) >= 0) s += 1;
    return s;
  }

  function render(results) {
    if (!results.length) {
      resultsEl.innerHTML = '<div class="search-empty">該当する記事がありません。<br>キーワードを変えてみてください。</div>';
      return;
    }
    resultsEl.innerHTML = results.map(function (r, i) {
      var it = r.item;
      return [
        '<a class="search-result', i === 0 ? ' is-selected' : '', '" href="', it.url, '">',
        '  <div class="search-result__title">', escapeHtml(it.title), '</div>',
        '  <div class="search-result__meta"><span class="search-result__cat">', escapeHtml(it.category || ''), '</span></div>',
        '  <div class="search-result__excerpt">', escapeHtml(it.excerpt || ''), '</div>',
        '</a>'
      ].join('');
    }).join('');
  }

  function moveSelection(d) {
    var items = resultsEl.querySelectorAll('.search-result');
    if (!items.length) return;
    var cur = resultsEl.querySelector('.search-result.is-selected');
    var idx = Array.prototype.indexOf.call(items, cur);
    var next = idx + d;
    if (next < 0) next = items.length - 1;
    if (next >= items.length) next = 0;
    items.forEach(function (el) { el.classList.remove('is-selected'); });
    items[next].classList.add('is-selected');
    items[next].scrollIntoView({ block: 'nearest' });
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  // ====== 起動 ======
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.search-toggle').forEach(function (btn) {
      btn.addEventListener('click', openModal);
    });

    // Cmd/Ctrl + K でも開く
    document.addEventListener('keydown', function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        openModal();
      }
    });
  });
})();
