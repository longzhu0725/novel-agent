// Use jsdom to load the Vite dev server page and check for errors
import { JSDOM, VirtualConsole, ResourceLoader } from '/workspace/frontend/node_modules/jsdom/lib/api.js';

const virtualConsole = new VirtualConsole();
const errors = [];
const consoleLogs = [];

virtualConsole.on('error', (err) => {
  errors.push(`[error] ${err.message || err}`);
});
virtualConsole.on('warn', (msg) => {
  consoleLogs.push(`[warn] ${msg}`);
});
virtualConsole.on('jsdomError', (err) => {
  errors.push(`[jsdomError] ${err.message || err}`);
});
virtualConsole.on('log', (msg) => {
  consoleLogs.push(`[log] ${msg}`);
});

// Custom resource loader that proxies through to the right hosts
class ProxyLoader extends ResourceLoader {
  fetch(url, options) {
    // Vite HMR ws & localhost only
    return super.fetch(url, options);
  }
}

const dom = await JSDOM.fromURL('http://127.0.0.1:5173/', {
  runScripts: 'dangerously',
  resources: new ProxyLoader(),
  pretendToBeVisual: true,
  virtualConsole,
});

console.log('=== Loading page, waiting 5s for JS ===');
await new Promise(r => setTimeout(r, 5000));

const root = dom.window.document.getElementById('root');
console.log('=== Root innerHTML (first 3000 chars) ===');
console.log(root ? root.innerHTML.substring(0, 3000) : 'no root');
console.log();
console.log('=== Errors ===');
errors.forEach(e => console.log(e));
console.log('=== Console logs ===');
consoleLogs.slice(-20).forEach(l => console.log(l));
console.log('=== Body text content ===');
console.log(dom.window.document.body.textContent.substring(0, 500));

dom.window.close();
