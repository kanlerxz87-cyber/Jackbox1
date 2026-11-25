(function () {
  const KEY = "nnn-private-calc-v1";
  const form = document.getElementById("calc-form");
  const out = document.getElementById("calc-out");
  if (!form || !out) return;

  const fields = [
    "salePrice", "sellingCostsPct", "costBasis", "accumDep",
    "filing", "niitApplies", "caRatePct", "do1031", "boot",
    "noi", "holdYears", "rentGrowthPct", "discountPct",
    "vacancyMonths", "capexAnnual", "renewalRent", "quoteCapPct", "taxableIncome"
  ];

  function num(id) {
    const el = document.getElementById(id);
    if (!el || el.value === "") return null;
    const n = Number(el.value);
    return Number.isFinite(n) ? n : null;
  }

  function money(n) {
    if (n === null || !Number.isFinite(n)) return "—";
    return n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
  }

  function load() {
    try {
      const raw = localStorage.getItem(KEY);
      if (!raw) return;
      const data = JSON.parse(raw);
      fields.forEach(function (id) {
        if (data[id] !== undefined && document.getElementById(id)) {
          document.getElementById(id).value = data[id];
        }
      });
    } catch (e) { /* ignore corrupt local data */ }
  }

  function save() {
    const data = {};
    fields.forEach(function (id) {
      const el = document.getElementById(id);
      if (el) data[id] = el.value;
    });
    localStorage.setItem(KEY, JSON.stringify(data));
  }

  function federalLtcgRate(taxableProxy, filing) {
    // IRS Topic 409 for 2025. Owner taxable income is an input proxy, not computed AGI.
    const t = taxableProxy;
    if (t === null) return null;
    if (filing === "single") {
      if (t <= 48350) return 0;
      if (t <= 533400) return 0.15;
      return 0.20;
    }
    if (filing === "mfs") {
      if (t <= 48350) return 0;
      if (t <= 300000) return 0.15;
      return 0.20;
    }
    if (t <= 96700) return 0;
    if (t <= 600050) return 0.15;
    return 0.20;
  }

  function compute() {
    save();
    const salePrice = num("salePrice");
    const sellingCostsPct = num("sellingCostsPct");
    const costBasis = num("costBasis");
    const accumDep = num("accumDep");
    const filing = document.getElementById("filing").value;
    const niitApplies = document.getElementById("niitApplies").value === "yes";
    const caRatePct = num("caRatePct");
    const do1031 = document.getElementById("do1031").value === "yes";
    const boot = num("boot") || 0;
    const taxableIncome = num("taxableIncome");
    const noi = num("noi");
    const holdYears = num("holdYears");
    const rentGrowthPct = num("rentGrowthPct");
    const discountPct = num("discountPct");
    const vacancyMonths = num("vacancyMonths") || 0;
    const capexAnnual = num("capexAnnual") || 0;
    const renewalRent = num("renewalRent");
    const quoteCapPct = num("quoteCapPct");

    const missingCore = [];
    if (salePrice === null) missingCore.push("sale price");
    if (sellingCostsPct === null) missingCore.push("selling costs %");
    if (costBasis === null) missingCore.push("adjusted cost basis before current dep. recapture layering");
    if (accumDep === null) missingCore.push("accumulated depreciation");
    if (caRatePct === null) missingCore.push("California marginal rate applicable to the owner");
    if (taxableIncome === null) missingCore.push("taxable income (to pick the IRS 0/15/20% band)");

    const netSale = salePrice !== null && sellingCostsPct !== null ? salePrice * (1 - sellingCostsPct / 100) : null;
    const adjustedBasis = costBasis !== null && accumDep !== null ? costBasis - accumDep : null;
    const realizedGain = netSale !== null && adjustedBasis !== null ? netSale - adjustedBasis : null;

    const unrecaptured1250 = realizedGain !== null && accumDep !== null
      ? Math.max(0, Math.min(accumDep, Math.max(0, realizedGain)))
      : null;
    const residualLtcg = realizedGain !== null && unrecaptured1250 !== null
      ? Math.max(0, realizedGain - unrecaptured1250)
      : null;

    const ltcgRate = federalLtcgRate(taxableIncome, filing);
    const recaptureRate = 0.25;
    const niitRate = niitApplies ? 0.038 : 0;
    const caRate = caRatePct !== null ? caRatePct / 100 : null;

    let recognizedGain = realizedGain;
    let recognized1250 = unrecaptured1250;
    let recognizedLtcg = residualLtcg;
    let exchangeNote = "Taxable sale path (no §1031).";
    if (do1031) {
      exchangeNote = "§1031 path: gain is recognized only to the extent of boot (cash or other non-like-kind property), per IRS like-kind exchange tips. This model does not compute debt-relief boot.";
      const rec = Math.max(0, boot);
      recognizedGain = rec;
      recognized1250 = unrecaptured1250 !== null ? Math.min(unrecaptured1250, rec) : null;
      recognizedLtcg = recognized1250 !== null ? Math.max(0, rec - recognized1250) : null;
    }

    let fedTax = null;
    let caTax = null;
    let niitTax = null;
    let totalTax = null;
    if (recognized1250 !== null && recognizedLtcg !== null && ltcgRate !== null && caRate !== null) {
      fedTax = recognized1250 * recaptureRate + recognizedLtcg * ltcgRate;
      caTax = recognizedGain * caRate;
      niitTax = (recognized1250 + recognizedLtcg) * niitRate;
      totalTax = fedTax + caTax + niitTax;
    }

    const afterTaxProceeds = netSale !== null && totalTax !== null ? netSale - totalTax : null;

    let holdNpv = null;
    let holdNote = "Hold NPV not computed — need current NOI, hold years, and discount rate.";
    if (noi !== null && holdYears !== null && discountPct !== null) {
      const g = (rentGrowthPct || 0) / 100;
      const r = discountPct / 100;
      let npv = 0;
      for (let t = 1; t <= holdYears; t++) {
        let cf = noi * Math.pow(1 + g, t - 1) - capexAnnual;
        if (t === 1) cf -= noi * (vacancyMonths / 12);
        npv += cf / Math.pow(1 + r, t);
      }
      holdNpv = npv;
      holdNote = "Illustrative levered-off cash NOI path only. No terminal value is included because no verified cap rate or residual rent exists. This is not a decision.";
    }

    const impliedValueFromQuote = noi !== null && quoteCapPct !== null && quoteCapPct !== 0
      ? noi / (quoteCapPct / 100)
      : null;

    const renewalGap = renewalRent !== null && noi !== null ? renewalRent - noi : null;

    const winner = "No winner selected. Verified private inputs are incomplete.";

    out.innerHTML = [
      '<div class="callout warn"><strong>Local only.</strong> Figures never leave this browser. They are not tax advice. IRS Topic 409, NIIT FAQ, and FTB rates are rules; your return may differ.</div>',
      '<div class="grid">',
      card("Net sale proceeds (pre-tax)", money(netSale), "Observation if sale price and costs are from a written quote; otherwise assumption."),
      card("Realized gain", money(realizedGain), "Net sale minus (cost basis − accumulated depreciation)."),
      card("Unrecaptured §1250 layer", money(recognized1250), "Capped at 25% federal (IRS Topic 409)."),
      card("Residual LTCG layer", money(recognizedLtcg), "0% / 15% / 20% band from IRS Topic 409 using the taxable-income input."),
      card("Estimated federal + NIIT + CA tax", money(totalTax), exchangeNote),
      card("After-tax sale proceeds", money(afterTaxProceeds), "One number to compare with a hold case — still not a recommendation."),
      card("Hold cash-flow NPV (no exit)", money(holdNpv), holdNote),
      card("Value implied by quoted cap rate × NOI", money(impliedValueFromQuote), "Uses only a user-entered written quote. Blank quote → blank value."),
      card("Renewal NOI vs current NOI", money(renewalGap), "Requires a negotiated renewal rent. Do not invent it."),
      card("Decision", winner, "W-02 / W-03 gate: do not select sell or renew until the lease abstract, quotes, and tax inputs are verified."),
      "</div>",
      missingCore.length ? '<p class="lede">Still blank until filled: ' + missingCore.join("; ") + ".</p>" : "",
      '<p class="lede">Black-swan vacancy is modeled only as extra empty months on year-1 NOI. It is not an insurance, seismic, or flood loss model.</p>'
    ].join("");
  }

  function card(k, v, s) {
    return '<div class="card output"><div class="k">' + k + '</div><div class="v">' + v + '</div><div class="s">' + s + "</div></div>";
  }

  document.getElementById("wipe").addEventListener("click", function () {
    localStorage.removeItem(KEY);
    form.reset();
    out.innerHTML = '<p class="lede">Private inputs cleared from this browser.</p>';
  });

  form.addEventListener("input", compute);
  form.addEventListener("change", compute);
  load();
  compute();
})();
