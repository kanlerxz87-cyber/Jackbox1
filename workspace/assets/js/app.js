/* Minimal, dependency-free client behaviour. No network calls, no cookies, no storage. */
(function () {
  'use strict';

  /* ---- table filter: one search box + one status select per .filter block ---- */
  document.querySelectorAll('[data-filter]').forEach(function (bar) {
    var scope = document.querySelector(bar.getAttribute('data-filter'));
    if (!scope) return;
    var input = bar.querySelector('input[type=search]');
    var select = bar.querySelector('select');
    var rows = Array.prototype.slice.call(scope.querySelectorAll('tbody tr'));
    var counter = bar.querySelector('[data-count]');

    function apply() {
      var q = input ? input.value.trim().toLowerCase() : '';
      var s = select ? select.value : '';
      var shown = 0;
      rows.forEach(function (tr) {
        var text = tr.textContent.toLowerCase();
        var okText = !q || text.indexOf(q) !== -1;
        var okStatus = !s || tr.getAttribute('data-status') === s;
        var show = okText && okStatus;
        tr.hidden = !show;
        if (show) shown++;
      });
      if (counter) counter.textContent = shown + ' of ' + rows.length + ' rows';
    }
    if (input) input.addEventListener('input', apply);
    if (select) select.addEventListener('change', apply);
    apply();
  });

  /* ---- mark the current page in the nav ---- */
  var here = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('nav.site a').forEach(function (a) {
    var target = a.getAttribute('href');
    if (target === here) a.setAttribute('aria-current', 'page');
  });

  /* ---- suggestion picker: builds a plain-text shortlist the reader can copy ---- */
  var picker = document.getElementById('suggestion-picker');
  if (picker) {
    var out = document.getElementById('suggestion-out');
    var copy = document.getElementById('suggestion-copy');
    var update = function () {
      var chosen = Array.prototype.slice.call(picker.querySelectorAll('input[type=checkbox]:checked'))
        .map(function (i) { return '• ' + i.getAttribute('data-title'); });
      out.value = chosen.length
        ? 'Shortlist (' + chosen.length + ') — ' + new Date().toISOString().slice(0, 10) + '\n' + chosen.join('\n')
        : 'Nothing selected yet. Tick the options you want implemented first.';
    };
    picker.addEventListener('change', update);
    update();
    if (copy) {
      copy.addEventListener('click', function () {
        out.select();
        if (navigator.clipboard) { navigator.clipboard.writeText(out.value); }
        else { document.execCommand('copy'); }
        copy.textContent = 'Copied';
        setTimeout(function () { copy.textContent = 'Copy shortlist'; }, 1600);
      });
    }
  }
})();
