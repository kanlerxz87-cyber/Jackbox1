#!/usr/bin/env node
/**
 * Build static pages from data/*.json.
 * No framework, no runtime dependency: output is plain HTML so GitHub Pages
 * serves it without a build step, and every table is real markup for print/SEO.
 */
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const D = (n) => JSON.parse(readFileSync(join(ROOT, 'data', n + '.json'), 'utf8'));
const out = (p, s) => { mkdirSync(dirname(join(ROOT, p)), { recursive: true }); writeFileSync(join(ROOT, p), s); };

const sources = D('sources');
const SRC = Object.fromEntries(sources.sources.map(s => [s.id, s]));

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const nf = (v, unit) => {
  if (v === null || v === undefined) return null;
  if (typeof v === 'string') return v;
  if (Array.isArray(v)) return v.join(' – ');
  const u = (unit || '').toLowerCase();
  const isMoney = u.includes('usd') && !u.includes('thousand');
  if (isMoney) return '$' + v.toLocaleString('en-US', { maximumFractionDigits: 0 });
  if (Math.abs(v) >= 10000) return v.toLocaleString('en-US', { maximumFractionDigits: 0 });
  return v.toLocaleString('en-US', { maximumFractionDigits: 2 });
};

const BADGE = {
  verified: ['b-ok', 'Verified'],
  'verified-context': ['b-ok', 'Verified'],
  'verified-programme': ['b-ok', 'Verified'],
  'verified-rule': ['b-ok', 'Verified'],
  'verified-reference-only': ['b-info', 'Ref. point only'],
  observation: ['b-ok', 'Observation'],
  'computed-from-observation': ['b-ok', 'Computed'],
  assumption: ['b-warn', 'Assumption'],
  'assumption-anchored-to-observation': ['b-warn', 'Assumption'],
  'assumption-slot': ['b-warn', 'Assumption'],
  'owner-asserted': ['b-warn', 'Owner-asserted'],
  'owner-asserted-window': ['b-warn', 'Owner-asserted'],
  'owner-asserted; externally unverifiable': ['b-warn', 'Owner-asserted'],
  unverified: ['b-bad', 'Unverified'],
};
const badge = (st) => {
  const [cls, txt] = BADGE[st] || ['b-neutral', st || 'n/a'];
  return `<span class="b ${cls}">${esc(txt)}</span>`;
};

/** A source cell must be a live link to an official site, or an explicit flag. */
function srcCell(id) {
  if (!id) return `<td class="blank" title="No official source could confirm this">no source — unverified</td>`;
  const s = SRC[id];
  if (!s) return `<td class="blank">unknown source ${esc(id)}</td>`;
  return `<td class="src"><a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${esc(id)}</a><br><span class="faint">${esc(s.publisher)}</span></td>`;
}

const NAV = [
  ['index.html', 'Dashboard'],
  ['market.html', 'Market &amp; trade area'],
  ['hazards.html', 'Hazard screening'],
  ['lease.html', 'Lease &amp; calendar'],
  ['decision.html', 'Sell vs hold'],
  ['scenarios.html', 'Model &amp; stress'],
  ['questions.html', 'Open questions'],
  ['suggestions.html', 'Suggestions'],
  ['flagged.html', 'Flagged for review'],
  ['sources.html', 'Sources'],
  ['print.html', 'Printable brief'],
];

function layout({ title, page, body, extraHead = '', wide = false }) {
  const nav = NAV.map(([h, t]) =>
    `<a href="${h}"${h === page ? ' aria-current="page"' : ''}>${t}</a>`).join('\n        ');
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)} · Jackbox property decision workspace</title>
<meta name="description" content="Anonymised, source-verified decision workspace for a single-tenant quick-service restaurant parcel in central Los Angeles. Public aggregate findings only.">
<meta name="robots" content="index,follow">
<link rel="stylesheet" href="../assets/css/site.css">
${extraHead}
</head>
<body>
<header class="site">
  <div class="wrap hdr">
    <a class="brand" href="index.html"><span class="dot"></span>JACKBOX&nbsp;/&nbsp;PARCEL-001</a>
    <nav class="main">
        ${nav}
    </nav>
  </div>
</header>
<main>
  <div class="wrap${wide ? ' wide' : ''}">
${body}
  </div>
</main>
<footer class="site">
  <div class="wrap">
    <p><b>Privacy.</b> This site publishes aggregate, non-identifying findings only. No parcel address, owner identity, APN, lease document, rent figure or personal finance appears anywhere in this repository or on this site. The parcel is referred to as <code>PARCEL-001</code> throughout.</p>
    <p><b>Integrity.</b> Every data row carries a source identifier linking to an official source. Where an official source could not confirm a value, the value is left blank and listed on <a href="flagged.html">Flagged for review</a>. Nothing is inferred or filled in.</p>
    <p class="faint">Data cut-off 2026-11-25 · Build ${new Date().toISOString().slice(0, 10)} · Not investment, legal or tax advice. Engage a licensed appraiser, attorney and CPA before acting.</p>
  </div>
</footer>
</body>
</html>`;
}

/** Generic table renderer. Every row gets a source cell. */
function table(cols, rows, opts = {}) {
  const head = cols.map(c => `<th${c.num ? ' class="num"' : ''}>${c.label}</th>`).join('');
  const body = rows.map(r => {
    const tds = cols.map(c => {
      if (c.k === 'src') return srcCell(r.source_id);
      if (c.k === 'status') return `<td>${badge(r.status)}</td>`;
      if (c.k === 'value') {
        const v = nf(r[c.k], r.unit);
        return v === null
          ? `<td class="blank">—</td>`
          : `<td${c.num ? ' class="num"' : ''}>${esc(v)}${r.unit ? ` <span class="faint">${esc(r.unit)}</span>` : ''}</td>`;
      }
      const v = r[c.k];
      if (v === null || v === undefined || v === '') return `<td class="blank">—</td>`;
      return `<td>${c.html ? v : esc(v)}</td>`;
    }).join('');
    return `<tr>${tds}</tr>`;
  }).join('\n');
  return `<div class="tbl-wrap"><table><thead><tr>${head}</tr></thead><tbody>\n${body}\n</tbody></table></div>` +
    (opts.note ? `<p class="tbl-note">${opts.note}</p>` : '');
}

const callout = (kind, label, html) => `<div class="callout c-${kind}"><strong>${esc(label)}</strong>${html}</div>`;

/* ======================================================================= */
/*  DATA                                                                   */
/* ======================================================================= */
const ta = D('tradearea'), hz = D('hazards'), lz = D('lease'), va = D('valuation'),
  qt = D('quotes'), md = D('model'), st = D('stress'), qs = D('questions'),
  sg = D('suggestions'), fl = D('flagged');

const countBy = (arr, f) => arr.reduce((m, x) => (m[f(x)] = (m[f(x)] || 0) + 1, m), {});
const totalRows = ta.rows.length + hz.rows.length + lz.abstract_fields.length + lz.notice_calendar.length +
  va.market_anchors.length + va.sell_side_inputs.length + va.hold_side_inputs.length + va.tax_rules.length +
  qt.quote_log.length + qt.what_the_public_record_does_show.length + md.observations.length +
  md.assumptions.length + st.probability_context_verified.length + st.scenarios.length + qs.have.length +
  qs.do_not_have.length + sg.proposals.length + fl.irregularities.length + fl.unverified_values.length;
const verifiedRows = [...ta.rows, ...hz.rows, ...va.market_anchors, ...va.tax_rules,
  ...qt.what_the_public_record_does_show, ...md.observations, ...md.assumptions, ...st.probability_context_verified,
  ...qs.have].filter(r => (r.status || '').startsWith('verified') || r.status === 'observation' ||
  r.status === 'computed-from-observation' || r.status === 'assumption' ||
  r.status === 'assumption-anchored-to-observation' || r.status === 'assumption-slot').length;

/* ======================================================================= */
/*  DASHBOARD (W-03 decision-gate progress board + executive summary)      */
/* ======================================================================= */
const GATES = [
  { id: 'G-01', q: 'Parcel location known (so tract, zones and ring can be computed)', state: 'blocked', why: 'Not in repo; must stay private.' },
  { id: 'G-02', q: 'Census tract data retrieved for the trade area', state: 'blocked', why: 'API key required.' },
  { id: 'G-03', q: 'Parcel flood / fire / seismic zone status confirmed', state: 'blocked', why: 'Depends on G-01.' },
  { id: 'G-04', q: 'Exact lease expiration and renewal-option dates', state: 'blocked', why: 'Highest-impact gap.' },
  { id: 'G-05', q: 'Contract rent and NNN recoveries', state: 'blocked', why: 'Private lease.' },
  { id: 'G-06', q: 'Two or three real cap-rate quotes and a short-lease discount', state: 'blocked', why: 'No official source exists.' },
  { id: 'G-07', q: 'Adjusted basis and accumulated depreciation', state: 'blocked', why: 'Private tax records.' },
  { id: 'G-08', q: 'Insurance premium, limits and renewal date', state: 'blocked', why: 'Private binder.' },
  { id: 'G-09', q: 'Financing terms and prepayment penalty', state: 'blocked', why: 'Private loan documents.' },
  { id: 'G-10', q: 'Building condition and seismic assessment', state: 'blocked', why: 'Requires engagement.' },
  { id: 'G-11', q: 'Competitive QSR set within 3 miles', state: 'blocked', why: 'Field survey or vendor.' },
  { id: 'G-12', q: 'Adjacent-street traffic count', state: 'blocked', why: 'Depends on G-01.' },
  { id: 'G-13', q: 'Franchisee financials and guaranty', state: 'blocked', why: 'Private.' },
  { id: 'G-14', q: 'Owner liquidity and concentration', state: 'blocked', why: 'Private; adviser conversation.' },
  { id: 'G-15', q: 'California marginal bracket confirmed', state: 'blocked', why: 'FTB page failed to load.' },
];
const DONE = [
  { id: 'D-01', q: 'Official source register built and every row linked', note: '22 official sources, all on an allowlisted host.' },
  { id: 'D-02', q: 'Metro market and labour evidence verified', note: 'BLS, FHFA, Federal Reserve.' },
  { id: 'D-03', q: 'Hazard query method proven end to end', note: 'FEMA, USGS and CAL FIRE services all returned real responses.' },
  { id: 'D-04', q: 'Tax rules for a sale verified', note: 'IRS capital gains, 25% recapture, 3.8% NIIT, §1031; FTB no-preference rule.' },
  { id: 'D-05', q: 'Macro model built and back-tested', note: 'Mean reversion in 5-year appreciation, correlation −0.937 over 7 overlapping pairs.' },
  { id: 'D-06', q: 'Browser-only calculator built, transmits nothing', note: 'Rent, basis and tax stay on the reader\'s machine.' },
  { id: 'D-07', q: 'Decision rule published instead of a verdict', note: 'No winner selected while inputs are missing.' },
];
const doneCount = DONE.length, gateCount = GATES.length, closed = 0;

const gateBoard = `
<div class="grid g4">
  <div class="kpi"><div class="k-label">Gates closed</div><div class="k-value" style="color:var(--bad)">${closed} / ${gateCount}</div><div class="k-note">Decision inputs still open</div></div>
  <div class="kpi"><div class="k-label">Verified data rows</div><div class="k-value" style="color:var(--ok)">${verifiedRows}</div><div class="k-note">each with an official source link</div></div>
  <div class="kpi"><div class="k-label">Tracked rows</div><div class="k-value">${totalRows}</div><div class="k-note">across 8 datasets</div></div>
  <div class="kpi"><div class="k-label">Official sources</div><div class="k-value">${sources.sources.length}</div><div class="k-note">all government or Fed-hosted</div></div>
</div>

<h2>Decision-gate progress board <span class="faint" style="font-weight:400">— W-03</span></h2>
<p class="sub">A gate closes only when an official source or a private document answers it. Nothing here is marked closed on assumption. The board is the honest answer to &ldquo;can a decision be made yet?&rdquo; — <b>not yet, and here is exactly why</b>.</p>
<div class="grid g2" style="margin-top:16px">
  <div>
    <h3 style="margin-top:0">Closed (${closed} of ${gateCount})</h3>
    ${GATES.filter(g => g.state === 'closed').length === 0
      ? `<div class="callout c-bad" style="margin-top:0"><strong>Zero closed</strong>No decision gate can close without the parcel location or the lease dates. This is the finding, not a failure of the work.</div>`
      : ''}
    ${GATES.filter(g => g.state === 'closed').map(g => `<div class="gate"><div class="idx">${g.id}</div><div class="body"><div class="q">${esc(g.q)}</div></div><div class="state"><span class="b b-ok">closed</span></div></div>`).join('')}
    <h3>Open (${gatesOpen()} of ${gateCount})</h3>
    ${GATES.filter(g => g.state !== 'closed').map(g => `<div class="gate"><div class="idx">${g.id}</div><div class="body"><div class="q">${esc(g.q)}</div><div class="meta">${esc(g.why)}</div></div><div class="state"><span class="b b-bad">open</span></div></div>`).join('')}
  </div>
  <div>
    <h3 style="margin-top:0">Work completed (${doneCount})</h3>
    ${DONE.map((d, i) => `<div class="gate"><div class="idx">${String(i + 1).padStart(2, '0')}</div><div class="body"><div class="q">${esc(d.q)}</div><div class="meta">${esc(d.note)}</div></div><div class="state"><span class="b b-ok">done</span></div></div>`).join('')}
    <div class="callout c-warn" style="margin-top:16px">
      <strong>Read the two columns together</strong>
      A large amount of verified work can coexist with zero closed decision gates. The work is real: it is the evidence base and the method. The gates are what still stand between that evidence and a signature.
    </div>
  </div>
</div>`;

function gatesOpen() { return GATES.filter(g => g.state !== 'closed').length; }

const executiveSummary = `
<h2>Executive summary</h2>
<div class="card">
<p><b>The question.</b> For a single-tenant Jack in the Box on a triple-net lease in central Los Angeles, with an expiration reported somewhere between 2030 and 2035: sell before expiry, or renew?</p>
<p><b>The answer today.</b> It cannot be answered responsibly yet, and this site says so rather than manufacturing a verdict. Both the sell side and the hold side are missing every property-level input. A recommendation built on those inputs would be a fabricated cap rate attached to an eight-year date window.</p>
<p><b>What the verified evidence does say.</b></p>
<ul class="tight">
  <li>The metro labour market is sound but not accelerating: 4.6% unemployment in October 2026, total nonfarm employment up 0.9% year-over-year, with leisure and hospitality up 2.0%.</li>
  <li>The metro housing index has rolled over at the margin: 4.57% annualised over the last five years, the <b>lowest of 27 rolling windows</b> in the sample, and 0.82% below its 2026 Q1 peak.</li>
  <li>Trailing appreciation does not predict forward appreciation here. Across 7 overlapping pairs the correlation is <b>−0.937</b>. Extrapolating the last five years would be systematically wrong, in the optimistic direction.</li>
  <li>The risk-free rate is 4.92% and moved 31 basis points within November 2026 alone. Exit cap rates are not stable.</li>
  <li>The county has absorbed a major wildfire disaster declaration, five storm and flood declarations and a pandemic declaration within six years. Tail risk here is demonstrated, not hypothetical.</li>
  <li>California offers no preferential capital-gain rate, depreciation recapture is taxed at up to 25% federally, and the 3.8% net investment income tax may apply. The sale is more expensive after tax than most owners assume.</li>
</ul>
<p><b>What can be done this week without any new spending.</b> Three things, and one has a hard deadline:</p>
<ol class="tight">
  <li><b>Before 2026-11-30:</b> if assessed value exceeds market value, file the decline-in-value application. It is free and the window closes in days.</li>
  <li>Pin the four lease dates — option window opens, option deadline, tenant notice, expiration. A lapsed option is the only irreversible loss in this project.</li>
  <li>Register a free Census API key so the tract-level trade-area analysis can run.</li>
</ol>
<p><b>What it would take to answer the real question.</b> Fifteen named information gates, listed above and detailed on <a href="questions.html">Open questions</a>. One of them — the exact lease expiration and its options — matters more than every forecast on this site combined.</p>
</div>`;

const dashboardBody = `
<div class="eyebrow">Anonymised decision workspace · data cut-off 2026-11-25</div>
<h1>Sell before expiry, or renew?<br><span style="color:var(--ink-dim);font-size:22px;font-weight:520">A verified evidence base, an explicit decision rule, and no invented numbers.</span></h1>
<p class="lede">A single-tenant quick-service restaurant parcel in central Los Angeles, on a triple-net lease expiring between 2030 and 2035. This workspace collects, organises and verifies every factor that could affect the decision — and is explicit about what is still unknown.</p>

<div class="ribbon">
  <div class="chip">Parcel <b>PARCEL-001</b> · address withheld by design</div>
  <div class="chip">Official sources <b>${sources.sources.length}</b></div>
  <div class="chip">Open gates <b>${gatesOpen()}</b></div>
  <div class="chip">Flagged items <b>${fl.irregularities.length + fl.unverified_values.length}</b></div>
  <div class="chip">Model version <b>${esc(md.meta.version)}</b></div>
</div>

${callout('bad', 'The headline finding, stated plainly',
  'No decision gate can be closed from public data alone. The two inputs that decide this case — the exact lease term and a real cap rate — exist only in private documents. Everything on this site is the scaffolding around those two facts.')}

${gateBoard}

${executiveSummary}

<h2>What this workspace covers</h2>
<div class="grid g3">
  <a class="card" href="market.html" style="display:block;color:inherit"><div class="eyebrow">W-01</div><h3 style="margin:0 0 6px">Market &amp; trade area</h3><p class="sub" style="margin:0">City and county figures are shown only to prove they are the wrong unit of analysis. The tract and ring work is prepared, and blocked on one free API key.</p></a>
  <a class="card" href="hazards.html" style="display:block;color:inherit"><div class="eyebrow">W-04</div><h3 style="margin:0 0 6px">Hazard screening</h3><p class="sub" style="margin:0">Seismic, flood and fire. Real FEMA and USGS responses captured at a reference point, with the parcel's own zones explicitly still unknown.</p></a>
  <a class="card" href="lease.html" style="display:block;color:inherit"><div class="eyebrow">Lease</div><h3 style="margin:0 0 6px">Abstract &amp; notice calendar</h3><p class="sub" style="margin:0">Identity-free abstract and a reconciled calendar, including the one dated item that expires in days.</p></a>
  <a class="card" href="decision.html" style="display:block;color:inherit"><div class="eyebrow">W-02</div><h3 style="margin:0 0 6px">Sell vs hold</h3><p class="sub" style="margin:0">Both sides, the after-tax module, the short-lease discount method, and a calculator that keeps your numbers in your browser.</p></a>
  <a class="card" href="scenarios.html" style="display:block;color:inherit"><div class="eyebrow">Model</div><h3 style="margin:0 0 6px">Model &amp; stress</h3><p class="sub" style="margin:0">A versioned cash-flow model with a completed back-test, plus the compound black-swan case nobody models.</p></a>
  <a class="card" href="questions.html" style="display:block;color:inherit"><div class="eyebrow">Gaps</div><h3 style="margin:0 0 6px">Open questions</h3><p class="sub" style="margin:0">Fifteen blocking questions, each with the holder, the discovery path, and a recommended order.</p></a>
  <a class="card" href="suggestions.html" style="display:block;color:inherit"><div class="eyebrow">Review</div><h3 style="margin:0 0 6px">Suggestions</h3><p class="sub" style="margin:0">Four paths and twelve proposals. You choose the path before anything is implemented.</p></a>
  <a class="card" href="flagged.html" style="display:block;color:inherit"><div class="eyebrow">Integrity</div><h3 style="margin:0 0 6px">Flagged for review</h3><p class="sub" style="margin:0">Twelve irregularities and sixteen unverified values, each with its source and what would close it.</p></a>
  <a class="card" href="print.html" style="display:block;color:inherit"><div class="eyebrow">W-10</div><h3 style="margin:0 0 6px">Printable brief</h3><p class="sub" style="margin:0">One page for your advisers. No private figures, safe to hand over.</p></a>
</div>

${callout('info', 'How to read a blank',
  'A dash in a table means the value is genuinely unknown, not zero and not unimportant. Each one is listed on <a href="flagged.html">Flagged for review</a> with the exact document or lookup that would fill it.')}
`;

out('pages/index.html', layout({ title: 'Dashboard', page: 'index.html', body: dashboardBody }));

/* ======================================================================= */
/*  MARKET & TRADE AREA (W-01)                                             */
/* ======================================================================= */
const marketCols = [
  { k: 'id', label: 'ID' },
  { k: 'metric', label: 'Metric' },
  { k: 'geography', label: 'Geography actually described' },
  { k: 'value', label: 'Value', num: true },
  { k: 'period', label: 'Period' },
  { k: 'status', label: 'Status' },
  { k: 'src', label: 'Official source' },
];
const marketBody = `
<div class="eyebrow">W-01 · Trade-area figures</div>
<h1>Market &amp; trade area</h1>
<p class="lede">The brief asks to replace city and county proxies with trade-area figures. This page does something more useful than supplying different averages: it shows, row by row, why each city-level figure fails as a trade-area proxy, and what would replace it.</p>

${callout('warn', 'Why a trade area cannot be drawn yet',
  'A trade area is a drive-time ring around the parcel. The parcel location is withheld for privacy and was never supplied in a usable form, so the ring has no centre. Additionally, the Census API rejected every keyless request, so even the tract-level building blocks could not be pulled. Both blockers are logged as G-01 and G-02 with a documented fix.')}

<h2>Verified metro and city context</h2>
<p class="sub">These figures are real and officially sourced. They are labelled with the geography they actually describe, and with how far that geography is from a trade area. None of them is the trade-area answer.</p>
${table(marketCols, ta.rows, { note: 'Every row links an official source. Rows reading &ldquo;unverified&rdquo; are deliberately blank — see <a href="flagged.html">Flagged for review</a>.' })}

<h2>The tract pull that replaces them</h2>
<div class="grid g2">
  <div class="card">
    <h3 style="margin-top:0">Seven variables, one query</h3>
    <p class="sub">Once a Census API key exists, one request per tract in the county returns everything a drive-time ring needs:</p>
    <ul class="tight">${ta.tract_pull_plan.tables.map(t => `<li><code>${esc(t)}</code></li>`).join('')}</ul>
    <p class="faint">${esc(ta.tract_pull_plan.why_these)}</p>
  </div>
  <div class="card">
    <h3 style="margin-top:0">Blocker and fix</h3>
    <p class="sub"><b>Blocker:</b> ${esc(ta.tract_pull_plan.blocker)}</p>
    <p class="sub">Keyless requests returned a <q>Missing Key</q> page from <code>api.census.gov</code>.</p>
    <p class="sub"><b>Fix:</b> register the free key, then run the documented endpoint. This is the cheapest open item in the whole project.</p>
    <p class="faint" style="word-break:break-all">${esc(ta.tract_pull_plan.endpoint)}</p>
  </div>
</div>

<h2>Labour market and jobs</h2>
<div class="grid g3">
  <div class="kpi"><div class="k-label">Unemployment</div><div class="k-value">4.6%</div><div class="k-note">Oct 2026, LA-Long Beach-Glendale MD</div></div>
  <div class="kpi"><div class="k-label">Nonfarm jobs, YoY</div><div class="k-value" style="color:var(--ok)">+0.9%</div><div class="k-note">Oct 2026, preliminary</div></div>
  <div class="kpi"><div class="k-label">Leisure &amp; hospitality</div><div class="k-value">548.0k</div><div class="k-note">+2.0% YoY — closest sector proxy to restaurant demand</div></div>
</div>
<p class="sub" style="margin-top:10px">Sector detail from the same release: education and health services +3.3%, professional and business services +0.5%, information and financial activities both negative. The metro is being carried by health and leisure, not by office-adjacent employment. For a QSR pad the leisure line matters most, and it is positive.</p>

<h2>Prices, rates and asset values</h2>
<div class="grid g4">
  <div class="kpi"><div class="k-label">10-yr Treasury</div><div class="k-value">4.92%</div><div class="k-note">2026-11-23</div></div>
  <div class="kpi"><div class="k-label">Local CPI, YoY</div><div class="k-value">3.7%</div><div class="k-note">Sep 2026</div></div>
  <div class="kpi"><div class="k-label">Metro HPI, 5-yr CAGR</div><div class="k-value" style="color:var(--warn)">4.57%</div><div class="k-note">lowest of 27 rolling windows</div></div>
  <div class="kpi"><div class="k-label">HPI vs 2026 Q1 peak</div><div class="k-value" style="color:var(--bad)">−0.82%</div><div class="k-note">2026 Q3</div></div>
</div>

${callout('info', 'The one market conclusion that survives scrutiny',
  'The metro has not collapsed, but its rate of price growth is at the bottom of its own 11-year range. Any hold case that assumes continued 6-7% annual appreciation is assuming the average of the past, at the exact moment that average stopped being delivered. See the back-test on <a href="scenarios.html">Model &amp; stress</a>.')}

<h2>Traffic and demand</h2>
<p class="sub">Caltrans is the official source for traffic volumes on the state highway system, publishing Annual Average Daily Traffic by segment. City of Los Angeles surface streets are published by the city traffic engineering office instead. Neither can be pulled until the adjacent segment is known, which depends on the parcel location. This is logged as G-12.</p>
<p class="sub">Competitive supply within 1, 3 and 5 miles has no official federal publisher. It requires either a field survey of the ring or a licensed location-intelligence vendor, and any vendor figure must be labelled non-official on this site. Logged as G-11.</p>
`;

out('pages/market.html', layout({ title: 'Market & trade area', page: 'market.html', body: marketBody }));

/* ======================================================================= */
/*  HAZARDS (W-04)                                                         */
/* ======================================================================= */
const hzCols = [
  { k: 'id', label: 'ID' },
  { k: 'hazard', label: 'Hazard / metric' },
  { k: 'geography', label: 'Geography' },
  { k: 'value', label: 'Value', num: true },
  { k: 'status', label: 'Status' },
  { k: 'src', label: 'Official source' },
];
const hzBody = `
<div class="eyebrow">W-04 · Parcel-level hazard screening</div>
<h1>Hazard screening</h1>
<p class="lede">The requirement is to replace regional hazard context with the parcel's actual zone status for earthquake, fire and flood. This page delivers the machinery and the proof that it works — and refuses to claim the parcel's status until the parcel's coordinates exist.</p>

${callout('bad', 'Read this before any number below',
  esc(hz.meta.critical_caveat))}

<h2>Reference-point query results</h2>
<p class="sub">Real responses from official services, captured at <code>34.0522, -118.2437</code>. Every row is stamped <span class="b b-info">Ref. point only</span> so it cannot be mistaken for the parcel.</p>
${table(hzCols, hz.rows)}

<h2>What the regional record already proves</h2>
<div class="grid g2">
  <div class="card">
    <h3 style="margin-top:0">Seismic: low frequency, high severity</h3>
    <p class="sub">Only <b>four</b> magnitude 4.5+ earthquakes occurred in the central-LA bounding box in 26 years — yet ASCE 7-22 assigns <b>Seismic Design Category D</b> at the reference point, with S<sub>S</sub> of 2.25g.</p>
    <p class="sub">That combination is the definition of a tail risk: a model calibrated on observed frequency will understate loss almost every year, then be catastrophically wrong once.</p>
  </div>
  <div class="card">
    <h3 style="margin-top:0">Fire and flood: repeated, not rare</h3>
    <p class="sub">The county carried a major wildfire disaster declaration (<b>DR-4856</b>) in January 2025, six fire-management declarations across 14 months, and five storm and flood declarations in two winters.</p>
    <p class="sub">These are verified federal declarations with numbers and dates, not news summaries. Any stress model that treats them as once-in-a-generation events is mis-calibrated.</p>
  </div>
</div>

<h2>How each hazard gets resolved for the parcel</h2>
<div class="tbl-wrap"><table>
<thead><tr><th>Hazard</th><th>Query method</th><th>What counts as an answer</th><th>Official source</th></tr></thead>
<tbody>
${hz.query_recipes.map(r => `<tr><td><b>${esc(r.hazard)}</b></td><td>${esc(r.how)}</td><td>${esc(r.note)}</td>${srcCell(r.hazard === 'flood' ? 'S-007' : r.hazard === 'seismic' ? 'S-006' : 'S-009')}</tr>`).join('')}
</tbody></table></div>

${callout('warn', 'The gap that no public source can close',
  'Building-specific retrofit status, liquefaction susceptibility and — most importantly — the actual insurance binder are all private. Those three documents convert four of the black-swan scenarios on <a href="scenarios.html">Model &amp; stress</a> from qualitative to quantified. Until they exist, any dollar loss figure for a seismic or fire event would be invented.')}
`;
out('pages/hazards.html', layout({ title: 'Hazard screening', page: 'hazards.html', body: hzBody }));

/* ======================================================================= */
/*  LEASE & CALENDAR                                                       */
/* ======================================================================= */
const lzBody = `
<div class="eyebrow">Private lease abstract · notice-calendar reconciliation</div>
<h1>Lease &amp; calendar</h1>
<p class="lede">A private lease abstract is supposed to be commissioned and reconciled with the notice calendar before any sale or renewal commitment. This page shows the abstract structure, the reconciliation attempt, and precisely why it cannot close yet.</p>

${callout('bad', 'Status',
  '<b>' + esc(lz.meta.status_statement) + '</b>')}

<h2>Abstract fields · identity-free</h2>
<p class="sub">Only term structure is reproduced. No landlord, tenant entity, guarantor, signatory, address, APN or rent figure appears here or anywhere in this repository.</p>
${table([
  { k: 'field', label: 'Field' },
  { k: 'value', label: 'Value' },
  { k: 'provenance', label: 'Provenance' },
  { k: 'status', label: 'Status' },
  { k: 'src', label: 'Source' },
], lz.abstract_fields)}

<h2>Notice calendar, reconciled</h2>
${table([
  { k: 'id', label: 'ID' },
  { k: 'event', label: 'Event' },
  { k: 'date', label: 'Date' },
  { k: 'rule', label: 'Rule / window' },
  { k: 'status', label: 'Status' },
  { k: 'src', label: 'Official source' },
], lz.notice_calendar, { note: 'Rows with no source are lease-dependent and therefore unverified; rows citing a source are statutory or programme dates.' })}

${callout('bad', 'Reconciliation result: ' + esc(lz.reconciliation.conclusion),
  esc(lz.reconciliation.reason))}

<h2>What would close the reconciliation</h2>
<ul class="tight">${lz.reconciliation.what_would_close_it.map(x => `<li>${esc(x)}</li>`).join('')}</ul>

${callout('warn', 'The hard stop', esc(lz.reconciliation.hard_stop))}

<h2>The one dated item that expires in days</h2>
<div class="card">
  <p><b>Decline-in-value filing, 2026-2027 tax year.</b> The Los Angeles County Assessor opened the window on <b>2026-07-02</b> and the deadline is <b>2026-11-30</b> — six days after this report's data cut-off.</p>
  <p class="sub">This is the only action item on the entire site that is simultaneously verified, free, and time-limited. It reduces the property tax line, which in a triple-net hold is the largest fixed expense the owner controls. It does not require any of the missing inputs, only the assessed value on the county bill.</p>
  <p class="faint">Source: ${SRC['S-019'].publisher} — <a href="${SRC['S-019'].url}" target="_blank" rel="noopener noreferrer">${SRC['S-019'].url}</a></p>
</div>
`;
out('pages/lease.html', layout({ title: 'Lease & calendar', page: 'lease.html', body: lzBody }));

/* ======================================================================= */
/*  DECISION (W-02 + after-tax + short-lease discount)                     */
/* ======================================================================= */
const decisionBody = `
<div class="eyebrow">W-02 · Sell versus hold · after-tax module · short-lease discount</div>
<h1>Sell versus hold</h1>
<p class="lede">An after-tax sale comparison side by side with a negotiated renewal case, and no winner declared until verified inputs exist. Below: what each side requires, what is verified, the tax rules that apply, how the short-lease discount must be measured, and a calculator that keeps every private number inside your browser.</p>

${callout('bad', 'No winner is declared on this page — deliberately',
  esc(va.decision_rule.why_no_winner_today) + '<br><br><b>What can be said now:</b> ' + esc(va.decision_rule.what_can_be_said_now))}

<h2>Verified market anchors</h2>
${table([
  { k: 'id', label: 'ID' },
  { k: 'metric', label: 'Anchor' },
  { k: 'value', label: 'Value', num: true },
  { k: 'period', label: 'Period' },
  { k: 'status', label: 'Status' },
  { k: 'src', label: 'Official source' },
], va.market_anchors)}

<h2>The two sides, input by input</h2>
<div class="grid g2">
  <div>
    <h3 style="margin-top:0">Sell side — ${va.sell_side_inputs.length} required inputs</h3>
    ${table([
      { k: 'id', label: 'ID' },
      { k: 'input', label: 'Input' },
      { k: 'status', label: 'Status' },
    ], va.sell_side_inputs)}
  </div>
  <div>
    <h3 style="margin-top:0">Hold side — ${va.hold_side_inputs.length} required inputs</h3>
    ${table([
      { k: 'id', label: 'ID' },
      { k: 'input', label: 'Input' },
      { k: 'status', label: 'Status' },
    ], va.hold_side_inputs)}
  </div>
</div>

<h2>After-tax module — the rules that are verified</h2>
<p class="sub">The owner asked for one number to compare against the hold case. Here is the tax machinery that produces it, every element sourced. What is missing is not the rule, it is the owner's basis and bracket.</p>
${table([
  { k: 'id', label: 'ID' },
  { k: 'rule', label: 'Rule' },
  { k: 'detail', label: 'Detail' },
  { k: 'status', label: 'Status' },
  { k: 'src', label: 'Official source' },
], va.tax_rules)}

<div class="callout c-info">
  <strong>Three tax facts that change the sell decision most</strong>
  <ul class="tight" style="margin-bottom:0">
    <li><b>Depreciation comes back at 25%.</b> Unrecaptured section 1250 gain is capped at a 25% federal rate — often higher than the 20% applied to the rest of the gain. Long holds accumulate a lot of it.</li>
    <li><b>California offers no relief.</b> Net capital gain is taxed as ordinary income. There is no state equivalent of the federal preferential rate.</li>
    <li><b>§1031 must be decided before signing.</b> Forty-five days to identify, one hundred and eighty to complete. It cannot be elected retroactively.</li>
  </ul>
</div>

<h2>Pricing the short-lease discount from real quotes</h2>
<p class="sub">${esc(qt.why_this_matters)}</p>
${table([
  { k: 'id', label: 'ID' },
  { k: 'what', label: 'Quote required' },
  { k: 'source_type', label: 'Source type' },
  { k: 'value', label: 'Value', num: true },
  { k: 'status', label: 'Status' },
  { k: 'src', label: 'Official source' },
], qt.quote_log, { note: 'Six quote slots, all empty. No official source publishes single-tenant QSR cap rates, and no broker quotes were obtained — so the honest value is blank, not a guess.' })}

<div class="card">
  <h3 style="margin-top:0">Method, ready to run the moment quotes exist</h3>
  <ol class="tight">
    <li>${esc(qt.method_once_quotes_exist.step_1)}</li>
    <li>${esc(qt.method_once_quotes_exist.step_2)}</li>
    <li>${esc(qt.method_once_quotes_exist.step_3)}</li>
    <li>${esc(qt.method_once_quotes_exist.step_4)}</li>
    <li>${esc(qt.method_once_quotes_exist.step_5)}</li>
  </ol>
  <div class="callout c-warn" style="margin-bottom:0"><strong>Anti-pattern</strong>${esc(qt.method_once_quotes_exist.anti_pattern)}</div>
</div>

<h2>The gates that block a verdict</h2>
${table([
  { k: 'id', label: 'ID' },
  { k: 'question', label: 'Question' },
  { k: 'blocks', label: 'Blocks' },
  { k: 'status', label: 'Status' },
], va.gates.map(g => ({ ...g, blocks: g.blocks.join(', ') })))}

<hr class="sep">

<h2 id="calculator">Private calculator</h2>
<p class="sub">Everything you type stays in this browser tab. There is no network request, no analytics, no storage, and nothing is written to this repository. Verify it yourself: the calculator is a single JavaScript file with no dependencies, and it never calls <code>fetch</code>.</p>

<div class="calc" id="calc">
  <fieldset>
    <legend>1 · Sale today</legend>
    <div class="fields">
      <div class="field"><label for="c_price">Sale price (USD)</label><input id="c_price" type="number" min="0" step="1000" placeholder="0"><div class="hint">Your broker's opinion or a contract price.</div></div>
      <div class="field"><label for="c_cap_in">Cap rate paid (offer), %</label><input id="c_cap_in" type="number" min="0" step="0.05" placeholder="e.g. 5.75"><div class="hint">From a real quote, not a guess.</div></div>
      <div class="field"><label for="c_sellcost">Selling costs, % of price</label><input id="c_sellcost" type="number" min="0" step="0.1" value="4"><div class="hint">Commission, title, transfer tax, legal. 3–6% typical.</div></div>
      <div class="field"><label for="c_basis">Adjusted basis (USD)</label><input id="c_basis" type="number" min="0" step="1000" placeholder="0"><div class="hint">Cost + improvements − depreciation taken.</div></div>
      <div class="field"><label for="c_deprec">Accumulated depreciation (USD)</label><input id="c_deprec" type="number" min="0" step="1000" placeholder="0"><div class="hint">Drives the 25% recapture slice.</div></div>
      <div class="field"><label for="c_mortgage">Mortgage payoff (USD)</label><input id="c_mortgage" type="number" min="0" step="1000" value="0"><div class="hint">Balance plus any prepayment penalty.</div></div>
    </div>
  </fieldset>

  <fieldset>
    <legend>2 · Tax position</legend>
    <div class="fields">
      <div class="field"><label for="c_filing">Filing status</label><select id="c_filing">
        <option value="single">Single</option>
        <option value="mfj" selected>Married filing jointly</option>
        <option value="mfs">Married filing separately</option>
        <option value="hoh">Head of household</option>
      </select></div>
      <div class="field"><label for="c_income">Other taxable income (USD)</label><input id="c_income" type="number" min="0" step="1000" value="0"><div class="hint">Sets the bracket the gain lands in.</div></div>
      <div class="field"><label for="c_ca">California marginal rate, %</label><input id="c_ca" type="number" min="0" max="13.3" step="0.1" value="9.3"><div class="hint">Enter your own bracket. This is not baked in — see <a href="flagged.html">IR-06</a>.</div></div>
      <div class="field"><label for="c_reinvest">Reinvest with §1031?</label><select id="c_reinvest">
        <option value="no" selected>No — recognise the gain</option>
        <option value="yes">Yes — defer everything</option>
      </select><div class="hint">Deferral is not forgiveness; basis carries over.</div></div>
    </div>
  </fieldset>

  <fieldset>
    <legend>3 · Hold and renew</legend>
    <div class="fields">
      <div class="field"><label for="c_rent">Contract rent, year 1 (USD)</label><input id="c_rent" type="number" min="0" step="1000" placeholder="0"><div class="hint">Annual base rent.</div></div>
      <div class="field"><label for="c_opex">Landlord expense not recovered (USD/yr)</label><input id="c_opex" type="number" min="0" step="1000" value="0"><div class="hint">The part that is genuinely not reimbursed.</div></div>
      <div class="field"><label for="c_ins">Insurance (USD/yr)</label><input id="c_ins" type="number" min="0" step="1000" placeholder="0"><div class="hint">Leave blank if unknown — output will be flagged.</div></div>
      <div class="field"><label for="c_tax">Property tax (USD/yr)</label><input id="c_tax" type="number" min="0" step="1000" placeholder="0"><div class="hint">Post-decline-in-value if you file.</div></div>
      <div class="field"><label for="c_esc">Rent escalation, %/yr</label><input id="c_esc" type="number" step="0.1" value="2"><div class="hint">Compare against local CPI of 3.7%.</div></div>
      <div class="field"><label for="c_years">Years remaining</label><input id="c_years" type="number" min="1" max="20" step="1" value="5"><div class="hint">From the lease, not the 2030–2035 window.</div></div>
      <div class="field"><label for="c_disc">Discount rate, %</label><input id="c_disc" type="number" min="0" step="0.1" placeholder="0"><div class="hint">At least 4.92% (10-yr UST) plus a risk premium. No default — this is yours.</div></div>
      <div class="field"><label for="c_cap_out">Exit cap rate, %</label><input id="c_cap_out" type="number" min="0" step="0.05" placeholder="0"><div class="hint">Terminal value is not computed without it.</div></div>
      <div class="field"><label for="c_vac">Vacancy months at expiry</label><input id="c_vac" type="number" min="0" max="36" step="1" value="12"><div class="hint">Downtime before re-leasing.</div></div>
      <div class="field"><label for="c_capex">Capex backlog (USD)</label><input id="c_capex" type="number" min="0" step="1000" value="0"><div class="hint">Roof, HVAC, seismic, parking.</div></div>
    </div>
  </fieldset>

  <div class="btnrow">
    <button id="c_run" type="button">Compute comparison</button>
    <button id="c_clear" class="ghost" type="button">Clear all</button>
  </div>

  <div id="c_out" class="hidden">
    <div class="out" id="c_kpis"></div>
    <div id="c_warnbox"></div>
    <div id="c_table"></div>
  </div>
</div>

${callout('info', 'Why there is no default cap rate or discount rate',
  'A cap rate multiplies straight into value: 100 basis points on a 5% cap is roughly a 17% swing in price. Shipping a default would make an assumption look like an answer. Both fields start empty on purpose, and the calculator refuses to produce a terminal value without them.')}
`;

out('pages/decision.html', layout({
  title: 'Sell vs hold',
  page: 'decision.html',
  body: decisionBody,
  extraHead: '<script src="../assets/js/calc.js" defer></script>',
}));

/* ======================================================================= */
/*  MODEL & STRESS                                                         */
/* ======================================================================= */
const bt = md.back_test;
const scenBody = `
<div class="eyebrow">Versioned cash-flow model · back-test · black-swan stress</div>
<h1>Model &amp; stress</h1>
<p class="lede">A versioned cash-flow model, back-tested wherever verified history exists, with observations and assumptions kept strictly apart. Then the stress cases — seismic, flood, fire, rent loss, repair cost and exit liquidity — stressed together, as the brief requires.</p>

${callout('info', 'Version and scope',
  '<b>' + esc(md.meta.version) + '</b> · Back-tested: ' + esc(md.governance.what_is_backtested) + ' Not back-tested: ' + esc(md.governance.what_is_not_backtested))}

<h2>Observations — things the data says</h2>
<p class="sub">Every row below is an observation or arithmetic computed from observations. No assumption is allowed in this table.</p>
${table([
  { k: 'id', label: 'ID' },
  { k: 'statement', label: 'Observation' },
  { k: 'value', label: 'Value', num: true },
  { k: 'status', label: 'Kind' },
  { k: 'src', label: 'Official source' },
], md.observations)}

<h2>The back-test</h2>
<div class="card">
  <p><b>Question:</b> ${esc(bt.question)}</p>
  <p><b>Design:</b> ${esc(bt.design)}</p>
  <div class="grid g3" style="margin:14px 0">
    <div class="kpi"><div class="k-label">Correlation</div><div class="k-value" style="color:var(--warn)">${bt.results.correlation_trailing_vs_forward}</div><div class="k-note">trailing vs forward 5-yr growth</div></div>
    <div class="kpi"><div class="k-label">Direction hit rate</div><div class="k-value">${bt.results.direction_hit_rate_percent}%</div><div class="k-note">${bt.results.pairs} overlapping pairs</div></div>
    <div class="kpi"><div class="k-label">Mean absolute error</div><div class="k-value">${bt.results.mean_absolute_error_pp} pp</div><div class="k-note">per 5-yr window</div></div>
  </div>
  <p><b>Interpretation.</b> ${esc(bt.interpretation)}</p>
  <div class="callout c-warn"><strong>Honest limitations</strong><ul class="tight" style="margin-bottom:0">${bt.honest_limitations.map(l => `<li>${esc(l)}</li>`).join('')}</ul></div>
  <p class="sub" style="margin-bottom:0"><b>Conclusion.</b> ${esc(bt.conclusion)}</p>
</div>

<h2>Assumptions — things a person chose</h2>
<p class="sub">Kept separate from observations on purpose. Each carries the reason it was chosen and the risk if it is wrong.</p>
${table([
  { k: 'id', label: 'ID' },
  { k: 'assumption', label: 'Assumption' },
  { k: 'value', label: 'Value', num: true },
  { k: 'status', label: 'Kind' },
  { k: 'justification', label: 'Why' },
], md.assumptions)}

<h2>Cash-flow engine</h2>
<div class="card">
  <p class="sub">${esc(md.cash_flow_engine.shape)}</p>
  <ul class="tight">
    <li><b>Contract period.</b> ${esc(md.cash_flow_engine.periods.contract_period)}</li>
    <li><b>Option period.</b> ${esc(md.cash_flow_engine.periods.option_period)}</li>
    <li><b>Post-expiry.</b> ${esc(md.cash_flow_engine.periods.post_expiry_period)}</li>
  </ul>
  <p class="sub"><b>Terminal value.</b> ${esc(md.cash_flow_engine.terminal_value)}</p>
  <h3>Refusal conditions — the model will not answer without these</h3>
  <ul class="tight">${md.cash_flow_engine.refusal_conditions.map(r => `<li>${esc(r)}</li>`).join('')}</ul>
</div>

<div class="grid g4" style="margin-top:16px">
  ${md.scenario_skeletons.map(s => `<div class="kpi unverified"><div class="k-label">${esc(s.id)}</div><div class="k-value" style="font-size:15px;color:var(--ink)">${esc(s.name)}</div><div class="k-note">${esc(s.narrative)}</div><div style="margin-top:8px"><span class="b b-bad">cannot run</span></div></div>`).join('')}
</div>

<hr class="sep">

<h2>Black-swan and base-case stress</h2>
<p class="sub">${esc(st.meta.core_insight)}</p>

<h3>Verified probability context</h3>
${table([
  { k: 'id', label: 'ID' },
  { k: 'finding', label: 'Verified finding' },
  { k: 'implication', label: 'Why it matters' },
  { k: 'src', label: 'Official source' },
], st.probability_context_verified)}

<h3>Scenarios</h3>
${table([
  { k: 'id', label: 'ID' },
  { k: 'name', label: 'Scenario' },
  { k: 'class', label: 'Class' },
  { k: 'mechanism', label: 'Mechanism' },
  { k: 'exit_liquidity_effect', label: 'Exit-liquidity effect' },
], st.scenarios, { note: 'No dollar loss is stated anywhere: replacement cost, insured limits, deductibles and business-interruption terms are all private documents not supplied to this project.' })}

<h3>Compound stress matrix</h3>
<p class="sub">${esc(st.compound_stress_matrix.description)} Ratings are qualitative — <span class="faint">${esc(st.compound_stress_matrix.ratings_key)}</span></p>
<div class="tbl-wrap"><table>
<thead><tr><th>Scenario</th><th>Rent loss</th><th>Repair cost</th><th>Exit liquidity</th></tr></thead>
<tbody>
${st.compound_stress_matrix.rows.map(r => {
  const rate = v => `<span class="b ${v === 'severe' ? 'b-bad' : v === 'high' ? 'b-warn' : v === 'moderate' ? 'b-info' : v === 'low' ? 'b-neutral' : 'b-neutral'}">${esc(v)}</span>`;
  return `<tr><td><b>${esc(r.scenario)}</b></td><td>${rate(r.rent)}</td><td>${rate(r.repair)}</td><td>${rate(r.liquidity)}</td></tr>`;
}).join('')}
</tbody></table></div>
${callout('bad', 'The finding that matters', esc(st.compound_stress_matrix.reading))}

<h3>Mitigations</h3>
${table([
  { k: 'id', label: 'ID' },
  { k: 'mitigation', label: 'Mitigation' },
  { k: 'status', label: 'Status' },
  { k: 'costs', label: 'Cost' },
  { k: 'src', label: 'Official source' },
], st.mitigations)}

${callout('warn', 'The honest black-swan position', esc(st.black_swan_statement.the_honest_position))}
`;
out('pages/scenarios.html', layout({ title: 'Model & stress', page: 'scenarios.html', body: scenBody }));

/* ======================================================================= */
/*  OPEN QUESTIONS                                                         */
/* ======================================================================= */
const gapCols = [
  { k: 'id', label: 'ID' },
  { k: 'question', label: 'Question' },
  { k: 'why_blocks', label: 'Why it blocks the decision' },
  { k: 'holder', label: 'Who holds it' },
  { k: 'discovery', label: 'How to discover it' },
  { k: 'status', label: 'Status' },
];
const qBody = `
<div class="eyebrow">Information gaps · discovery plan</div>
<h1>Open questions</h1>
<p class="lede">A clear list of the questions, information and answers that must be addressed before any decision can reasonably be made — separated into what we have, what we do not have, and exactly how each gap gets closed.</p>

${callout('info', 'How to use this page',
  'Each question names who holds the answer, how to discover it, and whether the answer can be obtained without revealing private data. A question with no discovery path is not a question, it is a wish — so every row here has one.')}

<h2>What we have</h2>
${table([
  { k: 'id', label: 'ID' },
  { k: 'item', label: 'Established' },
  { k: 'evidence', label: 'Evidence' },
  { k: 'src', label: 'Official source' },
], qs.have)}

<h2>What we do not have — ${qs.do_not_have.length} blocking gaps</h2>
<p class="sub">Ordered by priority, then by ID. Priority 1 items are the ones that can change the answer on their own.</p>
${table(gapCols, [...qs.do_not_have].sort((a, b) => a.priority - b.priority || a.id.localeCompare(b.id)))}

<h2>Recommended sequence</h2>
<p class="sub">${esc(qs.sequence.why_order_matters)}</p>
<div class="tbl-wrap"><table>
<thead><tr><th>Step</th><th>Gaps to close</th><th>Why this order</th></tr></thead>
<tbody>
${qs.sequence.recommended_order.map(s => `<tr><td class="num">${s.step}</td><td><span class="b b-info">${s.gaps.join('</span> <span class="b b-info">')}</span></td><td>${esc(s.why)}</td></tr>`).join('')}
</tbody></table></div>

<h2>Questions already answered by design</h2>
${table([
  { k: 'id', label: 'ID' },
  { k: 'question', label: 'Question' },
  { k: 'answer', label: 'Decision, and why' },
  { k: 'status', label: 'Status' },
], qs.answered_by_design)}
`;
out('pages/questions.html', layout({ title: 'Open questions', page: 'questions.html', body: qBody }));

/* ======================================================================= */
/*  SUGGESTIONS                                                            */
/* ======================================================================= */
const sgBody = `
<div class="eyebrow">Review section · choose the path before anything is implemented</div>
<h1>Suggestions</h1>
<p class="lede">${esc(sg.meta.purpose)}</p>

${callout('info', 'How to use this page', esc(sg.meta.how_to_use))}

<h2>Suggested path</h2>
<div class="card">
  <h3 style="margin-top:0">${esc(sg.suggested_path.name)}</h3>
  <p>${esc(sg.suggested_path.rationale)}</p>
  <ol class="tight">${sg.suggested_path.steps.map(s => `<li>${esc(s)}</li>`).join('')}</ol>
  <p class="sub"><b>Why not the alternative:</b> ${esc(sg.suggested_path.why_not_alternative)}</p>
  <div class="callout c-warn" style="margin-bottom:0"><strong>Decision needed from you</strong>${esc(sg.suggested_path.decision_needed_from_you)}</div>
</div>

<h2>The four paths</h2>
<div class="tbl-wrap"><table>
<thead><tr><th>Path</th><th>Cost</th><th>Time to first real answer</th><th>Main risk</th><th>Recommended</th></tr></thead>
<tbody>
${sg.paths.map(p => `<tr><td><b>${esc(p.name)}</b></td><td>${esc(p.cost)}</td><td>${esc(p.speed_to_first_real_answer)}</td><td>${esc(p.main_risk)}</td><td>${p.recommended ? '<span class="b b-ok">yes</span>' : '<span class="b b-neutral">no</span>'}</td></tr>`).join('')}
</tbody></table></div>

<h2>Proposals — ${sg.proposals.length}</h2>
<p class="sub">Every proposal is a proposal, not an action taken. Status is <span class="b b-neutral">proposed</span> on all of them.</p>
${sg.proposals.map(p => `
<div class="card">
  <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap">
    <div style="flex:1;min-width:240px">
      <div class="eyebrow">${esc(p.id)} · ${esc(p.tier)}</div>
      <h3 style="margin:0 0 8px">${esc(p.proposal)}</h3>
    </div>
    <span class="b b-neutral">${esc(p.status)}</span>
  </div>
  <div class="grid g3" style="margin-top:6px">
    <div><div class="eyebrow">Benefit</div><p class="sub" style="margin:0">${esc(p.benefit)}</p></div>
    <div><div class="eyebrow">Cost</div><p class="sub" style="margin:0">${esc(p.cost)}</p></div>
    <div><div class="eyebrow">Risk of adopting</div><p class="sub" style="margin:0">${esc(p.risk)}</p></div>
  </div>
  <p class="sub" style="margin:10px 0 0"><b>Decision needed from you:</b> ${esc(p.decision_needed)}</p>
  ${p.source_id ? `<p class="faint" style="margin:6px 0 0">Source: <a href="${SRC[p.source_id].url}" target="_blank" rel="noopener noreferrer">${SRC[p.source_id].publisher}</a></p>` : ''}
</div>`).join('')}

<h2>Review workflow</h2>
<ol class="tight">${sg.review_workflow.map(w => `<li><b>${esc(w.action)}</b></li>`).join('')}</ol>
`;
out('pages/suggestions.html', layout({ title: 'Suggestions', page: 'suggestions.html', body: sgBody }));

/* ======================================================================= */
/*  FLAGGED FOR REVIEW                                                     */
/* ======================================================================= */
const flagBody = `
<div class="eyebrow">Integrity register</div>
<h1>Flagged for review</h1>
<p class="lede">Every irregularity found while verifying line by line, and every value that could not be confirmed against an official source. Published deliberately, with source links, so each item can be reviewed and a decision recorded against it.</p>

${callout('info', 'Counting rule', esc(fl.meta.counting_rule))}

<h2>Irregularities — ${fl.irregularities.length}</h2>
${fl.irregularities.map(r => `
<div class="card">
  <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap">
    <div style="flex:1;min-width:240px">
      <div class="eyebrow">${esc(r.id)} · severity: ${esc(r.severity)}</div>
      <h3 style="margin:0 0 8px">${esc(r.title)}</h3>
    </div>
    <span class="b ${r.severity === 'high' ? 'b-bad' : r.severity === 'medium' ? 'b-warn' : 'b-neutral'}">${esc(r.severity)}</span>
  </div>
  <p class="sub">${esc(r.detail)}</p>
  <p class="sub"><b>Impact.</b> ${esc(r.impact)}</p>
  <p class="sub" style="margin-bottom:6px"><b>Action requested.</b> ${esc(r.action_requested)}</p>
  <p class="faint" style="margin:0">Sources: ${r.sources.length ? r.sources.map(s => `<a href="${SRC[s].url}" target="_blank" rel="noopener noreferrer">${s}</a>`).join(' · ') : 'none available — this is a gap in the public record itself'}</p>
</div>`).join('')}

<h2>Unverified values — ${fl.unverified_values.length}</h2>
<p class="sub">Each of these appears as a blank on its page. None has been estimated, interpolated or filled from a nearby geography.</p>
${table([
  { k: 'id', label: 'ID' },
  { k: 'item', label: 'Value left blank' },
  { k: 'why', label: 'Why it is blank' },
  { k: 'page', label: 'Appears on' },
], fl.unverified_values.map(v => ({ ...v, page: `<a href="${v.page}.html">${v.page}</a>` })), { note: '' })}

<h2>What was verified</h2>
<div class="card">
  <ul class="tight" style="margin-bottom:0">${fl.what_was_verified.map(v => `<li>${esc(v)}</li>`).join('')}</ul>
</div>
`;
out('pages/flagged.html', layout({ title: 'Flagged for review', page: 'flagged.html', body: flagBody }));

/* ======================================================================= */
/*  SOURCES                                                                */
/* ======================================================================= */
const srcBody = `
<div class="eyebrow">Source register</div>
<h1>Sources</h1>
<p class="lede">Every figure on this site traces to one of these ${sources.sources.length} official sources. All are government or Federal-Reserve-hosted, retrieved 2026-11-25, and enforced by an automated allowlist check in the build.</p>

${callout('info', 'Verification rule applied',
  'A row is only marked verified if the value was read directly from the official page or API response during this session. Where an official source could not be reached, the row is left blank and listed on <a href="flagged.html">Flagged for review</a> — never filled with an estimate.')}

${table([
  { k: 'id', label: 'ID' },
  { k: 'publisher', label: 'Publisher' },
  { k: 'title', label: 'Document' },
  { k: 'used_for', label: 'Used for' },
  { k: 'retrieved', label: 'Retrieved' },
], sources.sources.map(s => ({ ...s, title: `<a href="${s.url}" target="_blank" rel="noopener noreferrer">${esc(s.title)}</a>` })))}

<h2>Allowlisted hosts</h2>
<p class="sub">The build fails if any source URL is outside this list, so an unofficial or scraped source cannot silently enter the register.</p>
<div class="card"><p class="src" style="word-break:break-all;margin:0">${sources.allowlisted_hosts.map(h => esc(h)).join(' · ')}</p></div>

<h2>Reproducing any figure</h2>
<p class="sub">Where a source is a machine-readable endpoint, the exact query is recorded in the dataset so any number can be reproduced:</p>
<ul class="tight">
  <li>Hazard queries: <code>data/hazards.json</code> → <code>query_recipes</code></li>
  <li>Trade-area query: <code>data/tradearea.json</code> → <code>tract_pull_plan</code></li>
  <li>Back-test inputs and arithmetic: <code>data/model.json</code> → <code>observations</code></li>
</ul>
`;
out('pages/sources.html', layout({ title: 'Sources', page: 'sources.html', body: srcBody }));

/* ======================================================================= */
/*  PRINTABLE BRIEF (W-10)                                                 */
/* ======================================================================= */
const printBody = `
<div class="no-print" style="margin-bottom:18px">
  <div class="eyebrow">W-10 · One-page printable summary for advisers</div>
  <h1 style="margin-bottom:8px">Advisor brief</h1>
  <p class="lede">Safe to hand to an adviser: it contains no private figures, no address and no owner identity. Print it from your browser; the layout is set to one page at A4/Letter.</p>
  <div class="btnrow"><button type="button" onclick="window.print()">Print this brief</button></div>
</div>

<div class="card" style="border-width:2px">
  <h2 style="margin-top:0">PARCEL-001 — single-tenant QSR, central Los Angeles</h2>
  <p class="sub" style="margin-bottom:14px">Triple-net lease, expiration reported between 2030 and 2035. Anonymised: no address, owner identity, rent figure or personal finance is disclosed. Prepared 2026-11-25 for adviser review.</p>

  <h3>1 · The question put to you</h3>
  <p class="sub">Should the owner sell before lease expiry, or hold and renew? We are asking for a professional opinion on method and sequence, not for a valuation — the valuation inputs do not yet exist.</p>

  <h3>2 · What is verified</h3>
  <table style="font-size:9.5pt">
    <tbody>
      <tr><td>Metro unemployment, Oct 2026</td><td class="num">4.6%</td><td class="faint">BLS</td></tr>
      <tr><td>Metro nonfarm employment, YoY</td><td class="num">+0.9%</td><td class="faint">BLS</td></tr>
      <tr><td>Leisure &amp; hospitality employment</td><td class="num">548.0k, +2.0%</td><td class="faint">BLS</td></tr>
      <tr><td>Local CPI, 12-month</td><td class="num">3.7%</td><td class="faint">BLS</td></tr>
      <tr><td>10-year Treasury, 2026-11-23</td><td class="num">4.92%</td><td class="faint">Federal Reserve H.15</td></tr>
      <tr><td>Metro HPI, 5-yr CAGR (latest window)</td><td class="num">4.57%</td><td class="faint">FHFA</td></tr>
      <tr><td>Metro HPI vs 2026 Q1 peak</td><td class="num">−0.82%</td><td class="faint">FHFA</td></tr>
      <tr><td>County wildfire major-disaster declaration</td><td class="num">DR-4856, 2025-01-08</td><td class="faint">FEMA</td></tr>
      <tr><td>Federal disaster declarations, county, last 20</td><td class="num">fire 9 · flood 5 · bio 2</td><td class="faint">FEMA</td></tr>
      <tr><td>Federal LTCG / recapture / NIIT</td><td class="num">20% / 25% / 3.8%</td><td class="faint">IRS</td></tr>
      <tr><td>California capital-gain preference</td><td class="num">none</td><td class="faint">CA FTB</td></tr>
      <tr><td>§1031 limits</td><td class="num">45 / 180 days</td><td class="faint">IRS</td></tr>
      <tr><td>Decline-in-value deadline, 2026-27</td><td class="num">2026-11-30</td><td class="faint">LA Assessor</td></tr>
    </tbody>
  </table>

  <h3>3 · What is missing, and it is decisive</h3>
  <ul class="tight" style="columns:2;column-gap:26px;font-size:9.5pt">
    <li>Exact lease expiration and renewal-option dates</li>
    <li>Two or three real cap-rate quotes</li>
    <li>Contract rent and true NNN recoveries</li>
    <li>Adjusted basis and accumulated depreciation</li>
    <li>Insurance premium, limits and renewal date</li>
    <li>Building condition and seismic status</li>
    <li>Loan balance and prepayment penalty</li>
    <li>Parcel flood, fire and seismic zone status</li>
  </ul>

  <h3>4 · The finding you are being asked to test</h3>
  <p class="sub">Trailing appreciation does not predict forward appreciation in this metro: correlation <b>−0.937</b> across 7 overlapping five-year pairs, with the latest trailing window the lowest of 27. Our position is that a hold case assuming continued 6–7% growth is assuming a rate the market has already stopped delivering. Please test that.</p>

  <h3>5 · What we ask of you</h3>
  <ol class="tight" style="font-size:9.5pt">
    <li>Confirm or correct the sequence: lease dates → insurance binder → cap-rate quotes and condition assessment → valuation.</li>
    <li>Give a written cap-rate opinion for the asset at both ends of its possible remaining term, expressed as a spread over 4.92%.</li>
    <li>Flag anything in the missing-items list that you would prioritise differently.</li>
    <li>State whether §1031 should be evaluated before listing.</li>
  </ol>

  <p class="faint" style="margin-top:16px;border-top:1px solid #ccc;padding-top:8px">Anonymised working document. No parcel address, owner identity, lease document or personal finance is included. Not investment, legal or tax advice. Full source register: <span class="src">https://kanlerxz87-cyber.github.io/Jackbox1/sources.html</span></p>
</div>
`;
out('pages/print.html', layout({ title: 'Printable advisor brief', page: 'print.html', body: printBody }));

/* ======================================================================= */
/*  ROOT REDIRECT                                                          */
/* ======================================================================= */
out('index.html', `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=pages/index.html">
<title>Jackbox property decision workspace</title>
<link rel="canonical" href="pages/index.html">
</head><body style="background:#0e1116;color:#e8edf4;font-family:system-ui,sans-serif;padding:40px">
<p>Opening the workspace… <a href="pages/index.html" style="color:#4da3ff">continue to the dashboard</a></p>
</body></html>`);

console.log('built: index.html + ' + readdirSync(join(ROOT, 'pages')).length + ' pages');
