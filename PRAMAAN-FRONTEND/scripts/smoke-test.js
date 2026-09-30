import fs from 'node:fs';
import path from 'node:path';

const required = [
  'index.html',
  'package.json',
  'vite.config.js',
  'src/App.jsx',
  'src/main.jsx',
  'src/core/pramaanRuntime.js',
  'src/styles/global.css',
  'public/favicon.svg',
];

const missing = required.filter((file) => !fs.existsSync(path.resolve(file)));
if (missing.length) {
  console.error('Missing required files:', missing.join(', '));
  process.exit(1);
}
const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
if (pkg.scripts.dev !== 'vite') process.exit(1);
console.log('PRAMAAN frontend smoke test: PASS');
