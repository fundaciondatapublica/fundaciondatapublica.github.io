#!/usr/bin/env python3
"""Radiografía de datos.gob.cl para la portada.

Consulta la API pública (CKAN) del portal nacional de datos abiertos, cruza
los municipios que publican con la lista de comunas y reescribe la ficha de
index.html entre los marcadores <!-- radiografia:inicio/fin -->.

Uso:  python3 _herramientas/radiografia.py
(Jekyll no publica carpetas que empiezan con guion bajo.)
"""
import collections, datetime, html, json, pathlib, re, unicodedata, urllib.request

API = 'https://datos.gob.cl/api/3/action/'
WIKI = ('https://es.wikipedia.org/w/api.php?action=parse&page=Anexo:Comunas_de_Chile'
        '&prop=text&format=json&formatversion=2')
INDEX = pathlib.Path(__file__).resolve().parent.parent / 'index.html'

# Regiones de norte a sur, con nombre corto para la ficha.
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


def leer(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'DataPublica-radiografia/1.0'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def norm(s):
    s = unicodedata.normalize('NFKD', s.lower()).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z ]', '', s).strip()


def miles(n):
    return f'{n:,}'.replace(',', '.')


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
            comunas[norm(c[1])] = c[4].split('\xa0')[0]

    por_org = collections.Counter(p['owner_org'] for p in paquetes)
    publican = collections.Counter()
    for o in orgs:
        m = re.match(r'(?i)(ilustre\s+)?municipalidad\s+de\s+(.*)', o['title'].strip())
        if m and por_org[o['id']] and norm(m.group(2)) in comunas:
            publican[comunas[norm(m.group(2))]] += 1
    total_reg = collections.Counter(comunas.values())

    recursos = [r for p in paquetes for r in p['resources']]
    fmt = [(r.get('format') or '').lower().strip('.') for r in recursos]
    pct = lambda n, d: round(100 * n / d)
    abiertos = pct(sum(f in ABIERTOS for f in fmt), len(fmt))
    api = pct(sum(bool(r.get('datastore_active')) for r in recursos), len(recursos))
    hace5 = str(datetime.date.today().year - 5)
    viejos = pct(sum(p['metadata_modified'][:4] <= hace5 for p in paquetes), len(paquetes))

    n_com, n_pub = len(comunas), sum(publican.values())
    vacias = [corto for largo, corto in REGIONES if publican[largo] == 0]
    hoy = datetime.date.today().strftime('%d-%m-%Y')

    filas = []
    for largo, corto in REGIONES:
        t, p = total_reg[largo], publican[largo]
        puntos = '<i class="si"></i>' * p + '<i></i>' * (t - p)
        cls = ' class="vacia"' if p == 0 else ''
        filas.append(f'<li{cls}><span class="reg">{corto}</span>'
                     f'<span class="puntos" aria-hidden="true">{puntos}</span>'
                     f'<span class="cuenta">{p}/{t}</span></li>')

    if len(vacias) > 1:
        lista = ', '.join(vacias[:-1]) + ' y ' + vacias[-1]
        vacias_txt = f' En {lista}, ninguna.'
    else:
        vacias_txt = f' En {vacias[0]}, ninguna.' if vacias else ''

    ficha = f'''<!-- radiografia:inicio -->
                <figure class="ficha radiografia" aria-labelledby="radiografia-titulo">
                    <div class="ficha-cab"><span>Radiografía · datos.gob.cl</span><span>Corte {hoy}</span></div>
                    <h3 id="radiografia-titulo">¿Quién publica datos abiertos en Chile?</h3>
                    <p class="desc">Municipios con datos en el portal nacional, de norte a sur. Cada punto es una comuna.</p>
                    <ol class="mapa" aria-label="Comunas que publican datos, por región">
                        {(chr(10) + ' ' * 24).join(filas)}
                    </ol>
                    <div class="hallazgo"><strong>Hallazgo</strong>Solo {n_pub} de {n_com} comunas publican datos en el portal nacional.{vacias_txt}</div>
                    <dl class="cifras">
                        <div><dt>{miles(len(paquetes))}</dt><dd>conjuntos de datos de {len(por_org)} instituciones</dd></div>
                        <div><dt>{abiertos} %</dt><dd>de los archivos en formatos abiertos</dd></div>
                        <div><dt>{api} %</dt><dd>consultable por API</dd></div>
                        <div><dt>{viejos} %</dt><dd>sin actualizar en 5 años</dd></div>
                    </dl>
                    <p class="carril">Fuente: API pública de datos.gob.cl · consulta {hoy}<br>Método: conjuntos por institución, formato y última modificación</p>
                    <figcaption class="ficha-pie">Datos reales. No incluye municipios que publican solo en portales propios.</figcaption>
                </figure>
                <!-- radiografia:fin -->'''

    texto = INDEX.read_text(encoding='utf-8')
    nuevo, n = re.subn(r'<!-- radiografia:inicio -->.*?<!-- radiografia:fin -->', ficha, texto, flags=re.S)
    if n != 1:
        raise SystemExit('No encontré los marcadores radiografia en index.html')
    INDEX.write_text(nuevo, encoding='utf-8')
    print(f'{len(paquetes)} conjuntos · {n_pub}/{n_com} comunas · abiertos {abiertos} % · API {api} % · sin actualizar {viejos} %')


if __name__ == '__main__':
    main()
