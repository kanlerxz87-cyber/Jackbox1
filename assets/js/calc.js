/* =====================================================================
   Private sell-versus-hold calculator.

   PRIVACY CONTRACT — enforced by the design, not just by policy:
     • no fetch / XMLHttpRequest / sendBeacon
     • no localStorage / sessionStorage / IndexedDB / cookies
     • no third-party scripts, no analytics, no fonts
     • nothing leaves this tab; reloading the page discards everything

   Every tax rate and threshold below is sourced from an official page and is
   cited in data/valuation.json (TX-01 .. TX-10): 2026 Federal LTCG brackets
   from IRS Rev. Proc. 2025-32 (S-032), 2025 Federal LTCG from IRS Topic 409
   (S-013), and 2026 California PIT brackets + 1% MHSA surcharge from FTB
   October 2026 Tax News (S-033) and FTB Form 5805F (S-034). The reader may
   also override with a custom California marginal rate.
   ===================================================================== */
(function () {
  'use strict';

  var $ = function (id) { return document.getElementById(id); };
  var num = function (id) {
    var el = $(id); if (!el) return NaN;
    var v = parseFloat(el.value);
    return isFinite(v) ? v : NaN;
  };
  var money = function (n) {
    if (!isFinite(n)) return '—';
    var s = Math.abs(Math.round(n)).toLocaleString('en-US');
    return (n < 0 ? '−$' : '$') + s;
  };
  var pct = function (n, d) { return isFinite(n) ? n.toFixed(d == null ? 2 : d) + '%' : '—'; };

  /* --- Federal long-term capital gain brackets -------------------------- */
  /* 2026: IRS Rev. Proc. 2025-32 (S-032); 2025: IRS Topic 409 (S-013)     */
  var LTCG_BY_YEAR = {
    '2026': {
      single: { b1: 49450, b2: 545500 },
      mfs: { b1: 49450, b2: 306850 },
      mfj: { b1: 98900, b2: 613700 },
      hoh: { b1: 66200, b2: 579600 }
    },
    '2025': {
      single: { b1: 48350, b2: 533400 },
      mfs: { b1: 48350, b2: 300000 },
      mfj: { b1: 96700, b2: 600050 },
      hoh: { b1: 64750, b2: 566700 }
    }
  };
  /* --- 2026 California PIT brackets (FTB Oct 2026 Tax News, S-033) ----- */
  /* Plus 1% Mental Health Services Act tax > $1,000,000 (FTB 5805F, S-034)*/
  var CA_2026_SCHEDULES = {
    single: [
      [0, 11456, 0.01], [11456, 27157, 0.02], [27157, 42861, 0.04],
      [42861, 59498, 0.06], [59498, 75197, 0.08], [75197, 384109, 0.093],
      [384109, 460927, 0.103], [460927, 768213, 0.113], [768213, Infinity, 0.123]
    ],
    mfs: [
      [0, 11456, 0.01], [11456, 27157, 0.02], [27157, 42861, 0.04],
      [42861, 59498, 0.06], [59498, 75197, 0.08], [75197, 384109, 0.093],
      [384109, 460927, 0.103], [460927, 768213, 0.113], [768213, Infinity, 0.123]
    ],
    mfj: [
      [0, 22912, 0.01], [22912, 54314, 0.02], [54314, 85722, 0.04],
      [85722, 118996, 0.06], [118996, 150394, 0.08], [150394, 768218, 0.093],
      [768218, 921854, 0.103], [921854, 1536426, 0.113], [1536426, Infinity, 0.123]
    ],
    hoh: [
      [0, 22927, 0.01], [22927, 54316, 0.02], [54316, 70018, 0.04],
      [70018, 86654, 0.06], [86654, 102356, 0.08], [102356, 522385, 0.093],
      [522385, 626864, 0.103], [626864, 1044771, 0.113], [1044771, Infinity, 0.123]
    ]
  };
  /* --- NIIT thresholds (IRS Topic 559) ---------------------------------- */
  var NIIT_THRESHOLD = { single: 200000, hoh: 200000, mfj: 250000, mfs: 125000 };
  var NIIT_RATE = 0.038;
  var RECAPTURE_RATE = 0.25; /* unrecaptured s.1250 ceiling, IRS Topic 409 */

  /* Tax on a long-term gain, given other ordinary taxable income.
     Simplified progressive application: the gain stacks on top of other
     income and is taxed in slices at 0/15/20%. Deliberately does not model
     deductions, credits or state apportionment. */
  function federalLTCG(gain, otherIncome, filing, taxYear) {
    if (!(gain > 0)) return 0;
    var table = LTCG_BY_YEAR[taxYear] || LTCG_BY_YEAR['2026'];
    var b = table[filing] || table.mfj;
    var start = otherIncome;
    var end = otherIncome + gain;
    var tax = 0;
    var slices = [
      [0, b.b1, 0.00],
      [b.b1, b.b2, 0.15],
      [b.b2, Infinity, 0.20]
    ];
    for (var i = 0; i < slices.length; i++) {
      var lo = Math.max(start, slices[i][0]);
      var hi = Math.min(end, slices[i][1]);
      if (hi > lo) tax += (hi - lo) * slices[i][2];
    }
    return tax;
  }

  function californiaProgressiveTax(gain, otherIncome, filing) {
    if (!(gain > 0)) return 0;
    var brackets = CA_2026_SCHEDULES[filing] || CA_2026_SCHEDULES.mfj;
    var start = Math.max(0, otherIncome);
    var end = start + gain;
    var tax = 0;
    for (var i = 0; i < brackets.length; i++) {
      var lo = Math.max(start, brackets[i][0]);
      var hi = Math.min(end, brackets[i][1]);
      if (hi > lo) tax += (hi - lo) * brackets[i][2];
    }
    var mhsaStart = Math.max(start, 1000000);
    if (end > mhsaStart) tax += (end - mhsaStart) * 0.01;
    return tax;
  }

  function calc() {
    var warnings = [];

    var price = num('c_price');
    var sellCostPct = num('c_sellcost');
    var basis = num('c_basis');
    var deprec = num('c_deprec');
    var mortgage = num('c_mortgage');
    var filing = ($('c_filing') || {}).value || 'mfj';
    var taxYear = ($('c_taxyear') || {}).value || '2026';
    var otherIncome = num('c_income'); if (!isFinite(otherIncome)) otherIncome = 0;
    var caMode = ($('c_camode') || {}).value || 'brackets_2026';
    var caRate = num('c_ca'); if (!isFinite(caRate)) caRate = 0;
    var reinvest = ($('c_reinvest') || {}).value === 'yes';

    var rent = num('c_rent');
    var opex = num('c_opex'); if (!isFinite(opex)) opex = 0;
    var ins = num('c_ins');
    var propTax = num('c_tax');
    var esc = num('c_esc'); if (!isFinite(esc)) esc = 0;
    var years = num('c_years'); if (!isFinite(years)) years = 5;
    var disc = num('c_disc');
    var capOut = num('c_cap_out');
    var vacMonths = num('c_vac'); if (!isFinite(vacMonths)) vacMonths = 0;
    var capex = num('c_capex'); if (!isFinite(capex)) capex = 0;

    /* ---- SALE SIDE ---- */
    var canSell = isFinite(price) && price > 0;
    var sellCost = canSell && isFinite(sellCostPct) ? price * sellCostPct / 100 : 0;
    var netBeforeDebt = canSell ? price - sellCost : NaN;
    var netProceeds = canSell ? netBeforeDebt - (isFinite(mortgage) ? mortgage : 0) : NaN;

    var gain = (canSell && isFinite(basis)) ? (price - sellCost - basis) : NaN;
    var afterTaxProceeds = NaN, fedTax = NaN, caTax = NaN, niit = NaN, recapture = NaN, ordGain = NaN;

    if (isFinite(gain)) {
      if (gain <= 0) {
        fedTax = 0; caTax = 0; niit = 0; recapture = 0; ordGain = 0;
        afterTaxProceeds = netProceeds;
        warnings.push(['info', 'Loss position',
          'The sale produces no taxable gain on these inputs. Note that a capital loss on business real property is generally deductible, ' +
          'but the treatment depends on how the property is held and whether depreciation taken exceeds original basis. Confirm with a CPA.']);
      } else {
        /* Split the gain into the recapture slice and the remaining gain.
           Recapture cannot exceed gain, nor exceed depreciation actually taken. */
        var dep = isFinite(deprec) && deprec > 0 ? deprec : 0;
        if (!isFinite(deprec)) {
          warnings.push(['bad', 'Depreciation not supplied',
            'Without accumulated depreciation the 25% recapture slice is set to zero, which UNDERSTATES tax. ' +
            'Supply it from the depreciation schedule before relying on this number.']);
        }
        recapture = Math.min(dep, gain);
        ordGain = gain - recapture;

        if (reinvest) {
          /* s.1031: gain deferred, not forgiven. Tax on recognised boot only,
             which we assume is zero. State that assumption loudly. */
          fedTax = 0; caTax = 0; niit = 0;
          afterTaxProceeds = netProceeds;
          warnings.push(['warn', '§1031 deferral modelled as full deferral',
            'This assumes a qualifying like-kind replacement is actually completed within 45 days of identification and 180 days of closing ' +
            '(IRS FS-2008-18). Deferral is not forgiveness: the deferred gain carries into the replacement property\'s basis. ' +
            'If the exchange fails, the full tax below applies in the year of sale.']);
        } else {
          var taxRecap = recapture * RECAPTURE_RATE;
          var taxRest = federalLTCG(ordGain, otherIncome, filing, taxYear);
          fedTax = taxRecap + taxRest;

          caTax = caMode === 'brackets_2026'
            ? californiaProgressiveTax(gain, otherIncome, filing)
            : gain * caRate / 100;

          var magi = otherIncome + gain;
          var over = magi - (NIIT_THRESHOLD[filing] || 200000);
          var nii = Math.max(0, gain);
          niit = Math.max(0, Math.min(nii, over)) * NIIT_RATE;

          afterTaxProceeds = netProceeds - fedTax - caTax - niit;
        }
      }
    } else {
      warnings.push(['bad', 'Adjusted basis not supplied',
        'No after-tax figure can be produced without adjusted basis. Enter it from the depreciation schedule — ' +
        'adjusted basis is cost plus improvements less depreciation allowed or allowable (IRS Publication 946).']);
    }

    /* ---- HOLD SIDE ---- */
    var canHold = isFinite(rent) && rent > 0 && isFinite(disc) && isFinite(capOut);
    var rows = [];
    var npv = 0, pvCFs = 0, totalCF = 0, noiYear1 = NaN, terminalValue = NaN, pvTerminal = 0;

    if (isFinite(rent) && rent > 0) {
      var noIns = !isFinite(ins);
      var noTax = !isFinite(propTax);
      if (noIns) warnings.push(['bad', 'Insurance missing',
        'Insurance is a top-three expense line for a California asset after the 2025 fire market repriced. ' +
        'The hold value below overstates true NOI by the whole premium.']);
      if (noTax) warnings.push(['warn', 'Property tax missing',
        'Property tax is the largest fixed expense in a triple-net hold. Enter it, ideally after any decline-in-value reduction.']);

      noiYear1 = rent - opex - (noIns ? 0 : ins) - (noTax ? 0 : propTax);

      for (var y = 1; y <= years; y++) {
        var yearRent = rent * Math.pow(1 + esc / 100, y - 1);
        var noi = yearRent - opex - (noIns ? 0 : ins) - (noTax ? 0 : propTax);
        var cf = noi - (y === 1 ? capex : 0);
        totalCF += cf;
        rows.push({ y: y, rent: yearRent, noi: noi, cf: cf });
      }

      /* Post-expiry vacancy: rent is lost for vacMonths, but the owner still
         carries non-recoverable expenses and property tax. */
      if (vacMonths > 0) {
        var vacCost = (opex + (noIns ? 0 : ins) + (noTax ? 0 : propTax)) * (vacMonths / 12);
        totalCF -= vacCost;
        rows.push({ y: years + 1, rent: 0, noi: -vacCost, cf: -vacCost, vac: true });
      }

      /* Discount the contract-period cash flows at the reader's rate. */
      if (isFinite(disc)) {
        var r = disc / 100;
        for (var i = 0; i < rows.length; i++) {
          var t = rows[i].y;
          rows[i].df = 1 / Math.pow(1 + r, t);
          rows[i].pv = rows[i].cf * rows[i].df;
          npv += rows[i].pv; pvCFs += rows[i].pv;
        }
        /* Terminal value requires a quoted exit cap rate. */
        if (isFinite(capOut) && capOut > 0) {
          var exitNOI = rent * Math.pow(1 + esc / 100, years) - opex - (noIns ? 0 : ins) - (noTax ? 0 : propTax);
          terminalValue = exitNOI / (capOut / 100);
          pvTerminal = terminalValue / Math.pow(1 + r, years + (rows.some(function (x) { return x.vac; }) ? 1 : 0));
          npv += pvTerminal;
        } else {
          warnings.push(['warn', 'No terminal value',
            'Exit cap rate is blank, so the hold figure EXCLUDES the value of the property itself. It is only the discounted cash flow. ' +
            'Do not compare it with a sale price. Supply a quoted cap rate to make the comparison whole.']);
        }
      } else {
        warnings.push(['bad', 'No discount rate',
          'Present value cannot be computed without a discount rate. Enter at least the current 4.91% ten-year Treasury (2026-11-24) plus a property risk premium.']);
      }
    } else {
      warnings.push(['bad', 'Contract rent not supplied', 'The hold case cannot be built without annual base rent from the lease.']);
    }

    if (canSell && canHold) {
      warnings.push(['info', 'These are not yet comparable',
        'The sale side is a net-of-tax lump sum today. The hold side is a discounted cash flow whose terminal value depends on a cap rate you supply. ' +
        'Only compare the two once a real quoted cap rate is in the exit field and the discount rate is set at or above the cost of capital. ' +
        'No recommendation is implied by the ordering of these numbers.']);
    }

    render({ canSell, canHold, price, sellCost, netBeforeDebt, netProceeds, gain, recapture, ordGain,
      fedTax, caTax, niit, afterTaxProceeds, reinvest, noiYear1, totalCF, npv, pvCFs, terminalValue, pvTerminal,
      rows, years, warnings, esc, vacMonths });
  }

  function render(m) {
    var out = $('c_out'); if (!out) return;
    out.classList.remove('hidden');

    var kpis = [];
    if (m.canSell) {
      kpis.push(o('Gross sale price', money(m.price), 'before costs'));
      kpis.push(o('Selling costs', money(m.sellCost), 'commission, title, transfer tax'));
      kpis.push(o('Net before debt', money(m.netBeforeDebt), ''));
      kpis.push(o('Net cash to you', money(m.netProceeds), 'after mortgage payoff', ''));
      if (isFinite(m.gain)) {
        kpis.push(o('Taxable gain', money(m.gain), 'price − costs − adjusted basis'));
        if (!m.reinvest && m.gain > 0) {
          kpis.push(o('Federal tax', money(m.fedTax), '25% recapture slice + 0/15/20% on the rest', 'neg'));
          kpis.push(o('California tax', money(m.caTax), 'no preferential state rate', 'neg'));
          kpis.push(o('Net investment income tax', money(m.niit), '3.8% where MAGI exceeds the threshold', 'neg'));
        }
        kpis.push(o(m.reinvest ? 'Proceeds, gain deferred' : 'After-tax proceeds', money(m.afterTaxProceeds),
          m.reinvest ? '§1031 assumed to complete' : 'what actually reaches you', m.reinvest ? '' : (m.afterTaxProceeds < m.netProceeds ? 'neg' : 'pos')));
      }
    }
    if (m.canHold) {
      kpis.push(o('NOI, year 1', money(m.noiYear1), 'rent less unrecovered expenses', ''));
      kpis.push(o('Cumulative cash flow', money(m.totalCF), 'over the modelled period'));
      kpis.push(o('PV of contract cash flows', money(m.pvCFs), 'discounted at your rate, no terminal value'));
      if (isFinite(m.pvTerminal) && m.pvTerminal > 0) {
        kpis.push(o('PV of exit value', money(m.pvTerminal), 'NOI at exit ÷ your cap rate'));
        kpis.push(o('Total hold value (PV)', money(m.npv), 'cash flows + exit, both discounted'));
      }
    }

    var el = $('c_kpis');
    /* Only build with DOM text nodes via innerHTML of pre-escaped content:
       every value here is a number we formatted ourselves. */
    el.innerHTML = kpis.join('');

    var wb = $('c_warnbox');
    wb.innerHTML = m.warnings.map(function (w) {
      return '<div class="callout c-' + (w[0] === 'bad' ? 'bad' : w[0] === 'warn' ? 'warn' : 'info') + '">' +
        '<strong>' + esc(w[1]) + '</strong>' + esc(w[2]) + '</div>';
    }).join('');

    var tbl = '';
    if (m.rows && m.rows.length) {
      tbl = '<h3>Year-by-year hold cash flow</h3><div class="tbl-wrap"><table><thead><tr>' +
        '<th>Year</th><th class="num">Rent</th><th class="num">NOI</th><th class="num">Cash flow</th>' +
        '<th class="num">Discount factor</th><th class="num">Present value</th></tr></thead><tbody>' +
        m.rows.map(function (r) {
          return '<tr><td>' + (r.vac ? (m.years + 1) + ' <span class="b b-warn">vacancy</span>' : r.y) + '</td>' +
            '<td class="num">' + money(r.rent) + '</td>' +
            '<td class="num">' + money(r.noi) + '</td>' +
            '<td class="num">' + money(r.cf) + '</td>' +
            '<td class="num">' + (r.df ? r.df.toFixed(4) : '—') + '</td>' +
            '<td class="num">' + (r.pv ? money(r.pv) : '—') + '</td></tr>';
        }).join('') + '</tbody></table></div>' +
        '<p class="tbl-note">Rent escalates at ' + m.esc + '%/year. ' +
        (m.vacMonths > 0 ? 'Vacancy of ' + m.vacMonths + ' months is modelled after expiry, carrying unrecovered expenses but no rent.' : 'No post-expiry vacancy modelled.') +
        ' Terminal value is shown separately above and is never mixed into the cash-flow column.</p>';
    }
    $('c_table').innerHTML = tbl;
  }

  function o(label, value, note, cls) {
    return '<div class="o ' + (cls || '') + '"><div class="l">' + esc(label) + '</div>' +
      '<div class="v">' + esc(value) + '</div>' +
      (note ? '<div class="n">' + esc(note) + '</div>' : '') + '</div>';
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function clearAll() {
    ['c_price', 'c_cap_in', 'c_basis', 'c_deprec', 'c_rent', 'c_ins', 'c_tax', 'c_disc', 'c_cap_out']
      .forEach(function (id) { var e = $(id); if (e) e.value = ''; });
    ['c_sellcost', 'c_mortgage', 'c_income', 'c_ca', 'c_opex', 'c_esc', 'c_years', 'c_vac', 'c_capex']
      .forEach(function (id) {
        var e = $(id); if (!e) return;
        e.value = { c_sellcost: '4', c_mortgage: '0', c_income: '0', c_ca: '9.3', c_opex: '0', c_esc: '2', c_years: '5', c_vac: '12', c_capex: '0' }[id];
      });
    var ty = $('c_taxyear'); if (ty) ty.value = '2026';
    var cm = $('c_camode'); if (cm) cm.value = 'brackets_2026';
    var out = $('c_out'); if (out) out.classList.add('hidden');
  }

  document.addEventListener('DOMContentLoaded', function () {
    var run = $('c_run'), clr = $('c_clear');
    if (run) run.addEventListener('click', calc);
    if (clr) clr.addEventListener('click', clearAll);
  });
})();
