/* Browser-only calculator. No fetch, no storage, no cookies. */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var ids = ['sale','basis','depr','mortgage','ula','citytx','broker','fedlt','niit','cainc','exch',
             'rent','esc','term','renew','hold','cap','disc','vac'];

  function n(id) { var v = parseFloat($(id).value); return isFinite(v) ? v : 0; }
  function money(x) {
    if (!isFinite(x)) x = 0;
    var s = Math.abs(Math.round(x)).toLocaleString('en-US');
    return (x < 0 ? '−$' : '$') + s;
  }
  function pct(x) { return (isFinite(x) ? (100 * x).toFixed(1) : '0.0') + '%'; }

  function calc() {
    var sale = n('sale'), basis = n('basis'), depr = n('depr'), mortgage = n('mortgage');
    var brokerPct = n('broker') / 100;
    var fedlt = parseFloat($('fedlt').value);
    var niitOn = $('niit').value === '1';
    var caRate = parseFloat($('cainc').value);
    var exchange = $('exch').value === '1';

    /* --- sale side ------------------------------------------------------- */
    var gain = Math.max(0, sale - basis);
    var recap = Math.min(gain, Math.max(0, depr));
    var ltgain = Math.max(0, gain - recap);

    var fedRecap = recap * 0.25;              /* IRS Topic 409: unrecaptured 1250 max 25% */
    var fedLt = ltgain * fedlt;               /* IRS Topic 409 brackets */
    var fed = fedRecap + fedLt;
    var niit = niitOn ? gain * 0.038 : 0;     /* IRS: 3.8% NIIT */
    var ca = gain * caRate;                   /* FTB 2025 schedules, flat at the top bracket */

    var county = sale * 0.0011;               /* RTC 11911(a): $0.55 per $500 = 0.11% */
    var city = $('citytx').value === '1' ? sale * 0.00055 : 0;   /* RTC 11911(b): half again */
    var ula = 0;
    if ($('ula').value === '1' && sale >= 5000000) {
      ula = sale >= 10000000 ? sale * 0.055 : sale * 0.04;       /* Measure ULA tiers */
    }
    var xfer = county + city + ula;
    var cost = sale * brokerPct;

    var taxTotal = exchange ? 0 : (fed + niit + ca);
    var net = sale - taxTotal - xfer - cost - mortgage;
    var leak = sale > 0 ? (sale - Math.max(0, net)) / sale : 0;

    $('o-gain').textContent = money(gain);
    $('o-recap').textContent = money(recap);
    $('o-fed').textContent = money(fed);
    $('o-niit').textContent = money(niit);
    $('o-ca').textContent = money(ca);
    $('o-xfer').textContent = money(xfer) + (ula > 0 ? '  (incl. ULA ' + money(ula) + ')' : '');
    $('o-cost').textContent = money(cost);
    $('o-net').textContent = money(net);
    $('o-leak').textContent = pct(leak) + (exchange ? '  (tax deferred)' : '');

    /* --- hold side ------------------------------------------------------- */
    var rent = n('rent'), esc = n('esc') / 100, term = Math.max(0, n('term'));
    var renew = Math.min(1, Math.max(0, n('renew') / 100));
    var holdYrs = Math.max(1, n('hold'));
    var cap = n('cap') / 100, disc = n('disc') / 100;
    var vacMonths = Math.max(0, n('vac'));

    var cf = 0, r = rent;
    for (var y = 0; y < holdYrs; y++) {
      /* rent continues while the lease runs; after expiry it continues only
         in proportion to the renewal probability, net of a vacancy gap */
      var factor = (y < term) ? 1 : renew;
      var gross = r * factor;
      if (y >= term && y < term + Math.ceil(vacMonths / 12)) gross = 0;
      cf += gross;
      r *= (1 + esc);
    }
    var exitRent = rent * Math.pow(1 + esc, holdYrs) * (holdYrs > term ? renew : 1);
    var exitVal = cap > 0 ? exitRent / cap : 0;
    var expected = cf + exitVal;
    var npv = 0;
    for (var k = 1; k <= holdYrs; k++) npv += (rent * Math.pow(1 + esc, k - 1) * (k <= term ? 1 : renew)) / Math.pow(1 + disc, k);
    npv += exitVal / Math.pow(1 + disc, holdYrs);

    $('o-holdcf').textContent = money(cf);
    $('o-exit').textContent = money(exitVal);
    $('o-exp').textContent = money(expected);
    $('o-npv').textContent = money(npv);

    /* break-even: the discount the sale must beat to be worth more than holding */
    var be = expected > 0 ? Math.max(0, (expected - Math.max(0, net)) / expected) : 0;
    $('o-be').textContent = pct(be) + ' of hold-case value';
  }

  var ready = false;
  ids.forEach(function (id) { var el = $(id); if (el) { el.addEventListener('input', function () { if (ready) calc(); }); el.addEventListener('change', function () { if (ready) calc(); }); } });
  if ($('sale')) { ready = true; calc(); }
})();
