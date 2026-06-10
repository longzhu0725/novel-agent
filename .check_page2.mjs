// Use jsdom to load the Vite dev server page and execute scripts
import { JSDOM, VirtualConsole, ResourceLoader } from '/workspace/frontend/node_modules/jsdom/lib/api.js';

const virtualConsole = new VirtualConsole();
const errors = [];
const consoleLogs = [];

virtualConsole.on('error', (...args) => {
  errors.push(`[error] ${args.map(a => a?.message || a).join(' ')}`);
});
virtualConsole.on('warn', (...args) => {
  consoleLogs.push(`[warn] ${args.join(' ')}`);
});
virtualConsole.on('jsdomError', (err) => {
  errors.push(`[jsdomError] ${err.message || err}`);
  if (err.detail) errors.push(`  detail: ${err.detail.message || err.detail}`);
});
virtualConsole.on('log', (...args) => {
  consoleLogs.push(`[log] ${args.join(' ')}`);
});
virtualConsole.on('info', (...args) => {
  consoleLogs.push(`[info] ${args.join(' ')}`);
});

// Allow loading external resources
class ProxyLoader extends ResourceLoader {
  fetch(url, options) {
    return super.fetch(url, options);
  }
}

const dom = await JSDOM.fromURL('http://127.0.0.1:5173/', {
  runScripts: 'dangerously',
  resources: new ProxyLoader(),
  pretendToBeVisual: true,
  virtualConsole,
});

console.log('=== Loading page, waiting 8s for JS to execute ===');
await new Promise(r => setTimeout(r, 8000));

const root = dom.window.document.getElementById('root');
console.log('=== Root innerHTML length:', root?.innerHTML?.length || 0);
console.log('=== Root innerHTML (first 1500 chars) ===');
console.log(root?.innerHTML?.substring(0, 1500) || 'no root');
console.log();
console.log('=== Body text content (first 1000 chars) ===');
console.log(dom.window.document.body.textContent?.substring(0, 1000) || 'empty');
console.log();
console.log('=== Errors (' + errors.length + ') ===');
errors.forEach(e => console.log(e));
console.log('=== Console logs (last 20) ===');
consoleLogs.slice(-20).forEach(l => console.log(l));

dom.window.close();
