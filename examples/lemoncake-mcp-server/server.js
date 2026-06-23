#!/usr/bin/env node
/**
 * LemonCake MCP Server — x402 billable MCP server (Phase 1 MVP)
 *
 * Phase 1: Base Sepolia testnet, no secrets, runnable immediately.
 * Phase 2 (future): Mainnet + BankID/Swish hybrid + Agent.market registration.
 *
 * 5 tools:
 *   1. search_web            $0.001
 *   2. get_weather           $0.001
 *   3. redovisning_helper    $0.005 (Swedish SME accounting helper)
 *   4. validate_skill_md     $0.002
 *   5. gdpr_scan             $0.003
 *
 * Free tier: 100 calls/day per wallet (in-memory stub)
 * 402 challenge: via x402 PAYMENT-REQUIRED header
 * Bypass: SKIP_PAYMENT=1 env var (for testing)
 *
 * Uses MCP Streamable HTTP transport.
 */

import express from 'express';
import { randomUUID } from 'node:crypto';

// --- Config ---
const PORT = parseInt(process.env.PORT || '4021', 10);
const SKIP_PAYMENT = process.env.SKIP_PAYMENT === '1';
const PAYTO = process.env.PAYTO_ADDRESS || '0x000000000000000000000000000000000000dEaD'; // placeholder Sepolia address
const NETWORK = process.env.NETWORK || 'eip155:84532'; // Base Sepolia
const FREE_TIER_DAILY = parseInt(process.env.FREE_TIER_DAILY || '100', 10);

const TOOLS = [
  {
    name: 'search_web',
    description: 'Web search via Serper. Returns top 5 organic results. Price: $0.001/call.',
    price: '$0.001',
    priceUsd: 0.001,
  },
  {
    name: 'get_weather',
    description: 'Current weather for a city (wttr.in). Price: $0.001/call.',
    price: '$0.001',
    priceUsd: 0.001,
  },
  {
    name: 'redovisning_helper',
    description: 'Swedish SME accounting helper (BAS-kontoplan lookup, moms calculation). Price: $0.005/call. NOT official accounting advice.',
    price: '$0.005',
    priceUsd: 0.005,
  },
  {
    name: 'validate_skill_md',
    description: 'Validate a SKILL.md frontmatter + structure. Price: $0.002/call.',
    price: '$0.002',
    priceUsd: 0.002,
  },
  {
    name: 'gdpr_scan',
    description: 'Lightweight GDPR red-flag scan of a text snippet (PII detection, no storage). Price: $0.003/call.',
    price: '$0.003',
    priceUsd: 0.003,
  },
];

// --- Free tier tracking (in-memory stub; replace with DB in Phase 2) ---
const freeTier = new Map(); // wallet -> { date: 'YYYY-MM-DD', count: N }
function getFreeTierCount(wallet) {
  const today = new Date().toISOString().slice(0, 10);
  const entry = freeTier.get(wallet);
  if (!entry || entry.date !== today) return 0;
  return entry.count;
}
function incrementFreeTier(wallet) {
  const today = new Date().toISOString().slice(0, 10);
  const entry = freeTier.get(wallet) || { date: today, count: 0 };
  if (entry.date !== today) entry.date = today;
  entry.count++;
  freeTier.set(wallet, entry);
}

// --- Tool implementations ---
async function toolSearchWeb({ query }) {
  if (!query) throw new Error('query required');
  // Phase 1: stub; Phase 2: Serper API call
  return {
    content: [
      { type: 'text', text: `[stub] Search results for: "${query}"\n\n1. https://example.com/result1 — Stub result 1\n2. https://example.com/result2 — Stub result 2\n3. https://example.com/result3 — Stub result 3\n\n(Phase 2: real Serper integration)` },
    ],
  };
}

async function toolGetWeather({ city }) {
  if (!city) throw new Error('city required');
  return {
    content: [
      { type: 'text', text: `[stub] Weather for "${city}": 18°C, partly cloudy. (Phase 2: wttr.in integration)` },
    ],
  };
}

async function toolRedovisningHelper({ question }) {
  if (!question) throw new Error('question required');
  // Tiny Swedish accounting knowledge base (Phase 1 stub)
  const lc = question.toLowerCase();
  let answer = '';
  if (lc.includes('moms') || lc.includes('vat')) {
    answer = 'Moms (VAT) i Sverige: 25% standard, 12% livsmedel, 6% kultur/tidningar. Redovisning: SKV-deklaration månadsvis/årsvis.';
  } else if (lc.includes('bas') || lc.includes('kontoplan')) {
    answer = 'BAS-kontoplanen: 1000-1999 Tillgångar, 2000-2999 Eget kapital/skulder, 3000-3999 Intäkter, 4000-7999 Kostnader.';
  } else if (lc.includes('bokslut')) {
    answer = 'Bokslut: årsredovisning för AB, årsbokslut för enskild firma. Skatteverket.se för detaljer.';
  } else {
    answer = `Redovisning helper (Phase 1 stub): "${question}". Phase 2: full BAS-kontoplan + momsrådgivning.`;
  }
  return {
    content: [
      { type: 'text', text: `${answer}\n\n(Detta är inte officiell redovisningsrådgivning. Konsultera auktoriserad revisor för bokslut.)` },
    ],
  };
}

async function toolValidateSkillMd({ content }) {
  if (!content) throw new Error('content required');
  const issues = [];
  if (!content.startsWith('---')) issues.push('Missing YAML frontmatter (must start with ---)');
  if (!content.includes('name:')) issues.push('Missing "name:" in frontmatter');
  if (!content.includes('description:')) issues.push('Missing "description:" in frontmatter');
  if (content.length < 200) issues.push('Content too short (<200 chars)');
  return {
    content: [
      { type: 'text', text: issues.length === 0 ? `✅ Valid SKILL.md (${content.length} chars)` : `❌ Issues:\n${issues.map((i) => `  - ${i}`).join('\n')}` },
    ],
  };
}

async function toolGdprScan({ text }) {
  if (!text) throw new Error('text required');
  // Lightweight PII detection (Phase 1 stub)
  const piiPatterns = [
    { re: /\b\d{8}-\d{4}\b/g, label: 'personnummer' },
    { re: /\b\d{10,16}\b/g, label: 'possible credit card / phone' },
    { re: /\b[A-ZÅÄÖa-zåäö0-9._%+-]+@[A-ZÅÄÖa-zåäö0-9.-]+\.[A-Z]{2,}\b/g, label: 'email' },
  ];
  const found = [];
  for (const { re, label } of piiPatterns) {
    const matches = text.match(re) || [];
    if (matches.length) found.push(`${label}: ${matches.length} match(es)`);
  }
  return {
    content: [
      { type: 'text', text: found.length === 0 ? `✅ No obvious PII detected (${text.length} chars scanned, no storage)` : `⚠️ Possible PII: ${found.join(', ')}` },
    ],
  };
}

const TOOL_HANDLERS = {
  search_web: toolSearchWeb,
  get_weather: toolGetWeather,
  redovisning_helper: toolRedovisningHelper,
  validate_skill_md: toolValidateSkillMd,
  gdpr_scan: toolGdprScan,
};

// --- x402 402 challenge ---
function x402Challenge(tool, wallet) {
  return {
    x402Version: 2,
    accepts: [
      {
        scheme: 'exact',
        network: NETWORK,
        payTo: PAYTO,
        maxAmountRequired: Math.ceil(tool.priceUsd * 1_000_000).toString(), // USDC has 6 decimals
        resource: `/mcp/tools/${tool.name}`,
        description: tool.description,
        mimeType: 'application/json',
        outputSchema: {},
        paywall: 'https://x402.org',
      },
    ],
  };
}

// --- Express app ---
const app = express();
app.use(express.json({ limit: '1mb' }));

// CORS for local testing
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Payer-Wallet, PAYMENT-SIGNATURE');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

// --- Info endpoints ---
app.get('/', (req, res) => {
  res.json({
    name: 'LemonCake MCP Server',
    version: '0.1.0',
    phase: 'Phase 1 MVP (Base Sepolia testnet)',
    skipPayment: SKIP_PAYMENT,
    payTo: PAYTO,
    network: NETWORK,
    freeTierDaily: FREE_TIER_DAILY,
    tools: TOOLS.map((t) => ({
      name: t.name,
      description: t.description,
      price: t.price,
    })),
  });
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok', uptime: process.uptime(), skipPayment: SKIP_PAYMENT });
});

// --- x402 middleware (simplified for Phase 1) ---
function x402Paywall(tool) {
  return (req, res, next) => {
    if (SKIP_PAYMENT) {
      console.log(`[bypass] ${tool.name} called (SKIP_PAYMENT=1)`);
      return next();
    }

    const wallet = req.headers['x-payer-wallet'] || 'anonymous';
    const today = new Date().toISOString().slice(0, 10);
    const count = getFreeTierCount(wallet);

    // Free tier: still allowed
    if (count < FREE_TIER_DAILY) {
      incrementFreeTier(wallet);
      console.log(`[free-tier] ${tool.name} (wallet ${wallet.slice(0, 8)}…, ${count + 1}/${FREE_TIER_DAILY} today)`);
      return next();
    }

    // Otherwise: require payment
    const hasPayment = req.headers['payment-signature'] || req.headers['x-payment'];
    if (!hasPayment) {
      console.log(`[402] ${tool.name} (wallet ${wallet.slice(0, 8)}…, free tier exhausted)`);
      const challenge = x402Challenge(tool, wallet);
      res.setHeader('PAYMENT-REQUIRED', Buffer.from(JSON.stringify(challenge)).toString('base64'));
      return res.status(402).json({
        error: 'Payment required',
        challenge,
        freeTierExhausted: true,
        freeTierDaily: FREE_TIER_DAILY,
      });
    }

    // Phase 1: accept signature header as proof-of-concept (Phase 2: verify via CDP facilitator)
    console.log(`[paid] ${tool.name} (signature: ${String(hasPayment).slice(0, 20)}…)`);
    next();
  };
}

// --- MCP tool dispatch endpoint (simplified Streamable HTTP) ---
app.post('/mcp/tools/:name', (req, res, next) => {
  const tool = TOOLS.find((t) => t.name === req.params.name);
  if (!tool) return res.status(404).json({ error: `Unknown tool: ${req.params.name}` });
  // Apply paywall
  const middleware = x402Paywall(tool);
  middleware(req, res, () => {
    const handler = TOOL_HANDLERS[tool.name];
    if (!handler) return res.status(500).json({ error: 'Handler missing' });
    handler(req.body || {})
      .then((result) => res.json({ ok: true, tool: tool.name, ...result }))
      .catch((err) => res.status(400).json({ error: err.message }));
  });
});

// List tools (no paywall — discovery is free)
app.get('/mcp/tools', (req, res) => {
  res.json({
    tools: TOOLS.map((t) => ({
      name: t.name,
      description: t.description,
      price: t.price,
    })),
  });
});

// --- Error handler ---
app.use((err, req, res, next) => {
  console.error('[error]', err);
  res.status(500).json({ error: err.message });
});

// --- Start ---
app.listen(PORT, () => {
  console.log(`🍋 LemonCake MCP Server listening on http://localhost:${PORT}`);
  console.log(`   Pay-to: ${PAYTO} (${NETWORK})`);
  console.log(`   Skip payment: ${SKIP_PAYMENT}`);
  console.log(`   Free tier: ${FREE_TIER_DAILY} calls/day per wallet`);
  console.log(`   Tools: ${TOOLS.map((t) => t.name).join(', ')}`);
  console.log(`   Try: curl http://localhost:${PORT}/`);
});