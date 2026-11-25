function statusBadge(status) {
  const map = {
    verified: ["verified", "Verified"],
    proxy: ["proxy", "City/county proxy"],
    unverified: ["unverified", "Unverified"],
    blank: ["blank", "Blank — not confirmed"],
    client: ["client", "Client-stated"],
    regional: ["proxy", "Regional only"]
  };
  const pair = map[status] || ["blank", status || "Unverified"];
  return '<span class="badge ' + pair[0] + '">' + pair[1] + "</span>";
}

function renderTable(el, rows, cols) {
  if (!el) return;
  const head = "<thead><tr>" + cols.map(function (c) { return "<th>" + c.label + "</th>"; }).join("") + "</tr></thead>";
  const body = "<tbody>" + rows.map(function (row) {
    return "<tr>" + cols.map(function (c) {
      let v = row[c.key];
      if (c.key === "status") return "<td>" + statusBadge(row.status) + "</td>";
      if (c.key === "source") {
        if (row.source_url) {
          return '<td><a href="' + row.source_url + '" target="_blank" rel="noopener">' + (row.source_name || "Source") + "</a></td>";
        }
        return "<td class=\"blank\">No official source linked</td>";
      }
      if (v === null || v === undefined || v === "") {
        return '<td class="blank">—</td>';
      }
      return "<td>" + v + "</td>";
    }).join("") + "</tr>";
  }).join("") + "</tbody>";
  el.innerHTML = '<div class="table-wrap"><table class="data">' + head + body + "</table></div>";
}

const COLS = [
  { key: "metric", label: "Metric" },
  { key: "geography", label: "Geography" },
  { key: "period", label: "Period" },
  { key: "value", label: "Value" },
  { key: "status", label: "Status" },
  { key: "source", label: "Official source" },
  { key: "notes", label: "Notes" }
];
