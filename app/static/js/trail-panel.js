/* Dashboard panel for the opt-in 6-hour location trail (same data as the report form). */
(function () {
  var list = document.getElementById('trail-list'), opt = document.getElementById('trail-opt'), clr = document.getElementById('trail-clear');
  if (!list || !opt || document.getElementById('loc-status')) return;
  var csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
  function esc(t) { var d = document.createElement('div'); d.textContent = t == null ? '' : String(t); return d.innerHTML; }
  function fmt(iso) { try { return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); } catch (e) { return ''; } }
  function load() {
    fetch('/items/api/trail', { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
      if (!d || !d.stops.length) { list.innerHTML = '<p class="muted">Nothing remembered yet. Tick the box to start.</p>'; if (clr) clr.hidden = true; return; }
      if (clr) clr.hidden = false;
      list.innerHTML = '<ul class="trail-ul">' + d.stops.map(function (s) {
        return '<li><div><strong>' + esc(s.place) + '</strong>' + (s.risk === 'high' ? ' <span class="pill fail">high risk</span>' : '') + '<br><small>' + fmt(s.from) + (s.to !== s.from ? ' – ' + fmt(s.to) : '') + '</small></div></li>';
      }).join('') + '</ul>';
    }).catch(function () { list.innerHTML = ''; });
  }
  opt.checked = !!(window.FindoraTrail && window.FindoraTrail.enabled());
  opt.addEventListener('change', function () { if (window.FindoraTrail) window.FindoraTrail.set(opt.checked); setTimeout(load, 1500); });
  if (clr) clr.addEventListener('click', function () { fetch('/items/api/trail/clear', { method: 'POST', credentials: 'same-origin', headers: { 'X-CSRFToken': csrf } }).then(load); });
  load();
})();
