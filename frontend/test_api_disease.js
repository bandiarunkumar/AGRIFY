import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { predictDisease, getDiseaseApiBase, _setEnvForTesting } from './js/api.js';

const originalFetch = globalThis.fetch;
const originalWindow = globalThis.window;
const image = new Blob(['leaf bytes'], { type: 'image/jpeg' });

try {
  // ---- Test 1: Staging config resolves to staging Crop Doctor ----
  _setEnvForTesting({
    VITE_API_BASE_URL: 'https://agri-connect-main-app-staging.onrender.com',
    VITE_IMAGE_API_BASE_URL: 'https://agri-connect-image-staging.onrender.com',
  });
  delete globalThis.window;
  assert.equal(
    getDiseaseApiBase(),
    'https://agri-connect-image-staging.onrender.com',
    'staging env must resolve to staging Crop Doctor'
  );

  // ---- Test 2: Production URLs cannot be selected by the staging build ----
  // The production URL strings must not exist anywhere in the module source.
  const moduleSource = readFileSync(new URL('./js/api.js', import.meta.url), 'utf-8');
  assert.ok(
    !moduleSource.includes('agri-connect-main-app.onrender.com'),
    'production Core API URL must not exist in api.js'
  );
  assert.ok(
    !moduleSource.includes('agri-connect-image.onrender.com'),
    'production Crop Doctor URL must not exist in api.js'
  );

  // ---- Test 3: Missing configuration throws (no production fallback) ----
  _setEnvForTesting({});
  delete globalThis.window;
  assert.throws(
    () => getDiseaseApiBase(),
    /Missing required environment variable VITE_IMAGE_API_BASE_URL/,
    'missing VITE_IMAGE_API_BASE_URL must throw, not fall back to production'
  );

  // Empty string also throws (treated as missing)
  _setEnvForTesting({ VITE_IMAGE_API_BASE_URL: '' });
  assert.throws(
    () => getDiseaseApiBase(),
    /Missing required environment variable/,
    'empty VITE_IMAGE_API_BASE_URL must throw'
  );

  // Whitespace-only also throws
  _setEnvForTesting({ VITE_IMAGE_API_BASE_URL: '   ' });
  assert.throws(
    () => getDiseaseApiBase(),
    /Missing required environment variable/,
    'whitespace-only VITE_IMAGE_API_BASE_URL must throw'
  );

  // ---- Test 4: Localhost fallback when env is missing ----
  _setEnvForTesting({});
  globalThis.window = { location: { hostname: 'localhost' } };
  assert.equal(
    getDiseaseApiBase(),
    'http://127.0.0.1:5001',
    'localhost with missing env must use local dev fallback'
  );

  globalThis.window = { location: { hostname: '127.0.0.1' } };
  assert.equal(
    getDiseaseApiBase(),
    'http://127.0.0.1:5001',
    '127.0.0.1 with missing env must use local dev fallback'
  );

  // ---- Test 5: Window overrides are not consulted (removed for production safety) ----
  // The module source must not reference __AGRIFY_DISEASE_API_BASE__ at all.
  const moduleSourceDisease = readFileSync(new URL('./js/api.js', import.meta.url), 'utf-8');
  assert.ok(
    !moduleSourceDisease.includes('__AGRIFY_DISEASE_API_BASE__'),
    'window.__AGRIFY_DISEASE_API_BASE__ override must not exist in api.js'
  );

  // Even if a runtime override is present on window, getDiseaseApiBase() must
  // ignore it and use only the configured env var.
  _setEnvForTesting({ VITE_IMAGE_API_BASE_URL: 'https://agri-connect-image-staging.onrender.com' });
  globalThis.window = {
    location: { hostname: 'agri-connect-staging.vercel.app' },
    __AGRIFY_DISEASE_API_BASE__: 'https://agri-connect-image.onrender.com',
  };
  assert.equal(
    getDiseaseApiBase(),
    'https://agri-connect-image-staging.onrender.com',
    'window override must be ignored; env var takes precedence'
  );

  // ---- Test 6: Non-localhost, non-window-override, missing env throws ----
  _setEnvForTesting({});
  globalThis.window = { location: { hostname: 'agri-connect-staging.vercel.app' } };
  assert.throws(
    () => getDiseaseApiBase(),
    /Missing required environment variable/,
    'staging host with missing env must throw, not fall back to production'
  );

  // ---- Test 7: predictDisease reports configured (non-production) host on failure ----
  _setEnvForTesting({ VITE_IMAGE_API_BASE_URL: 'https://agri-connect-image-staging.onrender.com' });
  globalThis.window = { location: { hostname: 'agri-connect-staging.vercel.app' } };
  let calls = 0;
  globalThis.fetch = async () => {
    calls += 1;
    throw new TypeError('Failed to fetch');
  };
  await assert.rejects(
    predictDisease(image),
    /Crop Doctor is currently unavailable at https:\/\/agri-connect-image-staging\.onrender\.com/,
    'failure error must name the configured staging host, not production'
  );
  assert.equal(calls, 1, 'an unavailable diagnosis must not silently fail over to another host');

  // ---- Test 8: Existing contract tests (unchanged behavior) ----
  globalThis.fetch = async () => ({
    ok: true,
    json: async () => ({ status: 'success', is_recognized: true }),
  });
  await assert.rejects(predictDisease(image), /incomplete diagnosis/);

  globalThis.fetch = async () => ({
    ok: true,
    json: async () => ({ status: 'success', is_recognized: false, error: 'Unsupported leaf' }),
  });
  const unrecognized = await predictDisease(image);
  assert.equal(unrecognized.is_recognized, false);

  globalThis.fetch = async () => ({
    ok: false,
    json: async () => ({ error: 'Unsupported image format.' }),
  });
  await assert.rejects(predictDisease(image), /Unsupported image format/);

  console.log('PASS: Crop Doctor staging URL selection, anti-production-fallback, and API contracts verified.');
} finally {
  _setEnvForTesting(null);
  globalThis.fetch = originalFetch;
  if (originalWindow !== undefined) {
    globalThis.window = originalWindow;
  } else {
    delete globalThis.window;
  }
}
