/**
 * cache.js — in-memory semantic cache (cosine on embeddings)
 * Per-tenant namespacing. LRU-ish simple eviction.
 */

import { cosine, mockEmbed, structuredLog } from './utils.js';

export class SemanticCache {
  constructor(opts = {}) {
    this.enabled = opts.enabled !== false;
    this.threshold = opts.threshold || 0.92;
    this.maxEntries = opts.maxEntries || 2000;
    this.ttlSec = opts.ttlSec || 3600;
    // namespace -> array of entries
    this.namespaces = new Map();
  }

  _getNs(tenant) {
    const t = tenant || 'default';
    if (!this.namespaces.has(t)) this.namespaces.set(t, []);
    return this.namespaces.get(t);
  }

  async embed(text, embedFn) {
    if (!this.enabled) return null;
    if (typeof embedFn === 'function') {
      return await embedFn(text);
    }
    return mockEmbed(text);
  }

  async getSimilar(embedding, tenant, threshold = this.threshold) {
    if (!this.enabled || !embedding) return null;
    const ns = this._getNs(tenant);
    const now = Date.now() / 1000;
    let best = null;
    let bestSim = 0;
    const toDelete = [];
    for (let i = 0; i < ns.length; i++) {
      const e = ns[i];
      if (this.ttlSec && (now - e.ts > this.ttlSec)) {
        toDelete.push(i);
        continue;
      }
      const sim = cosine(embedding, e.embedding);
      if (sim >= threshold && sim > bestSim) {
        bestSim = sim;
        best = { ...e, sim };
      }
    }
    // simple cleanup (reverse to not shift indices badly)
    for (let j = toDelete.length - 1; j >= 0; j--) ns.splice(toDelete[j], 1);
    return best;
  }

  async store(entry, tenant) {
    if (!this.enabled || !entry || !entry.embedding) return;
    const ns = this._getNs(tenant);
    ns.push({ ...entry, ts: Date.now() / 1000 });
    // evict oldest if over limit
    if (ns.length > this.maxEntries) {
      ns.splice(0, ns.length - this.maxEntries);
    }
    structuredLog({ type: 'cache_store', tenant, model: entry.model, tier: entry.tier });
  }

  clear(tenant) {
    if (tenant) this.namespaces.delete(tenant);
    else this.namespaces.clear();
  }

  stats() {
    let total = 0;
    for (const arr of this.namespaces.values()) total += arr.length;
    return { namespaces: this.namespaces.size, totalEntries: total, enabled: this.enabled };
  }
}

export default SemanticCache;
