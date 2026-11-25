#!/usr/bin/env node
/**
 * Headless functional test for the browser calculator (assets/js/calculator.js).
 * Builds a jsdom document from the real worksheet page, loads the real script,
 * fills the real form, and asserts the real output.
 *
 * Not part of the deploy gate (it needs a dev dependency); run with:
 *   npm install --no-save jsdom && node scripts/test-calculator.mjs
 */
import { readFileSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { JSDOM } from 'jsdom';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');

const html = readFileSync(join(ROOT, 'pages/worksheet.html'), 'utf8');
const calc = readFileSync(join(ROOT, 'assets/js/calculator.js'), 'utf8');

const dom = new JSDOM(html, { runScripts: 'outside-only', pretendToBeVisual: true });
const { window } = dom;

// no network is available/allowed inside the test harness
const netCalls = [];
window.fetch = (...a) => { netCalls.push(['fetch', a]); throw new Error('network blocked'); };
const OrigXHR = window.XMLHttpRequest;
window.XMLHttpRequest = function () { netCalls.push(['xhr']); return new OrigXHR(); };
Object.defineProperty(window, 'localStorage', {
  get() { netCalls.push(['localStorage']); throw new Error('storage blocked'); },
});
Object.defineProperty(window, 'sessionStorage', {
  get() { netCalls.push(['sessionStorage']); throw new Error('storage blocked'); },
});

window.eval(calc);
window.document.dispatchEvent(new window.Event('DOMContentLoaded'));

let failures = 0;
const check = (name, cond, extra = '') => {
  if (cond) {
    console.log(`  PASS  ${name}`);
  } else {
    failures++;
    console.log(`  FAIL  ${name} ${extra}`);
  }
};

const $ = (id) => window.document.getElementById(id);
const set = (id, v) => {
  const el = $(id);
  el.value = String(v);
  el.dispatchEvent(new window.Event('input', { bubbles: true }));
};
const out = () => $('c_out').textContent.replace(/\s+/g, ' ');

console.log('\n  Calculator functional test\n  ' + '-'.repeat(50));

// --- 1. empty state does not invent anything
check('empty state shows guidance, not a number', /Enter at least a sale price/.test(out()));
check('empty state does not show a dollar amount', !/\$\d/.test(out()));

// --- 2. a known, hand-checkable scenario
// price 1,000,000 · selling 5% (50,000) · basis 400,000 · accumDep 100,000
// adj basis = 300,000 ; net proceeds = 950,000 ; gain = 650,000
// recap = min(100,000, 650,000) = 100,000 @25%  = 25,000
// capGain = 550,000 ; other income 0 -> 15% tier -> 82,500
// NIIT off ; CA on @12.3% of 650,000 = 79,950
// total tax = 187,450 ; after-tax = 950,000 - 187,450 = 762,550
set('c_salePrice', 1_000_000);
set('c_sellingCost', 5);
set('c_basis', 400_000);
set('c_accumDep', 100_000);
set('c_mortgage', 0);
set('c_otherIncome', 0);
$('c_filing').value = 'single';
$('c_niit').value = 'no';
$('c_recapture').value = 'yes';
$('c_ca').value = 'yes';
set('c_years', 1);

const t2 = out();
check('net proceeds = $950,000', t2.includes('$950,000'), t2.slice(0, 400));
check('adjusted basis = $300,000', t2.includes('$300,000'));
check('realised gain = $650,000', t2.includes('$650,000'));
check('recapture tax = $25,000', t2.includes('$25,000'));
check('federal LTCG = $82,500', t2.includes('$82,500'));
check('CA tax = $79,950', t2.includes('$79,950'));
check('total tax = $187,450', t2.includes('$187,450'));
check('after-tax proceeds = $762,550', t2.includes('$762,550'));

// --- 3. NIIT toggle adds 3.8% of the gain (650,000 * 0.038 = 24,700)
$('c_niit').value = 'yes';
set('c_salePrice', 1_000_000);
check('NIIT adds $24,700', out().includes('$24,700'));
check('after-tax drops to $737,850', out().includes('$737,850'));

// --- 4. high income pushes the gain to the 20% federal tier
// other income 600,000 > single threshold 533,400 -> 20% of 550,000 = 110,000
$('c_niit').value = 'no';
set('c_otherIncome', 600_000);
check('20% tier applied ($110,000)', out().includes('$110,000'));

// --- 5. hold leg: NOI 100,000 flat, exit cap 6% -> exit value 1,666,667
set('c_otherIncome', 0);
set('c_noi', 100_000);
set('c_noiGrowth', 0);
set('c_holdExp', 0);
set('c_exitCap', 6);
set('c_discount', 8);
set('c_years', 5);
const t5 = out();
check('exit value ≈ $1,666,667', /1,666,66\d/.test(t5), t5.slice(0, 300));
check('five hold years rendered', (t5.match(/Year \d NOI/g) || []).length === 5);
check('sensitivity table rendered', t5.includes('Sensitivity'));
check('verdict warns it is not a recommendation', t5.includes('not a recommendation'));

// --- 6. a real loss produces no tax
set('c_salePrice', 100_000);
set('c_sellingCost', 5);
set('c_basis', 900_000);
set('c_accumDep', 0);
const t6 = out();
check('loss produces negative gain', t6.includes('−$805,000') || t6.includes('-$805,000'));
check('loss produces no CA tax', t6.includes('California income tax @ 12.30%$0') || /\$0/.test(t6));

// --- 7. privacy: nothing tried to leave the sandbox
check('no network calls made', netCalls.filter((c) => c[0] === 'fetch' || c[0] === 'xhr').length === 0,
  JSON.stringify(netCalls));
check('no storage access', netCalls.filter((c) => c[0].includes('Storage')).length === 0,
  JSON.stringify(netCalls));

// --- 8. reset clears
$('c_form').reset();
await new Promise((r) => setTimeout(r, 10));
check('reset clears the result', /Enter at least a sale price/.test(out()), out().slice(0,120));
check('reset cleared the fields', $('c_salePrice').value === '' && $('c_basis').value === '');

console.log('  ' + '-'.repeat(50));
if (failures) {
  console.log(`  ${failures} FAILURE(S)\n`);
  process.exit(1);
}
console.log('  All calculator assertions passed.\n');
