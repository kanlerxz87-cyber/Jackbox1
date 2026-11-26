/* Session S-02817d04 — Self-contained in-memory valuation, after-tax, and compound-stress engine.
 * Privacy architecture: runs 100% in volatile JS memory. Zero network requests, zero browser persistence, zero cookies.
 * Statutory constants verified on 2026-11-26 from IRS Topics 409 & 559, IRS Pub 946, IRC §1031, CA FTB 2025 schedules,
 * CA RTC §§11911 & 17043, LAHD Measure ULA, BOE Pub 29, and Federal Reserve H.15 (DGS10 = 4.91% on 2026-11-24).
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.JackboxCalc028 = factory();
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  var STATUTORY = Object.freeze({
    dgs10AnchorPct: 4.91,
    laCpiYoYPct: 3.70,
    sec1250MaxRate: 0.25,
    niitRate: 0.038,
    countyTransferPer500: 0.55,
    ulaBaseThreshold1: 5000000,
    ulaBaseThreshold2: 10000000,
    ulaBaseRate1: 0.04,
    ulaBaseRate2: 0.055,
    caTopScheduleRate: 0.123,
    caMentalHealthSurtax: 0.01,
    caTopCombinedRate: 0.133,
    fedLtcgBrackets2025: {
      single: { zeroMax: 48350, fifteenMax: 533400, niitMagi: 200000 },
      mfj: { zeroMax: 96700, fifteenMax: 600050, niitMagi: 250000 },
      mfs: { zeroMax: 48350, fifteenMax: 300000, niitMagi: 125000 },
      hoh: { zeroMax: 64750, fifteenMax: 566700, niitMagi: 200000 }
    }
  });

  function clampNum(v, fallback) {
    var n = Number(v);
    return Number.isFinite(n) ? n : fallback;
  }

  function roundCents(v) {
    return Math.round(v * 100) / 100;
  }

  function lookupFedLtcgRate(filingStatus, taxableIncomeWithGain) {
    var b = STATUTORY.fedLtcgBrackets2025[filingStatus] || STATUTORY.fedLtcgBrackets2025.mfj;
    if (taxableIncomeWithGain <= b.zeroMax) return 0.0;
    if (taxableIncomeWithGain <= b.fifteenMax) return 0.15;
    return 0.20;
  }

  function computeTransferTaxes(grossPrice, opts) {
    var price = Math.max(0, clampNum(grossPrice, 0));
    var countyTax = price > 0 ? roundCents(Math.ceil(price / 500) * STATUTORY.countyTransferPer500) : 0;
    var inLACity = Boolean(opts && opts.inLACity);
    var t1 = clampNum(opts && opts.ulaThreshold1, STATUTORY.ulaBaseThreshold1);
    var t2 = clampNum(opts && opts.ulaThreshold2, STATUTORY.ulaBaseThreshold2);
    var r1 = clampNum(opts && opts.ulaRate1, STATUTORY.ulaBaseRate1);
    var r2 = clampNum(opts && opts.ulaRate2, STATUTORY.ulaBaseRate2);
    var ulaTax = 0;
    var ulaTier = 'Exempt / Below Threshold';
    if (inLACity && price > t1) {
      if (price >= t2) {
        ulaTax = roundCents(price * r2);
        ulaTier = 'Measure ULA Tier 2 (' + (r2 * 100).toFixed(2) + '% gross)';
      } else {
        ulaTax = roundCents(price * r1);
        ulaTier = 'Measure ULA Tier 1 (' + (r1 * 100).toFixed(2) + '% gross)';
      }
    }
    return {
      countyTransferTax: countyTax,
      ulaTransferTax: ulaTax,
      ulaTier: ulaTier,
      totalTransferTax: roundCents(countyTax + ulaTax)
    };
  }

  function computeAfterTaxSale(raw) {
    var p = raw || {};
    var currentNOI = Math.max(0, clampNum(p.currentNOI, 0));
    var asIsCapRate = Math.max(0.005, clampNum(p.asIsCapRatePct, 6.5) / 100);
    var explicitSalePrice = clampNum(p.explicitSalePrice, 0);
    var grossSalePrice = explicitSalePrice > 0 ? explicitSalePrice : (currentNOI > 0 ? currentNOI / asIsCapRate : 0);

    var sellingCostPct = Math.max(0, clampNum(p.sellingCostPct, 4.0) / 100);
    var sellingCosts = grossSalePrice * sellingCostPct;
    var transfers = computeTransferTaxes(grossSalePrice, {
      inLACity: p.inLACity !== false,
      ulaThreshold1: p.ulaThreshold1,
      ulaThreshold2: p.ulaThreshold2,
      ulaRate1: p.ulaRate1Pct !== undefined ? clampNum(p.ulaRate1Pct, 4.0) / 100 : STATUTORY.ulaBaseRate1,
      ulaRate2: p.ulaRate2Pct !== undefined ? clampNum(p.ulaRate2Pct, 5.5) / 100 : STATUTORY.ulaBaseRate2
    });

    var originalBasis = Math.max(0, clampNum(p.originalBasis, 0));
    var capImprovements = Math.max(0, clampNum(p.capImprovements, 0));
    var accumDepreciation = Math.max(0, clampNum(p.accumDepreciation, 0));
    var adjustedBasis = Math.max(0, originalBasis + capImprovements - accumDepreciation);
    var debtPayoff = Math.max(0, clampNum(p.debtPayoff, 0));

    var amountRealized = Math.max(0, grossSalePrice - sellingCosts - transfers.totalTransferTax);
    var realizedGain = Math.max(0, amountRealized - adjustedBasis);
    var unrecaptured1250Gain = Math.min(realizedGain, accumDepreciation);
    var remainingLtcgGain = Math.max(0, realizedGain - unrecaptured1250Gain);

    var filingStatus = p.filingStatus || 'mfj';
    var otherIncome = Math.max(0, clampNum(p.otherTaxableIncome, 350000));
    var combinedIncome = otherIncome + realizedGain;
    var fedLtcgRate = p.overrideFedLtcgPct !== undefined && p.overrideFedLtcgPct !== null && p.overrideFedLtcgPct !== ''
      ? Math.max(0, clampNum(p.overrideFedLtcgPct, 20) / 100)
      : lookupFedLtcgRate(filingStatus, combinedIncome);
    var sec1250Rate = Math.min(STATUTORY.sec1250MaxRate, Math.max(fedLtcgRate, clampNum(p.sec1250RatePct, 25) / 100));

    var bracketInfo = STATUTORY.fedLtcgBrackets2025[filingStatus] || STATUTORY.fedLtcgBrackets2025.mfj;
    var niitApplies = p.niitApplies !== undefined ? Boolean(p.niitApplies) : (combinedIncome > bracketInfo.niitMagi);
    var caRate = Math.max(0, clampNum(p.caMarginalRatePct, combinedIncome > 1000000 ? 13.3 : 11.3) / 100);

    var sec1250Tax = unrecaptured1250Gain * sec1250Rate;
    var fedLtcgTax = remainingLtcgGain * fedLtcgRate;
    var niitTax = niitApplies ? realizedGain * STATUTORY.niitRate : 0;
    var caTax = realizedGain * caRate;
    var totalIncomeTaxes = sec1250Tax + fedLtcgTax + niitTax + caTax;

    var afterTaxSaleProceeds = amountRealized - debtPayoff - totalIncomeTaxes;
    var qiFee = Math.max(0, clampNum(p.qiFee, 1500));
    var exchange1031Equity = amountRealized - debtPayoff - qiFee;

    return {
      grossSalePrice: grossSalePrice,
      sellingCosts: sellingCosts,
      countyTransferTax: transfers.countyTransferTax,
      ulaTransferTax: transfers.ulaTransferTax,
      ulaTier: transfers.ulaTier,
      totalTransferTax: transfers.totalTransferTax,
      amountRealized: amountRealized,
      adjustedBasis: adjustedBasis,
      realizedGain: realizedGain,
      unrecaptured1250Gain: unrecaptured1250Gain,
      remainingLtcgGain: remainingLtcgGain,
      sec1250Rate: sec1250Rate,
      fedLtcgRate: fedLtcgRate,
      niitApplies: niitApplies,
      caRate: caRate,
      sec1250Tax: sec1250Tax,
      fedLtcgTax: fedLtcgTax,
      niitTax: niitTax,
      caTax: caTax,
      totalIncomeTaxes: totalIncomeTaxes,
      totalAllTaxesAndFriction: sellingCosts + transfers.totalTransferTax + totalIncomeTaxes,
      effectiveTaxPctOfGain: realizedGain > 0 ? (totalIncomeTaxes / realizedGain) * 100 : 0,
      debtPayoff: debtPayoff,
      afterTaxSaleProceeds: afterTaxSaleProceeds,
      exchange1031Equity: exchange1031Equity,
      taxDeferralAdvantage1031: exchange1031Equity - afterTaxSaleProceeds
    };
  }

  function computeHoldAndRenewalPV(raw) {
    var p = raw || {};
    var currentNOI = Math.max(0, clampNum(p.currentNOI, 0));
    var yearsToExpiry = Math.max(1, Math.min(20, Math.round(clampNum(p.yearsToExpiry, 6))));
    var inTermBumpPct = clampNum(p.inTermAnnualBumpPct, 1.5) / 100;
    var ordinaryIncomeTaxRate = Math.max(0, Math.min(0.60, clampNum(p.ordinaryIncomeTaxPct, 42.0) / 100));
    var discountRate = Math.max(0.01, clampNum(p.discountRatePct, 7.5) / 100);
    var debtPayoffAtHorizon = Math.max(0, clampNum(p.debtPayoffAtHorizon, clampNum(p.debtPayoff, 0)));

    var renewProb = Math.max(0, Math.min(1, clampNum(p.renewalProbPct, 60) / 100));
    var optionRentStepPct = clampNum(p.optionRentStepPct, 8.0) / 100;
    var renewedExitCap = Math.max(0.01, clampNum(p.renewedExitCapPct, 5.75) / 100);

    var darkMonths = Math.max(0, clampNum(p.darkMonthsIfVacate, 14));
    var annualDarkCarry = Math.max(0, clampNum(p.annualDarkCarryCost, currentNOI * 0.22));
    var retenantingCapex = Math.max(0, clampNum(p.retenantingCapex, currentNOI * 2.2));
    var replacementRentRatio = Math.max(0.2, clampNum(p.replacementRentPctOfPrior, 90) / 100);
    var reletExitCap = Math.max(0.01, clampNum(p.reletExitCapPct, 6.75) / 100);
    var landValueFloor = Math.max(0, clampNum(p.landValueFloor, 0));

    // Compound W-04 hazard shock (optional simultaneous rent loss + uninsured repair + exit cap widening)
    var stressRentLossMonths = Math.max(0, clampNum(p.stressRentLossMonths, 0));
    var stressUninsuredRepair = Math.max(0, clampNum(p.stressUninsuredRepair, 0));
    var stressExitCapBps = Math.max(0, clampNum(p.stressExitCapWideningBps, 0)) / 10000;

    var pvOperatingCashFlows = 0;
    var rentAtYear = currentNOI;
    for (var t = 1; t <= yearsToExpiry; t++) {
      if (t > 1) rentAtYear = rentAtYear * (1 + inTermBumpPct);
      var effectiveRent = rentAtYear;
      if (t === 1 && stressRentLossMonths > 0) {
        var lostFrac = Math.min(1, stressRentLossMonths / 12);
        effectiveRent = rentAtYear * (1 - lostFrac);
      }
      var afterTaxRent = effectiveRent * (1 - ordinaryIncomeTaxRate);
      if (t === 1 && stressUninsuredRepair > 0) {
        afterTaxRent -= stressUninsuredRepair;
      }
      if (t === 2 && stressRentLossMonths > 12) {
        var extraLostFrac = Math.min(1, (stressRentLossMonths - 12) / 12);
        afterTaxRent -= rentAtYear * extraLostFrac * (1 - ordinaryIncomeTaxRate);
      }
      pvOperatingCashFlows += afterTaxRent / Math.pow(1 + discountRate, t);
    }

    var finalInTermRent = rentAtYear;
    var renewedNOI = finalInTermRent * (1 + optionRentStepPct);
    var renewedGrossExit = renewedNOI / (renewedExitCap + stressExitCapBps);
    var renewedAfterTaxTerminal = computeAfterTaxSale(Object.assign({}, p, {
      explicitSalePrice: renewedGrossExit,
      debtPayoff: debtPayoffAtHorizon
    })).afterTaxSaleProceeds;

    var darkCarryTotal = annualDarkCarry * (darkMonths / 12);
    var reletNOI = finalInTermRent * replacementRentRatio;
    var rawReletValue = reletNOI / (reletExitCap + stressExitCapBps);
    var vacateGrossExit = Math.max(landValueFloor, rawReletValue);
    var vacateAfterTaxSale = computeAfterTaxSale(Object.assign({}, p, {
      explicitSalePrice: vacateGrossExit,
      capImprovements: clampNum(p.capImprovements, 0) + retenantingCapex,
      debtPayoff: debtPayoffAtHorizon
    })).afterTaxSaleProceeds;
    // Discount additional dark-period delay beyond yearsToExpiry
    var darkYearsExtra = darkMonths / 12;
    var vacateNetAtExpiry = (vacateAfterTaxSale / Math.pow(1 + discountRate, darkYearsExtra)) - darkCarryTotal - retenantingCapex;

    var expectedTerminalAtExpiry = renewProb * renewedAfterTaxTerminal + (1 - renewProb) * vacateNetAtExpiry;
    var pvExpectedTerminal = expectedTerminalAtExpiry / Math.pow(1 + discountRate, yearsToExpiry);
    var passiveHoldAfterTaxNPV = pvOperatingCashFlows + pvExpectedTerminal;

    // Negotiated Blend-and-Extend Now (Option 3)
    var blendStartRent = Math.max(0, clampNum(p.blendStartNOI, currentNOI));
    var blendTiConcession = Math.max(0, clampNum(p.blendTiConcession, currentNOI * 0.5));
    var blendCapRate = Math.max(0.01, (clampNum(p.blendExtendedCapPct, 5.50) / 100) + stressExitCapBps);
    var blendImmediateGrossValue = blendStartRent > 0 ? blendStartRent / blendCapRate : 0;
    var blendImmediateSale = computeAfterTaxSale(Object.assign({}, p, {
      explicitSalePrice: blendImmediateGrossValue,
      capImprovements: clampNum(p.capImprovements, 0) + blendTiConcession
    }));
    var blendImmediateAfterTaxNet = blendImmediateSale.afterTaxSaleProceeds - blendTiConcession;
    var blendImmediate1031Equity = blendImmediateSale.exchange1031Equity - blendTiConcession;

    // Hold 10 yrs under Blend-and-Extend
    var blendBumpPct = clampNum(p.blendAnnualBumpPct, 2.0) / 100;
    var blendHoldYears = Math.max(yearsToExpiry, Math.round(clampNum(p.blendHoldYears, 10)));
    var pvBlendHoldCF = -blendTiConcession;
    var bRent = blendStartRent;
    for (var k = 1; k <= blendHoldYears; k++) {
      if (k > 1) bRent = bRent * (1 + blendBumpPct);
      var bAfterTax = bRent * (1 - ordinaryIncomeTaxRate);
      if (k === 1 && stressUninsuredRepair > 0) bAfterTax -= stressUninsuredRepair;
      pvBlendHoldCF += bAfterTax / Math.pow(1 + discountRate, k);
    }
    var blendTerminalGross = (bRent * (1 + blendBumpPct)) / (renewedExitCap + stressExitCapBps);
    var blendTerminalNet = computeAfterTaxSale(Object.assign({}, p, {
      explicitSalePrice: blendTerminalGross,
      capImprovements: clampNum(p.capImprovements, 0) + blendTiConcession,
      debtPayoff: debtPayoffAtHorizon
    })).afterTaxSaleProceeds;
    var blendHoldAfterTaxNPV = pvBlendHoldCF + (blendTerminalNet / Math.pow(1 + discountRate, blendHoldYears));

    return {
      yearsToExpiry: yearsToExpiry,
      pvOperatingCashFlows: pvOperatingCashFlows,
      renewedGrossExit: renewedGrossExit,
      renewedAfterTaxTerminal: renewedAfterTaxTerminal,
      vacateGrossExit: vacateGrossExit,
      vacateNetAtExpiry: vacateNetAtExpiry,
      expectedTerminalAtExpiry: expectedTerminalAtExpiry,
      pvExpectedTerminal: pvExpectedTerminal,
      passiveHoldAfterTaxNPV: passiveHoldAfterTaxNPV,
      blendImmediateGrossValue: blendImmediateGrossValue,
      blendImmediateAfterTaxNet: blendImmediateAfterTaxNet,
      blendImmediate1031Equity: blendImmediate1031Equity,
      blendHoldAfterTaxNPV: blendHoldAfterTaxNPV
    };
  }

  function buildSensitivityGrid(baseInputs) {
    var capRates = [5.25, 5.75, 6.25, 6.75, 7.25];
    var renewProbs = [25, 50, 75, 100];
    var rows = [];
    for (var i = 0; i < capRates.length; i++) {
      var cap = capRates[i];
      var saleRes = computeAfterTaxSale(Object.assign({}, baseInputs, { asIsCapRatePct: cap, explicitSalePrice: 0 }));
      var cells = [];
      for (var j = 0; j < renewProbs.length; j++) {
        var rp = renewProbs[j];
        var holdRes = computeHoldAndRenewalPV(Object.assign({}, baseInputs, {
          asIsCapRatePct: cap,
          renewalProbPct: rp
        }));
        cells.push({
          renewalProbPct: rp,
          holdMinusSaleAfterTax: holdRes.passiveHoldAfterTaxNPV - saleRes.afterTaxSaleProceeds,
          passiveHoldNPV: holdRes.passiveHoldAfterTaxNPV
        });
      }
      rows.push({
        asIsCapRatePct: cap,
        afterTaxSaleProceeds: saleRes.afterTaxSaleProceeds,
        cells: cells
      });
    }
    return { capRates: capRates, renewProbs: renewProbs, rows: rows };
  }

  return {
    STATUTORY: STATUTORY,
    lookupFedLtcgRate: lookupFedLtcgRate,
    computeTransferTaxes: computeTransferTaxes,
    computeAfterTaxSale: computeAfterTaxSale,
    computeHoldAndRenewalPV: computeHoldAndRenewalPV,
    buildSensitivityGrid: buildSensitivityGrid
  };
});
