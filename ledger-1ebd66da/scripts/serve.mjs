#!/usr/bin/env node
/** Tiny static server for local preview only. Binds 0.0.0.0 so the Arena preview proxy can reach it. */
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { join, resolve, extname, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const PORT = Number(process.env.PORT || 4173);

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.txt': 'text/plain; charset=utf-8',
  '.ico': 'image/x-icon',
};

createServer(async (req, res) => {
  try {
    let p = decodeURIComponent((req.url || '/').split('?')[0]);
    if (p === '/' || p === '') p = '/index.html';
    let file = join(ROOT, p);
    if (!file.startsWith(ROOT)) { res.writeHead(403).end('forbidden'); return; }
    let s;
    try { s = await stat(file); } catch { s = null; }
    if (s?.isDirectory()) { file = join(file, 'index.html'); }
    const body = await readFile(file);
    res.writeHead(200, {
      'content-type': TYPES[extname(file)] || 'application/octet-stream',
      'cache-control': 'no-store',
      'x-content-type-options': 'nosniff',
    });
    res.end(body);
  } catch {
    res.writeHead(404, { 'content-type': 'text/html; charset=utf-8' });
    res.end('<h1>404</h1><p><a href="/index.html">Back to the workspace</a></p>');
  }
}).listen(PORT, '0.0.0.0', () => {
  console.log(`serving ${ROOT} on http://0.0.0.0:${PORT}`);
});
