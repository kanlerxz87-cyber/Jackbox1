/* ==========================================================================
   Central LA NNN QSR — Zero-Telemetry Private Calculator
   File: hub/assets/js/calculator.js
   Privacy Guarantee: Runs 100% in browser RAM. Zero network requests,
   zero cookies, zero browser storage, zero telemetry.

   Statutory Rules Coded (Verified 2026-11-26):
   - 2026 Federal LTCG Brackets: IRS Rev. Proc. 2025-32
   - Unrecaptured Sec. 1250 Recapture (25% ceiling): IRS Topic 409
   - Net Investment Income Tax (3.8% NIIT): IRS Topic 559
   - 2026 California Progressive Schedules X/Y/Z: CA FTB Tax News Oct 2026
   - CA 1.00% Behavioral Health Services Tax (>$1,000,000): 2026 Form 540-ES
   - City of LA Measure ULA (eff. 2026-07-01): $5.4M (4.0%) / $10.9M (5.5%)
   - City of LA Base Transfer Tax: $2.25 per $500 (0.45%)
   - LA County Documentary Transfer Tax: $0.55 per $500 (0.11%)
   ========================================================================== */

(function () {
  "use strict";

  var FED_LTCG_2026 = {
    mfj:    { zeroMax: 98900,  fifteenMax: 613700, niit: 250000 },
    single: { zeroMax: 49450,  fifteenMax: 545500, niit: 200000 },
    hoh:    { zeroMax: 66200,  fifteenMax: 579600, niit: 200000 },
    mfs:    { zeroMax: 49450,  fifteenMax: 306850, niit: 125000 },
    trust:  { zeroMax: 3300,   fifteenMax: 16250,  niit: 16000  }
  };

  // Exact 2026 CA FTB Schedules X, Y, Z (Tax News October 2026)
  var CA_SCHEDULES_2026 = {
    single: [
      [0,       11456,   0.010],
      [11456,   27157,   0.020],
      [27157,   42861,   0.040],
      [42861,   59498,   0.060],
      [59498,   75197,   0.080],
      [75197,   384109,  0.093],
      [384109,  460927,  0.103],
      [460927,  768213,  0.113],
      [768213,  Infinity,0.123]
    ],
    mfj: [
      [0,       22912,   0.010],
      [22912,   54314,   0.020],
      [54314,   85722,   0.040],
      [85722,   118996,  0.060],
      [118996,  150394,  0.080],
      [150394,  768218,  0.093],
      [768218,  921854,  0.103],
      [921854,  1536426, 0.113],
      [1536426, Infinity,0.123]
    ],
    hoh: [
      [0,       22927,   0.010],
      [22927,   54316,   0.020],
      [54316,   70018,   0.040],
      [70018,   86654,   0.060],
      [86654,   102356,  0.080],
      [102356,  522385,  0.093],
      [522385,  626864,  0.103],
      [626864,  1044771, 0.113],
      [1044771, Infinity,0.123]
    ]
  };
  CA_SCHEDULES_2026.mfs = CA_SCHEDULES_2026.single;
  CA_SCHEDULES_2026.trust = CA_SCHEDULES_2026.single;

  var BHSA_THRESHOLD = 1000000;
  var ULA_TIER1_GT = 5400000;   // > $5,400,000 to < $10,900,000 => 4.0%
  var ULA_TIER2_GTE = 10900000; // >= $10,900,000 => 5.5%

  function calcCATaxTotal(taxableIncome, status) {
    if (taxableIncome <= 0) return 0;
    var sched = CA_SCHEDULES_2026[status] || CA_SCHEDULES_2026.mfj;
    var tax = 0;
    for (var i = 0; i < sched.length; i++) {
      var low = sched[i][0];
      var high = sched[i][1];
      var rate = sched[i][2];
      if (taxableIncome > low) {
        tax += (Math.min(taxableIncome, high) - low) * rate;
      }
    }
    if (taxableIncome > BHSA_THRESHOLD) {
      tax += (taxableIncome - BHSA_THRESHOLD) * 0.01;
    }
    return tax;
  }

  function calcTransferTaxes(price, jurisdiction, customPct) {
    if (price <= 0) {
      return { county: 0, cityBase: 0, ula: 0, total: 0, ulaTier: "None" };
    }
    // Documentary Transfer Tax computed per $500 or fractional part thereof
    var units500 = Math.ceil(price / 500);
    var county = units500 * 0.55; // $1.10 per $1,000 = 0.11%
    var cityBase = 0;
    var ula = 0;
    var ulaTier = "Not in City of LA";

    if (jurisdiction === "city_la") {
      cityBase = units500 * 2.25; // $4.50 per $1,000 = 0.45%
      if (price >= ULA_TIER2_GTE) {
        ula = price * 0.055;
        ulaTier = "Tier 2 (5.5% >= $10.9M)";
      } else if (price > ULA_TIER1_GT) {
        ula = price * 0.04;
        ulaTier = "Tier 1 (4.0% > $5.4M)";
      } else {
        ulaTier = "Below $5.4M ULA Threshold ($0)";
      }
    } else if (jurisdiction === "custom") {
      cityBase = price * (Math.max(0, customPct) / 100);
      ulaTier = "Custom City Rate (" + customPct.toFixed(2) + "%)";
    }
    return {
      county: county,
      cityBase: cityBase,
      ula: ula,
      total: county + cityBase + ula,
      ulaTier: ulaTier
    };
  }

  function calcSaleTaxes(params) {
    var price = params.price;
    var sellingCosts = params.sellingCosts;
    var transfer = calcTransferTaxes(price, params.jurisdiction, params.customCityPct);
    var amountRealized = Math.max(0, price - sellingCosts - transfer.total);
    var totalGain = Math.max(0, amountRealized - params.adjustedBasis);

    var sec1250Gain = Math.min(totalGain, Math.max(0, params.accumDepr));
    var ltcgGain = Math.max(0, totalGain - sec1250Gain);

    var status = params.filingStatus;
    var fedRules = FED_LTCG_2026[status] || FED_LTCG_2026.mfj;
    var baseInc = Math.max(0, params.otherIncome);

    // IRC Sec. 1(h): Unrecaptured Sec. 1250 taxed up to 25% ceiling
    var fedSec1250Tax = sec1250Gain * 0.25;

    // LTCG sits atop ordinary income + Sec. 1250 gain in 2026 brackets
    var stackStart = baseInc + sec1250Gain;
    var stackEnd = stackStart + ltcgGain;

    var slice0 = Math.max(0, Math.min(stackEnd, fedRules.zeroMax) - stackStart);
    var slice15Start = Math.max(stackStart, fedRules.zeroMax);
    var slice15 = Math.max(0, Math.min(stackEnd, fedRules.fifteenMax) - slice15Start);
    var slice20Start = Math.max(stackStart, fedRules.fifteenMax);
    var slice20 = Math.max(0, stackEnd - slice20Start);

    var fedLtcgTax = slice0 * 0.0 + slice15 * 0.15 + slice20 * 0.20;

    // Federal 3.8% NIIT (IRC Sec. 1411)
    var niitBase = Math.min(totalGain, Math.max(0, baseInc + totalGain - fedRules.niit));
    var fedNiitTax = niitBase * 0.038;

    // Incremental California Tax (progressive 2026 schedule + 1% BHSA > $1M)
    var caTaxBefore = calcCATaxTotal(baseInc, status);
    var caTaxAfter = calcCATaxTotal(baseInc + totalGain, status);
    var caIncrementalTax = Math.max(0, caTaxAfter - caTaxBefore);
    var bhsaIncremental = Math.max(0, Math.max(0, baseInc + totalGain - BHSA_THRESHOLD) - Math.max(0, baseInc - BHSA_THRESHOLD)) * 0.01;

    var totalIncomeTax = fedSec1250Tax + fedLtcgTax + fedNiitTax + caIncrementalTax;
    var netAfterTaxCash = price - sellingCosts - transfer.total - params.debtPayoff - params.prepayPenalty - totalIncomeTax;
    var net1031Equity = price - sellingCosts - transfer.total - params.debtPayoff - params.prepayPenalty;

    return {
      price: price,
      sellingCosts: sellingCosts,
      transfer: transfer,
      amountRealized: amountRealized,
      totalGain: totalGain,
      sec1250Gain: sec1250Gain,
      ltcgGain: ltcgGain,
      fedSec1250Tax: fedSec1250Tax,
      fedLtcgTax: fedLtcgTax,
      fedNiitTax: fedNiitTax,
      caIncrementalTax: caIncrementalTax,
      bhsaIncremental: bhsaIncremental,
      totalIncomeTax: totalIncomeTax,
      totalLeakage: sellingCosts + transfer.total + params.prepayPenalty + totalIncomeTax,
      netAfterTaxCash: netAfterTaxCash,
      net1031Equity: net1031Equity
    };
  }

  function numVal(id) {
    var el = document.getElementById(id);
    if (!el) return NaN;
    var raw = String(el.value || "").replace(/,/g, "").trim();
    if (raw === "") return NaN;
    return parseFloat(raw);
  }

  function numOrZero(id) {
    var v = numVal(id);
    return isNaN(v) ? 0 : v;
  }

  function strVal(id) {
    var el = document.getElementById(id);
    return el ? el.value : "";
  }

  function boolVal(id) {
    var el = document.getElementById(id);
    return !!(el && el.checked);
  }

  function fmtUSD(n) {
    if (!isFinite(n)) return "—";
    var neg = n < 0;
    var abs = Math.round(Math.abs(n));
    return (neg ? "-$" : "$") + abs.toLocaleString("en-US");
  }

  function fmtPct(n) {
    if (!isFinite(n)) return "—";
    return (n * 100).toFixed(2) + "%";
  }

  function setText(id, text) {
    var el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function runCalculation() {
    var noi = numVal("in_noi");
    var saleCap = numVal("in_sale_cap");
    var priceOverride = numVal("in_price_override");
    var adjustedBasis = numVal("in_basis");

    var grossPrice = (!isNaN(priceOverride) && priceOverride > 0)
      ? priceOverride
      : ((!isNaN(noi) && noi > 0 && !isNaN(saleCap) && saleCap > 0) ? noi / (saleCap / 100) : NaN);

    var banner = document.getElementById("calc_status_banner");
    var missing = [];
    if (isNaN(noi) || noi <= 0) missing.push("Current Annual NOI");
    if (isNaN(grossPrice) || grossPrice <= 0) missing.push("Today's Sale Cap Rate (or Gross Price)");
    if (isNaN(adjustedBasis) || adjustedBasis < 0) missing.push("Adjusted Tax Basis");

    if (missing.length > 0) {
      if (banner) {
        banner.querySelector(".rb-title").textContent = "AWAITING PRIVATE OWNER INPUTS";
        banner.querySelector(".rb-main").textContent = "Enter " + missing.join(", ");
        banner.querySelector(".rb-sub").textContent = "No fabricated defaults are loaded. All calculations run strictly in local browser memory.";
      }
      var clearIds = [
        "out_case_a", "out_case_b", "out_case_c", "out_bridge",
        "out_gross_price", "out_sell_cost", "out_transfer_county", "out_transfer_city",
        "out_transfer_ula", "out_total_gain", "out_fed_1250", "out_fed_ltcg",
        "out_fed_niit", "out_ca_tax", "out_total_tax", "out_debt_payoff",
        "out_net_a", "out_net_b", "out_pv_cf", "out_pv_term", "out_net_c",
        "out_breakeven_cap", "out_ula_tier", "out_eff_rate"
      ];
      for (var c = 0; c < clearIds.length; c++) setText(clearIds[c], "—");
      return;
    }

    var filingStatus = strVal("in_filing_status") || "mfj";
    var jurisdiction = strVal("in_jurisdiction") || "city_la";
    var customCityPct = numOrZero("in_custom_city_pct");
    var accumDepr = numOrZero("in_depr");
    var otherIncome = numOrZero("in_other_income");
    var sellCostPct = numOrZero("in_sell_cost_pct");
    var debtPayoff = numOrZero("in_debt");
    var prepayPenalty = numOrZero("in_prepay");

    // Case A & Case B (Sell Today)
    var todaySale = calcSaleTaxes({
      price: grossPrice,
      sellingCosts: grossPrice * (sellCostPct / 100),
      jurisdiction: jurisdiction,
      customCityPct: customCityPct,
      adjustedBasis: adjustedBasis,
      accumDepr: accumDepr,
      otherIncome: otherIncome,
      filingStatus: filingStatus,
      debtPayoff: debtPayoff,
      prepayPenalty: prepayPenalty
    });

    // Case C (Hold / Negotiated Renewal + Optional Stress Test)
    var remPrimaryYrs = Math.max(0, Math.round(numOrZero("in_rem_yrs")));
    var renewYrs = Math.max(0, Math.round(numOrZero("in_renew_yrs")));
    var holdYears = Math.max(1, remPrimaryYrs + renewYrs);
    var escRate = numOrZero("in_esc_pct") / 100;
    var renewResetPct = numOrZero("in_renew_reset_pct") / 100;
    var renewCapex = numOrZero("in_renew_capex");
    var annualTaxRate = Math.min(0.60, Math.max(0, numOrZero("in_cf_tax_pct") / 100));
    var annualDebtService = numOrZero("in_debt_service");
    var discRate = Math.max(0.005, (numOrZero("in_disc_pct") || 6.5) / 100);
    var exitCapBase = (numOrZero("in_exit_cap") || saleCap) / 100;

    // Optional Compound Stress Inputs
    var stressVacMonths = Math.max(0, numOrZero("in_stress_vac_months"));
    var stressRepair = Math.max(0, numOrZero("in_stress_repair"));
    var stressCapBps = numOrZero("in_stress_cap_bps") / 10000;
    var stepUpAtExit = boolVal("in_step_up");

    var pvCashFlows = 0;
    var curNoi = noi;
    var stressYear = Math.min(holdYears, Math.max(1, remPrimaryYrs || 1));

    for (var y = 1; y <= holdYears; y++) {
      if (y > 1) {
        curNoi = curNoi * (1 + escRate);
      }
      var yearCapex = 0;
      if (renewYrs > 0 && y === remPrimaryYrs + 1) {
        curNoi = curNoi * (1 + renewResetPct);
        yearCapex += renewCapex;
      }
      var vacLoss = 0;
      var shockRepair = 0;
      if (y === stressYear && (stressVacMonths > 0 || stressRepair > 0)) {
        vacLoss = curNoi * Math.min(1, stressVacMonths / 12);
        shockRepair = stressRepair;
      }
      var operatingNet = curNoi - vacLoss;
      var afterTaxCF = operatingNet * (1 - annualTaxRate) - annualDebtService - yearCapex - shockRepair;
      pvCashFlows += afterTaxCF / Math.pow(1 + discRate, y);
    }

    // Forward Year N+1 NOI for terminal valuation
    var forwardNoi = curNoi * (1 + escRate);
    var exitCapFinal = Math.max(0.02, exitCapBase + stressCapBps);
    var terminalGrossPrice = forwardNoi / exitCapFinal;
    var termSellingCosts = terminalGrossPrice * (sellCostPct / 100);

    var termSale = calcSaleTaxes({
      price: terminalGrossPrice,
      sellingCosts: termSellingCosts,
      jurisdiction: jurisdiction,
      customCityPct: customCityPct,
      adjustedBasis: stepUpAtExit ? terminalGrossPrice : adjustedBasis,
      accumDepr: stepUpAtExit ? 0 : accumDepr,
      otherIncome: otherIncome,
      filingStatus: filingStatus,
      debtPayoff: debtPayoff,
      prepayPenalty: 0
    });

    var pvTerminal = termSale.netAfterTaxCash / Math.pow(1 + discRate, holdYears);
    var totalPvCaseC = pvCashFlows + pvTerminal;
    var bridgeDiff = totalPvCaseC - todaySale.netAfterTaxCash;

    // Solve approximate Break-Even Exit Cap Rate (where PV(Case C) == Case A)
    var reqTerminalNet = (todaySale.netAfterTaxCash - pvCashFlows) * Math.pow(1 + discRate, holdYears);
    var breakevenCapStr = "N/A";
    if (reqTerminalNet > 0 && forwardNoi > 0) {
      // Binary search on terminal gross price
      var lo = 0.02, hi = 0.25;
      for (var iter = 0; iter < 36; iter++) {
        var mid = (lo + hi) / 2;
        var testPrice = forwardNoi / mid;
        var testSale = calcSaleTaxes({
          price: testPrice,
          sellingCosts: testPrice * (sellCostPct / 100),
          jurisdiction: jurisdiction,
          customCityPct: customCityPct,
          adjustedBasis: stepUpAtExit ? testPrice : adjustedBasis,
          accumDepr: stepUpAtExit ? 0 : accumDepr,
          otherIncome: otherIncome,
          filingStatus: filingStatus,
          debtPayoff: debtPayoff,
          prepayPenalty: 0
        });
        if (testSale.netAfterTaxCash > reqTerminalNet) {
          lo = mid;
        } else {
          hi = mid;
        }
      }
      breakevenCapStr = ((lo + hi) / 2 * 100).toFixed(2) + "%";
    }

    // Render summary banner & detail cells
    if (banner) {
      banner.querySelector(".rb-title").textContent = "COMPARABLE AFTER-TAX PRESENT-VALUE BRIDGE (USER INPUTS ONLY)";
      var leadText = (bridgeDiff >= 0 ? "Hold / Renewal PV exceeds Sell-Today Taxable by +" : "Sell-Today Taxable exceeds Hold / Renewal PV by +") + fmtUSD(Math.abs(bridgeDiff));
      banner.querySelector(".rb-main").textContent = leadText;
      banner.querySelector(".rb-sub").textContent =
        "Hold Horizon: " + holdYears + " yrs · Terminal Exit Cap: " + fmtPct(exitCapFinal) +
        (stepUpAtExit ? " (IRC §1014 Step-Up Mode ON)" : " (Taxable Terminal Exit)") +
        " · §1031 Reinvestable Equity Today: " + fmtUSD(todaySale.net1031Equity) + ".";
    }

    setText("out_case_a", fmtUSD(todaySale.netAfterTaxCash));
    setText("out_case_b", fmtUSD(todaySale.net1031Equity));
    setText("out_case_c", fmtUSD(totalPvCaseC));
    setText("out_bridge", (bridgeDiff >= 0 ? "+" : "") + fmtUSD(bridgeDiff));

    setText("out_gross_price", fmtUSD(todaySale.price));
    setText("out_sell_cost", "-" + fmtUSD(todaySale.sellingCosts));
    setText("out_transfer_county", "-" + fmtUSD(todaySale.transfer.county));
    setText("out_transfer_city", "-" + fmtUSD(todaySale.transfer.cityBase));
    setText("out_transfer_ula", "-" + fmtUSD(todaySale.transfer.ula));
    setText("out_ula_tier", todaySale.transfer.ulaTier);
    setText("out_total_gain", fmtUSD(todaySale.totalGain));
    setText("out_fed_1250", "-" + fmtUSD(todaySale.fedSec1250Tax));
    setText("out_fed_ltcg", "-" + fmtUSD(todaySale.fedLtcgTax));
    setText("out_fed_niit", "-" + fmtUSD(todaySale.fedNiitTax));
    setText("out_ca_tax", "-" + fmtUSD(todaySale.caIncrementalTax) + (todaySale.bhsaIncremental > 0 ? " (incl. " + fmtUSD(todaySale.bhsaIncremental) + " BHSA)" : ""));
    setText("out_total_tax", "-" + fmtUSD(todaySale.totalIncomeTax));
    setText("out_eff_rate", todaySale.totalGain > 0 ? fmtPct(todaySale.totalIncomeTax / todaySale.totalGain) : "0.00%");
    setText("out_debt_payoff", "-" + fmtUSD(debtPayoff + prepayPenalty));
    setText("out_net_a", fmtUSD(todaySale.netAfterTaxCash));
    setText("out_net_b", fmtUSD(todaySale.net1031Equity));
    setText("out_pv_cf", fmtUSD(pvCashFlows));
    setText("out_pv_term", fmtUSD(pvTerminal));
    setText("out_net_c", fmtUSD(totalPvCaseC));
    setText("out_breakeven_cap", breakevenCapStr);
  }

  function clearAll() {
    var ids = [
      "in_noi", "in_sale_cap", "in_price_override", "in_basis", "in_depr",
      "in_other_income", "in_sell_cost_pct", "in_debt", "in_prepay",
      "in_custom_city_pct", "in_rem_yrs", "in_renew_yrs", "in_esc_pct",
      "in_renew_reset_pct", "in_renew_capex", "in_cf_tax_pct", "in_debt_service",
      "in_disc_pct", "in_exit_cap", "in_stress_vac_months", "in_stress_repair",
      "in_stress_cap_bps"
    ];
    for (var i = 0; i < ids.length; i++) {
      var el = document.getElementById(ids[i]);
      if (el) el.value = "";
    }
    var cb = document.getElementById("in_step_up");
    if (cb) cb.checked = false;
    var warn = document.getElementById("synthetic_warning");
    if (warn) warn.style.display = "none";
    runCalculation();
  }

  function loadSyntheticTest() {
    var sample = {
      in_noi: "300000",
      in_sale_cap: "5.25",
      in_price_override: "",
      in_basis: "1200000",
      in_depr: "650000",
      in_other_income: "250000",
      in_sell_cost_pct: "3.0",
      in_debt: "0",
      in_prepay: "0",
      in_rem_yrs: "5",
      in_renew_yrs: "5",
      in_esc_pct: "2.0",
      in_renew_reset_pct: "0",
      in_renew_capex: "75000",
      in_cf_tax_pct: "35",
      in_debt_service: "0",
      in_disc_pct: "6.5",
      in_exit_cap: "6.00",
      in_stress_vac_months: "0",
      in_stress_repair: "0",
      in_stress_cap_bps: "0"
    };
    for (var k in sample) {
      if (Object.prototype.hasOwnProperty.call(sample, k)) {
        var el = document.getElementById(k);
        if (el) el.value = sample[k];
      }
    }
    var jur = document.getElementById("in_jurisdiction");
    if (jur) jur.value = "city_la";
    var fs = document.getElementById("in_filing_status");
    if (fs) fs.value = "mfj";
    var warn = document.getElementById("synthetic_warning");
    if (warn) warn.style.display = "block";
    runCalculation();
  }

  function toggleCustomCity() {
    var jur = strVal("in_jurisdiction");
    var wrap = document.getElementById("custom_city_wrap");
    if (wrap) wrap.style.display = (jur === "custom") ? "block" : "none";
  }

  document.addEventListener("DOMContentLoaded", function () {
    var form = document.getElementById("calc_form");
    if (!form) return;

    var inputs = form.querySelectorAll("input, select");
    for (var i = 0; i < inputs.length; i++) {
      inputs[i].addEventListener("input", runCalculation);
      inputs[i].addEventListener("change", function () {
        toggleCustomCity();
        runCalculation();
      });
    }

    var clearBtn = document.getElementById("btn_clear_calc");
    if (clearBtn) clearBtn.addEventListener("click", clearAll);

    var sampleBtn = document.getElementById("btn_load_synthetic");
    if (sampleBtn) sampleBtn.addEventListener("click", loadSyntheticTest);

    toggleCustomCity();
    runCalculation();
  });
})();
