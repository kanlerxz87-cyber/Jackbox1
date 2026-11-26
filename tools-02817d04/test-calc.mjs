#!/usr/bin/env node
/**
 * Independent hand-verification suite for portal-02817d04/assets/calc.js (Session S-02817d04).
 * Verifies every statutory tax tier, transfer tax cliff, §1031 deferral, hold PV, blend-and-extend, and compound hazard shock.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const calcPath = path.resolve('portal-02817d04/assets/calc.js');
const calc = require(calcPath);

let passed = 0;
function check(name, fn) {
  fn();
  passed += 1;
}

// 1. Privacy static check on calc.js source code
check('calc.js contains zero network or browser storage calls', () => {
  const src = fs.readFileSync(calcPath, 'utf8');
  const forbidden = [/fetch\s*\(/, /XMLHttpRequest/, /sendBeacon/, /WebSocket/, /localStorage/, /sessionStorage/, /indexedDB/, /document\.cookie/];
  for (const rx of forbidden) {
    assert.equal(rx.test(src), false, `Forbidden API pattern matched: ${rx}`);
  }
});

// 2. Statutory constants match 2026-11-26 verified official sources
check('statutory constants match IRS, FTB, CA RTC, LAHD, and FRED H.15', () => {
  assert.equal(calc.STATUTORY.dgs10AnchorPct, 4.91);
  assert.equal(calc.STATUTORY.sec1250MaxRate, 0.25);
  assert.equal(calc.STATUTORY.niitRate, 0.038);
  assert.equal(calc.STATUTORY.countyTransferPer500, 0.55);
  assert.equal(calc.STATUTORY.caTopCombinedRate, 0.133);
  assert.equal(calc.lookupFedLtcgRate('mfj', 90000), 0.0);
  assert.equal(calc.lookupFedLtcgRate('mfj', 300000), 0.15);
  assert.equal(calc.lookupFedLtcgRate('mfj', 650000), 0.20);
  assert.equal(calc.lookupFedLtcgRate('single', 533400), 0.15);
  assert.equal(calc.lookupFedLtcgRate('single', 533401), 0.20);
});

// 3. Transfer taxes below and above $5M / $10M Measure ULA thresholds
check('CA RTC §11911 ($0.55/$500) and Measure ULA gross cliff tiers compute accurately', () => {
  const below = calc.computeTransferTaxes(4000000, { inLACity: true });
  assert.equal(below.countyTransferTax, 4400); // 8000 * 0.55
  assert.equal(below.ulaTransferTax, 0);

  const tier1 = calc.computeTransferTaxes(6000000, { inLACity: true });
  assert.equal(tier1.countyTransferTax, 6600);
  assert.equal(tier1.ulaTransferTax, 240000); // 4.0% of $6M

  const tier2 = calc.computeTransferTaxes(10000000, { inLACity: true });
  assert.equal(tier2.countyTransferTax, 11000);
  assert.equal(tier2.ulaTransferTax, 550000); // 5.5% of $10M

  const outsideLA = calc.computeTransferTaxes(6000000, { inLACity: false });
  assert.equal(outsideLA.ulaTransferTax, 0);
});

// 4. Exact hand-calculated after-tax sale test ($4.0M sale, $1.5M original basis, $500k accum dep, $400k debt)
check('computeAfterTaxSale matches exact penny hand-calculation', () => {
  const res = calc.computeAfterTaxSale({
    explicitSalePrice: 4000000,
    sellingCostPct: 4.0,
    inLACity: true,
    originalBasis: 1500000,
    capImprovements: 0,
    accumDepreciation: 500000,
    debtPayoff: 400000,
    filingStatus: 'mfj',
    otherTaxableIncome: 400000,
    caMarginalRatePct: 13.3,
    qiFee: 1500
  });
  // Selling costs: 4% of 4,000,000 = 160,000
  // County transfer tax: (4,000,000 / 500) * 0.55 = 4,400; ULA = 0 (<= 5,000,000)
  // Amount realized: 4,000,000 - 160,000 - 4,400 = 3,835,600
  // Adjusted basis: 1,500,000 - 500,000 = 1,000,000
  // Realized gain: 2,835,600
  // Unrecaptured §1250: 500,000 * 0.25 = 125,000
  // Remaining LTCG: 2,335,600 * 0.20 = 467,120
  // NIIT: 2,835,600 * 0.038 = 107,752.80
  // CA tax: 2,835,600 * 0.133 = 377,134.80
  // Total income taxes: 125,000 + 467,120 + 107,752.80 + 377,134.80 = 1,077,007.60
  // Net after-tax cash: 3,835,600 - 400,000 - 1,077,007.60 = 2,358,592.40
  assert.equal(res.amountRealized, 3835600);
  assert.equal(res.adjustedBasis, 1000000);
  assert.equal(res.realizedGain, 2835600);
  assert.equal(res.sec1250Tax, 125000);
  assert.equal(Math.round(res.fedLtcgTax * 100), 46712000);
  assert.equal(Math.round(res.niitTax * 100), 10775280);
  assert.equal(Math.round(res.caTax * 100), 37713480);
  assert.equal(Math.round(res.totalIncomeTaxes * 100), 107700760);
  assert.equal(Math.round(res.afterTaxSaleProceeds * 100), 235859240);
  // 1031 exchange equity: 3,835,600 - 400,000 - 1,500 = 3,434,100
  assert.equal(res.exchange1031Equity, 3434100);
});

// 5. Hold & Negotiated Renewal PV monotonicity and compound stress checks
check('Hold PV responds monotonically to renewal probability and compound hazard shocks', () => {
  const base = {
    currentNOI: 220000,
    asIsCapRatePct: 6.5,
    yearsToExpiry: 5,
    inTermAnnualBumpPct: 1.5,
    ordinaryIncomeTaxPct: 42,
    discountRatePct: 7.5,
    originalBasis: 1200000,
    accumDepreciation: 400000,
    debtPayoff: 0,
    renewalProbPct: 80,
    optionRentStepPct: 8,
    renewedExitCapPct: 5.75,
    darkMonthsIfVacate: 15,
    annualDarkCarryCost: 50000,
    retenantingCapex: 450000,
    replacementRentPctOfPrior: 85,
    reletExitCapPct: 6.75,
    landValueFloor: 2000000
  };
  const highRenew = calc.computeHoldAndRenewalPV(base);
  const lowRenew = calc.computeHoldAndRenewalPV({ ...base, renewalProbPct: 20 });
  assert.ok(highRenew.passiveHoldAfterTaxNPV > lowRenew.passiveHoldAfterTaxNPV, 'Higher renewal probability must yield higher Hold NPV');

  const stressed = calc.computeHoldAndRenewalPV({
    ...base,
    stressRentLossMonths: 18,
    stressUninsuredRepair: 500000,
    stressExitCapWideningBps: 150
  });
  assert.ok(stressed.passiveHoldAfterTaxNPV < highRenew.passiveHoldAfterTaxNPV - 450000, 'Compound hazard shock must materially depress Hold NPV');
  assert.ok(highRenew.blendImmediate1031Equity > highRenew.blendImmediateAfterTaxNet, '1031 equity exceeds taxable blend-and-extend sale');
});

// 6. Sensitivity grid dimensions
check('buildSensitivityGrid produces 5x4 cap-rate by renewal-probability matrix', () => {
  const grid = calc.buildSensitivityGrid({ currentNOI: 200000, originalBasis: 1000000, accumDepreciation: 300000 });
  assert.equal(grid.rows.length, 5);
  assert.equal(grid.rows[0].cells.length, 4);
});

console.log(`PASS: ${passed}/${passed} calculator mathematical & privacy assertions verified.`);
