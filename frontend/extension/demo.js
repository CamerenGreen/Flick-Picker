fetch('/extension/popup.html').then(response => response.text()).then(html => {
  const doc = new DOMParser().parseFromString(html, 'text/html');
  doc.querySelector('.settings').setAttribute('href', '/extension/options.html');
  document.getElementById('demo-root').replaceWith(doc.querySelector('main'));
  const script = document.createElement('script');
  script.src = '/extension/popup.js';
  document.body.appendChild(script);
});
