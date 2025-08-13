(function () {
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  const apiInput = $('#apiBase');
  const apiMsg   = $('#apiMsg');

  // Load & save base URL
  const saved = localStorage.getItem('bottie_api');
  if (saved) apiInput.value = saved;

  $('#saveApi').addEventListener('click', () => {
    const v = apiInput.value.trim();
    if (!v) return msg('Please enter API base URL');
    localStorage.setItem('bottie_api', v);
    msg('Saved ✓');
  });

  $('#pingApi').addEventListener('click', async () => {
    try {
      const base = baseUrl();
      const r = await fetch(base + '/health', { method: 'GET' });
      const j = await r.json();
      msg('Health: ' + pretty(j));
    } catch (e) {
      msg('Ping failed: ' + e.message);
    }
  });

  // Wire “Refresh” buttons
  $$('.btn.pull').forEach(btn => {
    btn.addEventListener('click', async () => {
      const ep = btn.getAttribute('data-endpoint');
      const targetId = ep.replace('/', '');
      const out = $('#' + targetId);
      try {
        const base = baseUrl();
        const r = await fetch(base + ep);
        const j = await r.json();
        out.textContent = pretty(j);
      } catch (e) {
        out.textContent = 'Error: ' + e.message;
      }
    });
  });

  // Helpers
  function baseUrl() {
    const v = apiInput.value.trim() || localStorage.getItem('bottie_api') || '';
    if (!v) throw new Error('No API URL set');
    return v.replace(/\/+$/, '');
  }
  function msg(t) { apiMsg.textContent = t; }
  function pretty(obj) { return JSON.stringify(obj, null, 2); }
})();
