/* ==========================================================================
   ARES-OS Mission Control
   Mars science atlas, aqueous-mineral overlays, 30-degree slope hazards,
   live Mars chronometry, and cooperative scout/follower path planning.
   Loaded after the main inline explorer script, so its top-level bindings
   (scene, camera, renderer, flyToCoordinate, ...) are available here.
   ========================================================================== */
/* global THREE, scene, camera, renderer, controls, marsGlobe, markersGroup,
   MARS_RADIUS, latLonToVector3, vector3ToLatLon, flyToCoordinate,
   getLandmarkZoomDist, DEFAULT_LANDING_SITES, renderLandingSiteMarkers,
   renderDrawerLandings, create3DLandmarks, appMode, flatCanvas, flatImg,
   flatZoom, flatPanX, flatPanY, draw2DFlat, computeLiveMarsEphemeris */
(function () {
  'use strict';

  var ARES = {
    ready: false,
    el: {},
    state: {
      atlas: { missions: [], landmarks: [], figures: {}, filter: 'missions', query: '', expanded: {} },
      index: new Map(),
      minerals: { classes: {}, sites: [], active: new Set(), showSites: true, drape: true, opacity: 0.62, ode: null },
      terrain: {
        grid: null, center: null, exaggeration: 1.2, opacity: 0.58,
        filters: { brightness: 100, contrast: 100, saturate: 100 },
        mesh: null, busy: false
      },
      scout: { result: null, iteration: 0, playing: false, timer: null, picking: null, hazards: true, busy: false },
      time: {
        baseReal: Date.now(), baseMsd: 0, baseLs: 0, eot: 0,
        subsolar: { lat: 0, lon: 0 }, rovers: {}, payload: null,
        cursorLon: null, cursorLat: null, fetched: 0, fallback: false
      },
      gds: { jobs: [], timer: null, submitting: false },
      layers: {}, hoverGroups: {}, footprints: []
    }
  };

  var COLOR = {
    safe: '#22c55e', caution: '#f59e0b', noGo: '#ef4444',
    cyan: '#38bdf8', green: '#22c55e', amber: '#fbbf24', violet: '#a78bfa',
    orange: '#ff6b3d', magenta: '#f472b6'
  };

  var INSTRUMENT_COLORS = { CRISM: '#a78bfa', OMEGA: '#38bdf8', HiRISE: '#f472b6', CTX: '#fbbf24' };

  /* ------------------------------------------------------------------------
     Small utilities
     ------------------------------------------------------------------------ */
  function $(id) { return document.getElementById(id); }
  function esc(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  function escAttr(value) { return esc(value).replace(/`/g, '&#96;'); }
  function normName(value) {
    return String(value == null ? '' : value)
      .toLowerCase()
      .replace(/\([^)]*\)/g, ' ')
      .replace(/[^a-z0-9]+/g, ' ')
      .trim();
  }
  function signedLon(lon) {
    var x = Number(lon) || 0;
    while (x > 180) x -= 360;
    while (x < -180) x += 360;
    return x;
  }
  function eastLon(lon) {
    var x = Number(lon) || 0;
    x = ((x % 360) + 360) % 360;
    return x;
  }
  function coordText(lat, lon, lonEast) {
    var la = Number(lat) || 0;
    var lo = (lonEast == null) ? eastLon(lon) : Number(lonEast);
    var ns = la >= 0 ? 'N' : 'S';
    var ew = 'E';
    return Math.abs(la).toFixed(3) + '\u00b0' + ns + ', ' + Math.abs(lo).toFixed(3) + '\u00b0' + ew;
  }
  function fmtHMS(hours) {
    if (!isFinite(hours)) return '--:--:--';
    var h = ((hours % 24) + 24) % 24;
    var total = Math.floor(h * 3600 + 0.5);
    var hh = Math.floor(total / 3600) % 24;
    var mm = Math.floor(total / 60) % 60;
    var ss = total % 60;
    return pad2(hh) + ':' + pad2(mm) + ':' + pad2(ss);
  }
  function pad2(n) { return (n < 10 ? '0' : '') + n; }
  function fmtCoord(lat, lon) {
    var ns = lat >= 0 ? 'N' : 'S';
    var ew = lon >= 0 ? 'E' : 'W';
    return Math.abs(lat).toFixed(2) + '\u00b0' + ns + ' ' + Math.abs(lon).toFixed(2) + '\u00b0' + ew;
  }
  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
  function hexToRgba(hex, alpha) {
    var h = String(hex || '#38bdf8').replace('#', '');
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    var n = parseInt(h, 16);
    if (!isFinite(n)) return 'rgba(56,189,248,' + alpha + ')';
    return 'rgba(' + ((n >> 16) & 255) + ',' + ((n >> 8) & 255) + ',' + (n & 255) + ',' + alpha + ')';
  }
  function setText(id, text) {
    var node = $(id);
    if (node) node.textContent = text;
  }
  function seasonFromLs(ls) {
    var x = ((Number(ls) || 0) % 360 + 360) % 360;
    if (x < 90) return 'Northern Spring';
    if (x < 180) return 'Northern Summer';
    if (x < 270) return 'Northern Autumn';
    return 'Northern Winter';
  }
  function statusClass(status) {
    var s = String(status || '').toLowerCase();
    if (s === 'active') return 'active';
    if (s === 'failed') return 'failed';
    if (s === 'proposed') return 'proposed';
    return 'completed';
  }
  function statusColor(status) {
    var s = String(status || '').toLowerCase();
    if (s === 'active') return COLOR.green;
    if (s === 'failed') return COLOR.noGo;
    if (s === 'proposed') return COLOR.cyan;
    return '#94a3b8';
  }
  function yearOf(value) {
    var m = String(value || '').match(/\b(19|20)\d{2}\b/);
    return m ? parseInt(m[0], 10) : null;
  }

  var toastTimer = null;
  function toast(message, isError) {
    var node = $('ares-toast');
    if (!node) return;
    node.textContent = message;
    node.className = isError ? 'error show' : 'show';
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { node.className = ''; }, isError ? 5200 : 3200);
  }

  async function fetchJSON(url, options, timeoutMs) {
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, timeoutMs || 120000);
    try {
      var opts = Object.assign({ cache: 'no-store' }, options || {});
      if (!opts.cache) opts.cache = 'no-store';
      opts.signal = controller.signal;
      var response = await fetch(url, opts);
      if (!response.ok) {
        var body = '';
        try { body = await response.text(); } catch (err) { body = ''; }
        throw new Error('HTTP ' + response.status + (body ? ': ' + body.slice(0, 180) : ''));
      }
      return await response.json();
    } finally {
      clearTimeout(timer);
    }
  }

  function disposeObject(obj) {
    if (!obj) return;
    if (obj.geometry && obj.geometry.dispose) obj.geometry.dispose();
    if (obj.material) {
      var mats = Array.isArray(obj.material) ? obj.material : [obj.material];
      mats.forEach(function (m) { if (m && m.dispose) m.dispose(); });
    }
    if (obj.children) obj.children.slice().forEach(disposeObject);
  }
  function clearGroup(group) {
    if (!group) return;
    while (group.children.length) {
      var child = group.children[0];
      group.remove(child);
      disposeObject(child);
    }
  }

  /* ------------------------------------------------------------------------
     Boot
     ------------------------------------------------------------------------ */
  function whenReady() {
    if (typeof THREE === 'undefined' || typeof scene === 'undefined' || typeof camera === 'undefined' || !document.body) {
      setTimeout(whenReady, 120);
      return;
    }
    if (ARES.ready) return;
    ARES.ready = true;
    init();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', whenReady);
  } else {
    whenReady();
  }

  function init() {
    injectUI();
    cacheElements();
    initLayers();
    patchExplorerHooks();
    startLandmarkPinScaling();
    bindPanel();
    bindAtlas();
    bindMinerals();
    bindTerrain();
    bindScout();
    bindGds();
    bindPicking();
    bindCursor();
    bindTooltipActions();
    applyVisualFilters();
    startClock();
    loadAll();
    window.addEventListener('resize', function () {
      if (ARES.state.scout.result && $('#ares-section-scout') && $('#ares-section-scout').classList.contains('active')) {
        drawScoutCharts();
      }
    });
    if (window.innerWidth < 900) setPanel(false);
  }

  /* ------------------------------------------------------------------------
     DOM injection
     ------------------------------------------------------------------------ */
  function injectUI() {
    var html = '' +
      '<div id="ares-chronometer" aria-label="Live Mars chronometer">' +
        '<div class="ares-chron-cell ares-clock-mars ares-live">' +
          '<div class="ares-chron-label">MTC</div>' +
          '<div class="ares-chron-value" id="ares-mtc">--:--:--</div>' +
          '<div class="ares-chron-sub" id="ares-msd">MSD --</div>' +
        '</div>' +
        '<div class="ares-chron-cell">' +
          '<div class="ares-chron-label">Ls / Season</div>' +
          '<div class="ares-chron-value" id="ares-ls">Ls --</div>' +
          '<div class="ares-chron-sub" id="ares-season">--</div>' +
        '</div>' +
        '<div class="ares-chron-cell">' +
          '<div class="ares-chron-label">Perseverance</div>' +
          '<div class="ares-chron-value" id="ares-persev-time">--:--:--</div>' +
          '<div class="ares-chron-sub" id="ares-persev-sub">Sol --</div>' +
        '</div>' +
        '<div class="ares-chron-cell">' +
          '<div class="ares-chron-label">Curiosity</div>' +
          '<div class="ares-chron-value" id="ares-curio-time">--:--:--</div>' +
          '<div class="ares-chron-sub" id="ares-curio-sub">Sol --</div>' +
        '</div>' +
        '<div class="ares-chron-cell ares-clock-accent">' +
          '<div class="ares-chron-label">Cursor LST</div>' +
          '<div class="ares-chron-value" id="ares-cursor-time">--:--:--</div>' +
          '<div class="ares-chron-sub" id="ares-cursor-sub">Move over the globe</div>' +
        '</div>' +
        '<div class="ares-chron-cell ares-chron-earth">' +
          '<div class="ares-chron-label">Earth UTC</div>' +
          '<div class="ares-chron-value" id="ares-earth-utc">--:--:--</div>' +
          '<div class="ares-chron-sub" id="ares-earth-date">----</div>' +
        '</div>' +
      '</div>' +

      '<button id="ares-panel-toggle" type="button" title="Open ARES-OS Mission Control">\u25c0 ARES-OS</button>' +

      '<aside id="ares-panel" aria-label="ARES-OS Mission Control">' +
        '<div class="ares-panel-head">' +
          '<div class="ares-brand-mark">A</div>' +
          '<div class="ares-brand-text"><strong>ARES-OS MISSION CONTROL</strong><small>Atlas \u00b7 Minerals \u00b7 Hazards \u00b7 Autonomy</small></div>' +
          '<div class="ares-spacer"></div>' +
          '<button class="ares-icon-btn" id="ares-panel-close" type="button" title="Collapse panel">\u2715</button>' +
        '</div>' +
        '<div class="ares-tabs" role="tablist">' +
          '<button class="ares-tab active" type="button" data-ares-tab="atlas">Atlas</button>' +
          '<button class="ares-tab" type="button" data-ares-tab="minerals">Minerals</button>' +
          '<button class="ares-tab" type="button" data-ares-tab="terrain">Terrain</button>' +
          '<button class="ares-tab" type="button" data-ares-tab="scout">Scout</button>' +
          '<button class="ares-tab" type="button" data-ares-tab="clock">Clock</button>' +
        '</div>' +
        '<div class="ares-panel-body">' +

          '<section class="ares-section active" id="ares-section-atlas" data-ares-section="atlas">' +
            '<div class="ares-search"><input id="ares-atlas-search" type="search" placeholder="Search missions, namesakes, landmarks\u2026" autocomplete="off"></div>' +
            '<div class="ares-subtabs">' +
              '<button class="ares-subtab active" type="button" data-atlas-filter="missions" id="ares-filter-missions">Missions</button>' +
              '<button class="ares-subtab" type="button" data-atlas-filter="landmarks" id="ares-filter-landmarks">Landmarks</button>' +
            '</div>' +
            '<div class="ares-note" style="margin-bottom:8px">Hover any marker for the namesake biography and scientific significance. Click a card to expand its mission dossier.</div>' +
            '<div id="ares-atlas-list"><div class="ares-empty">Loading the Mars exploration registry\u2026</div></div>' +
          '</section>' +

          '<section class="ares-section" id="ares-section-minerals" data-ares-section="minerals">' +
            '<div class="ares-block">' +
              '<div class="ares-block-title">Aqueous mineral classes</div>' +
              '<div class="ares-chips" id="ares-mineral-classes"><div class="ares-note">Loading spectral classes\u2026</div></div>' +
              '<div class="ares-slider-row"><label>Drape opacity</label><input id="ares-mineral-opacity" type="range" min="0.1" max="0.95" step="0.01" value="0.62"><output id="ares-mineral-opacity-out">62%</output></div>' +
              '<div class="ares-btn-row" style="margin-top:7px">' +
                '<button class="ares-btn ares-cyan" type="button" id="ares-mineral-drape">Drape ON</button>' +
                '<button class="ares-btn" type="button" id="ares-mineral-sites">Sites ON</button>' +
              '</div>' +
            '</div>' +
            '<div class="ares-block">' +
              '<div class="ares-block-title">On-demand orbital spectroscopy</div>' +
              '<div class="ares-note">Query the NASA PDS Orbital Data Explorer for CRISM or OMEGA footprint intersections at the current camera center.</div>' +
              '<div class="ares-btn-row" style="margin-top:7px">' +
                '<button class="ares-btn" type="button" id="ares-scan-crism">Scan CRISM</button>' +
                '<button class="ares-btn" type="button" id="ares-scan-omega">Scan OMEGA</button>' +
                '<button class="ares-btn ares-small" type="button" id="ares-scan-hirise">HiRISE</button>' +
              '</div>' +
              '<div id="ares-ode-results"></div>' +
            '</div>' +
            '<div class="ares-block">' +
              '<div class="ares-block-title">Mineral target registry</div>' +
              '<div class="ares-stats" id="ares-mineral-stats"></div>' +
              '<div id="ares-mineral-list" style="margin-top:8px"></div>' +
            '</div>' +
          '</section>' +

          '<section class="ares-section" id="ares-section-terrain" data-ares-section="terrain">' +
            '<div class="ares-block">' +
              '<div class="ares-block-title">DEM slope-hazard analysis</div>' +
              '<div class="ares-grid2">' +
                '<div class="ares-field"><label>AOI size (km)</label><input id="ares-slope-size" type="number" value="3.6" min="0.5" max="12" step="0.2"></div>' +
                '<div class="ares-field"><label>DEM resolution</label><select id="ares-slope-res"><option value="20">CTX 20 m/px</option><option value="1">HiRISE 1 m/px</option></select></div>' +
              '</div>' +
              '<div class="ares-btn-row" style="margin-top:7px">' +
                '<button class="ares-btn ares-primary" type="button" id="ares-slope-run">Analyze at camera center</button>' +
                '<button class="ares-btn ares-small" type="button" id="ares-slope-jezero">Jezero</button>' +
                '<button class="ares-btn ares-small" type="button" id="ares-slope-gale">Gale</button>' +
                '<button class="ares-btn ares-danger ares-small" type="button" id="ares-slope-clear">Clear</button>' +
              '</div>' +
              '<div class="ares-legend">' +
                '<div class="ares-legend-row"><span class="ares-legend-swatch" style="background:#22c55e;color:#22c55e"></span>Safe traverse \u00b7 0\u201315\u00b0</div>' +
                '<div class="ares-legend-row"><span class="ares-legend-swatch" style="background:#f59e0b;color:#f59e0b"></span>Caution \u00b7 15\u201330\u00b0</div>' +
                '<div class="ares-legend-row"><span class="ares-legend-swatch" style="background:#ef4444;color:#ef4444"></span>No-go \u00b7 >30\u00b0</div>' +
              '</div>' +
              '<div id="ares-slope-stats"></div>' +
              '<div class="ares-chart-wrap" style="margin-top:8px"><div class="ares-chart-title"><span>Local DEM hazard map</span><span id="ares-slope-map-legend">\u2014</span></div><canvas id="ares-slope-map" height="156"></canvas></div>' +
            '</div>' +
            '<div class="ares-block">' +
              '<div class="ares-block-title">Surface visualization</div>' +
              '<div class="ares-slider-row"><label>Vertical exaggeration</label><input id="ares-slope-exag" type="range" min="0" max="4" step="0.1" value="1.2"><output id="ares-slope-exag-out">1.2\u00d7</output></div>' +
              '<div class="ares-slider-row"><label>Hazard opacity</label><input id="ares-slope-opacity" type="range" min="0.1" max="0.95" step="0.01" value="0.58"><output id="ares-slope-opacity-out">58%</output></div>' +
              '<div class="ares-slider-row"><label>Brightness</label><input id="ares-brightness" type="range" min="60" max="150" step="1" value="100"><output id="ares-brightness-out">100%</output></div>' +
              '<div class="ares-slider-row"><label>Contrast</label><input id="ares-contrast" type="range" min="60" max="160" step="1" value="100"><output id="ares-contrast-out">100%</output></div>' +
              '<div class="ares-slider-row"><label>Saturation</label><input id="ares-saturate" type="range" min="0" max="200" step="1" value="100"><output id="ares-saturate-out">100%</output></div>' +
            '</div>' +
            '<div class="ares-block">' +
              '<div class="ares-block-title">NASA PDS Geosciences Node \u00b7 MOLA profile</div>' +
              '<div class="ares-note">Submit an asynchronous MOLA PEDR point query for the current AOI. Results are produced by the PDS GDS and may take 10\u201330 seconds.</div>' +
              '<div class="ares-btn-row" style="margin-top:7px">' +
                '<button class="ares-btn ares-cyan" type="button" id="ares-gds-submit">Submit MOLA query</button>' +
                '<button class="ares-btn ares-small" type="button" id="ares-gds-refresh">Refresh jobs</button>' +
              '</div>' +
              '<div id="ares-gds-list"></div>' +
            '</div>' +
          '</section>' +

          '<section class="ares-section" id="ares-section-scout" data-ares-section="scout">' +
            '<div class="ares-block">' +
              '<div class="ares-block-title">Cooperative scouting IPP</div>' +
              '<div class="ares-note">The follower solves a feasible route on known terrain while the scout selects information-gain viewpoints. Feasible versus optimistic costs bound the optimality gap.</div>' +
              '<div class="ares-grid2" style="margin-top:7px">' +
                '<div class="ares-field"><label>Start latitude</label><input id="ares-start-lat" type="number" value="18.4446" step="0.0001"></div>' +
                '<div class="ares-field"><label>Start longitude</label><input id="ares-start-lon" type="number" value="77.4508" step="0.0001"></div>' +
                '<div class="ares-field"><label>Target latitude</label><input id="ares-target-lat" type="number" value="18.5100" step="0.0001"></div>' +
                '<div class="ares-field"><label>Target longitude</label><input id="ares-target-lon" type="number" value="77.3500" step="0.0001"></div>' +
              '</div>' +
              '<div class="ares-btn-row" style="margin-top:6px">' +
                '<button class="ares-btn ares-small" type="button" id="ares-pick-start">Pick start on map</button>' +
                '<button class="ares-btn ares-small" type="button" id="ares-pick-target">Pick target on map</button>' +
              '</div>' +
              '<div class="ares-grid2" style="margin-top:6px">' +
                '<div class="ares-field"><label>Sensor radius (m)</label><input id="ares-sensor-radius" type="number" value="300" min="80" max="1200" step="20"></div>' +
                '<div class="ares-field"><label>Max sorties</label><input id="ares-max-iterations" type="number" value="18" min="2" max="30" step="1"></div>' +
              '</div>' +
              '<div class="ares-btn-row" style="margin-top:7px">' +
                '<button class="ares-btn ares-primary" type="button" id="ares-scout-run">Run cooperative plan</button>' +
                '<button class="ares-btn ares-small" type="button" id="ares-scout-clear">Clear</button>' +
              '</div>' +
              '<div class="ares-btn-row" style="margin-top:5px">' +
                '<button class="ares-btn ares-small" type="button" data-ares-preset="jezero">Jezero</button>' +
                '<button class="ares-btn ares-small" type="button" data-ares-preset="gale">Gale</button>' +
                '<button class="ares-btn ares-small" type="button" data-ares-preset="mawrth">Mawrth</button>' +
                '<button class="ares-btn ares-small" type="button" data-ares-preset="long">Long traverse</button>' +
              '</div>' +
            '</div>' +
            '<div id="ares-scout-status"></div>' +
            '<div id="ares-scout-metrics"></div>' +
            '<div class="ares-chart-wrap"><div class="ares-chart-title"><span>Local AOI map</span><span id="ares-minimap-legend">\u2014</span></div><canvas id="ares-scout-minimap" height="168"></canvas></div>' +
            '<div class="ares-timeline">' +
              '<button class="ares-btn ares-small" type="button" id="ares-scout-prev">\u25c0</button>' +
              '<button class="ares-btn ares-small" type="button" id="ares-scout-play">\u25b6 Play</button>' +
              '<input id="ares-scout-slider" type="range" min="0" max="1" value="0" step="1">' +
              '<button class="ares-btn ares-small" type="button" id="ares-scout-next">\u25b6</button>' +
              '<span class="ares-step-label" id="ares-scout-step-label">0 / 0</span>' +
            '</div>' +
            '<div class="ares-chart-wrap"><div class="ares-chart-title"><span>Elevation &amp; slope profile</span><span id="ares-profile-legend">\u2014</span></div><canvas id="ares-profile-canvas" height="150"></canvas></div>' +
            '<div class="ares-chart-wrap"><div class="ares-chart-title"><span>Cost convergence &amp; optimality gap</span><span id="ares-gap-legend">\u2014</span></div><canvas id="ares-convergence-canvas" height="128"></canvas></div>' +
            '<div id="ares-scout-proof"></div>' +
            '<div class="ares-source-line" id="ares-scout-source"></div>' +
            '<label class="ares-legend-row" style="margin-top:8px;cursor:pointer"><input id="ares-scout-hazards" type="checkbox" checked style="accent-color:#ef4444"> Show no-go cells (>30\u00b0)</label>' +
          '</section>' +

          '<section class="ares-section" id="ares-section-clock" data-ares-section="clock">' +
            '<div class="ares-clock-hero"><div><div class="ares-chron-label">MTC</div><div class="big" id="ares-clock-mtc">--:--:--</div></div><div class="small" id="ares-clock-msd">MSD --</div></div>' +
            '<div class="ares-block">' +
              '<div class="ares-block-title">Mars24 chronometry</div>' +
              '<div class="ares-clock-list" id="ares-clock-details"></div>' +
            '</div>' +
            '<div class="ares-btn-row">' +
              '<button class="ares-btn ares-cyan" type="button" id="ares-clock-sync">Sync ephemeris</button>' +
              '<button class="ares-btn" type="button" id="ares-clock-me">Center on rovers</button>' +
            '</div>' +
            '<div class="ares-note" style="margin-top:8px">MTC is the Martian equivalent of UTC. Local solar times include the equation of time and the longitude offset. Ls is the areocentric solar longitude; seasons are northern-hemisphere seasons.</div>' +
          '</section>' +

        '</div>' +
      '</aside>' +
      '<div class="ares-pick-banner" id="ares-pick-banner">Click the globe to set a coordinate \u00b7 Esc to cancel</div>' +
      '<div id="ares-toast"></div>';

    var holder = document.createElement('div');
    holder.id = 'ares-ui-root';
    holder.innerHTML = html;
    document.body.appendChild(holder);
  }

  function cacheElements() {
    ARES.el.panel = $('ares-panel');
    ARES.el.toggle = $('ares-panel-toggle');
    ARES.el.tabs = Array.prototype.slice.call(document.querySelectorAll('.ares-tab'));
    ARES.el.sections = Array.prototype.slice.call(document.querySelectorAll('.ares-section'));
    ARES.el.atlasList = $('ares-atlas-list');
    ARES.el.tooltip = $('hover-tooltip');
  }

  function initLayers() {
    var S = ARES.state;
    ['minerals', 'slope', 'scout', 'footprints'].forEach(function (key) {
      var group = new THREE.Group();
      group.name = 'ares-' + key;
      S.layers[key] = group;
      scene.add(group);
    });
    S.hoverGroups.minerals = new THREE.Group();
    S.hoverGroups.minerals.name = 'ares-mineral-hover';
    S.hoverGroups.footprints = new THREE.Group();
    S.hoverGroups.footprints.name = 'ares-footprint-hover';
    ensureHoverGroups();
  }

  function ensureHoverGroups() {
    if (typeof markersGroup === 'undefined' || !markersGroup) return;
    ['minerals', 'footprints'].forEach(function (key) {
      var group = ARES.state.hoverGroups[key];
      if (group && group.parent !== markersGroup) markersGroup.add(group);
    });
  }

  // Atlas pins keep a near-constant screen size. At close rover-planning zoom
  // their old world-space spheres filled the view and hid the route lines.
  function startLandmarkPinScaling() {
    function tick() {
      if (typeof camera !== 'undefined' && camera) {
        var d = Math.max(1.001, camera.position.length());
        var alt = Math.max(0.0015, d - 1.0);
        // Keep close-range clipping sane now that rover-scale zoom is enabled.
        var near = d < 1.08 ? clamp(alt * 0.12, 0.00035, 0.01) : 0.01;
        if (Math.abs(camera.near - near) > 1e-7) {
          camera.near = near;
          camera.updateProjectionMatrix();
        }
        var pinScale = clamp(0.0020 * alt / 0.006, 0.0001, 1.0);
        var groupsToScale = [];
        if (typeof markersGroup !== 'undefined' && markersGroup) groupsToScale.push(markersGroup);
        if (typeof landingSiteMarkersGroup !== 'undefined' && landingSiteMarkersGroup) groupsToScale.push(landingSiteMarkersGroup);
        if (window.landingSiteMarkersGroup && groupsToScale.indexOf(window.landingSiteMarkersGroup) === -1) {
          groupsToScale.push(window.landingSiteMarkersGroup);
        }
        groupsToScale.forEach(function (grp) {
          grp.children.forEach(function (g) {
            if (g && g.userData && g.userData.aresLandmarkPin) g.scale.setScalar(pinScale);
          });
        });
        var minerals = ARES.state.hoverGroups.minerals;
        if (minerals) {
          minerals.children.forEach(function (m) {
            var p = m && m.geometry && m.geometry.parameters;
            if (!p) return;
            var isDot = m.geometry.type === 'SphereGeometry';
            var base = isDot ? p.radius : (p.outerRadius || p.radius || 0);
            if (!base) return;
            var targetRad = isDot ? 0.0004 : 0.0010;
            m.scale.setScalar(clamp(targetRad * alt / base, 0.00001, 1.0));
          });
        }
      }
      requestAnimationFrame(tick);
    }
    tick();
  }

  function patchExplorerHooks() {
    if (typeof create3DLandmarks === 'function') {
      var originalCreate = create3DLandmarks;
      window.create3DLandmarks = function (list) {
        originalCreate.call(this, list);
        ensureHoverGroups();
      };
    }
    if (typeof draw2DFlat === 'function') {
      var originalDraw = draw2DFlat;
      window.draw2DFlat = function () {
        originalDraw.apply(this, arguments);
        drawAres2D();
      };
    }
  }

  /* ------------------------------------------------------------------------
     Panel + tabs
     ------------------------------------------------------------------------ */
  function setPanel(open) {
    if (!ARES.el.panel) return;
    ARES.el.panel.classList.toggle('ares-panel-collapsed', !open);
    if (ARES.el.toggle) ARES.el.toggle.classList.toggle('visible', !open);
  }

  function switchTab(name) {
    ARES.el.tabs.forEach(function (tab) {
      tab.classList.toggle('active', tab.getAttribute('data-ares-tab') === name);
    });
    ARES.el.sections.forEach(function (section) {
      section.classList.toggle('active', section.getAttribute('data-ares-section') === name);
    });
    if (name === 'scout' && ARES.state.scout.result) drawScoutCharts();
  }

  function bindPanel() {
    ARES.el.tabs.forEach(function (tab) {
      tab.addEventListener('click', function () { switchTab(tab.getAttribute('data-ares-tab')); });
    });
    var close = $('ares-panel-close');
    if (close) close.addEventListener('click', function () { setPanel(false); });
    if (ARES.el.toggle) ARES.el.toggle.addEventListener('click', function () { setPanel(true); });
  }

  /* ------------------------------------------------------------------------
     Atlas
     ------------------------------------------------------------------------ */
  function buildIndex() {
    var idx = ARES.state.index;
    idx.clear();
    function add(key, item) {
      if (key == null) return;
      var k = String(key).trim();
      if (!k) return;
      if (!idx.has(k)) idx.set(k, item);
      var n = normName(k);
      if (n && !idx.has(n)) idx.set(n, item);
    }
    ARES.state.atlas.missions.forEach(function (m) {
      var item = Object.assign({ _kind: 'mission' }, m);
      add(m.id, item);
      add(m.name, item);
      add(m.station, item);
      add(m.namesake && m.namesake.name, item);
    });
    ARES.state.atlas.landmarks.forEach(function (l) {
      var item = Object.assign({ _kind: 'landmark' }, l);
      add(l.id, item);
      add(l.name, item);
      add(l.namesake && l.namesake.name, item);
    });
  }

  function indexMineralSites() {
    var idx = ARES.state.index;
    ARES.state.minerals.sites.forEach(function (site) {
      var item = Object.assign({ _kind: 'mineral' }, site);
      var key = 'mineral_' + site.id;
      idx.set(key, item);
      if (!idx.has(site.id)) idx.set(site.id, item);
      var n = normName(site.name);
      if (n && !idx.has(n)) idx.set(n, item);
    });
  }

  function lookupItem(displayData) {
    if (!displayData) return null;
    var idx = ARES.state.index;
    var candidates = [displayData.missionId, displayData.name, displayData.station_name, displayData.station];
    for (var i = 0; i < candidates.length; i += 1) {
      var c = candidates[i];
      if (c == null) continue;
      if (idx.has(String(c))) return idx.get(String(c));
      var n = normName(c);
      if (n && idx.has(n)) return idx.get(n);
    }
    return null;
  }

  async function loadAtlas() {
    try {
      var results = await Promise.all([
        fetchJSON('/api/atlas/missions'),
        fetchJSON('/api/atlas/landmarks')
      ]);
      var missions = results[0] || {};
      var landmarks = results[1] || {};
      ARES.state.atlas.missions = missions.missions || [];
      ARES.state.atlas.landmarks = landmarks.landmarks || [];
      ARES.state.atlas.figures = missions.figures || landmarks.figures || {};
      buildIndex();
      renderAtlas();
      mergeAtlasLandingSites();
    } catch (err) {
      if (ARES.el.atlasList) {
        ARES.el.atlasList.innerHTML = '<div class="ares-empty">Atlas unavailable: ' + esc(err.message) + '</div>';
      }
    }
  }

  function mergeAtlasLandingSites() {
    if (typeof DEFAULT_LANDING_SITES === 'undefined' || !Array.isArray(DEFAULT_LANDING_SITES)) return;
    var ids = new Set(DEFAULT_LANDING_SITES.map(function (s) { return s.id; }));
    var names = new Set(DEFAULT_LANDING_SITES.map(function (s) { return normName(s.name); }));
    var added = 0;
    ARES.state.atlas.missions.forEach(function (m) {
      if (!m || m.lat == null || m.lon == null) return;
      if (ids.has(m.id) || names.has(normName(m.name))) return;
      var year = yearOf(m.arrival) || yearOf(m.launch) || yearOf(m.year);
      DEFAULT_LANDING_SITES.push({
        id: m.id,
        name: m.name,
        station: m.station || m.site || m.name,
        site: m.station || m.site || m.name,
        final_site: m.final_site || '',
        lat: Number(m.lat),
        lon: signedLon(m.lon),
        elevation_m: m.elevation_m || 0,
        status: m.status || 'Completed',
        type: m.type || 'lander',
        year: year || '',
        agency: m.agency || 'NASA',
        total_odometry_km: m.total_odometry_km || 0,
        sol_range: m.sol_range || '',
        description: m.summary || m.significance || ''
      });
      ids.add(m.id);
      names.add(normName(m.name));
      added += 1;
    });
    if (added && typeof renderLandingSiteMarkers === 'function') {
      renderLandingSiteMarkers(DEFAULT_LANDING_SITES);
      if (typeof renderDrawerLandings === 'function') renderDrawerLandings(DEFAULT_LANDING_SITES);
    }
  }

  function filteredAtlasItems() {
    var q = normName(ARES.state.atlas.query);
    var source = ARES.state.atlas.filter === 'landmarks' ? ARES.state.atlas.landmarks : ARES.state.atlas.missions.slice();
    if (ARES.state.atlas.filter !== 'landmarks') {
      var rank = { active: 0, proposed: 1, completed: 2, failed: 3 };
      source.sort(function (a, b) {
        var ra = rank[String(a.status || '').toLowerCase()];
        var rb = rank[String(b.status || '').toLowerCase()];
        if (ra == null) ra = 2;
        if (rb == null) rb = 2;
        if (ra !== rb) return ra - rb;
        return (yearOf(b.arrival) || yearOf(b.launch) || 0) - (yearOf(a.arrival) || yearOf(a.launch) || 0);
      });
    }
    return source.filter(function (item) {
      if (!q) return true;
      var hay = normName([
        item.name, item.station, item.site, item.category, item.agency,
        item.namesake && item.namesake.name,
        item.namesake && item.namesake.role,
        item.significance, item.summary, item.description
      ].join(' '));
      return hay.indexOf(q) >= 0;
    });
  }

  function renderAtlas() {
    var list = ARES.el.atlasList;
    if (!list) return;
    var items = filteredAtlasItems();
    setText('ares-filter-missions', 'Missions (' + ARES.state.atlas.missions.length + ')');
    setText('ares-filter-landmarks', 'Landmarks (' + ARES.state.atlas.landmarks.length + ')');
    if (!items.length) {
      list.innerHTML = '<div class="ares-empty">No matching registry entries.</div>';
      return;
    }
    var html = '';
    var isMission = ARES.state.atlas.filter === 'missions';
    items.forEach(function (item) {
      var id = item.id || item.name;
      var expanded = !!ARES.state.atlas.expanded[id];
      var ns = item.namesake || (item.figure && ARES.state.atlas.figures[item.figure]) || null;
      var color = isMission ? statusColor(item.status) : (item.category === 'polar_cap' ? '#7dd3fc' : '#a78bfa');
      var status = isMission ? (item.status || 'Completed') : (item.category || 'Landmark');
      var sub = isMission
        ? coordText(item.lat, item.lon, item.lon_east) + ' \u00b7 ' + (item.station || item.site || '')
        : coordText(item.lat, item.lon, item.lon_east) + ' \u00b7 ' + (item.category || '');
      var figureLine = ns ? '<div class="ares-card-figure"><b>' + esc(ns.name || 'Namesake') + '</b>' + (ns.role ? ' \u00b7 ' + esc(ns.role) : '') + '</div>' : '';
      var detail = '';
      if (expanded) {
        detail = '<div class="ares-card-detail">' +
          (ns && ns.bio ? '<div><strong>Namesake</strong> \u00b7 ' + esc(ns.name) + '<br>' + esc(ns.bio) + '</div>' : '') +
          (item.significance ? '<div class="ares-significance"><strong>Scientific significance</strong><br>' + esc(item.significance) + '</div>' : '') +
          (item.summary ? '<div class="ares-significance">' + esc(item.summary) + '</div>' : '') +
          (isMission ? '<div class="ares-tt-meta">' + esc([item.agency, item.launch, item.arrival, item.status].filter(Boolean).join(' \u00b7 ')) + '</div>' : '') +
          '</div>';
      }
      html += '<div class="ares-card" data-ares-id="' + escAttr(id) + '" data-ares-kind="' + (isMission ? 'mission' : 'landmark') + '">' +
        '<div class="ares-card-top">' +
          '<span class="ares-card-dot" style="background:' + color + ';color:' + color + '"></span>' +
          '<div style="min-width:0"><div class="ares-card-title">' + esc(item.name) + '</div><div class="ares-card-sub">' + esc(sub) + '</div></div>' +
          '<span class="ares-badge ' + (isMission ? statusClass(item.status) : 'proposed') + '">' + esc(status) + '</span>' +
        '</div>' + figureLine +
        '<div class="ares-card-actions">' +
          '<button class="ares-btn ares-small" type="button" data-ares-fly="' + escAttr(id) + '">Fly here</button>' +
          '<button class="ares-btn ares-small" type="button" data-ares-detail="' + escAttr(id) + '">' + (expanded ? 'Hide dossier' : 'Dossier') + '</button>' +
        '</div>' + detail + '</div>';
    });
    list.innerHTML = html;
  }

  function toggleAtlasCard(id) {
    ARES.state.atlas.expanded[id] = !ARES.state.atlas.expanded[id];
    renderAtlas();
  }

  function bindAtlas() {
    var search = $('ares-atlas-search');
    if (search) {
      search.addEventListener('input', function () {
        ARES.state.atlas.query = search.value;
        renderAtlas();
      });
    }
    document.querySelectorAll('[data-atlas-filter]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        ARES.state.atlas.filter = btn.getAttribute('data-atlas-filter');
        document.querySelectorAll('[data-atlas-filter]').forEach(function (b) { b.classList.toggle('active', b === btn); });
        renderAtlas();
      });
    });
    if (ARES.el.atlasList) {
      ARES.el.atlasList.addEventListener('click', function (ev) {
        var fly = ev.target.closest('[data-ares-fly]');
        if (fly) {
          ev.stopPropagation();
          flyToItem(lookupItem({ missionId: fly.getAttribute('data-ares-fly'), name: fly.getAttribute('data-ares-fly') }));
          return;
        }
        var detail = ev.target.closest('[data-ares-detail]');
        if (detail) {
          ev.stopPropagation();
          toggleAtlasCard(detail.getAttribute('data-ares-detail'));
          return;
        }
        var card = ev.target.closest('.ares-card[data-ares-id]');
        if (card) toggleAtlasCard(card.getAttribute('data-ares-id'));
      });
    }
  }

  function flyToItem(item, then) {
    if (!item || item.lat == null || item.lon == null) {
      toast('No coordinates are available for this entry.', true);
      return;
    }
    var lat = Number(item.lat);
    var lon = signedLon(item.lon);
    var dist = 1.85;
    var cat = String(item.category || '').toLowerCase();
    if (cat.indexOf('landing') >= 0 || item._kind === 'mission') dist = 1.15;
    else if (cat.indexOf('polar') >= 0) dist = 2.4;
    if (typeof flyToCoordinate === 'function') flyToCoordinate(lat, lon, dist);
    ARES.state.time.cursorLon = (item.lon_east == null) ? eastLon(lon) : Number(item.lon_east);
    ARES.state.time.cursorLat = lat;
    if (typeof then === 'function') setTimeout(then, 950);
  }

  /* ------------------------------------------------------------------------
     Live Mars clock
     ------------------------------------------------------------------------ */
  function startClock() {
    fetchEphemeris();
    updateClockUI();
    setInterval(updateClockUI, 1000);
    setInterval(fetchEphemeris, 30000);
    var sync = $('ares-clock-sync');
    if (sync) sync.addEventListener('click', function () { fetchEphemeris(true); });
    var me = $('ares-clock-me');
    if (me) me.addEventListener('click', function () { flyToItem({ lat: 18.4446, lon: 77.4508, lon_east: 77.4508, category: 'landing_site', _kind: 'mission' }); });
  }

  async function fetchEphemeris(showToast) {
    try {
      var payload = await fetchJSON('/api/mars/ephemeris', null, 20000);
      if (!payload || payload.status === 'error') throw new Error((payload && payload.message) || 'Invalid ephemeris response');
      var S = ARES.state.time;
      S.payload = payload;
      S.baseReal = Date.now();
      S.baseMsd = Number(payload.mars_sol_date);
      S.baseLs = Number(payload.solar_longitude_Ls) || 0;
      S.eot = Number(payload.equation_of_time_deg) || 0;
      S.subsolar = payload.subsolar_point || { lat: 0, lon: 0 };
      S.rovers = payload.rover_clocks || {};
      S.fetched = Date.now();
      S.fallback = false;
      updateClockUI();
      if (showToast) toast('Ephemeris synced with the Mars24 backend.');
    } catch (err) {
      if (showToast) toast('Ephemeris sync failed: ' + err.message, true);
      if (!ARES.state.time.fetched) fallbackEphemeris();
    }
  }

  function fallbackEphemeris() {
    try {
      if (typeof computeLiveMarsEphemeris !== 'function') return;
      var e = computeLiveMarsEphemeris(new Date());
      var S = ARES.state.time;
      S.baseReal = Date.now();
      S.baseMsd = Number(String(e.mars_sol_date || '0').replace(/,/g, '')) || 0;
      S.baseLs = Number(String(e.solar_longitude_Ls || '0').replace(/[^\d.\-]/g, '')) || 0;
      S.eot = 0;
      S.subsolar = e.subsolar_point || { lat: 0, lon: 0 };
      S.rovers = {};
      S.payload = e;
      S.fallback = true;
      updateClockUI();
    } catch (err) { /* keep placeholders */ }
  }

  function marsNow() {
    var S = ARES.state.time;
    var elapsed = Math.max(0, (Date.now() - S.baseReal) / 1000);
    var msd = S.baseMsd + elapsed / 88775.244;
    var mtc = ((msd % 1) + 1) % 1 * 24;
    var ls = ((S.baseLs + (elapsed / 86400) * 0.524) % 360 + 360) % 360;
    return { msd: msd, mtc: mtc, ls: ls, eot: S.eot, subsolarLat: Number(S.subsolar.lat) || 0, subsolarLon: Number(S.subsolar.lon) || 0 };
  }

  function localSolarTime(lonEast, now, includeEot) {
    var lmst = ((now.mtc + (Number(lonEast) || 0) / 15) % 24 + 24) % 24;
    if (!includeEot) return lmst;
    return ((lmst + now.eot / 15) % 24 + 24) % 24;
  }

  function solarElevation(lat, ltst, dec) {
    var rad = Math.PI / 180;
    var H = (ltst - 12) * 15 * rad;
    var phi = lat * rad;
    var delta = dec * rad;
    var s = Math.sin(phi) * Math.sin(delta) + Math.cos(phi) * Math.cos(delta) * Math.cos(H);
    return Math.asin(clamp(s, -1, 1)) / rad;
  }

  function roverState(key, now) {
    var r = ARES.state.time.rovers[key];
    if (!r) return null;
    var lon = Number(r.lon_east == null ? r.lon : r.lon_east);
    var ltst = localSolarTime(lon, now, true);
    var sol;
    if (r.landing_msd != null) sol = Math.floor(now.msd - Number(r.landing_msd));
    else if (r.sol != null) sol = Number(r.sol) + Math.floor(now.msd - ARES.state.time.baseMsd);
    else sol = null;
    var elev = solarElevation(Number(r.lat) || 0, ltst, now.subsolarLat);
    return {
      sol: sol, ltst: ltst, lmst: localSolarTime(lon, now, false), elev: elev,
      phase: elev > 8 ? 'DAY' : elev > -3 ? 'TWILIGHT' : 'NIGHT',
      lon: lon, lat: Number(r.lat) || 0, name: r.name || key
    };
  }

  function updateClockUI() {
    var now = marsNow();
    var ls = now.ls;
    var season = seasonFromLs(ls);
    setText('ares-mtc', fmtHMS(now.mtc));
    setText('ares-msd', 'MSD ' + now.msd.toFixed(3));
    setText('ares-ls', 'Ls ' + ls.toFixed(2) + '\u00b0');
    setText('ares-season', season);
    setText('ares-clock-mtc', fmtHMS(now.mtc));
    setText('ares-clock-msd', 'MSD ' + now.msd.toFixed(3) + ' \u00b7 Sol fraction ' + ((now.msd % 1) * 24).toFixed(2) + 'h');

    var p = roverState('perseverance', now);
    var c = roverState('curiosity', now);
    if (p) {
      setText('ares-persev-time', fmtHMS(p.ltst));
      setText('ares-persev-sub', 'Sol ' + p.sol + ' \u00b7 ' + p.phase);
    } else {
      setText('ares-persev-time', '--:--:--');
      setText('ares-persev-sub', 'Sol -- \u00b7 no lock');
    }
    if (c) {
      setText('ares-curio-time', fmtHMS(c.ltst));
      setText('ares-curio-sub', 'Sol ' + c.sol + ' \u00b7 ' + c.phase);
    } else {
      setText('ares-curio-time', '--:--:--');
      setText('ares-curio-sub', 'Sol -- \u00b7 no lock');
    }

    var cursorLon = ARES.state.time.cursorLon;
    if (cursorLon == null) {
      var center = getCameraCenterLatLon();
      cursorLon = center ? center.lon : 77.45;
    }
    var cursorLat = ARES.state.time.cursorLat;
    if (cursorLat == null) {
      var center2 = getCameraCenterLatLon();
      cursorLat = center2 ? center2.lat : 18.44;
    }
    var cursorLst = localSolarTime(cursorLon, now, true);
    var cursorElev = solarElevation(cursorLat, cursorLst, now.subsolarLat);
    setText('ares-cursor-time', fmtHMS(cursorLst));
    setText('ares-cursor-sub', Math.abs(cursorLon).toFixed(1) + '\u00b0' + (cursorLon >= 0 ? 'E' : 'W') + ' \u00b7 ' + (cursorElev > 0 ? 'DAY' : 'NIGHT') + ' \u00b7 ' + cursorElev.toFixed(0) + '\u00b0');

    var d = new Date();
    setText('ares-earth-utc', d.toISOString().slice(11, 19));
    setText('ares-earth-date', d.toISOString().slice(0, 10));

    var details = $('ares-clock-details');
    if (details) {
      var rows = [
        ['Earth UTC', d.toISOString().replace('T', ' ').slice(0, 19) + ' UTC'],
        ['Mars Sol Date', now.msd.toFixed(6)],
        ['Coordinated Mars Time', fmtHMS(now.mtc)],
        ['Solar longitude Ls', ls.toFixed(3) + '\u00b0'],
        ['Northern season', season],
        ['Equation of time', now.eot.toFixed(2) + '\u00b0'],
        ['Subsolar point', fmtCoord(now.subsolarLat, now.subsolarLon)],
        ['Solar irradiance', (ARES.state.time.payload && ARES.state.time.payload.solar_irradiance_wm2 != null) ? ARES.state.time.payload.solar_irradiance_wm2 + ' W/m\u00b2' : '--'],
        ['Perseverance', p ? ('Sol ' + p.sol + ' \u00b7 LTST ' + fmtHMS(p.ltst) + ' \u00b7 ' + p.phase + ' \u00b7 el ' + p.elev.toFixed(1) + '\u00b0') : 'No clock lock'],
        ['Curiosity', c ? ('Sol ' + c.sol + ' \u00b7 LTST ' + fmtHMS(c.ltst) + ' \u00b7 ' + c.phase + ' \u00b7 el ' + c.elev.toFixed(1) + '\u00b0') : 'No clock lock'],
        ['Cursor', Math.abs(cursorLon).toFixed(4) + '\u00b0' + (cursorLon >= 0 ? 'E' : 'W') + ' / ' + Math.abs(cursorLat).toFixed(4) + '\u00b0' + (cursorLat >= 0 ? 'N' : 'S') + ' \u00b7 LST ' + fmtHMS(cursorLst)],
        ['Source', ARES.state.time.fallback ? 'local Mars24 fallback' : 'Mars24 backend /api/mars/ephemeris']
      ];
      details.innerHTML = rows.map(function (row) {
        return '<div class="ares-clock-row"><span class="k">' + esc(row[0]) + '</span><span class="v">' + esc(row[1]) + '</span></div>';
      }).join('');
    }
  }

  /* ------------------------------------------------------------------------
     Aqueous minerals
     ------------------------------------------------------------------------ */
  async function loadMinerals() {
    try {
      var data = await fetchJSON('/api/minerals', null, 30000);
      ARES.state.minerals.classes = data.classes || {};
      ARES.state.minerals.sites = data.sites || [];
      ARES.state.minerals.active = new Set(Object.keys(ARES.state.minerals.classes));
      indexMineralSites();
      renderMineralPanel();
      rebuildMineralDrape();
      rebuildMineralMarkers();
    } catch (err) {
      var host = $('ares-mineral-classes');
      if (host) host.innerHTML = '<div class="ares-note">Mineral catalog unavailable: ' + esc(err.message) + '</div>';
    }
  }

  function activeClassesForSite(site) {
    return (site.classes || []).filter(function (key) { return ARES.state.minerals.active.has(key); });
  }

  function classColor(key) {
    var cls = ARES.state.minerals.classes[key];
    return (cls && cls.color) || COLOR.cyan;
  }
  function classLabel(key) {
    var cls = ARES.state.minerals.classes[key];
    return (cls && cls.label) || key;
  }

  function renderMineralPanel() {
    var M = ARES.state.minerals;
    var chips = $('ares-mineral-classes');
    if (chips) {
      chips.innerHTML = Object.keys(M.classes).map(function (key) {
        var cls = M.classes[key];
        var on = M.active.has(key);
        return '<button type="button" class="ares-chip ' + (on ? 'on' : 'off') + '" data-mineral-class="' + escAttr(key) + '" style="color:' + esc(cls.color || COLOR.cyan) + '">' +
          '<span class="ares-chip-dot"></span>' + esc(cls.label || key) + '</button>';
      }).join('');
    }
    var activeSites = M.sites.filter(function (s) { return activeClassesForSite(s).length > 0; });
    var stats = $('ares-mineral-stats');
    if (stats) {
      stats.innerHTML =
        '<div class="ares-stat"><div class="ares-stat-value">' + activeSites.length + '</div><div class="ares-stat-label">Active targets</div></div>' +
        '<div class="ares-stat"><div class="ares-stat-value">' + M.active.size + '</div><div class="ares-stat-label">Classes</div></div>' +
        '<div class="ares-stat"><div class="ares-stat-value">' + M.sites.length + '</div><div class="ares-stat-label">Total sites</div></div>';
    }
    var list = $('ares-mineral-list');
    if (list) {
      if (!activeSites.length) {
        list.innerHTML = '<div class="ares-empty">No targets match the selected spectral classes.</div>';
      } else {
        list.innerHTML = activeSites.map(function (site) {
          var keys = activeClassesForSite(site);
          var dots = keys.map(function (key) {
            return '<span class="ares-card-dot" style="background:' + classColor(key) + ';color:' + classColor(key) + '"></span>';
          }).join(' ');
          var labels = keys.map(classLabel).join(' \u00b7 ');
          return '<div class="ares-card" data-mineral-id="' + escAttr(site.id) + '">' +
            '<div class="ares-card-top">' +
              '<div style="display:flex;gap:3px;margin-top:3px">' + dots + '</div>' +
              '<div style="min-width:0"><div class="ares-card-title">' + esc(site.name) + '</div>' +
              '<div class="ares-card-sub">' + esc(coordText(site.lat, site.lon_east, site.lon_east)) + ' \u00b7 ' + Math.round((site.confidence || 0) * 100) + '% confidence</div></div>' +
            '</div>' +
            '<div class="ares-card-figure">' + esc(labels) + '</div>' +
            '<div class="ares-card-sub" style="margin-top:4px">' + esc(site.source || '') + '</div>' +
            '<div class="ares-card-actions">' +
              '<button class="ares-btn ares-small" type="button" data-mineral-fly="' + escAttr(site.id) + '">Fly here</button>' +
              '<button class="ares-btn ares-small" type="button" data-mineral-scan="' + escAttr(site.id) + '">Scan spectra</button>' +
            '</div></div>';
        }).join('');
      }
    }
    var drapeBtn = $('ares-mineral-drape');
    if (drapeBtn) { drapeBtn.textContent = 'Drape ' + (M.drape ? 'ON' : 'OFF'); drapeBtn.classList.toggle('ares-cyan', M.drape); }
    var siteBtn = $('ares-mineral-sites');
    if (siteBtn) { siteBtn.textContent = 'Sites ' + (M.showSites ? 'ON' : 'OFF'); siteBtn.classList.toggle('ares-cyan', M.showSites); }
    var opacity = $('ares-mineral-opacity');
    if (opacity) opacity.value = String(M.opacity);
    setText('ares-mineral-opacity-out', Math.round(M.opacity * 100) + '%');
  }

  function rebuildMineralDrape() {
    var M = ARES.state.minerals;
    var group = ARES.state.layers.minerals;
    if (!group) return;
    clearGroup(group);
    if (!M.drape) return;
    var canvas = document.createElement('canvas');
    canvas.width = 2048;
    canvas.height = 1024;
    var ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.globalCompositeOperation = 'lighter';
    var drew = 0;
    M.sites.forEach(function (site) {
      var keys = activeClassesForSite(site);
      if (!keys.length) return;
      var x = (eastLon(site.lon_east) / 360) * canvas.width;
      var y = ((90 - Number(site.lat)) / 180) * canvas.height;
      var radius = Math.max(4, ((Number(site.radius_deg) || 0.05) / 360) * canvas.width * 0.65);
      keys.forEach(function (key) {
        var color = classColor(key);
        var grad = ctx.createRadialGradient(x, y, 0, x, y, radius);
        grad.addColorStop(0, hexToRgba(color, 0.35));
        grad.addColorStop(0.5, hexToRgba(color, 0.10));
        grad.addColorStop(1, hexToRgba(color, 0));
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();
      });
      ctx.strokeStyle = hexToRgba(classColor(keys[0]), 0.22);
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(x, y, radius * 0.32, 0, Math.PI * 2);
      ctx.stroke();
      drew += 1;
    });
    if (!drew) return;
    var texture = new THREE.CanvasTexture(canvas);
    if ('SRGBColorSpace' in THREE) texture.colorSpace = THREE.SRGBColorSpace;
    else if ('sRGBEncoding' in THREE) texture.encoding = THREE.sRGBEncoding;
    texture.needsUpdate = true;
    var mat = new THREE.MeshBasicMaterial({
      map: texture, transparent: true, opacity: M.opacity,
      depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.FrontSide
    });
    var mesh = new THREE.Mesh(new THREE.SphereGeometry(MARS_RADIUS * 1.0012, 128, 64), mat);
    mesh.renderOrder = 3;
    mesh.name = 'ares-mineral-drape';
    group.add(mesh);
  }

  function rebuildMineralMarkers() {
    var M = ARES.state.minerals;
    var group = ARES.state.hoverGroups.minerals;
    if (!group) return;
    clearGroup(group);
    group.visible = M.showSites;
    if (!M.showSites) return;
    M.sites.forEach(function (site) {
      var keys = activeClassesForSite(site);
      if (!keys.length) return;
      var color = classColor(keys[0]);
      var size = Math.min(0.012, Math.max(0.0015, (Number(site.radius_deg) || 0.05) * 0.01745 * 0.4));
      var pos = latLonToVector3(Number(site.lat), eastLon(site.lon_east) > 180 ? eastLon(site.lon_east) - 360 : eastLon(site.lon_east), MARS_RADIUS * 1.0035);
      var normal = pos.clone().normalize();
      var ring = new THREE.Mesh(
        new THREE.RingGeometry(size * 0.78, size, 32),
        new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0.70, side: THREE.DoubleSide, depthWrite: false })
      );
      ring.position.copy(pos);
      ring.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal);
      ring.renderOrder = 6;
      ring.userData = {
        name: site.name, site_id: site.id,
        lat: Number(site.lat), lon: signedLon(site.lon_east), lon_east: Number(site.lon_east),
        elevation_m: 0, status: 'Mineral target', category: 'AQUEOUS MINERAL TARGET',
        description: (site.description || '') + ' Classes: ' + keys.map(classLabel).join(', ') + '.',
        significance: site.description || '',
        missionId: 'mineral_' + site.id,
        aresMineral: true
      };
      group.add(ring);
      var dot = new THREE.Mesh(
        new THREE.SphereGeometry(size * 0.10, 8, 8),
        new THREE.MeshBasicMaterial({ color: '#ffffff', transparent: true, opacity: 0.80 })
      );
      dot.position.copy(pos.clone().multiplyScalar(1.0002));
      dot.userData = ring.userData;
      group.add(dot);
    });
    ensureHoverGroups();
  }

  function bindMinerals() {
    var chips = $('ares-mineral-classes');
    if (chips) {
      chips.addEventListener('click', function (ev) {
        var chip = ev.target.closest('[data-mineral-class]');
        if (!chip) return;
        var key = chip.getAttribute('data-mineral-class');
        if (ARES.state.minerals.active.has(key)) ARES.state.minerals.active.delete(key);
        else ARES.state.minerals.active.add(key);
        renderMineralPanel();
        rebuildMineralDrape();
        rebuildMineralMarkers();
      });
    }
    var opacity = $('ares-mineral-opacity');
    if (opacity) {
      opacity.addEventListener('input', function () {
        ARES.state.minerals.opacity = Number(opacity.value);
        setText('ares-mineral-opacity-out', Math.round(ARES.state.minerals.opacity * 100) + '%');
        var mesh = ARES.state.layers.minerals.children[0];
        if (mesh && mesh.material) mesh.material.opacity = ARES.state.minerals.opacity;
      });
    }
    var drape = $('ares-mineral-drape');
    if (drape) drape.addEventListener('click', function () {
      ARES.state.minerals.drape = !ARES.state.minerals.drape;
      renderMineralPanel();
      rebuildMineralDrape();
    });
    var sites = $('ares-mineral-sites');
    if (sites) sites.addEventListener('click', function () {
      ARES.state.minerals.showSites = !ARES.state.minerals.showSites;
      renderMineralPanel();
      rebuildMineralMarkers();
    });
    ['crism', 'omega', 'hirise'].forEach(function (key) {
      var btn = $('ares-scan-' + key);
      if (!btn) return;
      btn.addEventListener('click', function () {
        var center = getCameraCenterLatLon();
        if (!center) { toast('Point the camera at Mars first.', true); return; }
        scanAt(center.lat, center.lon, key === 'hirise' ? 'HiRISE' : key.toUpperCase());
      });
    });
    var list = $('ares-mineral-list');
    if (list) {
      list.addEventListener('click', function (ev) {
        var fly = ev.target.closest('[data-mineral-fly]');
        var scan = ev.target.closest('[data-mineral-scan]');
        if (!fly && !scan) return;
        ev.stopPropagation();
        var id = (fly || scan).getAttribute(fly ? 'data-mineral-fly' : 'data-mineral-scan');
        var site = ARES.state.minerals.sites.filter(function (s) { return String(s.id) === String(id); })[0];
        if (!site) return;
        var item = Object.assign({ _kind: 'mineral' }, site);
        if (fly) flyToItem(item);
        else {
          flyToItem(item, function () { scanAt(site.lat, site.lon_east, 'CRISM'); });
        }
      });
    }
    var ode = $('ares-ode-results');
    if (ode) {
      ode.addEventListener('click', function (ev) {
        var fly = ev.target.closest('[data-ode-fly]');
        if (!fly) return;
        ev.stopPropagation();
        var pdsid = fly.getAttribute('data-ode-fly');
        var products = (ARES.state.minerals.ode && ARES.state.minerals.ode.products) || [];
        var product = products.filter(function (p) { return String(p.pdsid) === String(pdsid); })[0];
        if (product) {
          var center = product.center || { lat: product.center_lat, lon: product.center_lon };
          flyToItem({ lat: center.lat, lon: center.lon, lon_east: eastLon(center.lon), category: 'spectral_footprint', _kind: 'landmark' });
        }
      });
    }
  }

  async function scanAt(lat, lon, instrument) {
    var host = $('ares-ode-results');
    if (host) host.innerHTML = '<div class="ares-note">Querying NASA PDS ODE for ' + esc(instrument) + ' coverage\u2026</div>';
    try {
      var radius = instrument === 'OMEGA' ? 1.0 : (instrument === 'HiRISE' ? 0.12 : 0.4);
      var url = '/api/nasa/ode?instrument=' + encodeURIComponent(instrument) +
        '&lat=' + encodeURIComponent(lat) + '&lon=' + encodeURIComponent(eastLon(lon)) +
        '&radius=' + encodeURIComponent(radius) + '&limit=18';
      var data = await fetchJSON(url, null, 60000);
      ARES.state.minerals.ode = data;
      renderFootprints(data, instrument);
      renderOdeResults();
      var count = Number(data.count) || 0;
      toast(count ? (count + ' ' + instrument + ' products intersect this area.') : ('No ' + instrument + ' products found.'), !count);
    } catch (err) {
      if (host) host.innerHTML = '<div class="ares-note" style="color:#fecaca">ODE query failed: ' + esc(err.message) + '</div>';
      toast('ODE query failed: ' + err.message, true);
    }
  }

  function parseWKT(wkt) {
    var rings = [];
    if (!wkt) return rings;
    var text = String(wkt).replace(/^SRID=\d+;/i, '');
    var re = /\(([^()]+)\)/g;
    var m;
    while ((m = re.exec(text))) {
      var pts = [];
      m[1].trim().split(/\s*,\s*/).forEach(function (pair) {
        var nums = pair.trim().split(/\s+/).map(Number);
        if (nums.length >= 2 && isFinite(nums[0]) && isFinite(nums[1])) pts.push([nums[0], nums[1]]);
      });
      if (pts.length >= 3) rings.push(pts);
    }
    return rings;
  }

  function renderFootprints(data, instrument) {
    var group = ARES.state.layers.footprints;
    var hover = ARES.state.hoverGroups.footprints;
    if (!group || !hover) return;
    clearGroup(group);
    clearGroup(hover);
    ARES.state.footprints = [];
    var color = INSTRUMENT_COLORS[instrument] || COLOR.cyan;
    var products = (data && data.products) || [];
    products.forEach(function (product) {
      var rings = parseWKT(product.wkt || product.footprint_wkt || product.geometry_wkt);
      rings.forEach(function (ring) {
        var verts = ring.map(function (pt) {
          return latLonToVector3(Number(pt[1]), signedLon(pt[0]), MARS_RADIUS * 1.0045);
        });
        if (verts.length < 2) return;
        verts.push(verts[0]);
        var geo = new THREE.BufferGeometry().setFromPoints(verts);
        var line = new THREE.Line(geo, new THREE.LineBasicMaterial({ color: color, transparent: true, opacity: 0.82 }));
        line.renderOrder = 7;
        group.add(line);
        ARES.state.footprints.push({ ring: ring, color: color });
      });
      var center = product.center || { lat: product.center_lat, lon: product.center_lon };
      if (center.lat == null && rings.length && rings[0].length) {
        var sumLon = 0, sumLat = 0;
        rings[0].forEach(function (p) { sumLon += Number(p[0]); sumLat += Number(p[1]); });
        center = { lon: sumLon / rings[0].length, lat: sumLat / rings[0].length };
      }
      if (center.lat != null && center.lon != null) {
        var lat = Number(center.lat);
        var lon = signedLon(center.lon);
        var pos = latLonToVector3(lat, lon, MARS_RADIUS * 1.005);
        var marker = new THREE.Mesh(
          new THREE.SphereGeometry(0.004, 12, 10),
          new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0.95 })
        );
        marker.position.copy(pos);
        marker.userData = {
          name: (instrument || 'PDS') + ' footprint ' + (product.pdsid || ''),
          lat: lat, lon: lon, lon_east: eastLon(lon), elevation_m: 0,
          status: 'PDS product', category: (instrument || 'PDS') + ' SPECTRAL FOOTPRINT',
          description: 'Product ' + (product.pdsid || '') + (product.pt ? ' \u00b7 PT ' + product.pt : '') + (product.start_time ? ' \u00b7 ' + product.start_time : ''),
          significance: 'Observed spectral footprint returned by the NASA PDS Orbital Data Explorer.',
          missionId: 'ode_' + (product.pdsid || Math.random().toString(36).slice(2))
        };
        hover.add(marker);
        ARES.state.index.set(marker.userData.missionId, Object.assign({ _kind: 'footprint' }, marker.userData));
      }
    });
    ensureHoverGroups();
  }

  function renderOdeResults() {
    var host = $('ares-ode-results');
    if (!host) return;
    var data = ARES.state.minerals.ode;
    if (!data) { host.innerHTML = ''; return; }
    var products = data.products || [];
    if (!products.length) {
      host.innerHTML = '<div class="ares-note" style="margin-top:7px">No footprint intersections were returned for this instrument and radius.</div>';
      return;
    }
    var html = '<div class="ares-note" style="margin-top:7px">' + esc(data.count || products.length) + ' products returned</div>';
    products.slice(0, 18).forEach(function (p) {
      var center = p.center || { lat: p.center_lat, lon: p.center_lon };
      var coord = (center.lat != null) ? coordText(center.lat, center.lon, eastLon(center.lon)) : '';
      var browse = p.browse_url || ('/api/nasa/browse?pdsid=' + encodeURIComponent(p.pdsid || ''));
      html += '<div class="ares-card" style="cursor:default">' +
        '<div class="ares-card-top"><div style="min-width:0"><div class="ares-card-title ares-mono" style="font-size:10px">' + esc(p.pdsid || 'PDS product') + '</div>' +
        '<div class="ares-card-sub">' + esc(coord) + (p.pt ? ' \u00b7 PT ' + esc(p.pt) : '') + (p.start_time ? ' \u00b7 ' + esc(p.start_time) : '') + '</div></div></div>' +
        '<div class="ares-card-actions">' +
          '<button class="ares-btn ares-small" type="button" data-ode-fly="' + escAttr(p.pdsid || '') + '">Fly to footprint</button>' +
          '<a class="ares-btn ares-small" href="' + escAttr(browse) + '" target="_blank" rel="noopener">Browse</a>' +
        '</div></div>';
    });
    host.innerHTML = html;
  }

  /* ------------------------------------------------------------------------
     DEM slope hazards
     ------------------------------------------------------------------------ */
  function bindTerrain() {
    var run = $('ares-slope-run');
    if (run) run.addEventListener('click', function () {
      var center = getCameraCenterLatLon();
      if (!center) { toast('Point the camera at Mars first.', true); return; }
      analyzeSlopeAt(center.lat, center.lon);
    });
    var jezero = $('ares-slope-jezero');
    if (jezero) jezero.addEventListener('click', function () {
      flyToItem({ lat: 18.4446, lon: 77.4508, lon_east: 77.4508, category: 'landing_site', _kind: 'mission' }, function () {
        analyzeSlopeAt(18.4446, 77.4508);
      });
    });
    var gale = $('ares-slope-gale');
    if (gale) gale.addEventListener('click', function () {
      flyToItem({ lat: -4.5895, lon: 137.4417, lon_east: 137.4417, category: 'landing_site', _kind: 'mission' }, function () {
        analyzeSlopeAt(-4.5895, 137.4417);
      });
    });
    var clear = $('ares-slope-clear');
    if (clear) clear.addEventListener('click', clearSlope);
    var exag = $('ares-slope-exag');
    if (exag) exag.addEventListener('input', function () {
      ARES.state.terrain.exaggeration = Number(exag.value);
      setText('ares-slope-exag-out', ARES.state.terrain.exaggeration.toFixed(1) + '\u00d7');
      renderSlopePatch();
    });
    var opacity = $('ares-slope-opacity');
    if (opacity) opacity.addEventListener('input', function () {
      ARES.state.terrain.opacity = Number(opacity.value);
      setText('ares-slope-opacity-out', Math.round(ARES.state.terrain.opacity * 100) + '%');
      if (ARES.state.terrain.mesh && ARES.state.terrain.mesh.material) {
        ARES.state.terrain.mesh.material.opacity = ARES.state.terrain.opacity;
      }
    });
    [['ares-brightness', 'brightness'], ['ares-contrast', 'contrast'], ['ares-saturate', 'saturate']].forEach(function (pair) {
      var node = $(pair[0]);
      if (!node) return;
      node.addEventListener('input', function () {
        ARES.state.terrain.filters[pair[1]] = Number(node.value);
        setText(pair[0] + '-out', node.value + '%');
        applyVisualFilters();
      });
    });
  }

  function applyVisualFilters() {
    var f = ARES.state.terrain.filters;
    var identity = (Number(f.brightness) === 100 && Number(f.contrast) === 100 && Number(f.saturate) === 100);
    var filter = identity ? '' : 'brightness(' + f.brightness + '%) contrast(' + f.contrast + '%) saturate(' + f.saturate + '%)';
    if (renderer && renderer.domElement) renderer.domElement.style.filter = filter;
    if (typeof flatCanvas !== 'undefined' && flatCanvas) flatCanvas.style.filter = filter;
  }

  function clearSlope() {
    clearGroup(ARES.state.layers.slope);
    ARES.state.terrain.grid = null;
    ARES.state.terrain.mesh = null;
    var stats = $('ares-slope-stats');
    if (stats) stats.innerHTML = '<div class="ares-note" style="margin-top:7px">No DEM analysis loaded. The analyzer queries the USGS Astrogeology STAC archive for a CTX or HiRISE COG DTM and falls back to a deterministic MOLA-anchored terrain model if the archive is unreachable.</div>';
    drawSlopeMinimap();
    drawAres2D();
  }

  async function analyzeSlopeAt(lat, lon) {
    if (ARES.state.terrain.busy) return;
    var T = ARES.state.terrain;
    T.busy = true;
    var sizeKm = Number(($('ares-slope-size') || {}).value) || 3.6;
    var resolution = Number(($('ares-slope-res') || {}).value) || 20;
    var prefer = resolution <= 5 ? 'hirise' : 'ctx';
    var sizeDeg = sizeKm / 59.274;
    var runBtn = $('ares-slope-run');
    if (runBtn) { runBtn.disabled = true; runBtn.textContent = 'Reading USGS DTM\u2026'; }
    var stats = $('ares-slope-stats');
    if (stats) stats.innerHTML = '<div class="ares-note" style="margin-top:7px">Reading a real USGS Astrogeology COG DTM window and computing slope at native resolution\u2026</div>';
    try {
      var url = '/api/terrain/slope?lat=' + encodeURIComponent(lat) + '&lon=' + encodeURIComponent(eastLon(lon)) +
        '&size=' + encodeURIComponent(sizeDeg.toFixed(5)) + '&resolution=' + encodeURIComponent(resolution) +
        '&prefer=' + encodeURIComponent(prefer) + '&n=64';
      var data = await fetchJSON(url, null, 120000);
      if (!data || data.status === 'error' || !data.elevation) throw new Error((data && data.message) || 'Invalid terrain response');
      T.grid = data;
      T.center = { lat: lat, lon: eastLon(lon) };
      T.source = data;
      renderSlopePatch();
      renderSlopeStats(data);
      toast('DEM slope grid loaded \u00b7 ' + (data.is_real_dem ? data.source : 'synthetic fallback'));
    } catch (err) {
      if (stats) stats.innerHTML = '<div class="ares-note" style="margin-top:7px;color:#fecaca">DEM analysis failed: ' + esc(err.message) + '</div>';
      toast('Slope analysis failed: ' + err.message, true);
    } finally {
      T.busy = false;
      if (runBtn) { runBtn.disabled = false; runBtn.textContent = 'Analyze at camera center'; }
    }
  }

  function renderSlopeStats(data) {
    var g = data || {};
    var stats = $('ares-slope-stats');
    if (!stats) return;
    var counts = g.hazard_counts || {};
    var total = counts.total || (g.n ? g.n * g.n : 0) || 1;
    var safe = counts.safe || 0, caution = counts.caution || 0, noGo = counts.no_go || 0;
    var sourceLabel = g.source || 'DEM';
    var real = (g.is_real_dem === true) ? '<span class="ares-green">REAL USGS DEM</span>' : '<span class="ares-amber">SYNTHETIC FALLBACK</span>';
    var cell = g.cell_size_m || {};
    var cellText = (typeof cell === 'object') ? ((Number(cell.x) || 0).toFixed(1) + ' \u00d7 ' + (Number(cell.y) || 0).toFixed(1)) : Number(cell).toFixed(1);
    stats.innerHTML =
      '<div class="ares-stats" style="grid-template-columns:repeat(3,1fr)">' +
        '<div class="ares-stat"><div class="ares-stat-value" style="color:#22c55e">' + ((safe / total) * 100).toFixed(1) + '%</div><div class="ares-stat-label">Safe 0\u201315\u00b0</div></div>' +
        '<div class="ares-stat"><div class="ares-stat-value" style="color:#f59e0b">' + ((caution / total) * 100).toFixed(1) + '%</div><div class="ares-stat-label">Caution 15\u201330\u00b0</div></div>' +
        '<div class="ares-stat"><div class="ares-stat-value" style="color:#ef4444">' + ((noGo / total) * 100).toFixed(1) + '%</div><div class="ares-stat-label">No-go >30\u00b0</div></div>' +
      '</div>' +
      '<div class="ares-source-line"><b>' + esc(sourceLabel) + '</b> \u00b7 ' + real + '<br>' +
        esc(coordText(g.lat0 || 0, g.lon0 || 0, null)) +
        ' \u00b7 ' + (g.n || '--') + '\u00d7' + (g.n || '--') + ' grid \u00b7 ' + cellText + ' m cells' +
        (g.native_resolution_m ? ' \u00b7 ' + Number(g.native_resolution_m).toFixed(2) + ' m/px native' : '') +
        '<br>Max slope ' + (Number(g.slope_max_deg || 0)).toFixed(2) + '\u00b0 \u00b7 mean ' + (Number(g.slope_mean_deg || 0)).toFixed(2) + '\u00b0' +
        (g.coverage_fraction != null ? ' \u00b7 ' + (Number(g.coverage_fraction) * 100).toFixed(0) + '% DEM coverage' : '') +
        (g.stac_id ? '<br>STAC: ' + esc(g.stac_id) : '') +
        (g.source_detail ? '<br>' + esc(g.source_detail) : '') +
      '</div>';
  }

  function drawSlopeMinimap() {
    var canvas = $('ares-slope-map');
    if (!canvas) return;
    var setup = setupCanvas(canvas, 156);
    if (!setup) return;
    var ctx = setup.ctx, w = setup.w, h = setup.h;
    ctx.fillStyle = 'rgba(2,6,14,0.55)';
    ctx.fillRect(0, 0, w, h);
    var g = ARES.state.terrain.grid;
    if (!g || !g.classes) {
      ctx.fillStyle = '#64748b';
      ctx.font = '10px monospace';
      ctx.fillText('Analyze a DEM window to render the hazard map.', 12, h / 2);
      setText('ares-slope-map-legend', '\u2014');
      return;
    }
    var n = Number(g.n) || 0;
    if (!n) return;
    var pad = 8;
    var side = Math.min(w - pad * 2, h - pad * 2);
    var ox = (w - side) / 2;
    var oy = pad;
    var cell = side / n;
    for (var r = 0; r < n; r += 1) {
      for (var c = 0; c < n; c += 1) {
        ctx.fillStyle = slopeColor(g.classes[r][c]);
        ctx.globalAlpha = 0.82;
        ctx.fillRect(ox + c * cell, oy + r * cell, cell + 0.5, cell + 0.5);
      }
    }
    ctx.globalAlpha = 1;
    ctx.strokeStyle = 'rgba(226,232,240,0.4)';
    ctx.lineWidth = 1;
    ctx.strokeRect(ox, oy, side, side);
    var center = ARES.state.terrain.center;
    if (center) {
      // The map spans the AOI; draw a small target crosshair at the requested center.
      var cxo = ox + side / 2;
      var cyo = oy + side / 2;
      ctx.strokeStyle = 'rgba(255,255,255,0.8)';
      ctx.beginPath(); ctx.moveTo(cxo - 5, cyo); ctx.lineTo(cxo + 5, cyo); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(cxo, cyo - 5); ctx.lineTo(cxo, cyo + 5); ctx.stroke();
    }
    var cellSize = g.cell_size_m || {};
    var cellText = (typeof cellSize === 'object') ? ((Number(cellSize.x) || 0).toFixed(0) + '\u00d7' + (Number(cellSize.y) || 0).toFixed(0)) : Number(cellSize).toFixed(0);
    setText('ares-slope-map-legend', n + '\u00d7' + n + ' \u00b7 ' + cellText + ' m');
    ctx.fillStyle = '#94a3b8';
    ctx.font = '8px monospace';
    ctx.fillText('N', ox + 3, oy + 10);
    ctx.fillText(Number(g.size_km || 0).toFixed(2) + ' km', ox + 3, oy + side - 4);
  }

  function slopeColor(klass) {
    if (klass === 2 || klass === 'no_go') return COLOR.noGo;
    if (klass === 1 || klass === 'caution') return COLOR.caution;
    return COLOR.safe;
  }

  function renderSlopePatch() {
    var T = ARES.state.terrain;
    var group = ARES.state.layers.slope;
    if (!group) return;
    clearGroup(group);
    T.mesh = null;
    var g = T.grid;
    if (!g || !g.elevation || !g.classes) return;
    var n = Number(g.n) || 0;
    if (!n) return;
    var lat0 = Number(g.lat_grid0 != null ? g.lat_grid0 : g.lat0);
    var lon0 = Number(g.lon_grid0 != null ? g.lon_grid0 : g.lon0);
    var dlat = Number(g.dlat || 0), dlon = Number(g.dlon || 0);
    var elev = g.elevation;
    var classes = g.classes;
    var mean = Number(g.mean_elevation_m || 0);
    var range = Math.max(1, Number(g.max_elevation_m || 0) - Number(g.min_elevation_m || 0));
    var exag = Number(T.exaggeration) || 0;
    var positions = [];
    var colors = [];
    var c = new THREE.Color();
    function radiusFor(el) { return MARS_RADIUS * (1.0015 + ((Number(el) || mean) - mean) / range * 0.004 * exag); }
    for (var r = 0; r < n; r += 1) {
      for (var q = 0; q < n; q += 1) {
        var cellClass = classes[r][q];
        c.set(slopeColor(cellClass));
        var topLat = lat0 - r * dlat;
        var botLat = lat0 - (r + 1) * dlat;
        var leftLon = lon0 + q * dlon;
        var rightLon = lon0 + (q + 1) * dlon;
        var e = elev[r][q];
        var rad = radiusFor(e);
        var p00 = latLonToVector3(topLat, signedLon(leftLon), rad);
        var p10 = latLonToVector3(topLat, signedLon(rightLon), rad);
        var p01 = latLonToVector3(botLat, signedLon(leftLon), rad);
        var p11 = latLonToVector3(botLat, signedLon(rightLon), rad);
        positions.push(p00.x, p00.y, p00.z, p01.x, p01.y, p01.z, p10.x, p10.y, p10.z);
        positions.push(p10.x, p10.y, p10.z, p01.x, p01.y, p01.z, p11.x, p11.y, p11.z);
        for (var k = 0; k < 6; k += 1) colors.push(c.r, c.g, c.b);
      }
    }
    var geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geo.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    geo.computeVertexNormals();
    var mat = new THREE.MeshBasicMaterial({
      vertexColors: true, transparent: true, opacity: T.opacity,
      side: THREE.DoubleSide, depthWrite: false
    });
    var mesh = new THREE.Mesh(geo, mat);
    mesh.renderOrder = 4;
    mesh.name = 'ares-slope-patch';
    group.add(mesh);
    T.mesh = mesh;

    // Red outlines around >30-degree cells make the no-go barriers legible.
    var hazardPositions = [];
    for (var hr = 0; hr < n; hr += 1) {
      for (var hc = 0; hc < n; hc += 1) {
        if (classes[hr][hc] !== 2 && classes[hr][hc] !== 'no_go') continue;
        var ht = lat0 - hr * dlat, hb = lat0 - (hr + 1) * dlat;
        var hl = lon0 + hc * dlon, hrr = lon0 + (hc + 1) * dlon;
        var he = elev[hr][hc];
        var hrad = radiusFor(he) * 1.00035;
        var a = latLonToVector3(ht, signedLon(hl), hrad);
        var b = latLonToVector3(ht, signedLon(hrr), hrad);
        var d = latLonToVector3(hb, signedLon(hl), hrad);
        var f = latLonToVector3(hb, signedLon(hrr), hrad);
        hazardPositions.push(a.x, a.y, a.z, b.x, b.y, b.z);
        hazardPositions.push(b.x, b.y, b.z, f.x, f.y, f.z);
        hazardPositions.push(f.x, f.y, f.z, d.x, d.y, d.z);
        hazardPositions.push(d.x, d.y, d.z, a.x, a.y, a.z);
      }
    }
    if (hazardPositions.length) {
      var hgeo = new THREE.BufferGeometry();
      hgeo.setAttribute('position', new THREE.Float32BufferAttribute(hazardPositions, 3));
      var hlines = new THREE.LineSegments(hgeo, new THREE.LineBasicMaterial({ color: COLOR.noGo, transparent: true, opacity: 0.9 }));
      hlines.renderOrder = 5;
      group.add(hlines);
    }
    drawSlopeMinimap();
    drawAres2D();
  }

  /* ------------------------------------------------------------------------
     PDS GDS asynchronous MOLA jobs
     ------------------------------------------------------------------------ */
  function bindGds() {
    var submit = $('ares-gds-submit');
    if (submit) submit.addEventListener('click', submitGdsJob);
    var refresh = $('ares-gds-refresh');
    if (refresh) refresh.addEventListener('click', refreshGds);
    var list = $('ares-gds-list');
    if (list) {
      list.addEventListener('click', function (ev) {
        var abort = ev.target.closest('[data-gds-abort]');
        if (!abort) return;
        abortGdsJob(abort.getAttribute('data-gds-abort'));
      });
    }
  }

  async function submitGdsJob() {
    var center = ARES.state.terrain.center || getCameraCenterLatLon();
    if (!center) { toast('Point the camera at Mars first.', true); return; }
    var d = 0.05;
    var west = clamp(eastLon(center.lon) - d, 0, 360);
    var east = clamp(eastLon(center.lon) + d, 0, 360);
    var south = clamp(Number(center.lat) - d, -90, 90);
    var north = clamp(Number(center.lat) + d, -90, 90);
    var btn = $('ares-gds-submit');
    if (btn) { btn.disabled = true; btn.textContent = 'Submitting\u2026'; }
    var url = '/api/nasa/gds/jobs?action=submit&minlat=' + south.toFixed(4) + '&maxlat=' + north.toFixed(4) +
      '&westernlon=' + west.toFixed(4) + '&easternlon=' + east.toFixed(4);
    // The PDS GDS call can take tens of seconds; let it run in the background while
    // the panel polls the job registry, so the UI stays responsive.
    ARES.state.gds.submitting = true;
    fetchJSON(url, null, 180000).then(function () {
      ARES.state.gds.submitting = false;
      refreshGds();
    }).catch(function (err) {
      ARES.state.gds.submitting = false;
      toast('GDS submission failed: ' + err.message, true);
    });
    toast('MOLA query submitted to the PDS Geosciences Node.');
    startGdsPolling();
    setTimeout(refreshGds, 1200);
    setTimeout(function () {
      if (btn) { btn.disabled = false; btn.textContent = 'Submit MOLA query'; }
    }, 1400);
  }

  async function refreshGds() {
    try {
      var data = await fetchJSON('/api/nasa/gds/jobs?action=list', null, 30000);
      ARES.state.gds.jobs = data.jobs || [];
      renderGdsJobs();
      var running = ARES.state.gds.jobs.some(function (j) { return j.state === 'running' || j.state === 'queued'; });
      if (running && !ARES.state.gds.timer) startGdsPolling();
      if (!running && !ARES.state.gds.submitting && ARES.state.gds.timer) {
        clearInterval(ARES.state.gds.timer);
        ARES.state.gds.timer = null;
      }
    } catch (err) {
      var host = $('ares-gds-list');
      if (host && !ARES.state.gds.jobs.length) host.innerHTML = '<div class="ares-note" style="margin-top:6px;color:#fecaca">Job list unavailable: ' + esc(err.message) + '</div>';
    }
  }

  function startGdsPolling() {
    if (ARES.state.gds.timer) return;
    ARES.state.gds.timer = setInterval(refreshGds, 3000);
  }

  async function abortGdsJob(id) {
    try {
      await fetchJSON('/api/nasa/gds/jobs?action=abort&jobid=' + encodeURIComponent(id), null, 30000);
      toast('Abort requested for ' + id + '.');
      refreshGds();
    } catch (err) { toast('Abort failed: ' + err.message, true); }
  }

  function renderGdsJobs() {
    var host = $('ares-gds-list');
    if (!host) return;
    var jobs = ARES.state.gds.jobs || [];
    if (!jobs.length) {
      host.innerHTML = '<div class="ares-note" style="margin-top:6px">No GDS jobs in this server session.</div>';
      return;
    }
    host.innerHTML = jobs.slice(0, 8).map(function (job) {
      var state = job.state || 'unknown';
      var result = job.result || {};
      var files = result.files || [];
      var canAbort = state === 'running' || state === 'queued';
      return '<div class="ares-job">' +
        '<div class="ares-job-top"><span class="ares-job-state ' + esc(state) + '">' + esc(state) + '</span>' +
          '<span class="ares-mono" style="font-size:8.5px;color:#94a3b8">' + esc(job.id) + '</span>' +
          (canAbort ? '<button class="ares-btn ares-danger ares-small" style="margin-left:auto" type="button" data-gds-abort="' + escAttr(job.id) + '">Abort</button>' : '') +
        '</div>' +
        '<div class="ares-job-note">' + esc(job.status_note || job.error || '') + '</div>' +
        (files.length ? '<div class="ares-job-files">' + files.slice(0, 4).map(function (f) {
          return '<a href="' + escAttr(f.url) + '" target="_blank" rel="noopener">' + esc(f.url.split('/').pop()) + ' \u00b7 ' + esc(f.size_kb || '?') + ' kB</a>';
        }).join('') + '</div>' : '') +
      '</div>';
    }).join('');
  }

  /* ------------------------------------------------------------------------
     Cooperative scouting: control, animation, proofs and charts
     ------------------------------------------------------------------------ */
  function bindScout() {
    var run = $('ares-scout-run');
    if (run) run.addEventListener('click', runScout);
    var clear = $('ares-scout-clear');
    if (clear) clear.addEventListener('click', clearScout);
    document.querySelectorAll('[data-ares-preset]').forEach(function (btn) {
      btn.addEventListener('click', function () { applyScoutPreset(btn.getAttribute('data-ares-preset')); });
    });
    var pickStart = $('ares-pick-start');
    if (pickStart) pickStart.addEventListener('click', function () { setPickMode('start'); });
    var pickTarget = $('ares-pick-target');
    if (pickTarget) pickTarget.addEventListener('click', function () { setPickMode('target'); });
    var slider = $('ares-scout-slider');
    if (slider) slider.addEventListener('input', function () {
      stopScoutPlay();
      setScoutIteration(Number(slider.value));
    });
    var play = $('ares-scout-play');
    if (play) play.addEventListener('click', function () {
      if (ARES.state.scout.playing) stopScoutPlay();
      else playScout();
    });
    var prev = $('ares-scout-prev');
    if (prev) prev.addEventListener('click', function () {
      stopScoutPlay();
      setScoutIteration(ARES.state.scout.iteration - 1);
    });
    var next = $('ares-scout-next');
    if (next) next.addEventListener('click', function () {
      stopScoutPlay();
      setScoutIteration(ARES.state.scout.iteration + 1);
    });
    var hazards = $('ares-scout-hazards');
    if (hazards) hazards.addEventListener('change', function () {
      ARES.state.scout.hazards = hazards.checked;
      renderScoutOverlay();
    });
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && ARES.state.scout.picking) {
        setPickMode(null);
        toast('Coordinate picking cancelled.');
      }
    });
  }

  function applyScoutPreset(name) {
    var presets = {
      jezero: [18.4446, 77.4508, 18.5100, 77.3500],
      gale: [-4.5895, 137.4417, -4.6500, 137.3800],
      mawrth: [22.3000, -16.5000, 22.3600, -16.6200],
      long: [18.4446, 77.4508, 18.5500, 77.4000]
    };
    var p = presets[name];
    if (!p) return;
    setValue('ares-start-lat', p[0]);
    setValue('ares-start-lon', p[1]);
    setValue('ares-target-lat', p[2]);
    setValue('ares-target-lon', p[3]);
    toast('Scouting preset loaded: ' + name + '.');
  }

  function setValue(id, value) {
    var node = $(id);
    if (node) node.value = String(value);
  }
  function numberValue(id, fallback) {
    var node = $(id);
    var value = node ? Number(node.value) : NaN;
    return isFinite(value) ? value : fallback;
  }

  async function runScout() {
    if (ARES.state.scout.busy) return;
    var startLat = numberValue('ares-start-lat', 18.4446);
    var startLon = numberValue('ares-start-lon', 77.4508);
    var targetLat = numberValue('ares-target-lat', 18.51);
    var targetLon = numberValue('ares-target-lon', 77.35);
    var sensorRadius = clamp(numberValue('ares-sensor-radius', 300), 80, 1200);
    var maxIterations = clamp(Math.round(numberValue('ares-max-iterations', 18)), 2, 30);
    if (Math.abs(startLat) > 90 || Math.abs(targetLat) > 90) { toast('Latitude must be between -90 and 90 degrees.', true); return; }
    stopScoutPlay();
    ARES.state.scout.busy = true;
    var btn = $('ares-scout-run');
    if (btn) { btn.disabled = true; btn.textContent = 'Planning\u2026'; }
    var status = $('ares-scout-status');
    if (status) status.innerHTML = '<div class="ares-outcome working"><div class="ares-outcome-icon">\u25c9</div><div><div class="ares-outcome-title">COOPERATIVE IPP RUNNING</div><div class="ares-outcome-sub">Reading the DEM, expanding the scout sensor corridor, and bounding the follower cost\u2026</div></div></div>';
    try {
      var url = '/api/scouting/plan?start_lat=' + encodeURIComponent(startLat.toFixed(6)) +
        '&start_lon=' + encodeURIComponent(signedLon(startLon).toFixed(6)) +
        '&target_lat=' + encodeURIComponent(targetLat.toFixed(6)) +
        '&target_lon=' + encodeURIComponent(signedLon(targetLon).toFixed(6)) +
        '&sensor_radius=' + encodeURIComponent(sensorRadius) +
        '&max_iterations=' + encodeURIComponent(maxIterations);
      var data = await fetchJSON(url, null, 180000);
      if (!data || data.status === 'error') throw new Error((data && data.message) || 'Planner returned no result');
      ARES.state.scout.result = data;
      ARES.state.scout.iteration = (data.iterations && data.iterations.length > 1) ? 0 : Math.max(0, (data.iterations || []).length - 1);
      renderScoutPanel();
      renderScoutOverlay();
      drawScoutCharts();
      focusScoutAOI(data);
      if (data.iterations && data.iterations.length > 2) playScout();
      toast(scoutOutcomeLabel(data.outcome).title + (data.summary && data.summary.optimality_gap_pct != null ? ' \u00b7 gap ' + Number(data.summary.optimality_gap_pct).toFixed(2) + '%' : ''));
    } catch (err) {
      if (status) status.innerHTML = '<div class="ares-outcome infeasible"><div class="ares-outcome-icon">\u2715</div><div><div class="ares-outcome-title">PLANNER ERROR</div><div class="ares-outcome-sub">' + esc(err.message) + '</div></div></div>';
      toast('Scouting failed: ' + err.message, true);
    } finally {
      ARES.state.scout.busy = false;
      if (btn) { btn.disabled = false; btn.textContent = 'Run cooperative plan'; }
    }
  }

  function clearScout() {
    stopScoutPlay();
    ARES.state.scout.result = null;
    ARES.state.scout.iteration = 0;
    clearGroup(ARES.state.layers.scout);
    var status = $('ares-scout-status');
    if (status) status.innerHTML = '<div class="ares-note">No plan loaded. Choose a start and target, then run the cooperative planner.</div>';
    var metrics = $('ares-scout-metrics');
    if (metrics) metrics.innerHTML = '';
    var proof = $('ares-scout-proof');
    if (proof) { proof.className = ''; proof.innerHTML = ''; }
    var source = $('ares-scout-source');
    if (source) source.innerHTML = '';
    var slider = $('ares-scout-slider');
    if (slider) { slider.max = '1'; slider.value = '0'; }
    setText('ares-scout-step-label', '0 / 0');
    drawScoutCharts();
    drawAres2D();
  }

  function scoutOutcomeLabel(outcome) {
    var key = String(outcome || '').toUpperCase();
    if (key === 'OPTIMAL_PROVEN') return { cls: 'optimal', icon: '\u2713', title: 'OPTIMALITY PROVEN', sub: 'The feasible and optimistic paths have converged to the same route.', label: 'Optimal' };
    if (key === 'INFEASIBILITY_PROVEN') return { cls: 'infeasible', icon: '\u2715', title: 'INFEASIBILITY PROVEN', sub: 'No route can satisfy the slope limit within the searched terrain.', label: 'Infeasible' };
    if (key === 'MAX_ITERATIONS') return { cls: 'working', icon: '\u25c9', title: 'ITERATION LIMIT', sub: 'The scout budget expired before the lower bound could be certified.', label: 'Budget limited' };
    return { cls: 'working', icon: '\u25c9', title: key || 'PLANNER RESULT', sub: 'The planner returned a partial result.', label: key || 'Result' };
  }

  function renderScoutPanel() {
    var result = ARES.state.scout.result;
    if (!result) return;
    var meta = scoutOutcomeLabel(result.outcome);
    var status = $('ares-scout-status');
    if (status) {
      status.innerHTML = '<div class="ares-outcome ' + meta.cls + '"><div class="ares-outcome-icon">' + meta.icon + '</div><div><div class="ares-outcome-title">' + esc(meta.title) + '</div><div class="ares-outcome-sub">' + esc(meta.sub) + '</div></div></div>';
    }
    var snapshot = (result.iterations && result.iterations[ARES.state.scout.iteration]) || result.iterations[(result.iterations || []).length - 1] || {};
    var s = result.summary || {};
    var feasibleKm = snapshot.feasible_distance_km != null ? snapshot.feasible_distance_km : s.feasible_distance_km;
    var optimisticKm = snapshot.optimistic_distance_km != null ? snapshot.optimistic_distance_km : s.optimistic_distance_km;
    var gap = snapshot.gap_pct != null ? snapshot.gap_pct : s.optimality_gap_pct;
    var known = snapshot.known_fraction != null ? snapshot.known_fraction : s.known_fraction;
    var metrics = $('ares-scout-metrics');
    if (metrics) {
      metrics.innerHTML = '<div class="ares-metric-grid">' +
        '<div class="ares-metric"><div class="k">Feasible route</div><div class="v" style="color:#22c55e">' + (feasibleKm != null ? Number(feasibleKm).toFixed(2) + ' km' : 'UNVERIFIED') + '</div></div>' +
        '<div class="ares-metric"><div class="k">Optimistic lower bound</div><div class="v" style="color:#38bdf8">' + (optimisticKm != null ? Number(optimisticKm).toFixed(2) + ' km' : '\u2014') + '</div></div>' +
        '<div class="ares-metric"><div class="k">Optimality gap</div><div class="v" style="color:#f472b6">' + (gap != null ? Number(gap).toFixed(3) + '%' : '\u2014') + '</div></div>' +
        '<div class="ares-metric"><div class="k">Known terrain</div><div class="v">' + (known != null ? (Number(known) * 100).toFixed(2) + '%' : '\u2014') + '</div></div>' +
        '<div class="ares-metric"><div class="k">Scout distance</div><div class="v" style="color:#fbbf24">' + (s.scout_distance_km != null ? Number(s.scout_distance_km).toFixed(2) + ' km' : '\u2014') + '</div></div>' +
        '<div class="ares-metric"><div class="k">Scout sorties</div><div class="v">' + (s.scout_sorties != null ? s.scout_sorties : '\u2014') + '</div></div>' +
      '</div>';
    }
    var iterations = result.iterations || [];
    var slider = $('ares-scout-slider');
    if (slider) {
      slider.max = String(Math.max(0, iterations.length - 1));
      slider.value = String(ARES.state.scout.iteration);
    }
    setText('ares-scout-step-label', (ARES.state.scout.iteration + 1) + ' / ' + Math.max(1, iterations.length));
    var proof = $('ares-scout-proof');
    if (proof) {
      var p = result.proof || {};
      var isGood = p.optimality_proven === true;
      var isBad = p.infeasibility_proven === true;
      proof.className = 'ares-proof' + (isBad ? ' bad' : '');
      proof.innerHTML = '<b>' + (isGood ? 'Certificate of optimality' : (isBad ? 'Certificate of infeasibility' : 'Search status')) + '</b><br>' +
        esc(p.reason || meta.sub) +
        (p.optimality_gap_pct != null ? '<br>Gap: ' + Number(p.optimality_gap_pct).toFixed(3) + '%' : '');
    }
    var source = $('ares-scout-source');
    if (source) {
      var t = result.terrain || {};
      var aoi = result.aoi || {};
      source.innerHTML = '<b>' + esc(t.source || 'Terrain') + '</b> \u00b7 ' + (t.is_real_dem ? '<span class="ares-green">REAL DEM</span>' : '<span class="ares-amber">FALLBACK</span>') +
        '<br>AOI ' + Number(aoi.size_km || 0).toFixed(2) + ' km \u00b7 ' + (aoi.n || '--') + '\u00d7' + (aoi.n || '--') + ' grid \u00b7 sensor ' + Number(s.sensor_radius_m || 0).toFixed(0) + ' m' +
        '<br>Slope limit ' + Number(s.slope_limit_deg || 30).toFixed(0) + '\u00b0 \u00b7 planner ' + esc(result.planner || 'cooperative IPP') +
        (t.source_detail ? '<br>' + esc(t.source_detail) : '');
    }
  }

  function setScoutIteration(value) {
    var result = ARES.state.scout.result;
    if (!result) return;
    var max = Math.max(0, (result.iterations || []).length - 1);
    ARES.state.scout.iteration = clamp(Math.round(value), 0, max);
    renderScoutPanel();
    renderScoutOverlay();
    drawScoutCharts();
  }

  function playScout() {
    var result = ARES.state.scout.result;
    if (!result || !result.iterations || result.iterations.length < 2) return;
    stopScoutPlay();
    ARES.state.scout.playing = true;
    var play = $('ares-scout-play');
    if (play) play.textContent = '\u275a\u275a Pause';
    if (ARES.state.scout.iteration >= result.iterations.length - 1) ARES.state.scout.iteration = 0;
    setScoutIteration(ARES.state.scout.iteration);
    ARES.state.scout.timer = setInterval(function () {
      var max = result.iterations.length - 1;
      if (ARES.state.scout.iteration >= max) {
        stopScoutPlay();
        return;
      }
      setScoutIteration(ARES.state.scout.iteration + 1);
    }, 950);
  }

  function stopScoutPlay() {
    var S = ARES.state.scout;
    if (S.timer) { clearInterval(S.timer); S.timer = null; }
    S.playing = false;
    var play = $('ares-scout-play');
    if (play) play.textContent = '\u25b6 Play';
  }

  function addLine3D(points, color, dashed, group) {
    if (!points || points.length < 2) return;
    var verts = points.map(function (p) { return latLonToVector3(Number(p.lat), signedLon(p.lon == null ? p.lon_east : p.lon), MARS_RADIUS * 1.0045); });
    var geo = new THREE.BufferGeometry().setFromPoints(verts);
    var mat;
    if (dashed) {
      mat = new THREE.LineDashedMaterial({ color: color, dashSize: 0.0055, gapSize: 0.0035, transparent: true, opacity: 0.95 });
    } else {
      mat = new THREE.LineBasicMaterial({ color: color, transparent: true, opacity: 0.98 });
    }
    var line = new THREE.Line(geo, mat);
    if (dashed) line.computeLineDistances();
    line.renderOrder = 8;
    group.add(line);
  }

  var ARES_DOT_TEXTURE = null;

  function aresDotTexture() {
    if (ARES_DOT_TEXTURE) return ARES_DOT_TEXTURE;
    var canvas = document.createElement('canvas');
    canvas.width = 64;
    canvas.height = 64;
    var ctx = canvas.getContext('2d');
    var glow = ctx.createRadialGradient(32, 32, 1, 32, 32, 31);
    glow.addColorStop(0.0, 'rgba(255,255,255,1)');
    glow.addColorStop(0.55, 'rgba(255,255,255,0.95)');
    glow.addColorStop(0.82, 'rgba(255,255,255,0.35)');
    glow.addColorStop(1.0, 'rgba(255,255,255,0)');
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(32, 32, 31, 0, Math.PI * 2);
    ctx.fill();
    ARES_DOT_TEXTURE = new THREE.CanvasTexture(canvas);
    if ('SRGBColorSpace' in THREE) ARES_DOT_TEXTURE.colorSpace = THREE.SRGBColorSpace;
    return ARES_DOT_TEXTURE;
  }

  // Screen-space point: stays small at every zoom, so route lines stay readable.
  function addPoint3D(lat, lon, sizePx, color, group, opacity) {
    var geo = new THREE.BufferGeometry().setFromPoints([
      latLonToVector3(Number(lat), signedLon(lon), MARS_RADIUS * 1.0055)
    ]);
    var mat = new THREE.PointsMaterial({
      color: color,
      size: Math.max(1, Number(sizePx) || 2),
      sizeAttenuation: false,
      map: aresDotTexture(),
      transparent: true,
      opacity: opacity == null ? 0.95 : opacity,
      alphaTest: 0.04,
      depthWrite: false
    });
    var points = new THREE.Points(geo, mat);
    points.renderOrder = 9;
    group.add(points);
    return points;
  }

  function renderScoutOverlay() {
    var result = ARES.state.scout.result;
    var group = ARES.state.layers.scout;
    if (!group) return;
    clearGroup(group);
    if (!result) { drawAres2D(); return; }
    var iterations = result.iterations || [];
    var snapshot = iterations[ARES.state.scout.iteration] || iterations[iterations.length - 1] || {};
    var optimistic = snapshot.optimistic_path || result.optimistic_path || [];
    var feasible = snapshot.feasible_path || [];
    addLine3D(optimistic, COLOR.cyan, true, group);
    if (feasible.length) addLine3D(feasible, COLOR.green, false, group);

    var trajectory = snapshot.scout_trajectory || (result.scout_trajectory || []).filter(function (p) {
      return p.iteration == null || Number(p.iteration) <= ARES.state.scout.iteration;
    });
    if (trajectory && trajectory.length) {
      addLine3D(trajectory, COLOR.amber, false, group);
      trajectory.forEach(function (p) {
        addPoint3D(p.lat, p.lon, 2.4, p.iteration === 0 ? COLOR.green : COLOR.amber, group, 0.9);
      });
    }

    if (ARES.state.scout.hazards && result.hazard_cells && result.hazard_cells.length) {
      var positions = result.hazard_cells.map(function (h) {
        var v = latLonToVector3(Number(h.lat), signedLon(h.lon), MARS_RADIUS * 1.0048);
        return v.x + ',' + v.y + ',' + v.z;
      });
      var pos = [];
      positions.forEach(function (s) { s.split(',').forEach(function (n) { pos.push(Number(n)); }); });
      var geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
      var hazards = new THREE.Points(geo, new THREE.PointsMaterial({ color: COLOR.noGo, size: 2.2, sizeAttenuation: false, map: aresDotTexture(), transparent: true, opacity: 0.55, alphaTest: 0.04, depthWrite: false }));
      hazards.renderOrder = 7;
      group.add(hazards);
    }

    var start = result.start || {};
    var target = result.target || {};
    if (start.lat != null) {
      addPoint3D(start.lat, start.lon == null ? start.lon_east : start.lon, 7, '#22c55e', group, 1);
    }
    if (target.lat != null) {
      addPoint3D(target.lat, target.lon == null ? target.lon_east : target.lon, 7, '#f472b6', group, 1);
    }
    drawAres2D();
  }

  function focusScoutAOI(result) {
    if (!result || typeof flyToCoordinate !== 'function') return;
    var start = result.start || {};
    var target = result.target || {};
    if (start.lat == null || target.lat == null) return;
    var midLat = (Number(start.lat) + Number(target.lat)) / 2;
    var startLon = signedLon(start.lon == null ? start.lon_east : start.lon);
    var targetLon = signedLon(target.lon == null ? target.lon_east : target.lon);
    var midLon = startLon + signedLon(targetLon - startLon) / 2;
    // Fly to rover scale: make the AOI cover roughly 40% of the viewport
    // instead of leaving a 7 km route as a few pixels at orbital altitude.
    if (typeof controls !== 'undefined' && controls) {
      controls.minDistance = Math.min(controls.minDistance || 1.08, 1.0035);
    }
    var sizeKm = Math.max(1.0, Number((result.aoi && result.aoi.size_km) || 8.0));
    var fovRad = ((typeof camera !== 'undefined' && camera.fov) ? camera.fov : 45) * Math.PI / 180;
    var alt = (sizeKm * 1000) / (3396190 * Math.max(0.35, fovRad) * 0.20);
    var minDist = (typeof controls !== 'undefined' && controls.minDistance) ? controls.minDistance : 1.0035;
    var targetDist = clamp(1.0 + alt, minDist, 1.35);
    flyToCoordinate(midLat, midLon, targetDist);
  }

  function haversineKm(a, b) {
    var R = 3396190;
    var la1 = Number(a.lat) * Math.PI / 180;
    var la2 = Number(b.lat) * Math.PI / 180;
    var dLat = la2 - la1;
    var dLon = (Number(b.lon == null ? b.lon_east : b.lon) - Number(a.lon == null ? a.lon_east : a.lon)) * Math.PI / 180;
    var h = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(la1) * Math.cos(la2) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return 2 * R * Math.asin(Math.min(1, Math.sqrt(h))) / 1000;
  }

  function setupCanvas(canvas, height) {
    if (!canvas) return null;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var cssW = canvas.clientWidth || canvas.parentElement && canvas.parentElement.clientWidth || 330;
    if (cssW < 100) cssW = 330;
    canvas.width = Math.round(cssW * dpr);
    canvas.height = Math.round(height * dpr);
    canvas.style.height = height + 'px';
    var ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cssW, height);
    return { ctx: ctx, w: cssW, h: height };
  }

  function drawScoutCharts() {
    drawScoutMinimap();
    drawProfileChart();
    drawConvergenceChart();
  }

  function drawScoutMinimap() {
    var canvas = $('ares-scout-minimap');
    if (!canvas) return;
    var setup = setupCanvas(canvas, 168);
    if (!setup) return;
    var ctx = setup.ctx, w = setup.w, h = setup.h;
    ctx.fillStyle = 'rgba(2,6,14,0.55)';
    ctx.fillRect(0, 0, w, h);
    var result = ARES.state.scout.result;
    if (!result) {
      ctx.fillStyle = '#64748b';
      ctx.font = '10px monospace';
      ctx.fillText('Run a cooperative plan to see the local AOI.', 12, h / 2);
      setText('ares-minimap-legend', '\u2014');
      return;
    }
    var aoi = result.aoi || {};
    var lat0 = Number(aoi.lat0);
    var lon0 = Number(aoi.lon0);
    var size = Number(aoi.size_deg) || 0.05;
    if (!isFinite(lat0) || !isFinite(lon0)) {
      var all = (result.optimistic_path || []).concat(result.feasible_path || []);
      if (!all.length) return;
      var lats = all.map(function (p) { return Number(p.lat); });
      var lons = all.map(function (p) { return signedLon(p.lon == null ? p.lon_east : p.lon); });
      lat0 = Math.max.apply(null, lats) + 0.01;
      lon0 = Math.min.apply(null, lons) - 0.01;
      size = Math.max(Math.max.apply(null, lats) - Math.min.apply(null, lats), Math.max.apply(null, lons) - Math.min.apply(null, lons)) + 0.02;
    }
    var pad = 9;
    var lon0e = eastLon(lon0);
    function x(lon) { return pad + ((eastLon(lon) - lon0e) / size) * (w - pad * 2); }
    function y(lat) { return pad + ((lat0 - Number(lat)) / size) * (h - pad * 2); }
    ctx.strokeStyle = 'rgba(148,163,184,0.18)';
    ctx.lineWidth = 1;
    for (var gi = 0; gi <= 4; gi += 1) {
      var gx = pad + (gi / 4) * (w - pad * 2);
      var gy = pad + (gi / 4) * (h - pad * 2);
      ctx.beginPath(); ctx.moveTo(gx, pad); ctx.lineTo(gx, h - pad); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(pad, gy); ctx.lineTo(w - pad, gy); ctx.stroke();
    }
    ctx.strokeStyle = 'rgba(56,189,248,0.35)';
    ctx.strokeRect(pad, pad, w - pad * 2, h - pad * 2);
    var snap = (result.iterations || [])[ARES.state.scout.iteration] || (result.iterations || [])[(result.iterations || []).length - 1] || {};
    if (ARES.state.scout.hazards && result.hazard_cells) {
      ctx.fillStyle = 'rgba(239,68,68,0.8)';
      result.hazard_cells.forEach(function (hz) {
        ctx.beginPath(); ctx.arc(x(hz.lon), y(hz.lat), 1.25, 0, Math.PI * 2); ctx.fill();
      });
    }
    function drawPath(points, color, dashed, width) {
      if (!points || points.length < 2) return;
      ctx.save();
      ctx.strokeStyle = color;
      ctx.lineWidth = width || 2;
      if (dashed) ctx.setLineDash([4, 3]);
      ctx.beginPath();
      points.forEach(function (p, idx) {
        var px = x(p.lon == null ? p.lon_east : p.lon), py = y(p.lat);
        if (idx === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      });
      ctx.stroke();
      ctx.restore();
    }
    drawPath(snap.optimistic_path, '#38bdf8', true, 1.5);
    drawPath(snap.feasible_path, '#22c55e', false, 2.4);
    var traj = snap.scout_trajectory || (result.scout_trajectory || []).filter(function (p) { return p.iteration == null || Number(p.iteration) <= ARES.state.scout.iteration; });
    drawPath(traj, '#fbbf24', false, 1.4);
    if (traj) traj.forEach(function (p) {
      ctx.fillStyle = p.iteration === 0 ? '#22c55e' : '#fbbf24';
      ctx.beginPath(); ctx.arc(x(p.lon), y(p.lat), 1.6, 0, Math.PI * 2); ctx.fill();
    });
    var start = result.start || {}, target = result.target || {};
    if (start.lat != null) {
      ctx.fillStyle = '#22c55e';
      ctx.beginPath(); ctx.arc(x(start.lon == null ? start.lon_east : start.lon), y(start.lat), 3, 0, Math.PI * 2); ctx.fill();
    }
    if (target.lat != null) {
      ctx.fillStyle = '#f472b6';
      ctx.beginPath(); ctx.arc(x(target.lon == null ? target.lon_east : target.lon), y(target.lat), 3, 0, Math.PI * 2); ctx.fill();
    }
    ctx.fillStyle = '#94a3b8';
    ctx.font = '8px monospace';
    ctx.fillText('AOI ' + Number(aoi.size_km || 0).toFixed(2) + ' km', pad + 3, h - pad - 3);
    setText('ares-minimap-legend', snap.feasible_path ? 'feasible + optimistic' : 'optimistic only');
  }

  function drawProfileChart() {
    var canvas = $('ares-profile-canvas');
    if (!canvas) return;
    var setup = setupCanvas(canvas, 150);
    if (!setup) return;
    var ctx = setup.ctx, w = setup.w, h = setup.h;
    var result = ARES.state.scout.result;
    var snapshot = result && result.iterations && result.iterations[ARES.state.scout.iteration];
    var path = snapshot ? (snapshot.feasible_path || snapshot.optimistic_path) : (result && (result.feasible_path || result.optimistic_path));
    ctx.fillStyle = 'rgba(2,6,14,0.42)';
    ctx.fillRect(0, 0, w, h);
    if (!path || path.length < 2) {
      ctx.fillStyle = '#64748b';
      ctx.font = '10px monospace';
      ctx.fillText('No profile yet \u2014 run or step the planner.', 12, h / 2);
      setText('ares-profile-legend', '\u2014');
      return;
    }
    var padL = 33, padR = 30, padT = 12, padB = 20;
    var distances = [0];
    var maxDist = 0;
    for (var pi = 1; pi < path.length; pi += 1) {
      maxDist += haversineKm(path[pi - 1], path[pi]);
      distances.push(maxDist);
    }
    if (!isFinite(maxDist) || maxDist <= 0) maxDist = Number(path[path.length - 1].distance_km || 1);
    var elevs = path.map(function (p) { return Number(p.elev_m); }).filter(isFinite);
    var slopes = path.map(function (p) { return Number(p.slope_deg); }).filter(isFinite);
    var eMin = Math.min.apply(null, elevs), eMax = Math.max.apply(null, elevs);
    if (!isFinite(eMin) || eMax - eMin < 1) { eMin -= 5; eMax += 5; }
    var sMax = Math.max(40, Math.ceil(Math.max.apply(null, slopes) / 10) * 10);
    function x(d) { return padL + (d / maxDist) * (w - padL - padR); }
    function yE(e) { return padT + (1 - (e - eMin) / (eMax - eMin)) * (h - padT - padB); }
    function yS(s) { return padT + (1 - s / sMax) * (h - padT - padB); }
    ctx.strokeStyle = 'rgba(148,163,184,0.16)';
    ctx.lineWidth = 1;
    for (var i = 0; i <= 4; i += 1) {
      var yy = padT + (i / 4) * (h - padT - padB);
      ctx.beginPath(); ctx.moveTo(padL, yy); ctx.lineTo(w - padR, yy); ctx.stroke();
    }
    ctx.fillStyle = '#64748b';
    ctx.font = '8px monospace';
    ctx.textAlign = 'right';
    ctx.fillText(eMax.toFixed(0) + 'm', padL - 4, padT + 3);
    ctx.fillText(eMin.toFixed(0) + 'm', padL - 4, h - padB + 2);
    ctx.textAlign = 'left';
    ctx.fillStyle = '#f59e0b';
    ctx.fillText(sMax + '\u00b0', w - padR + 4, padT + 3);
    ctx.fillText('0\u00b0', w - padR + 4, h - padB + 2);

    ctx.strokeStyle = 'rgba(239,68,68,0.65)';
    ctx.setLineDash([4, 3]);
    var y30 = yS(30);
    ctx.beginPath(); ctx.moveTo(padL, y30); ctx.lineTo(w - padR, y30); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = 'rgba(239,68,68,0.8)';
    ctx.font = '7.5px monospace';
    ctx.fillText('30\u00b0 limit', padL + 2, y30 - 2);

    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    path.forEach(function (p, idx) {
      var px = x(distances[idx]);
      var py = yE(Number(p.elev_m));
      if (idx === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    });
    ctx.stroke();

    ctx.strokeStyle = '#fbbf24';
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    path.forEach(function (p, idx) {
      var px = x(distances[idx]);
      var py = yS(Number(p.slope_deg));
      if (idx === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    });
    ctx.stroke();
    ctx.fillStyle = '#94a3b8';
    ctx.font = '8px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(maxDist.toFixed(2) + ' km', (padL + w - padR) / 2, h - 4);
    ctx.textAlign = 'left';
    setText('ares-profile-legend', (snapshot && snapshot.feasible_path ? 'feasible' : 'optimistic') + ' \u00b7 ' + maxDist.toFixed(2) + ' km');
  }

  function drawConvergenceChart() {
    var canvas = $('ares-convergence-canvas');
    if (!canvas) return;
    var setup = setupCanvas(canvas, 128);
    if (!setup) return;
    var ctx = setup.ctx, w = setup.w, h = setup.h;
    var result = ARES.state.scout.result;
    var conv = (result && result.convergence) || [];
    ctx.fillStyle = 'rgba(2,6,14,0.42)';
    ctx.fillRect(0, 0, w, h);
    if (!conv.length) {
      ctx.fillStyle = '#64748b';
      ctx.font = '10px monospace';
      ctx.fillText('No convergence history yet.', 12, h / 2);
      setText('ares-gap-legend', '\u2014');
      return;
    }
    var padL = 33, padR = 30, padT = 12, padB = 20;
    var costs = [];
    conv.forEach(function (c) {
      if (c.feasible_cost != null) costs.push(Number(c.feasible_cost));
      if (c.optimistic_cost != null) costs.push(Number(c.optimistic_cost));
    });
    var cMin = Math.min.apply(null, costs), cMax = Math.max.apply(null, costs);
    if (!isFinite(cMin) || cMax - cMin < 1) { cMin -= 10; cMax += 10; }
    var n = Math.max(1, conv.length - 1);
    function x(i) { return padL + (i / n) * (w - padL - padR); }
    function y(c) { return padT + (1 - (c - cMin) / (cMax - cMin)) * (h - padT - padB); }
    ctx.strokeStyle = 'rgba(148,163,184,0.16)';
    ctx.lineWidth = 1;
    for (var i = 0; i <= 4; i += 1) {
      var yy = padT + (i / 4) * (h - padT - padB);
      ctx.beginPath(); ctx.moveTo(padL, yy); ctx.lineTo(w - padR, yy); ctx.stroke();
    }
    ctx.fillStyle = '#64748b';
    ctx.font = '8px monospace';
    ctx.textAlign = 'right';
    ctx.fillText(cMax.toFixed(0), padL - 4, padT + 3);
    ctx.fillText(cMin.toFixed(0), padL - 4, h - padB + 2);
    ctx.textAlign = 'left';

    function line(key, color) {
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      var started = false;
      conv.forEach(function (c, idx) {
        if (c[key] == null) { started = false; return; }
        var px = x(idx), py = y(Number(c[key]));
        if (!started) { ctx.moveTo(px, py); started = true; } else ctx.lineTo(px, py);
      });
      ctx.stroke();
    }
    line('optimistic_cost', '#38bdf8');
    line('feasible_cost', '#22c55e');

    var current = Math.min(ARES.state.scout.iteration, conv.length - 1);
    ctx.strokeStyle = 'rgba(255,255,255,0.45)';
    ctx.setLineDash([3, 3]);
    ctx.beginPath(); ctx.moveTo(x(current), padT); ctx.lineTo(x(current), h - padB); ctx.stroke();
    ctx.setLineDash([]);

    var gap = conv[current] && conv[current].gap_pct;
    ctx.fillStyle = gap != null ? '#f472b6' : '#94a3b8';
    ctx.font = 'bold 9px monospace';
    ctx.textAlign = 'right';
    ctx.fillText(gap != null ? Number(gap).toFixed(3) + '% gap' : 'gap unverified', w - 4, padT + 9);
    ctx.textAlign = 'left';
    ctx.fillStyle = '#94a3b8';
    ctx.font = '8px monospace';
    ctx.fillText('iteration ' + current, padL, h - 4);
    setText('ares-gap-legend', gap != null ? Number(gap).toFixed(2) + '% gap' : 'unverified');
  }

  /* ------------------------------------------------------------------------
     Camera / canvas coordinate helpers and map picking
     ------------------------------------------------------------------------ */
  var aresRaycaster = new THREE.Raycaster();

  function getCameraCenterLatLon() {
    try {
      if (typeof appMode !== 'undefined' && appMode === '2D' && typeof flatCanvas !== 'undefined' && flatCanvas) {
        return flatCanvasLatLon(flatCanvas.width / 2, flatCanvas.height / 2);
      }
      if (!camera) return null;
      var v = camera.position.clone().normalize();
      var ll = vector3ToLatLon(v);
      return { lat: ll.lat, lon: eastLon(ll.lon) };
    } catch (err) { return null; }
  }

  function flatCanvasLatLon(px, py) {
    if (typeof flatCanvas === 'undefined' || !flatCanvas || !flatImg || !flatImg.complete || !flatImg.naturalWidth) return null;
    var aspect = flatImg.naturalWidth / flatImg.naturalHeight;
    var drawW = flatCanvas.width * flatZoom;
    var drawH = (flatCanvas.width / aspect) * flatZoom;
    var drawX = (flatCanvas.width - drawW) / 2 + flatPanX;
    var drawY = (flatCanvas.height - drawH) / 2 + flatPanY;
    var lon = ((px - drawX) / drawW) * 360 - 180;
    var lat = 90 - ((py - drawY) / drawH) * 180;
    if (lat < -90 || lat > 90 || lon < -180 || lon > 180) return null;
    return { lat: lat, lon: lon };
  }

  function canvasLatLon(clientX, clientY) {
    if (typeof appMode !== 'undefined' && appMode === '2D' && typeof flatCanvas !== 'undefined' && flatCanvas) {
      var fr = flatCanvas.getBoundingClientRect();
      return flatCanvasLatLon(clientX - fr.left, clientY - fr.top);
    }
    if (!renderer || !renderer.domElement || !camera || !marsGlobe) return null;
    var rect = renderer.domElement.getBoundingClientRect();
    var ndc = new THREE.Vector2(
      ((clientX - rect.left) / rect.width) * 2 - 1,
      -((clientY - rect.top) / rect.height) * 2 + 1
    );
    aresRaycaster.setFromCamera(ndc, camera);
    var hits = aresRaycaster.intersectObject(marsGlobe);
    if (!hits.length) return null;
    var ll = vector3ToLatLon(hits[0].point);
    return { lat: ll.lat, lon: ll.lon };
  }

  function bindCursor() {
    var last = 0;
    function onMove(ev) {
      var now = performance.now();
      if (now - last < 70) return;
      last = now;
      var ll = canvasLatLon(ev.clientX, ev.clientY);
      if (!ll) return;
      ARES.state.time.cursorLat = ll.lat;
      ARES.state.time.cursorLon = eastLon(ll.lon);
    }
    if (renderer && renderer.domElement) renderer.domElement.addEventListener('mousemove', onMove, { passive: true });
    if (typeof flatCanvas !== 'undefined' && flatCanvas) flatCanvas.addEventListener('mousemove', onMove, { passive: true });
  }

  function setPickMode(mode) {
    var S = ARES.state.scout;
    S.picking = mode || null;
    var banner = $('ares-pick-banner');
    document.body.classList.toggle('ares-picking', !!mode);
    if (banner) {
      banner.classList.toggle('show', !!mode);
      banner.textContent = mode ? ('Click the globe to set the ' + mode + ' coordinate \u00b7 Esc to cancel') : '';
    }
    if (mode) toast('Pick the ' + mode + ' coordinate on the globe.');
  }

  function bindPicking() {
    function onPick(ev) {
      if (!ARES.state.scout.picking) return;
      var ll = canvasLatLon(ev.clientX, ev.clientY);
      if (!ll) return;
      ev.preventDefault();
      ev.stopPropagation();
      if (ev.stopImmediatePropagation) ev.stopImmediatePropagation();
      var mode = ARES.state.scout.picking;
      if (mode === 'start') {
        setValue('ares-start-lat', ll.lat.toFixed(6));
        setValue('ares-start-lon', signedLon(ll.lon).toFixed(6));
      } else {
        setValue('ares-target-lat', ll.lat.toFixed(6));
        setValue('ares-target-lon', signedLon(ll.lon).toFixed(6));
      }
      setPickMode(null);
      toast('Picked ' + mode + ': ' + fmtCoord(ll.lat, ll.lon));
    }
    if (renderer && renderer.domElement) renderer.domElement.addEventListener('pointerup', onPick, true);
    if (typeof flatCanvas !== 'undefined' && flatCanvas) flatCanvas.addEventListener('pointerup', onPick, true);
  }

  /* ------------------------------------------------------------------------
     2D map overlays (appended to the existing flat Mars map)
     ------------------------------------------------------------------------ */
  var ARES_2D_MAP = { drawX: 0, drawY: 0, drawW: 0, drawH: 0 };

  function drawAres2D() {
    try {
      if (typeof appMode === 'undefined' || appMode !== '2D' || typeof flatCanvas === 'undefined' || !flatCanvas) return;
      if (!flatImg || !flatImg.complete || !flatImg.naturalWidth) return;
      var ctx = flatCanvas.getContext('2d');
      var aspect = flatImg.naturalWidth / flatImg.naturalHeight;
      var drawW = flatCanvas.width * flatZoom;
      var drawH = (flatCanvas.width / aspect) * flatZoom;
      var drawX = (flatCanvas.width - drawW) / 2 + flatPanX;
      var drawY = (flatCanvas.height - drawH) / 2 + flatPanY;
      ARES_2D_MAP = { drawX: drawX, drawY: drawY, drawW: drawW, drawH: drawH };
      function px(lon) { return drawX + ((signedLon(lon) + 180) / 360) * drawW; }
      function py(lat) { return drawY + ((90 - lat) / 180) * drawH; }

      var g = ARES.state.terrain.grid;
      if (g && g.elevation && g.classes) {
        var n = Number(g.n) || 0;
        var lat0 = Number(g.lat0), lon0 = Number(g.lon0);
        var dlat = Number(g.dlat), dlon = Number(g.dlon);
        ctx.save();
        ctx.globalAlpha = 0.42;
        for (var r = 0; r < n; r += 1) {
          for (var c = 0; c < n; c += 1) {
            var klass = g.classes[r][c];
            ctx.fillStyle = slopeColor(klass);
            var x0 = px(lon0 + c * dlon);
            var y0 = py(lat0 - r * dlat);
            var x1 = px(lon0 + (c + 1) * dlon);
            var y1 = py(lat0 - (r + 1) * dlat);
            ctx.fillRect(x0, y0, Math.max(1, x1 - x0), Math.max(1, y1 - y0));
          }
        }
        ctx.restore();
      }

      if (ARES.state.footprints && ARES.state.footprints.length) {
        ctx.save();
        ctx.lineWidth = 1;
        ARES.state.footprints.forEach(function (fp) {
          ctx.strokeStyle = fp.color;
          ctx.globalAlpha = 0.75;
          ctx.beginPath();
          fp.ring.forEach(function (pt, idx) {
            var x = px(pt[0]), y = py(pt[1]);
            if (idx === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
          });
          ctx.closePath();
          ctx.stroke();
        });
        ctx.restore();
      }

      var M = ARES.state.minerals;
      if (M.showSites) {
        M.sites.forEach(function (site) {
          var keys = activeClassesForSite(site);
          if (!keys.length) return;
          var x = px(site.lon_east), y = py(site.lat);
          var radius = Math.max(2.5, ((Number(site.radius_deg) || 0.05) / 360) * drawW * 0.35);
          ctx.save();
          ctx.strokeStyle = classColor(keys[0]);
          ctx.fillStyle = hexToRgba(classColor(keys[0]), 0.06);
          ctx.lineWidth = 1.0;
          ctx.beginPath(); ctx.arc(x, y, radius, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
          ctx.restore();
        });
      }

      var result = ARES.state.scout.result;
      if (result) {
        var iterations = result.iterations || [];
        var snap = iterations[ARES.state.scout.iteration] || iterations[iterations.length - 1] || {};
        function draw2DPath(points, color, dashed) {
          if (!points || points.length < 2) return;
          ctx.save();
          ctx.strokeStyle = color;
          ctx.lineWidth = dashed ? 1.5 : 2.6;
          if (dashed) ctx.setLineDash([5, 4]);
          ctx.beginPath();
          points.forEach(function (p, idx) {
            var x = px(p.lon == null ? p.lon_east : p.lon), y = py(p.lat);
            if (idx === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
          });
          ctx.stroke();
          ctx.restore();
        }
        draw2DPath(snap.optimistic_path, COLOR.cyan, true);
        draw2DPath(snap.feasible_path, COLOR.green, false);
        var traj = snap.scout_trajectory || (result.scout_trajectory || []).filter(function (p) { return p.iteration == null || Number(p.iteration) <= ARES.state.scout.iteration; });
        draw2DPath(traj, COLOR.amber, false);
        if (ARES.state.scout.hazards && result.hazard_cells) {
          ctx.save();
          ctx.fillStyle = COLOR.noGo;
          ctx.globalAlpha = 0.8;
          result.hazard_cells.forEach(function (h) {
            ctx.beginPath(); ctx.arc(px(h.lon), py(h.lat), 1.7, 0, Math.PI * 2); ctx.fill();
          });
          ctx.restore();
        }
        var start = result.start || {}, target = result.target || {};
        if (start.lat != null) {
          ctx.fillStyle = COLOR.green;
          ctx.beginPath(); ctx.arc(px(start.lon == null ? start.lon_east : start.lon), py(start.lat), 4, 0, Math.PI * 2); ctx.fill();
        }
        if (target.lat != null) {
          ctx.fillStyle = COLOR.magenta;
          ctx.beginPath(); ctx.arc(px(target.lon == null ? target.lon_east : target.lon), py(target.lat), 4, 0, Math.PI * 2); ctx.fill();
        }
      }
    } catch (err) {
      // Never let an overlay error break the base map render.
      if (window.console && console.warn) console.warn('ARES 2D overlay:', err);
    }
  }

  /* ------------------------------------------------------------------------
     Hover-card enrichment
     ------------------------------------------------------------------------ */
  function namesakeOf(item) {
    if (!item) return null;
    if (item.namesake) return item.namesake;
    if (item.figure && ARES.state.atlas.figures[item.figure]) return ARES.state.atlas.figures[item.figure];
    return null;
  }

  window.aresRenderTooltipDetails = function (displayData) {
    var tt = $('hover-tooltip');
    if (!tt) return;
    tt.classList.add('ares-tooltip');
    var old = $('ares-tt-details');
    if (old && old.parentNode) old.parentNode.removeChild(old);
    var item = lookupItem(displayData);
    if (!item) return;
    var ns = namesakeOf(item);
    var key = item.id || item.name || '';
    var significance = item.significance || item.description || item.summary || '';
    var meta = [];
    if (item._kind === 'mission') {
      if (item.agency) meta.push(item.agency);
      if (item.launch) meta.push('Launch ' + item.launch);
      if (item.arrival) meta.push('Arrival ' + item.arrival);
      if (item.status) meta.push(item.status);
    } else if (item._kind === 'mineral') {
      if (item.confidence != null) meta.push(Math.round(Number(item.confidence) * 100) + '% confidence');
      var keys = (item.classes || []).filter(function (k) { return ARES.state.minerals.active.has(k); });
      if (keys.length) meta.push(keys.map(classLabel).join(', '));
      if (item.source) meta.push(item.source);
    } else if (item._kind === 'footprint') {
      if (item.category) meta.push(item.category);
    } else {
      if (item.category) meta.push(item.category);
      if (item.diameter_km) meta.push(Number(item.diameter_km).toFixed(1) + ' km diameter');
    }
    var html = '<div class="ares-tt-details" id="ares-tt-details">';
    if (ns) {
      html += '<div class="ares-tt-figure"><div class="name">' + esc(ns.name || 'Namesake') + '</div>' +
        (ns.role ? '<div class="role">' + esc(ns.role) + '</div>' : '') +
        (ns.bio ? '<div class="bio">' + esc(ns.bio) + '</div>' : '') + '</div>';
    }
    if (significance) {
      html += '<div class="ares-tt-significance"><b>Scientific significance</b>' + esc(significance) + '</div>';
    }
    if (meta.length) html += '<div class="ares-tt-meta">' + esc(meta.join(' \u00b7 ')) + '</div>';
    html += '<div class="ares-tt-actions">' +
      '<button class="ares-btn ares-primary" type="button" data-ares-action="focus" data-ares-key="' + escAttr(key) + '">Focus</button>' +
      '<button class="ares-btn" type="button" data-ares-action="slope" data-ares-key="' + escAttr(key) + '">30\u00b0 slope</button>' +
      '<button class="ares-btn" type="button" data-ares-action="minerals" data-ares-key="' + escAttr(key) + '">Minerals</button>' +
      '</div></div>';
    tt.insertAdjacentHTML('beforeend', html);
    requestAnimationFrame(function () {
      try {
        var rect = tt.getBoundingClientRect();
        if (rect.right > window.innerWidth - 10) tt.style.left = Math.max(10, window.innerWidth - rect.width - 12) + 'px';
        if (rect.bottom > window.innerHeight - 10) tt.style.top = Math.max(10, window.innerHeight - rect.height - 12) + 'px';
      } catch (err) { /* ignore */ }
    });
  };

  function bindTooltipActions() {
    var tt = $('hover-tooltip');
    if (!tt) return;
    tt.addEventListener('click', function (ev) {
      var btn = ev.target.closest('[data-ares-action]');
      if (!btn) return;
      ev.preventDefault();
      ev.stopPropagation();
      var action = btn.getAttribute('data-ares-action');
      var key = btn.getAttribute('data-ares-key');
      var item = lookupItem({ missionId: key, name: key });
      if (!item) return;
      if (action === 'focus') {
        flyToItem(item);
      } else if (action === 'slope') {
        setPanel(true);
        switchTab('terrain');
        flyToItem(item, function () {
          if (item.lat != null) analyzeSlopeAt(Number(item.lat), eastLon(item.lon == null ? item.lon_east : item.lon));
        });
      } else if (action === 'minerals') {
        setPanel(true);
        switchTab('minerals');
        flyToItem(item, function () {
          if (item.lat != null) scanAt(Number(item.lat), eastLon(item.lon == null ? item.lon_east : item.lon), 'CRISM');
        });
      }
    });
  }

  /* ------------------------------------------------------------------------
     Initial data load
     ------------------------------------------------------------------------ */
  async function loadAll() {
    clearSlope();
    refreshGds();
    await Promise.allSettled([loadAtlas(), loadMinerals()]);
    ensureHoverGroups();
    if (ARES.state.minerals.sites.length) {
      // Re-apply after the explorer's asynchronous landmark fetch completes.
      setTimeout(function () { ensureHoverGroups(); rebuildMineralMarkers(); }, 1600);
    }
  }

  // Expose a few integration points for the existing console and for debugging.
  window.ARES = ARES;
  window.aresMissionControl = {
    flyTo: function (lat, lon) { flyToItem({ lat: lat, lon: lon, lon_east: eastLon(lon) }); },
    analyzeSlope: analyzeSlopeAt,
    scan: scanAt,
    runScout: runScout,
    refresh: fetchEphemeris
  };
})();
