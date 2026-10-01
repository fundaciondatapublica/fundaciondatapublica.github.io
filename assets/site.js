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
