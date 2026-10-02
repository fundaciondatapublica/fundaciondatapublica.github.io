#!/usr/bin/env python3
"""Radiografía de datos.gob.cl para la portada.

Consulta la API pública (CKAN) del portal nacional de datos abiertos, cruza
los municipios que publican con la lista de comunas y reescribe la ficha de
index.html entre los marcadores <!-- radiografia:inicio/fin -->.

Uso:  python3 _herramientas/radiografia.py
(Jekyll no publica carpetas que empiezan con guion bajo.)
"""
import datetime, html, json, pathlib, re, unicodedata, urllib.request

API = 'https://datos.gob.cl/api/3/action/'
WIKI = ('https://es.wikipedia.org/w/api.php?action=parse&page=Anexo:Comunas_de_Chile'
        '&prop=text&format=json&formatversion=2')
INDEX = pathlib.Path(__file__).resolve().parent.parent / 'index.html'

# Regiones de norte a sur, con nombre corto.
REGIONES = [
    ('Arica y Parinacota', 'Arica y Parinacota'), ('Tarapacá', 'Tarapacá'),
    ('Antofagasta', 'Antofagasta'), ('Atacama', 'Atacama'), ('Coquimbo', 'Coquimbo'),
    ('Valparaíso', 'Valparaíso'), ('Metropolitana de Santiago', 'Metropolitana'),
    ("Lib. Gral. Bernardo O'Higgins", "O'Higgins"), ('Maule', 'Maule'), ('Ñuble', 'Ñuble'),
    ('Biobío', 'Biobío'), ('La Araucanía', 'La Araucanía'), ('Los Ríos', 'Los Ríos'),
    ('Los Lagos', 'Los Lagos'), ('Aysén del General Carlos Ibáñez del Campo', 'Aysén'),
    ('Magallanes y Antártica Chilena', 'Magallanes'),
]
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
         'septiembre', 'octubre', 'noviembre', 'diciembre']


def leer(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'DataPublica-radiografia/1.0'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def norm(s):
    s = unicodedata.normalize('NFKD', s.lower()).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z ]', '', s).strip()


def main():
    orgs = leer(f'{API}organization_list?all_fields=true&limit=1000')['result']

    # Comunas en orden de la tabla (código territorial), agrupadas por región.
    comunas = []
    tabla = leer(WIKI)['parse']['text']
    for fila in re.findall(r'<tr>(.*?)</tr>', tabla, re.S):
        c = [html.unescape(re.sub(r'<[^>]+>', '', x)).strip()
             for x in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', fila, re.S)]
        if len(c) > 5 and c[0].isdigit():
            comunas.append((norm(c[1]), c[4].split('\xa0')[0]))

    publican = set()
    for o in orgs:
        m = re.match(r'(?i)(ilustre\s+)?municipalidad\s+de\s+(.*)', o['title'].strip())
        if m and o.get('package_count', 0) > 0:
            publican.add(norm(m.group(2)))

    puntos, vacias = [], []
    for largo, corto in REGIONES:
        de_la_region = [n for n, reg in comunas if reg == largo]
        si = [n for n in de_la_region if n in publican]
        if not si:
            vacias.append(corto)
        puntos += ['<i class="si"></i>'] * len(si) + ['<i></i>'] * (len(de_la_region) - len(si))

    n_com = len(comunas)
    n_pub = sum(n in publican for n, _ in comunas)
    hoy = datetime.date.today()
    lista = ', '.join(vacias[:-1]) + ' y ' + vacias[-1] if len(vacias) > 1 else ''.join(vacias)

    ficha = f'''<!-- radiografia:inicio -->
                <figure class="ficha radiografia" aria-labelledby="radiografia-titulo">
                    <div class="ficha-cab"><span>datos.gob.cl</span><span>{MESES[hoy.month - 1]} {hoy.year}</span></div>
                    <p class="cifra" id="radiografia-titulo"><b>{n_pub}</b> de {n_com}</p>
                    <p class="desc">comunas de Chile publican datos en el portal nacional de datos abiertos.</p>
                    <div class="puntos" role="img" aria-label="{n_com} puntos, uno por comuna, de norte a sur; {n_pub} están marcados">{''.join(puntos)}</div>
                    <p class="carril">Cada punto es una comuna, de Arica a Magallanes.</p>''' + (f'''
                    <div class="hallazgo"><strong>{len(vacias)} regiones en cero</strong>{lista}.</div>''' if vacias else '') + f'''
                    <figcaption class="ficha-pie">Fuente: API de datos.gob.cl, {hoy.strftime('%d-%m-%Y')}.</figcaption>
                </figure>
                <!-- radiografia:fin -->'''

    texto = INDEX.read_text(encoding='utf-8')
    nuevo, n = re.subn(r'<!-- radiografia:inicio -->.*?<!-- radiografia:fin -->', ficha, texto, flags=re.S)
    if n != 1:
        raise SystemExit('No encontré los marcadores radiografia en index.html')
    INDEX.write_text(nuevo, encoding='utf-8')
    print(f'{n_pub}/{n_com} comunas publican · regiones en cero: {lista or "ninguna"}')


if __name__ == '__main__':
    main()
