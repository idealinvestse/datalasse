/**
 * pricing.js — static price table + cost calc (June 2026 prices, per 1M tokens)
 * All non-deprecated. Includes Groq LPU models.
 */

const DEFAULT_PRICES = {
  // OpenAI
  'gpt-4.1-nano': { in: 0.10, out: 0.40 },
  'gpt-4.1-mini': { in: 0.40, out: 1.60 },
  'gpt-4.1': { in: 2.00, out: 8.00 },
  'gpt-4o': { in: 2.50, out: 10.00 },
  'o3': { in: 2.00, out: 8.00 },
  'gpt-5.5': { in: 5.00, out: 30.00 },

  // Anthropic (current series)
  'claude-haiku-4.5': { in: 0.90, out: 4.50 },
  'claude-sonnet-4.6': { in: 3.00, out: 15.00 },
  'claude-opus-4.8': { in: 5.00, out: 25.00 },

  // Google Gemini
  'gemini-2.0-flash': { in: 0.10, out: 0.40 },
  'gemini-2.5-flash': { in: 0.30, out: 2.50 },
  'gemini-2.5-pro': { in: 1.25, out: 10.00 },

  // Groq (LPU - very cheap + fast)
  'llama-3.1-8b-instant': { in: 0.05, out: 0.08 },
  'openai/gpt-oss-20b': { in: 0.075, out: 0.30 },
  'meta-llama/llama-4-scout-17b-16e-instruct': { in: 0.11, out: 0.34 },
  'openai/gpt-oss-120b': { in: 0.15, out: 0.60 },
  'qwen/qwen3-32b': { in: 0.29, out: 0.59 },
  'llama-3.3-70b-versatile': { in: 0.59, out: 0.79 },
  'qwen/qwen3.6-27b': { in: 0.60, out: 3.00 },

  // OpenRouter pass-through examples (approx)
  'deepseek/deepseek-v4-flash': { in: 0.12, out: 0.25 },
};

export function getPrice(model) {
  if (!model) return { in: 0.5, out: 1.5 }; // safe fallback
  // normalize common variants
  const m = String(model).toLowerCase();
  if (DEFAULT_PRICES[m]) return DEFAULT_PRICES[m];
  // prefix match for groq names etc
  for (const [k, p] of Object.entries(DEFAULT_PRICES)) {
    if (m.includes(k) || k.includes(m.split('/').pop())) return p;
  }
  return { in: 0.5, out: 1.5 };
}

export function calculateCost(usage, modelOrPrice) {
  if (!usage) return 0;
  const p = typeof modelOrPrice === 'object' ? modelOrPrice : getPrice(modelOrPrice);
  const pin = usage.prompt_tokens || usage.input_tokens || 0;
  const pout = usage.completion_tokens || usage.output_tokens || 0;
  const cost = (pin / 1_000_000 * p.in) + (pout / 1_000_000 * p.out);
  return Number(cost.toFixed(6));
}

export const TIER_DEFAULTS = {
  nano: {
    description: 'Ultra low cost (classification, extraction, formatting)',
    models: [
      { provider: 'google', model: 'gemini-2.0-flash', priceIn: 0.10, priceOut: 0.40 },
      { provider: 'groq', model: 'llama-3.1-8b-instant', priceIn: 0.05, priceOut: 0.08 },
      { provider: 'openrouter', model: 'deepseek/deepseek-v4-flash', priceIn: 0.12, priceOut: 0.25 }
    ]
  },
  eco: {
    description: 'Balanced daily driver',
    models: [
      { provider: 'groq', model: 'openai/gpt-oss-20b', priceIn: 0.075, priceOut: 0.30 },
      { provider: 'google', model: 'gemini-2.5-flash', priceIn: 0.30, priceOut: 2.50 },
      { provider: 'openai', model: 'gpt-4.1-mini', priceIn: 0.40, priceOut: 1.60 }
    ]
  },
  standard: {
    description: 'Most work (good quality/cost)',
    models: [
      { provider: 'openai', model: 'gpt-4.1', priceIn: 2.00, priceOut: 8.00 },
      { provider: 'anthropic', model: 'claude-sonnet-4.6', priceIn: 3.00, priceOut: 15.00 },
      { provider: 'groq', model: 'llama-3.3-70b-versatile', priceIn: 0.59, priceOut: 0.79 }
    ]
  },
  premium: {
    description: 'Complex reasoning',
    models: [
      { provider: 'groq', model: 'openai/gpt-oss-120b', priceIn: 0.15, priceOut: 0.60 },
      { provider: 'openai', model: 'gpt-4o', priceIn: 2.50, priceOut: 10.00 },
      { provider: 'anthropic', model: 'claude-sonnet-4.6', priceIn: 3.00, priceOut: 15.00 }
    ]
  },
  flagship: {
    description: 'Max quality',
    models: [
      { provider: 'openai', model: 'gpt-5.5', priceIn: 5.00, priceOut: 30.00 },
      { provider: 'anthropic', model: 'claude-opus-4.8', priceIn: 5.00, priceOut: 25.00 },
      { provider: 'groq', model: 'qwen/qwen3.6-27b', priceIn: 0.60, priceOut: 3.00 }
    ]
  }
};

export function getTierConfig(tierName, overrideConfig) {
  const base = TIER_DEFAULTS[tierName] || TIER_DEFAULTS.eco;
  if (!overrideConfig || !overrideConfig.tiers || !overrideConfig.tiers[tierName]) {
    return base;
  }
  // allow override merge
  return { ...base, ...overrideConfig.tiers[tierName] };
}
