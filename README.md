# levi-infotv

Levi Info TV — a single HTML file (`levi-infotv.html`) for 1920×1080 screens.
It scales to any TV and switches to a scrolling mobile layout on phones (≤ 900 px wide).

Live: https://oomfmarketing.github.io/levi-infotv/levi-infotv.html

## Data sources (all free, no API keys)

| What | Source |
|---|---|
| Weather now | FMI observations, station `fmisid=101886` (Kittilä Kenttärova) |
| Forecast, cloud cover | FMI forecast for 67.8009 N, 24.8009 E |
| Northern lights | NOAA SWPC planetary Kp + Kp forecast |
| Sunrise / sunset / night mode | Calculated in the browser |
| Cameras | Levi YouTube live streams (two players, crossfaded) |

## Editing

At the top of the `<script>` block:

- `TICKER` holds the footer ticker lines. Edit freely.
- `CAMS` holds the camera list.
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
