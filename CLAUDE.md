# LeviTV — notes for Claude

> This repo is public (and served by GitHub Pages): keep prices, customer data and secrets out of it.

LeviTV (levitv.com) is a real-time info TV for Levi, Ylläs, Rovaniemi and Helsinki: live cameras, weather,
aurora, daylight, slope status, ads, and (new) each business customer's own content. Owner: Lassi Nummi,
OOMF Marketing Oy (hello@oomf.fi). **Talk to Lassi in Finnish, casually and directly.** Keep code, comments,
commit messages and on-screen texts in English (TV UI is English; customer admin `/hallinta/` is Finnish).

## How the site is built
- `levi-infotv.html` is the **one template** for every view (mobile, `view=tv`, `view=full`). Location config is the
  `LOCS` block (name, sub, lat/lon, fmisid, cams, ticker, ads, kp, mark, site).
- After **any** edit to the template run `python3 build.py`. It generates `/levi/ /yllas/ /rovaniemi/ /helsinki/`,
  their `/full/` redirects, `sitemap.xml` and `tv.html` (esbuild-transpiled to chrome56 for old Samsung/LG browsers;
  install esbuild with npm if missing). Commit the generated files too.
- `config.js`: analytics (Umami), ad target URLs (`lwa, edmc, haus, oomf`, routed via `go.html`), `api` (customer API base).
- Brand V9: dark arctic theme (#06111D, #0B1B2B, #F2F6FA, #ADC4D5, glacier #76C7EF, sun #FFB366, lines #37556A),
  Literata (self-hosted, `fonts/literata`) for headings, system sans for UI. Product name is always **"LeviTV"**;
  the place goes in the brand-sub row. Logos in `brand/`.
- Hosting today: **GitHub Pages** (`CNAME` → levitv.com). `_headers` / `_redirects` are prepared for Cloudflare Pages.

## Cameras
- YouTube IFrame API, double buffer with single-player fallback, thumbnail cover while buffering, watchdogs,
  TV pages reload if hidden >10 min or no video for 4 min (max once / 15 min). Errors 100/101/150 skip a cam 30 min.
- `scripts/check_streams.py` (workflow `streams.yml`, daily 07:17) writes `cam-status.json`; offline cams are skipped
  24 h and an issue is opened. Data-centre checks are unreliable: only specific reasons count as offline, plus a >50 % sanity check.

## Slope data
External Grok bot writes `slopes.json` to the **`data` branch** (every 30 min 06:30–21:00). Per location:
`slopesOpen/Total, liftsOpen/Total, snowDepthCm, openSlopes[{name,difficulty,hours}], openLifts, updated`.
Older than 6 h is hidden. Never push to `data` yourself.

## Customer content (new, Oct 2026)
- API: `functions/api/[[path]].js` — Cloudflare Pages Function, KV binding `DB`, secret `ADMIN_KEY`. Endpoints documented in the file header.
- `/hallinta/` customer admin (login = one-time link `#t=<token>`), `/hallinta/admin.html` OOMF admin (ADMIN_KEY),
  `hallinta/schedule.js` shared ES5 schedule logic (also loaded by the TV page).
- TV page: `?c=CODE` or the app setting → `loadCustomer()`; customer banners replace LeviTV ads (`.cx-off`), logo goes to `#tag`,
  ticker lines go first. All customer text is escaped.
- Local test: `npx wrangler pages dev . --kv DB --binding ADMIN_KEY=<16+ chars>` and point `config.js → api` at it. `.wrangler/` is gitignored.

## TV apps
- **Android TV** (`android/`, package `com.levitv.app`, GeckoView 140–149, minSdk 26, TV-only/leanback).
  Native menu (OK): location, layout, customer code, start on boot, reload, diagnostics. Workflow `android.yml` on
  `android/**` changes: signed build from secrets, release `app-v1.0.<run>` with `levitv.apk` + `levitv.aab`;
  optional Play internal upload if secret `PLAY_SERVICE_ACCOUNT_JSON` exists (`vars.PLAY_RELEASE_STATUS`, default draft).
- **Samsung Tizen** (`tizen/`) and **LG webOS** (`webos/`, workflow `webos.yml` → `lg-v1.0.N`): start screen →
  `tv.html?app=tizen|webos`; settings menu inside the page (OK key), incl. customer code entry.
- Play assets: `android/play-assets/` (icon 512, feature graphic, TV banner).

## Rules
- **Never commit keystores, `*.jks`, passwords, service-account JSON or ADMIN_KEY.** The upload keystore
  (alias `levitv-upload`) lives in Lassi's password manager; signing comes from GitHub secrets.
- Don't publish store releases, change Play Console / Cloudflare settings, or send anything on Lassi's behalf without asking.
- After changes: run `build.py`, check the page renders (Playwright screenshot at 1920×1080 and a phone width), then commit and push to `main`.

## Open items (25 Oct 2026)
1. **Google Play production:** fill App content + store listing (EN default, FI translation), add Android TV form factor,
   create the production release with **1.0.25** (has customer code), send for review. Give Google a demo customer code under "Sign-in details".
2. **Cloudflare:** create Pages project `levitv` from this repo (no build, output `/`, preview branches None), KV `levitv` bound as `DB`,
   secret `ADMIN_KEY`, redeploy. Steps in README → "Customer content". If the address isn't `levitv.pages.dev`, update `config.js → api`.
   Later: move levitv.com DNS (GoDaddy) to Cloudflare, then `api` can be `https://levitv.com`.
3. After Play approval: point `levitv.com/app` to the Play listing (now redirects to the APK).
4. Open question for sales: agreement with Levi ski resort on slope data / brand use.
