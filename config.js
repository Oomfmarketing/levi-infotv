/* Info TV — shared settings for levi-infotv.html and go.html.
   Edit this file; no other change is needed. */
window.INFOTV = {

  // Cookieless analytics. Leave provider empty to turn analytics off.
  //   Umami Cloud:  provider:'umami',     id:'<website id>'
  //   Plausible:    provider:'plausible', id:'<your domain, e.g. levi.tv>'
  analytics: { provider: 'umami', id: 'ced80469-2f42-45f0-8153-00f6fa4c2f66', src: '' },

  // Customer content API (Cloudflare Pages Functions, see functions/api and README).
  // Screens with a customer code load their banners and logo from here; /hallinta/ edits them.
  // After levitv.com itself moves to Cloudflare this can be 'https://levitv.com'.
  api: 'https://levitv.pages.dev',

  // How often each TV/full screen reports that it is online (minutes).
  heartbeatMinutes: 60,

  // Ad targets. QR codes point to go.html?a=<key>, which records the scan
  // and forwards here (http links get utm_* parameters added).
  ads: {
    lwa:  'https://laplandwinteractivities.com',
    edmc: 'https://elamysdmc.com',
    haus: 'https://levi.haus',
    oomf: 'mailto:hello@oomf.fi?subject=LeviTV%20advertising',
  },
};
