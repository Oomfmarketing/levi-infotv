/* Info TV — shared settings for levi-infotv.html and go.html.
   Edit this file; no other change is needed. */
window.INFOTV = {

  // Cookieless analytics. Leave provider empty to turn analytics off.
  //   Umami Cloud:  provider:'umami',     id:'<website id>'
  //   Plausible:    provider:'plausible', id:'<your domain, e.g. levi.tv>'
  analytics: { provider: '', id: '', src: '' },

  // How often each TV/full screen reports that it is online (minutes).
  heartbeatMinutes: 60,

  // Ad targets. QR codes point to go.html?a=<key>, which records the scan
  // and forwards here (http links get utm_* parameters added).
  ads: {
    lwa:  'https://laplandwinteractivities.com',
    edmc: 'https://elamysdmc.com',
    oomf: 'mailto:hello@oomf.fi?subject=Info%20TV%20advertising',
  },
};
