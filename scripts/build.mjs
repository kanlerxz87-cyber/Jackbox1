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
  return `<td class="src"><a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${esc(id)}</a> <span class="faint">(${esc(s.retrieved)})</span><br><span class="faint">${esc(s.publisher)}</span></td>`;
}

const NAV = [
  ['index.html', 'Dashboard'],
  ['market.html', 'Market &amp; trade area'],
  ['hazards.html', 'Hazard screening'],
  ['tenant.html', 'Tenant (SEC)'],
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
    <p class="faint">Data cut-off 2026-11-26 · Build ${new Date().toISOString().slice(0, 10)} · Not investment, legal or tax advice. Engage a licensed appraiser, attorney and CPA before acting.</p>
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
const ta = D('tradearea'), hz = D('hazards'), tn = D('tenant'), lz = D('lease'), va = D('valuation'),
  qt = D('quotes'), md = D('model'), st = D('stress'), qs = D('questions'),
  sg = D('suggestions'), fl = D('flagged');

const countBy = (arr, f) => arr.reduce((m, x) => (m[f(x)] = (m[f(x)] || 0) + 1, m), {});
const ALL = [{ d: ta, k: ['rows'] }, { d: hz, k: ['rows'] }, { d: tn, k: ['series'] },
  { d: lz, k: ['abstract_fields', 'notice_calendar'] },
  { d: va, k: ['market_anchors', 'sell_side_inputs', 'hold_side_inputs', 'tax_rules', 'decision_options_risk_matrix'] },
  { d: qt, k: ['quote_log', 'what_the_public_record_does_show'] },
  { d: md, k: ['observations', 'assumptions'] },
  { d: st, k: ['probability_context_verified', 'scenarios', 'mitigations'] },
  { d: qs, k: ['have', 'do_not_have', 'answered_by_design'] },
  { d: sg, k: ['proposals'] },
  { d: fl, k: ['irregularities', 'unverified_values'] }];
const totalRows = ALL.reduce((n, x) => n + x.k.reduce((m, k) => m + (Array.isArray(x.d[k]) ? x.d[k].length : 0), 0), 0);
const datasetCount = ALL.length;
/* Same definition the validator enforces: an observation or a verified row,
   which must carry a resolving source_id. Assumptions are deliberately excluded. */
const VERIFIED_LIKE = new Set(['verified', 'verified-context', 'verified-programme', 'verified-rule',
  'verified-reference-only', 'observation', 'computed-from-observation']);
const allRowsFlat = ALL.reduce((a, x) => a.concat(...x.k.map(k => Array.isArray(x.d[k]) ? x.d[k] : [])), []);
const verifiedRows = allRowsFlat.filter(r => VERIFIED_LIKE.has(r.status)).length;
const assumptionRows = allRowsFlat.filter(r => (r.status || '').startsWith('assumption')).length;
const unverifiedRows = allRowsFlat.filter(r => r.status === 'unverified').length;

/* ======================================================================= */
/*  DASHBOARD (W-03 decision-gate progress board + executive summary)      */
/* ======================================================================= */
const GATES = qs.do_not_have.map(g => ({
  id: g.id,
  q: g.question,
  state: g.status === 'closed' ? 'closed' : 'blocked',
  why: g.why_blocks,
  holder: g.holder,
}));
const DONE = [
  { id: 'D-01', q: 'Official source register built and every row linked', note: `${sources.sources.length} official sources, all on an allowlisted government or Fed host with retrieval dates.` },
  { id: 'D-02', q: 'Metro market, schools, DOF/SCAG projections & labour evidence verified', note: 'BLS Oct 2026, FHFA Q3 2026, Fed H.15 2026-11-24, Census V2025, CA DOF E-1, SCAG 2024, CDE SY 2025-26.' },
  { id: 'D-03', q: 'Tenant SEC EDGAR series built (FY2023–Q3 FY2026)', note: 'Same-store sales, unit closures, franchise rental revenues & Series 2026-1 7.624% debt verified.' },
  { id: 'D-04', q: 'Hazard query method & UCERF3/FAIR Plan context verified', note: 'FEMA, USGS ASCE 7-22, USGS UCERF3, CAL FIRE & CDI Q1 2026 FAIR Plan records.' },
  { id: 'D-05', q: '2026 Federal LTCG & 2026 California PIT tax schedules verified', note: 'IRS Rev. Proc. 2025-32, Topic 409/559, §1031, BOE Pub 29 Prop 13, FTB Oct 2026 Schedules X/Y/Z + 1% MHSA.' },
  { id: 'D-06', q: 'Macro HPI model back-tested & browser-only calculator built', note: 'Mean reversion r = −0.937 over 7 overlapping pairs; parcel model remains v0.1-unbacktested-core.' },
  { id: 'D-07', q: 'Decision-by-decision risk & wealth-preservation matrix published', note: 'Compares all 5 paths without selecting a winner while property-level gates remain open.' },
];
const doneCount = DONE.length, gateCount = GATES.length, closed = GATES.filter(g => g.state === 'closed').length;

const gateBoard = `
<div class="grid g4">
  <div class="kpi"><div class="k-label">Gates closed</div><div class="k-value" style="color:var(--bad)">${closed} / ${gateCount}</div><div class="k-note">Decision inputs still open</div></div>
  <div class="kpi"><div class="k-label">Verified data rows</div><div class="k-value" style="color:var(--ok)">${verifiedRows}</div><div class="k-note">+ ${assumptionRows} labelled assumptions</div></div>
  <div class="kpi"><div class="k-label">Tracked rows</div><div class="k-value">${totalRows}</div><div class="k-note">across ${datasetCount} datasets</div></div>
  <div class="kpi"><div class="k-label">Official sources</div><div class="k-value">${sources.sources.length}</div><div class="k-note">all government or Fed-hosted</div></div>
</div>

<h2>Decision-gate progress board <span class="faint" style="font-weight:400">— W-03</span></h2>
<p class="sub">A gate closes only when an official source or a private document answers it. Nothing here is marked closed on assumption. The board is the honest answer to &ldquo;can a decision be made yet?&rdquo; — <b>not yet, and here is exactly why</b>.</p>
<div class="grid g2" style="margin-top:16px">
  <div>
    <h3 style="margin-top:0">Closed (${closed} of ${gateCount})</h3>
    ${GATES.filter(g => g.state === 'closed').length === 0
      ? `<div class="callout c-bad" style="margin-top:0"><strong>Zero closed</strong>No decision gate can close without the parcel location or the lease dates. This is the finding, not a failure of the work.</div>`
      : `<div class="callout c-info" style="margin-top:0"><strong>${closed} statutory gate closed; ${gatesOpen()} parcel/private gates remain open</strong>Verification of 2026 California PIT brackets closed G-15, while every parcel-level, lease-date, quote and binder gate stays open until private documents arrive.</div>`}
    ${GATES.filter(g => g.state === 'closed').map(g => `<div class="gate"><div class="idx">${g.id}</div><div class="body"><div class="q">${esc(g.q)}</div><div class="meta">${esc(g.why)}</div></div><div class="state"><span class="b b-ok">closed</span></div></div>`).join('')}
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
  <li>The risk-free rate is 4.91% (2026-11-24; 4.92% on 2026-11-23) and moved 31 basis points within November 2026 alone (4.84%–5.15%). Exit cap rates are not stable.</li>
  <li>The tenant franchisor (Jack in the Box Inc.) posted negative same-store sales in FY25 (−4.2%) and Q1–Q3 FY26 (−6.7%, −3.8%, −1.1%), pruned system units from 2,191 (FY24) to 2,115 (Q3 FY26, guiding ~2,100), saw 9M FY26 franchise rental revenue drop −6.8% YoY, and issued $500M of 7.624% 2026-1 Notes. See <a href="tenant.html">Tenant (SEC)</a>.</li>
  <li>The county has absorbed a major wildfire disaster declaration, six fire-management declarations and five storm/flood declarations, while USGS UCERF3 puts 30-year Los Angeles earthquake probability at 60% (M6.7), 46% (M7.0) and 31% (M7.5). Tail risk here is demonstrated, not hypothetical.</li>
  <li>California offers no preferential capital-gain rate (2026 FTB Schedules X/Y/Z run 1%–12.30% plus 1% MHSA over $1M), depreciation recapture is taxed at up to 25% federally, and the 3.8% net investment income tax may apply. The taxable sale is more expensive after tax than most owners assume.</li>
</ul>
<p><b>What can be done this week without any new spending.</b> Three things, and one has a hard deadline:</p>
<ol class="tight">
  <li><b>Before 2026-11-30 (four days from 2026-11-26):</b> if assessed value exceeds market value, file the decline-in-value application. It is free and the window closes in days.</li>
  <li>Pin the four lease dates — option window opens, option deadline, tenant notice, expiration. A lapsed option is the only irreversible loss in this project.</li>
  <li>Register a free Census API key so the tract-level trade-area analysis can run.</li>
</ol>
<p><b>What it would take to answer the real question.</b> Sixteen open information gates (with G-15 now closed), listed above and detailed on <a href="questions.html">Open questions</a>. One of them — the exact lease expiration and its options — matters more than every forecast on this site combined.</p>
</div>`;

const dashboardBody = `
<div class="eyebrow">Anonymised decision workspace · data cut-off 2026-11-26</div>
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
  <a class="card" href="market.html" style="display:block;color:inherit"><div class="eyebrow">W-01</div><h3 style="margin:0 0 6px">Market &amp; trade area</h3><p class="sub" style="margin:0">City, county, DOF E-1, SCAG 2024, CDE LAUSD schools &amp; ZIMAS planning. Tract pull &amp; trend method ready for one Census key.</p></a>
  <a class="card" href="hazards.html" style="display:block;color:inherit"><div class="eyebrow">W-04</div><h3 style="margin:0 0 6px">Hazard screening</h3><p class="sub" style="margin:0">Seismic (ASCE 7-22 &amp; UCERF3), flood, fire &amp; CDI FAIR Plan market stress. Parcel zones explicitly held open pending G-01.</p></a>
  <a class="card" href="tenant.html" style="display:block;color:inherit"><div class="eyebrow">Tenant · SEC</div><h3 style="margin:0 0 6px">Franchisor operating series</h3><p class="sub" style="margin:0">FY2023–Q3 FY2026 same-store sales, unit closures, franchise rental revenues &amp; $1.49B debt stack from SEC EDGAR.</p></a>
  <a class="card" href="lease.html" style="display:block;color:inherit"><div class="eyebrow">Lease</div><h3 style="margin:0 0 6px">Abstract &amp; notice calendar</h3><p class="sub" style="margin:0">Identity-free abstract, Prop 13 rules &amp; reconciled calendar, including the 2026-11-30 decline-in-value deadline.</p></a>
  <a class="card" href="decision.html" style="display:block;color:inherit"><div class="eyebrow">W-02</div><h3 style="margin:0 0 6px">Sell vs hold</h3><p class="sub" style="margin:0">All 5 options risk/wealth-preservation matrix, 2026 IRS &amp; FTB tax schedules, short-lease discount method &amp; browser calculator.</p></a>
  <a class="card" href="scenarios.html" style="display:block;color:inherit"><div class="eyebrow">Model</div><h3 style="margin:0 0 6px">Model &amp; stress</h3><p class="sub" style="margin:0">Versioned cash-flow model, HPI back-test boundary disclosure &amp; compound black-swan matrix.</p></a>
  <a class="card" href="questions.html" style="display:block;color:inherit"><div class="eyebrow">Gaps</div><h3 style="margin:0 0 6px">Open questions</h3><p class="sub" style="margin:0">${gatesOpen()} open blocking questions (1 closed), each with the holder, discovery path &amp; recommended order.</p></a>
  <a class="card" href="suggestions.html" style="display:block;color:inherit"><div class="eyebrow">Review</div><h3 style="margin:0 0 6px">Suggestions</h3><p class="sub" style="margin:0">Four paths and twelve proposals. You choose the path before anything is implemented.</p></a>
  <a class="card" href="flagged.html" style="display:block;color:inherit"><div class="eyebrow">Integrity</div><h3 style="margin:0 0 6px">Flagged for review</h3><p class="sub" style="margin:0">${fl.irregularities.length} irregularities and ${fl.unverified_values.length} unverified values, each with its source and what would close it.</p></a>
  <a class="card" href="print.html" style="display:block;color:inherit"><div class="eyebrow">W-10</div><h3 style="margin:0 0 6px">Printable brief</h3><p class="sub" style="margin:0">One page for your advisers. No private figures, safe to hand over.</p></a>
</div>

<h2>Parallel verification trees in this repository</h2>
<p class="sub">This repository preserves independent verification builds from prior branches for full audit traceability:</p>
<div class="tbl-wrap"><table>
<thead><tr><th>Tree</th><th>Focus</th><th>Entry point</th></tr></thead>
<tbody>
  <tr><td><b>Primary workspace</b></td><td>Complete anonymised decision workspace (W-01..W-10, 2026 tax &amp; SEC Q3'26 updates)</td><td><a href="index.html">pages/index.html</a></td></tr>
  <tr><td><b>Line-by-line audit register</b></td><td>432-row audit &amp; review findings (F-01..F-20)</td><td><a href="../audit/index.html">audit/index.html</a></td></tr>
  <tr><td><b>Cross-checked data ledger</b></td><td>281-row source-locked analytical site &amp; 384-link check</td><td><a href="../web/index.html">web/index.html</a></td></tr>
  <tr><td><b>Private desk &amp; docs</b></td><td>Preserved branch deliverables &amp; verification notes</td><td><a href="../docs/index.html">docs/index.html</a> · <a href="../workspace/index.html">workspace/index.html</a> · <a href="../desk/index.html">desk/index.html</a></td></tr>
  <tr><td><b>Additional archived trees</b></td><td>Independent PR verification snapshots</td><td><a href="../ledger-1ebd66da/index.html">ledger-1ebd66da/index.html</a> · <a href="../audit-78005353/site/index.html">audit-78005353/site/index.html</a></td></tr>
</tbody></table></div>

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
    <p class="sub" style="margin-bottom:0"><b>Tract-level trend method:</b> ${esc(ta.tract_pull_plan.tract_trend_methodology)}</p>
  </div>
  <div class="card">
    <h3 style="margin-top:0">Blocker and fix</h3>
    <p class="sub"><b>Blocker:</b> ${esc(ta.tract_pull_plan.blocker)}</p>
    <p class="sub">Keyless requests returned a <q>Missing Key</q> page from <code>api.census.gov</code>.</p>
    <p class="sub"><b>Fix:</b> register the free key, then run the documented endpoint. This is the cheapest open item in the whole project.</p>
    <p class="faint" style="word-break:break-all">${esc(ta.tract_pull_plan.endpoint)}</p>
  </div>
</div>

<h2>County, school systems, projections &amp; planning</h2>
<div class="grid g3">
  <div class="kpi"><div class="k-label">LA County (Census V2025)</div><div class="k-value">9,694,934</div><div class="k-note">−3.2% vs Apr 2020; DOF E-1 −64,000 in 2025</div></div>
  <div class="kpi"><div class="k-label">SCAG 2050 LA jobs</div><div class="k-value">5,461k</div><div class="k-note">+8.5% over 31 yrs (vs 5,031k in 2019)</div></div>
  <div class="kpi"><div class="k-label">LAUSD enrollment (2025–26)</div><div class="k-value">497,105</div><div class="k-note">16.4% English Learners; CA total 5,731,260</div></div>
</div>
<p class="sub" style="margin-top:10px"><b>Planning &amp; zoning (ZIMAS):</b> Once G-01 closes, run the parcel's APN on LA City Planning's ZIMAS (<a href="${SRC['S-028'].url}" target="_blank" rel="noopener noreferrer">CP-7826 guidelines</a>) to confirm Community Plan designation, commercial zone, and Transit Oriented Communities (TOC) tier — the key test for whether post-2030 redevelopment value exceeds a QSR pad hold.</p>

<h2>Labour market and jobs</h2>
<div class="grid g3">
  <div class="kpi"><div class="k-label">Unemployment</div><div class="k-value">4.6%</div><div class="k-note">Oct 2026, LA-Long Beach-Glendale MD</div></div>
  <div class="kpi"><div class="k-label">Nonfarm jobs, YoY</div><div class="k-value" style="color:var(--ok)">+0.9%</div><div class="k-note">Oct 2026, preliminary</div></div>
  <div class="kpi"><div class="k-label">Leisure &amp; hospitality</div><div class="k-value">548.0k</div><div class="k-note">+2.0% YoY — closest sector proxy to restaurant demand</div></div>
</div>
<p class="sub" style="margin-top:10px">Sector detail from the same release: education and health services +3.3%, professional and business services +0.5%, information and financial activities both negative. The metro is being carried by health and leisure, not by office-adjacent employment. For a QSR pad the leisure line matters most, and it is positive.</p>

<h2>Prices, rates and asset values</h2>
<div class="grid g4">
  <div class="kpi"><div class="k-label">10-yr Treasury</div><div class="k-value">4.91%</div><div class="k-note">2026-11-24 (4.92% on 2026-11-23)</div></div>
  <div class="kpi"><div class="k-label">Local CPI, YoY</div><div class="k-value">3.7%</div><div class="k-note">Sep 2026</div></div>
  <div class="kpi"><div class="k-label">Metro HPI, 5-yr CAGR</div><div class="k-value" style="color:var(--warn)">4.57%</div><div class="k-note">lowest of 27 rolling windows</div></div>
  <div class="kpi"><div class="k-label">HPI vs 2026 Q1 peak</div><div class="k-value" style="color:var(--bad)">−0.82%</div><div class="k-note">2026 Q3</div></div>
</div>

${callout('info', 'The one market conclusion that survives scrutiny',
  'The metro has not collapsed, but its rate of price growth is at the bottom of its own 11-year range. Any hold case that assumes continued 6-7% annual appreciation is assuming the average of the past, at the exact moment that average stopped being delivered. See the back-test on <a href="scenarios.html">Model &amp; stress</a>.')}

<h2>Traffic and demand</h2>
<p class="sub">Caltrans is the official source for traffic volumes on the state highway system, publishing Annual Average Daily Traffic (<a href="${SRC['S-010'].url}" target="_blank" rel="noopener noreferrer">2021–2024 AADT workbooks</a>) by segment. City of Los Angeles surface streets are published by the city traffic engineering office (LADOT) instead. Neither can be pulled until the adjacent segment is known, which depends on the parcel location. This is logged as G-12.</p>
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
    <p class="sub">Only <b>four</b> magnitude 4.5+ earthquakes occurred in the central-LA bounding box in 26 years — yet ASCE 7-22 assigns <b>Seismic Design Category D</b> at the reference point (S<sub>S</sub> 2.25g), and <a href="${SRC['S-029'].url}" target="_blank" rel="noopener noreferrer">USGS UCERF3</a> estimates 30-year Los Angeles probabilities at <b>60% (M6.7)</b>, <b>46% (M7.0)</b> and <b>31% (M7.5)</b>.</p>
    <p class="sub">That combination is the definition of a tail risk: a model calibrated on observed frequency will understate loss almost every year, then be catastrophically wrong once.</p>
  </div>
  <div class="card">
    <h3 style="margin-top:0">Fire, flood &amp; California insurance repricing</h3>
    <p class="sub">The county carried a major wildfire disaster declaration (<b>DR-4856</b>) in January 2025, six fire-management declarations across 14 months, and five storm and flood declarations in two winters. Meanwhile <a href="${SRC['S-030'].url}" target="_blank" rel="noopener noreferrer">CDI Q1 2026 data</a> shows commercial FAIR Plan policies elevated at <b>21,464</b> (up from 21,200).</p>
    <p class="sub">These are verified federal and state records with numbers and dates. Any stress model that ignores insurance repricing or treats disasters as once-in-a-generation events is mis-calibrated.</p>
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
/*  TENANT & FRANCHISOR SERIES (SEC EDGAR)                                 */
/* ======================================================================= */
const tnBody = `
<div class="eyebrow">Tenant &amp; franchisor credit · SEC EDGAR FY2023–Q3 FY2026</div>
<h1>Tenant &amp; lease risk (SEC)</h1>
<p class="lede">${esc(tn.meta.caveat)}</p>

<div class="grid g4">
  <div class="kpi"><div class="k-label">Q3 FY26 system SSS</div><div class="k-value" style="color:var(--warn)">−1.1%</div><div class="k-note">Improved from −6.7% (Q1'26) &amp; −7.4% (Q4'25)</div></div>
  <div class="kpi"><div class="k-label">System units (Jul 2026)</div><div class="k-value">2,115</div><div class="k-note">Down from 2,191 (FY24); FY26 guide ~2,100</div></div>
  <div class="kpi"><div class="k-label">9M FY26 franchise rent rev.</div><div class="k-value">$242.5M</div><div class="k-note">−6.8% YoY vs $260.3M (9M FY25)</div></div>
  <div class="kpi"><div class="k-label">Total debt (Jul 2026)</div><div class="k-value">$1.49B</div><div class="k-note">Incl. $500M Series 2026-1 7.624% Notes</div></div>
</div>

${callout('warn', 'What this multi-period series shows — and what it cannot show',
  'A multi-year series shows direction rather than one quarter: Jack in the Box system same-store sales moved from −1.3% (FY24) to −4.2% (FY25) and improved sequentially across FY26 (−6.7% Q1 → −3.8% Q2 → −1.1% Q3), while store closures reduced the system from 2,191 to 2,115 units and franchise rental revenues fell 4.2% in FY25 and 6.8% in 9M FY26. Meanwhile, corporate refinancing moved to 7.624% on the $500M Series 2026-1 notes and Del Taco closed its sale on 2025-12-22. <b>None of this discloses PARCEL-001 store sales or the franchisee\'s balance sheet</b> (see <a href="questions.html">G-05 &amp; G-13</a>).')}

<h2>Verified SEC series (FY2023 – Q3 FY2026)</h2>
${table([
  { k: 'id', label: 'ID' },
  { k: 'period', label: 'Period' },
  { k: 'metric', label: 'Metric' },
  { k: 'value', label: 'Value', num: true },
  { k: 'status', label: 'Status' },
  { k: 'src', label: 'Official source' },
], tn.series, { note: 'No Q4 or full-year FY2026 Form 10-K/release was filed on SEC EDGAR as of 2026-11-26 (logged as <a href="flagged.html">IR-14</a>).' })}
`;
out('pages/tenant.html', layout({ title: 'Tenant (SEC)', page: 'tenant.html', body: tnBody }));

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
  <p><b>Decline-in-value filing, 2026-2027 tax year.</b> The Los Angeles County Assessor opened the window on <b>2026-07-02</b> and the deadline is <b>2026-11-30</b> — four days after this report's 2026-11-26 data cut-off.</p>
  <p class="sub">This is the only action item on the entire site that is simultaneously verified, free, and time-limited. It reduces the property tax line, which in a triple-net hold is the largest fixed expense the owner controls. It does not require any of the missing inputs, only the assessed value on the county bill. Under <a href="${SRC['S-031'].url}" target="_blank" rel="noopener noreferrer">BOE Pub 29 (Prop 13)</a>, a long-held parcel also enjoys a 2% annual assessment cap that resets to market value on change of ownership.</p>
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

<h2>All decision options: risk, wealth preservation &amp; growth</h2>
<p class="sub">No single option wins without private lease dates, basis and broker quotes. Below is the risk-return trade-off across every possible decision on PARCEL-001, balancing wealth preservation against growth.</p>
${table([
  { k: 'id', label: 'ID' },
  { k: 'option', label: 'Decision option' },
  { k: 'wealth_preservation', label: 'Wealth preservation' },
  { k: 'growth_opportunity', label: 'Growth opportunity' },
  { k: 'key_risks', label: 'BAU &amp; black-swan risks' },
  { k: 'risk_level', label: 'Risk posture' },
  { k: 'src', label: 'Official source' },
], va.decision_options_risk_matrix)}

<h2>The two sides, input by input</h2>
<div class="grid g2">
  <div>
    <h3 style="margin-top:0">Sell side — ${va.sell_side_inputs.length} required inputs</h3>
    ${table([
      { k: 'id', label: 'ID' },
      { k: 'input', label: 'Input' },
      { k: 'status', label: 'Status' },
      { k: 'why', label: 'Why / source status' },
    ], va.sell_side_inputs)}
  </div>
  <div>
    <h3 style="margin-top:0">Hold side — ${va.hold_side_inputs.length} required inputs</h3>
    ${table([
      { k: 'id', label: 'ID' },
      { k: 'input', label: 'Input' },
      { k: 'status', label: 'Status' },
      { k: 'why', label: 'Why / source status' },
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
  { k: 'src', label: 'Reference' },
], va.gates.map(g => ({ ...g, blocks: g.blocks.join(', '), source_id: g.id === 'G-06' ? 'S-004' : g.id === 'G-07' ? 'S-016' : g.id === 'G-08' ? 'S-030' : null })))}

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
      <div class="field"><label for="c_taxyear">Federal LTCG brackets</label><select id="c_taxyear">
        <option value="2026" selected>2026 (IRS Rev. Proc. 2025-32)</option>
        <option value="2025">2025 (IRS Topic 409)</option>
      </select><div class="hint">2026 verified from S-032.</div></div>
      <div class="field"><label for="c_filing">Filing status</label><select id="c_filing">
        <option value="single">Single</option>
        <option value="mfj" selected>Married filing jointly</option>
        <option value="mfs">Married filing separately</option>
        <option value="hoh">Head of household</option>
      </select></div>
      <div class="field"><label for="c_income">Other taxable income (USD)</label><input id="c_income" type="number" min="0" step="1000" value="0"><div class="hint">Sets the bracket the gain lands in.</div></div>
      <div class="field"><label for="c_camode">California PIT method</label><select id="c_camode">
        <option value="brackets_2026" selected>2026 FTB Schedules X/Y/Z + 1% MHSA &gt;$1M</option>
        <option value="custom">Custom flat marginal rate below</option>
      </select><div class="hint">2026 brackets verified from S-033 &amp; S-034.</div></div>
      <div class="field"><label for="c_ca">Custom CA marginal rate, %</label><input id="c_ca" type="number" min="0" max="13.3" step="0.1" value="9.3"><div class="hint">Used only when &ldquo;Custom flat marginal rate&rdquo; is selected.</div></div>
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
      <div class="field"><label for="c_disc">Discount rate, %</label><input id="c_disc" type="number" min="0" step="0.1" placeholder="0"><div class="hint">At least 4.91% (10-yr UST, 2026-11-24) plus a risk premium. No default — this is yours.</div></div>
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
  { k: 'src', label: 'Anchor / source' },
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
  { k: 'src', label: 'Evidence anchor' },
], st.scenarios.map(s => ({ ...s, source_id: s.id === 'ST-02' ? 'S-030' : s.id === 'ST-04' ? 'S-029' : s.id === 'ST-05' || s.id === 'ST-06' ? 'S-008' : s.id === 'ST-08' ? 'S-004' : null })), { note: 'No dollar loss is stated anywhere: replacement cost, insured limits, deductibles and business-interruption terms are all private documents not supplied to this project.' })}

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
  { k: 'src', label: 'Official source' },
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

<h2>What we do not have — ${qs.do_not_have.filter(g => g.status !== 'closed').length} open gaps (${qs.do_not_have.filter(g => g.status === 'closed').length} closed)</h2>
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
  { k: 'page', label: 'Appears on', html: true },
  { k: 'src', label: 'Official source' },
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
<p class="lede">Every figure on this site traces to one of these ${sources.sources.length} official sources. All are government, regional-agency or Federal-Reserve-hosted, retrieved 2026-11-25 to 2026-11-26, and enforced by an automated allowlist check in the build.</p>

${callout('info', 'Verification rule applied',
  'A row is only marked verified if the value was read directly from the official page or API response during this session. Where an official source could not be reached, the row is left blank and listed on <a href="flagged.html">Flagged for review</a> — never filled with an estimate.')}

${table([
  { k: 'id', label: 'ID' },
  { k: 'publisher', label: 'Publisher' },
  { k: 'title', label: 'Document', html: true },
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
  <p class="sub" style="margin-bottom:14px">Triple-net lease, expiration reported between 2030 and 2035. Anonymised: no address, owner identity, rent figure or personal finance is disclosed. Prepared 2026-11-26 for adviser review.</p>

  <h3>1 · The question put to you</h3>
  <p class="sub">Should the owner sell before lease expiry, or hold and renew? We are asking for a professional opinion on method and sequence, not for a valuation — the valuation inputs do not yet exist.</p>

  <h3>2 · What is verified</h3>
  <table style="font-size:9.5pt">
    <thead><tr><th>Metric</th><th class="num">Verified figure</th><th>Source</th></tr></thead>
    <tbody>
      <tr><td>Metro unemployment, Oct 2026</td><td class="num">4.6%</td><td class="faint"><a href="${SRC['S-002'].url}" target="_blank" rel="noopener noreferrer">BLS (S-002)</a></td></tr>
      <tr><td>Metro nonfarm / leisure jobs, YoY</td><td class="num">+0.9% / +2.0% (548.0k)</td><td class="faint"><a href="${SRC['S-002'].url}" target="_blank" rel="noopener noreferrer">BLS (S-002)</a></td></tr>
      <tr><td>Local CPI, 12-month (Sep 2026)</td><td class="num">3.7%</td><td class="faint"><a href="${SRC['S-002'].url}" target="_blank" rel="noopener noreferrer">BLS (S-002)</a></td></tr>
      <tr><td>10-year Treasury, 2026-11-24</td><td class="num">4.91%</td><td class="faint"><a href="${SRC['S-004'].url}" target="_blank" rel="noopener noreferrer">Fed H.15 / FRED (S-004)</a></td></tr>
      <tr><td>Metro HPI, 5-yr CAGR / vs Q1 peak</td><td class="num">4.57% / −0.82%</td><td class="faint"><a href="${SRC['S-005'].url}" target="_blank" rel="noopener noreferrer">FHFA (S-005)</a></td></tr>
      <tr><td>Tenant Q3 FY26 SSS / units / 9M rent rev.</td><td class="num">−1.1% / 2,115 / $242.5M</td><td class="faint"><a href="${SRC['S-039'].url}" target="_blank" rel="noopener noreferrer">SEC EDGAR (S-039, S-040)</a></td></tr>
      <tr><td>County disaster &amp; UCERF3 30-yr seismic</td><td class="num">DR-4856 / 60% M6.7</td><td class="faint"><a href="${SRC['S-029'].url}" target="_blank" rel="noopener noreferrer">FEMA / USGS (S-008, S-029)</a></td></tr>
      <tr><td>2026 Federal LTCG / §1250 / NIIT</td><td class="num">20% / 25% / 3.8%</td><td class="faint"><a href="${SRC['S-032'].url}" target="_blank" rel="noopener noreferrer">IRS Rev. Proc. 2025-32 (S-032)</a></td></tr>
      <tr><td>2026 California PIT + MHSA (no CG pref.)</td><td class="num">1.0%–12.3% + 1% &gt;$1M</td><td class="faint"><a href="${SRC['S-033'].url}" target="_blank" rel="noopener noreferrer">CA FTB (S-033, S-034)</a></td></tr>
      <tr><td>§1031 limits / Prop 13 base-year cap</td><td class="num">45 &amp; 180d / 1% + 2%/yr</td><td class="faint"><a href="${SRC['S-015'].url}" target="_blank" rel="noopener noreferrer">IRS / BOE Pub 29 (S-015, S-031)</a></td></tr>
      <tr><td>Decline-in-value deadline, 2026-27</td><td class="num">2026-11-30</td><td class="faint"><a href="${SRC['S-019'].url}" target="_blank" rel="noopener noreferrer">LA Assessor (S-019)</a></td></tr>
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
    <li>Parcel flood, fire, seismic &amp; ZIMAS/TOC status</li>
  </ul>

  <h3>4 · The finding you are being asked to test</h3>
  <p class="sub">Trailing appreciation does not predict forward appreciation in this metro: correlation <b>−0.937</b> across 7 overlapping five-year pairs, with the latest trailing window the lowest of 27. Meanwhile, the franchisor system shrunk from 2,191 to 2,115 units and carries $1.49B of debt including 7.624% 2026-1 notes. Please test whether any hold case relying on cap compression or 6%+ appreciation survives real quotes.</p>

  <h3>5 · What we ask of you</h3>
  <ol class="tight" style="font-size:9.5pt">
    <li>Confirm or correct the sequence: lease dates → insurance binder → cap-rate quotes and condition assessment → valuation.</li>
    <li>Give a written cap-rate opinion for the asset at both ends of its possible remaining term, expressed as a spread over 4.91%.</li>
    <li>Flag anything in the missing-items list that you would prioritise differently.</li>
    <li>State whether §1031 should be evaluated before listing.</li>
  </ol>

  <p class="faint" style="margin-top:16px;border-top:1px solid #ccc;padding-top:8px">Anonymised working document. No parcel address, owner identity, lease document or personal finance is included. Not investment, legal or tax advice. Full source register: <a href="sources.html">pages/sources.html</a> (<span class="src">https://kanlerxz87-cyber.github.io/Jackbox1/pages/sources.html</span>)</p>
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
