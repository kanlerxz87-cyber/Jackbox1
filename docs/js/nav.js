(function () {
  const pages = [
    { group: "Overview", items: [
      { href: "index.html", label: "Dashboard" },
      { href: "decision-gate.html", label: "Decision gates" },
      { href: "questions.html", label: "Questions & gaps" },
      { href: "advisor-summary.html", label: "Advisor one-pager" }
    ]},
    { group: "Evidence", items: [
      { href: "trade-area.html", label: "Trade-area proxies" },
      { href: "tenant.html", label: "Tenant system" },
      { href: "hazards.html", label: "Hazard screening" },
      { href: "sources.html", label: "Sources" }
    ]},
    { group: "Private tools", items: [
      { href: "calculator.html", label: "Private calculator" },
      { href: "sell-vs-hold.html", label: "Sell vs hold" },
      { href: "after-tax.html", label: "After-tax module" }
    ]},
    { group: "Review", items: [
      { href: "flagged.html", label: "Flagged for review" },
      { href: "suggestions.html", label: "Suggestions" },
      { href: "methods.html", label: "Methods" },
      { href: "privacy.html", label: "Privacy" }
    ]}
  ];

  const here = (location.pathname.split("/").pop() || "index.html");
  const nav = document.getElementById("nav");
  if (!nav) return;
  nav.innerHTML = [
    '<p class="brand">Subject NNN workspace</p>',
    '<p class="brand-sub">Anonymous Central LA proxy · no owner identifiers</p>',
    pages.map(function (g) {
      return '<div class="group">' + g.group + "</div>" + g.items.map(function (p) {
        const active = p.href === here ? " active" : "";
        return '<a class="' + active.trim() + '" href="' + p.href + '">' + p.label + "</a>";
      }).join("");
    }).join("")
  ].join("");
})();
