#!/usr/bin/env python3
"""Build the location pages (/levi/, /yllas/, /rovaniemi/, /helsinki/) from levi-infotv.html.

Each page is the full live app with its own title, description, canonical URL,
structured data (JSON-LD) and a crawlable text section for search engines and
AI search. Run after editing levi-infotv.html:

    python3 build.py
"""
import html, json, os, re, datetime, shutil, subprocess

SITE = 'https://levitv.com'
ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = open(os.path.join(ROOT, 'levi-infotv.html'), encoding='utf-8').read()
TODAY = datetime.date.today().isoformat()
DATE_TOKEN = '@@MODIFIED@@'

# YouTube upload date of each camera stream (required by VideoObject structured data).
# Add a line when adding a camera: "uploadDate" in the page source of youtube.com/watch?v=<id>.
CAM_UPLOADED = {
  'LwihxyJ4V20': '2020-11-11T22:50:38-08:00', '89vRm9bb9_c': '2021-02-16T01:05:46-08:00',
  'X7tdyNFpp1g': '2022-10-02T22:49:25-07:00', 'gehi4YiVYdY': '2022-07-22T04:36:42-07:00',
  'jQrqWYe5Cn4': '2025-03-13T06:50:36-07:00', 'Wr9b5aYA4mI': '2023-09-28T03:16:30-07:00',
  'eXDCi75TjM8': '2025-06-17T03:32:22-07:00', 'hWN0iCg8pDY': '2023-02-21T00:57:43-08:00',
  'EmoTKMm5sDI': '2025-08-05T01:20:07-07:00', '9NxBGQUb1oY': '2026-09-23T11:10:18-07:00',
  'PeLTbbI2i6U': '2025-11-05T05:40:51-08:00', 'ptZhHJtTqRY': '2026-04-09T07:25:50-07:00',
  '5Oda5wfGpvw': '2025-11-12T01:02:52-08:00', 'Cp4RRAEgpeU': '2020-01-28T22:35:48-08:00',
  'wT8Zhh9MBEE': '2026-07-22T02:06:15-07:00', 'LMZQ7eFhm58': '2020-08-17T04:10:04-07:00',
  'CvOB-Is_yYU': '2020-02-28T04:05:04-08:00', '6hPWq2IG08M': '2022-01-09T22:51:53-08:00',
  'JnJhFYhIjFs': '2022-01-09T22:39:01-08:00',
}

LOCATIONS = {
  'levi': {
    'name': 'Levi', 'lat': 67.8009, 'lon': 24.8009, 'region': 'Kittilä, Lapland, Finland',
    'type': 'SkiResort', 'elevation': 531, 'wiki': 'https://en.wikipedia.org/wiki/Levi,_Finland',
    'title': 'Levi Live Webcams, Weather, Slopes & Northern Lights — LeviTV',
    'desc': 'Watch Levi live: 10 webcams including an aurora cam, weather now, 5-day forecast, '
            'open slopes, northern lights (Kp) and daylight in Finnish Lapland.',
    'h1': 'Levi live webcams, weather, slopes and northern lights',
    'intro': [
      'LeviTV shows Levi in Finnish Lapland in real time: live cameras from around Levi Fell, '
      'the current weather on the fell, a 5-day forecast, northern lights activity and today\'s daylight — on one screen.',
      'Levi is a fell and ski resort in Kittilä, Finnish Lapland, about 170 km north of the Arctic Circle. '
      'The summit is 531 m above sea level.',
    ],
    'cams_title': 'Live cameras in Levi',
    'cams': ['Zero Point (Levi Center)', 'South Point (South Slopes)', 'Village View', 'Levi Black (Gondola Area)',
             'Levi West (West Slopes)', 'Glacier Express', 'Top of Levi (summit, 531 m)',
             'Lifts 13 & 14 (North)', 'Elves Village (Tonttula)', 'Aurora Cam (Levi Igloos)'],
    'data': [
      ('Weather now', 'observations from the Finnish Meteorological Institute (FMI) station Kittilä Kenttärova, refreshed every 10 minutes'),
      ('Forecast', '5-day FMI forecast for Levi with daily highs, lows and cloud cover'),
      ('Slopes and lifts', 'how many slopes and lifts are open and the snow depth, when reported; data older than 6 hours is hidden'),
      ('Northern lights', 'live planetary Kp index and 12-hour Kp forecast from NOAA, rated for Levi\'s latitude (67.8°N), plus tonight\'s cloud cover'),
      ('Daylight', 'sunrise, sunset and day length for Levi, calculated for today'),
    ],
    'faq': [
      ('Where can I watch Levi webcams live?',
       'On LeviTV (levitv.com/levi/). It rotates through 10 live cameras around Levi Fell — Levi Center, the slopes, '
       'the gondola area, the summit and an aurora camera — and you can pick a single camera on your phone.'),
      ('What is the weather in Levi right now?',
       'LeviTV shows the latest observation from the FMI weather station Kittilä Kenttärova near Levi, '
       'with temperature, feels-like temperature, wind and cloud cover, plus a 5-day forecast.'),
      ('How many slopes are open in Levi today?',
       'LeviTV shows the number of open slopes and lifts in Levi and the snow depth when they are reported, and hides data '
       'older than 6 hours. For the official slope status see levi.fi.'),
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
    'fi': 'LeviTV näyttää Levin reaaliajassa: 10 live-kameraa Levitunturilta (myös revontulikamera), Levin sää nyt ja '
          '5 päivän ennuste (Ilmatieteen laitos), avoimet rinteet ja hissit, revontuliennuste (Kp-indeksi) sekä auringonnousu ja -lasku.',
    'fi_faq': [
      ('Missä näen Levin webkamerat livenä?',
       'LeviTV:ssä (levitv.com/levi/). Sivu kierrättää 10 live-kameraa Levitunturilta: Levin keskusta, rinteet, '
       'gondolialue, huippu ja revontulikamera. Puhelimella voit valita yksittäisen kameran.'),
      ('Mikä on Levin sää nyt?',
       'LeviTV näyttää Ilmatieteen laitoksen Kittilän Kenttärovan havaintoaseman tuoreimman havainnon: lämpötilan, '
       'tuntuvan lämpötilan, tuulen ja pilvisyyden sekä 5 päivän ennusteen.'),
      ('Montako rinnettä Levillä on auki?',
       'LeviTV näyttää avoimien rinteiden ja hissien määrän sekä lumensyvyyden, kun tiedot on ilmoitettu. '
       'Yli 6 tuntia vanhoja tietoja ei näytetä. Virallinen rinnetilanne on osoitteessa levi.fi.'),
      ('Näkyvätkö revontulet Levillä?',
       'Kyllä. Levi on revontulivyöhykkeellä, joten revontulia näkyy yleisesti elokuun lopulta huhtikuuhun, kun taivas on '
       'pimeä ja kirkas. Levin leveysasteella jo Kp-indeksi 2–3 voi riittää. LeviTV näyttää Kp-indeksin, ennusteen ja pilvisyyden.'),
    ],
  },
  'yllas': {
    'name': 'Ylläs', 'lat': 67.5644, 'lon': 24.2244, 'region': 'Kolari, Lapland, Finland',
    'type': 'SkiResort', 'elevation': 719, 'wiki': 'https://en.wikipedia.org/wiki/Yll%C3%A4s',
    'title': 'Ylläs Live Webcams, Weather & Northern Lights — LeviTV',
    'desc': 'Watch Ylläs live: ski resort webcams (gondola, chairlift, summit), weather now, '
            '5-day forecast, northern lights (Kp) and daylight in Finnish Lapland.',
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
    'fi_faq': [
      ('Missä näen Ylläksen webkamerat livenä?',
       'LeviTV:ssä (levitv.com/yllas/). Sivu kierrättää Ylläs Ski Resortin live-kameroita: gondoliasema, Ylläs Express -tuolihissi ja huippukamera.'),
      ('Mikä on Ylläksen sää tänään?',
       'LeviTV näyttää Ylläksen tämänhetkisen sään ja 5 päivän ennusteen Ilmatieteen laitokselta.'),
      ('Näkyvätkö revontulet Ylläksellä?',
       'Kyllä. Ylläs on Lapin revontulivyöhykkeellä, joten revontulia näkyy yleisesti elokuun lopulta huhtikuuhun pimeinä ja '
       'kirkkaina öinä. LeviTV näyttää Kp-indeksin, ennusteen ja pilvisyyden.'),
    ],
  },
  'rovaniemi': {
    'name': 'Rovaniemi', 'lat': 66.5039, 'lon': 25.7294, 'region': 'Rovaniemi, Lapland, Finland',
    'type': 'City', 'wiki': 'https://en.wikipedia.org/wiki/Rovaniemi',
    'title': 'Rovaniemi Live Webcams: Santa Claus Village & Aurora — LeviTV',
    'desc': 'Watch Rovaniemi live: Santa Claus Village on the Arctic Circle and the Apukka Resort aurora cam, '
            'weather now, 5-day forecast and northern lights (Kp).',
    'h1': 'Rovaniemi live webcams, weather and northern lights',
    'intro': [
      'LeviTV shows Rovaniemi, the capital of Finnish Lapland on the Arctic Circle, in real time: live cameras of '
      'Santa Claus Village and Apukka Resort, the weather now, a 5-day forecast, northern lights activity and today\'s daylight.',
    ],
    'cams_title': 'Live cameras in Rovaniemi',
    'cams': ['Santa Claus Village (Arctic Circle)', 'Apukka Resort (aurora cam)'],
    'data': [
      ('Weather now', 'observations from the Finnish Meteorological Institute (FMI) station Rovaniemi railway station, refreshed every 10 minutes'),
      ('Forecast', '5-day FMI forecast for Rovaniemi with daily highs, lows and cloud cover'),
      ('Northern lights', 'live Kp index and Kp forecast from NOAA, rated for Rovaniemi\'s latitude (66.5°N), plus tonight\'s cloud cover'),
      ('Daylight', 'sunrise, sunset and day length for Rovaniemi, calculated for today'),
    ],
    'faq': [
      ('Is there a live webcam at Santa Claus Village?',
       'Yes. LeviTV (levitv.com/rovaniemi/) shows the live camera of Santa Claus Village on the Arctic Circle in '
       'Rovaniemi, together with an aurora camera at Apukka Resort, the weather and the northern lights forecast.'),
      ('Can you see the northern lights in Rovaniemi?',
       'Yes, often. Rovaniemi is on the Arctic Circle and northern lights can be seen from late August to early April '
       'on dark, clear nights — already at a Kp index of about 2–3. Head away from city lights and look north.'),
    ],
    'fi_title': 'Rovaniemi live — webkamerat, sää ja revontulet',
    'fi': 'LeviTV näyttää Rovaniemen reaaliajassa: Joulupukin Pajakylän ja Apukka Resortin live-kamerat, '
          'Rovaniemen sää ja 5 päivän ennuste, revontuliennuste (Kp-indeksi) sekä auringonnousu ja -lasku.',
    'fi_faq': [
      ('Onko Joulupukin Pajakylässä live-webkameraa?',
       'Kyllä. LeviTV (levitv.com/rovaniemi/) näyttää Joulupukin Pajakylän live-kameran napapiiriltä sekä Apukka Resortin '
       'revontulikameran, sään ja revontuliennusteen.'),
      ('Näkyvätkö revontulet Rovaniemellä?',
       'Kyllä, usein. Revontulia voi nähdä elokuun lopulta huhtikuun alkuun pimeinä ja kirkkaina öinä, jo noin Kp-indeksillä 2–3. '
       'Mene pois kaupungin valoista ja katso pohjoiseen.'),
    ],
  },
  'helsinki': {
    'name': 'Helsinki', 'lat': 60.1699, 'lon': 24.9384, 'region': 'Helsinki, Finland',
    'type': 'City', 'wiki': 'https://en.wikipedia.org/wiki/Helsinki',
    'title': 'Helsinki Live Webcams, Weather & Harbour Cams — LeviTV',
    'desc': 'Watch Helsinki live: Market Square and Port of Helsinki webcams, weather now from Kaisaniemi, '
            '5-day forecast, northern lights (Kp) and daylight.',
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
    'fi_faq': [
      ('Missä näen Helsingin webkamerat livenä?',
       'LeviTV:ssä (levitv.com/helsinki/). Sivu kierrättää Kauppatorin sekä Helsingin Sataman Etelä- ja Länsisataman live-kameroita.'),
      ('Näkyvätkö revontulet Helsingissä?',
       'Joskus. Helsinki on kaukana revontulivyöhykkeen eteläpuolella, joten revontulet näkyvät yleensä vain voimakkaalla '
       'aktiivisuudella (noin Kp 4–5 tai enemmän) pimeinä ja kirkkaina öinä, matalalla pohjoisessa.'),
    ],
  },
}

E = html.escape

def location_cams():
    """{loc: [(id, name, label)]} from the LOCS block of the template."""
    out, loc = {}, None
    for line in TEMPLATE.splitlines():
        m = re.match(r"  (\w+)\s*:\s*\{\s*$", line)
        if m:
            loc = m.group(1)
        c = re.search(r"\{id:'([\w-]{11})',\s*n:'([^']*)',\s*l:'([^']*)'", line)
        if c and loc:
            clean = lambda t: html.unescape(re.sub(r'<[^>]*>', ' ', t)).strip()
            out.setdefault(loc, []).append((c.group(1), clean(c.group(2)), clean(c.group(3))))
    return out

CAMS = location_cams()
for k, L in LOCATIONS.items():
    if len(CAMS.get(k, [])) != len(L['cams']):
        print(f"warning: {k} has {len(CAMS.get(k, []))} cameras in LOCS but {len(L['cams'])} in build.py: update the SEO texts")
    for cam_id, n, _ in CAMS.get(k, []):
        if cam_id not in CAM_UPLOADED:
            print(f'warning: no CAM_UPLOADED date for {n} ({cam_id}): it is left out of the structured data')

def about_html(k, L):
    url = f'{SITE}/{k}/'
    others = ' · '.join(f'<a href="/{o}/">{E(LOCATIONS[o]["name"])} live</a>' for o in LOCATIONS if o != k)
    return f'''<section id="about" aria-labelledby="about-h1">
    <h1 id="about-h1">{E(L['h1'])}</h1>
    {''.join(f'<p>{E(p)}</p>' for p in L['intro'])}
    <h2>{E(L['cams_title'])}</h2>
    <ul>{''.join(f'<li>{E(c)}</li>' for c in L['cams'])}</ul>
    <h2>What <span class="nm">LeviTV</span> shows</h2>
    <ul>{''.join(f'<li><strong>{E(a)}:</strong> {E(b)}</li>' for a, b in L['data'])}</ul>
    <h2>Frequently asked questions</h2>
    {''.join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in L['faq'])}
    <h2 lang="fi">{E(L['fi_title'])}</h2>
    <p lang="fi">{E(L['fi'])}</p>
    <div lang="fi">{''.join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in L['fi_faq'])}</div>
    <p>More live views: {others} · <a href="/">LeviTV home</a> · TV view: <a href="/{k}/full/">{url}full/</a></p>
  </section>'''

def video_ld(k, L):
    url = f'{SITE}/{k}/'
    return [{'@type': 'VideoObject', '@id': f'{url}#cam-{cam_id}', 'name': f'{label} live webcam',
             'description': f'Live webcam: {label}, {L["region"]}. Streamed around the clock on LeviTV.',
             'thumbnailUrl': f'https://i.ytimg.com/vi/{cam_id}/hqdefault_live.jpg',
             'uploadDate': CAM_UPLOADED[cam_id], 'embedUrl': f'https://www.youtube.com/embed/{cam_id}',
             'contentLocation': {'@id': url + '#place'},
             'publication': {'@type': 'BroadcastEvent', 'isLiveBroadcast': True, 'startDate': CAM_UPLOADED[cam_id]}}
            for cam_id, _, label in CAMS.get(k, []) if cam_id in CAM_UPLOADED]

def jsonld(k, L):
    url = f'{SITE}/{k}/'
    geo = {'@type': 'GeoCoordinates', 'latitude': L['lat'], 'longitude': L['lon']}
    if L.get('elevation'):
        geo['elevation'] = L['elevation']
    address = {'@type': 'PostalAddress', 'addressLocality': L['region'].split(',')[0], 'addressCountry': 'FI'}
    if 'Lapland' in L['region']:
        address['addressRegion'] = 'Lapland'
    videos = video_ld(k, L)
    return {
      '@context': 'https://schema.org',
      '@graph': [
        {'@type': 'WebSite', '@id': f'{SITE}/#website', 'url': f'{SITE}/', 'name': 'LeviTV', 'publisher': {'@id': f'{SITE}/#org'}},
        {'@type': 'Organization', '@id': f'{SITE}/#org', 'name': 'OOMF Marketing Oy', 'url': f'{SITE}/', 'email': 'hello@oomf.fi',
         'logo': f'{SITE}/apple-touch-icon.png'},
        {'@type': 'WebPage', '@id': url, 'url': url, 'name': L['title'], 'description': L['desc'],
         'inLanguage': 'en', 'isPartOf': {'@id': f'{SITE}/#website'}, 'about': {'@id': url + '#place'},
         'publisher': {'@id': f'{SITE}/#org'}, 'dateModified': DATE_TOKEN,
         'hasPart': [{'@id': v['@id']} for v in videos],
         'primaryImageOfPage': f'{SITE}/og.png',
         'breadcrumb': {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'LeviTV', 'item': f'{SITE}/'},
            {'@type': 'ListItem', 'position': 2, 'name': f'{L["name"]} live', 'item': url}]}},
        {'@type': [L['type'], 'TouristDestination'], '@id': url + '#place', 'name': L['name'], 'sameAs': L['wiki'],
         'address': address, 'geo': geo},
        *videos,
        {'@type': 'FAQPage', '@id': url + '#faq', 'inLanguage': 'en',
         'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in L['faq']]},
        {'@type': 'FAQPage', '@id': url + '#faq-fi', 'inLanguage': 'fi',
         'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in L['fi_faq']]},
      ]}

def seo_head(k, L):
    url = f'{SITE}/{k}/'
    first_cam = CAMS[k][0][0]
    return f'''<!--SEO:start-->
<link rel="preconnect" href="https://i.ytimg.com">
<link rel="preconnect" href="https://www.youtube.com">
<link rel="preload" as="image" href="https://i.ytimg.com/vi/{first_cam}/hqdefault_live.jpg" fetchpriority="high">
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
<meta property="og:image:alt" content="LeviTV: {E(L['name'])} live">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="geo.position" content="{L['lat']};{L['lon']}">
<meta name="geo.placename" content="{E(L['name'])}, Finland">
<script type="application/ld+json">{json.dumps(jsonld(k, L), ensure_ascii=False)}</script>
<script>window.INFOTV_LOC='{k}';</script>
<!--SEO:end-->'''

# Older TV browsers (Samsung Tizen 4+ = Chromium 56, LG webOS) don't understand
# ?. / ?? / ??= — esbuild rewrites the inline scripts of the generated pages.
ESBUILD = (os.environ.get('ESBUILD') or shutil.which('esbuild')
           or next((p for p in ['/tmp/claude-0/esb/node_modules/.bin/esbuild',
                                os.path.join(ROOT, 'node_modules/.bin/esbuild')] if os.path.exists(p)), None))
TARGET = 'chrome56'


def legacy(page):
    if not ESBUILD:
        print('warning: esbuild not found — pages keep modern JS (npm i esbuild)')
        return page
    def fix(m):
        attrs, code = m.group(1), m.group(2)
        if 'src=' in attrs or 'ld+json' in attrs or not code.strip():
            return m.group(0)
        r = subprocess.run([ESBUILD, '--loader=js', f'--target={TARGET}', '--log-level=error'],
                           input=code, capture_output=True, text=True)
        if r.returncode:
            raise SystemExit('esbuild failed:\n' + r.stderr)
        return f'<script{attrs}>\n{r.stdout}</script>'
    return re.sub(r'<script([^>]*)>(.*?)</script>', fix, page, flags=re.S)


# /tv.html: the live app for TV apps (Samsung, Android TV) — same as levi-infotv.html,
# but with TV-browser-safe JavaScript and kept out of search results
tv = legacy(TEMPLATE).replace('<!DOCTYPE html>', '<!DOCTYPE html>\n<!-- Generated by build.py from levi-infotv.html — do not edit -->', 1)
tv = tv.replace('<meta charset="UTF-8">', '<meta charset="UTF-8">\n<meta name="robots" content="noindex,follow">', 1)
open(os.path.join(ROOT, 'tv.html'), 'w', encoding='utf-8').write(tv)

def stamp_date(path, page):
    """Keep the old dateModified while the page content is unchanged, so lastmod stays truthful."""
    pattern = r'("dateModified": ")(\d{4}-\d{2}-\d{2}|' + DATE_TOKEN + ')'
    old = open(path, encoding='utf-8').read() if os.path.exists(path) else ''
    m = re.search(pattern, old)
    same = m and re.sub(pattern, r'\g<1>' + DATE_TOKEN, old) == page
    date = m.group(2) if same else TODAY
    return page.replace(DATE_TOKEN, date), date

lastmod = {}
for k, L in LOCATIONS.items():
    page = re.sub(r'<!--SEO:start-->.*?<!--SEO:end-->', lambda m: seo_head(k, L), TEMPLATE, flags=re.S)
    page = re.sub(r'<!--ABOUT:start-->.*?<!--ABOUT:end-->',
                  lambda m: '<!--ABOUT:start-->' + about_html(k, L) + '<!--ABOUT:end-->', page, flags=re.S)
    page = page.replace('<!DOCTYPE html>', '<!DOCTYPE html>\n<!-- Generated by build.py from levi-infotv.html — edit the template, then run: python3 build.py -->', 1)
    page = legacy(page)
    os.makedirs(os.path.join(ROOT, k), exist_ok=True)
    page, lastmod[k] = stamp_date(os.path.join(ROOT, k, 'index.html'), page)
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

# sitemap: hand-written pages get their date from git
git = lambda *a: subprocess.run(['git', *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
git_date = lambda p: TODAY if git('status', '--porcelain', p) else (git('log', '-1', '--format=%cs', '--', p) or TODAY)
urls = ([(f'{SITE}/', git_date('index.html'))] + [(f'{SITE}/{k}/', lastmod[k]) for k in LOCATIONS]
        + [(f'{SITE}/yrityksille/', git_date('yrityksille/index.html'))])
open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write(
  '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
  + ''.join(f'  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n' for u, d in urls)
  + '</urlset>\n')

# llms-full.txt: the same facts as the location pages, in plain text for AI assistants
full = ['# LeviTV: full guide', '',
        '> LeviTV (levitv.com) is a free, independent real-time view of Levi in Finnish Lapland, with live views of Ylläs, '
        'Rovaniemi and Helsinki. Made by OOMF Marketing Oy. Works on phones, computers and TVs with no login.', '']
for k, L in LOCATIONS.items():
    full += [f"## {L['name']} ({SITE}/{k}/)", '', *L['intro'], '', f"### {L['cams_title']}", '', *[f'- {c}' for c in L['cams']], '',
             '### What LeviTV shows', '', *[f'- {a}: {b}' for a, b in L['data']], '', '### Questions and answers', '']
    for q, a in L['faq']:
        full += [f'**{q}**', a, '']
    full += [f"### {L['fi_title']}", '', L['fi'], '']
    for q, a in L['fi_faq']:
        full += [f'**{q}**', a, '']
open(os.path.join(ROOT, 'llms-full.txt'), 'w', encoding='utf-8').write('\n'.join(full).rstrip() + '\n')
print('built:', ', '.join(f'/{k}/' for k in LOCATIONS), '+ tv.html + sitemap.xml + llms-full.txt')
