// globe.gl/three.js implementation smoke test — needs NO WebGL or browser.
// Runs js/travel-globe.js (the real IIFE) with mocked Globe/fetch/DOM on the
// REAL project data and asserts the layer inputs globe.gl receives.
//
// Why: globe.gl renders via WebGL; a headless browser often hangs on an
// animated, network-heavy map page (MapLibre tiles never idles), and the
// browser-use harness may be unavailable. This probe validates the data/logic
// path without a browser. It catches runtime ReferenceErrors, bad transforms,
// wrong counts, and broken accessor callbacks.
//
// Usage:  node scripts/globe-gl-smoke.js [project_dir]
//   project_dir defaults to the dmpotekhin.github.io travel site.

const fs = require('fs');
const path = require('path');

const BASE = process.argv[2] || '/Users/dmitrypotekhin/Downloads/dmpotekhin.github.io';

// --- real data ---
global.window = {};
require(`${BASE}/js/travel-data.js`); // sets window.TRAVEL_CITIES
const cities = global.window.TRAVEL_CITIES;
const world = JSON.parse(fs.readFileSync(`${BASE}/data/world_countries.geojson`, 'utf8'));
const visited = JSON.parse(fs.readFileSync(`${BASE}/data/visited_countries.geojson`, 'utf8'));
const media = global.window.TRAVEL_MEDIA || {};

if (!Array.isArray(cities) || !cities.length) {
  console.error('FAIL: could not read window.TRAVEL_CITIES from travel-data.js');
  process.exit(1);
}

// --- DOM mock ---
function makeEl() {
  return { clientWidth: 1200, clientHeight: 620, classList: { add() {}, remove() {} } };
}
global.document = {
  getElementById(id) { if (id === 'globe' || id === 'globe-loading') return makeEl(); return null; },
  querySelector(sel) { if (sel === '.globe-stats') return { textContent: '', innerHTML: '' }; return null; },
  querySelectorAll() { return []; }
};
global.window.addEventListener = function () {}; // 'resize', 'error', 'unhandledrejection'

// --- fetch mock (matches the two local geojsons the IIFE fetches) ---
global.fetch = (url) => {
  let data;
  if (String(url).includes('world_countries')) data = world;
  else if (String(url).includes('visited_countries')) data = visited;
  else return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  return Promise.resolve({ ok: true, json: () => Promise.resolve(data) });
};

// --- Globe mock: record the inputs each accessor receives ---
const calls = { pointsData: null, polygonsData: null, pointOfView: [], onReadyCb: null, onPointClickCb: null };
const controls = { autoRotate: false, enableDamping: false, dampingFactor: 0, autoRotateSpeed: 0 };
const g = {};
Object.assign(g, {
  width() { return g; }, height() { return g; },
  globeImageUrl() { return g; }, bumpImageUrl() { return g; },
  showAtmosphere() { return g; }, atmosphereColor() { return g; }, atmosphereAltitude() { return g; },
  backgroundColor() { return g; },
  pointsData(d) { calls.pointsData = d; return g; },
  pointLat() { return g; }, pointLng() { return g; }, pointColor() { return g; },
  pointAltitude() { return g; }, pointRadius() { return g; }, pointResolution() { return g; },
  pointLabel() { return g; },
  onPointClick(cb) { calls.onPointClickCb = cb; return g; },
  polygonsData(d) { calls.polygonsData = d; return g; },
  polygonAltitude(fn) { calls.polygonAltitudeFn = fn; return g; },
  polygonCapColor(fn) { calls.polygonCapColorFn = fn; return g; },
  polygonSideColor() { return g; },
  polygonStrokeColor() { return g; }, polygonLabel() { return g; },
  onGlobeReady(cb) { calls.onReadyCb = cb; return g; },
  pointOfView(cfg) { calls.pointOfView.push(cfg); return g; },
  controls() { return controls; }
});
global.Globe = () => g;

// --- run the real IIFE ---
require(`${BASE}/js/travel-globe.js`);

// Accent fill constant must match travel-globe.js (site accent). If the globe file
// changes the color, update ACCENT here too.
const ACCENT = 'rgba(224,36,94,0.75)';

setTimeout(() => {
  const problems = [];
  const okPts = calls.pointsData && calls.pointsData.length === cities.length;
  if (!okPts) problems.push(`pointsData length ${calls.pointsData && calls.pointsData.length} != cities ${cities.length}`);

  const okPoly = calls.polygonsData && calls.polygonsData.length === world.features.length;
  if (!okPoly) problems.push(`polygonsData length ${calls.polygonsData && calls.polygonsData.length} != world features ${world.features.length}`);

  // accent count = __visited features set by buildPolygons
  let accent = 0;
  let visitedFeat = null;
  if (calls.polygonsData) {
    for (const f of calls.polygonsData) if (f.__visited) { accent++; visitedFeat = visitedFeat || f; }
  }

  // exercise the accessor callbacks to confirm accent neighbors map correctly
  if (visitedFeat && calls.polygonCapColorFn) {
    const col = calls.polygonCapColorFn(visitedFeat);
    if (col !== ACCENT) problems.push(`capColor(visited) = ${col} != ${ACCENT}`);
  }

  if (!controls.autoRotate) problems.push('controls.autoRotate is false');
  if (!controls.enableDamping) problems.push('controls.enableDamping is false');

  // point shape sanity: {city, country, lat, lng}
  const s = calls.pointsData && calls.pointsData[0];
  if (!s || typeof s.lat !== 'number' || typeof s.lng !== 'number') {
    problems.push('pointsData[0] missing numeric lat/lng: ' + JSON.stringify(s));
  }

  // fire ready + click callbacks to test onGlobeReady / flyTo path
  let cbOk = true;
  try { if (calls.onReadyCb) calls.onReadyCb(); if (calls.onPointClickCb && s) calls.onPointClickCb(s); }
  catch (e) { cbOk = false; problems.push('callback threw: ' + e.message); }

  console.log('cities:', cities.length);
  console.log('pointsData len:', calls.pointsData && calls.pointsData.length);
  console.log('points sample:', JSON.stringify(s));
  console.log('polygonsData len:', calls.polygonsData && calls.polygonsData.length);
  console.log('accent (visited) polygons:', accent);
  console.log('controls.autoRotate:', controls.autoRotate, '| enableDamping:', controls.enableDamping);
  console.log('callbacks fired:', cbOk);

  if (problems.length) {
    console.log('\nFAIL:\n  - ' + problems.join('\n  - '));
    process.exit(1);
  }
  console.log('\nSMOKE RESULT: PASS');
}, 300);
