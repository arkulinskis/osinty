/* core.js: the shared front-end engine (window.UI). Same in every app made from APP_MAKER/template;
   app-specific things live in web/app.js (brand, nav, footer) and web/pages/*.html (the pages).

   Pages:   UI.page(name, {title, nav, icon, auth, order, chrome}, mount)
              auth: null (anyone) | 'guest' (signed-out only) | 'user' | 'admin'
              nav: label for the header / phone tab bar (omit to keep it out of the menus)
              mount(view, ctx) draws into `view`; ctx = {args, me, go, api}. Return a Promise (the page
              is "ready" when it resolves) or {ready, destroy}. URLs are #name/arg1/arg2.
   Server:  UI.api(fn, ...args) -> Promise of the server function's return value. A reply of
              {ok: false, error} rejects with that message (shown as a toast unless you .catch it).
            UI.apiQuiet(fn, ...args) is the same without Anvil's loading spinner.
   Auth:    UI.auth('login'|'signup'|'reset'|'logout', {...}) -> Promise of {ok, me, message}
   Helpers: UI.esc, UI.icon, UI.toast, UI.modal, UI.confirm, UI.busy, UI.formData, UI.fmtDate, UI.ago,
            UI.store, UI.setTheme, UI.feedback, UI.go, UI.refresh
   Tests:   window.UI_READY is true when the current page has finished loading. */
(function () {
  'use strict';
  if (window.UI && window.UI.__v) return;
  var UI = window.UI = { __v: 1, pages: {}, me: null, config: { name: 'App', key: 'app', home: 'home', landing: 'landing' } };
  window.UI_READY = false;

  // The saved theme lives under the app's key ('<key>.theme'), which is only known once the app configures UI:
  // apply it again then, or a saved Light/Dark choice is ignored after every reload.
  UI.configure = function (cfg) { Object.keys(cfg).forEach(function (k) { UI.config[k] = cfg[k]; }); if (cfg.key && UI.applyTheme) UI.applyTheme(UI.theme()); };

  /* ------------------------------------------------------------------ small helpers */
  UI.esc = function (s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };
  UI.plural = function (n, one, many) { return n + ' ' + (n === 1 ? one : (many || one + 's')); };
  UI.initials = function (name) {
    var p = String(name || '?').trim().split(/\s+/);
    return ((p[0] || '?')[0] + (p.length > 1 ? p[p.length - 1][0] : '')).toUpperCase();
  };
  UI.fmtDate = function (iso, opts) {
    if (!iso) return '';
    var d = iso.length <= 10 ? new Date(iso + 'T12:00:00') : new Date(iso);
    return d.toLocaleDateString(undefined, opts || { day: 'numeric', month: 'short', year: 'numeric' });
  };
  UI.fmtDateTime = function (iso) {
    return iso ? new Date(iso).toLocaleString(undefined, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '';
  };
  UI.ago = function (iso) {
    if (!iso) return '';
    var s = (Date.now() - new Date(iso).getTime()) / 1000;
    if (s < 60) return 'just now';
    var steps = [[60, 'minute'], [24, 'hour'], [7, 'day'], [4.35, 'week'], [12, 'month'], [Infinity, 'year']], n = s / 60;
    for (var i = 0; i < steps.length; i++) {
      if (n < steps[i][0]) { n = Math.floor(n); return UI.plural(n, steps[i][1]) + ' ago'; }
      n = n / steps[i][0];
    }
    return '';
  };
  UI.store = {
    get: function (k, dflt) { try { var v = localStorage.getItem(UI.config.key + '.' + k); return v == null ? dflt : JSON.parse(v); } catch (e) { return dflt; } },
    set: function (k, v) { try { localStorage.setItem(UI.config.key + '.' + k, JSON.stringify(v)); } catch (e) {} }
  };
  UI.formData = function (form) {
    var out = {};
    Array.prototype.forEach.call(form.elements, function (el) {
      if (!el.name || el.disabled) return;
      if (el.type === 'checkbox') out[el.name] = el.checked;
      else if (el.type === 'radio') { if (el.checked) out[el.name] = el.value; }
      else out[el.name] = el.value;
    });
    return out;
  };
  /* Disable a button while a Promise runs; returns the Promise. */
  UI.busy = function (btn, promise) {
    if (!btn) return promise;
    btn.disabled = true; btn.classList.add('is-busy');
    var done = function () { btn.disabled = false; btn.classList.remove('is-busy'); };
    promise.then(done, done);
    return promise;
  };

  var ICONS = {
    home: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/>',
    users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.5 3-5.5 6.5-5.5s6.5 2 6.5 5.5"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7"/><path d="M18 14.7c2.2.6 3.5 2.4 3.5 5.3"/>',
    sliders: '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
    shield: '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/>',
    logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    trash: '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/>',
    edit: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>',
    check: '<path d="M5 12.5l4.5 4.5L19 7"/>',
    x: '<path d="M6 6l12 12M18 6 6 18"/>',
    chat: '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20.5l1.4-4.9A8 8 0 1 1 21 12z"/>',
    bell: '<path d="M6 8a6 6 0 1 1 12 0c0 7 3 8 3 8H3s3-1 3-8"/><path d="M10 20a2 2 0 0 0 4 0"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    moon: '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>',
    menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
    arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    back: '<path d="M19 12H5M11 18l-6-6 6-6"/>',
    mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    bug: '<rect x="7" y="8" width="10" height="12" rx="5"/><path d="M12 8V5M9 5.5 7.5 4M15 5.5 16.5 4M7 13H3M21 13h-4M7.5 18l-3 2M16.5 18l3 2M7.5 9.5l-3-2M16.5 9.5l3-2"/>',
    bulb: '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
    star: '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
    heart: '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    chevron: '<path d="m6 9 6 6 6-6"/>',
    external: '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    lock: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    inbox: '<path d="M3 13h5l1.5 3h5L16 13h5"/><path d="M5 5h14l2 8v6H3v-6z"/>',
    grid: '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/>',
    sparkle: '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M6 18l2.5-2.5M15.5 8.5 18 6"/>',
    database: '<ellipse cx="12" cy="5.5" rx="7.5" ry="2.5"/><path d="M4.5 5.5v13c0 1.4 3.4 2.5 7.5 2.5s7.5-1.1 7.5-2.5v-13"/><path d="M4.5 12c0 1.4 3.4 2.5 7.5 2.5s7.5-1.1 7.5-2.5"/>',
    refresh: '<path d="M20 11a8 8 0 0 0-14.3-4.9L4 8"/><path d="M4 4v4h4"/><path d="M4 13a8 8 0 0 0 14.3 4.9L20 16"/><path d="M20 20v-4h-4"/>',
    calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    map: '<path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2z"/><path d="M9 4v14M15 6v14"/>',
    pin: '<path d="M12 21s7-6.2 7-12a7 7 0 0 0-14 0c0 5.8 7 12 7 12z"/><circle cx="12" cy="9" r="2.5"/>',
    camera: '<path d="M4 8h3l2-3h6l2 3h3v12H4z"/><circle cx="12" cy="13.5" r="3.5"/>',
    image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="m21 16-5-5-9 9"/>',
    globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3z"/>',
    copy: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/>',
    filter: '<path d="M4 5h16l-6 7.5V19l-4 1.5v-8z"/>',
    more: '<circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/>'
  };
  UI.ICONS = ICONS;
  UI.icon = function (name, cls) {
    return '<svg class="ui-ic ' + (cls || '') + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" ' +
      'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (ICONS[name] || ICONS.sparkle) + '</svg>';
  };

  /* ------------------------------------------------------------------ toasts, modals */
  UI.toast = function (msg, kind) {
    var box = document.querySelector('.ui-toasts');
    if (!box) { box = document.createElement('div'); box.className = 'ui ui-toasts'; box.setAttribute('aria-live', 'polite'); document.body.appendChild(box); }
    var t = document.createElement('div');
    t.className = 'ui-toast' + (kind ? ' ' + kind : '');
    t.innerHTML = (kind === 'error' ? UI.icon('info') : kind === 'ok' ? UI.icon('check') : '') + '<span>' + UI.esc(msg) + '</span>';
    box.appendChild(t);
    setTimeout(function () { t.classList.add('out'); setTimeout(function () { t.remove(); }, 300); }, kind === 'error' ? 6500 : 3200);
  };
  UI.modal = function (html, opts) {
    opts = opts || {};
    var prev = document.activeElement;
    var wrap = document.createElement('div');
    wrap.className = 'ui ui-modal-wrap';
    wrap.innerHTML = '<div class="ui-modal' + (opts.wide ? ' wide' : '') + '" role="dialog" aria-modal="true">' +
      '<button class="ui-btn ghost icon ui-modal-x" data-close aria-label="Close">' + UI.icon('x') + '</button>' + html + '</div>';
    document.body.appendChild(wrap);
    document.documentElement.classList.add('ui-modal-open');
    function key(e) { if (e.key === 'Escape') close(); }
    function close() {
      if (!wrap.parentNode) return;
      wrap.remove(); document.removeEventListener('keydown', key);
      if (!document.querySelector('.ui-modal-wrap')) document.documentElement.classList.remove('ui-modal-open');
      if (opts.onclose) opts.onclose();
      if (prev && prev.focus) prev.focus();
    }
    document.addEventListener('keydown', key);
    wrap.addEventListener('mousedown', function (e) { if (e.target === wrap) close(); });
    wrap.addEventListener('click', function (e) { if (e.target.closest('[data-close]')) close(); });
    var first = wrap.querySelector('input, textarea, select');
    setTimeout(function () { (first || wrap.querySelector('.ui-modal')).focus && (first || wrap.querySelector('.ui-modal')).focus(); }, 30);
    return { el: wrap.querySelector('.ui-modal'), close: close };
  };
  UI.confirm = function (o) {
    o = typeof o === 'string' ? { title: o } : (o || {});
    return new Promise(function (resolve) {
      var answered = false;
      var m = UI.modal('<h2>' + UI.esc(o.title || 'Are you sure?') + '</h2>' + (o.text ? '<p class="muted">' + UI.esc(o.text) + '</p>' : '') +
        '<div class="ui-row end" style="margin-top:20px"><button class="ui-btn ghost" data-close>' + UI.esc(o.cancel || 'Cancel') + '</button>' +
        '<button class="ui-btn ' + (o.danger ? 'danger solid' : 'primary') + '" data-ok>' + UI.esc(o.ok || 'OK') + '</button></div>',
      { onclose: function () { if (!answered) resolve(false); } });
      m.el.querySelector('[data-ok]').onclick = function () { answered = true; m.close(); resolve(true); };
    });
  };

  /* ------------------------------------------------------------------ theme */
  UI.theme = function () { return UI.store.get('theme', 'auto'); };
  UI.applyTheme = function (t) {
    if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
    else document.documentElement.removeAttribute('data-theme');
    var dark = t === 'dark' || (t !== 'light' && window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches);
    document.documentElement.classList.toggle('ui-dark', !!dark);
  };
  UI.setTheme = function (t) { UI.store.set('theme', t); UI.applyTheme(t); };
  UI.applyTheme(UI.theme());
  if (window.matchMedia) {
    try { matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () { UI.applyTheme(UI.theme()); }); } catch (e) {}
  }

  /* ------------------------------------------------------------------ server bridge */
  var bridge = null;
  function send(kind, payload) {
    if (!bridge) return Promise.reject(new Error('The app is still starting.'));
    var out;
    try { out = bridge(kind, JSON.stringify(payload || {})); } catch (e) { return Promise.reject(e); }
    return Promise.resolve(out).then(function (r) {
      r = typeof r === 'string' ? JSON.parse(r) : (r || {});
      if (r.error) {
        var err = new Error(r.error); err.uiApi = true; err.denied = !!r.denied;
        if (r.detail) console.error(kind, payload && payload.fn, r.detail);
        if (r.reload) setTimeout(function () { location.reload(); }, 2500);
        throw err;
      }
      return r.result;
    });
  }
  function apiCall(quiet, fn, args) {
    return send('call', { fn: fn, args: args, quiet: quiet }).then(function (res) {
      if (res && typeof res === 'object' && res.ok === false) {
        var err = new Error(res.error || 'That didn\'t work.'); err.uiApi = true; err.expected = true; err.result = res;
        throw err;
      }
      return res;
    });
  }
  UI.api = function (fn) { return apiCall(false, fn, Array.prototype.slice.call(arguments, 1)); };
  UI.apiQuiet = function (fn) { return apiCall(true, fn, Array.prototype.slice.call(arguments, 1)); };
  /* Errors nobody caught become a toast, so a failed action is never silent. */
  window.addEventListener('unhandledrejection', function (e) {
    if (e.reason && e.reason.uiApi) { e.preventDefault(); UI.toast(e.reason.message, 'error'); }
  });

  /* Sign in / up / out. On success it navigates: to where the visitor was heading (UI.after) or home
     after signing in, to the landing page after signing out. */
  UI.auth = function (kind, payload) {
    return send(kind, payload || {}).then(function (r) {
      if (r && r.ok === false) { var err = new Error(r.error); err.uiApi = true; err.expected = true; throw err; }
      if (r && 'me' in r && (r.me || kind === 'logout')) {
        UI.me = r.me || null;
        var target = r.me ? (UI.after || '#' + UI.config.home) : '#' + UI.config.landing;
        UI.after = null;
        if (location.hash === target) route(); else location.hash = target;
      }
      return r;
    });
  };
  /* Update the signed-in user's details (e.g. a new name) and redraw the header, without reloading the page. */
  UI.setMe = function (me) {
    UI.me = me || null;
    if (shellRoot) renderChrome(current.name);
  };

  /* ------------------------------------------------------------------ pages and routing */
  UI.page = function (name, opts, mount) {
    if (typeof opts === 'function') { mount = opts; opts = {}; }
    opts.name = name; opts.mount = mount;
    UI.pages[name] = opts;
  };
  UI.allowed = function (p) {
    if (!p) return false;
    if (p.auth === 'user') return !!UI.me;
    if (p.auth === 'admin') return !!(UI.me && UI.me.is_admin);
    if (p.auth === 'guest') return !UI.me;
    return true;
  };
  UI.navPages = function () {
    return Object.keys(UI.pages).map(function (k) { return UI.pages[k]; })
      .filter(function (p) { return p.nav && UI.allowed(p) && (!p.when || p.when()); })
      .sort(function (a, b) { return (a.order || 50) - (b.order || 50); });
  };
  UI.parseHash = function () {
    var h = (location.hash || '').replace(/^#!?\/?/, '');
    var parts = h.split('?')[0].split('/').filter(function (x) { return x !== ''; }).map(decodeURIComponent);
    return { name: parts[0] || '', args: parts.slice(1) };
  };
  UI.hashFor = function (name) {
    var args = Array.prototype.slice.call(arguments, 1).filter(function (a) { return a != null && a !== ''; });
    return '#' + [name].concat(args.map(encodeURIComponent)).join('/');
  };
  UI.go = function (name) {
    var h = UI.hashFor.apply(null, arguments);
    if (location.hash === h) route(); else location.hash = h;
  };
  UI.refresh = function () { route(); };
  UI.after = null;  // where to go after signing in

  var shellRoot = null, view = null, current = { name: null, destroy: null }, routeSeq = 0;

  function defaultPage() { return UI.me ? UI.config.home : UI.config.landing; }

  function route() {
    var r = UI.parseHash(), name = r.name || defaultPage(), p = UI.pages[name];
    if (!p) { name = defaultPage(); p = UI.pages[name]; r.args = []; }
    if (p.auth === 'guest' && UI.me) { p = UI.pages[UI.config.home]; name = UI.config.home; r.args = []; }
    if ((p.auth === 'user' || p.auth === 'admin') && !UI.me) {
      UI.after = location.hash && location.hash !== '#' ? location.hash : null;
      p = UI.pages.auth; name = 'auth'; r.args = [];
    }
    if (p.auth === 'admin' && !(UI.me && UI.me.is_admin)) {
      UI.toast('That page is for admins only.', 'error');
      p = UI.pages[UI.config.home]; name = UI.config.home; r.args = [];
    }
    var seq = ++routeSeq;
    window.UI_READY = false;
    if (current.destroy) { try { current.destroy(); } catch (e) { console.error(e); } }
    current = { name: name, args: r.args, destroy: null };
    if (shellRoot) {
      shellRoot.className = 'ui ui-shell page-' + name + (UI.me ? ' signed-in' : ' signed-out') + (p.chrome === false ? ' no-chrome' : '');
      renderChrome(name);
    }
    // A fresh element for every page, so listeners a page adds to `view` never pile up.
    var fresh = view.cloneNode(false);
    view.parentNode.replaceChild(fresh, view);
    view = fresh;
    window.scrollTo(0, 0);
    document.title = (p.title ? (typeof p.title === 'function' ? p.title(r.args) : p.title) + ' · ' : '') + UI.config.name;
    var ctx = { name: name, args: r.args, me: UI.me, go: UI.go, api: UI.api, page: p };
    var out;
    try { out = p.mount(view, ctx); } catch (e) { console.error(e); out = Promise.reject(e); }
    var ready = out && typeof out.then === 'function' ? out : (out && out.ready) || Promise.resolve();
    if (out && out.destroy) current.destroy = out.destroy;
    Promise.resolve(ready).then(function () { if (seq === routeSeq) window.UI_READY = true; },
      function (e) {
        if (seq !== routeSeq) return;
        console.error(e);
        if (!view.innerHTML) view.innerHTML = '<div class="ui-wrap"><div class="ui-empty">' + UI.icon('info') +
          '<h3>This page didn\'t load</h3><p class="muted">' + UI.esc(e && e.message || 'Something went wrong.') + '</p>' +
          '<button class="ui-btn" onclick="UI.refresh()">Try again</button></div></div>';
        window.UI_READY = true;
      });
  }
  UI.current = function () { return current; };

  /* The shell's parts come from web/app.js: UI.shell = {header(me, active), footer(me), tabbar(me, active)} */
  function renderChrome(active) {
    var S = UI.shell || {};
    var hd = shellRoot.querySelector('[data-ui-header]'), ft = shellRoot.querySelector('[data-ui-footer]'), tb = shellRoot.querySelector('[data-ui-tabbar]');
    if (hd) hd.innerHTML = S.header ? S.header(UI.me, active) : '';
    if (ft) ft.innerHTML = S.footer ? S.footer(UI.me, active) : '';
    if (tb) tb.innerHTML = S.tabbar ? S.tabbar(UI.me, active) : '';
  }
  UI.renderChrome = function () { if (shellRoot) renderChrome(current.name); };

  /* Called by client_code/Main.py (and by the local harness) once the page is up. */
  UI.start = function (node, bridgeFn, bootJson) {
    bridge = bridgeFn;
    var boot = typeof bootJson === 'string' ? JSON.parse(bootJson || '{}') : (bootJson || {});
    UI.me = boot.me || null;
    var host = node && node.matches && node.matches('[data-ui-app]') ? node : (node && node.querySelector('[data-ui-app]')) || node || document.body;
    host.innerHTML = '<div class="ui ui-shell">' +
      '<header class="ui-header" data-ui-header></header>' +
      '<main class="ui-main" data-ui-view></main>' +
      '<footer class="ui-footer" data-ui-footer></footer>' +
      '<nav class="ui-tabbar" data-ui-tabbar aria-label="Main"></nav></div>';
    shellRoot = host.firstChild;
    view = host.querySelector('[data-ui-view]');
    if (UI.shell && UI.shell.wire) UI.shell.wire(shellRoot);
    window.addEventListener('hashchange', route);
    route();
  };

  /* ------------------------------------------------------------------ feedback (footer + menu)
     All feedback goes to Prepsto. The widget tag in head.html (data-prepsto="CODE") slides its panel in;
     any [data-feedback] or [data-prepsto-open] element opens it. If the widget hasn't loaded, the panel opens in a new tab.
     There is no in-app feedback form any more: Admin -> Feedback only lists older messages (and app requests). */
  UI.feedback = function () {
    if (window.Prepsto && window.Prepsto.open) { window.Prepsto.open(); return; }
    var tag = document.querySelector('script[data-prepsto]');
    var code = tag && tag.getAttribute('data-prepsto');
    if (code && code.indexOf('__') !== 0) window.open('https://prepsto.com/#f/' + encodeURIComponent(code), '_blank', 'noopener');
    else UI.toast('Feedback is not set up yet.', 'error');
  };

  /* Shared clicks: [data-go="page/arg"], [data-feedback], [data-theme-set] anywhere in the app. */
  document.addEventListener('click', function (e) {
    var el = e.target.closest && e.target.closest('[data-go],[data-feedback],[data-theme-set]');
    if (!el) return;
    if (el.hasAttribute('data-go')) { e.preventDefault(); UI.go.apply(null, el.getAttribute('data-go').split('/')); }
    else if (el.hasAttribute('data-feedback')) { e.preventDefault(); UI.feedback(el.getAttribute('data-feedback') || null); }
    else if (el.hasAttribute('data-theme-set')) { e.preventDefault(); UI.setTheme(el.getAttribute('data-theme-set')); if (UI.shell && UI.shell.onTheme) UI.shell.onTheme(); }
  });
})();


/* app.js: this app's identity and frame: name, header, footer, phone tab bar.
   Pages live in web/pages/*.html. The engine (window.UI) is web/core.js. */
(function () {
  'use strict';
  UI.configure({
    name: 'Osinty',
    key: 'osinty',          // prefix for this app's browser storage
    tagline: 'Every trace tells a story. Learn to read it, legally and ethically.',   // footer line
    home: 'home',                // first page after signing in
    landing: 'landing'           // first page for visitors who aren't signed in
  });

  var esc = UI.esc;

  function brand() {
    return '<a class="ui-brand" href="#" data-go="' + (UI.me ? UI.config.home : UI.config.landing) + '" aria-label="' + esc(UI.config.name) + ' home">' +
      '<img src="_/theme/icon.svg" alt="" width="32" height="32"><span>' + esc(UI.config.name) + '</span></a>';
  }

  function themeSwitch() {
    var t = UI.theme();
    return '<div class="ui-seg" role="group" aria-label="Appearance">' + [['auto', 'Auto'], ['light', 'Light'], ['dark', 'Dark']].map(function (o) {
      return '<button type="button" data-theme-set="' + o[0] + '" class="' + (t === o[0] ? 'on' : '') + '">' + o[1] + '</button>';
    }).join('') + '</div>';
  }

  function userMenu(me) {
    return '<div class="ui-menu" data-menu hidden>' +
      '<div class="ui-menu-head"><strong>' + esc(me.name) + '</strong><span class="muted small">' + esc(me.email) + '</span></div>' +
      '<a href="#profile" data-go="profile">' + UI.icon('user') + 'Your dossier</a>' +
      '<a href="#kit" data-go="kit">' + UI.icon('tool') + 'Field Kit</a>' +
      (me.is_admin ? '<a href="#admin" data-go="admin">' + UI.icon('shield') + 'Admin</a>' : '') +
      '<div class="ui-menu-block"><span class="small muted">Appearance</span>' + themeSwitch() + '</div>' +
      '<button type="button" data-feedback>' + UI.icon('chat') + 'Submit feedback</button>' +
      '<button type="button" data-lk-open="overview">' + UI.icon('lock') + 'Privacy &amp; Terms</button>' +
      '<button type="button" data-signout>' + UI.icon('logout') + 'Sign out</button></div>';
  }

  /* Office radio: moody tracks streamed by ArkMusic (web/pages/_arkmusic.html). Off until switched on with the
     header button (remembered in this browser); plays on signed-in pages, never on admin. */
  UI.ICONS.music = UI.ICONS.music || '<path d="M9 18V5l11-2v13"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="16" r="2.5"/>';
  var RADIO = ['spiralis', 'toulouse', 'high-notes'];
  function radioOn() { return !!UI.store.get('radio', false); }
  function radioButton() {
    if (!window.ArkMusic) return '';
    setTimeout(syncRadio, 0);  // the header redraws on every page change and sign-in
    var on = radioOn();
    return '<button type="button" class="os-radio' + (on ? ' on' : '') + '" data-radio aria-pressed="' + on + '" title="' + (on ? 'Office radio on' : 'Office radio off') +
      '" aria-label="Office radio">' + UI.icon('music') + '</button>';
  }
  function syncRadio() {
    if (!window.ArkMusic) return;
    var page = UI.current && UI.current().name;
    if (radioOn() && UI.me && page !== 'admin') ArkMusic.play(RADIO, { volume: 0.3, shuffle: true, fade: 2 });
    else ArkMusic.stop(1);
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('[data-radio]');
    if (!b) return;
    var on = !radioOn();
    UI.store.set('radio', on);
    b.classList.toggle('on', on); b.setAttribute('aria-pressed', String(on)); b.title = on ? 'Office radio on' : 'Office radio off';
    UI.toast(on ? 'Office radio on' : 'Office radio off');
    syncRadio();
  });

  UI.shell = {
    header: function (me, active) {
      var nav = UI.navPages();
      return '<div class="ui-header-in">' + brand() +
        (me ? '<nav class="ui-nav" aria-label="Main">' + nav.map(function (p) {
          return '<a href="#' + p.name + '" class="' + (p.name === active ? 'on' : '') + '">' + UI.icon(p.icon) + '<span>' + esc(p.nav) + '</span></a>';
        }).join('') + '</nav>' : '') +
        '<div class="ui-header-right">' + (me ? radioButton() : '') +
        (me ? '<button type="button" class="ui-avatar-btn" data-menu-toggle aria-label="Your account" aria-haspopup="true">' + esc(UI.initials(me.name)) + '</button>' + userMenu(me)
          : (active === 'auth' ? '' : '<a class="ui-btn ghost" href="#auth" data-go="auth">Sign in</a><a class="ui-btn primary" href="#auth/signup" data-go="auth/signup">Get started</a>')) +
        '</div></div>';
    },
    footer: function (me) {
      return '<div class="ui-footer-in"><div class="ui-footer-brand">' + brand() + '<p class="muted small">' + esc(UI.config.tagline) + '</p></div>' +
        '<div class="ui-footer-links">' +
        '<a href="#landing" data-go="landing">About</a>' +
        (me ? '<a href="#kit" data-go="kit">Field Kit</a>' : '') +
        '<a href="https://prepsto.com/#f/4jv2pps" target="_blank" rel="noopener" data-prepsto-open>Submit feedback</a>' +
        '<button type="button" data-lk-open="overview">Privacy &amp; Terms</button>' +
        '</div><p class="ui-footer-legal small muted">© ' + new Date().getFullYear() + ' ' + esc(UI.config.name) + '. For education. All people, companies and websites in the case files are fictional. Osinty does not license you as a private investigator.</p></div>';
    },
    tabbar: function (me, active) {
      var nav = UI.navPages();
      if (!me || nav.length < 2) return '';
      return nav.slice(0, 4).map(function (p) {
        return '<a href="#' + p.name + '" class="' + (p.name === active ? 'on' : '') + '">' + UI.icon(p.icon) + '<span>' + esc(p.nav) + '</span></a>';
      }).join('') + '<a href="#profile" class="' + (active === 'profile' ? 'on' : '') + '">' + UI.icon('user') + '<span>Dossier</span></a>';
    },
    wire: function (root) {
      root.addEventListener('click', function (e) {
        var t = e.target.closest('[data-menu-toggle]');
        var menu = root.querySelector('[data-menu]');
        if (t && menu) { menu.hidden = !menu.hidden; t.setAttribute('aria-expanded', String(!menu.hidden)); return; }
        if (e.target.closest('[data-signout]')) { UI.auth('logout').then(function () { UI.toast('Signed out. See you soon!'); }); }
        if (menu && !menu.hidden && !e.target.closest('[data-menu] .ui-seg')) menu.hidden = true;
      });
      document.addEventListener('keydown', function (e) {
        var menu = root.querySelector('[data-menu]');
        if (e.key === 'Escape' && menu) menu.hidden = true;
      });
    },
    onTheme: function () {  // redraw the menu's Auto/Light/Dark buttons and keep the menu open
      var menu = document.querySelector('[data-menu]'), open = menu && !menu.hidden;
      UI.renderChrome();
      if (open) document.querySelector('[data-menu]').hidden = false;
    }
  };
})();


/* ===== _arkmusic.html ===== */
/* ark-music.js: the shared background-music player for Arkvital apps (canonical copy:
   APP_MAKER/media/public/ark-music.js; tools/music_sync.py copies it into each app).
   The music files are on Firebase Hosting: https://arkvital-media.web.app/music/<slug>.mp3
   (track list and which app uses what: APP_MAKER/media/manifest.json). Set window.ARK_MEDIA_BASE first to move them.

   ArkMusic.play('dont-stress-out')            loop one track
   ArkMusic.play(['cosmic', 'high-notes'])     playlist, loops the list
   ArkMusic.play(list, {shuffle: true, volume: 0.5, fade: 2, from: 'random'})
   ArkMusic.stop(fadeSeconds)                  fade out and stop
   ArkMusic.volume(0..1)                       app's music volume (slider)
   ArkMusic.duck(0..1)                         extra dip, e.g. 0.3 while a voice speaks; duck(1) to undo
   ArkMusic.enabled(bool)                      off = silent and nothing loads; on = resumes the last request
   ArkMusic.pause() / ArkMusic.resume()        hold the track where it is (a paused session), then carry on
   ArkMusic.onfail(fn)                         fn(slug) when a file can't load (play your synth music instead)
   ArkMusic.current()                          slug playing now, or null
   ArkMusic.state()                            {slug, time, paused, list, ...} for tests

   Volume goes through Web Audio when it can (iPhones ignore <audio>.volume), so the files are served with CORS.
   Browsers block sound until the first tap or key press; requests made before that start on the first gesture. */
(function () {
  if (window.ArkMusic) return;
  var BASE = (window.ARK_MEDIA_BASE || 'https://arkvital-media.web.app/') + 'music/';
  var ctx = null, master = null, useGraph = true;
  var vol = 0.6, duckLvl = 1, on = true, held = false, failFns = [];
  var want = null;          // last request {list, opts}
  var cur = null;           // {el, gain, slug}
  var unlocked = false, pendingStart = false, idx = 0, order = [];

  function graph() {
    if (ctx || !useGraph) return ctx;
    try {
      var AC = window.AudioContext || window.webkitAudioContext;
      ctx = new AC(); master = ctx.createGain(); master.connect(ctx.destination);
    } catch (e) { useGraph = false; ctx = null; }
    return ctx;
  }
  function level() { return on ? vol * duckLvl : 0; }
  function applyMaster(t) {
    t = t == null ? 0.25 : t;
    if (master) { var now = ctx.currentTime; master.gain.cancelScheduledValues(now); master.gain.setTargetAtTime(level(), now, t / 3); }
    else if (cur) cur.el.volume = Math.max(0, Math.min(1, level() * cur.mix));
  }

  function makeVoice(slug) {
    var el = new Audio();
    el.crossOrigin = 'anonymous'; el.preload = 'auto'; el.src = BASE + slug + '.mp3';
    var v = { el: el, slug: slug, gain: null, mix: 0 };
    if (graph()) {
      try { var src = ctx.createMediaElementSource(el); v.gain = ctx.createGain(); v.gain.gain.value = 0; src.connect(v.gain); v.gain.connect(master); }
      catch (e) { v.gain = null; }
    }
    el.addEventListener('error', function () { if (cur === v) { failFns.forEach(function (f) { try { f(slug); } catch (e) {} }); cur = null; } });
    el.addEventListener('ended', function () { if (cur === v) advance(); });
    return v;
  }
  function fadeVoice(v, to, sec, then) {
    if (v.gain) {
      var now = ctx.currentTime; v.gain.gain.cancelScheduledValues(now);
      v.gain.gain.setValueAtTime(v.gain.gain.value, now); v.gain.gain.linearRampToValueAtTime(to, now + Math.max(0.01, sec));
      v.mix = to; if (then) setTimeout(then, sec * 1000 + 30);
      return;
    }
    var from = v.mix, t0 = Date.now(), dur = Math.max(10, sec * 1000);
    (function step() {
      var k = Math.min(1, (Date.now() - t0) / dur); v.mix = from + (to - from) * k;
      v.el.volume = Math.max(0, Math.min(1, level() * v.mix));
      if (k < 1) setTimeout(step, 40); else if (then) then();
    })();
  }
  function retire(v, sec) { fadeVoice(v, 0, sec, function () { try { v.el.pause(); v.el.removeAttribute('src'); v.el.load(); } catch (e) {} }); }

  function startSlug(slug, opts) {
    var old = cur, fade = opts.fade == null ? 1.5 : opts.fade;
    var v = makeVoice(slug); cur = v;
    v.el.loop = order.length === 1 && opts.loop !== false;
    if (opts.from === 'random' && !old) {
      v.el.addEventListener('loadedmetadata', function once() { v.el.removeEventListener('loadedmetadata', once); if (v.el.duration > 60) v.el.currentTime = Math.random() * v.el.duration * 0.6; });
    }
    if (old) retire(old, fade);
    if (ctx && ctx.state === 'suspended') ctx.resume().catch(function () {});
    var p = v.el.play();
    if (p && p.catch) p.catch(function (e) { if (e && e.name === 'NotAllowedError') { pendingStart = true; } });
    applyMaster(0); fadeVoice(v, 1, old ? fade : Math.min(fade, 1));
  }
  function advance() {
    if (!want || !order.length) return;
    idx = (idx + 1) % order.length;
    if (idx === 0 && want.opts.shuffle) order = shuffled(order);
    startSlug(order[idx], want.opts);
  }
  function shuffled(a) { a = a.slice(); for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
  function same(a, b) { return a && b && a.length === b.length && a.every(function (x, i) { return x === b[i]; }); }

  function gesture() {
    unlocked = true;
    if (ctx && ctx.state === 'suspended') ctx.resume().catch(function () {});
    if (pendingStart && cur && on && !held) { pendingStart = false; var p = cur.el.play(); if (p && p.catch) p.catch(function () { pendingStart = true; }); }
  }
  ['pointerdown', 'keydown', 'touchend', 'click'].forEach(function (ev) { window.addEventListener(ev, gesture, { capture: true, passive: true }); });
  document.addEventListener('visibilitychange', function () {
    if (!cur) return;
    if (document.hidden) { cur.el.pause(); } else if (on && want && !held) { var p = cur.el.play(); if (p && p.catch) p.catch(function () { pendingStart = true; }); }
  });

  window.ArkMusic = {
    base: BASE,
    url: function (slug) { return BASE + slug + '.mp3'; },
    play: function (list, opts) {
      opts = opts || {}; list = [].concat(list || []).filter(Boolean);
      if (opts.volume != null) vol = +opts.volume;
      if (!list.length) return this.stop(opts.fade);
      if (want && same(want.list, list) && cur) { if (held) this.resume(); applyMaster(); return this; }  // already playing this
      held = false;
      want = { list: list, opts: opts };
      order = opts.shuffle ? shuffled(list) : list.slice(); idx = 0;
      if (on) startSlug(order[0], opts);
      return this;
    },
    pause: function () {
      if (!cur || held) return this;
      held = true; var v = cur;
      fadeVoice(v, 0, 0.5, function () { if (held && cur === v) v.el.pause(); });
      return this;
    },
    resume: function () {
      if (!held) return this;
      held = false;
      if (cur && on) { var p = cur.el.play(); if (p && p.catch) p.catch(function () { pendingStart = true; }); fadeVoice(cur, 1, 0.8); }
      return this;
    },
    stop: function (fade) {
      want = null; pendingStart = false; held = false;
      if (cur) { retire(cur, fade == null ? 1 : fade); cur = null; }
      return this;
    },
    volume: function (v) { if (v == null) return vol; vol = Math.max(0, Math.min(1, +v)); applyMaster(); return this; },
    duck: function (k, sec) { duckLvl = Math.max(0, Math.min(1, k == null ? 1 : +k)); applyMaster(sec == null ? 0.4 : sec); return this; },
    enabled: function (b) {
      if (b == null) return on;
      b = !!b; if (b === on) return this; on = b;
      if (!on) { if (cur) { var c = cur; cur = null; retire(c, 0.6); } }
      else if (want) { var w = want; want = null; this.play(w.list, w.opts); }
      return this;
    },
    onfail: function (fn) { failFns.push(fn); return this; },
    current: function () { return cur ? cur.slug : null; },
    state: function () {  // for tests: what is playing and how far in
      return { slug: cur ? cur.slug : null, time: cur ? cur.el.currentTime : 0, paused: cur ? cur.el.paused : true, held: held,
        on: on, volume: vol, duck: duckLvl, list: want ? want.list.slice() : [], webAudio: !!(cur && cur.gain) };
    },
    unlocked: function () { return unlocked; }
  };
})();

/* ===== _osinty.html ===== */
(function () {
  var I = UI.ICONS;
  I.eye = '<path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>';
  I.book = '<path d="M4 4.5A1.5 1.5 0 0 1 5.5 3H20v15H5.5A1.5 1.5 0 0 0 4 19.5z"/><path d="M4 19.5A1.5 1.5 0 0 0 5.5 21H20v-3"/><path d="M8 7h8"/>';
  I.award = '<circle cx="12" cy="9" r="6"/><path d="m8.5 14-1.5 7 5-3 5 3-1.5-7"/>';
  I.bolt = '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>';
  I.folder = '<path d="M3 6a2 2 0 0 1 2-2h4l2 2.5h8a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>';
  I.crown = '<path d="M3 8l4 4 5-7 5 7 4-4-2 11H5z"/>';
  I.link = '<path d="M10 14a4.5 4.5 0 0 0 6.4 0l3-3a4.5 4.5 0 0 0-6.4-6.4l-1 1"/><path d="M14 10a4.5 4.5 0 0 0-6.4 0l-3 3a4.5 4.5 0 0 0 6.4 6.4l1-1"/>';
  I.flame = '<path d="M12 22c4 0 7-2.7 7-7 0-4-3-6.5-4-10-1.5 2-2 3.5-2 5-1.5-1-2.5-2.5-3-4-2 2.5-5 5.5-5 9 0 4.3 3 7 7 7z"/>';
  I.tool = '<path d="M14.5 6.5a4 4 0 0 0 5 5L21 13l-8 8-2-2 3-3-3-3-3 3-2-2 8-8z"/><path d="M14.5 6.5 17 4"/>';
  I.briefcase = '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M3 13h18"/>';
  I.terminal = '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 9 3 3-3 3M13 15h4"/>';
  I.fingerprint = '<path d="M12 11v3c0 2.5-.8 4.5-2 6"/><path d="M8.5 9.5a3.5 3.5 0 0 1 7 0v3.5c0 1.8-.3 3.4-.9 4.8"/><path d="M5.5 15.5c.3-1.2.5-2.5.5-4a6 6 0 0 1 12 0v1.5c0 1.2-.1 2.3-.3 3.3"/><path d="M4 9a8.5 8.5 0 0 1 16 0"/>';
  I.target = '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.3"/>';
  I.pushpin = '<path d="M9 3h6l-1 6 3 3H7l3-3z"/><path d="M12 12v9"/>';
  I.print = '<path d="M6 9V3h12v6"/><rect x="3" y="9" width="18" height="8" rx="2"/><path d="M6 14h12v7H6z"/>';
  I.hat = '<path d="M2.5 15.5c3.5 2 15.5 2 19 0"/><path d="M6 15l1.4-7.4c.3-1.5 2-2.1 3.2-1.2l1.4 1 1.4-1c1.2-.9 2.9-.3 3.2 1.2L18 15"/><path d="M6.5 12c3.5 1.1 7.5 1.1 11 0"/>';
  I.board = '<rect x="3" y="4" width="18" height="15" rx="1.5"/><circle cx="8" cy="9" r="1.2"/><circle cx="16" cy="8" r="1.2"/><circle cx="11" cy="15" r="1.2"/><path d="m8 9 8-1M8 9l3 6"/>';
  I.play = '<path d="M7 4v16l13-8z"/>';
  I.key = '<circle cx="8" cy="15" r="4"/><path d="m11 12 9-9M17 6l3 3M14 9l2 2"/>';

  /* ------------------------------------------------------------------ the Field Kit library (real tools) */
  var CATS = {
    search: 'Search engines', archive: 'Archives & capture', people: 'People & usernames', images: 'Images & video',
    geo: 'Maps & geolocation', companies: 'Companies & money', domains: 'Domains & infrastructure', transport: 'Planes & ships',
    method: 'Method & community'
  };
  var TOOLS = [
    { id: 'googleadvanced', name: 'Google Advanced Search', cat: 'search', cost: 'Free', url: 'https://www.google.com/advanced_search', what: 'A form for operators: exact phrases, sites, file types, dates.', tip: 'Learn the operators here, then type them directly.' },
    { id: 'bing', name: 'Bing', cat: 'search', cost: 'Free', url: 'https://www.bing.com', what: 'A different index, plus operators like ip: and inbody:.', tip: 'Repeat every important dork here.' },
    { id: 'yandex', name: 'Yandex Images', cat: 'images', cost: 'Free', url: 'https://yandex.com/images/', what: 'Reverse image search known for faces, buildings and landmarks.', tip: 'Crop to the face or the building before uploading.' },
    { id: 'googlelens', name: 'Google Lens', cat: 'images', cost: 'Free', url: 'https://lens.google/', what: 'Reverse image search for objects, products, places and text.', tip: 'Select just one region of the image for sharper matches.' },
    { id: 'bingvisual', name: 'Bing Visual Search', cat: 'images', cost: 'Free', url: 'https://www.bing.com/visualsearch', what: 'Microsoft\'s reverse image search, with different results again.', tip: 'Good for finding the same photo at other sizes.' },
    { id: 'tineye', name: 'TinEye', cat: 'images', cost: 'Freemium', url: 'https://tineye.com', what: 'Finds exact copies of an image and sorts them by date.', tip: 'Sort by "Oldest" to find the source.' },
    { id: 'invid', name: 'InVID-WeVerify plugin', cat: 'images', cost: 'Free', url: 'https://www.invid-project.eu/tools-and-services/invid-verification-plugin/', what: 'Browser plugin to split videos into keyframes and verify them.', tip: 'Reverse-search several keyframes, not just the first.' },
    { id: 'exiftool', name: 'ExifTool', cat: 'images', cost: 'Free', url: 'https://exiftool.org', what: 'The reference tool for reading metadata in photos, videos and documents.', tip: 'Run it on PDFs and Office files too: authors leak.' },
    { id: 'forensically', name: 'Forensically', cat: 'images', cost: 'Free', url: 'https://29a.ch/photo-forensics/', what: 'In-browser photo forensics: clone detection, error level analysis, metadata.', tip: 'Edits leave traces; but read the help before concluding anything.' },
    { id: 'wayback', name: 'Wayback Machine', cat: 'archive', cost: 'Free', url: 'https://web.archive.org', what: 'Hundreds of billions of archived web pages since 1996, and "Save Page Now".', tip: 'Type a domain followed by /* to list every URL it knows.' },
    { id: 'archivetoday', name: 'archive.today', cat: 'archive', cost: 'Free', url: 'https://archive.ph', what: 'On-demand page captures, including some sites other archivers can\'t reach.', tip: 'Capture key pages yourself before they change.' },
    { id: 'hunchly', name: 'Hunchly', cat: 'archive', cost: 'Paid', url: 'https://www.hunch.ly', what: 'Captures every page you visit during a case, with hashes and notes.', tip: 'The professional way to keep a chain of custody.' },
    { id: 'whatsmyname', name: 'WhatsMyName', cat: 'people', cost: 'Free', url: 'https://whatsmyname.app', what: 'Checks a username on hundreds of websites at once.', tip: 'Confirm every hit with a shared detail; namesakes abound.' },
    { id: 'sherlock', name: 'Sherlock', cat: 'people', cost: 'Free', url: 'https://github.com/sherlock-project/sherlock', what: 'Open-source command-line username search across many sites.', tip: 'Great for batches of username variants.' },
    { id: 'hibp', name: 'Have I Been Pwned', cat: 'people', cost: 'Free', url: 'https://haveibeenpwned.com', what: 'Shows which known data breaches an email appears in (never the data).', tip: 'Breach names hint at which sites someone used.' },
    { id: 'courtlistener', name: 'CourtListener', cat: 'people', cost: 'Free', url: 'https://www.courtlistener.com', what: 'Free search of US court opinions and many federal dockets.', tip: 'Search names with and without middle initials.' },
    { id: 'canlii', name: 'CanLII', cat: 'people', cost: 'Free', url: 'https://www.canlii.org', what: 'Canadian court and tribunal decisions, free.', tip: 'Use quotes and the province filter.' },
    { id: 'opencorporates', name: 'OpenCorporates', cat: 'companies', cost: 'Freemium', url: 'https://opencorporates.com', what: 'Company records from 100+ jurisdictions in one search.', tip: 'Search officers (people), not just companies.' },
    { id: 'companieshouse', name: 'UK Companies House', cat: 'companies', cost: 'Free', url: 'https://find-and-update.company-information.service.gov.uk/', what: 'Every UK company: directors, filings, addresses, history.', tip: 'Click a director to see all their appointments.' },
    { id: 'edgar', name: 'SEC EDGAR', cat: 'companies', cost: 'Free', url: 'https://www.sec.gov/edgar/search/', what: 'Filings of US public companies and their insiders.', tip: 'Full-text search finds names buried in filings.' },
    { id: 'offshoreleaks', name: 'ICIJ Offshore Leaks', cat: 'companies', cost: 'Free', url: 'https://offshoreleaks.icij.org', what: 'Entities and people from the Panama, Paradise and Pandora papers.', tip: 'Search addresses too: offshore agents reuse them.' },
    { id: 'opensanctions', name: 'OpenSanctions', cat: 'companies', cost: 'Freemium', url: 'https://www.opensanctions.org', what: 'Sanctions lists, politically exposed persons and watchlists combined.', tip: 'A must for due-diligence work.' },
    { id: 'viewdns', name: 'ViewDNS.info', cat: 'domains', cost: 'Freemium', url: 'https://viewdns.info', what: 'WHOIS, reverse IP, reverse WHOIS, DNS history and more.', tip: 'Reverse IP shows other sites on the same server.' },
    { id: 'crtsh', name: 'crt.sh', cat: 'domains', cost: 'Free', url: 'https://crt.sh', what: 'Certificate-transparency logs: every TLS certificate issued for a domain.', tip: 'Search %.domain.com to uncover hidden subdomains.' },
    { id: 'dnsdumpster', name: 'DNSDumpster', cat: 'domains', cost: 'Freemium', url: 'https://dnsdumpster.com', what: 'Maps a domain\'s DNS records and hosts.', tip: 'Shared mail servers can link organisations.' },
    { id: 'urlscan', name: 'urlscan.io', cat: 'domains', cost: 'Freemium', url: 'https://urlscan.io', what: 'Loads a page in a sandbox and shows everything it contacts.', tip: 'Search past scans for a tracking ID or IP.' },
    { id: 'shodan', name: 'Shodan', cat: 'domains', cost: 'Freemium', url: 'https://www.shodan.io', what: 'A search engine for internet-connected devices and servers.', tip: 'Look, never touch: logging into devices is unauthorised access.' },
    { id: 'googleearth', name: 'Google Earth', cat: 'geo', cost: 'Free', url: 'https://earth.google.com', what: 'Satellite imagery, 3D terrain and historical imagery (desktop).', tip: 'The historical imagery slider dates construction.' },
    { id: 'streetview', name: 'Google Street View', cat: 'geo', cost: 'Free', url: 'https://www.google.com/maps', what: 'Stand where the photographer stood.', tip: 'Check older capture dates when the scene changed.' },
    { id: 'mapillary', name: 'Mapillary', cat: 'geo', cost: 'Free', url: 'https://www.mapillary.com', what: 'Crowd-sourced street-level photos, often where Street View isn\'t.', tip: 'Great for back roads and newer areas.' },
    { id: 'overpass', name: 'Overpass Turbo', cat: 'geo', cost: 'Free', url: 'https://overpass-turbo.eu', what: 'Query OpenStreetMap: "every church within 200 m of a river bridge".', tip: 'Turns a vague scene into a short list of candidates.' },
    { id: 'suncalc', name: 'SunCalc', cat: 'geo', cost: 'Free', url: 'https://www.suncalc.org', what: 'Sun position and shadow direction for any place, date and time.', tip: 'Drag the time slider until the shadows match.' },
    { id: 'sentinel', name: 'Sentinel Hub EO Browser', cat: 'geo', cost: 'Freemium', url: 'https://apps.sentinel-hub.com/eo-browser/', what: 'Free recent satellite imagery, updated every few days.', tip: 'See fires, floods and new construction.' },
    { id: 'flightradar', name: 'Flightradar24', cat: 'transport', cost: 'Freemium', url: 'https://www.flightradar24.com', what: 'Live and historical flight tracking by registration or flight number.', tip: 'Private jets often reveal their owners\' movements.' },
    { id: 'marinetraffic', name: 'MarineTraffic', cat: 'transport', cost: 'Freemium', url: 'https://www.marinetraffic.com', what: 'Ship positions and port calls from AIS signals.', tip: 'Yachts have names and IMO/MMSI numbers to pivot on.' },
    { id: 'osintframework', name: 'OSINT Framework', cat: 'method', cost: 'Free', url: 'https://osintframework.com', what: 'A clickable map of hundreds of OSINT resources by category.', tip: 'Start here when you don\'t know which source holds a record.' },
    { id: 'bellingcat', name: 'Bellingcat Online Investigations Toolkit', cat: 'method', cost: 'Free', url: 'https://bellingcat.gitbook.io/toolkit', what: 'A curated, maintained guide to investigation tools.', tip: 'Read the guides, not just the links.' },
    { id: 'tracelabs', name: 'Trace Labs', cat: 'method', cost: 'Free', url: 'https://www.tracelabs.org', what: 'Ethical search-party events finding leads on real missing-persons cases.', tip: 'The best real-world practice there is, for a good cause.' },
    { id: 'maltego', name: 'Maltego', cat: 'method', cost: 'Freemium', url: 'https://www.maltego.com', what: 'Graph tool to link people, domains, companies and more.', tip: 'The Community edition is enough to learn.' },
    { id: 'spiderfoot', name: 'SpiderFoot', cat: 'method', cost: 'Free', url: 'https://github.com/smicallef/spiderfoot', what: 'Open-source automation that runs many lookups on one selector.', tip: 'Automation finds leads; you still verify them.' }
  ];
  /* Gadgets: interactive helpers built into the kit page (#kit/<id>). */
  var GADGETS = [
    { id: 'dorkbuilder', name: 'Dork Builder', icon: 'search', what: 'Build precise search-engine queries with operators.' },
    { id: 'permutator', name: 'Username Permutator', icon: 'users', what: 'Turn a name into the usernames people actually pick.' },
    { id: 'emailperm', name: 'Email Permutator', icon: 'mail', what: 'List the likely work-email formats for a person and a domain.' },
    { id: 'exifreader', name: 'EXIF Reader', icon: 'camera', what: 'Read a photo\'s hidden metadata, privately in your browser.' },
    { id: 'snowflake', name: 'ID & Time Decoder', icon: 'clock', what: 'Turn social-media post IDs and Unix timestamps into dates.' },
    { id: 'grader', name: 'Source Grader', icon: 'target', what: 'Grade a source and a piece of information with the Admiralty code.' }
  ];

  function md(text) {
    var s = UI.esc(text || '');
    s = s.replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>');
    return s.replace(/\n/g, '<br>');
  }
  function paras(list) { return '<div class="os-md">' + (list || []).map(function (p) { return '<p>' + md(p) + '</p>'; }).join('') + '</div>'; }

  var RANK_COLORS = ['#8a7d69', '#7a5a3a', '#5d6f4a', '#3f6a7a', '#8f1d21', '#a8761f', '#c9a227'];
  function shield(level, cls) {
    var c = RANK_COLORS[Math.max(0, Math.min(RANK_COLORS.length - 1, (level || 1) - 1))];
    var stars = '';
    var n = Math.min(level || 1, 7);
    for (var i = 0; i < n; i++) {
      var x = 32 - (n - 1) * 4.5 + i * 9;
      stars += '<path transform="translate(' + x + ' 52) scale(.45)" d="M0-9 2.6-2.8 9.4-2.8 3.9 1.3 6 7.9 0 4 -6 7.9 -3.9 1.3 -9.4-2.8 -2.6-2.8z" fill="#f6ecd6"/>';
    }
    return '<svg class="shield ' + (cls || '') + '" viewBox="0 0 64 72" aria-hidden="true"><path d="M32 3 58 12v20c0 18-11 31-26 37C17 63 6 50 6 32V12z" fill="' + c + '" stroke="#1d1714" stroke-opacity=".35" stroke-width="2"/>' +
      '<path d="M32 9 52 16v16c0 14-8.5 24.5-20 29.5C20.5 56.5 12 46 12 32V16z" fill="none" stroke="#f6ecd6" stroke-opacity=".55" stroke-width="1.6"/>' +
      '<g transform="translate(32 30)" fill="none" stroke="#f6ecd6" stroke-width="3.2" stroke-linecap="round"><circle cx="-2" cy="-2" r="8"/><path d="M4 4l7 7"/></g>' + stars + '</svg>';
  }
  function rankBadge(me) { return '<span class="os-rank">' + shield(me.level) + '<span>' + UI.esc(me.rank) + '</span></span>'; }

  /* XP gained, a promotion, new badges: stamp, toasts, a promotion card. */
  function celebrate(res) {
    if (!res) return;
    if (res.xp_gained > 0) {
      var pop = document.createElement('div');
      pop.className = 'ui os-xp-pop';
      pop.textContent = '+' + res.xp_gained + ' XP';
      document.body.appendChild(pop);
      setTimeout(function () { pop.remove(); }, 2200);
    }
    (res.badges || []).forEach(function (b, i) {
      setTimeout(function () { UI.toast('Badge unlocked: ' + b.name, 'ok'); }, 700 + i * 500);
    });
    if (res.rank_up && res.me) {
      setTimeout(function () {
        UI.modal('<div class="os-promo">' + shield(res.me.level) + '<div class="os-stamp">Promoted</div><h2>You\'re now a ' + UI.esc(res.rank_up) + '</h2>' +
          '<p class="muted">' + UI.esc(res.me.xp) + ' XP on file.' + (res.me.next ? ' Next rank: ' + UI.esc(res.me.next) + ' at ' + res.me.next_xp + ' XP.' : ' The top of the Bureau. Respect.') + '</p>' +
          '<button class="ui-btn primary" data-close>Back to work</button></div>');
      }, 900);
    }
  }

  function toolById(id) {
    for (var i = 0; i < TOOLS.length; i++) if (TOOLS[i].id === id) return TOOLS[i];
    for (var j = 0; j < GADGETS.length; j++) if (GADGETS[j].id === id) return GADGETS[j];
    return null;
  }
  function toolChip(id) {
    var t = toolById(id);
    if (!t) return '';
    if (t.url) return '<a class="ui-badge" href="' + UI.esc(t.url) + '" target="_blank" rel="noopener">' + UI.icon('external') + UI.esc(t.name) + '</a>';
    return '<a class="ui-badge brand" href="#kit/' + t.id + '" data-go="kit/' + t.id + '">' + UI.icon(t.icon || 'tool') + UI.esc(t.name) + '</a>';
  }

  /* The Admiralty (NATO) grading system: source reliability A-F, information credibility 1-6. */
  var REL = { A: 'Completely reliable', B: 'Usually reliable', C: 'Fairly reliable', D: 'Not usually reliable', E: 'Unreliable', F: 'Reliability cannot be judged' };
  var CRED = { 1: 'Confirmed by other sources', 2: 'Probably true', 3: 'Possibly true', 4: 'Doubtful', 5: 'Improbable', 6: 'Truth cannot be judged' };

  window.OS = { REL: REL, CRED: CRED, TOOLS: TOOLS, GADGETS: GADGETS, CATS: CATS, md: md, paras: paras, shield: shield, rankBadge: rankBadge,
    celebrate: celebrate, toolById: toolById, toolChip: toolChip };
})();

/* ===== academy.html ===== */
(function () {
  var esc = UI.esc;

  function list(view) {
    return UI.api('get_academy').then(function (d) {
      var pct = Math.round(100 * d.done / d.total);
      view.innerHTML = '<div class="ui-wrap"><div class="ac-head"><div><div class="eyebrow">The Academy</div><h1>Training files</h1>' +
        '<p class="muted" style="margin:6px 0 0;max-width:40em">Eight modules, from the investigator\'s mindset to running a practice. Pass a lesson\'s quiz (2 of 3) for 30 XP; a perfect score adds 10.</p></div>' +
        '<div class="ac-prog"><div class="os-label"><span>Progress</span><span>' + d.done + '/' + d.total + '</span></div><div class="os-bar"><i style="width:' + pct + '%"></i></div></div></div>' +
        '<div class="ac-mods">' + d.modules.map(function (m) {
          var all = m.done === m.lessons.length;
          return '<section class="os-folder ac-mod" data-tab="Module ' + m.num + ' · ' + esc(m.tag) + '">' +
            (all ? '<span class="os-stamp good">Passed</span>' : m.done ? '<span class="os-stamp warn">' + m.done + '/' + m.lessons.length + '</span>' : '') +
            '<h2>' + UI.icon(m.icon) + esc(m.title) + '</h2><p>' + esc(m.blurb) + '</p>' +
            '<ol class="ac-lessons">' + m.lessons.map(function (l) {
              return '<li class="' + (l.done ? 'done' : '') + '"><a href="#academy/' + esc(l.id) + '" data-go="academy/' + esc(l.id) + '">' +
                '<span class="n">' + (l.done ? UI.icon('check') : esc(l.num)) + '</span><span class="t">' + esc(l.title) + '</span>' +
                '<span class="m">' + (l.done ? l.score + '/' + l.total : l.minutes + ' min') + '</span></a></li>';
            }).join('') + '</ol></section>';
        }).join('') + '</div></div>';
    });
  }

  function lesson(view, id) {
    return UI.api('get_lesson', id).then(function (d) {
      var L = d.lesson;
      document.title = L.title + ' · ' + UI.config.name;
      view.innerHTML = '<div class="ui-wrap"><div class="ls-wrap">' +
        '<div class="ls-crumb"><a href="#academy" data-go="academy">Academy</a><span>/</span><span>Module ' + d.module.num + ': ' + esc(d.module.title) + '</span></div>' +
        '<article class="ls-sheet"><div class="eyebrow">Lesson ' + esc(d.num) + ' · ' + esc(d.module.tag) + '</div><h1>' + esc(L.title) + '</h1>' +
          '<div class="ls-meta"><span class="ui-badge">' + UI.icon('clock') + L.minutes + ' min read</span>' +
          (d.best ? '<span class="ui-badge good">' + UI.icon('check') + 'Passed · best ' + d.best.score + '/' + d.best.total + '</span>' : '<span class="ui-badge brand">' + UI.icon('bolt') + 'Up to 40 XP</span>') + '</div>' +
          '<div class="ls-body">' + OS.paras(L.body) + '</div>' +
          '<div class="ls-box"><h3>' + UI.icon('target') + 'In the field</h3><ol class="ls-steps">' + L.steps.map(function (s) { return '<li>' + OS.md(s) + '</li>'; }).join('') + '</ol></div>' +
          (L.tools.length ? '<div class="ls-box"><h3>' + UI.icon('tool') + 'Tools for this</h3><div class="ls-tools">' + L.tools.map(OS.toolChip).join('') + '</div></div>' : '') +
          '<div class="ls-note"><b>Field note</b>' + OS.md(L.field_note) + '</div>' +
          '<form class="ls-quiz" data-quiz><h2>' + UI.icon('edit') + 'Pop quiz</h2><p class="muted small">Two out of three to pass. The answers are checked at HQ.</p><div data-result></div>' +
            L.quiz.map(function (q, qi) {
              return '<fieldset class="ls-q" data-q="' + qi + '"><legend><span>Q' + (qi + 1) + '</span>' + esc(q.q) + '</legend>' + q.options.map(function (o, oi) {
                return '<label class="ls-opt"><input type="radio" name="q' + qi + '" value="' + oi + '" required><span>' + esc(o) + '</span></label>';
              }).join('') + '<div data-why></div></fieldset>';
            }).join('') +
            '<div class="ui-row"><button class="ui-btn primary" type="submit">' + UI.icon('check') + 'Hand in</button><button class="ui-btn ghost" type="button" data-retry hidden>' + UI.icon('refresh') + 'Try again</button></div></form>' +
        '</article>' +
        '<div class="ls-nav">' + (d.prev ? '<a class="ui-btn" href="#academy/' + esc(d.prev) + '" data-go="academy/' + esc(d.prev) + '">' + UI.icon('back') + 'Previous lesson</a>' : '<span></span>') +
          (d.next ? '<a class="ui-btn" href="#academy/' + esc(d.next) + '" data-go="academy/' + esc(d.next) + '">Next lesson ' + UI.icon('arrow') + '</a>' : '<a class="ui-btn" href="#cases" data-go="cases">On to the case files ' + UI.icon('arrow') + '</a>') +
        '</div></div></div>';
      var form = view.querySelector('[data-quiz]');
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var answers = L.quiz.map(function (_q, qi) { var c = form.querySelector('input[name=q' + qi + ']:checked'); return c ? parseInt(c.value, 10) : -1; });
        if (answers.indexOf(-1) >= 0) { UI.toast('Answer every question first.', 'error'); return; }
        UI.busy(form.querySelector('[type=submit]'), UI.api('submit_quiz', L.id, answers)).then(function (r) {
          r.results.forEach(function (res, qi) {
            var fs = form.querySelector('[data-q="' + qi + '"]');
            fs.querySelectorAll('.ls-opt').forEach(function (lab, oi) {
              lab.classList.toggle('right', oi === res.answer);
              lab.classList.toggle('wrong', oi === answers[qi] && !res.correct);
              lab.querySelector('input').disabled = true;
            });
            fs.querySelector('[data-why]').innerHTML = '<div class="ls-why' + (res.correct ? '' : ' no') + '">' + (res.correct ? 'Correct. ' : 'Not quite. ') + esc(res.why) + '</div>';
          });
          form.querySelector('[data-result]').innerHTML = '<div class="ls-result"><span class="os-stamp ' + (r.passed ? 'good' : '') + '">' + (r.passed ? (r.score === r.total ? 'Perfect' : 'Passed') : 'Failed') + '</span>' +
            '<div><b>' + r.score + ' of ' + r.total + ' correct.</b><div class="small muted">' + (r.xp_gained ? '+' + r.xp_gained + ' XP added to your file.' : r.passed ? 'No new XP: you already banked this score.' : 'Read the briefing again and retry: there\'s no penalty.') + '</div></div></div>';
          form.querySelector('[type=submit]').hidden = true;
          form.querySelector('[data-retry]').hidden = false;
          form.querySelector('[data-result]').scrollIntoView({ behavior: 'smooth', block: 'center' });
          OS.celebrate(r);
        });
      });
      form.querySelector('[data-retry]').addEventListener('click', function () { UI.refresh(); });
    });
  }

  UI.page('academy', { title: 'Academy', nav: 'Academy', icon: 'book', auth: 'user', order: 20 }, function (view, ctx) {
    view.innerHTML = '<div class="ui-wrap"><div class="ui-skel" style="height:300px"></div></div>';
    return ctx.args[0] ? lesson(view, ctx.args[0]) : list(view);
  });
})();

/* ===== admin.html ===== */
(function () {
  var esc = UI.esc;
  var TABS = [['overview', 'Overview', 'grid'], ['feedback', 'Feedback', 'inbox'], ['users', 'Users', 'users'], ['training', 'Training', 'book'], ['bulletins', 'Bulletins', 'bell'], ['demo', 'Demo data', 'database']];

  UI.page('admin', { title: 'Admin', auth: 'admin' }, function (view, ctx) {
    var tab = TABS.some(function (t) { return t[0] === ctx.args[0]; }) ? ctx.args[0] : 'overview';
    var fbFilter = 'new';
    view.innerHTML = '<div class="ui-wrap"><div class="ui-page-head"><div><h1>Admin</h1><p class="muted">Only admins see this page.</p></div></div>' +
      '<nav class="ui-tabs">' + TABS.map(function (t) {
        return '<a href="#admin/' + t[0] + '" class="' + (t[0] === tab ? 'on' : '') + '">' + UI.icon(t[2]) + t[1] + '</a>';
      }).join('') + '</nav><div data-body><div class="ui-skel"></div></div></div>';
    var body = view.querySelector('[data-body]');

    function overview() {
      return UI.api('admin_overview').then(function (d) {
        var stat = function (n, label, go) { return '<a class="ui-card ui-stat" href="#admin/' + go + '" style="text-decoration:none;color:inherit"><b>' + n + '</b><span>' + label + '</span></a>'; };
        body.innerHTML = '<div class="ad-stats">' + stat(d.users, 'people signed up', 'users') + stat(d.admins, UI.plural(d.admins, 'admin').replace(/^\d+ /, ''), 'users') +
          stat(d.feedback_new, 'new feedback', 'feedback') + stat(d.lessons_passed, 'lessons passed', 'training') + stat(d.cases_solved, 'cases closed', 'training') +
          stat(d.investigations, 'investigations', 'overview') + '</div>' +
          '<p class="muted small" style="margin-top:18px">Demo data is <b>' + esc(d.demo.state) + '</b> (' + d.demo.counts.agents + ' demo agents). Manage it in the Demo data tab.</p>';
      });
    }

    function feedback() {
      return UI.api('list_feedback', null).then(function (d) {
        var items = d.items.filter(function (i) { return fbFilter === 'all' || i.status === fbFilter; });
        body.innerHTML = '<div class="ui-row" style="margin-bottom:16px"><div class="ui-seg">' + [['new', 'New'], ['read', 'Read'], ['done', 'Done'], ['all', 'All']].map(function (f) {
          var n = f[0] === 'all' ? d.items.length : d.counts[f[0]];
          return '<button data-filter="' + f[0] + '" class="' + (fbFilter === f[0] ? 'on' : '') + '">' + f[1] + ' (' + n + ')</button>';
        }).join('') + '</div></div>' +
          (items.length ? '<div class="ad-fb">' + items.map(function (i) {
            var c = i.context || {};
            return '<div class="ui-item" data-id="' + esc(i.id) + '"><div class="meta"><span class="ui-badge ' + (i.kind === 'bug' ? 'bad' : i.kind === 'idea' ? 'brand' : '') + '">' + esc(i.kind_label) + '</span>' +
              '<b>' + esc(i.name) + '</b>' + (i.email ? '<a href="mailto:' + esc(i.email) + '">' + esc(i.email) + '</a>' : '') + '<span>' + esc(UI.fmtDateTime(i.created)) + '</span></div>' +
              '<p class="msg">' + esc(i.message) + '</p>' +
              '<div class="ctx">' + esc([c.page, c.screen, c.theme, c.browser].filter(Boolean).join(' · ')) + '</div>' +
              '<textarea data-note placeholder="Private note (only admins see it)">' + esc(i.note) + '</textarea>' +
              '<div class="ui-row" style="margin-top:10px">' + ['new', 'read', 'done'].map(function (s) {
                return '<button class="ui-btn sm' + (i.status === s ? ' primary' : '') + '" data-status="' + s + '">' + s[0].toUpperCase() + s.slice(1) + '</button>';
              }).join('') + '<span class="ui-spacer"></span><button class="ui-btn sm danger" data-del-fb>' + UI.icon('trash') + 'Delete</button></div></div>';
          }).join('') + '</div>'
            : '<div class="ui-empty">' + UI.icon('inbox') + '<h3>No ' + (fbFilter === 'all' ? '' : fbFilter + ' ') + 'messages</h3><p>New feedback goes to Prepsto (prepsto.com). Older messages and requests from the app show up here.</p></div>');
      });
    }

    function users(query) {
      return UI.api('list_users', query || null).then(function (d) {
        body.innerHTML = '<form class="ui-row" data-search style="margin-bottom:14px"><input type="search" name="q" placeholder="Search by name or email" value="' + esc(query || '') + '" style="max-width:360px">' +
          '<button class="ui-btn" type="submit">' + UI.icon('search') + 'Search</button><span class="muted small">' + UI.plural(d.total, 'person', 'people') + '</span></form>' +
          '<table class="ad-users"><thead><tr><th>Name</th><th>Email</th><th>Joined</th><th>Admin</th><th>Active</th></tr></thead><tbody>' +
          d.users.map(function (u) {
            return '<tr data-id="' + esc(u.id) + '"><td><b>' + esc(u.name) + '</b></td><td class="email">' + esc(u.email) + '</td><td class="joined muted">' + esc(UI.fmtDate(u.joined)) + '</td>' +
              '<td><label class="ui-check"><input type="checkbox" data-admin' + (u.is_admin ? ' checked' : '') + '> Admin</label></td>' +
              '<td><label class="ui-check"><input type="checkbox" data-enabled' + (u.enabled ? ' checked' : '') + '> Active</label></td></tr>';
          }).join('') + '</tbody></table>';
      });
    }

    function demo() {
      return UI.api('admin_overview').then(function (d) {
        var c = d.demo.counts;
        body.innerHTML = '<div class="ui-card ui-narrow" style="margin:0"><h3>Demo data</h3>' +
          '<p class="muted">Demo agents with progress and solved cases (they fill the Bureau leaderboard) and three bulletins, so the app never looks empty for the first visitors. Demo rows are flagged, so removing them never touches real data. Once removed, it stays removed until you load it again.</p>' +
          '<p>Status: <b>' + esc(d.demo.state) + '</b> · ' + Object.keys(c).map(function (k) { return c[k] + ' ' + esc(k); }).join(', ') + '</p>' +
          '<div class="ui-row"><button class="ui-btn primary" data-demo="load">' + UI.icon('refresh') + (d.demo.state === 'loaded' ? 'Reload demo data' : 'Load demo data') + '</button>' +
          '<button class="ui-btn danger" data-demo="remove">' + UI.icon('trash') + 'Remove demo data</button></div></div>';
      });
    }

    function training() {
      return UI.api('admin_training').then(function (d) {
        var maxP = Math.max.apply(null, d.lessons.map(function (l) { return l.passes; }).concat([1]));
        body.innerHTML = '<h3>Case files</h3><table class="ad-tr"><thead><tr><th>Case</th><th>Started</th><th>Closed</th><th>Avg score</th><th class="hide-sm">Avg hints</th></tr></thead><tbody>' +
          d.cases.map(function (c) {
            return '<tr><td>' + esc(c.title) + '</td><td class="n">' + c.started + '</td><td class="n">' + c.solved + '</td><td class="n">' + (c.avg_score == null ? '–' : c.avg_score) + '</td><td class="n hide-sm">' + (c.avg_hints == null ? '–' : c.avg_hints) + '</td></tr>';
          }).join('') + '</tbody></table>' +
          '<h3 style="margin-top:26px">Lessons</h3><p class="muted small">Passes per lesson. A sharp drop shows where agents stop.</p><table class="ad-tr"><thead><tr><th>#</th><th>Lesson</th><th>Passes</th></tr></thead><tbody>' +
          d.lessons.map(function (l) {
            return '<tr><td class="n">' + esc(l.num) + '</td><td>' + esc(l.title) + '</td><td class="n"><span class="ad-barc" style="width:' + Math.round(80 * l.passes / maxP) + 'px"></span>' + l.passes + '</td></tr>';
          }).join('') + '</tbody></table>';
      });
    }

    function bulletins() {
      return UI.api('admin_bulletins').then(function (d) {
        body.innerHTML = '<form class="ui-card ad-bform" data-bulletin><h3 class="full" style="margin:0">Post a bulletin</h3><p class="muted small full" style="margin:0">It appears in every agent\'s office, newest first (the four latest show).</p>' +
          '<input type="text" name="title" maxlength="100" placeholder="Title" required><select name="kind"><option value="note">Note</option><option value="new">New</option><option value="alert">Alert</option></select>' +
          '<textarea name="body" maxlength="1000" rows="3" placeholder="Message" required></textarea><div class="full ui-row end"><button class="ui-btn primary" type="submit">' + UI.icon('bell') + 'Post</button></div></form>' +
          (d.items.length ? '<div class="ad-fb">' + d.items.map(function (b) {
            return '<div class="ui-item" data-id="' + esc(b.id) + '"><div class="meta"><span class="ui-badge ' + (b.kind === 'alert' ? 'bad' : b.kind === 'new' ? 'good' : '') + '">' + esc(b.kind) + '</span>' +
              '<b>' + esc(b.title) + '</b><span>' + esc(UI.fmtDate(b.created)) + ' · ' + esc(b.author) + '</span>' + (b.demo ? '<span class="ui-badge">Demo</span>' : '') + '</div>' +
              '<p class="msg">' + esc(b.body) + '</p><div class="ui-row end"><button class="ui-btn sm danger" data-del-bul>' + UI.icon('trash') + 'Delete</button></div></div>';
          }).join('') + '</div>' : '<div class="ui-empty">' + UI.icon('bell') + '<h3>No bulletins</h3><p>Post the first one above.</p></div>');
      });
    }

    var DRAW = { overview: overview, feedback: feedback, users: users, training: training, bulletins: bulletins, demo: demo };

    view.addEventListener('click', function (e) {
      var f = e.target.closest('[data-filter]');
      if (f) { fbFilter = f.getAttribute('data-filter'); feedback(); return; }
      var st = e.target.closest('[data-status]');
      if (st) {
        var card = st.closest('[data-id]');
        UI.api('set_feedback_status', card.getAttribute('data-id'), st.getAttribute('data-status'), card.querySelector('[data-note]').value).then(function () { UI.toast('Saved', 'ok'); feedback(); });
        return;
      }
      var del = e.target.closest('[data-del-fb]');
      if (del) {
        UI.confirm({ title: 'Delete this message?', ok: 'Delete', danger: true }).then(function (yes) {
          if (yes) UI.api('delete_feedback', del.closest('[data-id]').getAttribute('data-id')).then(feedback);
        });
        return;
      }
      var db = e.target.closest('[data-del-bul]');
      if (db) {
        UI.confirm({ title: 'Delete this bulletin?', ok: 'Delete', danger: true }).then(function (yes) {
          if (yes) UI.api('delete_bulletin', db.closest('[data-id]').getAttribute('data-id')).then(bulletins);
        });
        return;
      }
      var dm = e.target.closest('[data-demo]');
      if (dm) {
        var load = dm.getAttribute('data-demo') === 'load';
        UI.confirm({ title: load ? 'Load the demo data?' : 'Remove the demo data?', text: load ? 'Demo people and content are added (any old demo rows are replaced).' : 'Every demo row is deleted. Real data stays.', ok: load ? 'Load' : 'Remove', danger: !load })
          .then(function (yes) { if (yes) UI.busy(dm, UI.api(load ? 'demo_load' : 'demo_remove')).then(function () { UI.toast('Done', 'ok'); demo(); }); });
      }
    });
    view.addEventListener('change', function (e) {
      var row = e.target.closest('tr[data-id]');
      if (!row) return;
      var id = row.getAttribute('data-id'), box = e.target;
      var fn = box.hasAttribute('data-admin') ? 'set_admin' : box.hasAttribute('data-enabled') ? 'set_enabled' : null;
      if (fn) UI.api(fn, id, box.checked).then(function () { UI.toast('Saved', 'ok'); }, function (err) { box.checked = !box.checked; UI.toast(err.message, 'error'); });
    });
    view.addEventListener('submit', function (e) {
      if (e.target.matches('[data-search]')) { e.preventDefault(); users(UI.formData(e.target).q); }
      if (e.target.matches('[data-bulletin]')) {
        e.preventDefault();
        var v = UI.formData(e.target);
        UI.busy(e.target.querySelector('[type=submit]'), UI.api('post_bulletin', v.title, v.body, v.kind)).then(function () { UI.toast('Posted', 'ok'); bulletins(); });
      }
    });
    return DRAW[tab]();
  });
})();

/* ===== auth.html ===== */
(function () {
  var esc = UI.esc;
  var GOOGLE_G = '<svg viewBox="0 0 48 48" aria-hidden="true"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>' +
    '<path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>' +
    '<path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>' +
    '<path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>';
  function pw(name, auto) {
    return '<div class="au-pw"><input type="password" name="' + name + '" autocomplete="' + auto + '" required minlength="8">' +
      '<button type="button" data-show>Show</button></div>';
  }
  UI.page('auth', { title: 'Sign in', auth: 'guest' }, function (view, ctx) {
    var mode = ['signup', 'reset'].indexOf(ctx.args[0]) >= 0 ? ctx.args[0] : 'login';
    function draw(msg, isErr) {
      var heading = { login: 'Welcome back', signup: 'Create your account', reset: 'Reset your password' }[mode];
      var sub = { login: 'Sign in to continue to ' + esc(UI.config.name) + '.', signup: 'It\'s free and takes a few seconds.',
        reset: 'We\'ll email you a link to choose a new password.' }[mode];
      view.innerHTML = '<div class="au-wrap"><div class="ui-card au-card">' +
        '<h1>' + heading + '</h1><p class="muted">' + sub + '</p>' +
        (mode !== 'reset' ? '<div class="ui-seg" role="tablist"><button type="button" data-mode="login" class="' + (mode === 'login' ? 'on' : '') + '">Sign in</button>' +
          '<button type="button" data-mode="signup" class="' + (mode === 'signup' ? 'on' : '') + '">Create account</button></div>' : '<div style="height:14px"></div>') +
        '<form class="ui-stack" data-form="' + mode + '" novalidate>' +
        (mode === 'signup' ? '<label class="ui-field"><span>Your name</span><input type="text" name="name" autocomplete="name" required maxlength="60"></label>' : '') +
        '<label class="ui-field"><span>Email</span><input type="email" name="email" autocomplete="email" required></label>' +
        (mode === 'login' ? '<label class="ui-field"><span>Password</span>' + pw('password', 'current-password') + '</label>' : '') +
        (mode === 'signup' ? '<label class="ui-field"><span>Password <em>(at least 8 characters)</em></span>' + pw('password', 'new-password') + '</label>' +
          (window.LegalKit ? '<div>' + LegalKit.consentField() + '</div>' : '') : '') +
        '<div data-msg role="alert"' + (msg ? ' class="' + (isErr ? 'ui-error' : 'ui-note') + '">' + esc(msg) : ' hidden>') + '</div>' +
        '<button class="ui-btn primary block" type="submit">' + { login: 'Sign in', signup: 'Create account', reset: 'Send the link' }[mode] + '</button></form>' +
        (mode !== 'reset' ? '<div class="au-or">or</div><button type="button" class="ui-btn block au-google" data-google>' + GOOGLE_G + 'Continue with Google</button>' : '') +
        '<div class="au-links">' + (mode === 'login' ? '<a data-mode="reset">Forgot your password?</a>' : '<a data-mode="login">' + UI.icon('back') + ' Back to sign in</a>') +
        '<a href="#landing" data-go="landing">About ' + esc(UI.config.name) + '</a></div></div></div>';
      var first = view.querySelector('input');
      if (first && !msg) first.focus();
    }
    view.addEventListener('click', function (e) {
      var m = e.target.closest('[data-mode]');
      if (m) { e.preventDefault(); mode = m.getAttribute('data-mode'); history.replaceState(null, '', '#auth' + (mode === 'login' ? '' : '/' + mode)); draw(); return; }
      var g = e.target.closest('[data-google]');
      if (g) { google(g); return; }
      var s = e.target.closest('[data-show]');
      if (s) { var i = s.parentNode.querySelector('input'); i.type = i.type === 'password' ? 'text' : 'password'; s.textContent = i.type === 'password' ? 'Show' : 'Hide'; }
    });
    view.addEventListener('submit', function (e) {
      e.preventDefault();
      var form = e.target, v = UI.formData(form);
      var problem = !/^\S+@\S+\.\S+$/.test(v.email || '') ? 'Please enter a valid email address.'
        : mode !== 'reset' && (v.password || '').length < (mode === 'signup' ? 8 : 1) ? (mode === 'signup' ? 'Please choose a password of at least 8 characters.' : 'Please enter your password.')
        : mode === 'signup' && (v.name || '').trim().length < 2 ? 'Please tell us your name.' : null;
      if (problem) { say(problem, true); return; }
      if (mode === 'signup' && window.LegalKit && !LegalKit.consentChecked(form)) return;  // the kit shows its own message
      UI.busy(form.querySelector('[type=submit]'), UI.auth(mode, v)).then(function (r) {
        if (mode === 'reset' || (r && !r.me)) { mode = 'login'; draw(r && r.message, false); restore({ email: v.email }); }
        else UI.toast(mode === 'signup' ? 'Welcome to ' + UI.config.name + '!' : 'Welcome back!', 'ok');
      }, function (err) { say(err.message, true); });
    });
    // Sign-up asks for the Privacy & Terms tick here too (ticking it is remembered for the new account).
    function google(btn) {
      var form = view.querySelector('form'), v = mode === 'signup' ? UI.formData(form) : {};
      if (mode === 'signup' && window.LegalKit && !LegalKit.consentChecked(form)) return;
      UI.busy(btn, UI.auth('google', { name: (v.name || '').trim() })).then(function () {
        UI.toast(mode === 'signup' ? 'Welcome to ' + UI.config.name + '!' : 'Welcome back!', 'ok');
      }, function (err) { say(err.message, true); });
    }
    function say(msg, isErr) {
      var box = view.querySelector('[data-msg]');
      box.className = isErr ? 'ui-error' : 'ui-note'; box.textContent = msg; box.hidden = false;
    }
    function restore(v) {
      ['name', 'email'].forEach(function (k) { var i = view.querySelector('[name=' + k + ']'); if (i && v[k]) i.value = v[k]; });
    }
    draw();
  });
})();

/* ===== casebook.html ===== */
(function () {
  var esc = UI.esc;
  var KIND_ICON = { person: 'user', username: 'fingerprint', email: 'mail', phone: 'chat', address: 'home', place: 'pin', domain: 'globe',
    organisation: 'briefcase', vehicle: 'target', image: 'image', event: 'calendar', document: 'book', note: 'edit' };
  var KIND_LABEL = { organisation: 'Organisation' };
  function kindLabel(k) { return KIND_LABEL[k] || (k.charAt(0).toUpperCase() + k.slice(1)); }
  var STATUS = [['open', 'Open', ''], ['cold', 'Cold', 'muted'], ['closed', 'Closed', 'good']];
  function stamp(status) { var s = STATUS.filter(function (x) { return x[0] === status; })[0] || STATUS[0]; return '<span class="os-stamp ' + s[2] + '">' + s[1] + '</span>'; }

  function newFileModal() {
    var m = UI.modal('<h2>Open a new file</h2><p class="muted">Write the question before you collect anything. That\'s step one of the intelligence cycle.</p>' +
      '<form class="ui-stack" data-new><label class="ui-field"><span>Title</span><input type="text" name="title" maxlength="100" required placeholder="e.g. Background check: Acme Renovations"></label>' +
      '<label class="ui-field"><span>Subject <em>(who or what)</em></span><input type="text" name="subject" maxlength="160" placeholder="A person, company, website, photo..."></label>' +
      '<label class="ui-field"><span>The question <em>(one sentence you could answer with a fact)</em></span><textarea name="objective" maxlength="600" rows="3" placeholder="Is Acme Renovations a registered company, and who are its directors?"></textarea></label>' +
      '<div class="ui-row end"><button type="button" class="ui-btn ghost" data-close>Cancel</button><button class="ui-btn primary" type="submit">' + UI.icon('folder') + 'Open the file</button></div></form>');
    m.el.querySelector('[data-new]').addEventListener('submit', function (e) {
      e.preventDefault();
      var v = UI.formData(e.target);
      UI.busy(e.target.querySelector('[type=submit]'), UI.api('create_investigation', v.title, v.subject, v.objective)).then(function (r) {
        m.close(); UI.go('casebook', r.investigation.id);
      });
    });
  }

  function list(view) {
    return UI.api('list_investigations').then(function (d) {
      view.innerHTML = '<div class="ui-wrap"><div class="cb-head"><div><div class="eyebrow">Casebook</div><h1>Your investigations</h1></div>' +
        '<div class="ui-row"><button class="ui-btn" data-sample>' + UI.icon('book') + 'Add the training file</button><button class="ui-btn primary" data-new-file>' + UI.icon('plus') + 'New investigation</button></div></div>' +
        '<div class="cb-private">' + UI.icon('lock') + '<div><b>Private to you.</b> Nobody else, not even other agents, can see your casebook. Investigate only with a legitimate purpose, and never put information here that you obtained unlawfully.</div></div>' +
        (d.items.length ? '<div class="cb-list">' + d.items.map(function (i) {
          return '<article class="os-folder cb-item" data-tab="' + esc(UI.fmtDate(i.created)) + '" data-open="' + esc(i.id) + '" tabindex="0" role="link">' + stamp(i.status) +
            '<h3>' + esc(i.title) + '</h3><p>' + esc(i.subject || i.objective || 'No subject yet.') + '</p>' +
            '<div class="ui-row"><span class="ui-badge">' + UI.icon('pushpin') + UI.plural(i.leads, 'lead') + '</span><span class="ui-badge">' + UI.icon('link') + UI.plural(i.links, 'string') + '</span>' +
            '<span class="small faint">updated ' + esc(UI.ago(i.updated)) + '</span></div></article>';
        }).join('') + '</div>'
          : '<div class="ui-empty">' + UI.icon('board') + '<h3>No investigations yet</h3><p>Open a new file for your own practice case, or add the training file to see a finished corkboard first.</p>' +
            '<div class="ui-row" style="justify-content:center"><button class="ui-btn" data-sample>' + UI.icon('book') + 'Add the training file</button><button class="ui-btn primary" data-new-file>' + UI.icon('plus') + 'New investigation</button></div></div>') + '</div>';
      view.addEventListener('click', function (e) {
        var t = e.target.closest('[data-open]');
        if (t) { UI.go('casebook', t.getAttribute('data-open')); return; }
        if (e.target.closest('[data-new-file]')) { newFileModal(); return; }
        var s = e.target.closest('[data-sample]');
        if (s) UI.busy(s, UI.api('create_sample_investigation')).then(function (r) { UI.toast('Training file added.', 'ok'); UI.go('casebook', r.investigation.id); });
      });
      view.addEventListener('keydown', function (e) { var t = e.target.closest('[data-open]'); if (t && e.key === 'Enter') UI.go('casebook', t.getAttribute('data-open')); });
    });
  }

  function leadForm(kinds, lead) {
    lead = lead || {};
    var g = lead.grade || '';
    return '<form class="iv-form" data-lead-form>' +
      '<label class="ui-field"><span>Kind</span><select name="kind">' + kinds.map(function (k) { return '<option value="' + k + '"' + (lead.kind === k ? ' selected' : '') + '>' + kindLabel(k) + '</option>'; }).join('') + '</select></label>' +
      '<label class="ui-field"><span>Value</span><input type="text" name="value" maxlength="160" required value="' + esc(lead.value || '') + '" placeholder="A name, @handle, address, domain..."></label>' +
      '<label class="ui-field full"><span>Note</span><textarea name="note" maxlength="1500" rows="3" placeholder="What it is, why it matters, what to check next">' + esc(lead.note || '') + '</textarea></label>' +
      '<label class="ui-field"><span>Source <em>(where you found it)</em></span><input type="text" name="source" maxlength="400" value="' + esc(lead.source || '') + '" placeholder="URL or description"></label>' +
      '<label class="ui-field"><span>Date <em>(of the event, optional)</em></span><input type="text" name="when" maxlength="40" value="' + esc(lead.when || '') + '" placeholder="2026-10-07"></label>' +
      '<div class="ui-field full"><span>Admiralty grade</span><div class="iv-grade"><select name="rel" aria-label="Source reliability"><option value="">Source reliability: ungraded</option>' +
        Object.keys(OS.REL).map(function (k) { return '<option value="' + k + '"' + (g[0] === k ? ' selected' : '') + '>' + k + ': ' + OS.REL[k] + '</option>'; }).join('') + '</select>' +
        '<select name="cred" aria-label="Information credibility"><option value="">Information credibility: ungraded</option>' +
        Object.keys(OS.CRED).map(function (k) { return '<option value="' + k + '"' + (g[1] === k ? ' selected' : '') + '>' + k + ': ' + OS.CRED[k] + '</option>'; }).join('') + '</select></div></div>' +
      '<div class="ui-row end full">' + (lead.id ? '<button type="button" class="ui-btn ghost" data-close>Cancel</button>' : '') + '<button class="ui-btn primary" type="submit">' + UI.icon(lead.id ? 'check' : 'pushpin') + (lead.id ? 'Save lead' : 'Pin this lead') + '</button></div></form>';
  }
  function leadData(form) {
    var v = UI.formData(form);
    return { kind: v.kind, value: v.value, note: v.note, source: v.source, when: v.when, grade: v.rel && v.cred ? v.rel + v.cred : '' };
  }

  function investigation(view, id, tab) {
    var D = null, connectFrom = null, connectMode = false;
    tab = ['board', 'leads', 'checklist', 'report'].indexOf(tab) >= 0 ? tab : 'board';
    function load() { return UI.api('get_investigation', id).then(function (d) { D = d; draw(); }); }
    function draw() {
      var I = D.investigation;
      document.title = I.title + ' · ' + UI.config.name;
      var done = D.checklist.filter(function (c) { return I.checklist[c.id]; }).length;
      view.innerHTML = '<div class="ui-wrap"><div class="iv-noprint"><a class="small muted" href="#casebook" data-go="casebook">' + UI.icon('back') + ' Casebook</a>' +
        '<div class="iv-top"><div style="min-width:0"><h1>' + esc(I.title) + '</h1></div><div class="ui-row"><div class="ui-seg" role="group" aria-label="Status">' + STATUS.map(function (s) {
          return '<button type="button" data-status="' + s[0] + '" class="' + (I.status === s[0] ? 'on' : '') + '">' + s[1] + '</button>';
        }).join('') + '</div><button class="ui-btn sm" data-edit-file>' + UI.icon('edit') + 'Edit</button><button class="ui-btn sm ghost danger" data-del-file aria-label="Delete investigation">' + UI.icon('trash') + '</button></div></div>' +
        '<p class="iv-sub">' + (I.subject ? '<b>Subject:</b> ' + esc(I.subject) + (/[.?!]$/.test(I.subject) ? ' ' : '. ') : '') + (I.objective ? '<b>Question:</b> ' + esc(I.objective) : '<i>No question written yet. Edit the file and write one.</i>') + '</p>' +
        '<nav class="ui-tabs">' + [['board', 'Corkboard', 'board', D.leads.length], ['leads', 'Leads', 'pushpin', D.leads.length], ['checklist', 'Checklist', 'check', done + '/' + D.checklist.length], ['report', 'Report', 'print', '']].map(function (t) {
          return '<a href="#casebook/' + esc(id) + '/' + t[0] + '" class="' + (t[0] === tab ? 'on' : '') + '">' + UI.icon(t[2]) + t[1] + (t[3] !== '' ? ' <span class="count">' + t[3] + '</span>' : '') + '</a>';
        }).join('') + '</nav></div><div data-body></div></div>';
      ({ board: drawBoard, leads: drawLeads, checklist: drawChecklist, report: drawReport })[tab]();
    }

    // ------------------------------------------------------------- corkboard
    function pinById(lid) { return D.leads.filter(function (l) { return l.id === lid; })[0]; }
    function drawBoard() {
      var body = view.querySelector('[data-body]');
      body.innerHTML = '<div class="cb-tools iv-noprint"><button class="ui-btn sm primary" data-add-lead>' + UI.icon('plus') + 'Add a lead</button>' +
        '<button class="ui-btn sm' + (connectMode ? ' primary' : '') + '" data-connect>' + UI.icon('link') + (connectMode ? 'Done tying' : 'Tie a red string') + '</button>' +
        '<span class="cb-connect-hint" data-hint>' + (connectMode ? (connectFrom ? 'Now click the second lead.' : 'Click the first lead.') : 'Drag pins to arrange them. Click a pin to edit it, a string\'s label to cut it.') + '</span></div>' +
        '<div class="cb-board" data-board><div class="cb-canvas" style="width:' + D.board.w + 'px;height:' + D.board.h + 'px"><svg class="cb-svg" width="' + D.board.w + '" height="' + D.board.h + '" data-svg></svg>' +
        D.leads.map(function (l, i) {
          return '<div class="cb-pin kind-' + esc(l.kind) + (connectFrom === l.id ? ' sel' : '') + '" data-pin="' + esc(l.id) + '" style="left:' + l.x + 'px;top:' + l.y + 'px;--r:' + (((i * 37) % 7) - 3) * 0.6 + 'deg" tabindex="0">' +
            '<div class="k"><span style="display:inline-flex;gap:5px;align-items:center">' + UI.icon(KIND_ICON[l.kind] || 'edit') + esc(kindLabel(l.kind)) + '</span>' + (l.grade ? '<span class="g">' + esc(l.grade) + '</span>' : '') + '</div>' +
            '<div class="v">' + esc(l.value) + '</div>' + (l.note ? '<div class="n">' + esc(l.note) + '</div>' : '') + '</div>';
        }).join('') +
        (D.leads.length ? '' : '<div class="cb-board-empty"><b>An empty corkboard.</b><p class="small" style="margin:6px 0 12px">Every selector you find (a name, a username, a domain, a photo) becomes a pin. Then tie red strings between the ones that connect.</p><button class="ui-btn primary sm" data-add-lead>' + UI.icon('plus') + 'Add the first lead</button></div>') +
        '</div></div>';
      drawStrings();
      wireDrag(body.querySelector('[data-board]'));
    }
    function drawStrings() {
      var svg = view.querySelector('[data-svg]');
      if (!svg) return;
      svg.innerHTML = D.links.map(function (k) {
        var a = pinById(k.a), b = pinById(k.b);
        if (!a || !b) return '';
        var x1 = a.x + 90, y1 = a.y + 2, x2 = b.x + 90, y2 = b.y + 2, mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
        var lbl = k.label || 'link', w = Math.max(36, lbl.length * 7 + 14);
        return '<line x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 + '"/>' +
          '<g class="lbl" data-link="' + esc(k.id) + '" transform="translate(' + mx + ' ' + my + ')"><title>Click to cut this string</title><rect x="' + (-w / 2) + '" y="-10" width="' + w + '" height="20" rx="2"/><text text-anchor="middle" y="4">' + esc(lbl) + '</text></g>';
      }).join('');
    }
    function wireDrag(board) {
      var drag = null;
      board.addEventListener('pointerdown', function (e) {
        var pin = e.target.closest('.cb-pin');
        if (!pin || e.button > 0) return;
        var l = pinById(pin.getAttribute('data-pin'));
        drag = { pin: pin, lead: l, sx: e.clientX, sy: e.clientY, ox: l.x, oy: l.y, moved: false, id: e.pointerId };
        pin.setPointerCapture(e.pointerId);
      });
      board.addEventListener('pointermove', function (e) {
        if (!drag || e.pointerId !== drag.id) return;
        var dx = e.clientX - drag.sx, dy = e.clientY - drag.sy;
        if (!drag.moved && Math.abs(dx) + Math.abs(dy) < 5) return;
        drag.moved = true;
        drag.pin.classList.add('dragging');
        drag.lead.x = Math.max(0, Math.min(D.board.w - 180, Math.round(drag.ox + dx)));
        drag.lead.y = Math.max(0, Math.min(D.board.h - 90, Math.round(drag.oy + dy)));
        drag.pin.style.left = drag.lead.x + 'px'; drag.pin.style.top = drag.lead.y + 'px';
        drawStrings();
      });
      function end(e) {
        if (!drag || e.pointerId !== drag.id) return;
        var d = drag; drag = null;
        d.pin.classList.remove('dragging');
        if (d.moved) UI.apiQuiet('move_lead', d.lead.id, d.lead.x, d.lead.y);
        else pinClicked(d.lead);
      }
      board.addEventListener('pointerup', end);
      board.addEventListener('pointercancel', function (e) { if (drag && e.pointerId === drag.id) { drag.pin.classList.remove('dragging'); drag = null; } });
      board.addEventListener('keydown', function (e) { var p = e.target.closest('.cb-pin'); if (p && e.key === 'Enter') pinClicked(pinById(p.getAttribute('data-pin'))); });
    }
    function pinClicked(lead) {
      if (!connectMode) { editLead(lead); return; }
      if (!connectFrom) { connectFrom = lead.id; drawBoard(); return; }
      if (connectFrom === lead.id) { connectFrom = null; drawBoard(); return; }
      var a = connectFrom;
      var m = UI.modal('<h2>Tie a red string</h2><p class="muted">From <b>' + esc(pinById(a).value) + '</b> to <b>' + esc(lead.value) + '</b>. How are they connected?</p>' +
        '<form class="ui-stack" data-link-form><label class="ui-field"><span>Label <em>(short)</em></span><input type="text" name="label" maxlength="40" placeholder="director, same photo, registered..."></label>' +
        '<div class="ui-row end"><button type="button" class="ui-btn ghost" data-close>Cancel</button><button class="ui-btn primary" type="submit">' + UI.icon('link') + 'Tie it</button></div></form>');
      m.el.querySelector('form').addEventListener('submit', function (e) {
        e.preventDefault();
        UI.busy(e.target.querySelector('[type=submit]'), UI.api('add_link', id, a, lead.id, UI.formData(e.target).label)).then(function (r) {
          m.close(); D.links.push(r.link); connectFrom = null; drawBoard(); OS.celebrate(r);
        });
      });
    }

    // ------------------------------------------------------------- leads
    function editLead(lead) {
      var m = UI.modal('<h2>Edit lead</h2>' + leadForm(D.kinds, lead) + '<div class="ui-row" style="margin-top:14px"><button class="ui-btn sm danger" data-del-lead>' + UI.icon('trash') + 'Remove from the board</button></div>', { wide: true });
      m.el.querySelector('form').addEventListener('submit', function (e) {
        e.preventDefault();
        UI.busy(e.target.querySelector('[type=submit]'), UI.api('update_lead', lead.id, leadData(e.target))).then(function (r) {
          D.leads = D.leads.map(function (l) { return l.id === lead.id ? r.lead : l; }); m.close(); draw();
        });
      });
      m.el.querySelector('[data-del-lead]').addEventListener('click', function () {
        UI.confirm({ title: 'Remove this lead?', text: 'Its red strings are cut too.', ok: 'Remove', danger: true }).then(function (yes) {
          if (yes) UI.api('delete_lead', lead.id).then(function () { m.close(); return load(); });
        });
      });
    }
    function addLeadModal() {
      var m = UI.modal('<h2>Pin a new lead</h2>' + leadForm(D.kinds, null), { wide: true });
      m.el.querySelector('form').addEventListener('submit', function (e) {
        e.preventDefault();
        UI.busy(e.target.querySelector('[type=submit]'), UI.api('add_lead', id, leadData(e.target))).then(function (r) {
          m.close(); D.leads.push(r.lead); draw(); OS.celebrate(r); UI.toast('Pinned.', 'ok');
        });
      });
    }
    function drawLeads() {
      var body = view.querySelector('[data-body]');
      body.innerHTML = '<div class="ui-card" style="margin-bottom:18px"><h3>' + UI.icon('pushpin') + ' Pin a new lead</h3>' + leadForm(D.kinds, null) + '</div>' +
        (D.leads.length ? '<div class="iv-leads">' + D.leads.map(function (l) {
          return '<div class="iv-lead"><span class="ic">' + UI.icon(KIND_ICON[l.kind] || 'edit') + '</span><div style="min-width:0"><h4>' + esc(l.value) + ' ' + (l.grade ? '<span class="ui-badge brand">' + esc(l.grade) + '</span>' : '<span class="ui-badge">ungraded</span>') + '</h4>' +
            (l.note ? '<p>' + esc(l.note) + '</p>' : '') + '<div class="meta">' + esc(kindLabel(l.kind)) + (l.when ? ' · ' + esc(l.when) : '') + (l.source ? ' · source: ' + esc(l.source) : '') + '</div></div>' +
            '<button class="ui-btn ghost icon" data-edit-lead="' + esc(l.id) + '" aria-label="Edit">' + UI.icon('edit') + '</button></div>';
        }).join('') + '</div>' : '<div class="ui-empty">' + UI.icon('pushpin') + '<h3>No leads yet</h3><p>Add what you know first: your selectors.</p></div>') +
        (D.links.length ? '<h3 style="margin-top:24px">Red strings</h3><div class="iv-leads">' + D.links.map(function (k) {
          var a = pinById(k.a), b = pinById(k.b);
          return '<div class="iv-lead" style="grid-template-columns:38px 1fr auto"><span class="ic">' + UI.icon('link') + '</span><div style="min-width:0"><b>' + esc(a ? a.value : '?') + '</b> <span class="muted">— ' + esc(k.label || 'linked') + ' —</span> <b>' + esc(b ? b.value : '?') + '</b></div>' +
            '<button class="ui-btn ghost icon" data-link="' + esc(k.id) + '" aria-label="Cut this string">' + UI.icon('x') + '</button></div>';
        }).join('') + '</div>' : '');
      body.querySelector('[data-lead-form]').addEventListener('submit', function (e) {
        e.preventDefault();
        var f = e.target;
        UI.busy(f.querySelector('[type=submit]'), UI.api('add_lead', id, leadData(f))).then(function (r) { D.leads.push(r.lead); draw(); OS.celebrate(r); UI.toast('Pinned.', 'ok'); });
      });
    }

    // ------------------------------------------------------------- checklist + report
    function drawChecklist() {
      var I = D.investigation, PH = ['Plan', 'Plan', 'Plan', 'Collect', 'Collect', 'Process', 'Analyse', 'Analyse', 'Analyse', 'Report'];
      view.querySelector('[data-body]').innerHTML = '<p class="muted" style="max-width:46em">Walk the intelligence cycle. A professional ticks every box before a report leaves the office.</p>' +
        '<div class="iv-check">' + D.checklist.map(function (c, i) {
          return '<label><input type="checkbox" data-check="' + c.id + '"' + (I.checklist[c.id] ? ' checked' : '') + '><span><span class="ph">' + PH[i] + '</span>' + esc(c.text) + '</span></label>';
        }).join('') + '</div>';
    }
    function drawReport() {
      var I = D.investigation, graded = D.leads.filter(function (l) { return l.grade; }).length;
      var byKind = {};
      D.leads.forEach(function (l) { (byKind[l.kind] = byKind[l.kind] || []).push(l); });
      var timeline = D.leads.filter(function (l) { return l.when; }).sort(function (a, b) { return a.when < b.when ? -1 : 1; });
      var done = D.checklist.filter(function (c) { return I.checklist[c.id]; });
      view.querySelector('[data-body]').innerHTML = '<div class="ui-row end iv-noprint" style="margin-bottom:12px"><button class="ui-btn primary" data-print>' + UI.icon('print') + 'Print or save as PDF</button></div>' +
        '<article class="iv-report"><div class="hd"><span>Confidential · investigation report</span><span>' + esc(new Date().toLocaleDateString(undefined, { day: 'numeric', month: 'long', year: 'numeric' })) + '</span></div>' +
        '<h1>' + esc(I.title) + '</h1>' + stamp(I.status) +
        '<h2>1. Bottom line up front</h2><div class="bluf">' + (I.objective ? esc(I.objective) : 'Write the question in this file, then your answer here before sending.') + '</div>' +
        '<h2>2. Scope</h2><table><tr><th>Subject</th><td>' + esc(I.subject || '—') + '</td></tr><tr><th>Opened</th><td>' + esc(UI.fmtDate(I.created)) + '</td></tr><tr><th>Leads</th><td>' + D.leads.length + ' (' + graded + ' graded)</td></tr><tr><th>Connections</th><td>' + D.links.length + '</td></tr></table>' +
        '<h2>3. Findings</h2>' + (D.leads.length ? Object.keys(byKind).map(function (k) {
          return '<h3 style="font-size:1rem;margin:14px 0 6px">' + esc(kindLabel(k)) + '</h3><table><tr><th style="width:28%">Finding</th><th>Notes</th><th style="width:12%">Grade</th><th style="width:22%">Source</th></tr>' +
            byKind[k].map(function (l) { return '<tr><td><b>' + esc(l.value) + '</b>' + (l.when ? '<br><span style="color:#777">' + esc(l.when) + '</span>' : '') + '</td><td>' + esc(l.note) + '</td><td>' + esc(l.grade || '—') + '</td><td>' + esc(l.source || '—') + '</td></tr>'; }).join('') + '</table>';
        }).join('') : '<p>No findings recorded.</p>') +
        (D.links.length ? '<h2>4. Connections</h2><table>' + D.links.map(function (k) { var a = pinById(k.a), b = pinById(k.b); return '<tr><td>' + esc(a ? a.value : '?') + '</td><td>' + esc(k.label || 'linked to') + '</td><td>' + esc(b ? b.value : '?') + '</td></tr>'; }).join('') + '</table>' : '') +
        (timeline.length ? '<h2>' + (D.links.length ? 5 : 4) + '. Timeline</h2><table>' + timeline.map(function (l) { return '<tr><td style="width:24%">' + esc(l.when) + '</td><td>' + esc(l.value) + '</td></tr>'; }).join('') + '</table>' : '') +
        '<h2>Method and quality checks</h2><p>' + done.length + ' of ' + D.checklist.length + ' checks completed' + (done.length ? ': ' + done.map(function (c) { return esc(c.text.toLowerCase()); }).join('; ') + '.' : '.') + '</p>' +
        '<p style="font-size:.8rem;color:#777;margin-top:24px">Grades use the Admiralty code: source reliability A (completely reliable) to F (cannot be judged); information credibility 1 (confirmed) to 6 (cannot be judged). Facts are recorded as found; assessments are the investigator\'s judgement.</p></article>';
    }

    view.addEventListener('click', function (e) {
      var t;
      if (e.target.closest('[data-add-lead]')) { addLeadModal(); return; }
      if (e.target.closest('[data-connect]')) {
        connectMode = !connectMode; connectFrom = null;
        if (connectMode && D.leads.length < 2) { connectMode = false; UI.toast('Pin at least two leads first.', 'error'); }
        drawBoard(); return;
      }
      if ((t = e.target.closest('[data-link]'))) {
        var lid = t.getAttribute('data-link');
        UI.confirm({ title: 'Cut this string?', ok: 'Cut it', danger: true }).then(function (yes) {
          if (yes) UI.api('delete_link', lid).then(function () { D.links = D.links.filter(function (k) { return k.id !== lid; }); draw(); });
        });
        return;
      }
      if ((t = e.target.closest('[data-edit-lead]'))) { editLead(pinById(t.getAttribute('data-edit-lead'))); return; }
      if ((t = e.target.closest('[data-status]'))) {
        var s = t.getAttribute('data-status');
        UI.api('update_investigation', id, { status: s }).then(function (r) { D.investigation.status = r.investigation.status; draw(); UI.toast('Marked ' + s + '.'); });
        return;
      }
      if (e.target.closest('[data-print]')) { window.print(); return; }
      if (e.target.closest('[data-del-file]')) {
        UI.confirm({ title: 'Delete this investigation?', text: 'Every lead and string goes with it. This can\'t be undone.', ok: 'Delete', danger: true }).then(function (yes) {
          if (yes) UI.api('delete_investigation', id).then(function () { UI.toast('Deleted.'); UI.go('casebook'); });
        });
        return;
      }
      if (e.target.closest('[data-edit-file]')) {
        var I = D.investigation;
        var m = UI.modal('<h2>Edit the file</h2><form class="ui-stack" data-edit><label class="ui-field"><span>Title</span><input type="text" name="title" maxlength="100" required value="' + esc(I.title) + '"></label>' +
          '<label class="ui-field"><span>Subject</span><input type="text" name="subject" maxlength="160" value="' + esc(I.subject) + '"></label>' +
          '<label class="ui-field"><span>The question</span><textarea name="objective" maxlength="600" rows="3">' + esc(I.objective) + '</textarea></label>' +
          '<div class="ui-row end"><button type="button" class="ui-btn ghost" data-close>Cancel</button><button class="ui-btn primary" type="submit">Save</button></div></form>');
        m.el.querySelector('form').addEventListener('submit', function (ev) {
          ev.preventDefault();
          UI.busy(ev.target.querySelector('[type=submit]'), UI.api('update_investigation', id, UI.formData(ev.target))).then(function (r) { D.investigation = r.investigation; m.close(); draw(); });
        });
      }
    });
    view.addEventListener('change', function (e) {
      var c = e.target.closest('[data-check]');
      if (!c) return;
      UI.api('set_checklist', id, c.getAttribute('data-check'), c.checked).then(function (r) { D.investigation.checklist = r.checklist; });
    });
    return load();
  }

  UI.page('casebook', { title: 'Casebook', nav: 'Casebook', icon: 'board', auth: 'user', order: 40 }, function (view, ctx) {
    view.innerHTML = '<div class="ui-wrap"><div class="ui-skel" style="height:300px"></div></div>';
    return ctx.args[0] ? investigation(view, ctx.args[0], ctx.args[1]) : list(view);
  });
})();

/* ===== cases.html ===== */
(function () {
  var esc = UI.esc;
  var SRC_ICON = { web: 'search', social: 'users', records: 'book', whois: 'globe', archive: 'clock', image: 'camera' };

  function statusStamp(c) {
    if (c.solved) return '<span class="os-stamp good">Closed · ' + c.best + '</span>';
    if (c.status === 'open' || c.status === 'replay') return '<span class="os-stamp warn">Open</span>';
    return '';
  }

  function list(view) {
    return UI.api('list_cases').then(function (d) {
      var solved = d.cases.filter(function (c) { return c.solved; }).length;
      view.innerHTML = '<div class="ui-wrap"><div class="cs-intro"><div><div class="eyebrow">Case files</div><h1>The filing cabinet</h1>' +
        '<p class="muted" style="margin:6px 0 0;max-width:42em">Six fictional investigations. Search the web, social networks, records, WHOIS, archives and the image lab; pivot from one clue to the next; crack the questions. Hints and wrong guesses cost points.</p></div>' +
        '<span class="ui-badge good">' + UI.icon('folder') + solved + ' of ' + d.cases.length + ' closed</span></div>' +
        '<div class="cs-grid">' + d.cases.map(function (c) {
          return '<article class="os-folder cs-card" data-tab="File #' + c.num + ' · ' + esc(c.level) + '">' + statusStamp(c) +
            '<div class="code">OPERATION ' + esc(c.codename) + '</div><h2>' + esc(c.title) + '</h2>' +
            '<div class="client">Client: <b>' + esc(c.client) + '</b></div><p>' + esc(c.teaser) + '</p>' +
            '<div class="foot"><a class="ui-btn primary sm" href="#cases/' + esc(c.id) + '" data-go="cases/' + esc(c.id) + '">' + UI.icon('terminal') + (c.solved ? 'Review' : c.status === 'new' ? 'Open the file' : 'Resume') + '</a>' +
              '<span class="ui-badge brand">' + c.xp + ' XP</span><span class="ui-badge">' + c.minutes + ' min</span>' +
              '<span class="cs-srcs" title="Sources">' + c.sources.map(function (s) { return UI.icon(SRC_ICON[s]); }).join('') + '</span></div>' +
            '<p class="small faint" style="margin:10px 0 0">' + (c.solvers ? 'Closed by ' + UI.plural(c.solvers, 'agent') : 'Nobody has closed this one yet') + '</p></article>';
        }).join('') + '</div>' +
        '<p class="small muted" style="margin-top:28px">All people, companies, websites and records in the case files are invented. Domains end in <code>.example</code>, a name reserved for examples, so nothing here points at a real site.</p></div>';
    });
  }

  function docHtml(doc, sources, isNew) {
    var s = sources[doc.src] || { label: doc.src };
    return '<article class="cd-doc' + (doc.pinned ? ' pinned' : '') + '" data-doc="' + esc(doc.id) + '">' +
      '<div class="src">' + UI.icon(SRC_ICON[doc.src]) + esc(s.label) + (doc.date ? ' · ' + esc(doc.date) : '') + (isNew ? ' · <span class="new">new</span>' : '') + (doc.pinned ? ' · <span class="cd-pinmark">pinned</span>' : '') + '</div>' +
      '<h4>' + esc(doc.title) + '</h4>' + (doc.url ? '<div class="url">' + esc(doc.url) + '</div>' : '') +
      (doc.meta && doc.meta.length ? '<table class="meta">' + doc.meta.map(function (m) { return '<tr><th>' + esc(m[0]) + '</th><td>' + OS.md(m[1]) + '</td></tr>'; }).join('') + '</table>' : '') +
      '<div class="body">' + OS.md(doc.body) + '</div>' +
      '<div class="acts"><button class="ui-btn sm" data-pin="' + esc(doc.id) + '">' + UI.icon('pushpin') + (doc.pinned ? 'Unpin' : 'Pin as evidence') + '</button></div></article>';
  }

  function desk(view, id) {
    var st = null, info = null, sources = null, src = null, lastResults = [], lastNew = [], lastLog = '';

    function drawAll() {
      view.innerHTML = '<div class="ui-wrap"><div class="cd-top"><div><a class="small muted" href="#cases" data-go="cases">' + UI.icon('back') + ' All case files</a>' +
        '<div class="eyebrow" style="margin:12px 0 0">File #' + info.num + ' · Operation ' + esc(info.codename) + ' · ' + esc(info.level) + '</div><h1>' + esc(info.title) + '</h1></div>' +
        '<div class="cd-score" data-score></div></div>' +
        '<div class="cd"><div class="cd-col">' +
          '<section class="ui-card cd-brief"><div class="os-label" style="margin-bottom:8px">Briefing</div><div class="who">Client: ' + esc(info.client) + '</div>' + OS.paras(info.brief) +
            '<div class="os-label" style="margin-top:14px">Exhibits <span class="faint" style="text-transform:none;letter-spacing:0">(click to search)</span></div><dl class="cd-ex">' +
            info.exhibits.map(function (e) { return '<div><dt>' + esc(e[0]) + '</dt><dd data-copy="' + esc(e[1]) + '">' + esc(e[1]) + '</dd></div>'; }).join('') + '</dl></section>' +
          '<section class="ui-card cd-qs" data-qs></section>' +
        '</div><div class="cd-col">' +
          '<div class="cd-term-wrap" style="display:grid;gap:14px"><section class="cd-term"><div class="bar"><i></i><i></i><i></i>OSINTY FIELD TERMINAL</div>' +
            '<div class="cd-srcs" role="tablist">' + info.sources.map(function (s) {
              return '<button type="button" data-src="' + s + '" class="' + (s === src ? 'on' : '') + '">' + UI.icon(SRC_ICON[s]) + esc(sources[s].label) + '</button>';
            }).join('') + '</div>' +
            '<form class="cd-search" data-search><span class="pr">&gt;</span><input type="search" name="q" autocomplete="off" spellcheck="false" maxlength="120" aria-label="Search query" placeholder="' + esc(sources[src].hint) + '">' +
            '<button class="ui-btn" type="submit">' + UI.icon('search') + 'Run</button></form><div class="cd-log" data-log></div></section>' +
          '<div class="cd-results" data-results></div></div>' +
          '<section class="ui-card cd-notes" data-notes></section>' +
        '</div></div></div>';
      drawScore(); drawQs(); drawResults(); drawNotes(); log(lastLog || 'Ready. Pick a source, type a query, press Run.');
    }
    function drawScore() {
      var box = view.querySelector('[data-score]');
      if (!box) return;
      var solved = st.status === 'solved';
      box.innerHTML = (solved ? '<span class="os-stamp good">Case closed</span>' : '') +
        '<div><span class="os-label">' + (solved ? 'Best score' : 'Score if you crack it now') + '</span><span class="num">' + (solved ? st.best : st.score) + '</span><span class="muted small"> / 100</span></div>' +
        (st.status !== 'new' ? '<button class="ui-btn sm ghost" data-reset title="Start this case again">' + UI.icon('refresh') + 'Restart</button>' : '');
    }
    function drawQs() {
      var box = view.querySelector('[data-qs]');
      var n = st.questions.filter(function (q) { return q.answer; }).length;
      box.innerHTML = '<div class="ui-row between"><h3>Case questions</h3><span class="ui-badge ' + (n === st.questions.length ? 'good' : '') + '">' + n + '/' + st.questions.length + '</span></div>' +
        '<p class="small muted" style="margin:0 0 6px">Short answers. Each hint costs 8 points, each wrong answer 4.</p>' +
        st.questions.map(function (q, i) {
          return '<div class="cd-q" data-qid="' + esc(q.id) + '"><div class="qt"><span class="n">Q' + (i + 1) + '</span><span>' + esc(q.text) + '</span></div>' +
            (q.answer ? '<div class="solved">' + UI.icon('check') + esc(q.answer) + '</div>'
              : '<form data-answer><input type="text" name="a" maxlength="80" autocomplete="off" spellcheck="false" placeholder="Your answer" aria-label="Answer to question ' + (i + 1) + '"><button class="ui-btn primary sm" type="submit">Submit</button></form>' +
                '<div class="row2"><span></span>' + (q.hints_left ? '<button class="ui-btn ghost sm" type="button" data-hint>' + UI.icon('bulb') + 'Hint (' + q.hints_left + ' left)</button>' : '<span class="small faint">No hints left</span>') + '</div>') +
            q.hints.map(function (h, hi) { return '<div class="hint"><b>HINT ' + (hi + 1) + '</b>' + esc(h) + '</div>'; }).join('') + '</div>';
        }).join('') +
        (st.debrief ? '<button class="ui-btn sm" style="margin-top:14px" data-debrief>' + UI.icon('award') + 'Read the debrief</button>' : '');
    }
    function drawResults() {
      var box = view.querySelector('[data-results]');
      if (!lastResults.length) { box.innerHTML = ''; return; }
      box.innerHTML = lastResults.map(function (doc) { return docHtml(doc, sources, lastNew.indexOf(doc.id) >= 0); }).join('');
    }
    function drawNotes() {
      var box = view.querySelector('[data-notes]');
      var open = box.querySelector('details.cd-notes-d') ? box.querySelector('details.cd-notes-d').open : true;
      var pinned = st.found.filter(function (d) { return d.pinned; });
      box.innerHTML = '<details class="cd-notes-d"' + (open ? ' open' : '') + '><summary><h3>' + UI.icon('book') + ' Notebook</h3><span class="ui-badge">' + UI.plural(st.found.length, 'document') + ' · ' + pinned.length + ' pinned</span></summary>' +
        (st.found.length ? '<div class="cd-nlist">' + st.found.slice().sort(function (a, b) { return (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0); }).map(function (doc) {
          return '<details><summary>' + UI.icon(doc.pinned ? 'pushpin' : SRC_ICON[doc.src]) + '<span>' + esc(doc.title) + '</span></summary>' + docHtml(doc, sources) + '</details>';
        }).join('') + '</div>' : '<div class="cd-empty" style="margin-top:12px">Everything you find lands here, so you never lose a lead.</div>') + '</details>';
    }
    function log(html) { lastLog = html; var el = view.querySelector('[data-log]'); if (el) el.innerHTML = html; }
    function setFound(results) {
      var known = {};
      st.found.forEach(function (d) { known[d.id] = true; });
      results.forEach(function (d) { if (!known[d.id]) st.found.push(d); });
    }
    function search(q) {
      var form = view.querySelector('[data-search]');
      return UI.busy(form.querySelector('[type=submit]'), UI.api('case_search', info.id, src, q)).then(function (r) {
        lastResults = r.results; lastNew = r.new;
        setFound(r.results);
        if (st.status === 'new') { st.status = 'open'; drawScore(); }
        log('&gt; <b>' + esc(sources[src].label) + '</b>: "' + esc(r.query) + '": ' + (r.results.length ? UI.plural(r.results.length, 'result') + (r.new.length ? ', ' + r.new.length + ' new' : '') : 'no results. Try other keywords, a different source, or something you found earlier.'));
        drawResults(); drawNotes();
        if (r.results.length && innerWidth < 900) view.querySelector('[data-results]').scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, function (err) { log('&gt; <b>error</b>: ' + esc(err.message)); });
    }
    function useQuery(text) {
      var inp = view.querySelector('[data-search] input');
      inp.value = text;
      inp.focus();
      view.querySelector('.cd-term').scrollIntoView({ behavior: 'smooth', block: 'center' });
      UI.toast('Copied into the search box. Pick a source and Run.');
    }
    function debrief(res) {
      UI.modal('<div class="cd-closed"><div class="os-stamp good">Case closed</div><h2>' + esc(info.title) + '</h2>' +
        (res ? '<p><b>Score ' + res.score + '/100</b>' + (res.xp_gained ? ' · +' + res.xp_gained + ' XP' : ' · replay, no new XP') + '</p>' : '') +
        '<div class="os-label" style="text-align:left;margin:16px 0 8px">Debrief from HQ</div>' + OS.paras(st.debrief) +
        '<div class="ui-row end" style="margin-top:18px"><button class="ui-btn" data-close>Stay here</button><a class="ui-btn primary" href="#cases" data-go="cases" data-close>Next case</a></div></div>', { wide: true });
    }

    view.addEventListener('click', function (e) {
      var t;
      if ((t = e.target.closest('[data-src]'))) {
        src = t.getAttribute('data-src');
        view.querySelectorAll('[data-src]').forEach(function (b) { b.classList.toggle('on', b === t); });
        view.querySelector('[data-search] input').placeholder = sources[src].hint;
        view.querySelector('[data-search] input').focus();
        return;
      }
      if ((t = e.target.closest('[data-copy]'))) { useQuery(t.getAttribute('data-copy')); return; }
      if ((t = e.target.closest('.cd-doc .body code'))) { useQuery(t.textContent); return; }
      if ((t = e.target.closest('[data-pin]'))) {
        var docId = t.getAttribute('data-pin'), doc = st.found.filter(function (d) { return d.id === docId; })[0];
        var flag = !(doc && doc.pinned);
        UI.busy(t, UI.api('case_pin', info.id, docId, flag)).then(function (r) {
          st.found.forEach(function (d) { d.pinned = r.pinned.indexOf(d.id) >= 0; });
          lastResults.forEach(function (d) { d.pinned = r.pinned.indexOf(d.id) >= 0; });
          drawResults(); drawNotes();
          UI.toast(flag ? 'Pinned to the evidence board.' : 'Unpinned.');
        });
        return;
      }
      if ((t = e.target.closest('[data-hint]'))) {
        var qid = t.closest('[data-qid]').getAttribute('data-qid');
        UI.confirm({ title: 'Take a hint?', text: 'It costs 8 points off this case\'s score.', ok: 'Show the hint' }).then(function (yes) {
          if (!yes) return;
          UI.api('case_hint', info.id, qid).then(function (r) {
            st.questions.forEach(function (q) { if (q.id === qid) { q.hints = r.hints; q.hints_left = r.hints_left; } });
            st.score = r.score; if (st.status === 'new') st.status = 'open';
            drawQs(); drawScore();
          });
        });
        return;
      }
      if (e.target.closest('[data-debrief]')) { debrief(null); return; }
      if (e.target.closest('[data-reset]')) {
        UI.confirm({ title: 'Restart this case?', text: st.solved_once ? 'Your XP and best score stay. Your notebook and answers are cleared so you can try for a better score.' : 'Your notebook, answers and hints are cleared.', ok: 'Restart', danger: true })
          .then(function (yes) { if (yes) UI.api('case_reset', info.id).then(function (r) { st = r.state; lastResults = []; lastLog = ''; drawAll(); }); });
      }
    });
    view.addEventListener('submit', function (e) {
      if (e.target.matches('[data-search]')) {
        e.preventDefault();
        var q = e.target.querySelector('input').value.trim();
        if (q) search(q);
        return;
      }
      if (e.target.matches('[data-answer]')) {
        e.preventDefault();
        var form = e.target, qid = form.closest('[data-qid]').getAttribute('data-qid'), val = form.querySelector('input').value.trim();
        if (!val) return;
        UI.busy(form.querySelector('[type=submit]'), UI.api('case_answer', info.id, qid, val)).then(function (r) {
          var keepFound = st.found;
          st = r.state; st.found = keepFound.length >= r.state.found.length ? keepFound : r.state.found;
          if (!r.correct) {
            form.classList.add('shake'); setTimeout(function () { form.classList.remove('shake'); }, 450);
            UI.toast('That doesn\'t match the evidence. -4 points.', 'error');
            st.score = r.score; drawScore();
            return;
          }
          drawQs(); drawScore();
          if (r.solved) { OS.celebrate(r); setTimeout(function () { debrief(r); }, r.rank_up ? 2600 : 700); }
          else UI.toast('Correct. Keep digging.', 'ok');
        });
      }
    });
    return UI.api('get_case', id).then(function (d) {
      info = d.case; sources = d.sources; st = d.state; src = info.sources[0];
      document.title = info.title + ' · ' + UI.config.name;
      drawAll();
    });
  }

  UI.page('cases', { title: 'Case files', nav: 'Cases', icon: 'folder', auth: 'user', order: 30 }, function (view, ctx) {
    view.innerHTML = '<div class="ui-wrap"><div class="ui-skel" style="height:300px"></div></div>';
    return ctx.args[0] ? desk(view, ctx.args[0]) : list(view);
  });
})();

/* ===== home.html ===== */
(function () {
  var esc = UI.esc;
  function greeting() {
    var h = new Date().getHours();
    return h < 5 ? 'Working late' : h < 12 ? 'Morning' : h < 18 ? 'Afternoon' : 'Evening';
  }
  UI.page('home', { title: 'The Office', nav: 'Office', icon: 'hat', auth: 'user', order: 10 }, function (view, ctx) {
    view.innerHTML = '<div class="ui-wrap"><div class="ui-skel" style="height:240px"></div></div>';
    function draw(d) {
      var me = d.me, first = (ctx.me.name || 'Agent').split(' ')[0];
      var dateStr = new Date().toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
      var nl = d.next_lesson, nc = d.next_case, ac = d.active_cases[0];
      var earned = d.badges.filter(function (b) { return b.earned; }).length;
      view.innerHTML = '<div class="ui-wrap">' +
        '<div class="of-top">' +
          '<section class="of-hello"><div class="date">' + esc(dateStr) + '</div><h1>' + greeting() + ', Agent <em>' + esc(first) + '</em>.</h1>' +
            '<div class="of-rank">' + OS.shield(me.level) + '<div class="grow"><div class="nm">' + esc(me.rank) + '</div>' +
              '<div class="sub">' + me.xp + ' XP' + (me.next ? ' · ' + me.to_next + ' to ' + esc(me.next) : ' · top rank') + '</div>' +
              '<div class="os-bar" role="progressbar" aria-valuenow="' + me.pct + '" aria-valuemin="0" aria-valuemax="100"><i style="width:' + me.pct + '%"></i></div></div></div>' +
            '<div class="of-chips"><span class="of-chip' + (d.streak >= 3 ? ' hot' : '') + '">' + UI.icon('flame') + UI.plural(d.streak, 'day') + ' on duty</span>' +
              '<span class="of-chip">' + UI.icon('book') + d.lessons_done + '/' + d.lessons_total + ' lessons</span>' +
              '<span class="of-chip">' + UI.icon('folder') + d.cases_solved + '/' + d.cases_total + ' cases closed</span>' +
              (d.board.my_place ? '<span class="of-chip">' + UI.icon('crown') + '#' + d.board.my_place + ' in the Bureau</span>' : '') + '</div>' +
          '</section>' +
          '<section class="of-memo" data-memo><div class="os-label">Confidential · daily briefing</div><h2>' + esc(d.tip.title) + '</h2><p>' + esc(d.tip.body) + '</p>' +
            (d.briefing_done ? '<span class="os-stamp">Signed</span><p class="small" style="margin:0;color:#6a5d4c">Back tomorrow for a fresh one.</p>'
              : '<button class="ui-btn primary" data-sign>' + UI.icon('edit') + 'Sign the briefing · +5 XP</button>') + '</section>' +
        '</div>' +
        '<div class="of-row">' +
          '<article class="ui-card of-card"><div class="os-label">' + UI.icon('book') + 'Continue training</div>' +
            (nl ? '<h3>' + esc(nl.num + ' ' + nl.title) + '</h3><p>' + esc(nl.summary) + '</p><div class="foot"><a class="ui-btn primary sm" href="#academy/' + esc(nl.id) + '" data-go="academy/' + esc(nl.id) + '">' + UI.icon('play') + 'Start · ' + nl.minutes + ' min</a><span class="small muted">Module ' + nl.module_num + '</span></div>'
              : '<h3>Academy complete</h3><p>Every lesson passed. Retake any quiz for a perfect score.</p><div class="foot"><a class="ui-btn sm" href="#academy" data-go="academy">Open the Academy</a></div>') + '</article>' +
          '<article class="ui-card of-card"><div class="os-label">' + UI.icon('folder') + 'Case files</div>' +
            (ac ? '<h3>' + esc(ac.title) + '</h3><p>Operation ' + esc(ac.codename) + ' is open on your desk: ' + ac.answered + '/' + ac.total + ' questions cracked, ' + UI.plural(ac.found, 'document') + ' found.</p><div class="foot"><a class="ui-btn primary sm" href="#cases/' + esc(ac.id) + '" data-go="cases/' + esc(ac.id) + '">' + UI.icon('terminal') + 'Resume</a></div>'
              : nc ? '<h3>' + esc(nc.title) + '</h3><p>' + esc(nc.teaser) + '</p><div class="foot"><a class="ui-btn primary sm" href="#cases/' + esc(nc.id) + '" data-go="cases/' + esc(nc.id) + '">' + UI.icon('terminal') + 'Open the file</a><span class="ui-badge">' + esc(nc.level) + ' · ' + nc.xp + ' XP</span></div>'
              : '<h3>All cases closed</h3><p>Replay any file to beat your best score.</p><div class="foot"><a class="ui-btn sm" href="#cases" data-go="cases">All case files</a></div>') + '</article>' +
          '<article class="ui-card of-card"><div class="os-label">' + UI.icon('board') + 'Your casebook</div>' +
            '<div class="of-big">' + d.investigations.open + '</div><p>' + (d.investigations.total ? UI.plural(d.investigations.open, 'open investigation') + ' out of ' + d.investigations.total + '. Pin leads, tie red strings, print the report.' : 'Your own investigations live here: leads, a corkboard, a checklist and a printable report.') + '</p>' +
            '<div class="foot"><a class="ui-btn sm" href="#casebook" data-go="casebook">' + UI.icon('board') + 'Open the casebook</a></div></article>' +
        '</div>' +
        '<div class="of-sec"><h2>Commendations</h2><span class="small muted">' + earned + ' of ' + d.badges.length + ' earned</span></div>' +
        '<div class="of-badges">' + d.badges.map(function (b) {
          return '<div class="of-badge' + (b.earned ? '' : ' off') + '" title="' + esc(b.how) + '"><span class="os-badge-ic' + (b.earned ? ' on' : '') + '">' + UI.icon(b.icon) + '</span><div style="min-width:0"><b>' + esc(b.name) + '</b><span>' + esc(b.how) + '</span></div></div>';
        }).join('') + '</div>' +
        '<div class="of-two">' +
          '<section class="ui-card"><div class="of-sec"><h2>The Bureau</h2><span class="small muted">' + UI.plural(d.board.total, 'agent') + ' ranked</span></div>' +
            (d.board.rows.length ? '<ol class="of-board">' + d.board.rows.map(function (r) {
              return '<li class="' + (r.me ? 'me' : '') + '"><span class="pl">' + r.place + '</span><div class="who"><b>' + esc(r.name) + (r.me ? ' (you)' : '') + '</b><span>' + esc(r.rank) + '</span></div><span class="xp">' + r.xp + ' XP</span></li>';
            }).join('') + '</ol>' : '<p class="muted">Nobody has earned XP yet. Be the first.</p>') +
            (d.board.my_place && d.board.my_place > d.board.rows.length ? '<p class="small muted" style="margin:10px 0 0">You\'re #' + d.board.my_place + '. Keep going.</p>' : '') +
            '<p class="small faint" style="margin:10px 0 0">Prefer to stay in the shadows? Hide yourself in <a href="#profile" data-go="profile">your dossier</a>.</p></section>' +
          '<section class="ui-card"><div class="of-sec"><h2>Bulletins from HQ</h2></div>' +
            (d.bulletins.length ? '<div class="of-bull">' + d.bulletins.map(function (b) {
              return '<article class="' + esc(b.kind) + '"><time>' + esc(UI.fmtDate(b.created)) + '</time><h4>' + esc(b.title) + '</h4><p>' + esc(b.body) + '</p></article>';
            }).join('') + '</div>' : '<p class="muted">Quiet night. No bulletins.</p>') + '</section>' +
        '</div></div>';
    }
    view.addEventListener('click', function (e) {
      var b = e.target.closest('[data-sign]');
      if (!b) return;
      UI.busy(b, UI.api('claim_briefing')).then(function (r) { OS.celebrate(r); UI.toast('Briefing signed. ' + UI.plural(r.streak, 'day') + ' on duty.', 'ok'); return load(); });
    });
    function load() { return UI.api('get_office').then(draw); }
    return load();
  });
})();

/* ===== kit.html ===== */
(function () {
  var esc = UI.esc;

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) return navigator.clipboard.writeText(text).then(function () { UI.toast('Copied.', 'ok'); }, function () { UI.toast('Copy didn\'t work here: select the text instead.', 'error'); });
    UI.toast('Copy isn\'t available here: select the text instead.', 'error');
  }
  function gadgetHead(g) {
    return '<a class="small muted" href="#kit" data-go="kit">' + UI.icon('back') + ' Field Kit</a><div class="ui-page-head" style="margin-top:10px"><div><div class="eyebrow">Gadget</div><h1>' + esc(g.name) + '</h1><p class="muted">' + esc(g.what) + '</p></div></div>';
  }

  /* ---------------------------------------------------------------- dork builder */
  var RECIPES = [
    ['Exact name, one site', { exact: 'Martin Kessler', site: 'linkedin.com', any: '', all: '', not: '', type: '', intitle: '', inurl: '', after: '', before: '' }],
    ['Company documents', { exact: 'VK Media Solutions', type: 'pdf', all: 'annual report', site: '', any: '', not: '', intitle: '', inurl: '', after: '', before: '' }],
    ['Mentions not on their own site', { exact: 'Lumenhaus', not: 'site:lumenhaus-deals.example', all: 'scam OR review', site: '', any: '', type: '', intitle: '', inurl: '', after: '', before: '' }],
    ['Username anywhere', { exact: 'mkess84', all: '', site: '', any: '', not: '', type: '', intitle: '', inurl: '', after: '', before: '' }],
    ['News in a date range', { exact: 'Nightjar Collective', all: '', site: '', any: 'residency exhibition', not: '', type: '', intitle: '', inurl: '', after: '2026-01-01', before: '2026-12-31' }]
  ];
  function dork(view, g) {
    view.innerHTML = '<div class="ui-wrap"><div class="gd">' + gadgetHead(g) +
      '<div class="gd-recipes">' + RECIPES.map(function (r, i) { return '<button class="ui-btn sm" data-recipe="' + i + '">' + esc(r[0]) + '</button>'; }).join('') + '</div>' +
      '<div class="gd-panel"><form class="gd-form ui-card" data-dork>' +
        '<label class="ui-field"><span>Exact phrase <em>"in quotes"</em></span><input type="text" name="exact"></label>' +
        '<label class="ui-field"><span>All these words</span><input type="text" name="all"></label>' +
        '<label class="ui-field"><span>Any of these words <em>(OR)</em></span><input type="text" name="any"></label>' +
        '<label class="ui-field"><span>None of these <em>(-word)</em></span><input type="text" name="not"></label>' +
        '<div class="two"><label class="ui-field"><span>site:</span><input type="text" name="site" placeholder="example.org or .gov"></label>' +
        '<label class="ui-field"><span>filetype:</span><select name="type"><option value="">any</option><option>pdf</option><option>doc</option><option>docx</option><option>xls</option><option>xlsx</option><option>ppt</option><option>pptx</option><option>csv</option><option>txt</option></select></label></div>' +
        '<div class="two"><label class="ui-field"><span>intitle:</span><input type="text" name="intitle"></label><label class="ui-field"><span>inurl:</span><input type="text" name="inurl"></label></div>' +
        '<div class="two"><label class="ui-field"><span>after: <em>(Google)</em></span><input type="date" name="after"></label><label class="ui-field"><span>before:</span><input type="date" name="before"></label></div>' +
      '</form><div style="position:sticky;top:calc(var(--header-h) + 12px)"><div class="gd-out"><span class="lbl">Your query</span><div class="q" data-q></div>' +
        '<div class="ui-row" style="margin-top:14px"><button class="ui-btn sm" data-copy-q>' + UI.icon('copy') + 'Copy</button><a class="ui-btn sm" data-g target="_blank" rel="noopener">' + UI.icon('external') + 'Google</a><a class="ui-btn sm" data-b target="_blank" rel="noopener">' + UI.icon('external') + 'Bing</a><a class="ui-btn sm" data-d target="_blank" rel="noopener">' + UI.icon('external') + 'DuckDuckGo</a></div></div>' +
        '<p class="small muted" style="margin-top:12px">Operators differ between engines; after:/before: are Google-only. Searching is passive, but what you do with results must stay legal and proportionate.</p></div></div></div></div>';
    var form = view.querySelector('[data-dork]');
    function words(s) { return (s || '').trim().split(/\s+/).filter(Boolean); }
    function build() {
      var v = UI.formData(form), out = [];
      if (v.exact.trim()) out.push('"' + v.exact.trim().replace(/"/g, '') + '"');
      out = out.concat(words(v.all));
      var any = words(v.any);
      if (any.length) out.push(any.length > 1 ? '(' + any.join(' OR ') + ')' : any[0]);
      words(v.not).forEach(function (w) { out.push('-' + w.replace(/^-/, '')); });
      if (v.site.trim()) out.push('site:' + v.site.trim());
      if (v.type) out.push('filetype:' + v.type);
      if (v.intitle.trim()) out.push('intitle:' + (/\s/.test(v.intitle.trim()) ? '"' + v.intitle.trim() + '"' : v.intitle.trim()));
      if (v.inurl.trim()) out.push('inurl:' + v.inurl.trim());
      if (v.after) out.push('after:' + v.after);
      if (v.before) out.push('before:' + v.before);
      var q = out.join(' ');
      view.querySelector('[data-q]').textContent = q || 'Fill in a field to start.';
      var enc = encodeURIComponent(q);
      view.querySelector('[data-g]').href = 'https://www.google.com/search?q=' + enc;
      view.querySelector('[data-b]').href = 'https://www.bing.com/search?q=' + enc;
      view.querySelector('[data-d]').href = 'https://duckduckgo.com/?q=' + enc;
      return q;
    }
    form.addEventListener('input', build);
    view.addEventListener('click', function (e) {
      var r = e.target.closest('[data-recipe]');
      if (r) { var vals = RECIPES[+r.getAttribute('data-recipe')][1]; Object.keys(vals).forEach(function (k) { form.querySelector('[name=' + k + ']').value = vals[k]; }); build(); }
      if (e.target.closest('[data-copy-q]')) copyText(build());
    });
    build();
  }

  /* ---------------------------------------------------------------- username + email permutators */
  function slug(s) { return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]/g, ''); }
  function usernames(f, l, extra) {
    f = slug(f); l = slug(l); extra = slug(extra);
    if (!f && !l) return [];
    var fi = f.charAt(0), li = l.charAt(0), base = [];
    if (f && l) base = [f + l, f + '.' + l, f + '_' + l, f + '-' + l, fi + l, fi + '.' + l, fi + '_' + l, f + li, l + f, l + '.' + f, l + fi, f + l.slice(0, 4), f.slice(0, 4) + l.slice(0, 4), fi + li];
    else base = [f || l];
    var out = base.slice();
    if (extra) base.slice(0, 8).forEach(function (b) { out.push(b + extra, b + '_' + extra); });
    if (extra && extra.length === 4) base.slice(0, 4).forEach(function (b) { out.push(b + extra.slice(2)); });
    return out.filter(function (x, i) { return x && out.indexOf(x) === i; });
  }
  function permutator(view, g) {
    view.innerHTML = '<div class="ui-wrap"><div class="gd">' + gadgetHead(g) + '<div class="gd-panel"><form class="gd-form ui-card" data-perm>' +
      '<label class="ui-field"><span>First name</span><input type="text" name="f" value="Martin"></label><label class="ui-field"><span>Last name</span><input type="text" name="l" value="Kessler"></label>' +
      '<label class="ui-field"><span>Number or year <em>(birth year, lucky number)</em></span><input type="text" name="x" value="1984"></label>' +
      '<p class="ui-hint">Then test them in a username checker. A hit is a lead, not proof: confirm with a shared photo, bio or location.</p></form>' +
      '<div class="gd-out"><span class="lbl">Candidates · <span data-n></span></span><ul data-list></ul><div class="ui-row" style="margin-top:14px"><button class="ui-btn sm" data-copy-all>' + UI.icon('copy') + 'Copy all</button>' +
      '<a class="ui-btn sm" href="https://whatsmyname.app" target="_blank" rel="noopener">' + UI.icon('external') + 'WhatsMyName</a></div></div></div></div></div>';
    var form = view.querySelector('[data-perm]'), list = [];
    function run() {
      var v = UI.formData(form);
      list = usernames(v.f, v.l, v.x);
      view.querySelector('[data-n]').textContent = list.length;
      view.querySelector('[data-list]').innerHTML = list.map(function (u) { return '<li>' + esc(u) + '</li>'; }).join('') || '<li>Type a name.</li>';
    }
    form.addEventListener('input', run);
    view.addEventListener('click', function (e) { if (e.target.closest('[data-copy-all]')) copyText(list.join('\n')); });
    run();
  }
  function emailperm(view, g) {
    view.innerHTML = '<div class="ui-wrap"><div class="gd">' + gadgetHead(g) + '<div class="gd-panel"><form class="gd-form ui-card" data-email>' +
      '<label class="ui-field"><span>First name</span><input type="text" name="f" value="Tom"></label><label class="ui-field"><span>Last name</span><input type="text" name="l" value="Wills"></label>' +
      '<label class="ui-field"><span>Company domain</span><input type="text" name="d" value="company.example"></label>' +
      '<p class="ui-hint">Find one real address at the company first (a press release, a PDF): it tells you which pattern they use. Never "test" addresses by triggering password resets.</p></form>' +
      '<div class="gd-out"><span class="lbl">Likely formats, most common first</span><ul data-list></ul><div class="ui-row" style="margin-top:14px"><button class="ui-btn sm" data-copy-all>' + UI.icon('copy') + 'Copy all</button></div></div></div></div></div>';
    var form = view.querySelector('[data-email]'), list = [];
    function run() {
      var v = UI.formData(form), f = slug(v.f), l = slug(v.l), d = (v.d || '').trim().toLowerCase().replace(/^@/, '').replace(/[^a-z0-9.-]/g, '');
      if (!f || !d) { list = []; } else {
        var fi = f.charAt(0), li = l.charAt(0);
        list = (l ? [f + '.' + l, fi + l, f, f + l, f + '_' + l, fi + '.' + l, f + li, l + '.' + f, l + fi, l, f + '-' + l, fi + li] : [f]).map(function (x) { return x + '@' + d; });
        list = list.filter(function (x, i) { return list.indexOf(x) === i; });
      }
      view.querySelector('[data-list]').innerHTML = list.map(function (u) { return '<li>' + esc(u) + '</li>'; }).join('') || '<li>Type a first name and a domain.</li>';
    }
    form.addEventListener('input', run);
    view.addEventListener('click', function (e) { if (e.target.closest('[data-copy-all]')) copyText(list.join('\n')); });
    run();
  }

  /* ---------------------------------------------------------------- EXIF reader (JPEG, in the browser) */
  var TAGS0 = { 0x010E: 'Description', 0x010F: 'Camera make', 0x0110: 'Camera model', 0x0112: 'Orientation', 0x0131: 'Software', 0x0132: 'Modified', 0x013B: 'Artist', 0x8298: 'Copyright' };
  var TAGSX = { 0x9003: 'Taken', 0x9004: 'Digitised', 0x9011: 'Time zone (taken)', 0x829A: 'Exposure', 0x829D: 'F-number', 0x8827: 'ISO', 0x920A: 'Focal length', 0xA434: 'Lens', 0xA431: 'Body serial number', 0xA002: 'Width', 0xA003: 'Height' };
  var SIZES = { 1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 7: 1, 9: 4, 10: 8 };
  function parseExif(buf) {
    var dv = new DataView(buf), len = dv.byteLength, off = 2;
    if (len < 4 || dv.getUint16(0) !== 0xFFD8) return { error: 'This isn\'t a JPEG. EXIF reading works on .jpg photos (most phone and camera photos).' };
    while (off + 4 < len) {
      var marker = dv.getUint16(off);
      if ((marker & 0xFF00) !== 0xFF00) break;
      var size = dv.getUint16(off + 2);
      if (marker === 0xFFE1 && dv.getUint32(off + 4) === 0x45786966) return readTiff(dv, off + 10);
      if (marker === 0xFFDA) break;
      off += 2 + size;
    }
    return { fields: [], gps: null };
  }
  function readTiff(dv, tiff) {
    var little = dv.getUint16(tiff) === 0x4949;
    function u16(o) { return dv.getUint16(o, little); }
    function u32(o) { return dv.getUint32(o, little); }
    function val(e) {
      var type = u16(e + 2), count = u32(e + 4), sz = (SIZES[type] || 1) * count, at = sz > 4 ? tiff + u32(e + 8) : e + 8, i, out = [];
      if (at + sz > dv.byteLength) return null;
      if (type === 2) { var s = ''; for (i = 0; i < count; i++) { var c = dv.getUint8(at + i); if (!c) break; s += String.fromCharCode(c); } return s.trim(); }
      for (i = 0; i < Math.min(count, 16); i++) {
        if (type === 3) out.push(u16(at + i * 2));
        else if (type === 4) out.push(u32(at + i * 4));
        else if (type === 9) out.push(dv.getInt32(at + i * 4, little));
        else if (type === 5) out.push(u32(at + i * 8) / (u32(at + i * 8 + 4) || 1));
        else if (type === 10) out.push(dv.getInt32(at + i * 8, little) / (dv.getInt32(at + i * 8 + 4, little) || 1));
        else out.push(dv.getUint8(at + i));
      }
      return out.length === 1 ? out[0] : out;
    }
    function ifd(start) {
      var res = {};
      if (start + 2 > dv.byteLength) return res;
      var n = u16(start);
      for (var i = 0; i < n && i < 400; i++) { var e = start + 2 + i * 12; if (e + 12 > dv.byteLength) break; res[u16(e)] = val(e); }
      return res;
    }
    var fields = [], gps = null;
    var i0 = ifd(tiff + u32(tiff + 4));
    Object.keys(TAGS0).forEach(function (t) { if (i0[t] != null && i0[t] !== '') fields.push([TAGS0[t], i0[t]]); });
    if (i0[0x8769]) {
      var ex = ifd(tiff + i0[0x8769]);
      Object.keys(TAGSX).forEach(function (t) {
        var v = ex[t];
        if (v == null || v === '') return;
        if (+t === 0x829A && typeof v === 'number') v = v < 1 ? '1/' + Math.round(1 / v) + ' s' : v + ' s';
        if (+t === 0x829D && typeof v === 'number') v = 'f/' + v.toFixed(1);
        if (+t === 0x920A && typeof v === 'number') v = v.toFixed(1) + ' mm';
        fields.push([TAGSX[t], v]);
      });
    }
    if (i0[0x8825]) {
      var gp = ifd(tiff + i0[0x8825]);
      function dms(a, ref) { if (!a || a.length < 3) return null; var d = a[0] + a[1] / 60 + a[2] / 3600; return (ref === 'S' || ref === 'W') ? -d : d; }
      var lat = dms(gp[2], gp[1]), lon = dms(gp[4], gp[3]);
      if (lat != null && lon != null && !(lat === 0 && lon === 0)) gps = { lat: lat, lon: lon, alt: typeof gp[6] === 'number' ? gp[6] : null };
    }
    return { fields: fields, gps: gps };
  }
  function exifreader(view, g) {
    view.innerHTML = '<div class="ui-wrap"><div class="gd">' + gadgetHead(g) +
      '<div class="ui-note" style="margin-bottom:16px">' + UI.icon('lock') + ' <b>Private:</b> your photo is read by this page in your browser. It is never uploaded to Osinty or anyone else.</div>' +
      '<label class="gd-drop" data-drop>' + UI.icon('camera') + '<div><b>Choose a photo</b> or drop it here</div><div class="small muted">JPEG files from phones and cameras usually carry metadata; photos saved from social networks usually don\'t.</div>' +
      '<input type="file" accept="image/jpeg,image/*" data-file></label><div class="gd-exif" data-res style="margin-top:18px"></div></div></div>';
    var res = view.querySelector('[data-res]'), drop = view.querySelector('[data-drop]'), url = null;
    function read(file) {
      if (!file) return;
      if (url) URL.revokeObjectURL(url);
      url = URL.createObjectURL(file);
      var fr = new FileReader();
      fr.onload = function () {
        var out;
        try { out = parseExif(fr.result); } catch (err) { out = { error: 'This file\'s metadata couldn\'t be read.' }; }
        var rows = out.fields ? out.fields.slice() : [];
        rows.unshift(['File', file.name + ' · ' + Math.round(file.size / 1024) + ' KB']);
        res.innerHTML = '<div class="ui-card"><img src="' + url + '" alt="Your photo">' +
          (out.error ? '<div class="ui-error">' + esc(out.error) + '</div>' : '') +
          (!out.error && rows.length === 1 && !out.gps ? '<div class="ui-note">No EXIF metadata in this file. It was probably stripped (social networks, messaging apps and screenshots do that). Try the original file.</div>' : '') +
          '<table>' + rows.map(function (r) { return '<tr><th>' + esc(r[0]) + '</th><td>' + esc(Array.isArray(r[1]) ? r[1].join(', ') : r[1]) + '</td></tr>'; }).join('') +
          (out.gps ? '<tr><th>GPS</th><td>' + out.gps.lat.toFixed(6) + ', ' + out.gps.lon.toFixed(6) + (out.gps.alt != null ? ' · ' + Math.round(out.gps.alt) + ' m' : '') +
            '<div class="ui-row" style="margin-top:8px"><a class="ui-btn sm" target="_blank" rel="noopener" href="https://www.openstreetmap.org/?mlat=' + out.gps.lat.toFixed(6) + '&mlon=' + out.gps.lon.toFixed(6) + '#map=18/' + out.gps.lat.toFixed(6) + '/' + out.gps.lon.toFixed(6) + '">' + UI.icon('map') + 'OpenStreetMap</a>' +
            '<a class="ui-btn sm" target="_blank" rel="noopener" href="https://www.google.com/maps?q=' + out.gps.lat.toFixed(6) + ',' + out.gps.lon.toFixed(6) + '">' + UI.icon('pin') + 'Google Maps</a></div></td></tr>' : '') + '</table>' +
          '<p class="small muted" style="margin:12px 0 0">Metadata can be wrong or edited. Treat it as one witness and corroborate it with what you see in the picture.</p></div>';
      };
      fr.readAsArrayBuffer(file.slice(0, 512 * 1024));
    }
    view.querySelector('[data-file]').addEventListener('change', function (e) { read(e.target.files[0]); });
    drop.addEventListener('dragover', function (e) { e.preventDefault(); drop.classList.add('over'); });
    drop.addEventListener('dragleave', function () { drop.classList.remove('over'); });
    drop.addEventListener('drop', function (e) { e.preventDefault(); drop.classList.remove('over'); read(e.dataTransfer.files[0]); });
    return { destroy: function () { if (url) URL.revokeObjectURL(url); } };
  }

  /* ---------------------------------------------------------------- ID + time decoder */
  function fmt(ms) {
    var d = new Date(ms);
    if (isNaN(d.getTime())) return null;
    return d.toISOString().replace('T', ' ').replace(/\.\d+Z$/, ' UTC') + '<br><span style="color:#8d7f69">' + esc(d.toLocaleString()) + ' (your time)</span>';
  }
  function snowflake(view, g) {
    view.innerHTML = '<div class="ui-wrap"><div class="gd">' + gadgetHead(g) + '<div class="gd-panel"><form class="gd-form ui-card" data-sf onsubmit="return false">' +
      '<label class="ui-field"><span>A post or message ID, or a Unix timestamp</span><input type="text" name="v" inputmode="numeric" value="1580661436132757504"></label>' +
      '<p class="ui-hint">X (Twitter) and Discord IDs are "snowflakes": the first bits are the creation time in milliseconds. A post\'s ID tells you exactly when it was made, even if the page hides it. Copy the long number from the post\'s URL.</p>' +
      '<label class="ui-field"><span>Or a date and time (UTC) to convert to Unix time</span><input type="datetime-local" name="dt"></label></form>' +
      '<div class="gd-out" data-out></div></div></div></div>';
    var form = view.querySelector('[data-sf]'), out = view.querySelector('[data-out]');
    function run() {
      var v = UI.formData(form), s = (v.v || '').replace(/\D/g, ''), html = '';
      if (s) {
        if (s.length >= 15 && s.length <= 20 && window.BigInt) {
          var big = BigInt(s), t = Number(big >> BigInt(22));
          var tw = fmt(t + 1288834974657), dc = fmt(t + 1420070400000);
          html += '<span class="lbl">As an X / Twitter post ID</span><div class="q">' + (tw || 'not valid') + '</div><br>' +
            '<span class="lbl">As a Discord ID</span><div class="q">' + (dc || 'not valid') + '</div><br>' +
            '<span class="lbl">Which one?</span><div>Use the one that matches where the ID came from. The other reading is meaningless.</div>';
        } else if (s.length === 10 || s.length === 13) {
          html += '<span class="lbl">Unix time (' + (s.length === 10 ? 'seconds' : 'milliseconds') + ')</span><div class="q">' + (fmt(s.length === 10 ? +s * 1000 : +s) || 'not valid') + '</div>';
        } else html += '<span class="lbl">Hmm</span><div>That\'s ' + s.length + ' digits. Snowflake IDs have 15 to 20 digits; Unix times have 10 (seconds) or 13 (milliseconds).</div>';
      }
      if (v.dt) {
        var ms = Date.parse(v.dt + ':00Z');
        if (!isNaN(ms)) html += (html ? '<br>' : '') + '<span class="lbl">' + esc(v.dt.replace('T', ' ')) + ' UTC as Unix time</span><div class="q">' + Math.floor(ms / 1000) + ' s · ' + ms + ' ms</div>';
      }
      out.innerHTML = html || '<span class="lbl">Result</span><div>Paste an ID or a timestamp.</div>';
    }
    form.addEventListener('input', run);
    run();
  }

  /* ---------------------------------------------------------------- source grader */
  var REL_HELP = { A: 'A proven, authoritative source: an official register, a court record.', B: 'Generally right, minor doubts: an established newspaper, a well-run company site.',
    C: 'Has been right before, but you have doubts: a known blogger, a review site.', D: 'Often wrong or biased: a tabloid, an anonymous aggregator.',
    E: 'Known to be wrong, or a suspected liar.', F: 'A new source you can\'t assess yet: an anonymous account, a first-time forum poster.' };
  function grader(view, g) {
    view.innerHTML = '<div class="ui-wrap"><div class="gd">' + gadgetHead(g) + '<form class="gd-grade" data-grade>' +
      '<fieldset><legend>Source reliability</legend>' + Object.keys(OS.REL).map(function (k) { return '<label><input type="radio" name="r" value="' + k + '"' + (k === 'B' ? ' checked' : '') + '><b class="mono">' + k + '</b> ' + esc(OS.REL[k]) + '</label>'; }).join('') + '</fieldset>' +
      '<fieldset><legend>Information credibility</legend>' + Object.keys(OS.CRED).map(function (k) { return '<label><input type="radio" name="c" value="' + k + '"' + (k === '2' ? ' checked' : '') + '><b class="mono">' + k + '</b> ' + esc(OS.CRED[k]) + '</label>'; }).join('') + '</fieldset></form>' +
      '<div class="gd-out" style="margin-top:18px" data-out></div>' +
      '<p class="small muted" style="margin-top:14px">The two are graded separately on purpose: a reliable source can pass on a rumour (A4), and an unknown source can tell you something you\'ve confirmed elsewhere (F1). Grade every lead in your casebook.</p></div></div>';
    var form = view.querySelector('[data-grade]'), out = view.querySelector('[data-out]');
    function run() {
      var v = UI.formData(form), code = v.r + v.c, n = +v.c;
      var advice = n <= 2 && 'ABC'.indexOf(v.r) >= 0 ? 'Strong enough to state as a finding, with the source cited.'
        : n <= 3 ? 'Report it as an assessment ("likely", "possibly") and look for a second, independent source.'
        : 'Treat as unconfirmed. Don\'t base conclusions on it; flag it and keep digging.';
      out.innerHTML = '<div class="ui-row" style="gap:20px;align-items:center"><div class="gd-code">' + esc(code) + '</div><div><b>' + esc(OS.REL[v.r]) + ' source, ' + esc(OS.CRED[v.c].toLowerCase()) + '.</b><div style="color:#b9a98c;margin-top:6px">' + esc(REL_HELP[v.r]) + '</div></div></div>' +
        '<div style="margin-top:12px;border-top:1px dashed #4b403a;padding-top:12px"><span class="lbl">How to use it</span>' + esc(advice) + '</div>';
    }
    form.addEventListener('change', run);
    run();
  }

  var GADGET_FN = { dorkbuilder: dork, permutator: permutator, emailperm: emailperm, exifreader: exifreader, snowflake: snowflake, grader: grader };

  /* ---------------------------------------------------------------- the kit page */
  function library(view) {
    var cat = UI.store.get('kit.cat', 'all'), q = '', savedOnly = false, saved = [];
    function drawLib() {
      var needle = q.toLowerCase();
      var tools = OS.TOOLS.filter(function (t) {
        return (cat === 'all' || t.cat === cat) && (!savedOnly || saved.indexOf(t.id) >= 0) &&
          (!needle || (t.name + ' ' + t.what + ' ' + t.tip).toLowerCase().indexOf(needle) >= 0);
      });
      view.querySelector('[data-lib]').innerHTML = tools.length ? tools.map(function (t) {
        var on = saved.indexOf(t.id) >= 0;
        return '<article class="kt-tool"><button class="ui-btn ghost icon kt-star' + (on ? ' on' : '') + '" data-star="' + t.id + '" aria-pressed="' + on + '" aria-label="' + (on ? 'Remove from' : 'Save to') + ' my kit">' + UI.icon('star') + '</button>' +
          '<div class="cat">' + esc(OS.CATS[t.cat]) + '</div><h3>' + esc(t.name) + '</h3><p>' + esc(t.what) + '</p><div class="tip">' + esc(t.tip) + '</div>' +
          '<div class="foot"><a class="ui-btn sm" href="' + esc(t.url) + '" target="_blank" rel="noopener">' + UI.icon('external') + 'Open</a><span class="ui-badge' + (t.cost === 'Free' ? ' good' : t.cost === 'Paid' ? ' warn' : '') + '">' + esc(t.cost) + '</span></div></article>';
      }).join('') : '<div class="ui-empty" style="grid-column:1/-1">' + UI.icon('tool') + '<h3>Nothing here</h3><p>' + (savedOnly ? 'Star tools to build your kit.' : 'No tool matches that search.') + '</p></div>';
    }
    view.addEventListener('input', function (e) { if (e.target.matches('[data-q]')) { q = e.target.value; drawLib(); } });
    view.addEventListener('change', function (e) { if (e.target.matches('[data-saved]')) { savedOnly = e.target.checked; drawLib(); } });
    view.addEventListener('click', function (e) {
      var c = e.target.closest('[data-cat]');
      if (c) { cat = c.getAttribute('data-cat'); UI.store.set('kit.cat', cat); view.querySelectorAll('[data-cat]').forEach(function (b) { b.classList.toggle('on', b === c); }); drawLib(); return; }
      var s = e.target.closest('[data-star]');
      if (s) {
        var id = s.getAttribute('data-star'), flag = saved.indexOf(id) < 0;
        UI.api('toggle_kit', id, flag).then(function (r) { saved = r.saved; drawLib(); OS.celebrate(r); if (flag) UI.toast('Saved to your kit.'); });
      }
    });
    return UI.api('get_kit').then(function (d) {
      saved = d.saved;
      view.innerHTML = '<div class="ui-wrap"><div class="ui-page-head"><div><div class="eyebrow">Field Kit</div><h1>Gadgets & tools</h1><p class="muted">Gadgets run right here. The library lists real tools investigators use, with a tip for each. Star the ones you rely on.</p></div></div>' +
        '<div class="kt-gadgets">' + OS.GADGETS.map(function (g) {
          return '<a class="kt-gadget" href="#kit/' + g.id + '" data-go="kit/' + g.id + '"><span class="ic">' + UI.icon(g.icon) + '</span><div><b>' + esc(g.name) + '</b><span>' + esc(g.what) + '</span></div></a>';
        }).join('') + '</div>' +
        '<div class="kt-bar"><h2 style="margin:0 12px 0 0">The library</h2><input type="search" placeholder="Search tools" aria-label="Search tools" data-q><label class="ui-check"><input type="checkbox" data-saved> My kit only</label></div>' +
        '<div class="kt-cats">' + [['all', 'All']].concat(Object.keys(OS.CATS).map(function (k) { return [k, OS.CATS[k]]; })).map(function (c) {
          return '<button type="button" data-cat="' + c[0] + '" class="' + (cat === c[0] ? 'on' : '') + '">' + esc(c[1]) + '</button>';
        }).join('') + '</div><div class="kt-lib" data-lib></div>' +
        '<p class="small muted" style="margin-top:22px">Osinty isn\'t affiliated with these tools. Read each one\'s terms, and remember: a tool being available doesn\'t make every use of it legal.</p></div>';
      drawLib();
    });
  }

  UI.page('kit', { title: 'Field Kit', nav: 'Kit', icon: 'tool', auth: 'user', order: 50 }, function (view, ctx) {
    var g = ctx.args[0] && OS.GADGETS.filter(function (x) { return x.id === ctx.args[0]; })[0];
    if (g) { document.title = g.name + ' · ' + UI.config.name; return GADGET_FN[g.id](view, g) || Promise.resolve(); }
    view.innerHTML = '<div class="ui-wrap"><div class="ui-skel" style="height:300px"></div></div>';
    return library(view);
  });
})();

/* ===== landing.html ===== */
// Watch section: swap the video's cover for YouTube's player (privacy-enhanced) only when it's pressed.
  if (!window.__ytFilm) {
    window.__ytFilm = true;
    document.addEventListener('click', function (e) {
      var b = e.target && e.target.closest ? e.target.closest('[data-yt-film]') : null;
      if (!b) return;
      var f = document.createElement('iframe');
      f.src = 'https://www.youtube-nocookie.com/embed/' + b.getAttribute('data-yt-film') + '?autoplay=1&rel=0&playsinline=1';
      f.title = b.getAttribute('data-yt-title') || 'Video';
      f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
      f.allowFullscreen = true;
      f.referrerPolicy = 'strict-origin-when-cross-origin';
      b.parentNode.replaceChild(f, b);
    });
  }
(function () {
  var COPY = {
    eyebrow: 'The OSINT academy for private eyes',
    title: 'Every trace tells a story. <em>Learn to read it.</em>',
    lead: 'Osinty teaches open-source intelligence the way private investigators use it: search like a pro, unmask fake profiles, geolocate a photo, trace a company. Then prove it on realistic case files. Legally, ethically, step by step.',
    cta: 'Join the Bureau, it\'s free',
    proof: ['24 lessons', '6 case files', '40 real tools', 'No ads'],
    steps: [['Train', 'Short, sharp lessons from the investigator\'s mindset to running a practice, each ending with a pop quiz.'],
            ['Investigate', 'Open a case file and work the terminal: web, social, records, WHOIS, archives and an image lab.'],
            ['Pivot', 'One clue leads to the next: a username to a photo, a photo to a street, a tracking ID to a network.'],
            ['Get promoted', 'Earn XP, climb seven ranks from Rookie to Master Sleuth, and collect commendations.']],
    modules: [['eye', 'The Investigator\'s Mindset', 'The intelligence cycle, the law and OPSEC.'], ['search', 'Search Like a Detective', 'Operators, other engines, archives.'],
              ['user', 'People & Records', 'Usernames, emails, public records.'], ['users', 'Social Media Intelligence', 'Profiles, patterns of life, catfish.'],
              ['camera', 'Images & Video', 'Reverse search, EXIF, verification.'], ['pin', 'Geolocation', 'Signs, satellites, shadows and the sun.'],
              ['briefcase', 'Companies & Domains', 'Registries, WHOIS, tracking IDs, assets.'], ['award', 'Going Pro', 'Licensing, grading sources, reports.']],
    features: [['terminal', 'Case files that feel real', 'Six fictional investigations, from a lost cat to a missing-person search party. Hints cost points; good tradecraft scores.'],
               ['board', 'Your own casebook', 'Pin leads on a corkboard, tie red strings, grade every source with the Admiralty code, print a clean report.'],
               ['tool', 'A field kit that works', 'Dork builder, username and email permutators, an in-browser EXIF reader, a post-ID decoder, a source grader.'],
               ['book', '40 real tools, explained', 'The tools investigators actually use, each with a pro tip. Star them to build your kit.'],
               ['crown', 'Ranks and the Bureau', 'XP, a daily briefing streak, 13 commendations and a leaderboard you can hide from.'],
               ['shield', 'Ethics built in', 'Every lesson keeps you on the right side of the line. Observe, never touch.']],
    faq: [['Will Osinty make me a licensed private investigator?', 'No. Many places require a licence to investigate for pay, issued by a regulator after experience, training and checks. Osinty teaches the open-source skills and the professional habits; the licence comes from your regulator. Lesson 8.1 explains how to find the rules where you live.'],
          ['Is any of this illegal?', 'No. Osinty only teaches lawful, open-source methods: reading what is already public. No hacking, no pretexting, no impersonation, no stolen data. The case files are fictional, and their websites use the reserved .example domain.'],
          ['Do I need to be technical?', 'No. If you can use a search engine, you can start. The lessons build up from there, and the gadgets do the fiddly parts for you.'],
          ['Is it free?', 'Yes, all of it: lessons, case files, casebook and field kit.'],
          ['Who can see my casebook?', 'Only you. Other agents see your display name and XP on the leaderboard, and you can hide even that. The Privacy & Terms page has the details.'],
          ['Can I use it on my phone?', 'Yes. It works in any modern browser, and you can add it to your home screen.']]
  };

  // the clues pinned across the board, tied to the case-file card with red string
  function heroArt() {
    return '<div class="lp-clues" aria-hidden="true">' +
      '<svg class="str" viewBox="0 0 100 100" preserveAspectRatio="none"><path d="M44 30 Q55 22 64 12"/><path d="M64 12 Q78 14 90 16"/><path d="M44 30 Q58 44 66 62"/>' +
        '<path d="M66 62 Q76 62 86 60"/><path d="M64 12 Q70 26 71 40"/><path d="M71 40 Q80 52 86 60"/></svg>' +
      '<div class="it pol p1"><svg class="ph" viewBox="0 0 60 60"><rect width="60" height="60" fill="#d9c7a6"/><rect y="38" width="60" height="22" fill="#b79b74"/><circle cx="30" cy="26" r="11" fill="#e08a3c"/><path d="M21 18 24 9 28 16zM39 18 36 9 32 16z" fill="#e08a3c"/><circle cx="26" cy="25" r="1.6" fill="#2a241d"/><circle cx="34" cy="25" r="1.6" fill="#2a241d"/><ellipse cx="30" cy="46" rx="14" ry="9" fill="#e08a3c"/><ellipse cx="22" cy="53" rx="3.5" ry="2.5" fill="#fff"/></svg><span>BISCUIT?</span></div>' +
      '<div class="it pol p2"><svg class="ph" viewBox="0 0 60 60"><rect width="60" height="60" fill="#9fb6c4"/><rect y="40" width="60" height="20" fill="#e8d9b5"/><path d="M0 40 Q15 34 30 38 T60 36 V40 H0z" fill="#5f8ba0"/><path d="M44 12h4v20h-4z" fill="#f4f1ea"/><path d="M42 12l4-6 4 6z" fill="#c0392f"/><circle cx="14" cy="13" r="6" fill="#f3d27a"/></svg><span>ERICEIRA</span></div>' +
      '<div class="it pol p3"><svg class="ph" viewBox="0 0 60 60"><rect width="60" height="60" fill="#3a3330"/><rect x="8" y="10" width="44" height="30" rx="2" fill="#f1e6d0"/><path d="M12 16h24M12 21h30M12 26h18" stroke="#8f1d21" stroke-width="2"/><rect x="12" y="31" width="14" height="5" fill="#e3b55c"/><rect x="8" y="44" width="44" height="8" fill="#5a4a3e"/></svg><span>LX-447821</span></div>' +
      '<div class="it card"><b>@mkess84</b>Winnipeg → Saskatoon?<br>curling · HVAC · b.1984</div>' +
      '<div class="it note">CASE FILE 05<i></i><i style="width:70%"></i><i style="width:85%"></i><i style="width:55%"></i></div>' +
      '<span class="os-stamp stampx" style="--stamp:#8f1d21;background:rgba(251,248,241,.7)">Case closed</span>' +
      '<div class="glass"></div></div>';
  }

  UI.page('landing', { title: 'Learn OSINT like a private investigator' }, function (view, ctx) {
    var me = ctx.me, C = COPY, esc = UI.esc;
    var primary = me ? '<a class="ui-btn primary lg" href="#home" data-go="home">Back to the office ' + UI.icon('arrow') + '</a>'
      : '<a class="ui-btn primary lg" href="#auth/signup" data-go="auth/signup">' + esc(C.cta) + ' ' + UI.icon('arrow') + '</a>' +
        '<a class="ui-btn lg" href="#auth" data-go="auth">I have a badge</a>';
    view.innerHTML =
      '<section class="lp-hero">' + heroArt() + '<div class="ui-wrap"><div class="lp-file">' +
        '<div class="eyebrow">' + esc(C.eyebrow) + '</div><h1>' + C.title + '</h1><p class="lp-lead">' + esc(C.lead) + '</p>' +
        '<div class="lp-cta">' + primary + '</div>' +
        '<div class="lp-proof">' + C.proof.map(function (p) { return '<span>' + UI.icon('check') + esc(p) + '</span>'; }).join('') + '</div>' +
      '</div></div></section>' +
      '<section class="lp-section ytf" id="watch"><div class="ui-wrap"><div class="ytf-in"><div class="ytf-copy"><div class="eyebrow"><svg viewBox="0 0 28 20" width="20" height="14" aria-hidden="true"><rect width="28" height="20" rx="5" fill="#FF0033"/><path d="M11.2 5.8v8.4l7.3-4.2z" fill="#fff"/></svg>Watch</div><h2>See Osinty in about a minute</h2><p>A short video tour of what Osinty does and how it works.</p><a class="ytf-link" href="https://www.youtube.com/watch?v=3AZprKF2iH0" target="_blank" rel="noopener">Watch on YouTube &#8599;</a></div><div><div class="ytf-frame"><button type="button" class="ytf-cover" data-yt-film="3AZprKF2iH0" data-yt-title="Osinty video" aria-label="Play the Osinty video (1:11)"><img src="_/theme/yt-cover.jpg" alt="" loading="lazy" decoding="async" width="960" height="540"><span class="ytf-play" aria-hidden="true"><svg viewBox="0 0 68 48" width="68" height="48"><path d="M66.5 7.7a8.5 8.5 0 0 0-6-6C55.3.3 34 .3 34 .3s-21.3 0-26.5 1.4a8.5 8.5 0 0 0-6 6C.1 13 .1 24 .1 24s0 11 1.4 16.3a8.5 8.5 0 0 0 6 6c5.2 1.4 26.5 1.4 26.5 1.4s21.3 0 26.5-1.4a8.5 8.5 0 0 0 6-6C67.9 35 67.9 24 67.9 24s0-11-1.4-16.3z" fill="#FF0033"/><path d="M45 24 27 14v20z" fill="#fff"/></svg></span><span class="ytf-len">1:11</span></button></div><p class="ytf-note">The video loads from YouTube when you press play.</p></div></div></div></section>' +
      '<section class="lp-section" id="how"><div class="ui-wrap"><div class="lp-head"><div class="eyebrow">How it works</div><h2>From rookie to master sleuth</h2><p>Learn a technique, use it on a case, and watch one clue unlock the next.</p></div>' +
        '<div class="lp-steps">' + C.steps.map(function (s) { return '<div class="ui-card lp-step"><h3>' + esc(s[0]) + '</h3><p class="muted" style="margin:0">' + esc(s[1]) + '</p></div>'; }).join('') + '</div></div></section>' +
      '<section class="lp-section" style="padding-top:20px"><div class="ui-wrap"><div class="lp-head"><div class="eyebrow">The Academy</div><h2>Eight modules, twenty-four lessons</h2><p>Plain language, real techniques, a field note and a pop quiz in every lesson.</p></div>' +
        '<div class="lp-mods">' + C.modules.map(function (m, i) { return '<div class="os-folder lp-mod" data-tab="Module ' + (i + 1) + '">' + UI.icon(m[0]) + '<h3>' + esc(m[1]) + '</h3><p>' + esc(m[2]) + '</p></div>'; }).join('') + '</div></div></section>' +
      '<section class="lp-section"><div class="ui-wrap lp-term"><div><div class="eyebrow">Case file #3 · Operation Lamplight</div><h2>A shop "trusted since 1998". On a domain registered in September.</h2>' +
        '<p class="muted">Every case gives you a client, a briefing and exhibits. You choose the source, type the query, and follow the trail. Find a tracking ID in the page source, and it leads to two more fake shops. One of them has an old WHOIS record...</p>' +
        '<p class="muted">Get stuck? Take a hint, at a price. Close the case and read HQ\'s debrief on what a professional would do next.</p></div>' +
        '<div class="lp-tbox" aria-hidden="true"><div class="bar"><i></i><i></i><i></i></div>' +
          '<div><span class="p">&gt; whois</span> lumenhaus-deals.example</div><div class="r">Created: 2 September 2026 · Registrant: REDACTED</div><br>' +
          '<div><span class="p">&gt; web</span> LX-447821</div><div class="hit">3 sites share this tracking ID</div><div class="r">nordic-sofa-outlet.example · brightbike-clearance.example</div><br>' +
          '<div><span class="p">&gt; whois</span> nordic-sofa-outlet.example</div><div class="hit">Historical record (2024): VK Media Solutions</div><br><div><span class="p">&gt;</span> <span class="cur"></span></div></div></div></section>' +
      '<section class="lp-section"><div class="ui-wrap"><div class="lp-head"><h2>Everything an investigator needs</h2></div>' +
        '<div class="ui-grid">' + C.features.map(function (f) { return '<div class="ui-card lp-feature">' + UI.icon(f[0]) + '<h3>' + esc(f[1]) + '</h3><p>' + esc(f[2]) + '</p></div>'; }).join('') + '</div></div></section>' +
      '<section class="lp-section"><div class="ui-wrap"><div class="lp-code"><span class="os-stamp">Code of conduct</span><h2 style="margin-top:0">The line we don\'t cross</h2>' +
        '<ol><li><b>Open sources only.</b> No hacking, no guessed passwords, no stolen or leaked data.</li>' +
        '<li><b>No pretexting, no impersonation.</b> We read what\'s public; we don\'t lie to get the rest.</li>' +
        '<li><b>Observe, never touch.</b> No liking, following, messaging or calling a subject.</li>' +
        '<li><b>A legitimate purpose, every time.</b> We refuse jobs that look like stalking, harassment or revenge.</li>' +
        '<li><b>Proportionate and private.</b> Collect only what the question needs, and keep it safe.</li></ol></div></div></section>' +
      '<section class="lp-section"><div class="ui-wrap"><div class="lp-head"><h2>Questions</h2></div><div class="lp-faq">' +
        C.faq.map(function (q) { return '<details><summary>' + esc(q[0]) + '</summary><p>' + esc(q[1]) + '</p></details>'; }).join('') + '</div></div></section>' +
      '<section class="lp-section"><div class="ui-wrap"><div class="lp-band"><div><h2>Your first case is waiting.</h2><p>A lost tabby, a neighbourhood board and a photo that knows where it was taken.</p></div>' +
        (me ? '<a class="ui-btn lg" href="#cases/c1" data-go="cases/c1">Open case file #1</a>' : '<a class="ui-btn lg" href="#auth/signup" data-go="auth/signup">' + esc(C.cta) + '</a>') +
      '</div></div></section>';
  });
})();

/* ===== profile.html ===== */
(function () {
  var esc = UI.esc;
  UI.page('profile', { title: 'Your dossier', auth: 'user' }, function (view, ctx) {
    var me = ctx.me;
    view.innerHTML = '<div class="ui-wrap ui-narrow"><div class="pf-head"><span class="ui-avatar">' + esc(UI.initials(me.name)) + '</span>' +
      '<div><h1>' + esc(me.name) + '</h1><div class="muted">' + esc(me.email) + (me.joined ? ' · member since ' + esc(UI.fmtDate(me.joined, { month: 'long', year: 'numeric' })) : '') + '</div></div></div>' +
      '<div data-dossier><div class="ui-skel" style="height:260px;margin-bottom:18px"></div></div>' +
      '<div class="pf-grid"><form class="ui-card ui-stack" data-name><h3>Your agent name</h3><label class="ui-field"><span>Shown on the Bureau leaderboard. A codename is fine.</span>' +
      '<input type="text" name="name" value="' + esc(me.name) + '" maxlength="60" required></label><button class="ui-btn primary" type="submit">Save</button></form>' +
      '<div class="ui-card ui-stack"><h3>Appearance</h3><p class="muted small">Follow your device, or pick one.</p><div data-theme-box></div>' +
      '<h3 style="margin-top:22px">Password</h3><p class="muted small">We\'ll email you a link to choose a new one.</p>' +
      '<button class="ui-btn" data-reset>' + UI.icon('mail') + 'Email me a reset link</button></div></div>' +
      '<div class="ui-card" style="margin-top:16px"><div class="pf-links">' +
      (me.is_admin ? '<a href="#admin" data-go="admin">' + UI.icon('shield') + 'Admin</a>' : '') +
      '<button data-feedback>' + UI.icon('chat') + 'Submit feedback</button>' +
      '<button data-lk-open="overview">' + UI.icon('lock') + 'Privacy &amp; Terms, and your data</button>' +
      '<button data-signout-here>' + UI.icon('logout') + 'Sign out</button></div></div></div>';
    function themeBox() {
      var t = UI.theme();
      view.querySelector('[data-theme-box]').innerHTML = '<div class="ui-seg">' + [['auto', 'Auto'], ['light', 'Light'], ['dark', 'Dark']].map(function (o) {
        return '<button type="button" data-theme-pick="' + o[0] + '" class="' + (t === o[0] ? 'on' : '') + '">' + o[1] + '</button>';
      }).join('') + '</div>';
    }
    themeBox();
    function dossier(d) {
      var me = d.me;
      view.querySelector('[data-dossier]').innerHTML = '<div class="pf-dossier"><div class="pf-id">' + OS.shield(me.level) + '<div class="rk">' + esc(me.rank) + '</div>' +
        '<div class="xp">' + me.xp + ' XP' + (me.next ? ' · ' + me.to_next + ' to ' + esc(me.next) : '') + '</div><div class="os-bar"><i style="width:' + me.pct + '%"></i></div>' +
        '<div class="xp" style="margin:12px 0 0">' + UI.plural(d.streak, 'day') + ' on duty' + (d.board.my_place ? ' · #' + d.board.my_place + ' in the Bureau' : '') + '</div></div>' +
        '<div class="ui-card"><h3>Service record</h3><div class="pf-grid" style="grid-template-columns:1fr 1.4fr;gap:18px"><ol class="pf-ladder">' + d.ranks.map(function (r) {
          return '<li class="' + (r.name === me.rank ? 'now' : me.xp >= r.xp ? 'got' : '') + '"><span>' + esc(r.name) + '</span><span>' + r.xp + '</span></li>';
        }).join('') + '</ol><div><div class="pf-stats">' +
          '<span class="ui-stat"><b>' + d.lessons_done + '/' + d.lessons_total + '</b><span>lessons passed</span></span>' +
          '<span class="ui-stat"><b>' + d.perfect + '</b><span>perfect quizzes</span></span>' +
          '<span class="ui-stat"><b>' + d.cases_solved + '/' + d.cases_total + '</b><span>cases closed</span></span>' +
          '<span class="ui-stat"><b>' + (d.best_case || '–') + '</b><span>best case score</span></span>' +
          '<span class="ui-stat"><b>' + d.investigations + '</b><span>investigations</span></span></div>' +
          '<label class="ui-check" style="margin-top:16px"><input type="checkbox" data-hide' + (d.board_hidden ? ' checked' : '') + '><span><b>Stay in the shadows</b><br><span class="small muted">Hide me from the Bureau leaderboard.</span></span></label></div></div></div></div>' +
        '<div class="ui-card" style="margin-bottom:16px"><h3>Commendations</h3><div class="pf-badges">' + d.badges.map(function (b) {
          return '<div class="' + (b.earned ? '' : 'off') + '"><span class="os-badge-ic' + (b.earned ? ' on' : '') + '">' + UI.icon(b.icon) + '</span><span><b>' + esc(b.name) + '</b><span class="muted">' + esc(b.how) + '</span></span></div>';
        }).join('') + '</div></div>';
    }
    var ready = UI.api('get_dossier').then(dossier);
    view.addEventListener('change', function (e) {
      if (!e.target.matches('[data-hide]')) return;
      var box = e.target;
      UI.api('set_board_hidden', box.checked).then(function (r) { UI.toast(r.board_hidden ? "You're off the leaderboard." : "You're back on the leaderboard.", 'ok'); },
        function (err) { box.checked = !box.checked; UI.toast(err.message, 'error'); });
    });
    view.addEventListener('click', function (e) {
      var t = e.target.closest('[data-theme-pick]');
      if (t) { UI.setTheme(t.getAttribute('data-theme-pick')); themeBox(); UI.renderChrome(); return; }
      if (e.target.closest('[data-reset]')) {
        UI.busy(e.target.closest('[data-reset]'), UI.auth('reset', { email: me.email })).then(function (r) { UI.toast(r.message, 'ok'); });
      }
      if (e.target.closest('[data-signout-here]')) UI.auth('logout');
    });
    view.querySelector('[data-name]').addEventListener('submit', function (e) {
      e.preventDefault();
      var v = UI.formData(e.target);
      UI.busy(e.target.querySelector('[type=submit]'), UI.api('update_profile', v.name)).then(function (r) {
        UI.setMe(r.me); ctx.me = r.me; UI.toast('Saved', 'ok');
        view.querySelector('.pf-head h1').textContent = r.me.name;
      });
    });
    return ready;
  });
})();
