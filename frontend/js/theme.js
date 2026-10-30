const STORAGE_KEY = 'agrify-theme';
const VALID_PREFERENCES = new Set(['system', 'light', 'dark']);

function getPreference() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return VALID_PREFERENCES.has(stored) ? stored : 'system';
  } catch {
    return 'system';
  }
}

function applyPreference(preference) {
  const safePreference = VALID_PREFERENCES.has(preference) ? preference : 'system';
  const dark = safePreference === 'dark' || (
    safePreference === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches
  );

  document.documentElement.dataset.themePreference = safePreference;
  document.documentElement.dataset.theme = dark ? 'dark' : 'light';

  try {
    localStorage.setItem(STORAGE_KEY, safePreference);
  } catch {
    // Theme still works for this session when browser storage is unavailable.
  }
}

export function initTheme() {
  applyPreference(getPreference());
  window.addEventListener('themeChange', event => applyPreference(event.detail));

  const systemTheme = window.matchMedia('(prefers-color-scheme: dark)');
  systemTheme.addEventListener?.('change', () => {
    if (getPreference() === 'system') applyPreference('system');
  });
}
