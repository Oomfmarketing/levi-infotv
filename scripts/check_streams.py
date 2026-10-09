#!/usr/bin/env python3
"""Daily check of every LeviTV camera stream (run by .github/workflows/streams.yml).

Reads the camera list from levi-infotv.html, asks YouTube whether each stream is
live and embeddable, and writes cam-status.json. The page skips cameras marked
"offline" there, so a dead stream never shows up on the screens.
Writes a markdown summary to stream-report.md for the GitHub issue.
"""
import json, re, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = (ROOT / 'levi-infotv.html').read_text(encoding='utf-8')
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')


def cameras():
    """[(loc, id, name)] from the LOCS block."""
    out, loc = [], None
    for line in HTML.splitlines():
        m = re.match(r"  (\w+)\s*:\s*\{\s*$", line)   # "  levi: {" opens a location
        if m:
            loc = m.group(1)
        c =re.search(r"\{id:'([\w-]{11})',\s*n:'([^']*)'", line)
        if c:
            out.append((loc or '?', c.group(1), c.group(2).replace('&amp;', '&')))
    return out


def get(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9',
        'Cookie': 'CONSENT=YES+1; SOCS=CAI'})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception as e:  # network trouble → unknown, never "offline"
        return 0, str(e)


def player_response(page):
    m = re.search(r'ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;\s*(?:var |</script>)', page, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except ValueError:
        return None


CLIENTS = [  # InnerTube clients that usually skip the bot check on data-centre IPs
    {'clientName': 'WEB_EMBEDDED_PLAYER', 'clientVersion': '1.20250310.01.00'},
    {'clientName': 'TVHTML5_SIMPLY_EMBEDDED_PLAYER', 'clientVersion': '2.0'},
    {'clientName': 'ANDROID_VR', 'clientVersion': '1.62.27', 'androidSdkVersion': 32},
    {'clientName': 'IOS', 'clientVersion': '20.10.4', 'deviceModel': 'iPhone16,2'},
]


def innertube(vid):
    for c in CLIENTS:
        body = json.dumps({'videoId': vid, 'context': {
            'client': dict(c, hl='en', gl='FI'),
            'thirdParty': {'embedUrl': 'https://levitv.com/'}}}).encode()
        req = urllib.request.Request(
            'https://www.youtube.com/youtubei/v1/player?prettyPrint=false', data=body,
            headers={'Content-Type': 'application/json', 'User-Agent': UA})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                pr = json.loads(r.read().decode('utf-8', 'replace'))
        except Exception:
            continue
        ps = json.dumps(pr.get('playabilityStatus', {})).lower()
        if 'bot' in ps or 'sign in' in ps:
            continue
        return pr
    return None


def check(vid):
    code, _ = get(f'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json')
    if code in (401, 403):
        return 'offline', 'embedding disabled by the channel'
    if code == 404:
        return 'offline', 'video removed or private'
    code, page = get(f'https://www.youtube.com/watch?v={vid}')
    pr = player_response(page) if code == 200 else None
    if not pr or 'bot' in json.dumps(pr.get('playabilityStatus', {})).lower():
        pr = innertube(vid)
    if not pr:
        return 'unknown', 'YouTube bot check'
    ps = pr.get('playabilityStatus', {})
    status, reason = ps.get('status', '?'), ps.get('reason', '')
    # Only trust specific reasons: a data-centre IP often gets a generic
    # "This video is unavailable" for streams that play fine on real screens.
    if status in ('ERROR', 'UNPLAYABLE'):
        if re.search(r'recording is not available|has ended|removed|private|terminated|no longer available', reason, re.I):
            return 'offline', reason
        return 'unknown', reason or status
    live = (pr.get('microformat', {}).get('playerMicroformatRenderer', {})
              .get('liveBroadcastDetails', {}))
    vd = pr.get('videoDetails', {})
    if live.get('endTimestamp') and not live.get('isLiveNow'):
        return 'offline', 'live stream has ended'
    if status == 'OK' and (live.get('isLiveNow') or vd.get('isLive')):
        return 'live', ''
    if status == 'LIVE_STREAM_OFFLINE':
        return 'offline', reason or 'stream offline'
    if status == 'OK' and not vd.get('isLiveContent'):
        return 'offline', 'not a live stream (plain video)'
    return 'unknown', f'{status} {reason}'.strip()


def main():
    cams = cameras()
    if not cams:
        sys.exit('no cameras found in levi-infotv.html')
    result, rows = {}, []
    for loc, vid, name in cams:
        state, why = check(vid)
        result[vid] = {'loc': loc, 'name': name, 'state': state, 'reason': why}
        rows.append((loc, name, vid, state, why))
        print(f'{loc:9} {name:18} {vid}  {state:8} {why}')
        time.sleep(1.5)

    # sanity check: if most cameras look offline, the check itself is blocked
    if sum(r['state'] == 'offline' for r in result.values()) > len(result) / 2:
        for r in result.values():
            if r['state'] == 'offline':
                r['state'], r['reason'] = 'unknown', 'check blocked? ' + r['reason']
    out = ROOT / 'cam-status.json'
    old = {}
    if out.exists():
        try:
            old = json.loads(out.read_text()).get('cams', {})
        except ValueError:
            pass
    # an "unknown" (YouTube blocked the check) keeps yesterday's verdict
    for vid, r in result.items():
        if r['state'] == 'unknown' and old.get(vid, {}).get('state') in ('live', 'offline') \
                and 'kept' not in old[vid].get('reason', ''):
            r['state'] = old[vid]['state']
            r['reason'] = (old[vid].get('reason') or '') + ' (kept from last check)'
    out.write_text(json.dumps({
        'checked': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ'),
        'cams': result}, ensure_ascii=False, indent=1) + '\n')

    bad = [r for r in rows if result[r[2]]['state'] != 'live']
    lines = ['Daily LeviTV camera check. Cameras marked **offline** are skipped on the screens '
             'automatically until they come back. Replace or remove them in `levi-infotv.html` '
             '(LOCS → cams) if they stay down.', '',
             '| Location | Camera | State | Reason |', '|---|---|---|---|']
    for loc, name, vid, _, _ in bad:
        r = result[vid]
        lines.append(f'| {loc} | [{name}](https://www.youtube.com/watch?v={vid}) | {r["state"]} | {r["reason"]} |')
    (ROOT / 'stream-report.md').write_text('\n'.join(lines) + '\n')
    offline = sum(1 for r in result.values() if r['state'] == 'offline')
    print(f'\n{len(rows)} cameras, {offline} offline, '
          f'{sum(1 for r in result.values() if r["state"] == "unknown")} unknown')
    # tell the workflow whether to open/close the issue
    with open(ROOT / '.stream-offline-count', 'w') as f:
        f.write(str(offline))


if __name__ == '__main__':
    main()
