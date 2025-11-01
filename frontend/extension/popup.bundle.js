// Self-contained popup bundle (vanilla JS) replacing the placeholder.
// This bundle provides the popup UI, persists current user and backend URL in chrome.storage,
// and calls the Flick-Picker backend API.
window.__PREACT_LOADED__ = true;
(function () {
	const DEFAULT_BACKEND = 'http://localhost:8000';

	function el(tag, attrs = {}, ...children) {
		const e = document.createElement(tag);
		for (const k in attrs) {
			if (k === 'style' && typeof attrs[k] === 'object') {
				Object.assign(e.style, attrs[k]);
			} else if (k.startsWith('on') && typeof attrs[k] === 'function') {
				e.addEventListener(k.substring(2).toLowerCase(), attrs[k]);
			} else {
				e.setAttribute(k, attrs[k]);
			}
		}
		for (const c of children) {
			if (typeof c === 'string') e.appendChild(document.createTextNode(c));
			else if (c) e.appendChild(c);
		}
		return e;
	}

	function withStorage(keys) {
		return new Promise((resolve) => chrome.storage.local.get(keys, resolve));
	}

	function setStorage(obj) {
		return new Promise((resolve) => chrome.storage.local.set(obj, resolve));
	}

	function apiBaseFromStorage(items) {
		return (items && items.backendUrl) || DEFAULT_BACKEND;
	}

	async function requestJson(base, path, opts = {}) {
		const res = await fetch(base + path, opts);
		if (!res.ok) throw new Error('API ' + res.status + ' ' + res.statusText);
		return res.json();
	}

	function spinner() {
		const s = el('div', { style: { width: '20px', height: '20px', border: '3px solid rgba(255,255,255,0.2)', borderTop: '3px solid #fff', borderRadius: '50%', animation: 'spin 1s linear infinite' } });
		return s;
	}

	const styleEl = document.createElement('style');
	styleEl.textContent = `
		@keyframes spin { from { transform: rotate(0deg);} to { transform: rotate(360deg);} }
		.fp-dark { background: #0f1720; color: #e6eef6; }
		.fp-card { width: 360px; padding: 12px; border-radius: 8px; box-shadow: 0 6px 18px rgba(0,0,0,0.6); font-family: Inter, Arial, sans-serif; }
		.fp-input { width: 100%; padding: 8px; margin-top:6px; border-radius:6px; border: none; background: #0b1220; color: #e6eef6 }
		.fp-btn { width:100%; padding:8px; margin-top:8px; border-radius:6px; border:none; background:#2563eb; color:white; cursor:pointer }
		.fp-btn.secondary { background:#475569 }
		.fp-status { margin-top:8px }
		.fp-error { color:#ff7b7b }
		.fp-recs { margin-top:8px; max-height:260px; overflow:auto }
		.fp-recs ul { padding-left: 18px }
	`;
	document.head.appendChild(styleEl);

	async function main() {
		const root = document.getElementById('app-root') || document.body;
		root.innerHTML = '';
		root.classList.add('fp-dark');

		const container = el('div', { class: 'fp-card' });
		const title = el('h3', {}, 'Flick Picker');
		const nameInput = el('input', { placeholder: 'Your name', class: 'fp-input', id: 'name-input' });
		const createBtn = el('button', { class: 'fp-btn' }, 'Create / Set User');
		const tmdbInput = el('input', { placeholder: 'TMDB ID', class: 'fp-input', id: 'tmdb-input' });
		const addBtn = el('button', { class: 'fp-btn secondary' }, 'Add Watched');
		const recBtn = el('button', { class: 'fp-btn' }, 'Get Recommendations');
		const status = el('div', { class: 'fp-status', id: 'status' });
		const recsEl = el('div', { class: 'fp-recs', id: 'recs' });

		container.appendChild(title);
		container.appendChild(nameInput);
		container.appendChild(createBtn);
		container.appendChild(tmdbInput);
		container.appendChild(addBtn);
		container.appendChild(recBtn);
		container.appendChild(status);
		container.appendChild(recsEl);
		root.appendChild(container);

		function setLoading(on, msg) {
			if (on) {
				status.innerHTML = '';
				const s = spinner();
				status.appendChild(s);
				if (msg) status.appendChild(el('span', { style: { marginLeft: '8px' } }, msg));
				createBtn.disabled = true; addBtn.disabled = true; recBtn.disabled = true;
			} else {
				createBtn.disabled = false; addBtn.disabled = false; recBtn.disabled = false;
			}
		}

		function showError(msg) {
			status.innerHTML = '';
			const e = el('div', { class: 'fp-error' }, msg);
			status.appendChild(e);
		}

		function showMessage(msg) {
			status.innerHTML = '';
			status.appendChild(el('div', {}, msg));
		}

			function renderRecs(list) {
				if (!list || list.length === 0) {
					recsEl.innerHTML = '<p>No recommendations yet.</p>';
					return;
				}
				// TMDB image base
				const IMG_BASE = 'https://image.tmdb.org/t/p/w185';
				recsEl.innerHTML = '';
				const ul = document.createElement('ul');
				ul.style.paddingLeft = '18px';
						for (const r of list) {
					const li = document.createElement('li');
					li.style.marginBottom = '10px';
					li.style.display = 'flex';
					li.style.gap = '8px';
					li.style.alignItems = 'center';

							// Make item clickable to open modal with more details
							li.style.cursor = 'pointer';
							li.addEventListener('click', async (ev) => {
								// Prevent clicks from anchor elements inside
								if (ev.target && (ev.target.tagName === 'A' || ev.target.tagName === 'BUTTON' || ev.target.tagName === 'IMG')) return;
								try {
									const items = await withStorage(['backendUrl']);
									const base = apiBaseFromStorage(items);
									const details = await requestJson(base, `/movies/${r.tmdb_id}`);
									showModal(details);
								} catch (e) {
									showError('Could not load movie details: ' + e.message);
								}
							});

					const imgWrap = document.createElement('div');
					imgWrap.style.width = '64px';
					imgWrap.style.height = '96px';
					imgWrap.style.flex = '0 0 64px';
									if (r.poster_path) {
										const img = document.createElement('img');
										// use server-side proxy if available
										(async function setImg() {
											try {
												const items = await withStorage(['backendUrl']);
												const base = apiBaseFromStorage(items);
												img.src = base + `/images/tmdb/${r.tmdb_id}/poster?size=w185`;
											} catch (e) {
												img.src = IMG_BASE + r.poster_path;
											}
										})();
						img.alt = r.title;
						img.style.width = '64px';
						img.style.height = '96px';
						img.style.objectFit = 'cover';
						img.style.borderRadius = '4px';
						imgWrap.appendChild(img);
					} else {
						const placeholder = document.createElement('div');
						placeholder.style.width = '64px';
						placeholder.style.height = '96px';
						placeholder.style.background = '#071026';
						placeholder.style.border = '1px solid rgba(255,255,255,0.04)';
						placeholder.style.borderRadius = '4px';
						placeholder.style.display = 'flex';
						placeholder.style.alignItems = 'center';
						placeholder.style.justifyContent = 'center';
						placeholder.style.color = '#4b5563';
						placeholder.innerText = 'No\nImage';
						placeholder.style.whiteSpace = 'pre-line';
						imgWrap.appendChild(placeholder);
					}

				const meta = document.createElement('div');
					meta.style.flex = '1 1 auto';
				const title = document.createElement('div');
				title.innerText = r.title || '(no title)';
				title.style.cursor = 'pointer';
					title.style.fontWeight = '600';
					const details = document.createElement('div');
					details.style.color = '#9fb3d6';
					details.style.fontSize = '12px';
				details.innerHTML = `tmdb ${r.tmdb_id} — score: ${Number(r.score).toFixed(3)} <a href="https://www.themoviedb.org/movie/${r.tmdb_id}" target="_blank" style="color:#7fb0ff;margin-left:8px;text-decoration:none">Open on TMDB</a>`;

					meta.appendChild(title);
					meta.appendChild(details);

					li.appendChild(imgWrap);
					li.appendChild(meta);
					ul.appendChild(li);
				}
				recsEl.appendChild(ul);
			}

					// Modal implementation
					function showModal(details) {
						// remove existing overlay if present
						const existingOverlay = document.getElementById('fp-modal-overlay');
						if (existingOverlay) existingOverlay.remove();

						const modal = document.createElement('div');
						modal.id = 'fp-modal';
						modal.style.position = 'relative';
						modal.style.zIndex = '9999';
						modal.style.background = '#071027';
						modal.style.color = '#e6eef6';
						modal.style.padding = '16px';
						modal.style.borderRadius = '10px';
						modal.style.width = '420px';
						modal.style.maxHeight = '80vh';
						modal.style.overflow = 'auto';
						modal.style.boxShadow = '0 8px 32px rgba(2,6,23,0.8)';

						const close = document.createElement('button');
						close.innerText = 'Close';
						close.style.float = 'right';
						close.style.background = '#1f2937';
						close.style.color = '#fff';
						close.style.border = 'none';
						close.style.padding = '6px 10px';
						close.style.borderRadius = '6px';

						const title = document.createElement('h3');
						title.innerText = details.title || 'Details';

						const overview = document.createElement('p');
						overview.innerText = (details.data && details.data.overview) ? details.data.overview : 'No overview available.';

						const more = document.createElement('div');
						more.style.marginTop = '8px';
						const release = details.data && details.data.release_date ? details.data.release_date : 'Unknown';
						const runtime = details.data && details.data.runtime ? details.data.runtime + ' min' : 'Unknown';
						more.innerHTML = `<div><strong>Release:</strong> ${escapeHtml(release)}</div><div><strong>Runtime:</strong> ${escapeHtml(runtime)}</div>`;

						modal.appendChild(close);
						modal.appendChild(title);
						modal.appendChild(overview);
						modal.appendChild(more);

						// backdrop
								if (details.data && details.data.backdrop_path) {
																			const img = document.createElement('img');
																			// use proxy for backdrop
																			(async function setBackdrop(){
																				try{
																					const items = await withStorage(['backendUrl']);
																					const base = apiBaseFromStorage(items);
																					img.src = base + `/images/tmdb/${details.tmdb_id}/backdrop?size=w780`;
																				}catch(e){
																					img.src = 'https://image.tmdb.org/t/p/w780' + details.data.backdrop_path;
																				}
																			})();
							img.style.width = '100%';
							img.style.borderRadius = '6px';
							img.style.marginTop = '8px';
							modal.appendChild(img);
						}

						// More like this section
						const moreLike = document.createElement('div');
						moreLike.style.marginTop = '12px';
						moreLike.appendChild(document.createElement('hr'));
						const heading = document.createElement('div');
						heading.innerText = 'More like this';
						heading.style.fontWeight = '600';
						heading.style.marginBottom = '8px';
						moreLike.appendChild(heading);
						const grid = document.createElement('div');
						grid.style.display = 'flex';
						grid.style.gap = '8px';
						grid.style.flexWrap = 'wrap';
						moreLike.appendChild(grid);

						// fetch similar movies
						(async function loadSimilar() {
							try {
								const items = await withStorage(['backendUrl']);
								const base = apiBaseFromStorage(items);
								const sim = await requestJson(base, `/movies/${details.tmdb_id}/recommend`);
								if (!sim || sim.length === 0) {
									const p = document.createElement('div'); p.innerText = 'No similar movies found.'; moreLike.appendChild(p); return;
								}
								for (const s of sim) {
									const card = document.createElement('div');
									card.style.width = '90px';
									card.style.cursor = 'pointer';
									card.style.textAlign = 'center';
									const img = document.createElement('img');
									if (s.poster_path) img.src = 'https://image.tmdb.org/t/p/w185' + s.poster_path;
									else img.src = '';
									img.style.width = '90px';
									img.style.height = '135px';
									img.style.objectFit = 'cover';
									img.style.borderRadius = '6px';
									const t = document.createElement('div'); t.style.fontSize = '12px'; t.style.marginTop = '6px'; t.innerText = s.title;
									card.appendChild(img); card.appendChild(t);
									// click opens TMDB page
									card.addEventListener('click', () => {
										window.open(`https://www.themoviedb.org/movie/${s.tmdb_id}`, '_blank');
									});
									grid.appendChild(card);
								}
							} catch (e) {
								const p = document.createElement('div'); p.innerText = 'Unable to load similar items.'; p.style.color = '#ffb4b4'; moreLike.appendChild(p);
							}
						})();

						modal.appendChild(moreLike);

						const overlay = document.createElement('div');
						overlay.id = 'fp-modal-overlay';
						overlay.style.position = 'fixed';
						overlay.style.left = '0';
						overlay.style.top = '0';
						overlay.style.right = '0';
						overlay.style.bottom = '0';
						overlay.style.background = 'rgba(0,0,0,0.6)';
						overlay.style.zIndex = '9998';
						overlay.appendChild(modal);
						overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
						close.addEventListener('click', () => overlay.remove());
						document.body.appendChild(overlay);
					}

		// Load stored values
		const items = await withStorage(['backendUrl', 'currentUser']);
		const base = apiBaseFromStorage(items);
		// Auto-login behavior: if currentUser exists with an id but no name, fetch user info from backend
		if (items.currentUser && items.currentUser.id) {
			let cu = items.currentUser;
			try {
				setLoading(true, 'Recovering user...');
				if (!cu.name) {
					const fetched = await requestJson(base, `/users/${cu.id}`);
					cu = fetched;
					await setStorage({ currentUser: cu });
				}
				showMessage(`User: ${cu.name} (id=${cu.id})`);
				// pre-fill name input for quick actions
				nameInput.value = cu.name || '';
				// Auto-fetch recommendations
				setLoading(true, 'Fetching recommendations...');
				try {
					const recs = await requestJson(base, `/users/${cu.id}/recommend`);
					renderRecs(recs);
				} catch (e) {
					showError('Could not fetch recommendations: ' + e.message);
				} finally { setLoading(false); }
			} catch (e) {
				// If fetch failed, show id and note offline
				showError(`User id saved: ${cu.id} (name unknown)`);
				setLoading(false);
			}
		}

		createBtn.addEventListener('click', async () => {
			const name = nameInput.value.trim();
			if (!name) return showError('Enter a name');
			try {
				setLoading(true, 'Creating user...');
				const user = await requestJson(base, '/users', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) });
				await setStorage({ currentUser: user });
				showMessage(`User set: ${user.name} (id=${user.id})`);
				nameInput.value = user.name;
			} catch (e) { showError(String(e)); }
			finally { setLoading(false); }
		});

		addBtn.addEventListener('click', async () => {
			const v = parseInt(tmdbInput.value || '0');
			const st = await withStorage(['currentUser', 'backendUrl']);
			const b = apiBaseFromStorage(st);
			if (!st.currentUser) { return showError('Set a user first'); }
			try {
				setLoading(true, 'Adding watched...');
				const r = await requestJson(b, `/users/${st.currentUser.id}/history`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ tmdb_id: v }) });
				showMessage('Added watched');
			} catch (e) { showError(String(e)); }
			finally { setLoading(false); }
		});

		recBtn.addEventListener('click', async () => {
			const st = await withStorage(['currentUser', 'backendUrl']);
			const b = apiBaseFromStorage(st);
			if (!st.currentUser) { return showError('Set a user first'); }
			try {
				setLoading(true, 'Fetching recommendations...');
				const recs = await requestJson(b, `/users/${st.currentUser.id}/recommend`);
				renderRecs(recs);
			} catch (e) { showError(String(e)); }
			finally { setLoading(false); }
		});
	}

	function escapeHtml(s) {
		return String(s).replace(/[&<>"]/g, function (c) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; });
	}

	try { main(); } catch (e) { console.error(e); }
})();
