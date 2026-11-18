/* FINDORA front-end: theme switcher, mobile nav, toasts. No framework needed. */
(function () {
  'use strict';
  var root = document.documentElement;
  function setTheme(theme) {
    root.setAttribute('data-theme', theme);
    try { localStorage.setItem('findora-theme', theme); } catch (e) {}
    document.querySelectorAll('.swatch').forEach(function (s) { s.classList.toggle('active', s.dataset.theme === theme); });
  }
  var toggleBtn = document.getElementById('theme-toggle-btn');
  var menu = document.getElementById('theme-menu');
  if (toggleBtn && menu) {
    toggleBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = menu.classList.toggle('open');
      toggleBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.addEventListener('click', function (e) { if (!menu.contains(e.target)) menu.classList.remove('open'); });
    document.querySelectorAll('.swatch').forEach(function (b) { b.addEventListener('click', function () { setTheme(b.dataset.theme); }); });
  }
  setTheme(root.getAttribute('data-theme') || 'dark');
  var hamburger = document.getElementById('hamburger');
  if (hamburger) hamburger.addEventListener('click', function () {
    var host = document.querySelector('.topbar-inner') || document.body;
    host.classList.toggle('nav-open'); document.body.classList.toggle('side-open');
  });
  document.querySelectorAll('.alert-close').forEach(function (btn) { btn.addEventListener('click', function () { btn.closest('.alert').remove(); }); });
  setTimeout(function () {
    document.querySelectorAll('.toast-stack .alert').forEach(function (a) { a.classList.add('fade-out'); setTimeout(function () { a.remove(); }, 500); });
  }, 6000);

  /* Opt-in "last 6 hours" location trail (stored server-side for the signed-in user only, auto-deleted). */
  var auth = document.body.getAttribute('data-auth') === '1';
  var meta = document.querySelector('meta[name="csrf-token"]');
  var csrf = meta ? meta.getAttribute('content') : '';
  window.FindoraTrail = {
    csrf: csrf,
    enabled: function () { try { return localStorage.getItem('findora-trail') === 'on'; } catch (e) { return false; } },
    set: function (on) { try { localStorage.setItem('findora-trail', on ? 'on' : 'off'); } catch (e) {} if (on) this.ping(); },
    ping: function (cb) {
      if (!auth || !navigator.geolocation) return;
      navigator.geolocation.getCurrentPosition(function (pos) {
        fetch('/items/api/ping', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
          body: JSON.stringify({ lat: pos.coords.latitude, lng: pos.coords.longitude, accuracy: pos.coords.accuracy }) })
          .then(function (r) { return r.json(); }).then(function (d) { if (cb) cb(d); }).catch(function () {});
      }, function () {}, { enableHighAccuracy: false, timeout: 10000, maximumAge: 120000 });
    }
  };
  if (auth && window.FindoraTrail.enabled()) {
    window.FindoraTrail.ping();
    setInterval(function () { if (document.visibilityState === 'visible') window.FindoraTrail.ping(); }, 5 * 60 * 1000);
  }
})();
