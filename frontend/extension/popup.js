// Compiled JS version of popup.ts included so extension works without a build step.
(() => {
    const API_BASE = 'http://localhost:8000';
    function requestJson(path, opts = {}) {
        return fetch(API_BASE + path, opts).then(res => {
            if (!res.ok)
                throw new Error('API error ' + res.status);
            return res.json();
        });
    }
    let currentUser = null;
    document.addEventListener('DOMContentLoaded', () => {
        document.getElementById('createUser').onclick = async () => {
            const name = document.getElementById('username').value;
            try {
                const user = await requestJson('/users', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) });
                currentUser = user;
                document.getElementById('status').innerText = `User set: ${user.name} (id=${user.id})`;
            }
            catch (err) {
                document.getElementById('status').innerText = String(err);
            }
        };
        document.getElementById('addWatched').onclick = async () => {
            if (!currentUser) {
                alert('Set a user first');
                return;
            }
            const tmdb = parseInt(document.getElementById('tmdbid').value || '0');
            try {
                const data = await requestJson(`/users/${currentUser.id}/history`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ tmdb_id: tmdb }) });
                document.getElementById('status').innerText = 'Added watched: ' + JSON.stringify(data);
            }
            catch (err) {
                document.getElementById('status').innerText = String(err);
            }
        };
        document.getElementById('getRecs').onclick = async () => {
            if (!currentUser) {
                alert('Set a user first');
                return;
            }
            try {
                const recs = await requestJson(`/users/${currentUser.id}/recommend`);
                const el = document.getElementById('recs');
                if (!recs || recs.length === 0) {
                    el.innerText = 'No recommendations yet.';
                    return;
                }
                el.innerHTML = '<ul>' + recs.map(r => `<li>${r.title} (tmdb ${r.tmdb_id}) — ${r.score.toFixed(3)}</li>`).join('') + '</ul>';
            }
            catch (err) {
                document.getElementById('status').innerText = String(err);
            }
        };
    });
})();
