import assert from 'node:assert/strict';
import { predictDisease, getDiseaseApiBase } from './js/api.js';

const originalFetch = globalThis.fetch;
const originalWindow = globalThis.window;
const image = new Blob(['leaf bytes'], { type: 'image/jpeg' });

try {
  // ---- Test URL Selection ----
  // 1. Non-browser / production default:
  delete globalThis.window;
  assert.equal(getDiseaseApiBase(), 'https://agri-connect-image.onrender.com');

  // 2. Localhost browser environment:
  globalThis.window = { location: { hostname: 'localhost' } };
  assert.equal(getDiseaseApiBase(), 'http://127.0.0.1:5001');

  // 3. 127.0.0.1 browser environment:
  globalThis.window = { location: { hostname: '127.0.0.1' } };
  assert.equal(getDiseaseApiBase(), 'http://127.0.0.1:5001');

  // 4. Custom override via window.__AGRIFY_DISEASE_API_BASE__:
  globalThis.window = {
    location: { hostname: 'localhost' },
    __AGRIFY_DISEASE_API_BASE__: 'https://custom-disease-service.internal',
  };
  assert.equal(getDiseaseApiBase(), 'https://custom-disease-service.internal');

  // 5. Production deployed domain:
  globalThis.window = { location: { hostname: 'agri-connect-frontend.onrender.com' } };
  assert.equal(getDiseaseApiBase(), 'https://agri-connect-image.onrender.com');

  // ---- Test Failure Behavior on Configured Host ----
  // Configure local host and verify error reports failure specifically on that host without silent failover
  globalThis.window = { location: { hostname: '127.0.0.1' } };
  let calls = 0;
  let targetUrl = '';
  globalThis.fetch = async (url) => {
    calls += 1;
    targetUrl = url;
    throw new TypeError('Failed to fetch');
  };
  await assert.rejects(
    predictDisease(image),
    /Crop Doctor is currently unavailable at http:\/\/127\.0\.0\.1:5001/
  );
  assert.equal(calls, 1, 'an unavailable diagnosis must not resend the image or silently fail over');
  assert.equal(targetUrl, 'http://127.0.0.1:5001/api/predict');

  // ---- Existing Contract Tests ----
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

  console.log('PASS: Crop Doctor URL selection, host-specific failure handling, and API contracts verified.');
} finally {
  globalThis.fetch = originalFetch;
  if (originalWindow !== undefined) {
    globalThis.window = originalWindow;
  } else {
    delete globalThis.window;
  }
}
