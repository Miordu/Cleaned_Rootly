(function () {
  var root = document.documentElement;
  root.classList.add('js');

  // Footer year
  var year = document.getElementById('year');
  if (year) year.textContent = new Date().getFullYear();

  // Theme toggle: follows the system until the visitor picks one.
  var toggle = document.querySelector('.theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var current = root.getAttribute('data-theme') ||
        (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      var next = current === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('theme', next); } catch (e) {}
    });
  }

  // Credits filter
  var chips = document.querySelectorAll('.chip');
  var rows = document.querySelectorAll('.credits tbody tr');
  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      var filter = chip.getAttribute('data-filter');
      chips.forEach(function (c) {
        var on = c === chip;
        c.classList.toggle('is-active', on);
        c.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
      rows.forEach(function (row) {
        row.hidden = filter !== 'all' && row.getAttribute('data-kind') !== filter;
      });
    });
  });

  if (!('IntersectionObserver' in window)) return;

  // Reveal blocks as they scroll into view
  var targets = document.querySelectorAll(
    '.section__head, .lede, .act, .role, .project, .skills > div, .credits-wrap, .edu__list li, .certs, .contact > *'
  );
  var reveal = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-in');
        reveal.unobserve(entry.target);
      }
    });
  }, { rootMargin: '0px 0px -8% 0px' });
  targets.forEach(function (el) {
    el.classList.add('reveal');
    reveal.observe(el);
  });

  // Highlight the current section in the nav
  var links = {};
  document.querySelectorAll('.nav a').forEach(function (a) {
    links[a.getAttribute('href').slice(1)] = a;
  });
  var spy = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      Object.keys(links).forEach(function (id) {
        links[id].classList.toggle('is-current', id === entry.target.id);
      });
    });
  }, { rootMargin: '-45% 0px -50% 0px' });
  document.querySelectorAll('main section[id]').forEach(function (s) {
    if (links[s.id]) spy.observe(s);
  });
})();
