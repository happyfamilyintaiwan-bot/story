/* 編織日和・追劇日曆計算機（story /drama/calendar/）
 *
 * 資料：同資料夾的 dramas.json（一部劇一筆，格式見 100_Todo/projects/2026-10-25_追劇日曆計算機-設計文件.md §3）
 * 頁面語言：<html lang> 決定（zh-Hant-TW／en／ja），介面文字在下面的 T。
 * 網址：?d=<劇代號>&p=<平台代號>；自己輸入的結果放在 #m=…（不送伺服器）。
 * 追蹤：按鈕與選單都有 data-interact，由 /hy-story.js 自動送 interaction；這裡不另外送事件。
 */
(function () {
  'use strict';

  var TOOL_URL = 'https://story.knittinghiyori.com/drama/calendar/';
  var DAY = 86400000;

  // ---------- 日期工具（一律用 UTC 算，避免時區把日期推前推後） ----------
  function toMs(s) { var a = s.split('-'); return Date.UTC(+a[0], a[1] - 1, +a[2]); }
  function toStr(ms) { return new Date(ms).toISOString().slice(0, 10); }
  function addDays(s, n) { return toStr(toMs(s) + n * DAY); }
  function weekday(s) { return new Date(toMs(s)).getUTCDay(); }
  function diffDays(a, b) { return Math.round((toMs(b) - toMs(a)) / DAY); }
  function localToday() {
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }

  // ---------- 計算 ----------
  function rateOn(rule, day) {
    if (!rule) return 0;
    if (rule.days && rule.days.indexOf(weekday(day)) < 0) return 0;
    return rule.perDay || 0;
  }

  // 回傳 { days: [{date, from, to, est}], finale: 'YYYY-MM-DD' 或 null }
  function schedule(drama, pid, memo) {
    memo = memo || {};
    if (memo[pid]) return memo[pid];
    var plat = findPlatform(drama, pid);
    var total = drama.episodes;
    var skip = drama.skip || [];
    var out = [];
    var res;

    if (plat.sameAs) {
      var base = schedule(drama, plat.sameAs, memo);
      var basePlat = findPlatform(drama, plat.sameAs);
      var lag = plat.lagDays || 0, behind = plat.behindEps || 0, prev = 0, last = null;
      base.days.forEach(function (b) {
        var cum = Math.max(0, b.to - behind);
        last = addDays(b.date, lag);
        if (cum > prev) { out.push({ date: last, from: prev + 1, to: cum, est: b.est || !!plat.guess }); prev = cum; }
      });
      // 比基準平台慢幾集：基準播完後，照官方排完後的速度補完
      var tail = basePlat.after || basePlat.phases[basePlat.phases.length - 1];
      var day = last, guard = 0;
      while (prev < total && day && guard++ < 400) {
        day = addDays(day, 1);
        var r = skip.indexOf(day) >= 0 ? 0 : rateOn(tail, day);
        if (r > 0) { out.push({ date: day, from: prev + 1, to: Math.min(total, prev + r), est: true }); prev = Math.min(total, prev + r); }
      }
      res = { days: out, finale: prev >= total ? out[out.length - 1].date : null };
    } else {
      var phases = plat.phases || [];
      var lastEnd = phases.reduce(function (m, p) { return p.to > m ? p.to : m; }, '');
      var cur = phases[0].from, ep = 0, n = 0;
      while (ep < total && n++ < 800) {
        var ph = null;
        for (var i = 0; i < phases.length; i++) if (phases[i].from <= cur && cur <= phases[i].to) ph = phases[i];
        var est = false, rate;
        if (ph) rate = rateOn(ph, cur);
        else if (cur > lastEnd) { if (!plat.after) break; rate = rateOn(plat.after, cur); est = !plat.exact; }
        else rate = 0;
        if (skip.indexOf(cur) >= 0) rate = 0;
        if (rate > 0) { out.push({ date: cur, from: ep + 1, to: Math.min(total, ep + rate), est: est || !!plat.guess }); ep = Math.min(total, ep + rate); }
        cur = addDays(cur, 1);
      }
      res = { days: out, finale: ep >= total ? out[out.length - 1].date : null };
    }
    memo[pid] = res;
    return res;
  }

  function findPlatform(drama, pid) {
    for (var i = 0; i < drama.platforms.length; i++) if (drama.platforms[i].id === pid) return drama.platforms[i];
    return drama.platforms[0];
  }

  // 沿著 sameAs 找到真正排日期的平台
  function rootPlatform(drama, pid) {
    var p = findPlatform(drama, pid), guard = 0;
    while (p.sameAs && guard++ < 10) p = findPlatform(drama, p.sameAs);
    return p;
  }
  function officialEnd(plat) {
    return (plat.phases || []).reduce(function (m, p) { return p.to > m ? p.to : m; }, '');
  }

  // 讀者的調整：{ per, days, skip: [日期], u: { d: 日期, to: 集數 } }
  // per／days／skip 只改官方還沒公布的日子（套在 sameAs 的源頭，所以同步的平台一起變）；u（超點）只套在選中的平台
  function applyAdjust(drama, pid, adj) {
    if (!adj) return drama;
    var d = JSON.parse(JSON.stringify(drama));
    var root = rootPlatform(d, pid), end = officialEnd(root);
    if (root.after && (adj.per > 0 || adj.days)) {
      root.after = { perDay: adj.per > 0 ? adj.per : root.after.perDay, days: adj.days && adj.days.length && adj.days.length < 7 ? adj.days : (adj.days ? null : root.after.days) };
      if (!root.after.days) delete root.after.days;
    }
    if (adj.skip && adj.skip.length) d.skip = (d.skip || []).concat(adj.skip.filter(function (s) { return s > end; }));
    if (adj.u && adj.u.d) findPlatform(d, pid).unlock = { date: adj.u.d, to: adj.u.to > 0 ? Math.min(adj.u.to, d.episodes) : d.episodes };
    return d;
  }

  // 今天（含）以前最後一次更新
  function progress(sch, today) {
    var seen = 0, todayRow = null, next = null;
    sch.days.forEach(function (d) {
      if (d.date <= today) seen = d.to;
      if (d.date === today) todayRow = d;
      if (!next && d.date > today) next = d;
    });
    return { seen: seen, todayRow: todayRow, next: next };
  }

  var API = { schedule: schedule, progress: progress, addDays: addDays, applyAdjust: applyAdjust, diffDays: diffDays, today: localToday };
  if (typeof module !== 'undefined') module.exports = API;
  if (typeof document === 'undefined') return;
  window.HyDramaCalendar = API;  // story 首頁的「今天第幾集」也用同一套算法
  if (!document.getElementById('dc-app')) return;

  // ---------- 介面文字 ----------
  var LANG = (document.documentElement.lang || 'zh').slice(0, 2);
  if (LANG !== 'en' && LANG !== 'ja') LANG = 'zh';
  var T = {
    zh: {
      paren: function (x) { return '（' + x + '）'; },
      wk: ['日', '一', '二', '三', '四', '五', '六'],
      ep: function (a, b) { return a === b ? '第 ' + a + ' 集' : '第 ' + a + '～' + b + ' 集'; },
      cell: function (a, b) { return a === b ? String(a) : a + '～' + b; },
      date: function (s) { var a = s.split('-'); return +a[1] + '/' + +a[2] + '（' + T.wk[weekday(s)] + '）'; },
      month: function (y, m) { return y + ' 年 ' + m + ' 月'; },
      seen: function (n) { return n ? '目前可看到' + T.ep(n, n) : '還沒開播'; },
      today: function (r) { return '今天更新' + T.ep(r.from, r.to); },
      next: function (r) { return '下次更新：' + T.date(r.date) + T.ep(r.from, r.to); },
      left: function (n, d) { return n > 0 ? '距離大結局還有 ' + n + ' 天：' + T.date(d) : (n === 0 ? '今天大結局：' + T.date(d) : '已完結：' + T.date(d)); },
      start: function (n, d) { return n + ' 天後開播：' + T.date(d); },
      noFinale: '官方還沒排到最後一集，大結局日期待公布',
      est: '推算', guess: '本站推測', finale: '大結局', unconfirmed: '集數待確認',
      total: function (n) { return '共 ' + n + ' 集'; },
      checked: function (s) { return '本站最後核對：' + s; },
      notFound: '找不到這部劇，請從清單選一部，或自己輸入。',
      noList: '劇清單暫時讀不到，可以先自己輸入。',
      pick: '選一部劇',
      bad: '請填開播日，集數與每次更新集數要大於 0。',
      evt: function (t, a, b) { return t + ' ' + T.ep(a, b) + '更新'; },
      evtFinale: function (t) { return t + ' 大結局'; },
      article: function (t) { return '看《' + t + '》追劇日曆全文：幾點更新、人物關係與劇情'; },
      copied: '已複製分享連結', manualTitle: '我的追劇', tzLabel: '台灣時間', zone: '+08:00', nextDay: '（隔天）',
      unlockOpen: function (n) { return '超點：可看到' + T.ep(n, n); },
      unlockSoon: function (d, n) { return '超點：' + T.date(d) + '開放，可看到' + T.ep(n, n); },
      skipOfficial: function (e) { return T.date(e) + '以前是官方已公布的日子，不能改；請選之後的日期。'; },
      unlock: '超點', adjusted: '已套用你的調整（只改官方還沒公布的日子）', skipped: '停更',
      shareText: function (t) { return '《' + t + '》追劇日曆：每天更新第幾集、哪天大結局'; }
    },
    en: {
      paren: function (x) { return ' (' + x + ')'; },
      wk: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
      ep: function (a, b) { return a === b ? 'Ep ' + a : 'Ep ' + a + '-' + b; },
      cell: function (a, b) { return a === b ? String(a) : a + '-' + b; },
      date: function (s) { var d = new Date(toMs(s)); return T.wk[d.getUTCDay()] + ', ' + ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][d.getUTCMonth()] + ' ' + d.getUTCDate(); },
      month: function (y, m) { return ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][m - 1] + ' ' + y; },
      seen: function (n) { return n ? 'Out now: up to ' + T.ep(n, n) : 'Not started yet'; },
      today: function (r) { return 'Today: ' + T.ep(r.from, r.to); },
      next: function (r) { return 'Next: ' + T.date(r.date) + ', ' + T.ep(r.from, r.to); },
      left: function (n, d) { return n > 0 ? n + ' days to the finale (' + T.date(d) + ')' : (n === 0 ? 'Finale today (' + T.date(d) + ')' : 'Finished on ' + T.date(d)); },
      start: function (n, d) { return 'Premieres in ' + n + ' days (' + T.date(d) + ')'; },
      noFinale: 'The official schedule does not reach the last episode yet. Finale date to be announced.',
      est: 'estimate', guess: 'our guess', finale: 'Finale', unconfirmed: 'episode count not final',
      total: function (n) { return n + ' episodes'; },
      checked: function (s) { return 'Last checked: ' + s; },
      notFound: 'We could not find that drama. Pick one from the list or enter your own.',
      noList: 'The drama list could not load. You can still enter your own.',
      pick: 'Choose a drama',
      bad: 'Add a premiere date. Episodes and episodes per update must be more than 0.',
      evt: function (t, a, b) { return t + ' ' + T.ep(a, b); },
      evtFinale: function (t) { return t + ' finale'; },
      article: function (t) { return 'Read the full ' + t + ' guide'; },
      copied: 'Link copied', manualTitle: 'My drama', zone: '', nextDay: ' (next day)',
      tzLabel: function (tz) { return tz === '+09:00' ? 'Japan time (UTC+9)' : 'China time (UTC+8)'; },
      unlockOpen: function (n) { return 'Paid early access: up to ' + T.ep(n, n); },
      unlockSoon: function (d, n) { return 'Paid early access from ' + T.date(d) + ': up to ' + T.ep(n, n); },
      skipOfficial: function (e) { return 'Dates up to ' + T.date(e) + ' are official and cannot be changed. Pick a later date.'; },
      unlock: 'Early access', adjusted: 'Your changes are applied (only to dates not announced yet)', skipped: 'Break',
      shareText: function (t) { return t + ' episode schedule: what airs each day and when it ends'; }
    },
    ja: {
      paren: function (x) { return '（' + x + '）'; },
      wk: ['日', '月', '火', '水', '木', '金', '土'],
      ep: function (a, b) { return a === b ? '第' + a + '話' : '第' + a + '〜' + b + '話'; },
      cell: function (a, b) { return a === b ? String(a) : a + '〜' + b; },
      date: function (s) { var a = s.split('-'); return +a[1] + '/' + +a[2] + '（' + T.wk[weekday(s)] + '）'; },
      month: function (y, m) { return y + '年' + m + '月'; },
      seen: function (n) { return n ? '現在' + T.ep(n, n) + 'まで配信中' : 'まだ配信前'; },
      today: function (r) { return '今日は' + T.ep(r.from, r.to) + 'を配信'; },
      next: function (r) { return '次回：' + T.date(r.date) + T.ep(r.from, r.to); },
      left: function (n, d) { return n > 0 ? '最終回まであと' + n + '日：' + T.date(d) : (n === 0 ? '今日が最終回：' + T.date(d) : '配信終了：' + T.date(d)); },
      start: function (n, d) { return n + '日後に配信開始：' + T.date(d); },
      noFinale: '公式スケジュールがまだ最終話まで出ていません。最終回の日付は発表待ちです。',
      est: '推定', guess: '当サイト推定', finale: '最終回', unconfirmed: '話数は未確定',
      total: function (n) { return '全' + n + '話'; },
      checked: function (s) { return '最終確認日：' + s; },
      notFound: 'このドラマが見つかりません。リストから選ぶか、自分で入力してください。',
      noList: 'ドラマリストを読み込めませんでした。自分で入力することはできます。',
      pick: 'ドラマを選ぶ',
      bad: '配信開始日を入力してください。話数と1回の配信話数は1以上にしてください。',
      evt: function (t, a, b) { return t + ' ' + T.ep(a, b) + '配信'; },
      evtFinale: function (t) { return t + ' 最終回'; },
      article: function (t) { return '『' + t + '』配信スケジュールの記事を読む'; },
      copied: 'リンクをコピーしました', manualTitle: 'わたしのドラマ', tzLabel: '日本時間', zone: '+09:00', nextDay: '（翌日）',
      unlockOpen: function (n) { return '有料先行（超点）：' + T.ep(n, n) + 'まで視聴可'; },
      unlockSoon: function (d, n) { return '有料先行（超点）：' + T.date(d) + 'から' + T.ep(n, n) + 'まで'; },
      skipOfficial: function (e) { return T.date(e) + 'までは公式発表済みのため変更できません。それ以降の日付を選んでください。'; },
      unlock: '先行', adjusted: '調整を反映しています（公式未発表の日だけ）', skipped: '休止',
      shareText: function (t) { return '『' + t + '』配信スケジュール：毎日何話まで、最終回はいつ'; }
    }
  }[LANG];

  // ---------- 狀態 ----------
  var $ = function (id) { return document.getElementById(id); };
  var list = [], drama = null, pid = null, sch = null, isManual = false;
  var base = null, adj = null;  // base＝原始資料，drama＝套用調整後

  function title(d) { return (d.title && (d.title[LANG] || d.title.zh)) || T.manualTitle; }
  function pname(p) { return (p.name && (p.name[LANG] || p.name.zh)) || ''; }
  function esc(s) { return String(s).replace(/[<>"']/g, function (c) { return { '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }

  // 時間換算：來源時區 → 頁面時區（英文版顯示來源時間）
  function offMin(o) { var m = /([+-])(\d\d):(\d\d)/.exec(o || '+08:00'); return (m[1] === '-' ? -1 : 1) * (m[2] * 60 + +m[3]); }
  function showTime(t, tz) {
    if (!t) return '';
    var a = t.split(':'), min = a[0] * 60 + +a[1];
    if (T.zone) min += offMin(T.zone) - offMin(tz);
    var plus = min >= 1440 ? T.nextDay : '';
    min = ((min % 1440) + 1440) % 1440;
    var label = typeof T.tzLabel === 'function' ? T.tzLabel(tz) : T.tzLabel;
    return String(Math.floor(min / 60)).padStart(2, '0') + ':' + String(min % 60).padStart(2, '0') + ' ' + label + plus;
  }

  // ---------- 畫面 ----------
  function msg(text) { var m = $('dc-msg'); m.textContent = text || ''; m.hidden = !text; }

  function fillPicker() {
    var sel = $('dc-pick');
    var order = { airing: 0, upcoming: 1, ended: 2 };
    var sorted = list.slice().sort(function (a, b) { return (order[a.status] || 0) - (order[b.status] || 0); });
    sel.innerHTML = '<option value="">' + esc(T.pick) + '</option>' + sorted.map(function (d) {
      return '<option value="' + esc(d.id) + '">' + esc(title(d)) + '</option>';
    }).join('');
  }

  function render() {
    var box = $('dc-result');
    if (!drama) { box.hidden = true; return; }
    box.hidden = false;
    drama = isManual ? base : applyAdjust(base, pid, adj);
    var memo = {};
    sch = schedule(drama, pid, memo);
    var today = localToday();

    // 劇名＋集數
    var meta = T.total(drama.episodes) + (drama.episodesConfirmed === false ? T.paren(T.unconfirmed) : '');
    if (drama.lastChecked) meta += '・' + T.checked(drama.lastChecked);
    $('dc-title').textContent = title(drama);
    $('dc-meta').textContent = meta;

    // 今天：每個平台一行
    var lines = drama.platforms.map(function (p) {
      var s = schedule(drama, p.id, memo), g = progress(s, today);
      var bits = [g.todayRow ? T.today(g.todayRow) : T.seen(g.seen)];
      if (!g.todayRow && g.next) bits.push(T.next(g.next));
      var t = showTime(p.time || drama.time, drama.tz);
      if (t) bits.push(t);
      if (p.unlock) bits.push(today >= p.unlock.date ? T.unlockOpen(p.unlock.to) : T.unlockSoon(p.unlock.date, p.unlock.to));
      var flag = p.guess ? ' <span class="dc-tag">' + esc(T.guess) + '</span>' : '';
      return '<li><b>' + esc(pname(p)) + '</b>' + flag + '<span>' + esc(bits.join('・')) + '</span></li>';
    });
    $('dc-today').innerHTML = lines.join('');
    var first = sch.days.length ? sch.days[0].date : null;
    var end = $('dc-finale');
    if (first && today < first) end.textContent = T.start(diffDays(today, first), first) + (sch.finale ? '・' + T.finale + ' ' + T.date(sch.finale) : '');
    else if (sch.finale) end.textContent = T.left(diffDays(today, sch.finale), sch.finale);
    else end.textContent = T.noFinale;
    var lastDay = sch.days[sch.days.length - 1];
    var finEst = !(first && today < first) && sch.finale && lastDay && lastDay.est;
    end.className = 'dc-finale' + (finEst ? ' is-est' : '');
    if (finEst) end.textContent += T.paren(T.est);

    // 平台切換
    $('dc-plat').innerHTML = drama.platforms.length < 2 ? '' : drama.platforms.map(function (p) {
      return '<button type="button" class="dc-chip" data-interact="switch_platform" data-pid="' + esc(p.id) + '" aria-pressed="' + (p.id === pid) + '">' + esc(pname(p)) + '</button>';
    }).join('');

    renderCalendar(today);
    renderAdjust();
    renderLinks();
  }

  function renderCalendar(today) {
    var byDate = {}, plat = findPlatform(drama, pid), skips = drama.skip || [];
    sch.days.forEach(function (d) { byDate[d.date] = d; });
    if (!sch.days.length) { $('dc-cal').innerHTML = ''; return; }
    var start = sch.days[0].date, stop = sch.days[sch.days.length - 1].date;
    var y = +start.slice(0, 4), m = +start.slice(5, 7), html = '';
    var head = T.wk.map(function (w) { return '<th scope="col">' + esc(w) + '</th>'; }).join('');
    while (y * 100 + m <= +stop.slice(0, 4) * 100 + +stop.slice(5, 7)) {
      var firstDay = y + '-' + String(m).padStart(2, '0') + '-01';
      var cells = [], pad = weekday(firstDay);
      for (var i = 0; i < pad; i++) cells.push('<td></td>');
      for (var d = firstDay; +d.slice(5, 7) === m; d = addDays(d, 1)) {
        var r = byDate[d], cls = [], label = '';
        if (r) {
          cls.push('has');
          if (r.est) cls.push('est');
          if (d === sch.finale) cls.push('fin');
          label = '<span class="dc-ep">' + esc(T.cell(r.from, r.to)) + '</span>' + (d === sch.finale ? '<span class="dc-fin">' + esc(T.finale) + '</span>' : '');
        }
        if (plat.unlock && d === plat.unlock.date) { cls.push('unl'); label += '<span class="dc-badge">' + esc(T.unlock) + '</span>'; }
        if (!r && skips.indexOf(d) >= 0 && d > start && d < stop) { cls.push('skip'); label += '<span class="dc-badge">' + esc(T.skipped) + '</span>'; }
        if (d === today) cls.push('today');
        var aria = r ? T.date(d) + ' ' + T.ep(r.from, r.to) + (r.est ? T.paren(T.est) : '') : '';
        cells.push('<td class="' + cls.join(' ') + '"' + (aria ? ' aria-label="' + esc(aria) + '"' : '') + '><span class="dc-d">' + +d.slice(8) + '</span>' + label + '</td>');
      }
      while (cells.length % 7) cells.push('<td></td>');
      var rows = '';
      for (var k = 0; k < cells.length; k += 7) rows += '<tr>' + cells.slice(k, k + 7).join('') + '</tr>';
      html += '<table class="dc-month"><caption>' + esc(T.month(y, m)) + '</caption><thead><tr>' + head + '</tr></thead><tbody>' + rows + '</tbody></table>';
      m++; if (m > 12) { m = 1; y++; }
    }
    $('dc-cal').innerHTML = html;
  }

  function shareUrl() {
    var here = location.origin + location.pathname;
    if (isManual) return here + '#m=' + encodeURIComponent(JSON.stringify(manualState()));
    return here + '?d=' + encodeURIComponent(drama.id) + (pid !== drama.platforms[0].id ? '&p=' + encodeURIComponent(pid) : '') +
      (adj ? '#a=' + encodeURIComponent(JSON.stringify(adj)) : '');
  }

  function renderLinks() {
    var t = title(drama), page = shareUrl();
    var art = drama.articles && (drama.articles[LANG] || (LANG === 'en' ? null : drama.articles.zh));
    var more = $('dc-more');
    if (art) { more.hidden = false; more.href = art; more.textContent = T.article(t); } else more.hidden = true;
    var affUrl = drama.aff && drama.aff[LANG];
    $('dc-aff').hidden = !affUrl;
    if (affUrl) $('dc-aff-link').href = affUrl;
    var g = $('dc-gcal');
    if (sch.finale) {
      var d1 = sch.finale.replace(/-/g, ''), d2 = addDays(sch.finale, 1).replace(/-/g, '');
      var q = new URLSearchParams({ action: 'TEMPLATE', text: T.evtFinale(t), dates: d1 + '/' + d2, details: page + '\n' + (art || TOOL_URL) });
      g.href = 'https://calendar.google.com/calendar/render?' + q.toString();
      g.hidden = false;
    } else g.hidden = true;
  }

  // ---------- 調整推算 ----------
  var draftSkip = [];
  function adjKey() { return 'dc-adj-' + base.id; }
  function loadAdj() {
    try { var v = localStorage.getItem(adjKey()); return v ? JSON.parse(v) : null; } catch (e) { return null; }
  }
  function saveAdj() {
    try { if (adj) localStorage.setItem(adjKey(), JSON.stringify(adj)); else localStorage.removeItem(adjKey()); } catch (e) { /* 私密模式：只是記不住 */ }
  }
  function renderSkips() {
    $('dc-a-skips').innerHTML = draftSkip.map(function (d, i) {
      return '<li>' + esc(T.date(d)) + ' <button type="button" class="dc-x" data-i="' + i + '" data-interact="adjust_skip_remove" aria-label="×">×</button></li>';
    }).join('');
  }
  function renderAdjust() {
    var box = $('dc-adj');
    var root = isManual ? null : rootPlatform(base, pid);
    box.hidden = !root || !root.after;
    if (box.hidden) return;
    var a = adj || {}, after = root.after;
    $('dc-a-per').value = a.per || after.perDay || '';
    var days = a.days || after.days;
    document.querySelectorAll('#dc-adj input[name="awd"]').forEach(function (c) { c.checked = !days || days.indexOf(+c.value) >= 0; });
    draftSkip = (a.skip || []).slice(); renderSkips();
    var u = a.u || {};
    $('dc-a-ud').value = u.d || ''; $('dc-a-uto').value = u.to || '';
    $('dc-a-end').textContent = officialEnd(root) ? T.date(officialEnd(root)) : '';
    $('dc-a-state').hidden = !adj;
    $('dc-a-reset').hidden = !adj;
  }
  function readAdjust() {
    var days = [];
    document.querySelectorAll('#dc-adj input[name="awd"]').forEach(function (c) { if (c.checked) days.push(+c.value); });
    var root = rootPlatform(base, pid), a = {};
    var per = +$('dc-a-per').value;
    if (per > 0 && per !== root.after.perDay) a.per = Math.min(per, 50);
    var orig = root.after.days || [0, 1, 2, 3, 4, 5, 6];
    if (days.length && days.slice().sort().join() !== orig.slice().sort().join()) a.days = days;
    var end = officialEnd(root), skip = draftSkip.filter(function (d) { return d > end; }).sort();
    if (skip.length) a.skip = skip;
    if ($('dc-a-ud').value) a.u = { d: $('dc-a-ud').value, to: +$('dc-a-uto').value || 0 };
    return Object.keys(a).length ? a : null;
  }
  function syncUrl() { if (!isManual) history.replaceState(null, '', shareUrl().replace(location.origin, '')); }

  // ---------- 行事曆 .ics ----------
  function icsEsc(s) { return String(s).replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\n/g, '\\n'); }
  function stamp(ms) { return new Date(ms).toISOString().replace(/[-:]/g, '').slice(0, 15) + 'Z'; }
  function buildIcs() {
    var t = title(drama), p = findPlatform(drama, pid), time = p.time || drama.time, page = shareUrl();
    var L = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Knitting Hiyori//Drama Calendar//' + LANG.toUpperCase(), 'CALSCALE:GREGORIAN', 'X-WR-CALNAME:' + icsEsc(t + ' ' + pname(p))];
    var now = stamp(Date.now());
    sch.days.forEach(function (d) {
      var sum = (d.date === sch.finale ? T.evtFinale(t) + ' ' + T.ep(d.from, d.to) : T.evt(t, d.from, d.to)) + (d.est ? T.paren(T.est) : '');
      L.push('BEGIN:VEVENT', 'UID:' + drama.id + '-' + p.id + '-' + d.date + '@story.knittinghiyori.com', 'DTSTAMP:' + now);
      if (time) {
        var a = time.split(':'), start = toMs(d.date) + (a[0] * 60 + +a[1] - offMin(drama.tz)) * 60000;
        L.push('DTSTART:' + stamp(start), 'DTEND:' + stamp(start + 3600000));
      } else {
        L.push('DTSTART;VALUE=DATE:' + d.date.replace(/-/g, ''), 'DTEND;VALUE=DATE:' + addDays(d.date, 1).replace(/-/g, ''));
      }
      L.push('SUMMARY:' + icsEsc(sum), 'DESCRIPTION:' + icsEsc(pname(p) + '\n' + page), 'URL:' + page, 'END:VEVENT');
    });
    L.push('END:VCALENDAR');
    return L.join('\r\n') + '\r\n';
  }
  function downloadIcs() {
    var blob = new Blob([buildIcs()], { type: 'text/calendar;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = (drama.id || 'drama') + '-calendar.ics';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
  }

  function share() {
    var url = shareUrl(), text = T.shareText(title(drama));
    if (navigator.share) { navigator.share({ title: text, text: text, url: url }).catch(function () {}); return; }
    var done = function () { msg(T.copied); setTimeout(function () { msg(''); }, 2500); };
    if (navigator.clipboard) navigator.clipboard.writeText(text + ' ' + url).then(done, function () { prompt('', url); });
    else prompt('', url);
  }

  // ---------- 自己輸入 ----------
  function manualState() {
    var days = [];
    document.querySelectorAll('#dc-manual input[name="wd"]').forEach(function (c) { if (c.checked) days.push(+c.value); });
    return {
      t: $('dc-m-title').value.trim(), s: $('dc-m-start').value, e: +$('dc-m-eps').value,
      f: +$('dc-m-first').value, p: +$('dc-m-per').value, w: days, h: $('dc-m-time').value
    };
  }
  function setManual(st) {
    $('dc-m-title').value = st.t || ''; $('dc-m-start').value = st.s || ''; $('dc-m-eps').value = st.e || '';
    $('dc-m-first').value = st.f || ''; $('dc-m-per').value = st.p || ''; $('dc-m-time').value = st.h || '';
    document.querySelectorAll('#dc-manual input[name="wd"]').forEach(function (c) { c.checked = !st.w || !st.w.length || st.w.indexOf(+c.value) >= 0; });
  }
  function fromManual(st) {
    if (!/^\d{4}-\d\d-\d\d$/.test(st.s || '') || !(st.e > 0) || !(st.p > 0)) return null;
    var w = st.w && st.w.length && st.w.length < 7 ? st.w : null;
    var first = st.f > 0 ? st.f : st.p;
    return {
      id: 'custom', title: { zh: st.t || T.manualTitle, en: st.t || T.manualTitle, ja: st.t || T.manualTitle },
      episodes: Math.min(st.e, 500), tz: T.zone || '+08:00', time: st.h || null,
      platforms: [{ id: 'custom', name: {}, exact: true, phases: [{ from: st.s, to: st.s, perDay: first }], after: w ? { perDay: st.p, days: w } : { perDay: st.p } }]
    };
  }
  function runManual() {
    var d = fromManual(manualState());
    if (!d) { msg(T.bad); return; }
    msg('');
    isManual = true; base = drama = d; adj = null; pid = 'custom'; $('dc-pick').value = '';
    history.replaceState(null, '', location.pathname + '#m=' + encodeURIComponent(JSON.stringify(manualState())));
    render();
  }

  function fromHashAdj() {
    var m = /#a=(.+)$/.exec(location.hash);
    if (!m) return null;
    try { var a = JSON.parse(decodeURIComponent(m[1])); return a && typeof a === 'object' ? a : null; } catch (e) { return null; }
  }

  function choose(id, p) {
    var d = null;
    for (var i = 0; i < list.length; i++) if (list[i].id === id) d = list[i];
    if (!d) { drama = null; render(); return false; }
    isManual = false; base = drama = d;
    pid = (p && d.platforms.some(function (x) { return x.id === p; })) ? p : d.platforms[0].id;
    adj = fromHashAdj() || loadAdj();
    $('dc-pick').value = d.id;
    return true;
  }

  // ---------- 啟動 ----------
  function bind() {
    $('dc-pick').addEventListener('change', function () {
      if (!this.value) return;
      history.replaceState(null, '', location.pathname + '?d=' + encodeURIComponent(this.value));
      choose(this.value); msg('');
      render(); syncUrl();
    });
    $('dc-plat').addEventListener('click', function (e) {
      var b = e.target.closest('[data-pid]'); if (!b) return;
      pid = b.getAttribute('data-pid'); render(); syncUrl();
    });
    $('dc-manual').addEventListener('submit', function (e) { e.preventDefault(); runManual(); });
    $('dc-ics').addEventListener('click', downloadIcs);
    $('dc-a-skip-add').addEventListener('click', function () {
      var v = $('dc-a-skip').value, end = officialEnd(rootPlatform(base, pid));
      var am = $('dc-a-msg');
      am.hidden = !(v && v <= end); am.textContent = am.hidden ? '' : T.skipOfficial(end);
      if (!am.hidden) return;
      if (v && draftSkip.indexOf(v) < 0) { draftSkip.push(v); draftSkip.sort(); renderSkips(); }
      $('dc-a-skip').value = '';
    });
    $('dc-a-skips').addEventListener('click', function (e) {
      var b = e.target.closest('[data-i]'); if (!b) return;
      draftSkip.splice(+b.getAttribute('data-i'), 1); renderSkips();
    });
    $('dc-a-apply').addEventListener('click', function () { adj = readAdjust(); saveAdj(); render(); syncUrl(); });
    $('dc-a-reset').addEventListener('click', function () { adj = null; saveAdj(); render(); syncUrl(); });
    $('dc-share').addEventListener('click', share);
  }

  function start() {
    bind();
    var q = new URLSearchParams(location.search);
    var hash = /^#m=(.+)$/.exec(location.hash);
    var ready = function () {
      if (hash) {
        try { var st = JSON.parse(decodeURIComponent(hash[1])); setManual(st); $('dc-manual-box').open = true; runManual(); return; } catch (e) { /* 壞掉的分享連結：當作沒帶 */ }
      }
      if (!list.length) return;
      var id = q.get('d');
      if (id && !choose(id, q.get('p'))) { msg(T.notFound); return; }
      if (!id && list.length) {
        var airing = list.filter(function (d) { return d.status === 'airing'; });
        choose((airing[0] || list[0]).id);
      }
      render();
    };
    fetch('/drama/calendar/dramas.json', { cache: 'no-cache' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (data) { list = data.dramas || []; fillPicker(); }, function () { $('dc-pick-row').hidden = true; $('dc-manual-box').open = true; msg(T.noList); })
      .then(ready);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
