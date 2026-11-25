/* =====================================================================
   Private, offline sell-versus-hold + after-tax calculator (W-02 / W-06 / W-09)
   ---------------------------------------------------------------------
   PRIVACY: this file makes no network requests, sets no cookies, writes
   nothing to storage, and never transmits an input. Every number the user
   types stays inside the browser tab and is discarded on reload.

   TAX RATES: every statutory rate used below is a named constant that is
   cited on the page from an official source. Nothing here is a forecast.
   ===================================================================== */
(function () {
  'use strict';

  /* ---- cited constants (see pages/worksheet.html for source links) ---- */
  var RATE = {
    fedLtcgLow: 0.15,      // IRS Topic 409 — 15% tier
    fedLtcgHigh: 0.20,     // IRS Topic 409 — 20% tier
    unrecaptured1250: 0.25, // IRS Topic 409 — max 25%
    niit: 0.038,           // IRS Topic 559
    caTop: 0.123           // FTB 2024 Form 540 top bracket listed
  };

  var $ = function (id) { return document.getElementById(id); };
  var num = function (id) {
    var el = $(id);
    if (!el) return 0;
    var v = parseFloat(String(el.value).replace(/[, ]/g, ''));
    return isFinite(v) ? v : 0;
  };
  var money = function (n) {
    if (!isFinite(n)) return '—';
    var neg = n < 0;
    var s = Math.round(Math.abs(n)).toLocaleString('en-US');
    return (neg ? '−$' : '$') + s;
  };
  var pct = function (n) { return (n * 100).toFixed(2) + '%'; };

  function readInputs() {
    return {
      // sale side
      salePrice: num('c_salePrice'),
      sellingCostPct: num('c_sellingCost') / 100,
      // basis side
      basis: num('c_basis'),
      accumDep: num('c_accumDep'),
      // hold side
      annualNoi: num('c_noi'),
      noiGrowth: num('c_noiGrowth') / 100,
      years: Math.max(0, Math.round(num('c_years'))),
      exitCap: num('c_exitCap') / 100,
      holdExpenses: num('c_holdExp'),
      // financing / discount
      discountRate: num('c_discount') / 100,
      mortgageBalance: num('c_mortgage'),
      // tax posture
      filing: ($('c_filing') || {}).value || 'mfj',
      niitApplies: ($('c_niit') || {}).value === 'yes',
      recapture: ($('c_recapture') || {}).value !== 'no',
      caEnabled: ($('c_ca') || {}).value !== 'no'
    };
  }

  /* ---- marginal long-term capital gain rate (IRS Topic 409) ---- */
  function fedLtcgRate(filing, otherIncome) {
    var t = filing === 'single'
      ? { hi: 533400 }
      : filing === 'mfs'
        ? { hi: 300000 }
        : filing === 'hoh'
          ? { hi: 566700 }
          : { hi: 600050 };
    return otherIncome > t.hi ? RATE.fedLtcgHigh : RATE.fedLtcgLow;
  }

  function computeSale(inp, otherIncome) {
    var salePrice = inp.salePrice;
    var selling = salePrice * inp.sellingCostPct;
    var netProceeds = salePrice - selling;

    var adjBasis = inp.basis - inp.accumDep;      // depreciation reduces basis
    var totalGain = netProceeds - adjBasis;        // may be negative

    // Split: unrecaptured s.1250 gain is the lesser of accumulated depreciation
    // or the total gain (if the deal is at a loss, nothing is recaptured).
    var recap = 0;
    var capGain = 0;
    if (totalGain > 0) {
      recap = inp.recapture ? Math.min(inp.accumDep, totalGain) : 0;
      capGain = totalGain - recap;
    }

    var rate = fedLtcgRate(inp.filing, otherIncome);

    var fedCap = capGain * rate;
    var fedRecap = recap * RATE.unrecaptured1250;
    var niit = inp.niitApplies ? Math.max(0, totalGain) * RATE.niit : 0;
    var ca = inp.caEnabled
      ? (Math.max(0, totalGain) * RATE.caTop)   // CA taxes capital gain as ordinary income
      : 0;

    var totalTax = fedCap + fedRecap + niit + ca;
    var afterTaxProceeds = netProceeds - totalTax - inp.mortgageBalance;

    return {
      selling: selling,
      netProceeds: netProceeds,
      adjBasis: adjBasis,
      totalGain: totalGain,
      recap: recap,
      capGain: capGain,
      fedCap: fedCap,
      fedRecap: fedRecap,
      niit: niit,
      ca: ca,
      totalTax: totalTax,
      afterTaxProceeds: afterTaxProceeds,
      ltcgRate: rate
    };
  }

  function computeHold(inp) {
    // Year-by-year NOI, terminal value at exit cap, discounted.
    var rows = [];
    var pv = 0;
    var cumNoi = 0;
    var r = inp.discountRate;
    for (var y = 1; y <= inp.years; y++) {
      var noi = inp.annualNoi * Math.pow(1 + inp.noiGrowth, y - 1) - inp.holdExpenses;
      var df = r === 0 ? 1 : 1 / Math.pow(1 + r, y);
      pv += noi * df;
      cumNoi += noi;
      rows.push({ year: y, noi: noi, pv: noi * df });
    }
    var exitNoi = inp.annualNoi * Math.pow(1 + inp.noiGrowth, inp.years);
    var exitValue = inp.exitCap > 0 ? exitNoi / inp.exitCap : NaN;
    var exitPv = r === 0 ? exitValue : exitValue / Math.pow(1 + r, inp.years);
    var holdPv = pv + exitPv;
    return {
      rows: rows,
      cumNoi: cumNoi,
      exitNoi: exitNoi,
      exitValue: exitValue,
      exitPv: exitPv,
      holdPv: holdPv,
      holdNetOfDebt: holdPv - inp.mortgageBalance
    };
  }

  function line(k, v, cls) {
    return '<div class="result-line' + (cls ? ' ' + cls : '') + '">' +
      '<span class="k">' + k + '</span><span class="v">' + v + '</span></div>';
  }

  function render() {
    var inp = readInputs();
    var otherIncome = num('c_otherIncome');

    if (!inp.salePrice && !inp.annualNoi) {
      $('c_out').innerHTML =
        '<div class="notice notice--info" style="margin:0">' +
        '<strong>Enter at least a sale price or a year-one NOI to begin.</strong>' +
        'Nothing is pre-filled, because a default would be an assumption rather than a verified ' +
        'fact about this parcel. Inputs are never transmitted or stored.</div>';
      return;
    }

    var s = computeSale(inp, otherIncome);
    var h = computeHold(inp);

    var saleHtml =
      '<div class="card" style="margin:0">' +
      '<h3 style="margin-top:0">Path A — Sell now</h3>' +
      line('Gross sale price', money(inp.salePrice)) +
      line('Less selling costs (' + pct(inp.sellingCostPct) + ')', money(-s.selling)) +
      line('Net sale proceeds', money(s.netProceeds)) +
      line('Adjusted basis (basis − accumulated depreciation)', money(s.adjBasis)) +
      line('Realised gain', money(s.totalGain)) +
      '<hr class="rule" style="margin:.6rem 0">' +
      line('Unrecaptured §1250 gain @ ' + pct(RATE.unrecaptured1250), money(s.recap)) +
      line('Long-term capital gain', money(s.capGain)) +
      line('Federal LTCG @ ' + pct(s.ltcgRate), money(-s.fedCap)) +
      line('Federal §1250 recapture tax @ 25%', money(-s.fedRecap)) +
      line('Net investment income tax @ 3.8%', money(-s.niit)) +
      line('California income tax @ ' + pct(RATE.caTop), money(-s.ca)) +
      line('Total tax on sale', money(-s.totalTax), 'total') +
      '<hr class="rule" style="margin:.6rem 0">' +
      line('Mortgage / debt repaid', money(-inp.mortgageBalance)) +
      line('After-tax equity in hand', money(s.afterTaxProceeds), 'total') +
      '</div>';

    var holdRows = h.rows.map(function (row) {
      return line('Year ' + row.year + ' NOI', money(row.noi) + '  ·  PV ' + money(row.pv));
    }).join('');

    var holdHtml =
      '<div class="card" style="margin:0">' +
      '<h3 style="margin-top:0">Path B — Hold ' + inp.years + ' year' + (inp.years === 1 ? '' : 's') + ' and exit</h3>' +
      line('Year-one NOI', money(inp.annualNoi)) +
      line('NOI growth', pct(inp.noiGrowth)) +
      '<hr class="rule" style="margin:.6rem 0">' +
      holdRows +
      '<hr class="rule" style="margin:.6rem 0">' +
      line('Cumulative undiscounted NOI', money(h.cumNoi)) +
      line('Year-' + inp.years + ' NOI', money(h.exitNoi)) +
      line('Exit value @ ' + pct(inp.exitCap) + ' cap', money(h.exitValue)) +
      line('PV of exit value', money(h.exitPv)) +
      line('PV of all cash flows', money(h.holdPv), 'total') +
      line('Less debt', money(-inp.mortgageBalance)) +
      line('PV net of debt', money(h.holdNetOfDebt), 'total') +
      '<p class="small muted" style="margin:.6rem 0 0">This is a pre-tax present value. Tax on the ' +
      'exit sale is not deducted because the exit-year tax position depends on facts not entered here ' +
      '(depreciation taken during the hold, entity structure, future law). Compare it with the after-tax ' +
      'sale figure only after an adviser supplies those inputs.</p>' +
      '</div>';

    var diff = h.holdNetOfDebt - s.afterTaxProceeds;
    var verdict =
      '<div class="verdict">' +
      '<strong>Directional difference (pre-tax hold PV − after-tax sale proceeds)</strong>' +
      'Hold path is ' + money(Math.abs(diff)) + (diff >= 0 ? ' higher' : ' lower') +
      ' on these inputs over ' + inp.years + ' years. ' +
      '<em>This is not a recommendation.</em> The hold figure is pre-tax, the sale figure is ' +
      'after-tax, and the inputs are typed by you rather than verified for this parcel. ' +
      'Use it to see which variable dominates, then send the same inputs to a CPA for a filed position.' +
      '</div>';

    var sens =
      '<div class="card" style="grid-column:1/-1">' +
      '<h3 style="margin-top:0">Sensitivity — what actually moves the answer</h3>' +
      '<div class="table-scroll" style="margin:0"><table><thead><tr>' +
      '<th>Variable</th><th>Low case</th><th>Base case</th><th>High case</th>' +
      '</tr></thead><tbody>' +
      '<tr><td>Exit cap rate</td><td class="num">' + pct(Math.max(0.0001, inp.exitCap - 0.01)) +
      ' → ' + money(inp.exitCap > 0.01 ? h.exitNoi / (inp.exitCap - 0.01) : NaN) +
      '</td><td class="num">' + pct(inp.exitCap) + ' → ' + money(h.exitValue) +
      '</td><td class="num">' + pct(inp.exitCap + 0.01) + ' → ' + money(h.exitNoi / (inp.exitCap + 0.01)) +
      '</td></tr>' +
      '<tr><td>Discount rate</td><td class="num">' + pct(Math.max(0, inp.discountRate - 0.02)) +
      '</td><td class="num">' + pct(inp.discountRate) +
      '</td><td class="num">' + pct(inp.discountRate + 0.02) + '</td></tr>' +
      '<tr><td>NOI growth / yr</td><td class="num">' + pct(inp.noiGrowth - 0.01) +
      '</td><td class="num">' + pct(inp.noiGrowth) +
      '</td><td class="num">' + pct(inp.noiGrowth + 0.01) + '</td></tr>' +
      '<tr><td>Federal LTCG rate</td><td class="num">' + pct(RATE.fedLtcgLow) +
      '</td><td class="num">' + pct(s.ltcgRate) +
      '</td><td class="num">' + pct(RATE.fedLtcgHigh) + '</td></tr>' +
      '</tbody></table></div>' +
      '<p class="small muted" style="margin:.7rem 0 0">Each row moves one variable by the stated step ' +
      'and holds the rest fixed. The cap-rate row alone shows how much of the "sell versus hold" gap is ' +
      'a valuation opinion rather than a fact — which is why FLAG-U04 blocks a final commitment.</p>' +
      '</div>';

    $('c_out').innerHTML =
      '<div class="grid grid--2">' + saleHtml + holdHtml + '</div>' +
      verdict + sens;
  }

  document.addEventListener('DOMContentLoaded', function () {
    var form = $('c_form');
    if (!form) return;
    form.addEventListener('submit', function (e) { e.preventDefault(); render(); });
    // 'input' covers typing; 'reset' fires before the fields are cleared, so the
    // re-render below it happens via the follow-up input/change pass.
    form.addEventListener('input', render);
    form.addEventListener('reset', function () {
      // Clear the fields first, then render, so the sheet shows its empty state.
      setTimeout(render, 0);
    });
    render();
  });
})();
