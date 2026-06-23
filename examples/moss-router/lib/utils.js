/**
 * utils.js — shared helpers for MossRouter (MVP)
 * Resilient JSON, logging, mock embed, headers, simple backoff.
 */

export function structuredLog(obj) {
  const line = JSON.stringify({ ts: new Date().toISOString(), ...obj });
  console.log(line);
  return line;
}

export function getEnv(key, def = undefined) {
  return process.env[key] !== undefined ? process.env[key] : def;
}

export function isMock() {
  return process.env.MOSS_MOCK === '1' || process.env.MOCK === '1';
}

export function parseTierFromModel(model) {
  if (!model) return null;
  if (model.startsWith('moss:')) {
    return model.split(':')[1] || null;
  }
  return null;
}

export function getTenant(reqOrOpts) {
  if (reqOrOpts && reqOrOpts.headers) {
    return reqOrOpts.headers['x-moss-tenant'] || reqOrOpts.headers['X-Moss-Tenant'] || 'default';
  }
  if (reqOrOpts && reqOrOpts.tenant) return reqOrOpts.tenant;
  return 'default';
}

export function getSpeed(reqOrOpts) {
  if (reqOrOpts && reqOrOpts.headers) {
    const h = reqOrOpts.headers['x-moss-speed'] || reqOrOpts.headers['X-Moss-Speed'];
    if (h) return h.toLowerCase();
  }
  if (reqOrOpts && reqOrOpts.speed) return String(reqOrOpts.speed).toLowerCase();
  return null;
}

export function getForceFail(reqOrOpts) {
  if (reqOrOpts && reqOrOpts.headers) {
    return reqOrOpts.headers['x-moss-force-fail'] || reqOrOpts.headers['X-Moss-Force-Fail'] || null;
  }
  if (reqOrOpts && reqOrOpts.forceFail) return reqOrOpts.forceFail;
  return null;
}

export function addMossHeaders(res, info) {
  if (!res || !info) return;
  if (info.costUsd != null) res.setHeader('X-Moss-Cost-USD', String(info.costUsd));
  if (info.model) res.setHeader('X-Moss-Model', info.model);
  if (info.tier) res.setHeader('X-Moss-Tier', info.tier);
  if (info.cache) res.setHeader('X-Moss-Cache', info.cache);
  if (info.latencyMs != null) res.setHeader('X-Moss-Latency-Ms', String(info.latencyMs));
  if (info.provider) res.setHeader('X-Moss-Provider', info.provider);
  if (info.usedCascade) res.setHeader('X-Moss-Cascade', 'true');
}

export function resilientJSONParse(text) {
  if (!text || typeof text !== 'string') return null;
  let t = text.trim();
  // strip ```json ... ``` or ``` ... ```
  t = t.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim();
  // attempt repair trailing commas in objects/arrays (simple)
  t = t.replace(/,\s*([}\]])/g, '$1');
  try {
    return JSON.parse(t);
  } catch (e) {
    // last resort: try to extract {...} or [...]
    const m = t.match(/(\{[\s\S]*\}|\[[\s\S]*\])/);
    if (m) {
      try { return JSON.parse(m[1].replace(/,\s*([}\]])/g, '$1')); } catch {}
    }
    return null;
  }
}

// Deterministic mock embedding (128 dim) for tests + zero-key mode
// Cosine will be high for near-duplicate strings, low for different.
export function mockEmbed(text) {
  const s = String(text || '');
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h += (h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24);
  }
  const dim = 128;
  const vec = new Array(dim);
  let seed = Math.abs(h) || 1;
  for (let i = 0; i < dim; i++) {
    seed = (seed * 16807) % 2147483647;
    vec[i] = (seed / 2147483647) * 2 - 1;
  }
  return vec;
}

export function cosine(a, b) {
  if (!a || !b || a.length !== b.length) return 0;
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  if (na === 0 || nb === 0) return 0;
  return dot / (Math.sqrt(na) * Math.sqrt(nb));
}

export async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

export function backoff(attempt) {
  return Math.min(50 * Math.pow(2, attempt), 400);
}
