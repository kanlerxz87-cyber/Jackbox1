/* Navigation state + table filter. No network calls, no storage, no tracking. */
(function () {
  'use strict';

  // Mark the current page in the nav.
  var here = location.pathname.split('/').pop() || 'index.html';
  var links = document.querySelectorAll('.nav a');
  for (var i = 0; i < links.length; i++) {
    var href = links[i].getAttribute('href') || '';
    var target = href.split('/').pop();
    if (target === here) {
      links[i].setAttribute('aria-current', 'page');
    }
  }

  // Optional live filter for tables: add data-filterable to a .table-scroll
  // wrapper and give the page an <input data-filter-for="id">.
  var inputs = document.querySelectorAll('[data-filter-for]');
  for (var j = 0; j < inputs.length; j++) {
    (function (input) {
      var table = document.getElementById(input.getAttribute('data-filter-for'));
      if (!table) return;
      input.addEventListener('input', function () {
        var q = input.value.trim().toLowerCase();
        var rows = table.tBodies[0] ? table.tBodies[0].rows : [];
        for (var r = 0; r < rows.length; r++) {
          var text = rows[r].textContent.toLowerCase();
          rows[r].style.display = !q || text.indexOf(q) !== -1 ? '' : 'none';
        }
      });
    })(inputs[j]);
  }
})();
