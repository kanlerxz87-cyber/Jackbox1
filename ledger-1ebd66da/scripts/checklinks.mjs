#!/usr/bin/env node
/**
 * Real-HTTP link check.
 *
 * verify.mjs resolves internal links on the filesystem, which cannot catch a
 * prefix that is wrong only when the site is actually served from a
 * subdirectory (e.g. a doubled `/<dir>/<dir>/`). This script crawls the tree
 * over HTTP against a running server and follows every internal reference
 * exactly as a browser would.
 *
 * Usage:
 *   python3 -m http.server 4173 --bind 0.0.0.0 &   # serve the repo root
 *   node scripts/checklinks.mjs [baseUrl] [treePath]
 *
 * Defaults: http://127.0.0.1:4173  /<this directory's name>/
 */
import { readFileSync, readdirSync } from 'node:fs';
import { join, dirname, resolve, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const PUB = ROOT.split('/').pop();

const BASE = (process.argv[2] || 'http://127.0.0.1:4173').replace(/\/$/, '');
const TREE = (process.argv[3] || `/${PUB}/`).replace(/\/?$/, '/');

const files = [
  join(ROOT, 'index.html'),
  ...readdirSync(join(ROOT, 'pages')).filter((f) => f.endsWith('.html')).map((f) => join(ROOT, 'pages', f)),
];

/** Map a repo file to its URL path under the published tree. */
function urlPathFor(file) {
  const rel = relative(ROOT, file).split('/').map(encodeURIComponent).join('/');
  return TREE + rel;
}

const seen = new Set();
const checked = [];
const failures = [];

async function head(url) {
  const res = await fetch(url, { method: 'GET', redirect: 'follow' });
  res.body?.cancel?.();
  return res.status;
}

let refCount = 0;

for (const file of files) {
  const html = readFileSync(file, 'utf8');
  const pageUrl = BASE + urlPathFor(file);

  for (const m of html.matchAll(/(?:href|src)="([^"]*)"/g)) {
    const raw = m[1];
    if (!raw || raw.startsWith('#') || /^(https?:|mailto:|tel:|data:|javascript:)/i.test(raw)) continue;

    // Resolve the way a browser does: relative to the page's own URL.
    const resolved = new URL(raw, pageUrl).toString();
    if (!resolved.startsWith(BASE)) continue;
    const path = resolved.slice(BASE.length).split('#')[0].split('?')[0];
    if (seen.has(path)) continue;
    seen.add(path);
    refCount++;

    let status;
    try {
      status = await head(resolved);
    } catch (e) {
      status = 'ERR ' + e.message;
    }
    checked.push({ path, status });
    if (status !== 200) failures.push({ page: relative(ROOT, file), path, status });
  }
}

console.log('');
console.log('  HTTP link check');
console.log('  ' + '─'.repeat(58));
console.log(`  base           : ${BASE}`);
console.log(`  tree           : ${TREE}`);
console.log(`  pages crawled  : ${files.length}`);
console.log(`  unique targets : ${refCount}`);

if (failures.length) {
  console.log('');
  console.log(`  BROKEN (${failures.length})`);
  for (const f of failures) console.log(`   ✗ ${f.path}  [${f.status}]  from ${f.page}`);
  console.log('');
  process.exit(1);
}

console.log('');
console.log('  All internal links resolve over HTTP.');
console.log('');
