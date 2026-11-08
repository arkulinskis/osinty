/* os-kit.js: Osinty's drawing engines, reached from Python through window.OS (client_code/os_kit.py wraps them).
   The pages, lists and dialogs are Python Forms; only what draws or reads bytes lives here:
     OS.shield(level)              the rank badge (SVG text; Components/Shield shows it)
     OS.xpPop(n)                   the "+30 XP" rubber stamp that slams onto the page
     OS.board(el, data, hooks)     the corkboard: pins you drag, red strings, labels you click (Components/Corkboard)
     OS.exif(file, done)           reads a JPEG's EXIF metadata in the browser (Gadgets/ExifReader)
     OS.copy(text, ok, fail)       copy to the clipboard */
(function () {
  'use strict';
  var OS = window.OS = window.OS || {};
  function esc(s) { return window.UI && UI.esc ? UI.esc(s) : String(s == null ? '' : s); }
  function icon(n) { return window.UI && UI.icon ? UI.icon(n) : ''; }

  /* ------------------------------------------------------------------ rank badge */
  var RANK_COLORS = ['#8a7d69', '#7a5a3a', '#5d6f4a', '#3f6a7a', '#8f1d21', '#a8761f', '#c9a227'];
  OS.shield = function (level, cls) {
    var c = RANK_COLORS[Math.max(0, Math.min(RANK_COLORS.length - 1, (level || 1) - 1))];
    var stars = '', n = Math.min(level || 1, 7);
    for (var i = 0; i < n; i++) {
      var x = 32 - (n - 1) * 4.5 + i * 9;
      stars += '<path transform="translate(' + x + ' 52) scale(.45)" d="M0-9 2.6-2.8 9.4-2.8 3.9 1.3 6 7.9 0 4 -6 7.9 -3.9 1.3 -9.4-2.8 -2.6-2.8z" fill="#f6ecd6"/>';
    }
    return '<svg class="shield ' + (cls || '') + '" viewBox="0 0 64 72" aria-hidden="true"><path d="M32 3 58 12v20c0 18-11 31-26 37C17 63 6 50 6 32V12z" fill="' + c + '" stroke="#1d1714" stroke-opacity=".35" stroke-width="2"/>' +
      '<path d="M32 9 52 16v16c0 14-8.5 24.5-20 29.5C20.5 56.5 12 46 12 32V16z" fill="none" stroke="#f6ecd6" stroke-opacity=".55" stroke-width="1.6"/>' +
      '<g transform="translate(32 30)" fill="none" stroke="#f6ecd6" stroke-width="3.2" stroke-linecap="round"><circle cx="-2" cy="-2" r="8"/><path d="M4 4l7 7"/></g>' + stars + '</svg>';
  };

  /* ------------------------------------------------------------------ XP stamp */
  OS.xpPop = function (n) {
    var pop = document.createElement('div');
    pop.className = 'ui os-xp-pop';
    pop.setAttribute('aria-hidden', 'true');
    pop.textContent = '+' + n + ' XP';
    document.body.appendChild(pop);
    setTimeout(function () { pop.remove(); }, 2200);
  };

  /* lower case, accents dropped (José -> jose): the gadgets' name folding */
  OS.fold = function (s) { return String(s == null ? '' : s).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, ''); };

  /* ------------------------------------------------------------------ clipboard */
  OS.copy = function (text, ok, fail) {
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(function () { ok && ok(); }, function () { fail && fail(); });
    else if (fail) fail();
  };

  /* ------------------------------------------------------------------ corkboard
     data = {w, h, leads: [{id, kind, value, note, grade, x, y, icon, label}], links: [{id, a, b, label}], selected, connect}
     hooks = {click(lead_id), move(lead_id, x, y), cut(link_id)}. Returns {update(data), destroy()}. */
  OS.board = function (el, data, hooks) {
    var D = data, drag = null;
    el.innerHTML = '';
    var canvas = document.createElement('div');
    canvas.className = 'cb-canvas';
    el.appendChild(canvas);
    function pinById(id) { for (var i = 0; i < D.leads.length; i++) if (D.leads[i].id === id) return D.leads[i]; return null; }
    function draw() {
      canvas.style.width = D.w + 'px'; canvas.style.height = D.h + 'px';
      canvas.innerHTML = '<svg class="cb-svg" width="' + D.w + '" height="' + D.h + '"></svg>' + D.leads.map(function (l, i) {
        return '<div class="cb-pin kind-' + esc(l.kind) + (D.selected === l.id ? ' sel' : '') + '" data-pin="' + esc(l.id) + '" role="button" tabindex="0" ' +
          'aria-label="' + esc(l.label + ': ' + l.value) + '" style="left:' + l.x + 'px;top:' + l.y + 'px;--r:' + (((i * 37) % 7) - 3) * 0.6 + 'deg">' +
          '<div class="k"><span class="kn">' + icon(l.icon) + esc(l.label) + '</span>' + (l.grade ? '<span class="g">' + esc(l.grade) + '</span>' : '') + '</div>' +
          '<div class="v">' + esc(l.value) + '</div>' + (l.note ? '<div class="n">' + esc(l.note) + '</div>' : '') + '</div>';
      }).join('');
      strings();
    }
    function strings() {
      var svg = canvas.querySelector('.cb-svg');
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
    function down(e) {
      var pin = e.target.closest('.cb-pin');
      if (!pin || e.button > 0) return;
      var l = pinById(pin.getAttribute('data-pin'));
      drag = { pin: pin, lead: l, sx: e.clientX, sy: e.clientY, ox: l.x, oy: l.y, moved: false, id: e.pointerId };
      pin.setPointerCapture(e.pointerId);
    }
    function move(e) {
      if (!drag || e.pointerId !== drag.id) return;
      var dx = e.clientX - drag.sx, dy = e.clientY - drag.sy;
      if (!drag.moved && Math.abs(dx) + Math.abs(dy) < 5) return;
      drag.moved = true;
      drag.pin.classList.add('dragging');
      drag.lead.x = Math.max(0, Math.min(D.w - 180, Math.round(drag.ox + dx)));
      drag.lead.y = Math.max(0, Math.min(D.h - 90, Math.round(drag.oy + dy)));
      drag.pin.style.left = drag.lead.x + 'px'; drag.pin.style.top = drag.lead.y + 'px';
      strings();
    }
    function up(e) {
      if (!drag || e.pointerId !== drag.id) return;
      var d = drag; drag = null;
      d.pin.classList.remove('dragging');
      if (d.moved) hooks.move(d.lead.id, d.lead.x, d.lead.y);
      else hooks.click(d.lead.id);
    }
    function cancel(e) { if (drag && e.pointerId === drag.id) { drag.pin.classList.remove('dragging'); drag = null; } }
    function key(e) { var p = e.target.closest('.cb-pin'); if (p && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); hooks.click(p.getAttribute('data-pin')); } }
    function click(e) { var g = e.target.closest('[data-link]'); if (g) hooks.cut(g.getAttribute('data-link')); }
    el.addEventListener('pointerdown', down);
    el.addEventListener('pointermove', move);
    el.addEventListener('pointerup', up);
    el.addEventListener('pointercancel', cancel);
    el.addEventListener('keydown', key);
    el.addEventListener('click', click);
    draw();
    return {
      update: function (d) { D = d; draw(); },
      destroy: function () {
        ['pointerdown', 'pointermove', 'pointerup', 'pointercancel', 'keydown', 'click'].forEach(function (t, i) {
          el.removeEventListener(t, [down, move, up, cancel, key, click][i]);
        });
        el.innerHTML = '';
      }
    };
  };

  /* ------------------------------------------------------------------ EXIF reader (JPEG APP1, first 512 KB) */
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
    function dms(a, ref) { if (!a || a.length < 3) return null; var d = a[0] + a[1] / 60 + a[2] / 3600; return (ref === 'S' || ref === 'W') ? -d : d; }
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
      var lat = dms(gp[2], gp[1]), lon = dms(gp[4], gp[3]);
      if (lat != null && lon != null && !(lat === 0 && lon === 0)) gps = { lat: lat, lon: lon, alt: typeof gp[6] === 'number' ? gp[6] : null };
    }
    return { fields: fields, gps: gps };
  }
  /* done(JSON text) with {name, kb, url, error?, rows: [[label, text]], gps?: {lat, lon, alt}} */
  OS.exif = function (file, done) {
    var url = URL.createObjectURL(file), fr = new FileReader();
    fr.onload = function () {
      var out;
      try { out = parseExif(fr.result); } catch (err) { out = { error: 'This file\'s metadata couldn\'t be read.' }; }
      var rows = (out.fields || []).map(function (r) { return [r[0], Array.isArray(r[1]) ? r[1].join(', ') : String(r[1])]; });
      done(JSON.stringify({ name: file.name, kb: Math.round(file.size / 1024), url: url, error: out.error || null, rows: rows,
        gps: out.gps ? { lat: out.gps.lat.toFixed(6), lon: out.gps.lon.toFixed(6), alt: out.gps.alt == null ? null : Math.round(out.gps.alt) } : null }));
    };
    fr.readAsArrayBuffer(file.slice(0, 512 * 1024));
    return url;
  };
})();
