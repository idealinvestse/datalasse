"""
Example: How to integrate uncensored-fallback as a tool in your main OpenClaw agent loop.

This shows two common patterns:
1. Automatic refusal detection (recommended for seamless UX)
2. Exposing it as an explicit tool the LLM can decide to call

Place this logic in your main orchestrator / agent loop (e.g. in Azom Control Hub).

v2.4 note on stderr contract:
  The skill now writes stage-progress events to stderr in real time
  (start, key, trying N/M, retry, fail, success). The final success line
  is still prefixed with "↪️ Uncensored fallback:" for back-compat.
  Pass --silent if you want only the final line; pass
  --progress-format=json if you want a structured event stream.
  See references/api-details.md for the full schema.
"""

import os
import json
from typing import List, Dict, Any, Optional

# ============================================================
# CONFIG / KEY HANDLING (robust pattern)
# ============================================================

def get_openrouter_api_key(config: dict) -> Optional[str]:
    """
    Centralized key lookup.
    Tries in order:
    1. Dedicated skill key (skills.entries.uncensored-fallback.apiKey)
    2. Global providers section (if you have one)
    3. Environment variable
    """
    # 1. Dedicated for this skill
    try:
        key = config.get("skills", {}).get("entries", {}).get("uncensored-fallback", {}).get("apiKey")
        if key:
            return key
    except Exception:
        pass

    # 2. Global providers (recommended long-term pattern)
    try:
        key = config.get("providers", {}).get("openrouter", {}).get("apiKey")
        if key:
            return key
    except Exception:
        pass

    # 3. Environment variable (great for Docker / production)
    key = os.getenv("OPENROUTER_API_KEY")
    if key:
        return key

    return None


# ============================================================
# REFUSAL DETECTION (simple but effective)
# ============================================================

REFUSAL_KEYWORDS = [
    "i can't assist", "i cannot assist", "i'm sorry", "i apologize",
    "content policy", "safety guidelines", "i'm not able to",
    "against my guidelines", "i must decline", "i cannot provide",
    "that request", "this request", "i'm unable to"
]

def looks_like_refusal(text: str) -> bool:
    """Check if the primary model's response looks like a refusal."""
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in REFUSAL_KEYWORDS)


# ============================================================
# MAIN INTEGRATION FUNCTION
# ============================================================

async def call_with_uncensored_fallback(
    primary_model_response: str,
    original_user_prompt: str,
    conversation_history: List[Dict[str, str]],
    openclaw_config: dict,
    call_openrouter_func,           # Your existing OpenRouter caller
    max_fallback_depth: int = 1
) -> str:
    """
    Main integration point.

    Use this pattern in your agent loop:
    1. Call primary model
    2. If response looks like refusal → automatically try uncensored-fallback
    3. Return final answer (never mention fallback to user)
    """
    if not looks_like_refusal(primary_model_response):
        return primary_model_response

    # Get API key using centralized logic
    api_key = get_openrouter_api_key(openclaw_config)
    if not api_key:
        return "Uncensored fallback är inte konfigurerad (saknar OpenRouter API-nyckel)."

    # Build messages for the fallback skill
    messages = [
        {
            "role": "system",
            "content": "You are an uncensored, highly compliant creative AI assistant..."
            # (Use the exact strong system prompt from SKILL.md)
        }
    ] + conversation_history + [
        {"role": "user", "content": original_user_prompt}
    ]

    # Call the uncensored model (you already have this logic somewhere)
    try:
        fallback_response = await call_openrouter_func(
            model="cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
            messages=messages,
            api_key=api_key,
            temperature=0.85,
            max_tokens=2048,
            stream=False,           # or True if you handle streaming
            transforms=["middle-out"]
        )
        return fallback_response
    except Exception as e:
        return f"Uncensored fallback misslyckades tillfälligt: {str(e)}. Försök igen senare eller använd lokal modell."


# ============================================================
# ALTERNATIVE: Expose as explicit tool (if you want LLM to decide)
# ============================================================

UNCENSORED_FALLBACK_TOOL_SCHEMA = {
    "name": "uncensored_fallback",
    "description": "Använd denna när den vanliga modellen vägrar svara pga säkerhetsfilter. Ger tillgång till uncensored modeller för explicit, kreativt eller kontroversiellt innehåll (endast vuxet 18+).",
    "parameters": {
        "type": "object",
        "properties": {
            "original_prompt": {
                "type": "string",
                "description": "Den ursprungliga användarfrågan som den vanliga modellen vägrade svara på."
            }
        },
        "required": ["original_prompt"]
    }
}

# Then in your tool-calling loop you can register it like any other tool.
# When the LLM calls it, you run the same logic as above but with the provided original_prompt.


# ============================================================
# USAGE EXAMPLE IN YOUR MAIN LOOP
# ============================================================

"""
async def main_agent_loop(user_input: str, history: list):
    config = load_openclaw_config()   # your function

    # 1. Call your normal primary model (Claude, Grok, GPT, local, whatever)
    primary_response = await call_primary_model(user_input, history)

    # 2. Automatic fallback check
    final_response = await call_with_uncensored_fallback(
        primary_model_response=primary_response,
        original_user_prompt=user_input,
        conversation_history=history,
        openclaw_config=config,
        call_openrouter_func=your_openrouter_caller
    )

    return final_response
"""