import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { getApiBase, _setEnvForTesting } from './js/api.js';

const originalWindow = globalThis.window;

try {
  // ---- Test 1: Staging config resolves to staging Core API ----
  _setEnvForTesting({ VITE_API_BASE_URL: 'https://agri-connect-main-app-staging.onrender.com' });
  delete globalThis.window;
  assert.equal(
    getApiBase(),
    'https://agri-connect-main-app-staging.onrender.com',
    'staging env must resolve to staging Core API'
  );

  // ---- Test 2: Production URL cannot be selected ----
  _setEnvForTesting({});
  delete globalThis.window;
  assert.throws(
    () => getApiBase(),
    /Missing required environment variable VITE_API_BASE_URL/,
    'missing VITE_API_BASE_URL must throw, not fall back to production'
  );

  // Empty string throws
  _setEnvForTesting({ VITE_API_BASE_URL: '' });
  assert.throws(
    () => getApiBase(),
    /Missing required environment variable/,
    'empty VITE_API_BASE_URL must throw'
  );

  // ---- Test 3: Localhost fallback when env is missing ----
  _setEnvForTesting({});
  globalThis.window = { location: { hostname: 'localhost' } };
  assert.equal(
    getApiBase(),
    'http://127.0.0.1:5000',
    'localhost with missing env must use local dev fallback'
  );

  globalThis.window = { location: { hostname: '127.0.0.1' } };
  assert.equal(
    getApiBase(),
    'http://127.0.0.1:5000',
    '127.0.0.1 with missing env must use local dev fallback'
  );

  // ---- Test 4: Window overrides are not consulted (removed for production safety) ----
  // The module source must not reference __AGRIFY_API_BASE__ at all, so no
  // runtime override can redirect the staging frontend to production.
  const moduleSource = readFileSync(new URL('./js/api.js', import.meta.url), 'utf-8');
  assert.ok(
    !moduleSource.includes('__AGRIFY_API_BASE__'),
    'window.__AGRIFY_API_BASE__ override must not exist in api.js'
  );

  // Even if a runtime override is present on window, getApiBase() must
  // ignore it and use only the configured env var.
  _setEnvForTesting({ VITE_API_BASE_URL: 'https://agri-connect-main-app-staging.onrender.com' });
  globalThis.window = {
    location: { hostname: 'agri-connect-staging.vercel.app' },
    __AGRIFY_API_BASE__: 'https://agri-connect-main-app.onrender.com',
  };
  assert.equal(
    getApiBase(),
    'https://agri-connect-main-app-staging.onrender.com',
    'window override must be ignored; env var takes precedence'
  );

  // ---- Test 5: Staging host with missing env throws (no production fallback) ----
  _setEnvForTesting({});
  globalThis.window = { location: { hostname: 'agrify-staging.vercel.app' } };
  assert.throws(
    () => getApiBase(),
    /Missing required environment variable/,
    'staging host with missing env must throw, not fall back to production'
  );

  // Trailing slash is stripped from configured URL
  _setEnvForTesting({ VITE_API_BASE_URL: 'https://agri-connect-main-app-staging.onrender.com/' });
  delete globalThis.window;
  assert.equal(
    getApiBase(),
    'https://agri-connect-main-app-staging.onrender.com',
    'trailing slash must be stripped from configured URL'
  );

  console.log('PASS: Core API staging URL selection and anti-production-fallback verified.');
} finally {
  _setEnvForTesting(null);
  if (originalWindow !== undefined) {
    globalThis.window = originalWindow;
  } else {
    delete globalThis.window;
  }
}
