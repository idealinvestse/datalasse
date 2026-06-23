/**
 * providers.js — provider abstraction factory (5 providers)
 * openai, anthropic, google, openrouter, groq
 * Groq uses OpenAI SDK with groq baseURL (no new deps).
 * Full mock support when MOSS_MOCK=1.
 */

import OpenAI from 'openai';
import Anthropic from '@anthropic-ai/sdk';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { isMock, structuredLog, resilientJSONParse, sleep, backoff } from './utils.js';
import { calculateCost, getPrice } from './pricing.js';

function makeMockResponse(promptText, tier, providerName, modelName, speedFast = false) {
  const content = `[MOCK:${providerName}/${modelName}] Response for tier=${tier}${speedFast ? ' (fast via Groq LPU)' : ''}:\n${(promptText || '').slice(0, 180)}...`;
  const pt = Math.max(8, Math.floor((promptText || '').length / 3.5));
  const ct = Math.max(12, Math.floor(pt * 0.6));
  const usage = { prompt_tokens: pt, completion_tokens: ct };
  return {
    content,
    usage,
    rawModel: modelName,
    provider: providerName,
    costUsd: calculateCost(usage, modelName)
  };
}

async function mockChat({ messages, model, tier, providerName, forceFail, speed }) {
  const text = (messages || []).map(m => m.content || '').join(' ');
  await sleep(8 + Math.random() * 25); // simulate tiny latency
  if (forceFail && forceFail === providerName) {
    const err = new Error(`MOCK_FORCE_FAIL:${providerName}`);
    err.code = 'mock_force_fail';
    throw err;
  }
  const speedFast = speed === 'fast';
  return makeMockResponse(text, tier || 'eco', providerName, model || 'mock-model', speedFast);
}

async function mockEmbed(text) {
  const { mockEmbed } = await import('./utils.js');
  return mockEmbed(text);
}

class MockProvider {
  constructor(name) { this.name = name; }
  async chat(opts) {
    return mockChat({ ...opts, providerName: this.name });
  }
  async embed(text) { return mockEmbed(text); }
}

function createOpenAICompatClient(apiKey, baseURL) {
  return new OpenAI({ apiKey: apiKey || 'sk-mock', baseURL });
}

export function createProvider(name, config = {}) {
  const mockMode = isMock();
  const apiKey = config.apiKey || process.env[config.apiKeyEnv || ''] || (mockMode ? 'sk-mock' : null);

  if (mockMode) {
    return new MockProvider(name);
  }

  if (name === 'openai' || name === 'openrouter' || name === 'groq') {
    let base = config.baseURL;
    if (name === 'openrouter') base = config.baseURL || 'https://openrouter.ai/api/v1';
    if (name === 'groq') base = 'https://api.groq.com/openai/v1';
    const client = createOpenAICompatClient(apiKey, base);
    return {
      name,
      async chat({ messages, model, temperature, max_tokens }) {
        const start = Date.now();
        try {
          const r = await client.chat.completions.create({
            model: model || (name === 'groq' ? 'llama-3.1-8b-instant' : 'gpt-4.1-mini'),
            messages,
            temperature: temperature ?? 0.7,
            max_tokens: max_tokens ?? 512,
          });
          const msg = r.choices?.[0]?.message?.content || '';
          const usage = r.usage || { prompt_tokens: 0, completion_tokens: 0 };
          return {
            content: msg,
            usage,
            rawModel: r.model || model,
            provider: name,
            latencyMs: Date.now() - start
          };
        } catch (e) {
          structuredLog({ type: 'provider_error', provider: name, error: e.message });
          throw e;
        }
      },
      async embed(text) {
        const r = await client.embeddings.create({ model: 'text-embedding-3-small', input: text });
        return r.data?.[0]?.embedding || [];
      }
    };
  }

  if (name === 'anthropic') {
    const client = new Anthropic({ apiKey });
    return {
      name,
      async chat({ messages, model, max_tokens, system }) {
        const start = Date.now();
        // Convert to Anthropic format + cache hint on first system if long
        let sys = system;
        const anthroMsgs = messages.map(m => ({ role: m.role === 'assistant' ? 'assistant' : 'user', content: m.content }));
        if (!sys && messages[0]?.role === 'system') sys = messages.shift().content;
        const params = {
          model: model || 'claude-sonnet-4.6',
          max_tokens: max_tokens || 512,
          messages: anthroMsgs,
        };
        if (sys) {
          params.system = [{ type: 'text', text: sys, cache_control: { type: 'ephemeral' } }];
        }
        try {
          const r = await client.messages.create(params);
          const content = r.content?.map(c => c.text || '').join('') || '';
          const usage = { prompt_tokens: r.usage?.input_tokens || 0, completion_tokens: r.usage?.output_tokens || 0 };
          return { content, usage, rawModel: r.model, provider: name, latencyMs: Date.now() - start };
        } catch (e) {
          structuredLog({ type: 'provider_error', provider: name, error: e.message });
          throw e;
        }
      },
      async embed(text) {
        // Fall back to mock for Anthropic embed (no native cheap embed)
        const { mockEmbed } = await import('./utils.js');
        return mockEmbed(text);
      }
    };
  }

  if (name === 'google') {
    const genai = new GoogleGenerativeAI(apiKey);
    return {
      name,
      async chat({ messages, model, temperature, max_tokens }) {
        const start = Date.now();
        const m = genai.getGenerativeModel({ model: model || 'gemini-2.5-flash' });
        const history = messages.map(m => ({ role: m.role === 'assistant' ? 'model' : 'user', parts: [{ text: m.content }] }));
        try {
          const r = await m.generateContent({
            contents: history,
            generationConfig: { temperature: temperature ?? 0.7, maxOutputTokens: max_tokens || 512 }
          });
          const content = r.response?.text() || '';
          // Google usage may be approximate
          const pt = Math.floor((messages.map(x=>x.content).join(' ').length)/4);
          const usage = { prompt_tokens: pt, completion_tokens: Math.floor(content.length/4) };
          return { content, usage, rawModel: model, provider: name, latencyMs: Date.now() - start };
        } catch (e) {
          structuredLog({ type: 'provider_error', provider: name, error: e.message });
          throw e;
        }
      },
      async embed(text) {
        // Use mock for now (Google embed model would be separate)
        const { mockEmbed } = await import('./utils.js');
        return mockEmbed(text);
      }
    };
  }

  // Fallback mock
  return new MockProvider(name || 'unknown');
}

export const PROVIDER_NAMES = ['openai', 'anthropic', 'google', 'openrouter', 'groq'];

export function createAllProviders(config = {}) {
  const out = {};
  for (const n of PROVIDER_NAMES) {
    const pcfg = (config.providers && config.providers[n]) || {};
    out[n] = createProvider(n, pcfg);
  }
  return out;
}
