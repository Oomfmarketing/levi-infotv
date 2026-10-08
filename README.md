# levi-infotv

Levi Info TV — a single HTML file (`levi-infotv.html`) for 1920×1080 screens.
It scales to any TV and switches to a scrolling mobile layout on phones (≤ 900 px wide).

Locations (pick with `?loc=`):

- Levi: https://oomfmarketing.github.io/levi-infotv/levi-infotv.html?loc=levi
- Ylläs: https://oomfmarketing.github.io/levi-infotv/levi-infotv.html?loc=yllas
- Helsinki: https://oomfmarketing.github.io/levi-infotv/levi-infotv.html?loc=helsinki

Add `&view=full` for the full-screen layout: the camera fills the whole
1920×1080 screen and the information floats on top. TV and full views always keep
the 1920×1080 canvas, even on small screens. Click or press F to go full screen.

Picker page: https://oomfmarketing.github.io/levi-infotv/

## Data sources (all free, no API keys)

| What | Source |
|---|---|
| Weather now | FMI observations: Levi `fmisid=101886`, Helsinki Kaisaniemi `100971`; Ylläs uses the FMI forecast for the current hour |
| Forecast, cloud cover | FMI forecast for the location's coordinates |
| Northern lights | NOAA SWPC planetary Kp + Kp forecast |
| Sunrise / sunset / night mode | Calculated in the browser |
| Cameras | Levi YouTube live streams (two players, crossfaded) |

## Editing

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
