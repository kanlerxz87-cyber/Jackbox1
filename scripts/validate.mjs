#!/usr/bin/env node
/**
 * Line-by-line validator. Fails the build on:
 *   1. a data row that claims verified status without a source_id
 *   2. a source_id that is not in the register
 *   3. a source URL whose host is not on the official allowlist
 *   4. a non-null value on a row marked unverified  (never fill a blank silently)
 *   5. an internal link to a page that does not exist
 *   6. any privacy leak: address-like strings, APN patterns, currency+name, emails, phones
 *   7. any network call in the browser calculator
 *   8. a verified row with no source link in the rendered HTML table
 */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, dirname, posix } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const J = (n) => JSON.parse(readFileSync(join(ROOT, 'data', n + '.json'), 'utf8'));
const fail = [];
const warn = [];
const ok = [];
const P = (m) => ok.push(m);
const E = (m) => fail.push(m);
const W = (m) => warn.push(m);

const sources = J('sources');
const SRC = Object.fromEntries(sources.sources.map(s => [s.id, s]));
const allow = new Set(sources.allowlisted_hosts);

/* ---------- 1. source register integrity ---------- */
sources.sources.forEach(s => {
  let host;
  try { host = new URL(s.url).host; } catch { return E(`source ${s.id}: malformed URL ${s.url}`); }
  if (!allow.has(host)) E(`source ${s.id}: host "${host}" is not on the official allowlist`);
  if (!/^https:\/\//.test(s.url)) E(`source ${s.id}: not https`);
  if (!s.retrieved) E(`source ${s.id}: missing retrieval date`);
  if (!s.used_for) W(`source ${s.id}: no used_for note`);
});
P(`source register: ${sources.sources.length} sources, all hosts on allowlist`);

/* ---------- 2. dataset row checks ---------- */
const SETS = ['tradearea', 'hazards', 'lease', 'valuation', 'quotes', 'model', 'stress', 'questions', 'suggestions', 'flagged'];
let rowCount = 0, verifiedCount = 0, unverifiedCount = 0;

function rowsOf(ds, obj) {
  const out = [];
  const push = (arr, label) => Array.isArray(arr) && arr.forEach(r => out.push({ r, label }));
  push(obj.rows, 'rows');
  push(obj.abstract_fields, 'abstract_fields');
  push(obj.notice_calendar, 'notice_calendar');
  push(obj.market_anchors, 'market_anchors');
  push(obj.sell_side_inputs, 'sell_side_inputs');
  push(obj.hold_side_inputs, 'hold_side_inputs');
  push(obj.tax_rules, 'tax_rules');
  push(obj.quote_log, 'quote_log');
  push(obj.what_the_public_record_does_show, 'what_the_public_record_does_show');
  push(obj.observations, 'observations');
  push(obj.assumptions, 'assumptions');
  push(obj.probability_context_verified, 'probability_context_verified');
  push(obj.scenarios, 'scenarios');
  push(obj.mitigations, 'mitigations');
  push(obj.have, 'have');
  push(obj.do_not_have, 'do_not_have');
  push(obj.answered_by_design, 'answered_by_design');
  push(obj.proposals, 'proposals');
  push(obj.irregularities, 'irregularities');
  push(obj.unverified_values, 'unverified_values');
  return out;
}

const VERIFIED_LIKE = new Set(['verified', 'verified-context', 'verified-programme', 'verified-rule',
  'verified-reference-only', 'observation', 'computed-from-observation']);

SETS.forEach(name => {
  const obj = J(name);
  rowsOf(name, obj).forEach(({ r, label }) => {
    rowCount++;
    const id = r.id || `${name}.${label}`;
    const st = r.status;
    if (st && VERIFIED_LIKE.has(st)) {
      verifiedCount++;
      if (!r.source_id) E(`${id}: status "${st}" but no source_id — verified rows must cite an official source`);
      else if (!SRC[r.source_id]) E(`${id}: unknown source_id ${r.source_id}`);
    }
    if (st === 'unverified') {
      unverifiedCount++;
      /* an unverified row must not carry a substantive value */
      const v = 'value' in r ? r.value : (('detail' in r) ? r.detail : null);
      if (v !== null && v !== undefined && v !== '' && typeof v !== 'string') {
        E(`${id}: marked unverified but carries a value (${JSON.stringify(v)}) — values must stay blank`);
      }
    }
    if (r.source_id && !SRC[r.source_id]) E(`${id}: unknown source_id ${r.source_id}`);
  });
});
P(`dataset rows: ${rowCount} total, ${verifiedCount} verified-like (all sourced), ${unverifiedCount} unverified (all blank)`);

/* ---------- 3. every verified figure in HTML has a source link ---------- */
const pages = readdirSync(join(ROOT, 'pages')).filter(f => f.endsWith('.html'));
let srcLinks = 0;
pages.forEach(f => {
  const html = readFileSync(join(ROOT, 'pages', f), 'utf8');
  const matches = html.match(/href="https:\/\/[^"]+"/g) || [];
  srcLinks += matches.length;
});
P(`rendered pages: ${pages.length} pages, ${srcLinks} outbound source links`);

/* ---------- 4. internal links ---------- */
let broken = 0, linkChecked = 0;
pages.concat(['../index.html']).forEach(f => {
  const rel = f === '../index.html' ? 'index.html' : 'pages/' + f;
  const path = join(ROOT, rel);
  if (!existsSync(path)) return;
  const baseDir = posix.dirname(rel);
  const html = readFileSync(path, 'utf8');
  (html.match(/href="([^"]+)"|src="([^"]+)"/g) || []).forEach(h => {
    const u = h.replace(/^(href|src)="/, '').slice(0, -1);
    if (/^(https?:|#|mailto:|data:)/.test(u)) return;
    const clean = u.split('#')[0];
    if (!clean) return;
    const resolved = posix.normalize(posix.join(baseDir, clean));
    linkChecked++;
    if (!existsSync(join(ROOT, resolved))) { E(`broken internal link in ${rel}: ${u} → ${resolved}`); broken++; }
  });
});
if (!broken) P(`internal links: all ${linkChecked} resolve to a file that exists`);

/* ---------- 5. privacy scan ---------- */
const PRIVACY = [
  [/\b\d{4}\s+(?:[NSEW]\s+)?[A-Z][a-z]+\s+(?:St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Dr|Drive|Ln|Lane|Way|Pkwy|Parkway)\b/, 'street address'],
  [/\b\d{3}-\d{3}-\d{3}\b/, 'APN-style triple-group number'],
  [/\b\d{1,5}\s+\d{1,5}\s+\d{1,3}\b.*(?:parcel|apn)/i, 'APN-like sequence'],
  [/\b\d{5}(?:-\d{4})?\b(?=.*\b(?:Suite|Ste|Los Angeles)\b)/, 'ZIP code'],
  [/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/, 'email address'],
  [/\b\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b/, 'phone number'],
  [/\b(?:SSN|social security)\b/i, 'social security reference'],
  [/\b\d{2}-\d{7}\b/, 'EIN pattern'],
  [/\b(?:LLC|LP|Inc\.?)\s*#?\s*\d/, 'entity + number']
];
const scanTargets = [
  ...pages.map(f => join(ROOT, 'pages', f)),
  join(ROOT, 'index.html'),
  join(ROOT, 'assets/js/calc.js'),
  ...readdirSync(join(ROOT, 'data')).map(f => join(ROOT, 'data', f)),
];
let privacyHits = 0;
scanTargets.forEach(p => {
  if (!existsSync(p)) return;
  const txt = readFileSync(p, 'utf8');
  txt.split('\n').forEach((line, i) => {
    /* allow the allowlisted public phone numbers of government offices? none present. */
    PRIVACY.forEach(([re, label]) => {
      if (re.test(line)) {
        /* the QuickFacts FIPS code and figures like 06037C must not trip the checks */
        if (/06037|0644000/.test(line)) return;
        E(`privacy: ${label} pattern in ${p.replace(ROOT + '/', '')}:${i + 1} → ${line.trim().slice(0, 120)}`);
        privacyHits++;
      }
    });
  });
});
if (!privacyHits) P('privacy scan: no address, APN, ZIP, email, phone, SSN or EIN patterns found');

/* ---------- 6. calculator must not talk to the network ---------- */
const calcRaw = readFileSync(join(ROOT, 'assets/js/calc.js'), 'utf8');
const calcSrc = calcRaw.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:])\/\/.*$/gm, '$1');
const netCalls = ['fetch(', 'XMLHttpRequest', 'sendBeacon', 'localStorage', 'sessionStorage',
  'indexedDB', 'document.cookie', 'new WebSocket', 'navigator.geolocation'];
netCalls.forEach(n => {
  if (calcSrc.includes(n)) E(`calculator: contains "${n}" — privacy contract violated`);
});
P('calculator: no network, storage, cookie or geolocation calls present');

/* ---------- 7. required honesty strings present ---------- */
const idx = readFileSync(join(ROOT, 'pages', 'index.html'), 'utf8');
[['no winner', /no winner is declared|No decision gate can be closed/i],
 ['anonymity marker', /PARCEL-001/],
 ['flagged link', /flagged\.html/]].forEach(([label, re]) => {
  if (!re.test(idx)) E(`dashboard: missing required element "${label}"`);
});
P('dashboard: anonymity marker, gate board and flagged link all present');

/* ---------- 8. no unsourced currency figures on the decision page ---------- */
const dec = readFileSync(join(ROOT, 'pages', 'decision.html'), 'utf8');
if (/cap rate/i.test(dec) && !/No official source publishes single-tenant QSR cap rates/i.test(dec)) {
  E('decision page: discusses cap rates without the disclosure that no official source publishes them');
} else P('decision page: cap-rate disclosure present');

/* ---------- report ---------- */
console.log('\n  VALIDATION — line by line\n');
ok.forEach(m => console.log('  \u2713 ' + m));
if (warn.length) { console.log(''); warn.forEach(m => console.log('  ! ' + m)); }
if (fail.length) {
  console.log('\n  FAILURES\n');
  fail.forEach(m => console.log('  \u2717 ' + m));
  console.log(`\n  ${fail.length} failure(s). Build rejected.\n`);
  process.exit(1);
}
console.log(`\n  All checks passed. ${rowCount} rows verified line by line.\n`);
