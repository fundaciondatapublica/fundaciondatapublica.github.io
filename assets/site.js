// Filtro de líneas de acción. Sin dependencias, sin rastreo.
(function () {
  var botones = document.querySelectorAll('[data-filtro]');
  var lineas = document.querySelectorAll('.linea[data-tipo]');
  botones.forEach(function (b) {
    b.addEventListener('click', function () {
      var f = b.getAttribute('data-filtro');
      botones.forEach(function (o) { o.setAttribute('aria-pressed', String(o === b)); });
      lineas.forEach(function (l) { l.hidden = f !== 'todas' && l.getAttribute('data-tipo') !== f; });
    });
  });
})();

// Suscripción al newsletter: guarda el correo en la base propia de la
// fundación sin salir de la página. Sin JavaScript, el formulario se envía igual.
(function () {
  document.querySelectorAll('form.suscribir').forEach(function (form) {
    var aviso = document.createElement('p');
    aviso.className = 'nota aviso';
    aviso.setAttribute('role', 'status');
    form.insertAdjacentElement('afterend', aviso);

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var boton = form.querySelector('button');
      boton.disabled = true;
      aviso.textContent = 'Enviando…';
      fetch(form.action, { method: 'POST', body: new FormData(form), headers: { 'X-Requested-With': 'fetch' } })
        .then(function (r) {
          if (r.ok) {
            form.hidden = true;
            aviso.textContent = '¡Listo, quedaste inscrito! Te escribiremos a ' + form.email.value + '.';
          } else {
            return r.text().then(function (t) {
              aviso.textContent = r.status === 400 && t ? t : 'No pudimos guardar tu correo. Intenta de nuevo en un rato.';
            });
          }
        })
        .catch(function () { aviso.textContent = 'No pudimos guardar tu correo. Intenta de nuevo en un rato.'; })
        .then(function () { boton.disabled = false; });
    });
  });
})();

// Menú de celular: se cierra al elegir una sección o al tocar fuera.
(function () {
  var menu = document.querySelector('details.menu');
  if (!menu) return;
  menu.querySelectorAll('a').forEach(function (a) {
    a.addEventListener('click', function () { menu.removeAttribute('open'); });
  });
  document.addEventListener('click', function (e) {
    if (menu.open && !menu.contains(e.target)) menu.removeAttribute('open');
  });
})();

// Atajos para celulares: aparece al bajar, abre el índice y marca la sección actual.
(function () {
  var nav = document.querySelector('.atajos');
  if (!nav) return;
  var boton = nav.querySelector('.atajos-boton');
  var panel = nav.querySelector('.atajos-panel');
  var enlaces = panel.querySelectorAll('ol a');

  function cerrar() { panel.hidden = true; boton.setAttribute('aria-expanded', 'false'); }
  boton.addEventListener('click', function () {
    var abrir = panel.hidden;
    panel.hidden = !abrir;
    boton.setAttribute('aria-expanded', String(abrir));
  });
  panel.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', cerrar); });
  document.addEventListener('click', function (e) { if (!nav.contains(e.target)) cerrar(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { cerrar(); boton.focus(); } });

  function mostrar() { nav.classList.toggle('visible', window.scrollY > 500); if (window.scrollY <= 500) cerrar(); }
  window.addEventListener('scroll', mostrar, { passive: true });
  mostrar();

  if ('IntersectionObserver' in window) {
    var obs = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (en) {
        if (!en.isIntersecting) return;
        enlaces.forEach(function (a) { a.setAttribute('aria-current', String(a.getAttribute('href') === '#' + en.target.id)); });
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    enlaces.forEach(function (a) { var s = document.querySelector(a.getAttribute('href')); if (s) obs.observe(s); });
  }
})();
