# LeviTV.com — your real-time view of Levi

LeviTV — a single HTML file (`levi-infotv.html`) for 1920×1080 screens.
It scales to any TV and switches to a scrolling mobile layout on phones (≤ 900 px wide).

Locations (pick with `?loc=`):

- Levi: https://oomfmarketing.github.io/levi-infotv/levi-infotv.html?loc=levi
- Ylläs: https://oomfmarketing.github.io/levi-infotv/levi-infotv.html?loc=yllas
- Helsinki: https://oomfmarketing.github.io/levi-infotv/levi-infotv.html?loc=helsinki

Add `&view=full` for the full-screen layout: the whole camera picture is shown
uncropped (1520×855, nothing on top of it), with the information in a sidebar and
the camera name, ad and ticker below the picture. TV and full views always keep
the 1920×1080 canvas, even on small screens. Click or press F to go full screen.

Picker page: https://oomfmarketing.github.io/levi-infotv/

Short links: `/levi/`, `/levi/full/`, `/yllas/`, `/yllas/full/`, `/helsinki/`, `/helsinki/full/`.
Add `?screen=<name>` to name a physical TV in analytics, e.g. `/levi/full/?screen=hotel-lobby`.

## Search engines & AI search

- Location pages have their own title, description, canonical URL, Open Graph
  tags, JSON-LD (WebPage, TouristDestination, FAQPage, breadcrumbs) and a
  crawlable text section (English + Finnish) shown on mobile.
- Home page: WebSite, Organization and FAQPage JSON-LD plus visible FAQ.
- `robots.txt` allows all crawlers including AI ones (GPTBot, OAI-SearchBot,
  ClaudeBot, PerplexityBot, Google-Extended…); `sitemap.xml`; `llms.txt` summary.
- TV / full-screen views are `noindex` and point canonically to the location page.

## Analytics

Cookieless, so no consent banner is needed. Set it up in `config.js`:

- Umami Cloud: `analytics: { provider:'umami', id:'<website id>' }`
- Plausible: `analytics: { provider:'plausible', id:'<domain>' }`

What is recorded:

| Event | When | Props |
|---|---|---|
| pageview | page opens | URL incl. `loc`, `view` |
| `screen_online` | every `heartbeatMinutes` (default 60) on TV / full views | `loc`, `view`, `screen` |
| `qr_scan` | someone scans an ad QR code (via `go.html`) | `ad`, `loc`, `screen` |
| `ad_click` | someone taps an ad (mobile) | `ad`, `loc`, `screen` |
| `camera_pick` | camera chosen on mobile | `cam`, `loc` |

Ad links and QR codes carry `utm_source=infotv`, `utm_medium=qr|screen`,
`utm_campaign=<location>`, `utm_content=<screen>`, so advertisers see the traffic
in their own analytics too. Ad targets live in `config.js` (`ads`).

## Data sources (all free, no API keys)

| What | Source |
|---|---|
| Weather now | FMI observations: Levi `fmisid=101886`, Helsinki Kaisaniemi `100971`; Ylläs uses the FMI forecast for the current hour |
| Forecast, cloud cover | FMI forecast for the location's coordinates |
| Northern lights | NOAA SWPC planetary Kp + Kp forecast |
| Sunrise / sunset / night mode | Calculated in the browser |
| Cameras | Levi YouTube live streams (two players, crossfaded) |

## Editing

`levi-infotv.html` is the template. The location pages `/levi/`, `/yllas/` and
`/helsinki/` are generated from it — **after editing it, run `python3 build.py`**
(location texts, FAQs and SEO data live in `build.py`).


At the top of the `<script>` block:

- `LOCS` holds every location: name, coordinates, FMI station, cameras,
  ticker lines and ad banners. Add a new location by copying one block.
- `SLOPE_FEED_URL` is an optional live slope and lift feed (see below).

## Slope & lift status in the ticker

levi.fi loads slope and lift status in the browser, and there is no public API.
The ticker is ready for a feed: set `SLOPE_FEED_URL` to a URL that returns

```json
{"slopesOpen": 12, "slopesTotal": 43, "liftsOpen": 8, "liftsTotal": 26}
```

and the ticker shows "Slopes open 12/43 · Lifts open 8/26" first, refreshed every 10 minutes.
The feed can be a small Cloudflare Worker that reads Levi's own data source
(with Levi Ski Resort's permission) and returns that JSON with CORS enabled.
