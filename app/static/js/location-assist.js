/* FINDORA - Smart location assist (report form)
   1. Shows written HIGH-RISK suggestions + a colour-coded map (aggregated, anonymous counts).
   2. Detects the reporter's GPS position (browser permission required), stores it WITH the report
      (hidden fields detected_lat / detected_lng) and pre-selects the nearest campus location.
   3. Optional "last 6 hours" trail: remembers where you were so you can recall where something went
      missing. Only the signed-in user can read it and old points are deleted automatically.
   GPS capture does NOT depend on the map library, so saving the location still works offline/blocked. */
(function () {
  var statusEl = document.getElementById('loc-status');
  if (!statusEl) return;
  var select = document.getElementById('location_id');
  var hLat = document.getElementById('detected_lat'), hLng = document.getElementById('detected_lng');
  var riskBox = document.getElementById('risk-box'), savedEl = document.getElementById('loc-saved');
  var trailList = document.getElementById('trail-list'), trailOpt = document.getElementById('trail-opt'), trailClear = document.getElementById('trail-clear');
  var mapEl = document.getElementById('smart-location-map');
  var csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
  var COLORS = { high: '#ef4444', medium: '#f59e0b', low: '#22c55e' };
  var map = null, circles = [], meMarker = null;

  function esc(t) { var d = document.createElement('div'); d.textContent = t == null ? '' : String(t); return d.innerHTML; }
  function setStatus(html, spin) { statusEl.innerHTML = (spin ? '<span class="spinner"></span>' : '') + '<span>' + html + '</span>'; }
  function getJSON(url, opts) { return fetch(url, Object.assign({ credentials: 'same-origin' }, opts || {})).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }); }
  function fmtTime(iso) { try { return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); } catch (e) { return ''; } }

  // ---- map (optional) ----
  if (mapEl && typeof L !== 'undefined') {
    try {
      map = L.map(mapEl).setView([29.016, 77.674], 16);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; OpenStreetMap contributors' }).addTo(map);
    } catch (e) { map = null; }
  }
  if (!map && mapEl) { mapEl.style.height = 'auto'; mapEl.innerHTML = '<div class="empty">The map could not be loaded (no internet?). Location detection and saving still work.</div>'; }

  function renderCircles(rows) {
    if (!map) return;
    circles.forEach(function (c) { map.removeLayer(c); }); circles = [];
    var pts = [];
    rows.forEach(function (r) {
      var col = COLORS[r.risk] || COLORS.low;
      var c = L.circle([r.lat, r.lng], { radius: 70 + Math.min(r.lost_count, 20) * 14, color: col, fillColor: col, fillOpacity: r.recent_count > 0 ? 0.55 : 0.28, weight: r.recent_count > 0 ? 3 : 1.5, dashArray: r.recent_count > 0 ? '4,4' : null }).addTo(map);
      c.bindPopup('<strong>' + esc(r.name) + '</strong><br>' + esc(r.tip) + (r.recent_count > 0 ? '<br><strong style="color:#ef4444">' + r.recent_count + ' report(s) in the last 6 hours</strong>' : ''));
      circles.push(c); pts.push([r.lat, r.lng]);
    });
    if (pts.length && !meMarker) map.fitBounds(pts, { padding: [30, 30], maxZoom: 17 });
  }

  function renderRisk(data) {
    if (!riskBox || !data) return;
    var html = '';
    if (data.nearest) {
      html += '<div class="risk-now level-' + data.nearest.risk + '"><strong>You are near ' + esc(data.nearest.name) + '</strong> &mdash; ' + esc(data.nearest.tip) + '</div>';
    }
    html += '<div class="risk-list"><strong><i class="bi bi-exclamation-triangle"></i> Where items go missing most often</strong>';
    if (data.suggestions && data.suggestions.length) {
      html += '<ul>' + data.suggestions.map(function (s) {
        return '<li class="risk-item ' + s.risk + '"><span class="dot"></span><span><strong>' + esc(s.name) + '</strong> &middot; ' + s.lost_count + ' lost report(s)' + (s.peak_window ? ' &middot; busiest ' + esc(s.peak_window) : '') + (s.recent_count ? ' &middot; <em>' + s.recent_count + ' in the last 6 h</em>' : '') + '</span></li>';
      }).join('') + '</ul>';
    } else { html += '<p class="muted">No high-risk spots yet — not enough reports.</p>'; }
    riskBox.innerHTML = html + '</div>'; riskBox.hidden = false;
  }

  function loadMap(lat, lng) {
    var url = '/items/api/map-data' + (lat != null ? '?lat=' + lat + '&lng=' + lng : '');
    return getJSON(url).then(function (d) { if (d) { renderCircles(d.locations || []); renderRisk(d); } return d; });
  }

  function selectLocation(id) {
    if (!select || !id) return;
    for (var i = 0; i < select.options.length; i++) {
      if (String(select.options[i].value) === String(id)) { select.selectedIndex = i; select.dispatchEvent(new Event('change')); return; }
    }
  }

  // ---- 6-hour trail ----
  function loadTrail() {
    if (!trailList) return;
    getJSON('/items/api/trail').then(function (d) {
      if (!d) { trailList.innerHTML = ''; return; }
      if (!d.stops.length) { trailList.innerHTML = '<p class="muted">Nothing remembered yet. Tick the box above to start remembering where you are.</p>'; if (trailClear) trailClear.hidden = true; return; }
      if (trailClear) trailClear.hidden = false;
      trailList.innerHTML = '<p class="muted">Where you were in the last ' + d.hours + ' hours (newest first):</p><ul class="trail-ul">' + d.stops.map(function (s) {
        var when = fmtTime(s.from) + (s.to !== s.from ? ' – ' + fmtTime(s.to) : '');
        return '<li><div><strong>' + esc(s.place) + '</strong>' + (s.risk === 'high' ? ' <span class="pill fail">high risk</span>' : s.risk === 'medium' ? ' <span class="pill muted">medium risk</span>' : '') + '<br><small>' + when + '</small></div>' +
          (s.location_id ? '<button type="button" class="btn ghost small use-place" data-id="' + s.location_id + '">Use this place</button>' : '') + '</li>';
      }).join('') + '</ul>';
      Array.prototype.forEach.call(trailList.querySelectorAll('.use-place'), function (b) { b.addEventListener('click', function () { selectLocation(b.getAttribute('data-id')); }); });
    });
  }
  if (trailOpt) {
    trailOpt.checked = !!(window.FindoraTrail && window.FindoraTrail.enabled());
    trailOpt.addEventListener('change', function () {
      if (window.FindoraTrail) window.FindoraTrail.set(trailOpt.checked);
      setTimeout(loadTrail, 1500);
    });
  }
  if (trailClear) trailClear.addEventListener('click', function () {
    getJSON('/items/api/trail/clear', { method: 'POST', headers: { 'X-CSRFToken': csrf } }).then(loadTrail);
  });

  // ---- device position ----
  function onPosition(pos) {
    var lat = pos.coords.latitude, lng = pos.coords.longitude, acc = Math.round(pos.coords.accuracy || 0);
    if (hLat && hLng) { hLat.value = lat.toFixed(6); hLng.value = lng.toFixed(6); }
    if (savedEl) savedEl.innerHTML = '<i class="bi bi-check-circle"></i> Your device position (' + lat.toFixed(5) + ', ' + lng.toFixed(5) + (acc ? ', ±' + acc + ' m' : '') + ') will be saved with this report and shown under “My past locations”.';
    if (map) {
      if (meMarker) map.removeLayer(meMarker);
      meMarker = L.circleMarker([lat, lng], { radius: 9, color: '#fff', weight: 3, fillColor: '#3b82f6', fillOpacity: 0.95 }).addTo(map).bindPopup('You (approximate)');
    }
    loadMap(lat, lng).then(function (d) {
      if (map) { if (meMarker) meMarker.addTo(map); map.setView([lat, lng], 17); }
      if (d && d.nearest) {
        selectLocation(d.nearest.id);
        setStatus('📍 Detected — closest campus spot is <strong>' + esc(d.nearest.name) + '</strong> (' + Math.round(d.nearest_distance_km * 1000) + ' m away). It is pre-selected below; change it if that is wrong.', false);
      } else {
        setStatus('📍 Position detected and saved, but no known campus location is close — please choose one below.', false);
      }
    });
    if (window.FindoraTrail && window.FindoraTrail.enabled()) window.FindoraTrail.ping(function () { loadTrail(); });
  }
  function onError(err) {
    var msg = err && err.code === 1 ? 'Location permission was denied. Allow location for this site in your browser, then press “Try again”.'
      : err && err.code === 3 ? 'Detecting your location timed out. Press “Try again”.'
      : 'Your device could not provide a position.';
    setStatus(msg + ' You can still choose the location manually below. <button type="button" class="btn ghost small" id="loc-retry">Try again</button>', false);
    var r = document.getElementById('loc-retry'); if (r) r.addEventListener('click', detect);
  }
  function detect() {
    if (!navigator.geolocation) { setStatus('This browser cannot detect location — choose it manually below.', false); return; }
    if (window.isSecureContext === false) { setStatus('Location only works on <strong>http://127.0.0.1:5000</strong>, <strong>localhost</strong> or HTTPS. Open the site with one of those addresses (not a LAN IP).', false); return; }
    setStatus('Asking your device for its location…', true);
    navigator.geolocation.getCurrentPosition(onPosition, onError, { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 });
  }

  loadMap().then(function (d) { if (!d) setStatus('Could not load the campus risk data right now — you can still pick a location manually.', false); });
  loadTrail();
  detect();
})();
