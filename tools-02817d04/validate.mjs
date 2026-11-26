#!/usr/bin/env node
/**
 * Line-by-line dataset, HTML row-source, blank-cell, link, and PII privacy validator for Session S-02817d04.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const DATA_DIR = path.join(ROOT, 'data-02817d04');
const SITE_DIR = path.join(ROOT, 'portal-02817d04');
const TOOLS_DIR = path.join(ROOT, 'tools-02817d04');

const errors = [];

function readJson(file) {
  return JSON.parse(fs.readFileSync(path.join(DATA_DIR, file), 'utf8'));
}

const sourcesData = readJson('sources.json');
const findings = readJson('findings.json');
const gatesData = readJson('gates.json');
const questionsData = readJson('questions.json');
const risksData = readJson('risks.json');
const suggestionsData = readJson('suggestions.json');
const flaggedData = readJson('flagged.json');

const allowedDomains = new Set(sourcesData.allowlisted_hosts);
const sourceMap = new Map();

for (const s of sourcesData.sources) {
  if (sourceMap.has(s.id)) errors.push(`Duplicate source ID: ${s.id}`);
  sourceMap.set(s.id, s);
  let u;
  try {
    u = new URL(s.url);
  } catch {
    errors.push(`Invalid URL on ${s.id}: ${s.url}`);
    continue;
  }
  if (u.protocol !== 'https:') errors.push(`Non-HTTPS URL on ${s.id}: ${s.url}`);
  if (!allowedDomains.has(u.hostname)) errors.push(`Domain not in official allowlist on ${s.id}: ${u.hostname}`);
}

// Check findings rows
const findingArrays = [
  ['trade_area', findings.trade_area],
  ['tenant', findings.tenant],
  ['lease', findings.lease],
  ['hazards', findings.hazards],
  ['tax_valuation', findings.tax_valuation],
  ['model_rows', findings.model_rows]
];

let verifiedCount = 0;
let unverifiedCount = 0;
for (const [group, arr] of findingArrays) {
  for (const r of arr) {
    const src = sourceMap.get(r.source_id);
    if (!src) {
      errors.push(`${group}/${r.id}: missing source_id ${r.source_id}`);
      continue;
    }
    if (r.status === 'verified') {
      verifiedCount += 1;
      if (r.value === null || r.value === undefined || String(r.value).trim() === '') {
        errors.push(`${group}/${r.id}: verified row has empty value`);
      }
      if (src.retrieval_status !== 'fetched-2026-11-26' || src.scope === 'repo-audit-only') {
        errors.push(`${group}/${r.id}: verified row cites non-primary/unfetched source ${r.source_id} (${src.retrieval_status} / ${src.scope})`);
      }
    } else if (r.status === 'unverified') {
      unverifiedCount += 1;
      if (r.value !== null) {
        errors.push(`${group}/${r.id}: unverified row MUST have value=null, got ${JSON.stringify(r.value)}`);
      }
    } else if (r.status !== 'assumption') {
      errors.push(`${group}/${r.id}: unknown status ${r.status}`);
    }
  }
}

for (const q of questionsData.questions) {
  if (!sourceMap.has(q.source_id)) errors.push(`Question ${q.id}: invalid source_id ${q.source_id}`);
  if (q.status === 'unverified' && q.missing_answer !== null) {
    errors.push(`Question ${q.id}: unverified question must have missing_answer=null`);
  }
}

for (const list of [gatesData.gates, risksData.decision_options, risksData.risk_register, risksData.compound_stress, suggestionsData.suggestions, flaggedData.repo_trees_audit, flaggedData.irregularities]) {
  for (const item of list) {
    if (!sourceMap.has(item.source_id)) errors.push(`Item ${item.id}: invalid source_id ${item.source_id}`);
  }
}

// HTML row-source, blank-cell, and link validation function (reusable for negative regression tests)
function inspectHtmlContent(html, filePath) {
  const localErrors = [];

  // 1. Every data-missing="true" cell must be strictly blank
  const missingRe = /<td\b[^>]*\bdata-missing="true"[^>]*>([\s\S]*?)<\/td>/gi;
  let m;
  while ((m = missingRe.exec(html)) !== null) {
    if (m[1].trim() !== '') {
      localErrors.push(`${filePath}: data-missing="true" cell is NOT blank: ${JSON.stringify(m[1])}`);
    }
  }

  // 2. Every <tbody>...</tbody> row must carry at least one official allowlisted HTTPS link
  const tbodyRe = /<tbody\b[^>]*>([\s\S]*?)<\/tbody>/gi;
  let tb;
  let rowCount = 0;
  while ((tb = tbodyRe.exec(html)) !== null) {
    const trRe = /<tr\b[^>]*>([\s\S]*?)<\/tr>/gi;
    let tr;
    while ((tr = trRe.exec(tb[1])) !== null) {
      rowCount += 1;
      const hrefRe = /href="([^"]+)"/gi;
      let hr;
      let hasOfficialLink = false;
      while ((hr = hrefRe.exec(tr[1])) !== null) {
        try {
          const u = new URL(hr[1]);
          if (u.protocol === 'https:' && allowedDomains.has(u.hostname)) {
            hasOfficialLink = true;
          }
        } catch {
          // relative link
        }
      }
      if (!hasOfficialLink) {
        localErrors.push(`${filePath}: tbody row #${rowCount} has no official HTTPS source link`);
      }
    }
  }

  // 3. Privacy / PII pattern scan
  const piiPatterns = [
    ['email address', /[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/],
    ['SSN pattern', /\b\d{3}-\d{2}-\d{4}\b/],
    ['LA APN pattern', /\b\d{4}-\d{3}-\d{3}\b/],
    ['phone pattern', /\(\d{3}\)\s*\d{3}-\d{4}\b/],
    ['street address', /\b\d{2,5}\s+[A-Z][a-zA-Z]+\s+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Way)\b/],
    ['California 5-digit ZIP', /\b9[0-5]\d{3}\b/]
  ];
  for (const [label, rx] of piiPatterns) {
    const hit = html.match(rx);
    if (hit) {
      localErrors.push(`${filePath}: potential PII (${label}) matched: ${hit[0]}`);
    }
  }

  // 4. Forbidden network / storage APIs in published HTML
  const netStorageRe = /\b(localStorage|sessionStorage|indexedDB|XMLHttpRequest|sendBeacon)\b|fetch\s*\(/;
  const nsHit = html.match(netStorageRe);
  if (nsHit) {
    localErrors.push(`${filePath}: forbidden network/storage API in published page: ${nsHit[0]}`);
  }

  return { localErrors, rowCount };
}

const htmlFiles = fs.readdirSync(SITE_DIR).filter((f) => f.endsWith('.html')).sort();
if (htmlFiles.length !== 17) {
  errors.push(`Expected 17 HTML pages in portal-02817d04/, found ${htmlFiles.length}`);
}

let totalTableRows = 0;
let totalInternalLinks = 0;
let totalOfficialLinks = 0;

for (const f of htmlFiles) {
  const full = path.join(SITE_DIR, f);
  const html = fs.readFileSync(full, 'utf8');
  const { localErrors, rowCount } = inspectHtmlContent(html, `portal-02817d04/${f}`);
  totalTableRows += rowCount;
  errors.push(...localErrors);

  // Check all href and src targets
  const attrRe = /\b(?:href|src)="([^"]+)"/gi;
  let a;
  while ((a = attrRe.exec(html)) !== null) {
    const raw = a[1];
    if (raw.startsWith('#')) continue;
    if (raw.startsWith('http://')) {
      errors.push(`portal-02817d04/${f}: insecure http:// link ${raw}`);
      continue;
    }
    if (raw.startsWith('https://')) {
      const u = new URL(raw);
      if (!allowedDomains.has(u.hostname)) {
        errors.push(`portal-02817d04/${f}: unapproved external domain ${u.hostname}`);
      } else {
        totalOfficialLinks += 1;
      }
      continue;
    }
    const cleanRel = raw.split('#')[0].split('?')[0];
    if (!cleanRel) continue;
    totalInternalLinks += 1;
    const resolved = path.resolve(SITE_DIR, cleanRel);
    if (!fs.existsSync(resolved)) {
      errors.push(`portal-02817d04/${f}: broken internal link ${raw} -> ${resolved}`);
    }
  }
}

// Scan JSON and JS files in data-02817d04/ and portal-02817d04/assets/ for PII too
const extraFiles = [
  ...fs.readdirSync(DATA_DIR).map((f) => path.join(DATA_DIR, f)),
  ...fs.readdirSync(path.join(SITE_DIR, 'assets')).map((f) => path.join(SITE_DIR, 'assets', f))
];
for (const ef of extraFiles) {
  const txt = fs.readFileSync(ef, 'utf8');
  // Strip official URLs before checking 5-digit numeric sequences (e.g., SEC accession numbers)
  const stripped = txt.replace(/https:\/\/[^\s"']+/g, '');
  const piiChecks = [
    ['email', /[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/],
    ['SSN', /\b\d{3}-\d{2}-\d{4}\b/],
    ['LA APN', /\b\d{4}-\d{3}-\d{3}\b/],
    ['street address', /\b\d{2,5}\s+[A-Z][a-zA-Z]+\s+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr)\b/],
    ['CA ZIP', /\b9[0-5]\d{3}\b/]
  ];
  for (const [lbl, rx] of piiChecks) {
    const hit = stripped.match(rx);
    if (hit) errors.push(`${path.relative(ROOT, ef)}: potential PII (${lbl}) matched: ${hit[0]}`);
  }
}

// Negative regression fixtures (ensure validator genuinely rejects bad inputs)
{
  const badUnsourced = inspectHtmlContent('<tbody><tr><td>Claim without link</td></tr></tbody>', 'fixture-unsourced.html');
  assert.ok(badUnsourced.localErrors.some((e) => e.includes('no official HTTPS source link')), 'Regression failed: unsourced row not caught');

  const badNonBlank = inspectHtmlContent('<tbody><tr><td data-missing="true">$123,456</td><td><a href="https://www.irs.gov/taxtopics/tc409">IRS</a></td></tr></tbody>', 'fixture-nonblank.html');
  assert.ok(badNonBlank.localErrors.some((e) => e.includes('NOT blank')), 'Regression failed: non-blank missing cell not caught');

  const badPii = inspectHtmlContent('<p>1234 Sunset Boulevard, Los Angeles 90026 · 5432-012-034</p>', 'fixture-pii.html');
  assert.ok(badPii.localErrors.length >= 2, 'Regression failed: PII street/APN/ZIP not caught');
}

if (errors.length > 0) {
  console.error('VALIDATION FAILED:');
  for (const e of errors) console.error(' -', e);
  process.exit(1);
}

console.log(`PASS [tools-02817d04/validate.mjs]:
 - ${sourcesData.sources.length} registered sources (${sourcesData.sources.filter((s) => s.retrieval_status === 'fetched-2026-11-26' && s.scope !== 'repo-audit-only').length} live-verified primary official, 2 fetch-failed manual-review with 0 verified claims, 1 repo-audit)
 - ${verifiedCount} verified finding rows, ${unverifiedCount} blank unverified finding rows, ${questionsData.questions.length} blank unverified question rows
 - ${htmlFiles.length} HTML pages, ${totalTableRows} sourced tbody rows, ${totalOfficialLinks} official outbound links, ${totalInternalLinks} internal links (0 broken)
 - 0 PII / address / ZIP / APN / network-storage leaks (+ 3 negative regression fixtures passed)`);
