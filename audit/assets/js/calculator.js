
/* Browser-only after-tax sell-versus-hold comparison.
   No network calls, no persistence. Inputs are adviser-entered assumptions.
   Verified tax rules are described on the page with official source links. */
(function () {
  'use strict';
  var form = document.getElementById('calc');
  if (!form) return;
  var out = document.getElementById('calcresult');
  var money = function (v) {
    return new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD', maximumFractionDigits: 0}).format(v);
  };
  function val(name) {
    var el = form.elements[name];
    if (!el || el.value === '' || el.value === null) return null;
    var n = Number(el.value);
    return Number.isFinite(n) ? n : null;
  }
  function pct(name) { var v = val(name); return v === null ? null : v / 100; }
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var required = ['price','costs','debt','basis','depr','fed','ca','rent','years','discount','cap'];
    var missing = required.filter(function (n) { return val(n) === null; });
    if (missing.length) {
      out.textContent = 'No comparison calculated. Fill every required adviser input first (missing: ' + missing.join(', ') + '). These are assumptions, not verified values.';
      return;
    }
    var price = val('price'), costs = val('costs'), debt = val('debt'), basis = val('basis');
    var depr = Math.max(0, val('depr')), fed = pct('fed'), ca = pct('ca');
    var rent = val('rent'), years = val('years'), discount = pct('discount'), cap = pct('cap');
    var lostMonths = val('lostmonths') || 0, repairs = val('repairs') || 0, haircut = pct('haircut') || 0;
    if (cap <= 0 || years <= 0 || discount < 0) {
      out.textContent = 'Check the cap rate, remaining years and discount rate inputs. No comparison calculated.';
      return;
    }
    var gain = Math.max(0, price - costs - basis);
    var unrecaptured = Math.min(depr, gain);
    var remainder = Math.max(0, gain - unrecaptured);
    var federalTax = remainder * fed + unrecaptured * 0.25;
    var caTax = gain * ca;
    var niit = form.elements['niit'].checked ? gain * 0.038 : 0;
    var saleNet = price - costs - debt - federalTax - caTax - niit;
    var d = 1 + discount;
    var pvRent = 0;
    for (var y = 1; y <= Math.floor(years); y++) pvRent += rent / Math.pow(d, y);
    var exitValue = rent / cap;
    var pvExit = exitValue / Math.pow(d, years);
    var holdPV = pvRent + pvExit;
    var stressed = holdPV - (rent * lostMonths / 12) - repairs - (exitValue * haircut / Math.pow(d, years));
    var lines = [
      'ILLUSTRATIVE RESULT — all amounts depend on adviser-entered assumptions, not verified property values.',
      '',
      'Sale case',
      '  Gain subject to tax:                 ' + money(gain),
      '  Unrecaptured §1250 portion (25%):   ' + money(unrecaptured),
      '  Federal tax (entered rate + 25%):  ' + money(federalTax),
      '  California tax (entered rate):     ' + money(caTax),
      '  NIIT (3.8% if selected):           ' + money(niit),
      '  AFTER-TAX SALE NET PROCEEDS:       ' + money(saleNet),
      '',
      'Hold case (same valuation date)',
      '  PV of net rent over ' + years + ' years:      ' + money(pvRent),
      '  PV of exit value at entered cap:    ' + money(pvExit),
      '  HOLD-CASE PRESENT VALUE:           ' + money(holdPV),
      '  Stressed hold value (joint):       ' + money(stressed),
      '',
      'COMPARISON NUMBER (sale − hold):     ' + money(saleNet - holdPV),
      'Sale − stressed hold:               ' + money(saleNet - stressed),
      '',
      'A positive number is not a recommendation. Verified lease, tax, hazard and quote inputs are still missing.',
      'Simplifications and official sources are listed on this page. Nothing was transmitted or stored.'
    ];
    out.textContent = lines.join('\n');
  });
  form.addEventListener('reset', function () {
    out.textContent = 'No comparison calculated — verified inputs are missing. Every field above is an assumption until an adviser verifies it privately.';
  });
  var p = document.getElementById('printcalc');
  if (p) p.addEventListener('click', function () { window.print(); });
})();
