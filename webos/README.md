# LeviTV for LG TV (webOS)

A small webOS web app: a dark start-up screen that opens `https://levitv.com/tv.html?app=webos`.
Everything else lives on the website, so changes reach every TV without reinstalling.

Remote: **OK** = settings (location, layout, diagnostics, reload) · **◀ ▶** = camera ·
**Back** = close the menu / exit. Works on LG TVs from 2018 onwards (webOS 4+).

GitHub Actions builds `levitv-lg.ipk` on every change (Releases → `lg-v1.0.x`).

## Install on your own TV (developer mode)

1. Create a free account at https://webostv.developer.lge.com and sign in to it on the TV.
2. TV: LG Content Store → install **Developer Mode** → open it → Dev Mode Status **On** →
   the TV restarts. Open the app again and turn **Key Server** on; note the IP and passphrase.
   (Dev mode expires after 50 h — press *Extend* in the app.)
3. Computer: `npm i -g @webos-tools/cli`, then
   `ares-setup-device` → add the TV (its IP, port 9922, user `prisoner`) →
   `ares-novacom --device tv --getkey` (enter the passphrase).
4. `ares-install --device tv levitv-lg.ipk` and `ares-launch --device tv com.levitv.app`.

## Publish (LG Content Store)

Sign in to the LG Seller Lounge (https://seller.lgappstv.com) with an OOMF Marketing Oy
seller account, upload the `.ipk`, screenshots and the icons in `android/play-assets/`.
LG reviews TV apps before they go live.
