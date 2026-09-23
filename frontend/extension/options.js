const storage = typeof chrome !== 'undefined' && chrome.storage?.local ? {
  get: key => new Promise(resolve => chrome.storage.local.get([key], result => resolve(result[key]))),
  set: (key, value) => new Promise(resolve => chrome.storage.local.set({[key]: value}, resolve))
} : {get: async key => JSON.parse(localStorage.getItem(key) || 'null'), set: async (key, value) => localStorage.setItem(key, JSON.stringify(value))};
document.addEventListener('DOMContentLoaded', async () => {
  const input = document.getElementById('backendUrl');
  input.value = await storage.get('backendUrl') || 'https://flick-picker-api-camerengreen.onrender.com';
  document.getElementById('save').onclick = async () => {
    const value = input.value.trim().replace(/\/$/, '');
    if (!/^https?:\/\//.test(value)) { document.getElementById('status').textContent = 'Enter a full http:// or https:// URL.'; return; }
    await storage.set('backendUrl', value);
    document.getElementById('status').textContent = 'Connection saved.';
  };
});
