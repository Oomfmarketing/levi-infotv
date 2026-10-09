#!/usr/bin/env python3
"""Build the location pages (/levi/, /yllas/, /helsinki/) from levi-infotv.html.

Each page is the full live app with its own title, description, canonical URL,
structured data (JSON-LD) and a crawlable text section for search engines and
AI search. Run after editing levi-infotv.html:

    python3 build.py
"""
import html, json, os, re, datetime

SITE = 'https://levitv.com'
ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = open(os.path.join(ROOT, 'levi-infotv.html'), encoding='utf-8').read()

LOCATIONS = {
  'levi': {
    'name': 'Levi', 'lat': 67.8009, 'lon': 24.8009, 'region': 'Kittilä, Lapland, Finland',
    'title': 'Levi Live Webcams, Weather & Northern Lights — LeviTV',
    'desc': 'Watch Levi live: 11 webcams from Levi Ski Resort including an aurora cam, '
            'real-time weather, 5-day forecast, northern lights (Kp) and sunrise & sunset in Levi, Finnish Lapland.',
    'h1': 'Levi live webcams, weather and northern lights',
    'intro': [
      'LeviTV shows Levi in Finnish Lapland in real time: live cameras from around Levi Fell, '
      'the current weather on the fell, a 5-day forecast, northern lights activity and today\'s daylight — on one screen.',
      'Levi is a fell and ski resort in Kittilä, Finnish Lapland, about 170 km north of the Arctic Circle. '
      'The summit is 531 m above sea level.',
    ],
    'cams_title': 'Live cameras in Levi',
    'cams': ['Zero Point (Levi Center)', 'South Point (South Slopes)', 'Village View', 'Levi Black (Gondola Area)',
             'Levi Six (NE Slopes)', 'Levi West (West Slopes)', 'Glacier Express', 'Top of Levi (summit, 531 m)',
             'Lifts 13 & 14 (North)', 'Leevilandia (South Slopes)', 'Aurora Cam (Levi Igloos)'],
    'data': [
      ('Weather now', 'observations from the Finnish Meteorological Institute (FMI) station Kittilä Kenttärova, refreshed every 10 minutes'),
      ('Forecast', '5-day FMI forecast for Levi with daily highs, lows and cloud cover'),
      ('Northern lights', 'live planetary Kp index and 12-hour Kp forecast from NOAA, rated for Levi\'s latitude (67.8°N), plus tonight\'s cloud cover'),
      ('Daylight', 'sunrise, sunset and day length for Levi, calculated for today'),
    ],
    'faq': [
      ('Where can I watch Levi webcams live?',
       'On LeviTV (levitv.com/levi/). It rotates through 11 live cameras around Levi Fell — Levi Center, the slopes, '
       'the gondola area, the summit and an aurora camera — and you can pick a single camera on your phone.'),
      ('What is the weather in Levi right now?',
       'LeviTV shows the latest observation from the FMI weather station Kittilä Kenttärova near Levi, '
       'with temperature, feels-like temperature, wind and cloud cover, plus a 5-day forecast.'),
      ('Can you see the northern lights in Levi?',
       'Yes. Levi lies under the auroral zone, so northern lights are common from late August to April whenever the sky is '
       'dark and clear. Even a moderate Kp index of 2–3 can be enough at Levi\'s latitude. LeviTV shows the live Kp index, '
       'the Kp forecast, tonight\'s cloud cover and when it gets dark.'),
      ('When does the sun rise and set in Levi?',
       'LeviTV calculates sunrise, sunset and day length for Levi every day. In midsummer the sun does not set (midnight sun) '
       'and in midwinter it stays below the horizon for a few weeks (polar night, kaamos).'),
      ('Is LeviTV an official Levi service?',
       'No. LeviTV is an independent real-time view of Levi made by OOMF Marketing Oy. The camera streams are public YouTube '
       'live streams, weather comes from FMI and aurora data from NOAA. For tickets, slopes and events see levi.fi.'),
    ],
    'fi_title': 'Levi live — webkamerat, sää ja revontulet',
    'fi': 'LeviTV näyttää Levin reaaliajassa: 11 live-kameraa Levitunturilta (myös revontulikamera), Levin sää nyt ja '
          '5 päivän ennuste (Ilmatieteen laitos), revontuliennuste (Kp-indeksi) sekä auringonnousu ja -lasku.',
  },
  'yllas': {
    'name': 'Ylläs', 'lat': 67.5644, 'lon': 24.2244, 'region': 'Kolari, Lapland, Finland',
    'title': 'Ylläs Live Webcams, Weather & Northern Lights — LeviTV',
    'desc': 'Watch Ylläs live: webcams from Ylläs Ski Resort (gondola, chairlift, summit), current weather, '
            '5-day forecast, northern lights (Kp) and sunrise & sunset in Ylläs, Finnish Lapland.',
    'h1': 'Ylläs live webcams, weather and northern lights',
    'intro': [
      'LeviTV shows Ylläs in Finnish Lapland in real time: live cameras from Ylläs Ski Resort, the weather now, '
      'a 5-day forecast, northern lights activity and today\'s daylight.',
      'Ylläs is a fell in Kolari, Finnish Lapland, rising to 719 m, with the villages of Äkäslompolo on the north side '
      'and Ylläsjärvi on the south side.',
    ],
    'cams_title': 'Live cameras in Ylläs',
    'cams': ['Gondola station (Ylläs South)', 'Ylläs Express chairlift', 'Summit camera (719 m)'],
    'data': [
      ('Weather now', 'the current hour of the Finnish Meteorological Institute (FMI) forecast for Ylläs'),
      ('Forecast', '5-day FMI forecast for Ylläs with daily highs, lows and cloud cover'),
      ('Northern lights', 'live Kp index and Kp forecast from NOAA, rated for Ylläs\' latitude (67.6°N), plus tonight\'s cloud cover'),
      ('Daylight', 'sunrise, sunset and day length for Ylläs, calculated for today'),
    ],
    'faq': [
      ('Where can I watch Ylläs webcams live?',
       'On LeviTV (levitv.com/yllas/), which rotates the live cameras of Ylläs Ski Resort: the gondola station, '
       'the Ylläs Express chairlift and the summit camera.'),
      ('Can you see the northern lights in Ylläs?',
       'Yes. Ylläs is in the auroral zone of Finnish Lapland, so northern lights are common from late August to April '
       'on dark, clear nights. LeviTV shows the live Kp index, the Kp forecast and tonight\'s cloud cover.'),
      ('What is the weather in Ylläs today?',
       'LeviTV shows the current conditions and a 5-day forecast for Ylläs from the Finnish Meteorological Institute.'),
    ],
    'fi_title': 'Ylläs live — webkamerat, sää ja revontulet',
    'fi': 'LeviTV näyttää Ylläksen reaaliajassa: Ylläs Ski Resortin live-kamerat (gondoli, tuolihissi, huippu), '
          'Ylläksen sää ja 5 päivän ennuste, revontuliennuste (Kp-indeksi) sekä auringonnousu ja -lasku.',
  },
  'helsinki': {
    'name': 'Helsinki', 'lat': 60.1699, 'lon': 24.9384, 'region': 'Helsinki, Finland',
    'title': 'Helsinki Live Webcams, Weather & Harbour Cams — LeviTV',
    'desc': 'Watch Helsinki live: webcams of Market Square and the Port of Helsinki (South and West Harbour), '
            'current weather from Kaisaniemi, 5-day forecast, northern lights (Kp) and sunrise & sunset.',
    'h1': 'Helsinki live webcams, weather and harbour views',
    'intro': [
      'LeviTV shows Helsinki in real time: live cameras of Market Square (Kauppatori) and the Port of Helsinki, '
      'the weather now, a 5-day forecast, northern lights activity and today\'s daylight.',
    ],
    'cams_title': 'Live cameras in Helsinki',
    'cams': ['Market Square & city centre', 'South Harbour (Port of Helsinki)', 'West Harbour — south (Port of Helsinki)',
             'West Harbour — north (Port of Helsinki)'],
    'data': [
      ('Weather now', 'observations from the Finnish Meteorological Institute (FMI) station Helsinki Kaisaniemi'),
      ('Forecast', '5-day FMI forecast for Helsinki with daily highs, lows and cloud cover'),
      ('Northern lights', 'live Kp index and Kp forecast from NOAA, rated for Helsinki\'s latitude (60.2°N)'),
      ('Daylight', 'sunrise, sunset and day length for Helsinki, calculated for today'),
    ],
    'faq': [
      ('Where can I watch Helsinki webcams live?',
       'On LeviTV (levitv.com/helsinki/), which rotates live cameras of Market Square and the South and West Harbour '
       'of the Port of Helsinki.'),
      ('Can you see the northern lights in Helsinki?',
       'Sometimes. Helsinki is far south of the auroral zone, so northern lights are usually visible only during strong '
       'geomagnetic activity (roughly Kp 4–5 or more) on dark, clear nights, low on the northern horizon. LeviTV shows the live Kp index.'),
    ],
    'fi_title': 'Helsinki live — webkamerat ja sää',
    'fi': 'LeviTV näyttää Helsingin reaaliajassa: Kauppatorin ja Helsingin Sataman live-kamerat, Helsingin sää '
          '(Kaisaniemi) ja 5 päivän ennuste, revontuliennuste sekä auringonnousu ja -lasku.',
  },
}

E = html.escape

def about_html(k, L):
    url = f'{SITE}/{k}/'
    others = ' · '.join(f'<a href="/{o}/">{E(LOCATIONS[o]["name"])} live</a>' for o in LOCATIONS if o != k)
    return f'''<section id="about" aria-labelledby="about-h1">
    <h1 id="about-h1">{E(L['h1'])}</h1>
    {''.join(f'<p>{E(p)}</p>' for p in L['intro'])}
    <h2>{E(L['cams_title'])}</h2>
    <ul>{''.join(f'<li>{E(c)}</li>' for c in L['cams'])}</ul>
    <h2>What LeviTV shows</h2>
    <ul>{''.join(f'<li><strong>{E(a)}:</strong> {E(b)}</li>' for a, b in L['data'])}</ul>
    <h2>Frequently asked questions</h2>
    {''.join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in L['faq'])}
    <h2 lang="fi">{E(L['fi_title'])}</h2>
    <p lang="fi">{E(L['fi'])}</p>
    <p>More live views: {others} · <a href="/">LeviTV home</a> · TV view: <a href="/{k}/full/">{url}full/</a></p>
  </section>'''

def jsonld(k, L):
    url = f'{SITE}/{k}/'
    return {
      '@context': 'https://schema.org',
      '@graph': [
        {'@type': 'WebPage', '@id': url, 'url': url, 'name': L['title'], 'description': L['desc'],
         'inLanguage': 'en', 'isPartOf': {'@id': f'{SITE}/#website'}, 'about': {'@id': url + '#place'},
         'primaryImageOfPage': f'{SITE}/og.png',
         'breadcrumb': {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'LeviTV', 'item': f'{SITE}/'},
            {'@type': 'ListItem', 'position': 2, 'name': f'{L["name"]} live', 'item': url}]}},
        {'@type': ['TouristDestination', 'Place'], '@id': url + '#place', 'name': L['name'],
         'address': {'@type': 'PostalAddress', 'addressLocality': L['region'].split(',')[0], 'addressCountry': 'FI'},
         'geo': {'@type': 'GeoCoordinates', 'latitude': L['lat'], 'longitude': L['lon']}},
        {'@type': 'FAQPage', '@id': url + '#faq',
         'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in L['faq']]},
      ]}

def seo_head(k, L):
    url = f'{SITE}/{k}/'
    return f'''<!--SEO:start-->
<title>{E(L['title'])}</title>
<meta name="description" content="{E(L['desc'])}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="LeviTV">
<meta property="og:title" content="{E(L['title'])}">
<meta property="og:description" content="{E(L['desc'])}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="geo.position" content="{L['lat']};{L['lon']}">
<meta name="geo.placename" content="{E(L['name'])}, Finland">
<script type="application/ld+json">{json.dumps(jsonld(k, L), ensure_ascii=False)}</script>
<script>window.INFOTV_LOC='{k}';</script>
<!--SEO:end-->'''

for k, L in LOCATIONS.items():
    page = re.sub(r'<!--SEO:start-->.*?<!--SEO:end-->', lambda m: seo_head(k, L), TEMPLATE, flags=re.S)
    page = re.sub(r'<!--ABOUT:start-->.*?<!--ABOUT:end-->',
                  lambda m: '<!--ABOUT:start-->' + about_html(k, L) + '<!--ABOUT:end-->', page, flags=re.S)
    page = page.replace('<!DOCTYPE html>', '<!DOCTYPE html>\n<!-- Generated by build.py from levi-infotv.html — edit the template, then run: python3 build.py -->', 1)
    os.makedirs(os.path.join(ROOT, k), exist_ok=True)
    open(os.path.join(ROOT, k, 'index.html'), 'w', encoding='utf-8').write(page)

    # full-screen TV view: a redirect, kept out of search results
    full = f'/levi-infotv.html?loc={k}&view=full'
    os.makedirs(os.path.join(ROOT, k, 'full'), exist_ok=True)
    open(os.path.join(ROOT, k, 'full', 'index.html'), 'w', encoding='utf-8').write(f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(L['name'])} full-screen TV view — LeviTV</title>
<meta name="robots" content="noindex,follow">
<link rel="canonical" href="{SITE}/{k}/">
<meta http-equiv="refresh" content="0;url={full}">
<script>location.replace('{full}'+(location.search?'&'+location.search.slice(1):''));</script>
</head><body style="background:#05080f"></body></html>
''')

# sitemap
today = datetime.date.today().isoformat()
urls = [f'{SITE}/'] + [f'{SITE}/{k}/' for k in LOCATIONS]
open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write(
  '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
  + ''.join(f'  <url><loc>{u}</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq>'
            f'<priority>{"1.0" if u.endswith("/levi/") or u == SITE + "/" else "0.7"}</priority></url>\n' for u in urls)
  + '</urlset>\n')
print('built:', ', '.join(f'/{k}/' for k in LOCATIONS), '+ sitemap.xml')
