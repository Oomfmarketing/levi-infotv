/* LeviTV Worker entry: /api/* goes to the customer API, everything else to the static assets. */
import { onRequest } from './functions/api/[[path]].js';

export default {
  fetch(request, env, ctx) {
    if (new URL(request.url).pathname.startsWith('/api/')) {
      return onRequest({ request, env, waitUntil: p => ctx.waitUntil(p) });
    }
    return env.ASSETS.fetch(request);
  },
};
