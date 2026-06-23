#!/usr/bin/env node
/**
 * MossRouter HTTP server (OpenAI compatible + Moss extensions)
 * Port 4022 by default. Full mock support.
 */

import express from 'express';
import MossRouter from './lib/router.js';
import { addMossHeaders, structuredLog, isMock, getTenant, getSpeed, getForceFail, parseTierFromModel } from './lib/utils.js';
import { getTierConfig, TIER_DEFAULTS } from './lib/pricing.js';
import { PROVIDER_NAMES } from './lib/providers.js';
import { readFileSync } from 'node:fs';

const PORT = parseInt(process.env.PORT || '4022', 10);
const MOCK = isMock();

const app = express();
app.use(express.json({ limit: '2mb' }));

// CORS (dev friendly)
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Moss-Tier, X-Moss-Tenant, X-Moss-Speed, X-Moss-Force-Fail, X-Moss-Cascade');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

// Load config
let CONFIG = {};
try {
  const cfgPath = new URL('./config.example.json', import.meta.url);
  CONFIG = JSON.parse(readFileSync(cfgPath, 'utf8'));
} catch {}
if (MOCK) CONFIG.mock = true;

const router = new MossRouter({ ...CONFIG, tiers: CONFIG.tiers || TIER_DEFAULTS });

app.get('/', (req, res) => {
  res.json({
    name: 'MossRouter',
    version: '0.1.0',
    phase: 'Phase 1 MVP',
    mock: MOCK,
    port: PORT,
    defaultTier: router.config.defaultTier,
    providers: PROVIDER_NAMES,
    tiers: router.getAvailableTiers(),
    cache: router.cache.stats(),
    groq: 'enabled (LPU speed tier)'
  });
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok', uptime: process.uptime(), mock: MOCK, port: PORT });
});

app.get('/tiers', (req, res) => {
  const out = {};
  for (const t of router.getAvailableTiers()) out[t] = getTierConfig(t, CONFIG);
  res.json({ tiers: out });
});

app.get('/pricing', (req, res) => {
  res.json({ pricing: 'see tiers + /tiers for per-tier model pricing (June 2026)' });
});

app.get('/v1/models', (req, res) => {
  const models = [
    ...router.getAvailableTiers().map(t => ({ id: `moss:${t}`, object: 'model', owned_by: 'moss' })),
    { id: 'groq/llama-3.1-8b-instant', object: 'model', owned_by: 'groq' }
  ];
  res.json({ object: 'list', data: models });
});

// Main chat completions (OpenAI compatible)
app.post('/v1/chat/completions', async (req, res) => {
  const body = req.body || {};
  const start = Date.now();
  try {
    let model = body.model || `moss:${router.config.defaultTier}`;
    const tierFromModel = parseTierFromModel(model);
    const tier = (req.headers['x-moss-tier'] || req.headers['X-Moss-Tier'] || tierFromModel || router.config.defaultTier);
    const tenant = getTenant(req);
    const speed = getSpeed(req);
    const forceFail = getForceFail(req);

    const messages = body.messages || [{ role: 'user', content: body.prompt || 'hello' }];

    const result = await router.routeRequest({
      messages,
      tier,
      model,
      tenant,
      speed,
      forceFail
    });

    const resp = {
      id: `chatcmpl-moss-${Date.now()}`,
      object: 'chat.completion',
      created: Math.floor(Date.now() / 1000),
      model: result.model,
      choices: [{
        index: 0,
        message: { role: 'assistant', content: result.content },
        finish_reason: 'stop'
      }],
      usage: result.usage,
      moss: {
        tier: result.tier,
        provider: result.provider,
        costUsd: result.costUsd,
        cache: result.cache,
        latencyMs: result.latencyMs
      }
    };

    addMossHeaders(res, result);
    structuredLog({ type: 'http_response', tier: result.tier, latency: Date.now() - start, cache: result.cache });
    res.json(resp);
  } catch (e) {
    structuredLog({ type: 'http_error', error: e.message });
    res.status(500).json({ error: { message: e.message } });
  }
});

// Extra moss debug
app.get('/v1/moss/route', (req, res) => {
  const tier = req.query.tier || 'eco';
  const speed = req.query.speed || null;
  const sel = router.selectProviderForTier(tier, speed);
  res.json({ tier, speed, selected: sel, mock: MOCK });
});

app.use((err, req, res, next) => {
  console.error('[error]', err);
  res.status(500).json({ error: err.message });
});

app.listen(PORT, () => {
  console.log(`🌿 MossRouter listening on http://localhost:${PORT} (mock=${MOCK})`);
  console.log(`   Providers: ${PROVIDER_NAMES.join(', ')}`);
  console.log(`   Tiers: ${router.getAvailableTiers().join(', ')}`);
  console.log(`   Try: curl http://localhost:${PORT}/  or  MOSS_MOCK=1 ./bin/moss-router chat --tier nano "hi"`);
  console.log(`   Test: MOSS_MOCK=1 npm test`);
});
