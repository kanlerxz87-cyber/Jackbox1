#!/usr/bin/env node
/**
 * Rebuilds the parts of the site that are derived from the data layer or shared
 * across pages, so they cannot drift:
 *
 *   - the .nav block on every page (single source of truth here)
 *   - the verified-metric tables on pages that declare <!--TABLE:METRICS ...-->
 *   - the source register table on pages/sources.html
 *   - the unverified/flagged table on pages/flagged.html
 *   - the data freshness stamp in the footer
 *
 * Idempotent: running it twice produces byte-identical output.
 */
import { readFileSync, writeFileSync, existsSync, readdirSync } from 'node:fs';
import { join, dirname, resolve, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

import { SOURCES, ACCESSED } from '../data/sources.mjs';
import { METRICS } from '../data/records.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..'); // this tree's directory
// Directory name this tree is published under, relative to the GitHub Pages root.
// Derived from the path so moving the tree cannot silently break every link.
const PUB = ROOT.split('/').pop();

/* ------------------------------------------------------------------ */
/* navigation                                                          */
/* ------------------------------------------------------------------ */
const NAV = [
  ['index.html', 'Overview'],
  ['pages/economics.html', 'Trade Area'],
  ['pages/worksheet.html', 'Sell v Hold'],
  ['pages/decision-gates.html', 'Decision Gates'],
  ['pages/hazards.html', 'Hazards'],
  ['pages/tract-trends.html', 'Tract Trends'],
  ['pages/rental-evidence.html', 'Rental Evidence'],
  ['pages/lease-abstract.html', 'Lease Abstract'],
  ['pages/risks.html', 'Risks'],
  ['pages/open-questions.html', 'Open Questions'],
  ['pages/suggestions.html', 'Suggestions'],
  ['pages/flagged.html', 'Flagged'],
  ['pages/sources.html', 'Sources'],
  ['pages/advisory-summary.html', 'Summary'],
  ['pages/privacy.html', 'Privacy'],
];

function navHtml(isRoot) {
  const items = NAV.map(([href, label]) => {
    // From this tree's index.html, page links live one directory down plus the
    // publish prefix (this tree is served from /<PUB>/).
    // From a page inside pages/, siblings are bare filenames and index.html is one level up.
    let full;
    if (isRoot) {
      // This tree's index.html is served as /<PUB>/, so sibling page links stay
      // relative. Prefixing here would double the directory name.
      full = href;
    } else {
      full = href === 'index.html' ? '../index.html' : href.replace(/^pages\//, '');
    }
    return `    <a href="${full}">${label}</a>`;
  }).join('\n');
  return `<nav class="nav" aria-label="Sections">\n  <div class="nav-inner">\n${items}\n  </div>\n</nav>`;
}

/* ------------------------------------------------------------------ */
/* helpers                                                             */
/* ------------------------------------------------------------------ */
const esc = (s) =>
  String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

const SRC_PREFIX = (isRoot) => (isRoot ? '' : '../');

function srcLink(key, isRoot, label) {
  const s = SOURCES[key];
  if (!s) return `<span class="pill pill--stop">missing source</span>`;
  const org = s.org.replace(/^U\.S\. /, '').replace(/ — .*$/, '');
  return `<a class="src" href="${s.url}" target="_blank" rel="noopener" title="${esc(s.title)}">${esc(label || org)} ↗</a>`;
}

function statusPill(m) {
  if (m.status === 'unverified') return '<span class="pill pill--stop">Unverified</span>';
  if (m.derived) return '<span class="pill pill--warn">Derived</span>';
  return '<span class="pill pill--ok">Verified</span>';
}

function granularityPill(g) {
  const map = {
    parcel: ['--warn', 'Parcel'],
    tract: ['--info', 'Tract'],
    lease: ['--neutral', 'Lease'],
    owner: ['--neutral', 'Owner'],
    submarket: ['--info', 'Submarket'],
    county: ['--ok', 'County'],
    city: ['--ok', 'City'],
    state: ['--ok', 'State'],
    msa: ['--ok', 'Metro'],
    national: ['--ok', 'National'],
    company: ['--ok', 'Tenant'],
    portfolio: ['--ok', 'Portfolio'],
  };
  const [mod, label] = map[g] || ['--neutral', g || 'n/a'];
  return `<span class="pill pill--${mod.replace('--', '')}">${esc(label)}</span>`;
}

/**
 * Metric table.
 * opts: { w: 'W-01' | ['W-01','W-02'] , category, ids, showSourceText }
 */
function metricTable(list, isRoot, opts = {}) {
  const rows = list
    .map((m) => {
      const value = m.status === 'unverified'
        ? '<span class="muted">—</span>'
        : esc(m.display ?? m.value);
      const ev = m.status === 'unverified'
        ? `<span class="muted">${esc(m.evidence)}</span>`
        : esc(m.evidence);
      return `<tr>
        <td><code>${esc(m.id)}</code></td>
        <td>${esc(m.metric)}</td>
        <td class="num">${m.status === 'unverified' ? '<span class="blank">—</span>' : value}</td>
        <td class="nowrap">${esc(m.period)}</td>
        <td>${granularityPill(m.granularity)}</td>
        <td>${statusPill(m)}</td>
        <td class="small">${ev}</td>
        <td>${srcLink(m.source, isRoot)}</td>
      </tr>`;
    })
    .join('\n');

  return `<div class="table-scroll">
<table>
  <caption><strong>${esc(opts.caption || 'Evidence table')}</strong>
  ${esc(opts.note || 'Every value is transcribed from the linked official source. Unverified rows are left empty on purpose.')}</caption>
  <thead><tr>
    <th>ID</th><th>Metric</th><th class="num">Value</th><th>Period</th>
    <th>Level</th><th>Status</th><th>Evidence quoted from source</th><th>Official source</th>
  </tr></thead>
  <tbody>
${rows}
  </tbody>
</table>
</div>`;
}

/* ------------------------------------------------------------------ */
/* filter helper                                                       */
/* ------------------------------------------------------------------ */
function filterBar(targetId, label, placeholder) {
  return `<p class="no-print" style="margin:0 0 .5rem">
  <label for="${targetId}-q" class="small" style="font-weight:700">${esc(label)}</label><br>
  <input id="${targetId}-q" data-filter-for="${targetId}" type="search"
    placeholder="${esc(placeholder)}"
    style="width:100%;max-width:420px;padding:.42rem .55rem;border:1px solid var(--rule);border-radius:6px;font-size:.86rem">
</p>`;
}

/* ------------------------------------------------------------------ */
/* markers                                                             */
/* ------------------------------------------------------------------ */
function renderMetricsDirective(html, isRoot) {
  return html.replace(
    /<!--METRICS:([^>]*?)-->/g,
    (_, spec) => {
      const parts = spec.split('|').map((s) => s.trim());
      const sel = parts[0];                       // e.g. W-01  or  ids:M-001,M-002
      const caption = parts[1] || 'Evidence table';
      const note = parts[2] || undefined;

      let list;
      if (sel.startsWith('ids:')) {
        const ids = sel.slice(4).split(',').map((s) => s.trim());
        list = ids.map((id) => METRICS.find((m) => m.id === id)).filter(Boolean);
      } else if (sel === 'unverified') {
        list = METRICS.filter((m) => m.status === 'unverified');
      } else if (sel === 'verified') {
        list = METRICS.filter((m) => m.status === 'verified');
      } else if (sel.includes(',')) {
        const tags = sel.split(',').map((s) => s.trim());
        list = METRICS.filter((m) => tags.includes(m.w));
      } else {
        list = METRICS.filter((m) => m.w === sel);
      }
      if (!list.length) return `<!-- no rows for ${esc(sel)} -->`;
      return metricTable(list, isRoot, { caption, note });
    }
  );
}

/* ------------------------------------------------------------------ */
/* sources page                                                        */
/* ------------------------------------------------------------------ */
function sourcesTable() {
  const rows = Object.entries(SOURCES)
    .map(([key, s]) => {
      const used = METRICS.filter((m) => m.source === key).length;
      return `<tr>
        <td><code>${esc(key)}</code></td>
        <td>${esc(s.org)}</td>
        <td>${esc(s.title)}</td>
        <td class="small">${esc(s.note || '')}</td>
        <td class="num">${used}</td>
        <td><a class="src" href="${s.url}" target="_blank" rel="noopener">Open ↗</a></td>
      </tr>`;
    })
    .join('\n');
  return `<div class="table-scroll"><table>
  <caption><strong>Official source register — ${Object.keys(SOURCES).length} publishers</strong>
  Fetched and read during this session on ${ACCESSED}. Every row on every other page resolves to one of these.</caption>
  <thead><tr><th>Key</th><th>Publisher</th><th>Document / dataset</th><th>Scope note</th><th class="num">Rows citing it</th><th>Link</th></tr></thead>
  <tbody>
${rows}
  </tbody></table></div>`;
}

/* ------------------------------------------------------------------ */
/* flagged page table                                                  */
/* ------------------------------------------------------------------ */
function flaggedTable() {
  const list = METRICS.filter((m) => m.status === 'unverified');
  return metricTable(list, false, {
    caption: `Unverified register — ${list.length} items`,
    note: 'Every cell in the Value column is intentionally empty. Each row names the official tool that would close it. Nothing here was estimated.',
  });
}

/* ------------------------------------------------------------------ */
/* run                                                                 */
/* ------------------------------------------------------------------ */
const files = [
  join(ROOT, 'index.html'),
  ...(existsSync(join(ROOT, 'pages'))
    ? readdirSync(join(ROOT, 'pages')).filter((f) => f.endsWith('.html')).map((f) => join(ROOT, 'pages', f))
    : []),
].filter(existsSync);

let changed = 0;

for (const file of files) {
  const isRoot = file === join(ROOT, 'index.html');
  let html = readFileSync(file, 'utf8');
  const before = html;

  // nav
  html = html.replace(/<nav class="nav"[\s\S]*?<\/nav>/, navHtml(isRoot));

  // metric directives
  html = renderMetricsDirective(html, isRoot);

  // sources table
  html = html.replace(/<!--SOURCES_TABLE-->/, sourcesTable());

  // flagged table
  html = html.replace(/<!--FLAGGED_TABLE-->/, flaggedTable());

  // freshness stamp
  html = html.replace(/<!--STAMP-->/g, `Evidence cut-off ${ACCESSED}`);

  if (html !== before) {
    writeFileSync(file, html);
    changed++;
    console.log('  rebuilt ' + relative(ROOT, file));
  }
}

console.log(`\n  build complete — ${changed} page(s) updated, ${files.length} scanned\n`);
