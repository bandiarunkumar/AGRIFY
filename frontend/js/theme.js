/* AGRIFY adaptive theme control — no dependency, local preference only. */
(() => {
  const root = document.documentElement;
  const key = 'agrify-theme';
  const read = () => {
    try { return localStorage.getItem(key); } catch (_) { return null; }
  };
  const apply = (theme) => {
    if (theme === 'light' || theme === 'dark') root.dataset.theme = theme;
    else root.removeAttribute('data-theme');
    const btn = document.querySelector('[data-agrify-theme-toggle]');
    if (btn) {
      const current = root.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      btn.setAttribute('aria-label', 'Switch to ' + (current === 'dark' ? 'light' : 'dark') + ' theme');
      btn.setAttribute('title', 'Theme: ' + current + ' (click to switch)');
      const label = (current === 'dark' ? '☀' : '☾') + '<span>' + (current === 'dark' ? 'Light' : 'Dark') + '</span>';
      if (btn.innerHTML !== label) btn.innerHTML = label;
    }
  };
  apply(read());
  const mount = () => {
    let btn = document.querySelector('[data-agrify-theme-toggle]');
    const nav = document.getElementById('navbar');
    if (!btn && nav) {
      btn = document.createElement('button');
      btn.type = 'button'; btn.className = 'ag-theme-toggle';
      btn.dataset.agrifyThemeToggle = 'true'; btn.setAttribute('aria-label','Toggle color theme');
      btn.addEventListener('click', () => {
        const current = root.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        const next = current === 'dark' ? 'light' : 'dark';
        apply(next);
        try { localStorage.setItem(key, next); } catch (_) {}
      });
      nav.appendChild(btn);
    }
    apply(read());
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
  new MutationObserver(mount).observe(document.getElementById('navbar') || document.body, {childList:true,subtree:true});
  if (matchMedia) matchMedia('(prefers-color-scheme: dark)').addEventListener?.('change', () => { if (!read()) apply(null); });
})();
