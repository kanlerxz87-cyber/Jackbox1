/* ==========================================================================
   calc.js — after-tax sell-versus-renew calculator.
   Runs entirely in the browser. No network calls, no storage, no analytics.

   Every rate applied here is listed with its official source on the page
   itself (Sell vs Renew > "Rates applied"). The arithmetic is deliberately
   simple and fully visible: if a step looks wrong, you can read it here.

   This tool computes. It does not advise. It will show you a number built on
   an assumption, and it will say so, because hiding the assumption is the
   thing that makes a spreadsheet dangerous.
   ========================================================================== */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var n = function (id) {
    var el = $(id);
    if (!el) return 0;
    var v = parseFloat(el.value);
    return isFinite(v) ? v : 0;
  };
  var money = function (v) {
    if (!isFinite(v)) return "—";
    var neg = v < 0;
    var s = Math.abs(Math.round(v)).toLocaleString("en-US");
    return (neg ? "−$" : "$") + s;
  };
  var pct = function (v) { return (isFinite(v) ? v.toFixed(2) : "—") + "%"; };

  function row(label, value, cls) {
    return '<tr class="' + (cls || "") + '"><td>' + label + "</td><td>" + value + "</td></tr>";
  }
  function sub(label, value) {
    return '<tr class="sub"><td>' + label + "</td><td>" + value + "</td></tr>";
  }

  function compute() {
    /* ---------------- sale case ---------------- */
    var price      = n("sale_price");
    var sellPct    = n("sell_costs_pct") / 100;
    var basis      = n("basis");
    var accumDep   = n("accum_dep");
    var fedRate    = n("fed_rate") / 100;
    var stateRate  = n("state_rate") / 100;
    var niitOn     = n("niit") === 1;
    var use1031    = n("use_1031") === 1;
    var capShockBp = n("cap_shock_bp");
    var repairPct  = n("repair_pct") / 100;
    var rentLostMo = n("rent_lost_months");

    /* ---------------- renewal / hold case ---------------- */
    var rent       = n("rent");
    var opex       = n("opex");
    var term       = n("term");
    var rentGrowth = n("rent_growth") / 100;
    var marketRent = n("market_rent");
    var disc       = n("disc") / 100;
    var cap        = n("cap") / 100;

    /* ---------------- stressors ---------------- */
    // Exit cap-rate shock reduces value. Only applied to the sale proceeds
    // that a stressed market would produce, and reported separately so the
    // reader can see the difference between the base case and the stress.
    var capShockPct = capShockBp / 10000;
    var stressedValue = (cap > 0) ? price * (cap / (cap + capShockPct)) : price;
    var repairShock = price * repairPct;
    var rentLost = (rent / 12) * rentLostMo;

    var sellCosts = price * sellPct;
    var netSaleBeforeShock = price - sellCosts;

    /* ---------------- gain and tax ---------------- */
    // Net amount realised after costs and after any stress deductions.
    // Unrecaptured s.1250 gain is the lesser of accumulated depreciation and
    // the total gain; it is taxed at up to 25% federally (IRS Topic 409).
    var netRealised = stressedValue - sellCosts - repairShock - rentLost;
    var totalGain = netRealised - basis;

    var out = [];

    out.push(row("<b>Sale case</b>", "", "total"));
    out.push(sub("Sale price (as entered)", money(price)));
    if (capShockBp !== 0) {
      out.push(sub("Stressed value at cap-rate shock of " + capShockBp + " bp", money(stressedValue)));
    }
    out.push(sub("Selling costs at " + pct(sellPct * 100), "−" + money(sellCosts)));
    if (repairShock > 0) out.push(sub("Repair shock at " + pct(repairPct * 100) + " of value", "−" + money(repairShock)));
    if (rentLost > 0) out.push(sub("Rent lost, " + rentLostMo + " month(s)", "−" + money(rentLost)));
    out.push(row("Net amount realised", money(netRealised), "total"));

    if (netRealised <= 0) {
      out.push(row("Adjusted basis", money(basis)));
      out.push(row("Gain / (loss)", money(totalGain)));
      out.push(row("After-tax net proceeds", money(netRealised), "total"));
      out.push(row("Tax on the sale", "$0 (no gain)", ""));
      render(out, {
        netAfterTax: netRealised,
        tax: 0,
        use1031: use1031,
        compare: null
      });
      return;
    }

    out.push(row("Adjusted basis", money(basis)));
    out.push(row("Gain before tax", money(totalGain), "total"));

    if (totalGain <= 0) {
      out.push(row("Taxable gain", "$0"));
      out.push(row("Federal tax", "$0"));
      out.push(row("California tax", "$0"));
      out.push(row("Net investment income tax", "$0"));
      out.push(row("<b>Total tax on the sale</b>", "<b>$0</b>", "total"));
      out.push(row("<b>After-tax net proceeds</b>", "<b>" + money(netRealised) + "</b>", "total"));
      render(out, { netAfterTax: netRealised, tax: 0, use1031: use1031, compare: null });
      return;
    }

    // Section 1250 recapture: the lesser of accumulated depreciation and the
    // total gain, taxed at 25% federal maximum. The remainder is long-term
    // capital gain at the selected federal rate.
    var recapture = Math.min(accumDep, totalGain);
    var ltGain = Math.max(0, totalGain - recapture);

    if (use1031) {
      out.push(sub("Section 1250 recapture recognised (25% max)", money(recapture)));
      out.push(sub("Long-term capital gain", money(ltGain)));
      out.push(row("Federal tax", "deferred under s.1031", ""));
      out.push(row("California tax", "deferred; FTB 3840 applies if replacement is out of state", ""));
      out.push(row("Net investment income tax", niitOn ? "not triggered on deferred gain" : "n/a", ""));
      out.push(row("<b>Total tax on the sale</b>", "<b>$0 recognised</b>", "total"));
      out.push(row("<b>After-tax net proceeds</b>", "<b>" + money(netRealised) + "</b>", "total"));
      out.push(sub("Note", "Deferral is not avoidance. The gain carries into the replacement property's basis."));
      render(out, { netAfterTax: netRealised, tax: 0, use1031: true, compare: null });
      return;
    }

    var fedTaxOnRecapture = recapture * 0.25;
    var fedTaxOnLt = ltGain * fedRate;
    var fedTax = fedTaxOnRecapture + fedTaxOnLt;
    // California: no preferential capital gains rate (FTB), so the whole gain
    // is taxed at the selected state marginal rate.
    var caTax = totalGain * stateRate;
    // NIIT: 3.8% on net investment income, which includes gain on investment
    // real estate, when modified AGI exceeds the thresholds (IRS NIIT Q&A).
    var niitTax = niitOn ? totalGain * 0.038 : 0;

    var totalTax = fedTax + caTax + niitTax;
    var netAfterTax = netRealised - totalTax;

    out.push(sub("Section 1250 recapture at 25% (max)", money(recapture) + " → " + money(fedTaxOnRecapture)));
    out.push(sub("Long-term capital gain at " + pct(fedRate * 100), money(ltGain) + " → " + money(fedTaxOnLt)));
    out.push(sub("California, ordinary rate " + pct(stateRate * 100), "→ " + money(caTax)));
    out.push(sub("Net investment income tax at 3.8%", niitOn ? "→ " + money(niitTax) : "not applied"));
    out.push(row("<b>Total tax on the sale</b>", "<b>" + money(totalTax) + "</b>", "total"));
    out.push(row("<b>After-tax net proceeds</b>", "<b>" + money(netAfterTax) + "</b>", "total"));

    /* ---------------- renewal case: present value ---------------- */
    // Present value of the net rent over the renewal term, with rent growing
    // at the assumed contract rate, plus the reversion valued at the assumed
    // cap rate on the final year's rent, discounted back.
    var years = Math.max(1, Math.round(term));
    var pv = 0;
    var nominalSum = 0;
    var r = rent;
    for (var y = 1; y <= years; y++) {
      r = rent * Math.pow(1 + rentGrowth, y - 1);
      var net = r - opex;
      nominalSum += net;
      pv += net / Math.pow(1 + disc, y);
    }
    var finalRent = r;
    var reversion = (cap > 0) ? finalRent / cap : 0;
    var pvReversion = reversion / Math.pow(1 + disc, years);
    var pvTotal = pv + pvReversion;

    out.push(row("<b>Renewal / hold case</b>", "", "total"));
    out.push(sub("Net rent over " + years + " years (nominal)", money(nominalSum)));
    out.push(sub("Present value of net rent at " + pct(disc * 100), money(pv)));
    out.push(sub("Rent in year " + years, money(finalRent)));
    out.push(sub("Reversion value at " + pct(cap * 100) + " cap", money(reversion)));
    out.push(sub("Present value of reversion", money(pvReversion)));
    out.push(row("<b>Present value of the renewal case</b>", "<b>" + money(pvTotal) + "</b>", "total"));

    if (marketRent > 0) {
      var gap = marketRent - rent;
      out.push(sub("Market rent entered", money(marketRent)));
      out.push(sub("Contract rent is " + (gap >= 0 ? "below" : "above") + " market by", money(Math.abs(gap)) + " per year"));
    }

    /* ---------------- the comparison itself ---------------- */
    out.push(row("<b>Comparison</b>", "", "total"));
    out.push(sub("After-tax cash if sold today", money(netAfterTax)));
    out.push(sub("Present value if renewed and held for " + years + " years", money(pvTotal)));
    var diff = pvTotal - netAfterTax;
    out.push(row("<b>Renewal value minus sale proceeds</b>", "<b>" + money(diff) + "</b>", "total"));

    render(out, {
      netAfterTax: netAfterTax,
      tax: totalTax,
      use1031: false,
      compare: { sell: netAfterTax, hold: pvTotal, diff: diff, years: years }
    });
  }

  function render(rows, ctx) {
    var body = $("results").querySelector("tbody");
    body.innerHTML = rows.join("");

    var v = $("verdict");
    var html = "";
    var warnings = [];

    // Zeros in the inputs mean the output is meaningless, and the tool says so.
    if (n("sale_price") <= 0) warnings.push("sale price is zero");
    if (n("basis") <= 0) warnings.push("adjusted basis is zero");
    if (n("rent") <= 0) warnings.push("current rent is zero");
    if (n("cap") <= 0) warnings.push("cap rate is zero");

    if (ctx.compare) {
      var d = ctx.compare;
      html += "<b>The two numbers are not the same kind of number.</b> ";
      html += "One is cash in hand after tax today. The other is the present value of an income stream you would " +
              "only realise by selling later at an assumed cap rate. Subtracting one from the other is a convenience, " +
              "not a like-for-like comparison. ";
      if (d.diff > 0) {
        html += "On the numbers entered, holding and renewing values the asset at " + money(d.diff) +
                " more than selling today.";
        v.className = "verdict good";
      } else {
        html += "On the numbers entered, selling today beats the modelled renewal case by " + money(Math.abs(d.diff)) + ".";
        v.className = "verdict bad";
      }
      html += " That conclusion is only as good as the cap rate, the discount rate and the rent you typed in.";
    } else if (ctx.use1031) {
      html += "<b>A deferral is not a gain that disappears.</b> A section 1031 exchange postpones recognition. The " +
              "deferred gain reduces the basis of the replacement property, so the tax arrives later. California also " +
              "requires FTB 3840 when California property is exchanged for replacement property outside California, " +
              "and California sources the gain to where the property is.";
      v.className = "verdict neutral";
    } else {
      html += "<b>No comparison can be made from these inputs.</b> Either there is no gain to tax, or the sale case " +
              "is worth less than its own costs. Check the sale price and the basis before reading anything into it.";
      v.className = "verdict neutral";
    }

    if (warnings.length) {
      html += '<br><br><b style="color:var(--stop)">Warning — ' + warnings.join(", ") +
              ".</b> The output below includes a number computed from a zero. A zero in this calculator means " +
              "'unknown', not 'nothing'. Replace it with a documented figure or treat the result as illustrative only.";
      v.className = "verdict bad";
    }

    html += '<br><br><span class="tiny">Nothing you typed has been sent anywhere. There is no network call in this ' +
            "page's script.</span>";
    v.innerHTML = html;
  }

  function init() {
    if (!$("results")) return;
    var form = $("calc-form");
    if (form) {
      form.addEventListener("input", compute);
      form.addEventListener("change", compute);
    }
    compute();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
