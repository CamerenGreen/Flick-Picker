// TypeScript source for the extension popup.
// This file is optional — compiled JS (popup.js) is included so you can load the extension without a build step.

type User = { id: number; name: string };

let currentUser: User | null = null;
const API_BASE = 'http://localhost:8000';

async function requestJson(path: string, opts: any = {}) {
  const res = await fetch(API_BASE + path, opts);
  if (!res.ok) throw new Error('API error ' + res.status);
  return res.json();
}

document.addEventListener('DOMContentLoaded', () => {
  (document.getElementById('createUser') as HTMLButtonElement).onclick = async () => {
    const name = (document.getElementById('username') as HTMLInputElement).value;
    try {
      const user = await requestJson('/users', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({name}) });
      currentUser = user as User;
      (document.getElementById('status') as HTMLElement).innerText = `User set: ${user.name} (id=${user.id})`;
    } catch (err) { (document.getElementById('status') as HTMLElement).innerText = String(err); }
  };

  (document.getElementById('addWatched') as HTMLButtonElement).onclick = async () => {
    if (!currentUser) { alert('Set a user first'); return; }
    const tmdb = parseInt((document.getElementById('tmdbid') as HTMLInputElement).value || '0');
    try {
      const data = await requestJson(`/users/${currentUser.id}/history`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({tmdb_id: tmdb}) });
      (document.getElementById('status') as HTMLElement).innerText = 'Added watched: ' + JSON.stringify(data);
    } catch (err) { (document.getElementById('status') as HTMLElement).innerText = String(err); }
  };

  (document.getElementById('getRecs') as HTMLButtonElement).onclick = async () => {
    if (!currentUser) { alert('Set a user first'); return; }
    try {
      const recs = await requestJson(`/users/${currentUser.id}/recommend`);
      const el = document.getElementById('recs') as HTMLElement;
      if (!recs || recs.length === 0) { el.innerText = 'No recommendations yet.'; return; }
      el.innerHTML = '<ul>' + recs.map((r: any) => `<li>${r.title} (tmdb ${r.tmdb_id}) — ${r.score.toFixed(3)}</li>`).join('') + '</ul>';
    } catch (err) { (document.getElementById('status') as HTMLElement).innerText = String(err); }
  };
});
