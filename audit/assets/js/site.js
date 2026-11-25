
/* Independent verification desk — browser-only helpers. No network calls, no storage. */
(function () {
  'use strict';
  var tables = document.querySelectorAll('table');
  if (tables.length) {
    var bar = document.createElement('div');
    bar.className = 'filterbar';
    bar.innerHTML = '<input type="search" id="rowfilter" placeholder="Filter rows on this page…" aria-label="Filter table rows">' +
                    '<button type="button" id="toggleblank">Hide blank/unverified rows</button>' +
                    '<span class="muted" id="rowcount"></span>';
    var first = tables[0];
    first.parentNode.insertBefore(bar, first);
    var input = bar.querySelector('#rowfilter');
    var toggle = bar.querySelector('#toggleblank');
    var count = bar.querySelector('#rowcount');
    var hideBlank = false;
    function apply() {
      var q = (input.value || '').toLowerCase().trim();
      var shown = 0, total = 0;
      document.querySelectorAll('table tbody tr').forEach(function (tr) {
        total++;
        var match = !q || tr.textContent.toLowerCase().indexOf(q) !== -1;
        var skipBlank = hideBlank && tr.getAttribute('data-unverified') === '1';
        tr.style.display = (match && !skipBlank) ? '' : 'none';
        if (match && !skipBlank) shown++;
      });
      count.textContent = shown + ' of ' + total + ' rows shown';
    }
    input.addEventListener('input', apply);
    toggle.addEventListener('click', function () {
      hideBlank = !hideBlank;
      toggle.textContent = hideBlank ? 'Show blank/unverified rows' : 'Hide blank/unverified rows';
      apply();
    });
    apply();
  }
  // Suggestion review board — memory only, nothing is transmitted or stored.
  var memoButton = document.getElementById('makememo');
  if (memoButton) {
    var memo = document.getElementById('memo');
    var pathForm = document.getElementById('pathform');
    memoButton.addEventListener('click', function () {
      var picked = Array.prototype.slice.call(document.querySelectorAll('.sug-pick:checked')).map(function (c) { return c.value; });
      var path = pathForm.querySelector('input[name="path"]:checked');
      var names = {A:'Verification first (recommended process decision)', B:'Build the sale track first', C:'Build the renewal track first', D:'No site changes yet'};
      var lines = [
        'DECISION MEMO — anonymous, generated locally in this browser',
        'Session: S-62b1c0c2    Retrieved: 2026-11-25',
        'No personal information, no network calls, no persistence.',
        '',
        'Chosen path: ' + (path ? path.value + ' — ' + names[path.value] : 'none selected'),
        'Shortlisted suggestions: ' + (picked.length ? picked.join(', ') : 'none'),
        '',
        'Rule: no change is implemented until a reviewer approves this memo and the relevant decision gates close.',
        'This memo is advisory. It does not select a sale or renewal winner.'
      ];
      memo.textContent = lines.join('\n');
    });
    document.getElementById('clearmemo').addEventListener('click', function () {
      document.querySelectorAll('.sug-pick').forEach(function (c) { c.checked = false; });
      memo.textContent = 'No memo generated. Shortlist suggestions and choose a path above.';
    });
  }
})();
