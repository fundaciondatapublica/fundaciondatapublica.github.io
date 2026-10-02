#!/usr/bin/env python3
"""Radiografía de datos.gob.cl para la portada.

Consulta la API pública (CKAN) del portal nacional de datos abiertos, cruza
los municipios que publican con la lista de comunas y reescribe dos bloques de
index.html: la ficha de la portada (<!-- radiografia-hero:… -->) y la sección
con el mapa por región (<!-- radiografia-seccion:… -->).

Uso:  python3 _herramientas/radiografia.py
(Jekyll no publica carpetas que empiezan con guion bajo.)
"""
import collections, datetime, html, json, pathlib, re, unicodedata, urllib.request

API = 'https://datos.gob.cl/api/3/action/'
WIKI = ('https://es.wikipedia.org/w/api.php?action=parse&page=Anexo:Comunas_de_Chile'
        '&prop=text&format=json&formatversion=2')
INDEX = pathlib.Path(__file__).resolve().parent.parent / 'index.html'

# Regiones de norte a sur, con nombre corto.
REGIONES = [
    ('Arica y Parinacota', 'Arica'), ('Tarapacá', 'Tarapacá'),
    ('Antofagasta', 'Antofagasta'), ('Atacama', 'Atacama'), ('Coquimbo', 'Coquimbo'),
    ('Valparaíso', 'Valparaíso'), ('Metropolitana de Santiago', 'Metropolitana'),
    ("Lib. Gral. Bernardo O'Higgins", "O'Higgins"), ('Maule', 'Maule'), ('Ñuble', 'Ñuble'),
    ('Biobío', 'Biobío'), ('La Araucanía', 'La Araucanía'), ('Los Ríos', 'Los Ríos'),
    ('Los Lagos', 'Los Lagos'), ('Aysén del General Carlos Ibáñez del Campo', 'Aysén'),
    ('Magallanes y Antártica Chilena', 'Magallanes'),
]
ABIERTOS = {'csv', 'json', 'xml', 'geojson', 'txt', 'tsv', 'kml', 'kmz', 'shp', 'api',
            'wms', 'wfs', 'ods', 'rdf', 'parquet'}
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
         'septiembre', 'octubre', 'noviembre', 'diciembre']


def leer(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'DataPublica-radiografia/1.0'})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)


def norm(s):
    s = unicodedata.normalize('NFKD', s.lower()).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z ]', '', s).strip()


def miles(n):
    return f'{n:,}'.replace(',', '.')


def y(lista):
    return ', '.join(lista[:-1]) + ' y ' + lista[-1] if len(lista) > 1 else ''.join(lista)


def reemplazar(texto, marca, bloque):
    nuevo, n = re.subn(rf'<!-- {marca}:inicio -->.*?<!-- {marca}:fin -->',
                       f'<!-- {marca}:inicio -->\n{bloque}\n        <!-- {marca}:fin -->',
                       texto, flags=re.S)
    if n != 1:
        raise SystemExit(f'No encontré los marcadores {marca} en index.html')
    return nuevo


def main():
    paquetes, inicio = [], 0
    while True:
        r = leer(f'{API}package_search?rows=1000&start={inicio}')['result']
        paquetes += r['results']
        inicio += 1000
        if inicio >= r['count']:
            break
    orgs = leer(f'{API}organization_list?all_fields=true&limit=1000')['result']

    comunas = {}
    tabla = leer(WIKI)['parse']['text']
    for fila in re.findall(r'<tr>(.*?)</tr>', tabla, re.S):
        c = [html.unescape(re.sub(r'<[^>]+>', '', x)).strip()
             for x in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', fila, re.S)]
        if len(c) > 5 and c[0].isdigit():
            comunas[norm(c[1])] = (c[1], c[4].split('\xa0')[0])

    por_org = collections.Counter(p['owner_org'] for p in paquetes)
    munis = {}  # comuna -> conjuntos publicados
    for o in orgs:
        m = re.match(r'(?i)(ilustre\s+)?municipalidad\s+de\s+(.*)', o['title'].strip())
        if m and por_org[o['id']] and norm(m.group(2)) in comunas:
            munis[norm(m.group(2))] = por_org[o['id']]

    total_reg = collections.Counter(reg for _, reg in comunas.values())
    pub_reg = collections.Counter(comunas[c][1] for c in munis)
    conj_reg = collections.Counter()
    for c, n in munis.items():
        conj_reg[comunas[c][1]] += n

    # Cifras de calidad y formato.
    recursos = [r for p in paquetes for r in p['resources']]
    fmt = collections.Counter((r.get('format') or '').lower().strip('.') for r in recursos)
    pct = lambda n, d: round(100 * n / d)
    abiertos = pct(sum(v for k, v in fmt.items() if k in ABIERTOS), len(recursos))
    api = pct(sum(bool(r.get('datastore_active')) for r in recursos), len(recursos))
    hoy = datetime.date.today()
    hace5 = str(hoy.year - 5)
    viejos = pct(sum(p['metadata_modified'][:4] <= hace5 for p in paquetes), len(paquetes))
    rar = fmt['rar']

    n_com, n_pub = len(comunas), len(munis)
    vacias = [corto for largo, corto in REGIONES if pub_reg[largo] == 0]
    mejor = max(REGIONES, key=lambda r: pub_reg[r[0]] / total_reg[r[0]])
    rm = 'Metropolitana de Santiago'
    rm_top = max((c for c in munis if comunas[c][1] == rm), key=munis.get)
    fecha = hoy.strftime('%d-%m-%Y')
    mes = f'{MESES[hoy.month - 1]} {hoy.year}'

    hero = f'''                <figure class="ficha radiografia" aria-labelledby="radiografia-titulo">
                    <div class="ficha-cab"><span>Radiografía · datos.gob.cl</span><span>{mes}</span></div>
                    <h3 id="radiografia-titulo">Lo que muestra el portal nacional de datos abiertos</h3>
                    <dl class="cifras">
                        <div><dt>{abiertos} %</dt><dd><b>Formato.</b> Solo esa parte de los archivos viene en formatos abiertos; hay {miles(rar)} comprimidos en .rar.</dd></div>
                        <div><dt>{viejos} %</dt><dd><b>Calidad.</b> De los conjuntos de datos no se actualiza hace cinco años o más.</dd></div>
                        <div><dt>{api} %</dt><dd><b>Acceso.</b> Se puede consultar por API; el resto hay que descargarlo y limpiarlo.</dd></div>
                        <div class="alerta"><dt>{n_pub}<small> de {n_com}</small></dt><dd><b>Territorio.</b> Comunas que publican datos. En {len(vacias)} regiones, ninguna.</dd></div>
                    </dl>
                    <a class="ir" href="#radiografia">Ver la radiografía por región ↓</a>
                    <figcaption class="ficha-pie">Fuente: API pública de datos.gob.cl, {fecha}. {miles(len(paquetes))} conjuntos de {len(por_org)} instituciones.</figcaption>
                </figure>'''

    filas = []
    for largo, corto in REGIONES:
        t, p = total_reg[largo], pub_reg[largo]
        puntos = '<i class="si"></i>' * p + '<i></i>' * (t - p)
        cls = ' class="vacia"' if p == 0 else (' class="mejor"' if largo == mejor[0] else '')
        filas.append(f'<li{cls}><span class="reg">{corto}</span>'
                     f'<span class="puntos" aria-hidden="true">{puntos}</span>'
                     f'<span class="cuenta">{p}/{t}</span></li>')

    seccion = f'''        <section class="seccion" id="radiografia">
            <div class="wrap">
                <div class="seccion-cab">
                    <div>
                        <span class="folio">Radiografía · {mes}</span>
                        <h2>¿Quién publica datos abiertos en Chile?</h2>
                    </div>
                    <p>Municipios con datos en el portal nacional, de norte a sur. Cada punto es una comuna.</p>
                </div>
                <div class="radio-grid">
                    <div class="relato">
                        <p class="grande"><b>{n_pub} de {n_com}</b> comunas publican datos en el portal nacional. Las otras {n_com - n_pub} no tienen ni un conjunto.</p>
                        <p><span class="marca-vacia">{y(vacias)}</span>: {len(vacias)} regiones donde ningún municipio publica. El norte y el extremo sur aparecen vacíos en el mapa.</p>
                        <p>En la Región Metropolitana publican {pub_reg[rm]} de {total_reg[rm]} municipios, y {comunas[rm_top][0]} reúne {munis[rm_top]} de sus {conj_reg[rm]} conjuntos. Un solo municipio sostiene casi toda la oferta de la región.</p>
                        <p><span class="marca-mejor">{mejor[1]}</span> tiene la mejor proporción: {pub_reg[mejor[0]]} de {total_reg[mejor[0]]} comunas. Se puede.</p>
                        <p class="cierre">Publicar datos no basta, pero sin publicar no hay nada que verificar. <a href="#newsletter">Recibe la próxima radiografía →</a></p>
                    </div>
                    <figure class="ficha mapa-ficha">
                        <ol class="mapa" aria-label="Comunas que publican datos, por región, de norte a sur">
                            {(chr(10) + ' ' * 28).join(filas)}
                        </ol>
                        <figcaption class="carril">Fuente: API pública de datos.gob.cl, {fecha}.<br>No incluye municipios que publican solo en portales propios.</figcaption>
                    </figure>
                </div>
            </div>
        </section>'''

    texto = INDEX.read_text(encoding='utf-8')
    texto = reemplazar(texto, 'radiografia-hero', hero)
    texto = reemplazar(texto, 'radiografia-seccion', seccion)
    INDEX.write_text(texto, encoding='utf-8')
    print(f'{n_pub}/{n_com} comunas · abiertos {abiertos} % · API {api} % · sin actualizar {viejos} % · '
          f'vacías: {y(vacias)} · mejor: {mejor[1]} · RM top: {comunas[rm_top][0]} {munis[rm_top]}/{conj_reg[rm]}')


if __name__ == '__main__':
    main()
