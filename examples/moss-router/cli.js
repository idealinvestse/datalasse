#!/usr/bin/env node
/**
 * CLI for MossRouter
 * Supports chat, models, tiers, route etc. Uses shared router.
 * --speed=fast, --tenant=foo
 */

import MossRouter from './lib/router.js';
import { isMock, structuredLog } from './lib/utils.js';
import { readFileSync } from 'node:fs';
import readline from 'node:readline';

const argv = process.argv.slice(2);
const MOCK = isMock();

function parseArg(name, def = null) {
  const f = argv.find(a => a.startsWith(`--${name}=`));
  if (f) return f.split('=')[1];
  const i = argv.indexOf(`--${name}`);
  if (i >= 0 && argv[i + 1] && !argv[i + 1].startsWith('--')) return argv[i + 1];
  return def;
}

let CONFIG = {};
try {
  CONFIG = JSON.parse(readFileSync(new URL('./config.example.json', import.meta.url), 'utf8'));
} catch {}
if (MOCK) CONFIG.mock = true;

const router = new MossRouter(CONFIG);

const cmd = argv[0] || 'chat';

async function runChat() {
  const tier = parseArg('tier', router.config.defaultTier);
  const speed = parseArg('speed', null);
  const tenant = parseArg('tenant', 'default');
  const prompt = argv.slice(1).filter(a => !a.startsWith('--')).join(' ') || 'Hello from MossRouter CLI.';
  const messages = [{ role: 'user', content: prompt }];

  console.log(`🌿 MossRouter CLI (mock=${MOCK}) tier=${tier} speed=${speed || 'auto'} tenant=${tenant}`);
  const res = await router.routeRequest({ messages, tier, tenant, speed });
  console.log(`\n[${res.provider}/${res.model} tier=${res.tier} cost=$${res.costUsd} cache=${res.cache} ${res.latencyMs}ms]`);
  console.log(res.content);
  console.log(`\nX-Moss-Cost-USD: ${res.costUsd}\nX-Moss-Model: ${res.model}`);
}

async function runModels() {
  const prov = parseArg('provider', null);
  console.log('Available moss: tiers and sample models:');
  for (const t of router.getAvailableTiers()) {
    const sel = router.selectProviderForTier(t, prov === 'groq' ? 'fast' : null);
    console.log(`  moss:${t} -> ${sel.provider}/${sel.model}`);
  }
  if (prov === 'groq' || !prov) {
    console.log('\nGroq models (via OpenAI compat):');
    console.log('  llama-3.1-8b-instant, openai/gpt-oss-20b, openai/gpt-oss-120b, llama-3.3-70b-versatile, ...');
  }
}

async function runTiers() {
  console.log('Tiers:');
  for (const t of router.getAvailableTiers()) {
    const cfg = router.config.tiers && router.config.tiers[t] ? router.config.tiers[t] : { description: t };
    console.log(`  ${t}: ${cfg.description || ''}`);
  }
}

async function runRoute() {
  const tier = parseArg('tier', 'eco');
  const prompt = parseArg('prompt', 'test');
  const speed = parseArg('speed');
  const sel = router.selectProviderForTier(tier, speed);
  console.log({ tier, speed, selected: sel, mock: MOCK });
}

async function runInteractive() {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  console.log('MossRouter interactive (type "exit" or ^C). Default tier eco. Use --tier etc on start.');
  const ask = () => rl.question('> ', async (line) => {
    if (['exit', 'quit'].includes(line.trim().toLowerCase())) { rl.close(); return; }
    try {
      const res = await router.routeRequest({ messages: [{ role: 'user', content: line }], tier: 'eco' });
      console.log(`[${res.tier}/${res.provider}] ${res.content}`);
    } catch (e) { console.error('err', e.message); }
    ask();
  });
  ask();
}

async function main() {
  try {
    if (cmd === 'chat' || cmd === 'c') await runChat();
    else if (cmd === 'models' || cmd === 'm') await runModels();
    else if (cmd === 'tiers' || cmd === 't') await runTiers();
    else if (cmd === 'route' || cmd === 'r') await runRoute();
    else if (cmd === 'interactive' || cmd === 'i') await runInteractive();
    else if (cmd === 'cost-estimate') {
      const tier = parseArg('tier', 'eco');
      console.log(`Estimated tier=${tier} (real cost after call)`);
    } else {
      console.log('Usage: moss-router chat --tier nano "prompt" | models | tiers | interactive');
    }
  } catch (e) {
    console.error('CLI error:', e.message);
    process.exit(1);
  }
}

main();
