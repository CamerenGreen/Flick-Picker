const $ = id => document.getElementById(id);
const storage = typeof chrome !== 'undefined' && chrome.storage?.local ? {
  get: key => new Promise(resolve => chrome.storage.local.get([key], result => resolve(result[key]))),
  set: (key, value) => new Promise(resolve => chrome.storage.local.set({[key]: value}, resolve))
} : {get: async key => JSON.parse(localStorage.getItem(key) || 'null'), set: async (key, value) => localStorage.setItem(key, JSON.stringify(value))};
let backend = '', user = null, filter = 'all', query = '', catalog = [], history = [];
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));

async function api(path, options) {
  const request = {...(options || {}), headers: {...(options?.headers || {})}};
  if (user?.token) request.headers.Authorization = `Bearer ${user.token}`;
  const response = await fetch(backend + path, request);
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || `Server returned ${response.status}`);
  }
  return response.json();
}
function message(value) { $('message').textContent = value; }
function showTab(name) {
  document.querySelectorAll('.tab').forEach(button => button.classList.toggle('active', button.dataset.tab === name));
  document.querySelectorAll('.tab-panel').forEach(panel => panel.hidden = panel.id !== name);
  if (name === 'for-you') loadRecommendations();
  if (name === 'watched') loadHistory();
  if (name === 'discover') loadCatalog();
}
function profile() {
  $('profileCreate').hidden = !!user;
  $('profileActive').hidden = !user;
  if (user) { $('profileName').textContent = user.name; $('avatar').textContent = user.name.slice(0,1).toUpperCase(); }
}
function card(item, mode) {
  const watched = history.some(entry => entry.id === item.id);
  const cover = item.poster_url ? `<img src="${escapeHtml(item.poster_url)}" alt="">` : item.media_type === 'tv' ? 'TV' : 'FILM';
  const action = mode === 'watched' ? '' : `<button class="card-action" data-action="watch" data-id="${item.id || ''}" data-source="${escapeHtml(item.source)}" data-source-id="${escapeHtml(item.source_id)}" data-type="${escapeHtml(item.media_type)}" aria-label="${watched ? 'Already watched' : 'Mark as watched'}: ${escapeHtml(item.title)}" ${watched ? 'disabled' : ''}>${watched ? 'Added' : 'Add'}</button>`;
  const detail = mode === 'recommend' ? item.reason : (item.genres || []).slice(0,2).join(' · ');
  return `<article class="media-card"><div class="cover ${item.media_type === 'tv' ? 'tv' : ''}">${cover}</div><div class="card-main"><strong title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</strong><div class="meta">${item.media_type === 'tv' ? 'Series' : 'Movie'} · ${escapeHtml(item.year || '—')}</div><div class="${mode === 'recommend' ? 'score' : 'tags'}" title="${escapeHtml(detail)}">${escapeHtml(detail)}</div></div>${action}</article>`;
}
function showList(id, items, mode, empty) {
  $(id).innerHTML = items.length ? items.map(item => card(item, mode)).join('') : `<div class="empty">${escapeHtml(empty)}</div>`;
}
async function loadCatalog() {
  try {
    const url = query ? `/search?q=${encodeURIComponent(query)}&media_type=${filter}` : `/catalog?media_type=${filter}`;
    catalog = await api(url);
    $('catalogCount').textContent = `${catalog.length} titles`;
    showList('catalogList', catalog, 'catalog', 'No titles found. Try another search.');
  } catch (error) { message(`Could not connect to the backend: ${error.message}`); }
}
async function loadHistory() {
  if (!user) { showList('watchedList', [], 'watched', 'Create a profile to save watched titles.'); return; }
  try { history = await api(`/users/${user.id}/history`); showList('watchedList', history, 'watched', 'Your watch history is empty. Find a title in Discover.'); }
  catch (error) { message(error.message); }
}
async function loadRecommendations() {
  if (!user) { showList('recommendList', [], 'recommend', 'Create a profile and add a watched title to get recommendations.'); return; }
  try {
    const items = await api(`/users/${user.id}/recommend`);
    showList('recommendList', items, 'recommend', 'Add a watched title from Discover to train your taste profile.');
  } catch (error) { message(error.message); }
}
async function createUser(name) {
  if (!name.trim()) { message('Enter your name to start.'); return null; }
  user = await api('/users', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name:name.trim()})});
  await storage.set('currentUser', user);
  profile();
  await loadHistory();
  message(`Profile created. Add a title you’ve watched.`);
  return user;
}
async function addWatched(button) {
  if (!user) { message('Create a profile first.'); return; }
  const item = {rating: 4};
  if (button.dataset.id) item.media_id = Number(button.dataset.id);
  else { item.source = 'tmdb'; item.source_id = button.dataset.sourceId; item.media_type = button.dataset.type; }
  button.disabled = true;
  try {
    const result = await api(`/users/${user.id}/history`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(item)});
    await loadHistory();
    await loadCatalog();
    message(`Added ${result.media.title} to your watched list.`);
    showTab('for-you');
  } catch (error) { message(error.message); }
  finally { button.disabled = false; }
}
async function demo() {
  try {
    const created = await createUser('Demo Viewer');
    if (!created) return;
    const titles = await api('/search?q=Matrix');
    const matrix = titles.find(item => item.title === 'The Matrix');
    if (matrix) await api(`/users/${created.id}/history`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({media_id:matrix.id,rating:5})});
    await loadHistory();
    showTab('for-you');
    message('Sample profile created with The Matrix in its history.');
  } catch (error) { message(error.message); }
}
async function init() {
  backend = await storage.get('backendUrl') || (location.protocol === 'http:' || location.protocol === 'https:'
    ? location.origin
    : 'https://flick-picker-api-camerengreen.onrender.com');
  backend = backend.replace(/\/$/, '');
  user = await storage.get('currentUser');
  if (user) {
    try {
      const saved = user;
      const profileData = await api(`/users/${user.id}`);
      user = {...profileData, token: saved.token};
    } catch { user = null; await storage.set('currentUser', null); }
  }
  profile();
  document.querySelectorAll('.tab').forEach(button => button.onclick = () => showTab(button.dataset.tab));
  document.querySelectorAll('.filter').forEach(button => button.onclick = () => {
    filter = button.dataset.filter;
    document.querySelectorAll('.filter').forEach(element => element.classList.toggle('active', element === button));
    loadCatalog();
  });
  $('createUser').onclick = () => createUser($('nameInput').value).catch(error => message(error.message));
  $('nameInput').onkeydown = event => { if (event.key === 'Enter') $('createUser').click(); };
  $('demoButton').onclick = demo;
  $('switchUser').onclick = async () => { user = null; await storage.set('currentUser', null); profile(); showTab('discover'); message('Create a new profile.'); };
  $('searchButton').onclick = () => { query = $('searchInput').value.trim(); loadCatalog(); };
  $('searchInput').onkeydown = event => { if (event.key === 'Enter') $('searchButton').click(); };
  document.querySelector('.app').onclick = event => {
    const button = event.target.closest('[data-action="watch"]');
    if (button) addWatched(button);
  };
  try { const status = await api('/model/status'); $('modelLabel').textContent = `${status.item_count} titles in catalog`; }
  catch { $('modelLabel').textContent = 'Server offline'; }
  await loadHistory();
  await loadCatalog();
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
