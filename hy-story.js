/* 編織日和・故事｜GA4 標準追蹤（所有故事互動頁共用）
 *
 * 用法：<head> 裡依序放
 *   1. GA4 載入碼（config 要有 cookie_domain: '.knittinghiyori.com'）
 *   2. <script src="/hy-story.js"></script>
 *
 * story_id 預設用作品資料夾名稱，略過類別資料夾（例如 /drama/hidden-love/ → hidden-love），
 * 要自訂就在它前面寫 <script>var HY_STORY_ID = '…';</script>
 *
 * 自動送出的標準事件：
 *   story_start / story_progress(25,50,75,100) / section_view / interaction /
 *   story_complete / cta_click（元素加 data-cta）/ story_exit
 * 首頁（網址是 / ）只送 cta_click，不送故事事件。
 *
 * 頁面自己的互動也可以直接呼叫：
 *   hyInteract(type, id, index)、hySection(id, index)、hyComplete()
 */
(function () {
  if (window.__hyStoryLoaded) return;
  window.__hyStoryLoaded = true;

  var seg = location.pathname.split('/').filter(Boolean);
  if (/^(books|drama|comics)$/.test(seg[0] || '')) seg.shift();
  var STORY_ID = window.HY_STORY_ID || seg[0] || 'home';
  var IS_HUB = STORY_ID === 'home';
  var LANG = window.HY_PAGE_LANG || document.documentElement.lang || 'zh-Hant';

  window.dataLayer = window.dataLayer || [];
  if (typeof window.gtag !== 'function') {
    window.gtag = function () { window.dataLayer.push(arguments); };
  }
  gtag('set', {
    story_id: STORY_ID,
    page_lang: LANG,
    content_group: IS_HUB ? 'story-hub' : 'interactive-story'
  });

  var started = false, completed = false, interactions = 0, maxScroll = 0;
  var seenSections = {}, marks = { 25: false, 50: false, 75: false, 100: false };

  window.hyEvent = function (name, params) {
    var p = params || {};
    p.story_id = STORY_ID;
    gtag('event', name, p);
  };

  // 首頁點擊（作品卡片、data-cta 連結）
  document.addEventListener('click', function (e) {
    if (!e.target.closest) return;
    var el = e.target.closest('[data-cta]');
    if (!el && IS_HUB) {
      var card = e.target.closest('a.card, a.pola');
      if (card) {
        var li = card.closest('li');
        hyEvent('cta_click', {
          cta_id: (li && li.id) || card.getAttribute('href'),
          cta_type: 'story_card',
          link_url: card.getAttribute('href') || ''
        });
      }
      return;
    }
    if (!el) return;
    hyEvent('cta_click', {
      cta_id: el.getAttribute('data-cta'),
      cta_type: el.getAttribute('data-cta-type') || 'article',
      link_url: el.getAttribute('href') || ''
    });
  }, true);

  if (IS_HUB) return;

  window.hyStart = function (entryPoint) {
    if (started) return;
    started = true;
    hyEvent('story_start', { entry_point: entryPoint || 'scroll' });
  };

  window.hyInteract = function (type, id, index) {
    hyStart('interaction');
    interactions++;
    hyEvent('interaction', {
      interaction_type: type,
      interaction_id: id,
      interaction_index: (typeof index === 'number') ? index : interactions
    });
  };

  window.hySection = function (sectionId, sectionIndex) {
    if (seenSections[sectionId]) return;
    seenSections[sectionId] = true;
    hyEvent('section_view', { section_id: sectionId, section_index: Number(sectionIndex) || 0 });
  };

  window.hyComplete = function () {
    if (completed) return;
    completed = true;
    hyEvent('story_complete', { interactions_count: interactions, max_scroll: maxScroll });
  };

  function trackScroll() {
    var doc = document.documentElement;
    var h = doc.scrollHeight - window.innerHeight;
    var pct = h > 0 ? Math.round((window.scrollY / h) * 100) : 100;
    if (pct > maxScroll) maxScroll = Math.min(pct, 100);
    if (maxScroll > 5) hyStart('scroll');
    [25, 50, 75, 100].forEach(function (m) {
      if (!marks[m] && maxScroll >= m) {
        marks[m] = true;
        hyEvent('story_progress', { percent_scrolled: m });
      }
    });
    if (maxScroll >= 95) hyComplete();
  }
  window.addEventListener('scroll', trackScroll, { passive: true });
  window.addEventListener('load', trackScroll);

  // 互動：按鈕、滑桿、展開等（連結 CTA 不算）
  var INTERACTIVE = 'button, [role="button"], summary, input, select, textarea, [data-interact]';
  document.addEventListener('click', function (e) {
    if (!e.target.closest) return;
    var el = e.target.closest(INTERACTIVE);
    if (!el || el.closest('[data-cta]')) return;
    var id = el.getAttribute('data-interact') || el.id ||
             (el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 40) ||
             el.tagName.toLowerCase();
    hyInteract('click', id);
  }, true);

  // 段落：有 data-sec 的元素優先，沒有就用 <section>
  function observeSections() {
    if (!('IntersectionObserver' in window)) return;
    var list = document.querySelectorAll('[data-sec]');
    if (!list.length) list = document.querySelectorAll('section');
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var el = en.target;
        hySection(el.getAttribute('data-sec') || el.id || ('section_' + el.__hyIndex), el.__hyIndex);
        io.unobserve(el);
      });
    }, { threshold: 0.4 });
    for (var i = 0; i < list.length; i++) { list[i].__hyIndex = i + 1; io.observe(list[i]); }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', observeSections);
  else observeSections();

  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') {
      hyEvent('story_exit', { interactions_count: interactions, max_scroll: maxScroll });
    }
  });
})();
