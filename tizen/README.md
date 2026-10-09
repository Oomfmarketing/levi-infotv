# LeviTV for Samsung TV (Tizen)

A small Tizen web app: a dark start-up screen that turns the TV's screen saver off and
opens `https://levitv.com/tv.html?app=tizen`. Everything else lives on the website, so
changes to levitv.com reach every TV without reinstalling.

Remote: **OK** = settings (location, layout, diagnostics, reload) · **◀ ▶** = camera ·
**Back** = close the menu / exit.

Works on Samsung TVs from 2018 onwards (Tizen 4.0+).

## Install on your own TV (developer mode)

1. Install **Tizen Studio** with the **TV Extensions** and the **Samsung Certificate Extension**
   (Package Manager → Extension SDK).
2. TV: Apps → type `12345` on the remote → Developer mode **On**, Host PC IP = your computer's IP → restart the TV.
3. Tizen Studio → Certificate Manager → **+** → *Samsung* → *TV* → sign in with the Samsung
   account → create the author and distributor certificates (add the TV's DUID — the
   Device Manager shows it once the TV is connected).
4. Device Manager → Remote Device Manager → **+** → the TV's IP → connect.
5. File → Import → Tizen → Tizen Project → this `tizen` folder → right-click the project →
   **Run As → Tizen Web Application**.

## Publish (Samsung Apps TV)

Needs a Samsung Apps TV Seller Office partner account (https://seller.samsungapps.com/tv/)
for OOMF Marketing Oy. Build a signed `.wgt` with the distributor certificate from the
seller account (Project → Build Signed Package) and upload it with screenshots and the
icon in `android/play-assets/`. Samsung reviews TV apps before they go live.
