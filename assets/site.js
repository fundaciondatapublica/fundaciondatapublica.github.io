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
