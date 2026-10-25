/* LeviTV customer content API — Cloudflare Pages Function.
 *
 * Bindings (Cloudflare dashboard → the Pages project → Settings):
 *   DB         KV namespace  (customers, codes, images)
 *   ADMIN_KEY  secret        (OOMF admin page; at least 16 characters)
 *
 * Public
 *   GET  /api/screen/:code      content for TV screens using that customer code
 *   GET  /api/img/:key          uploaded image
 * Customer (Authorization: Bearer <management link token>)
 *   GET  /api/me                own settings and content
 *   PUT  /api/me                save settings and content
 *   POST /api/me/image          upload an image (raw body, image/jpeg|png|webp)
 * OOMF (Authorization: Bearer <ADMIN_KEY>)
 *   GET    /api/admin/customers
 *   POST   /api/admin/customers              {name, email, loc, until}
 *   PUT    /api/admin/customers/:id          {name, email, loc, until, active}
 *   POST   /api/admin/customers/:id/link     new management link (old one stops working)
 *   DELETE /api/admin/customers/:id
 *
 * KV keys: cust:<id> → JSON · code:<CODE> → id · tok:<sha256(token)> → id · img:<id>-<rand> → bytes
 */

const LOCS = ['levi', 'yllas', 'rovaniemi', 'helsinki'];
const CODE_ABC = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';   // no 0/O, 1/I
const MAX_ITEMS = 30, MAX_IMG = 1.5 * 1024 * 1024;
const IMG_TYPES = { 'image/jpeg': 1, 'image/png': 1, 'image/webp': 1 };

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Authorization, Content-Type',
  'Access-Control-Max-Age': '86400',
};
const json = (data, status = 200, extra = {}) => new Response(JSON.stringify(data), {
  status, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...CORS, ...extra },
});
const fail = (status, error) => json({ error }, status);

function rand(n, abc) {
  const b = crypto.getRandomValues(new Uint8Array(n));
  if (abc) return Array.from(b, x => abc[x % abc.length]).join('');
  return btoa(String.fromCharCode(...b)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
async function sha256(s) {
  const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return Array.from(new Uint8Array(d), x => x.toString(16).padStart(2, '0')).join('');
}
function sameString(a, b) {           // constant-time compare
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  let r = 0; for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}
const bearer = req => (req.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '').trim();

// ── validation ─────────────────────────────────────────────────────
const str = (v, max) => String(v == null ? '' : v).replace(/[\u0000-\u001f\u007f]/g, ' ').trim().slice(0, max);
const isTime = v => /^([01]\d|2[0-3]):[0-5]\d$/.test(v) || v === '24:00';
const isDate = v => /^\d{4}-\d{2}-\d{2}$/.test(v);
const isUrl = v => /^https?:\/\/[^\s<>"]{3,}$/i.test(v);
const isImg = (v, id) => typeof v === 'string' && v.startsWith(id + '-') && /^[\w-]{6,80}$/.test(v);

function cleanItem(x, id) {
  if (!x || typeof x !== 'object') return null;
  const it = {
    id: /^[\w-]{4,24}$/.test(x.id || '') ? x.id : rand(6, CODE_ABC.toLowerCase()),
    place: x.place === 'ticker' ? 'ticker' : 'banner',
    on: x.on !== false,
    tag: str(x.tag, 24),
    title: str(x.title, 90),
    text: str(x.text, 220),
    url: isUrl(str(x.url, 300)) ? str(x.url, 300) : '',
    img: isImg(x.img, id) ? x.img : '',
    days: Array.isArray(x.days) ? [...new Set(x.days.map(Number).filter(d => d >= 1 && d <= 7))].sort() : [],
    from: isTime(x.from) ? x.from : '',
    to: isTime(x.to) ? x.to : '',
    start: isDate(x.start) ? x.start : '',
    end: isDate(x.end) ? x.end : '',
  };
  if (it.place === 'ticker') { it.img = ''; it.tag = ''; it.url = ''; }
  return it.title || it.text ? it : null;
}

function publicView(c, origin) {
  const live = c.active !== false && (!c.until || c.until >= today());
  if (!live) return { off: true };
  const img = k => (k ? `${origin}/api/img/${k}` : '');
  return {
    name: c.name, loc: c.loc, logo: img(c.logo), v: c.updated,
    items: (c.items || []).filter(i => i.on).map(i => ({
      place: i.place, tag: i.tag, title: i.title, text: i.text, url: i.url, img: img(i.img),
      days: i.days, from: i.from, to: i.to, start: i.start, end: i.end,
    })),
  };
}
const ownView = c => ({
  id: c.id, name: c.name, email: c.email, loc: c.loc, code: c.code, until: c.until || '',
  active: c.active !== false, logo: c.logo || '', items: c.items || [], updated: c.updated,
});
const adminView = c => ({ ...ownView(c), items: (c.items || []).length, created: c.created });
function today() {   // YYYY-MM-DD in Helsinki
  return new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Helsinki' }).format(new Date());
}

// ── storage ────────────────────────────────────────────────────────
const getCust = async (env, id) => id ? env.DB.get('cust:' + id, 'json') : null;
async function putCust(env, c) {
  c.updated = new Date().toISOString();
  await env.DB.put('cust:' + c.id, JSON.stringify(c));
}
async function newLink(env, c) {
  if (c.tok) await env.DB.delete('tok:' + c.tok);
  const token = rand(24);
  c.tok = await sha256(token);
  await env.DB.put('tok:' + c.tok, c.id);
  return token;
}
async function newCode(env) {
  for (let i = 0; i < 20; i++) {
    const code = rand(6, CODE_ABC);
    if (!(await env.DB.get('code:' + code))) return code;
  }
  throw new Error('no free code');
}
async function dropUnusedImages(env, c) {
  const used = new Set([c.logo, ...(c.items || []).map(i => i.img)].filter(Boolean));
  let cursor;
  do {
    const r = await env.DB.list({ prefix: `img:${c.id}-`, cursor });
    for (const k of r.keys) if (!used.has(k.name.slice(4))) await env.DB.delete(k.name);
    cursor = r.list_complete ? null : r.cursor;
  } while (cursor);
}

// ── handlers ───────────────────────────────────────────────────────
async function screen(env, code, req, ctx) {
  code = code.toUpperCase();
  if (!/^[A-Z0-9]{6}$/.test(code)) return fail(404, 'unknown code');
  const cache = typeof caches !== 'undefined' ? caches.default : null;
  const key = new Request(new URL(req.url).origin + '/api/screen/' + code);
  if (cache) { const hit = await cache.match(key); if (hit) return hit; }
  const c = await getCust(env, await env.DB.get('code:' + code));
  if (!c) return fail(404, 'unknown code');
  const res = json(publicView(c, new URL(req.url).origin), 200, { 'Cache-Control': 'public, max-age=60' });
  if (cache) ctx.waitUntil(cache.put(key, res.clone()));
  return res;
}

async function image(env, key) {
  if (!/^[\w-]{6,80}$/.test(key)) return fail(404, 'not found');
  const r = await env.DB.getWithMetadata('img:' + key, 'arrayBuffer');
  if (!r.value) return fail(404, 'not found');
  return new Response(r.value, { headers: {
    'Content-Type': (r.metadata && r.metadata.type) || 'image/jpeg',
    'Cache-Control': 'public, max-age=31536000, immutable', ...CORS } });
}

async function customer(env, req, rest) {
  const t = bearer(req);
  if (t.length < 20) return fail(401, 'login required');
  const c = await getCust(env, await env.DB.get('tok:' + await sha256(t)));
  if (!c) return fail(401, 'this link is no longer valid');

  if (rest === '' && req.method === 'GET') return json(ownView(c));

  if (rest === '' && req.method === 'PUT') {
    let b; try { b = await req.json(); } catch { return fail(400, 'invalid JSON'); }
    if (b.name != null) c.name = str(b.name, 60) || c.name;
    if (LOCS.includes(b.loc)) c.loc = b.loc;
    if (b.logo === '' || isImg(b.logo, c.id)) c.logo = b.logo;
    if (Array.isArray(b.items)) {
      if (b.items.length > MAX_ITEMS) return fail(400, `at most ${MAX_ITEMS} items`);
      c.items = b.items.map(x => cleanItem(x, c.id)).filter(Boolean);
    }
    await putCust(env, c);
    await dropUnusedImages(env, c);
    return json(ownView(c));
  }

  if (rest === '/image' && req.method === 'POST') {
    const type = (req.headers.get('Content-Type') || '').split(';')[0].trim().toLowerCase();
    if (!IMG_TYPES[type]) return fail(415, 'JPEG, PNG or WebP only');
    const buf = await req.arrayBuffer();
    if (!buf.byteLength) return fail(400, 'empty file');
    if (buf.byteLength > MAX_IMG) return fail(413, 'image is too large (max 1.5 MB)');
    const key = `${c.id}-${rand(8, CODE_ABC.toLowerCase())}`;
    await env.DB.put('img:' + key, buf, { metadata: { type } });
    return json({ key, url: `${new URL(req.url).origin}/api/img/${key}` });
  }
  return fail(404, 'not found');
}

async function admin(env, req, rest) {
  if (!env.ADMIN_KEY || env.ADMIN_KEY.length < 16) return fail(503, 'ADMIN_KEY is not set');
  if (!sameString(bearer(req), env.ADMIN_KEY)) return fail(401, 'wrong admin key');
  let b = {};
  if (req.method === 'POST' || req.method === 'PUT') { try { b = await req.json(); } catch { b = {}; } }
  const fields = c => {
    if (b.name != null) c.name = str(b.name, 60) || c.name;
    if (b.email != null) c.email = str(b.email, 120);
    if (LOCS.includes(b.loc)) c.loc = b.loc;
    if (b.until != null) c.until = isDate(b.until) ? b.until : '';
    if (b.active != null) c.active = !!b.active;
  };

  if (rest === '/customers' && req.method === 'GET') {
    const out = []; let cursor;
    do {
      const r = await env.DB.list({ prefix: 'cust:', cursor });
      for (const k of r.keys) { const c = await env.DB.get(k.name, 'json'); if (c) out.push(adminView(c)); }
      cursor = r.list_complete ? null : r.cursor;
    } while (cursor);
    out.sort((a, b) => a.name.localeCompare(b.name, 'fi'));
    return json(out);
  }
  if (rest === '/customers' && req.method === 'POST') {
    if (!str(b.name, 60)) return fail(400, 'name is required');
    const c = { id: 'c' + rand(7, CODE_ABC.toLowerCase()), name: '', email: '', loc: 'levi', until: '',
      active: true, logo: '', items: [], created: new Date().toISOString() };
    fields(c);
    c.code = await newCode(env);
    await env.DB.put('code:' + c.code, c.id);
    const token = await newLink(env, c);
    await putCust(env, c);
    return json({ ...adminView(c), token }, 201);
  }
  const m = rest.match(/^\/customers\/(c[a-z0-9]{7})(\/link)?$/);
  if (!m) return fail(404, 'not found');
  const c = await getCust(env, m[1]);
  if (!c) return fail(404, 'no such customer');
  if (m[2] && req.method === 'POST') {
    const token = await newLink(env, c);
    await putCust(env, c);
    return json({ ...adminView(c), token });
  }
  if (!m[2] && req.method === 'PUT') { fields(c); await putCust(env, c); return json(adminView(c)); }
  if (!m[2] && req.method === 'DELETE') {
    if (c.tok) await env.DB.delete('tok:' + c.tok);
    await env.DB.delete('code:' + c.code);
    c.logo = ''; c.items = [];
    await dropUnusedImages(env, c);
    await env.DB.delete('cust:' + c.id);
    return json({ ok: true });
  }
  return fail(405, 'method not allowed');
}

export async function onRequest(ctx) {
  const { request: req, env } = ctx;
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });
  if (!env.DB) return fail(503, 'storage (KV binding "DB") is not set up');
  const path = new URL(req.url).pathname.replace(/\/+$/, '');
  try {
    let m;
    if ((m = path.match(/^\/api\/screen\/([^/]+)$/)) && req.method === 'GET') return await screen(env, m[1], req, ctx);
    if ((m = path.match(/^\/api\/img\/([^/]+)$/)) && req.method === 'GET') return await image(env, m[1]);
    if ((m = path.match(/^\/api\/me(\/image)?$/))) return await customer(env, req, m[1] || '');
    if ((m = path.match(/^\/api\/admin(\/.*)?$/))) return await admin(env, req, m[1] || '');
    return fail(404, 'not found');
  } catch (e) {
    return fail(500, 'server error: ' + (e && e.message || e));
  }
}
