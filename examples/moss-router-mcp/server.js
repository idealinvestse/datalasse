#!/usr/bin/env node
/**
 * MossRouter MCP Server — x402 billable MCP wrapper for MossRouter tiers (Phase 2b)
 *
 * Phase 2a preserved + additive:
 * - Full MCP Streamable /mcp (McpServer + StreamableHTTPServerTransport)
 * - Redis-backed spend/rate/free (in-mem fallback)
 * - Langfuse v5 tracing (no-op if no keys)
 * - CDP facilitator support (default testnet x402.org, CDP switch, mainnet yellow)
 * - All Phase 2a custom routes + behavior 100% backward compat
 *
 * 5 tier tools, multi-tenant, spend caps. LemonCake parity in tests/docs.
 */

import express from 'express';
import { spawn } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { readFileSync, writeFileSync } from 'node:fs';
import { setTimeout as sleep } from 'node:timers/promises';

// --- MCP SDK (Phase 2b) ---
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { z } from 'zod';

// --- Config ---
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = parseInt(process.env.PORT || '4023', 10);
const SKIP_PAYMENT = process.env.SKIP_PAYMENT === '1';
const MOCK = process.env.MOSS_MOCK === '1' || process.env.MOCK === '1';

let CONFIG = {};
try {
  const cfgPath = new URL('./config.example.json', import.meta.url);
  CONFIG = JSON.parse(readFileSync(cfgPath, 'utf8'));
} catch (e) {
  console.warn('[config] using defaults');
}

const MOSS_ROUTER_PORT = parseInt(process.env.MOSS_ROUTER_PORT || CONFIG.mossRouter?.port || '4022', 10);
const MOSS_ROUTER_SCRIPT = CONFIG.mossRouter?.script || '../moss-router/server.js';
const MOSS_HEALTH = CONFIG.mossRouter?.healthUrl || `http://127.0.0.1:${MOSS_ROUTER_PORT}/health`;

let NETWORK = process.env.NETWORK || CONFIG.x402?.network || 'eip155:84532';
let PAYTO = process.env.PAY_TO || CONFIG.x402?.payTo || '0x000000000000000000000000000000000000dEaD';
let FACILITATOR_URL = process.env.FACILITATOR_URL || CONFIG.x402?.facilitatorUrl || 'https://x402.org/facilitator';

const FREE_TIER_DAILY = parseInt(process.env.FREE_TIER_DAILY || CONFIG.freeTier?.callsPerDay || '100', 10);

const PRICING = CONFIG.pricing || { nano: 0.001, eco: 0.003, standard: 0.008, premium: 0.020, flagship: 0.050 };
const SPEND_DAILY_CAP = parseFloat(CONFIG.tenant?.defaultSpendCapDaily || 5.0);
const SPEND_MONTHLY_CAP = parseFloat(CONFIG.tenant?.defaultSpendCapMonthly || 50.0);
const RATE_LIMIT_PER_MIN = parseInt(CONFIG.tenant?.rateLimitPerMin || '60', 10);

// CDP support (Phase 2b)
const CDP_API_KEY = process.env.CDP_API_KEY || '';
const CDP_API_SECRET = process.env.CDP_API_SECRET || '';
if (CDP_API_KEY && CDP_API_SECRET) {
  if (FACILITATOR_URL.includes('x402.org')) {
    FACILITATOR_URL = 'https://api.cdp.coinbase.com/platform/v2/x402';
  }
  console.log('[facilitator] CDP keys present — using CDP endpoint');
}
if (NETWORK === 'eip155:8453' || NETWORK.includes('8453')) {
  console.warn('[WARN] NETWORK mainnet (eip155:8453) selected — YELLOW ZONE. Owner approval required before real usage.');
}

// --- @x402 setup ---
let paymentMiddleware, x402ResourceServer, ExactEvmScheme, HTTPFacilitatorClient;
try {
  const x402Express = await import('@x402/express');
  const x402Core = await import('@x402/core/server');
  const x402Evm = await import('@x402/evm/exact/server');
  paymentMiddleware = x402Express.paymentMiddleware;
  x402ResourceServer = x402Express.x402ResourceServer;
  ExactEvmScheme = x402Evm.ExactEvmScheme;
  HTTPFacilitatorClient = x402Core.HTTPFacilitatorClient;
  console.log('[x402] packages loaded');
} catch (e) {
  console.warn('[x402] packages not fully usable, falling back:', e.message);
}

const facilitatorClient = HTTPFacilitatorClient ? new HTTPFacilitatorClient({ url: FACILITATOR_URL }) : null;

// --- Tools (5 tiers) ---
const TOOLS = [
  { name: 'moss_nano', tier: 'nano', price: '$0.001', priceUsd: PRICING.nano, description: 'Nano tier routing (ultra cheap). Price: $0.001/call.' },
  { name: 'moss_eco', tier: 'eco', price: '$0.003', priceUsd: PRICING.eco, description: 'Eco tier (balanced daily). Price: $0.003/call.' },
  { name: 'moss_standard', tier: 'standard', price: '$0.008', priceUsd: PRICING.standard, description: 'Standard tier (GPT-5.1/Sonnet 4.6 class). Price: $0.008/call.' },
  { name: 'moss_premium', tier: 'premium', price: '$0.020', priceUsd: PRICING.premium, description: 'Premium tier (GPT-5.5/Opus 4.8). Price: $0.020/call.' },
  { name: 'moss_flagship', tier: 'flagship', price: '$0.050', priceUsd: PRICING.flagship, description: 'Flagship tier (max quality). Price: $0.050/call.' },
];

// --- Redis (Phase 2b) + in-mem fallback ---
const REDIS_URL = process.env.REDIS_URL || '';
let redis = null;
let redisStatus = 'off';
if (REDIS_URL) {
  try {
    const { default: Redis } = await import('ioredis');
    redis = new Redis(REDIS_URL, { lazyConnect: true, maxRetriesPerRequest: 1 });
    redis.on('error', (e) => { console.warn('[redis] error, falling back in-mem:', e.message); redisStatus = 'degraded'; });
    redis.on('connect', () => { redisStatus = 'ok'; console.log('[redis] connected'); });
    await redis.connect().catch(() => { redisStatus = 'degraded'; });
  } catch (e) {
    console.warn('[redis] ioredis not available or connect fail, using in-mem:', e.message);
    redisStatus = 'degraded';
  }
}

// In-memory stores (always present as fallback / cache)
const freeTier = new Map(); // hash -> {date, count}
const tenantSpend = new Map(); // hash -> {daily, monthly, rate}
const spendFile = path.join(__dirname, 'spend.json');

function loadSpend() {
  try {
    const data = JSON.parse(readFileSync(spendFile, 'utf8'));
    Object.entries(data).forEach(([k, v]) => tenantSpend.set(k, v));
  } catch {}
}
function flushSpend() {
  try {
    const obj = Object.fromEntries(tenantSpend);
    writeFileSync(spendFile, JSON.stringify(obj, null, 2));
  } catch {}
}
loadSpend();

function hashTenant(key) {
  if (!key) return 'default';
  return createHash('sha256').update(String(key)).digest('hex').slice(0, 32);
}

function getTenantFromReq(req) {
  const auth = req.headers['authorization'] || req.headers['x-moss-api-key'] || req.headers['x-moss-tenant-key'] || '';
  const m = String(auth).match(/moss_(live|test)_([A-Za-z0-9_-]+)/i);
  if (m) {
    const full = `moss_${m[1]}_${m[2]}`;
    return { key: full, isTest: m[1] === 'test', hash: hashTenant(full) };
  }
  return { key: 'default', isTest: !!MOCK, hash: 'default' };
}

// --- Redis + mem helpers (atomic friendly) ---
async function redisGet(key) {
  if (!redis || redisStatus === 'degraded') return null;
  try { return await redis.get(key); } catch { redisStatus = 'degraded'; return null; }
}
async function redisSet(key, val, ttlSec) {
  if (!redis || redisStatus === 'degraded') return false;
  try {
    if (ttlSec) await redis.set(key, val, 'EX', ttlSec);
    else await redis.set(key, val);
    return true;
  } catch { redisStatus = 'degraded'; return false; }
}
async function redisIncrByFloat(key, delta, ttlSec) {
  if (!redis || redisStatus === 'degraded') return null;
  try {
    const v = await redis.incrbyfloat(key, delta);
    if (ttlSec) await redis.expire(key, ttlSec);
    return parseFloat(v);
  } catch { redisStatus = 'degraded'; return null; }
}

async function getFreeTierCount(h) {
  const today = new Date().toISOString().slice(0, 10);
  const rkey = `mossmcp:free:${h}:${today}`;
  const mem = freeTier.get(h);
  if (redis && redisStatus === 'ok') {
    const v = await redisGet(rkey);
    if (v != null) return parseInt(v, 10) || 0;
  }
  if (mem && mem.date === today) return mem.count || 0;
  return 0;
}
async function incrementFreeTier(h) {
  const today = new Date().toISOString().slice(0, 10);
  const rkey = `mossmcp:free:${h}:${today}`;
  if (redis && redisStatus === 'ok') {
    const newVal = await redisIncrByFloat(rkey, 1, 36 * 3600);
    if (newVal != null) return;
  }
  // mem
  const entry = freeTier.get(h) || { date: today, count: 0 };
  if (entry.date !== today) { entry.date = today; entry.count = 0; }
  entry.count++;
  freeTier.set(h, entry);
}

async function getTenantSpend(h) {
  const today = new Date().toISOString().slice(0, 10);
  const month = today.slice(0, 7);
  if (redis && redisStatus === 'ok') {
    const dkey = `mossmcp:spend:${h}:daily:${today}`;
    const mkey = `mossmcp:spend:${h}:monthly:${month}`;
    const rkey = `mossmcp:rate:${h}`;
    let dailyUsd = parseFloat(await redisGet(dkey) || '0') || 0;
    let monthlyUsd = parseFloat(await redisGet(mkey) || '0') || 0;
    let rate = [];
    try { rate = (await redis.lrange(rkey, 0, -1) || []).map(Number); } catch {}
    return { daily: { date: today, usd: dailyUsd }, monthly: { month, usd: monthlyUsd }, rate };
  }
  if (!tenantSpend.has(h)) {
    tenantSpend.set(h, { daily: { date: today, usd: 0 }, monthly: { month, usd: 0 }, rate: [] });
  }
  return tenantSpend.get(h);
}

async function checkRateLimit(h) {
  const now = Date.now();
  const windowMs = 60 * 1000;
  const s = await getTenantSpend(h);
  if (redis && redisStatus === 'ok') {
    const rkey = `mossmcp:rate:${h}`;
    // trim old
    await redis.ltrim(rkey, -RATE_LIMIT_PER_MIN, -1).catch(() => {});
    const recent = await redis.lrange(rkey, 0, -1).catch(() => []);
    const filtered = recent.filter(ts => now - Number(ts) < windowMs);
    if (filtered.length >= RATE_LIMIT_PER_MIN) {
      const err = new Error('Rate limit exceeded'); err.code = 429; err.status = 429; throw err;
    }
    await redis.rpush(rkey, now);
    await redis.expire(rkey, 90);
    return;
  }
  // mem
  s.rate = s.rate.filter(ts => now - ts < windowMs);
  if (s.rate.length >= RATE_LIMIT_PER_MIN) {
    const err = new Error('Rate limit exceeded'); err.code = 429; err.status = 429; throw err;
  }
  s.rate.push(now);
}

async function checkAndRecordSpend(h, priceUsd) {
  const today = new Date().toISOString().slice(0, 10);
  const month = today.slice(0, 7);
  if (redis && redisStatus === 'ok') {
    const dkey = `mossmcp:spend:${h}:daily:${today}`;
    const mkey = `mossmcp:spend:${h}:monthly:${month}`;
    const dailyStr = (await redisGet(dkey)) || '0';
    const monthlyStr = (await redisGet(mkey)) || '0';
    const daily = parseFloat(dailyStr) || 0;
    const monthly = parseFloat(monthlyStr) || 0;

    if (daily + priceUsd > SPEND_DAILY_CAP) {
      const err = new Error(`Daily spend cap exceeded ($${SPEND_DAILY_CAP})`); err.code = 429; err.status = 429; err.spend = true; throw err;
    }
    if (monthly + priceUsd > SPEND_MONTHLY_CAP) {
      const err = new Error(`Monthly spend cap exceeded ($${SPEND_MONTHLY_CAP})`); err.code = 429; err.status = 429; err.spend = true; throw err;
    }
    await redisIncrByFloat(dkey, priceUsd, 36*3600);
    await redisIncrByFloat(mkey, priceUsd, 35*24*3600);
    return;
  }
  // mem fallback
  const s = await getTenantSpend(h);
  if (s.daily.date !== today) s.daily = { date: today, usd: 0 };
  if (s.monthly.month !== month) s.monthly = { month, usd: 0 };
  if (s.daily.usd + priceUsd > SPEND_DAILY_CAP) { const err = new Error(`Daily spend cap exceeded ($${SPEND_DAILY_CAP})`); err.code = 429; err.status = 429; err.spend = true; throw err; }
  if (s.monthly.usd + priceUsd > SPEND_MONTHLY_CAP) { const err = new Error(`Monthly spend cap exceeded ($${SPEND_MONTHLY_CAP})`); err.code = 429; err.status = 429; err.spend = true; throw err; }
  s.daily.usd = Number((s.daily.usd + priceUsd).toFixed(6));
  s.monthly.usd = Number((s.monthly.usd + priceUsd).toFixed(6));
  flushSpend();
}

async function recordActualCost(h, actualUsd) {
  // best effort reconcile (Phase 2b keeps simple pre-record)
  if (redis && redisStatus === 'ok') {
    // could diff but for MVP we accept pre-record delta
    return;
  }
  flushSpend();
}

// --- MCP Server (Phase 2b) ---
const mcpServer = new McpServer({
  name: 'moss-router-mcp',
  version: '0.2.0',
});

// Register 5 tier tools (MCP format). Payment handled at transport/route level.
TOOLS.forEach((toolDef) => {
  mcpServer.tool(
    toolDef.name,
    `${toolDef.description} (flat price ${toolDef.price})`,
    { prompt: z.string().optional(), messages: z.array(z.any()).optional() },
    async (args) => {
      try {
        console.log(`[mcp-tool] ${toolDef.name} called, args=${JSON.stringify(args)}`);
        const tenantDefault = { key: 'mcp-tenant', hash: 'default' };
        const result = await internalProxyCall(toolDef.tier, args, tenantDefault);
        console.log(`[mcp-tool] ${toolDef.name} result ok=${result?.ok}, content-len=${result?.content?.length}`);
        if (result && result.error) {
          console.error('[mcp-tool] proxy err', result);
          return { content: [{ type: 'text', text: 'error: ' + (result.details || result.error) }] };
        }
        return { content: [{ type: 'text', text: result.content || JSON.stringify(result) }] };
      } catch (e) {
        console.error('[mcp-tool] handler crash', e);
        return { content: [{ type: 'text', text: 'handler error' }] };
      }
    }
  );
});

// Internal shared proxy (returns data instead of writing res) for MCP + old
async function internalProxyCall(tier, bodyArg, tenantInfo) {
  const start = Date.now();
  try {
    let messages = bodyArg?.messages;
    if (!messages && bodyArg?.prompt) {
      messages = [{ role: 'user', content: bodyArg.prompt }];
    }
    if (!messages) messages = [{ role: 'user', content: 'Hello from MossRouter MCP' }];

    const upstreamRes = await fetch(`http://127.0.0.1:${MOSS_ROUTER_PORT}/v1/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Moss-Tier': tier,
        'X-Moss-Tenant': tenantInfo?.key || 'default'
      },
      body: JSON.stringify({ model: `moss:${tier}`, messages })
    });
    const text = await upstreamRes.text();
    let data; try { data = JSON.parse(text); } catch { data = { error: text }; }

    const costHeader = upstreamRes.headers.get('x-moss-cost-usd');
    const actualCost = (data.moss && data.moss.costUsd) || parseFloat(costHeader || '0') || PRICING[tier] || 0;

    await recordActualCost(tenantInfo?.hash || 'default', actualCost);

    const content = data.choices?.[0]?.message?.content || data.content || '[no content]';
    return {
      ok: true,
      tool: `moss_${tier}`,
      content,
      moss: { tier, costUsd: actualCost, provider: data.moss?.provider, model: data.model, cache: data.moss?.cache },
      usage: data.usage,
      costHeader
    };
  } catch (err) {
    return { error: 'Upstream error', details: err.message };
  }
}

// --- x402 challenge + paywall (extended for real facilitator in 2b) ---
function x402Challenge(tool) {
  return {
    x402Version: 2,
    accepts: [{
      scheme: 'exact',
      network: NETWORK,
      payTo: PAYTO,
      maxAmountRequired: Math.ceil(tool.priceUsd * 1_000_000).toString(),
      resource: `/mcp/tools/${tool.name}`,
      description: tool.description,
      mimeType: 'application/json',
      outputSchema: {},
      paywall: 'https://x402.org'
    }]
  };
}

function x402Paywall(tool) {
  return async (req, res, next) => {
    if (SKIP_PAYMENT || MOCK) {
      console.log(`[bypass] ${tool.name} (SKIP_PAYMENT or MOCK)`);
      return next();
    }

    const { key, isTest, hash } = getTenantFromReq(req);
    const freeCount = await getFreeTierCount(hash);

    if (isTest && freeCount < FREE_TIER_DAILY) {
      await incrementFreeTier(hash);
      console.log(`[free-tier] ${tool.name} key=${key} (${freeCount + 1}/${FREE_TIER_DAILY})`);
      return next();
    }

    const hasPayment = req.headers['payment-signature'] || req.headers['x-payment'] || req.headers['paymenT-signature'] || req.headers['x-payment-signature'];
    if (!hasPayment) {
      console.log(`[402] ${tool.name} (payment required)`);
      const challenge = x402Challenge(tool);
      res.setHeader('PAYMENT-REQUIRED', Buffer.from(JSON.stringify(challenge)).toString('base64'));
      return res.status(402).json({
        error: 'Payment required',
        challenge,
        freeTierExhausted: !isTest,
        freeTierDaily: FREE_TIER_DAILY
      });
    }

    // Real facilitator verify path (Phase 2b)
    if (facilitatorClient && !MOCK && !SKIP_PAYMENT && FACILITATOR_URL && !FACILITATOR_URL.includes('x402.org')) {
      try {
        // Build minimal payload/reqs from known + header (mock sig still works for dev)
        const paymentPayload = { x402Version: 2, scheme: 'exact', network: NETWORK, payload: { signature: String(hasPayment) } };
        const paymentRequirements = x402Challenge(tool).accepts[0];
        const verifyRes = await facilitatorClient.verify(paymentPayload, paymentRequirements).catch(e => ({ isValid: false, error: e.message }));
        if (!verifyRes || verifyRes.isValid === false) {
          console.log(`[facilitator] verify failed for ${tool.name}`);
          const challenge = x402Challenge(tool);
          res.setHeader('PAYMENT-REQUIRED', Buffer.from(JSON.stringify(challenge)).toString('base64'));
          return res.status(402).json({ error: 'Payment verification failed', details: verifyRes });
        }
        console.log(`[paid] ${tool.name} (facilitator verified)`);
        // Note: settle will be called post-proxy in the calling route for MCP/custom
        return next();
      } catch (e) {
        console.warn('[facilitator] verify error, falling back to mock accept:', e.message);
      }
    }

    // mock facilitator accept (Phase 2a parity + default)
    console.log(`[paid] ${tool.name} (mock sig: ${String(hasPayment).slice(0, 24)}...)`);
    next();
  };
}

// --- Proxy (kept for custom routes, used by MCP internally) ---
async function proxyToMoss(req, res, tier, tenantKey) {
  const result = await internalProxyCall(tier, req.body || {}, { key: tenantKey, hash: hashTenant(tenantKey) });
  if (result.error) {
    return res.status(502).json(result);
  }
  if (result.costHeader) res.setHeader('X-Moss-Cost-USD', result.costHeader);
  res.setHeader('X-Moss-Tier', tier);
  res.setHeader('X-Moss-Model', result.moss?.model || `moss:${tier}`);
  res.json(result);
}

// --- Langfuse v5 (Phase 2b, conditional no-op) ---
let langfuseEnabled = false;
let langfuseSdk = null;
let startActiveObservation = null;

async function initLangfuse() {
  const pub = process.env.LANGFUSE_PUBLIC_KEY;
  const sec = process.env.LANGFUSE_SECRET_KEY;
  if (!pub || !sec) {
    console.log('[langfuse] no keys — tracing disabled (no-op)');
    return;
  }
  try {
    const otel = await import('@opentelemetry/sdk-node');
    const { LangfuseSpanProcessor } = await import('@langfuse/otel');
    const exporterMod = await import('@opentelemetry/exporter-trace-otlp-http');
    const { NodeSDK } = otel;
    const { OTLPTraceExporter } = exporterMod;

    const baseUrl = process.env.LANGFUSE_BASE_URL || 'https://cloud.langfuse.com';
    const exporter = new OTLPTraceExporter({ url: `${baseUrl}/api/public/otel` });

    const sdk = new NodeSDK({
      spanProcessors: [new LangfuseSpanProcessor()],
      traceExporter: exporter
    });
    sdk.start();

    const tracing = await import('@langfuse/tracing');
    startActiveObservation = tracing.startActiveObservation;

    langfuseEnabled = true;
    langfuseSdk = sdk;
    console.log('[langfuse] v5 tracing enabled');
  } catch (e) {
    console.warn('[langfuse] init failed (no-op):', e.message);
    langfuseEnabled = false;
  }
}

async function withObservation(name, fn, meta = {}) {
  if (!langfuseEnabled || !startActiveObservation) {
    return fn();
  }
  return startActiveObservation(name, async (span) => {
    span.update({ metadata: { ...meta, moss: { ...meta.moss } } });
    const res = await fn();
    return res;
  });
}

// --- Express app ---
const app = express();
app.use(express.json({ limit: '2mb' }));

// CORS
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Moss-Api-Key, X-Payer-Wallet, PAYMENT-SIGNATURE, X-Payment, X-PAYMENT-SIGNATURE');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

// Info (updated Phase 2b)
app.get('/', (req, res) => {
  res.json({
    name: 'MossRouter MCP',
    version: '0.2.0',
    phase: 'Phase 2b (MCP + Redis + Langfuse + CDP)',
    skipPayment: SKIP_PAYMENT,
    mock: MOCK,
    mossRouterPort: MOSS_ROUTER_PORT,
    payTo: PAYTO,
    network: NETWORK,
    freeTierDaily: FREE_TIER_DAILY,
    redis: redisStatus,
    langfuse: langfuseEnabled ? 'ok' : 'off',
    facilitator: FACILITATOR_URL.includes('cdp') ? 'cdp' : 'x402.org',
    tools: TOOLS.map(t => ({ name: t.name, description: t.description, price: t.price }))
  });
});

app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    uptime: process.uptime(),
    skipPayment: SKIP_PAYMENT,
    mock: MOCK,
    mossChild: !!mossChild,
    redis: redisStatus,
    langfuse: langfuseEnabled ? 'ok' : 'off',
    facilitator: FACILITATOR_URL,
    network: NETWORK,
    phase: '2b'
  });
});

// Tool catalog
app.get('/mcp/tools', (req, res) => {
  res.json({ tools: TOOLS.map(t => ({ name: t.name, description: t.description, price: t.price })) });
});

// Custom 5 billable routes (Phase 2a — untouched behavior)
TOOLS.forEach((tool) => {
  const route = `/mcp/tools/${tool.name}`;
  app.post(route, async (req, res, next) => {
    const { key, hash } = getTenantFromReq(req);
    const priceUsd = tool.priceUsd;

    try {
      await checkRateLimit(hash);
      await checkAndRecordSpend(hash, priceUsd);
    } catch (e) {
      const status = e.status || e.code || 429;
      return res.status(status).json({ error: e.message, code: status });
    }

    const mw = x402Paywall(tool);
    await mw(req, res, async () => {
      // If we reach here with facilitator and payment, settle after
      const origJson = res.json.bind(res);
      res.json = (body) => {
        // fire-and-forget settle for real path
        if (facilitatorClient && !SKIP_PAYMENT && !MOCK) {
          // best effort — real impl would build proper payload/reqs
          facilitatorClient.settle({ x402Version: 2, scheme: 'exact', network: NETWORK, payload: { signature: 'mock-for-settle' } }, x402Challenge(tool).accepts[0]).catch(() => {});
        }
        return origJson(body);
      };
      await proxyToMoss(req, res, tool.tier, key);
    });
  });
});

// --- Full MCP Streamable endpoint (Phase 2b) ---
// Stateful transport: each client session gets a sessionId, transport is reusable.
// (Stateless mode requires fresh transport per request — incompatible with our setup.)
const mcpTransport = new StreamableHTTPServerTransport({
  sessionIdGenerator: () => `mcp_${randomUUID()}`,
  enableJsonResponse: true
});
await mcpServer.connect(mcpTransport).catch(e => console.warn('[mcp] transport connect', e.message));

app.post('/mcp', async (req, res) => {
  // MCP clients should send Accept: application/json, text/event-stream
  if (!req.headers.accept) {
    req.headers.accept = 'application/json, text/event-stream';
  }
  const body = req.body || {};
  const isToolsCall = body.method === 'tools/call' && body.params && body.params.name;
  let tool = null;

  if (isToolsCall) {
    const toolName = body.params.name;
    tool = TOOLS.find(t => t.name === toolName);
    if (!tool) {
      return res.status(400).json({ jsonrpc: '2.0', id: body.id || null, error: { code: -32601, message: 'Unknown tool' } });
    }

    const { key, hash } = getTenantFromReq(req);
    const priceUsd = tool.priceUsd;

    try {
      await checkRateLimit(hash);
      await checkAndRecordSpend(hash, priceUsd);
    } catch (e) {
      const status = e.status || e.code || 429;
      return res.status(status).json({ error: e.message });
    }

    // Payment gate for MCP call
    const mw = x402Paywall(tool);
    // Use a small promise wrapper to support 402 early return from mw
    let paid = false;
    await new Promise((resolve) => {
      mw(req, res, () => { paid = true; resolve(); });
      // If mw sent response (402) it won't call next
      if (res.headersSent) resolve();
    });
    if (!paid || res.headersSent) return; // 402 or bypass already handled
  }

  // Proceed with MCP transport (uses shared global stateful transport)
  console.log(`[mcp] ${body.method} method=${body.method} id=${body.id}`);

  try {
    await mcpTransport.handleRequest(req, res, req.body);
    console.log(`[mcp] ${body.method} done, headersSent=${res.headersSent}`);
  } catch (e) {
    console.error('[mcp] handle error', e);
    if (!res.headersSent) res.status(500).json({ jsonrpc: '2.0', error: { code: -32603, message: e.message } });
  }
});

// Optional GET for transport discovery
app.get('/mcp', async (req, res) => {
  await mcpTransport.handleRequest(req, res);
});

// --- Error + 404 ---
app.use((req, res) => { res.status(404).json({ error: 'Not found' }); });
app.use((err, req, res, next) => { console.error('[error]', err); res.status(500).json({ error: err.message }); });

// --- Startup ---
let mossChild = null;

async function waitForHealth(url, timeoutMs = 8000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const r = await fetch(url, { method: 'GET' });
      if (r.ok) return true;
    } catch {}
    await sleep(250);
  }
  return false;
}

async function startMossRouter() {
  if (mossChild) return mossChild;
  const scriptPath = path.resolve(__dirname, MOSS_ROUTER_SCRIPT);
  const env = { ...process.env, PORT: String(MOSS_ROUTER_PORT), ...(MOCK ? { MOSS_MOCK: '1' } : {}) };
  mossChild = spawn(process.execPath, [scriptPath], { cwd: path.dirname(scriptPath), env, stdio: ['ignore', 'pipe', 'pipe'] });
  mossChild.stdout.on('data', (d) => process.stdout.write(`[moss-router] ${d}`));
  mossChild.stderr.on('data', (d) => process.stderr.write(`[moss-router:err] ${d}`));
  mossChild.on('exit', (code) => { console.error(`[moss-router] exited ${code}`); mossChild = null; });
  await waitForHealth(MOSS_HEALTH, 8000);
  return mossChild;
}

function stopMossRouter() {
  if (mossChild) { mossChild.kill('SIGTERM'); mossChild = null; }
}

async function main() {
  await startMossRouter();
  await initLangfuse();

  const server = app.listen(PORT, () => {
    console.log(`🌿 MossRouter MCP (Phase 2b) listening on http://localhost:${PORT}`);
    console.log(`   MossRouter child: ${MOSS_ROUTER_PORT} (mock=${MOCK})`);
    console.log(`   Pay-to: ${PAYTO} (${NETWORK})`);
    console.log(`   Facilitator: ${FACILITATOR_URL}`);
    console.log(`   Redis: ${redisStatus}   Langfuse: ${langfuseEnabled ? 'on' : 'off'}`);
    console.log(`   Skip: ${SKIP_PAYMENT}  Free/day: ${FREE_TIER_DAILY}`);
    console.log(`   Tools: ${TOOLS.map(t => t.name).join(', ')}`);
    console.log(`   MCP: POST /mcp (initialize / tools/list / tools/call)`);
  });

  process.on('SIGINT', () => { stopMossRouter(); if (redis) redis.quit(); server.close(); process.exit(0); });
  process.on('SIGTERM', () => { stopMossRouter(); if (redis) redis.quit(); server.close(); process.exit(0); });
}

main().catch(err => { console.error('Startup failed:', err); stopMossRouter(); process.exit(1); });
