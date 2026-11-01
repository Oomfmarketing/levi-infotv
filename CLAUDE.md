# LeviTV — notes for Claude

> This repo is public (and served by GitHub Pages): keep customer data, prospect lists, internal notes and secrets out of it.
> Public list prices live on `/yrityksille/` (B2B page, Finnish); change them only when Lassi says so.

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
- Hosting today: **GitHub Pages** (`CNAME` → levitv.com). The Cloudflare Worker `levitv` serves the same files plus the API, and uses `_headers` / `_redirects`.
- DNS: levitv.com is registered at GoDaddy, nameservers and records at Cloudflare. A and `www` records must stay **DNS only** (grey cloud), the site is served by GitHub Pages. oomf.fi mail (Google) is separate.

## Cameras
- YouTube IFrame API, double buffer with single-player fallback, thumbnail cover while buffering, watchdogs,
  TV pages reload if hidden >10 min or no video for 4 min (max once / 15 min). Errors 100/101/150 skip a cam 30 min.
- `scripts/check_streams.py` (workflow `streams.yml`, daily 07:17) writes `cam-status.json`; offline cams are skipped
  24 h and an issue is opened. Data-centre checks are unreliable: only specific reasons count as offline, plus a >50 % sanity check.

- SEO: a new camera needs its YouTube upload date in `CAM_UPLOADED` and the texts in `LOCATIONS` (both in `build.py`); the build warns if they are out of sync.

## Slope data
External Grok bot writes `slopes.json` to the **`data` branch** (every 30 min 06:30–21:00). Per location:
`slopesOpen/Total, liftsOpen/Total, snowDepthCm, openSlopes[{name,difficulty,hours}], openLifts, updated`.
Older than 6 h is hidden. Never push to `data` yourself.

## Customer content (new, Oct 2026)
- API: `functions/api/[[path]].js`, called from `worker.js` — Cloudflare Worker `levitv` (`wrangler.jsonc`), KV binding `DB`, secret `ADMIN_KEY`. Endpoints documented in the file header.
- `.assetsignore` lists what the Worker must not serve: add anything new that should stay private. `levitv.pages.dev` is an unrelated third-party site, never use it.
- `/hallinta/` customer admin (login = one-time link `#t=<token>`), `/hallinta/admin.html` OOMF admin (ADMIN_KEY),
  `hallinta/schedule.js` shared ES5 schedule logic (also loaded by the TV page).
- `/hallinta/ohje.html` customer guide (sizes: logo 600×160 PNG, banner image 16:9 640×360, tag ≤14, title ≤45, text ≤100, ticker ≤120 chars).
  The admin form shows counters with the same limits; the TV clamps titles to one line and texts to two.
- Lead form on `/yrityksille/#yhteys` → `POST /api/lead` (KV `lead:*`, honeypot `website`, 5/hour per IP). Leads show in `admin.html` → Yhteydenotot.
  Each lead also emails hello@oomf.fi from leads@levitv.com (`send_email` binding `MAIL`, restricted to that address; needs Email Routing, free). A failed email never loses the lead.
- TV page: `?c=CODE` or the app setting → `loadCustomer()`; customer banners replace LeviTV ads (`.cx-off`), logo goes to `#tag`,
  ticker lines go first. All customer text is escaped.
- Local test: `npx wrangler dev --var ADMIN_KEY:<16+ chars>` and point `config.js → api` at it. `.wrangler/` is gitignored.

## TV apps
- **Android TV** (`android/`, package `com.levitv.app`, GeckoView 140–149, minSdk 26, TV-only/leanback).
  Native menu (OK): location, layout, customer code, start on boot, reload, diagnostics. Workflow `android.yml` on
  `android/**` changes: signed build from secrets, release `app-v1.0.<run>` with `levitv.apk` + `levitv.aab`;
  optional Play internal upload if secret `PLAY_SERVICE_ACCOUNT_JSON` exists (`vars.PLAY_RELEASE_STATUS`, default draft).
- **Samsung Tizen** (`tizen/`) and **LG webOS** (`webos/`, workflow `webos.yml` → `lg-v1.0.N`): start screen →
  `tv.html?app=tizen|webos`; settings menu inside the page (OK key), incl. customer code entry.
- Play assets: `android/play-assets/` (icon 512, feature graphic, TV banner, `screenshots/` 1920×1080 with the ski-resort logo blurred,
  `play-listing.md` = every Play Console answer and the EN/FI store texts).

## Rules
- **Never commit keystores, `*.jks`, passwords, service-account JSON or ADMIN_KEY.** The upload keystore
  (alias `levitv-upload`) lives in Lassi's password manager; signing comes from GitHub secrets.
- Don't publish store releases, change Play Console / Cloudflare settings, or send anything on Lassi's behalf without asking.
- After changes: run `build.py`, check the page renders (Playwright screenshot at 1920×1080 and a phone width), then commit and push to `main`.

## Two places work on this repo
Lassi uses both a cloud Claude session (planning, docs, assets) and Claude Code on his Mac (Cloudflare, local tests, TV).
GitHub `main` is the only source of truth: **always `git pull` before starting and push when done**; never force-push.

## B2B page `/yrityksille/` (Finnish)
How it works, who it is for, pricing (485 € + VAT self-installed, 585 € installed, device 125 €; season 1.11.–31.5.; season price is per site, number of screens not limited; 585 € includes installing one screen, the rest by agreement), requirements,
advertising, FAQ, lead form. **No launch offer / free installation** (Lassi said no). No customer logos until a real customer agrees.
Product image `yrityksille/levitv-yrityksille.jpg` is a real screenshot with an example banner and a "Your logo" placeholder.

## Open items (1 Nov 2026, evening)
1. **Google Play production:** everything prepared in `android/play-assets/` (Grok bot fills the Console). Release **1.0.25**,
   Android TV form factor, Lassi sends for review himself. Add a demo customer code under "Sign-in details".
2. **Cloudflare:** live. Worker `levitv` (Workers Builds on `main`, `https://levitv.flat-cloud-8d4c.workers.dev`), KV `levitv` as `DB`,
   secret `ADMIN_KEY`. Test customer "Levihovi 1" (code E68CWB).
   Later: if the site moves from GitHub Pages to the Worker, `api` can be `https://levitv.com`.
3. Lead notifications by email: done and tested 1 Nov 2026.
4. B2B page phone: 040 513 2723 (header "Soita" on mobile, contact section, footer).
5. Demo customer "LeviTV Demo" with sample banners for sales and Google review.
6. After Play approval: point `levitv.com/app` to the Play listing (now redirects to the APK).
7. Possible: English `/business/` page; proof section once a first customer agrees.
8. Open question for sales: agreement with Levi ski resort on slope data / brand use.
