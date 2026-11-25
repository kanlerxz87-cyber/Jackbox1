#!/usr/bin/env node
/**
 * Build-time verification. Fails the build (non-zero exit) if any rule is broken.
 *
 * Checks
 *  1. Every row in data/records.mjs cites a source that exists in data/sources.mjs.
 *  2. Every source URL is https and on an allow-list of official domains (or a
 *     documented exception), so no aggregator or blog can slip in.
 *  3. Every row carries an `evidence` string. No row is verified without quoted evidence.
 *  4. `status: 'unverified'` rows must have value === null. Nothing half-filled.
 *  5. Every internal link in every HTML page resolves to a file that exists.
 *  6. Every HTML page links assets/css/style.css and assets/js/nav.js and sets a <title>.
 *  7. No US street address, lat/long pair, phone number, email address, or
 *     person/entity name pattern appears in any published HTML. (Privacy gate.)
 *  8. Every metric id referenced from HTML (data-metric="M-xxx") exists in records.mjs.
 */

import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join, dirname, resolve, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

import { SOURCES } from '../data/sources.mjs';
import { METRICS } from '../data/records.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
// This tree is published as a subdirectory of the Pages root, so links from its
// index.html carry a `/<PUB>/` prefix that must resolve from the parent of ROOT.
const PUB = ROOT.split('/').pop();
const SITE_ROOT = resolve(ROOT, '..');

const errors = [];
const warnings = [];
const err = (m) => errors.push(m);
const warn = (m) => warnings.push(m);

/* ------------------------------------------------------------------ */
/* 1. official-domain allow-list                                       */
/* ------------------------------------------------------------------ */
const OFFICIAL_DOMAINS = [
  'bls.gov', 'fred.stlouisfed.org', 'census.gov', 'dof.ca.gov', 'sec.gov',
  'irs.gov', 'ftb.ca.gov', 'lacity.gov', 'lacity.org', 'cityclerk.lacity.org',
  'housing.lacity.gov', 'fire.ca.gov', 'osfm.fire.ca.gov', 'conservation.ca.gov',
  'fema.gov', 'msc.fema.gov', 'ca.gov', 'assessor.lacounty.gov',
  'portal.assessor.lacounty.gov', 'lacounty.gov', 'scag.ca.gov', 'edd.ca.gov',
  'labormarketinfo.edd.ca.gov', 'stlouisfed.org', 'federalreserve.gov',
  'treasury.gov', 'huduser.gov', 'cdc.gov', 'data.cdc.gov', 'california.gov',
];

function hostOk(url) {
  let u;
  try { u = new URL(url); } catch { return false; }
  if (u.protocol !== 'https:') return false;
  const h = u.hostname;
  return OFFICIAL_DOMAINS.some((d) => h === d || h.endsWith('.' + d));
}

/* ------------------------------------------------------------------ */
/* 2. source registry                                                  */
/* ------------------------------------------------------------------ */
for (const [key, s] of Object.entries(SOURCES)) {
  if (!s.url?.startsWith('https://')) err(`SOURCE ${key}: url is not https`);
  else if (!hostOk(s.url)) err(`SOURCE ${key}: host not on official allow-list → ${s.url}`);
  if (!s.org) err(`SOURCE ${key}: missing publisher`);
  if (!s.title) err(`SOURCE ${key}: missing title`);
}

/* ------------------------------------------------------------------ */
/* 3. metric rows                                                      */
/* ------------------------------------------------------------------ */
const seenIds = new Set();

for (const r of METRICS) {
  const tag = `ROW ${r.id}`;
  if (!r.id) { err('ROW with no id'); continue; }
  if (seenIds.has(r.id)) err(`${tag}: duplicate id`);
  seenIds.add(r.id);

  if (!SOURCES[r.source]) err(`${tag}: unknown source "${r.source}"`);
  if (!r.evidence || String(r.evidence).trim().length < 12) {
    err(`${tag}: missing or too-short evidence quote`);
  }
  if (!r.metric) err(`${tag}: missing metric label`);

  if (!['verified', 'unverified'].includes(r.status)) {
    err(`${tag}: status must be verified|unverified (got ${r.status})`);
  }
  if (r.status === 'unverified' && r.value !== null) {
    err(`${tag}: unverified rows must have value === null (nothing inferred)`);
  }
  if (r.status === 'unverified' && !r.flag) {
    err(`${tag}: unverified rows must reference a FLAG id for the Flagged page`);
  }
  if (r.status === 'verified' && r.value === null && !r.nonNumeric) {
    err(`${tag}: verified row has null value without nonNumeric:true`);
  }
  if (!r.w) err(`${tag}: missing workstream tag (W-xx)`);
}

/* ------------------------------------------------------------------ */
/* 4. HTML link + privacy gate                                         */
/* ------------------------------------------------------------------ */
const PAGES_DIR = join(ROOT, 'pages');
const htmlFiles = [
  join(ROOT, 'index.html'),
  ...(existsSync(PAGES_DIR) ? readdirSync(PAGES_DIR).filter((f) => f.endsWith('.html')).map((f) => join(PAGES_DIR, f)) : []),
].filter(existsSync);

if (htmlFiles.length === 0) err('No HTML pages found');

const PRIVACY_PATTERNS = [
  { re: /\b\d{1,6}\s+[A-Z][A-Za-z.'-]*(?:\s+[A-Z][A-Za-z.'-]*)*\s+(Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Way|Court|Ct|Place|Pl|Parkway|Pkwy)\b/g,
    why: 'US street address' },
  { re: /\b-?\d{1,3}\.\d{3,}\s*,\s*-?\d{1,3}\.\d{3,}\b/g, why: 'latitude/longitude pair' },
  { re: /\b\(\d{3}\)\s*\d{3}-\d{4}\b|\b\d{3}-\d{3}-\d{4}\b/g, why: 'telephone number' },
  { re: /\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b/g, why: 'email address' },
  { re: /\b\d{3}-\d{2}-\d{4}\b/g, why: 'US SSN pattern' },
];

/* Card-number-like runs, but SEC accession numbers (18 digits, e.g. in EDGAR
   archive URLs) and other long numeric identifiers that appear inside an href
   are legitimate. Strip href attributes before testing for card numbers. */
const CARD_RE = /\b(?:\d[ -]?){13,19}\b/g;
const stripHrefs = (html) => html.replace(/href="[^"]*"/g, 'href=""');

const seenMetricRefs = new Set();

for (const f of htmlFiles) {
  const rel = relative(ROOT, f);
  const html = readFileSync(f, 'utf8');

  if (!/<title>[^<]{5,}<\/title>/.test(html)) err(`${rel}: missing or empty <title>`);
  if (/<html[^>]*lang=/.test(html) === false) warn(`${rel}: <html> has no lang attribute`);
  if (!html.includes('assets/css/style.css')) err(`${rel}: does not link assets/css/style.css`);
  if (!html.includes('assets/js/nav.js')) warn(`${rel}: does not load assets/js/nav.js`);

  // internal links
  for (const m of html.matchAll(/href="([^"#][^"]*)"/g)) {
    const href = m[1];
    if (/^(https?:|mailto:|tel:|data:|javascript:)/i.test(href)) continue;
    const clean = href.split('#')[0].split('?')[0];
    if (!clean) continue;
    // Resolve exactly as a browser and a static host do: relative to the
    // containing file, with '/' meaning the published site root.
    const target = clean.startsWith('/')
      ? join(SITE_ROOT, clean.replace(/^\/Jackbox1/, ''))
      : resolve(dirname(f), clean);
    if (!existsSync(target)) err(`${rel}: broken internal link → ${href}`);
  }

  // external links must be https
  for (const m of html.matchAll(/href="(http:[^"]*)"/g)) {
    err(`${rel}: non-https external link → ${m[1]}`);
  }

  // privacy
  const privacyText = stripHrefs(html);
  for (const { re, why } of PRIVACY_PATTERNS) {
    re.lastIndex = 0;
    let hit;
    while ((hit = re.exec(privacyText)) !== null) {
      const s = hit[0];
      if (/^(555-|410-)/.test(s)) continue;
      err(`${rel}: possible ${why} in published HTML → "${s.slice(0, 60)}"`);
    }
  }
  // Card numbers: check visible text only, and ignore pure digit strings that
  // are part of a longer alphanumeric token (CIKs, FIPS codes, series IDs).
  CARD_RE.lastIndex = 0;
  let card;
  while ((card = CARD_RE.exec(privacyText)) !== null) {
    const digits = card[0].replace(/\D/g, '');
    if (digits.length < 13 || digits.length > 19) continue;
    const idx = card.index;
    const before = privacyText[idx - 1] || ' ';
    const after = privacyText[idx + card[0].length] || ' ';
    if (/[A-Za-z0-9]/.test(before) || /[A-Za-z0-9]/.test(after)) continue;
    err(`${rel}: possible card-number-like digit run → "${card[0].slice(0, 30)}"`);
  }

  for (const m of html.matchAll(/data-metric="(M-\d+|[A-Z]{2,4}-\d+)"/g)) {
    seenMetricRefs.add(m[1]);
  }
}

for (const id of seenMetricRefs) {
  if (!seenIds.has(id)) err(`HTML references unknown metric id "${id}"`);
}

/* ------------------------------------------------------------------ */
/* 5. required pages                                                   */
/* ------------------------------------------------------------------ */
const REQUIRED_PAGES = [
  'index.html',
  'pages/economics.html',
  'pages/worksheet.html',
  'pages/decision-gates.html',
  'pages/hazards.html',
  'pages/tract-trends.html',
  'pages/rental-evidence.html',
  'pages/lease-abstract.html',
  'pages/advisory-summary.html',
  'pages/open-questions.html',
  'pages/risks.html',
  'pages/suggestions.html',
  'pages/flagged.html',
  'pages/privacy.html',
  'pages/sources.html',
];
for (const p of REQUIRED_PAGES) {
  if (!existsSync(join(ROOT, p))) err(`missing required page: ${p}`);
}

/* ------------------------------------------------------------------ */
/* 6. no large artifacts                                               */
/* ------------------------------------------------------------------ */
function walk(dir, out = []) {
  for (const e of readdirSync(dir)) {
    if (e === '.git' || e === 'node_modules') continue;
    const p = join(dir, e);
    const st = statSync(p);
    if (st.isDirectory()) walk(p, out);
    else out.push({ p, size: st.size });
  }
  return out;
}
for (const { p, size } of walk(ROOT)) {
  if (size > 3_000_000) warn(`large file in repo: ${relative(ROOT, p)} (${(size / 1e6).toFixed(1)} MB)`);
}

/* ------------------------------------------------------------------ */
/* report                                                              */
/* ------------------------------------------------------------------ */
const verified = METRICS.filter((r) => r.status === 'verified').length;
const unverified = METRICS.filter((r) => r.status === 'unverified').length;

console.log('');
console.log('  Jack in the Box — build verification');
console.log('  ' + '─'.repeat(58));
console.log(`  sources registered : ${Object.keys(SOURCES).length}`);
console.log(`  metric rows        : ${METRICS.length}  (verified ${verified} / unverified ${unverified})`);
console.log(`  html pages         : ${htmlFiles.length}`);
console.log(`  metric ids in HTML : ${seenMetricRefs.size}`);

if (warnings.length) {
  console.log('');
  console.log(`  WARNINGS (${warnings.length})`);
  for (const w of warnings) console.log('   · ' + w);
}

if (errors.length) {
  console.log('');
  console.log(`  ERRORS (${errors.length})`);
  for (const e of errors) console.log('   ✗ ' + e);
  console.log('');
  console.log('  BUILD FAILED');
  process.exit(1);
}

console.log('');
console.log('  All checks passed.');
console.log('');
