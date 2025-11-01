// Self-contained options bundle (vanilla JS) replacing the placeholder.
window.__PREACT_LOADED__ = true;
(function () {
	function el(tag, attrs = {}, ...children) {
		const e = document.createElement(tag);
		for (const k in attrs) {
			if (k === 'style' && typeof attrs[k] === 'object') Object.assign(e.style, attrs[k]);
			else if (k.startsWith('on') && typeof attrs[k] === 'function') e.addEventListener(k.substring(2).toLowerCase(), attrs[k]);
			else e.setAttribute(k, attrs[k]);
		}
		for (const c of children) { if (typeof c === 'string') e.appendChild(document.createTextNode(c)); else if (c) e.appendChild(c); }
		return e;
	}

	function withStorage(keys) { return new Promise((res) => chrome.storage.local.get(keys, res)); }
	function setStorage(obj) { return new Promise((res) => chrome.storage.local.set(obj, res)); }
	function removeStorage(keys) { return new Promise((res) => chrome.storage.local.remove(keys, res)); }

	async function main() {
		// attach to body
		const root = document.body;
		root.style.fontFamily = 'Arial';
		root.style.padding = '12px';
		root.innerHTML = '';

		const title = el('h3', {}, 'Flick Picker Options');
		const backendLabel = el('label', {}, 'Backend URL');
		const backendInput = el('input', { style: { width: '100%' }, id: 'backend' });
		const userLabel = el('label', { style: { marginTop: '8px', display: 'block' } }, 'Persisted User ID');
		const userInput = el('input', { style: { width: '100%' }, id: 'userid' });
		const saveBtn = el('button', { style: { marginTop: '8px' } }, 'Save');
		const clearBtn = el('button', { style: { marginLeft: '8px' } }, 'Clear');
		const status = el('div', { style: { marginTop: '8px', color: 'green' }, id: 'status' });

		root.appendChild(title);
		root.appendChild(backendLabel);
		root.appendChild(backendInput);
		root.appendChild(userLabel);
		root.appendChild(userInput);
		root.appendChild(saveBtn);
		root.appendChild(clearBtn);
		root.appendChild(status);

		const items = await withStorage(['backendUrl', 'currentUser']);
		if (items.backendUrl) backendInput.value = items.backendUrl;
		if (items.currentUser) userInput.value = String(items.currentUser.id || '');

		saveBtn.addEventListener('click', async () => {
			const b = backendInput.value || '';
			const uid = userInput.value.trim();
			const cu = uid ? { id: parseInt(uid) } : null;
			await setStorage({ backendUrl: b, currentUser: cu });
			status.textContent = 'Saved';
		});

		clearBtn.addEventListener('click', async () => {
			await removeStorage(['backendUrl', 'currentUser']);
			backendInput.value = '';
			userInput.value = '';
			status.textContent = 'Cleared';
		});
	}

	try { main(); } catch (e) { console.error(e); }
})();
