import assert from 'node:assert/strict';
import { getFarmActionPlan } from './js/api.js';

const originalFetch = globalThis.fetch;
const originalWindow = globalThis.window;

try {
  // Test 1: Successful action plan retrieval
  globalThis.window = {
    location: { hostname: 'localhost' },
    localStorage: { getItem: () => 'en' },
  };

  let requestedUrl = '';
  let sentPayload = null;

  globalThis.fetch = async (url, options) => {
    requestedUrl = url;
    sentPayload = JSON.parse(options.body);
    return {
      ok: true,
      json: async () => ({
        status: 'success',
        plan: { immediate_actions: ['Inspect soil moisture'], season: 'Kharif' }
      })
    };
  };

  const res = await getFarmActionPlan({ crop_name: 'rice', season: 'Kharif' });
  assert.equal(res.status, 'success');
  assert.equal(sentPayload.crop_name, 'rice');
  assert.equal(sentPayload.language, 'en');

  // Test 2: Error handling on fetch failure (verifies isLocal is defined and does not throw ReferenceError)
  let localFetchCalls = 0;
  globalThis.fetch = async (url) => {
    localFetchCalls += 1;
    throw new TypeError('Network connection failed');
  };

  await assert.rejects(
    getFarmActionPlan({ crop_name: 'rice' }),
    /Cannot connect to Agri-Connect server|Network connection failed/
  );
  assert.ok(localFetchCalls > 0, 'fetch should have been attempted');

  console.log('PASS: getFarmActionPlan contract and fallback error handling verified.');
} finally {
  globalThis.fetch = originalFetch;
  if (originalWindow !== undefined) {
    globalThis.window = originalWindow;
  } else {
    delete globalThis.window;
  }
}
