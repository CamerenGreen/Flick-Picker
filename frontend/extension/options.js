const storage = typeof chrome !== 'undefined' && chrome.storage?.local ? {
  get: key => new Promise(resolve => chrome.storage.local.get([key], result => resolve(result[key]))),
  set: (key, value) => new Promise(resolve => chrome.storage.local.set({[key]: value}, resolve))
} : {get: async key => JSON.parse(localStorage.getItem(key) || 'null'), set: async (key, value) => localStorage.setItem(key, JSON.stringify(value))};
document.addEventListener('DOMContentLoaded', async () => {
  const input = document.getElementById('backendUrl');
  input.value = await storage.get('backendUrl') || 'http://127.0.0.1:8000';
  document.getElementById('save').onclick = async () => {
    const value = input.value.trim().replace(/\/$/, '');
    if (!/^https?:\/\//.test(value)) { document.getElementById('status').textContent = 'Enter a full http:// or https:// URL.'; return; }
    await storage.set('backendUrl', value);
    document.getElementById('status').textContent = 'Connection saved.';
  };
  async function sync(mediaType) {
    const status = document.getElementById('syncStatus');
    status.textContent = `Importing ${mediaType === 'tv' ? 'shows' : 'movies'}…`;
    try {
      const backend = input.value.trim().replace(/\/$/, '');
      const response = await fetch(`${backend}/tmdb/sync_popular?media_type=${mediaType}`, {method:'POST'});
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'Sync failed');
      status.textContent = `Added ${result.added} titles. Model trained on ${result.item_count} titles.`;
    } catch (error) { status.textContent = error.message; }
  }
  document.getElementById('syncMovies').onclick = () => sync('movie');
  document.getElementById('syncShows').onclick = () => sync('tv');
});
